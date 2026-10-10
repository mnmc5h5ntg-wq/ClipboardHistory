"""`scripts/frame_baseline.py` 的自测（第三轮审计 §3 C-2）。

这里测的是**分类**：变了 / 少了 / 多了 必须分开，因为三者的处置完全不同。
如果只报一个"diff 不为零"，那这条守卫和没有一样 —— reviewer 仍然不知道看哪张图。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.frame_baseline import (  # noqa: E402
    BASELINE_RELATIVE,
    collect,
    compare,
    latest_released_baseline,
    load_baseline,
    main,
    manifest_path,
    released_baselines,
    snapshot,
    version_key,
    write_baseline,
)


def make_frame(directory: str, name: str, payload: bytes) -> str:
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(payload)
    return path


class FrameBaselineTests(unittest.TestCase):
    def test_three_kinds_of_difference_are_reported_separately(self):
        baseline = {"a.png": "1", "b.png": "2", "c.png": "3"}
        current = {"a.png": "1", "b.png": "9", "d.png": "4"}
        changed, missing, added = compare(baseline, current)
        self.assertEqual(changed, ["b.png"])
        self.assertEqual(missing, ["c.png"], "帧不见了=有夹具不再被执行，这必须和「变了一格」分开报")
        self.assertEqual(added, ["d.png"])

    def test_identical_trees_produce_no_findings(self):
        frames = {"x.png": "abc", "y.png": "def"}
        self.assertEqual(compare(frames, dict(frames)), ([], [], []))

    def test_collect_only_reads_pngs_and_is_order_independent(self):
        with tempfile.TemporaryDirectory() as root:
            make_frame(root, "one.png", b"1")
            make_frame(root, "two.png", b"2")
            make_frame(root, "notes.txt", b"ignore me")
            os.mkdir(os.path.join(root, "subdir.png"))   # 同名目录不许被当成帧
            found = collect(root)
        self.assertEqual(sorted(found), ["one.png", "two.png"])

    def test_update_then_compare_is_clean_and_exit_codes_are_used(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, "row-a.png", b"content")
            self.assertEqual(main(["update", frames_dir, "--repo-root", root]), 0)
            self.assertTrue(os.path.exists(manifest_path(root)))
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 0)

            make_frame(frames_dir, "row-a.png", b"changed!")
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 1,
                             "变帧必须让退出码非零，否则 CI 那步只是打印")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 0,
                             "check 只在乎「不许少帧」：新功能加帧不该把它判红")

            os.remove(os.path.join(frames_dir, "row-a.png"))
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1,
                             "少帧是回归信号，check 必须抓到")

    def test_missing_or_broken_baseline_is_an_error_not_a_pass(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, "a.png", b"x")
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 2,
                             "没有基线时不能报「一致」—— 那等于这一步永远绿")
            bad = manifest_path(root)
            os.makedirs(os.path.dirname(bad), exist_ok=True)
            Path(bad).write_text("{not json", encoding="utf-8")
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 2)
            Path(bad).write_text(json.dumps({"schema": 1}), encoding="utf-8")
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 2)

    def test_allow_missing_only_absolves_the_named_frames(self):
        """许可名单是**按名字**的，不是"允许少 N 张"。

        按数字容差的话，夹具丢一张、另一张改名，两条都会被"反正差一张"吃掉；
        按名字则只赦免"我们已经知道为什么缺席"的那几张，其余一张都不许溜走。
        """
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, "a.png", b"1")
            make_frame(frames_dir, "b.png", b"2")
            write_baseline(manifest_path(root), {"a.png": "1", "b.png": "2", "c.png": "3", "d.png": "4"})

            self.assertEqual(main(["check", frames_dir, "--repo-root", root,
                                   "--allow-missing", "c.png", "--allow-missing", "d.png"]), 0,
                             "两张都在许可名单里，check 不该判红")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root,
                                   "--allow-missing", "c.png"]), 1,
                             "d.png 不在名单里却缺席：这才是真回归，必须红")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1,
                             "没给名单时两张缺席都要红")

    def test_version_ordering_is_numeric_not_lexicographic(self):
        """v1.4.10 必须排在 v1.4.9 之后。

        按字符串排会得到 `v1.4.9 > v1.4.10`，于是"上一版"会选错对象，
        整条 diff 语义就悄悄反了 —— 而这正是这条守卫唯一的存在理由。
        """
        self.assertGreater(version_key("v1.4.10.json"), version_key("v1.4.9.json"))
        self.assertGreater(version_key("v1.10.0.json"), version_key("v1.9.2.json"))
        names = ["v1.4.8.json", "v1.4.10.json", "v1.9.0.json"]
        self.assertEqual(sorted(names, key=version_key),
                         ["v1.4.8.json", "v1.4.10.json", "v1.9.0.json"])

    def test_snapshot_freezes_the_working_manifest_and_becomes_the_default_target(self):
        """C-2 要的是"和**上一版**比"。只有一份可随时 update 的工作基线的话，
        "上一版"其实等于"上一次有人记得 update 的时候"。所以发布时冻结一份逐版本快照，
        而 `auto` 优先解析到最新的那一版。
        """
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, "a.png", b"1")
            main(["update", frames_dir, "--repo-root", root])
            self.assertIsNone(latest_released_baseline(root), "还没发布过就不该有逐版本基线")

            self.assertEqual(main(["snapshot", "--version", "1.4.8", "--repo-root", root]), 0)
            self.assertEqual(main(["snapshot", "--version", "1.4.9", "--repo-root", root]), 0)
            self.assertEqual(released_baselines(root), ["v1.4.8.json", "v1.4.9.json"])

            # 改了内容：默认对最新一版比，仍然是"没变"；把版本顺序反过来就会红 —— 那条排序才是关键
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 0)
            make_frame(frames_dir, "a.png", b"2")
            self.assertEqual(main(["compare", frames_dir, "--repo-root", root]), 1)

    def test_snapshot_without_a_working_manifest_is_an_error(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(main(["snapshot", "--version", "9.9.9", "--repo-root", root]), 2)
            self.assertEqual(main(["compare", "--repo-root", root]), 2,
                             "缺 frames 目录参数要报用法错误，不是崩在 argparse 之外")

    def test_roundtrip_preserves_every_entry(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "docs", "frame_baseline.json")
            frames = {"f-%d.png" % i: "%064x" % i for i in range(5)}
            write_baseline(path, frames)
            self.assertEqual(load_baseline(path), frames)

    def test_the_committed_baseline_covers_the_current_suite(self):
        """仓库里那份基线不许过期到「只剩几张」的程度。

        帧数下限写死在这里，是为了让"夹具被删/不再执行"这件事在自测里就红一次，
        而不是等到 CI 比对时才发现基线本来就残缺。
        """
        repo_root = Path(__file__).resolve().parents[2]
        path = repo_root / BASELINE_RELATIVE
        self.assertTrue(path.exists(), "docs/frame_baseline.json 不见了：C-2 那一环又断了")
        frames = load_baseline(str(path))
        self.assertGreaterEqual(len(frames), 70,
                                "基线只覆盖 %d 帧；离屏夹具现在有 78 张" % len(frames))
        self.assertTrue(all(len(v) == 64 for v in frames.values()), "基线里有不是 sha256 的长度")


if __name__ == "__main__":
    unittest.main()
