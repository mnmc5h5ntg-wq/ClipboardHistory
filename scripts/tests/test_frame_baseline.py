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
    drift_registry_path,
    judge_drift,
    latest_released_baseline,
    load_baseline,
    load_drift_registry,
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
            # R583 **显式推翻**这一格原来的第二句断言（「check 只在乎不许少帧，加帧/变帧不该红」）：
            # 那一版把 changed 与 added 交给"人判断"，而实际上没人判 —— 本机那 8 张变帧
            # 从 R577 起连续四轮逐字相同地挂在 CHANGED=8 上，退出码一直是 0（655 那个洞的形状）。
            # 现在两态都要逐张登记：没登记 ⇒ 红；登记了 ⇒ 绿，并且名册本身也要能被判腐烂。
            absent = os.path.join(root, "no-registry.json")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root,
                                   "--drift-registry", absent]), 1,
                             "变帧没登记 ⇒ check 必须红（旧语义在这一态上是「命令成功、谁都没判」）")
            registry = os.path.join(root, "docs", "frame_drift_registry.json")
            os.makedirs(os.path.dirname(registry), exist_ok=True)
            Path(registry).write_text(json.dumps({"schema": 1, "rows": [
                {"frame": "row-a.png", "kind": "changed", "ticket": "655",
                 "reason": "合成用例：这张帧在本测试里确实变了"}]}), encoding="utf-8")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 0,
                             "同一张变帧登记过之后 check 必须绿 —— 绿要由名册给，不许由「不判」给")

            os.remove(os.path.join(frames_dir, "row-a.png"))
            self.assertEqual(main(["check", frames_dir, "--repo-root", root,
                                   "--drift-registry", absent]), 1,
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
            # 基线里 a/b 用**真哈希**（本轮之后 check 也判 changed，拿假哈希当基线就会凭空造出两张变帧），
            # c/d 用假哈希占位 —— 它们要的是"缺席"那一态。
            write_baseline(manifest_path(root), dict(collect(frames_dir), **{"c.png": "3", "d.png": "4"}))

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


class DriftRegistryTests(unittest.TestCase):
    """R583 / 655：`check` 里 changed 与 added 两态从"没人判"变成"逐张登记否则红"。

    三件场景是派单点名的，各自钉一条相反的坏法：
    ① 塞一张改动帧而**不登记** ⇒ 红；
    ② 登记之后 ⇒ 绿，**且**报出「已登记 N 张」，N 等于 changed 里被登记的那部分；
    ③ 把登记名单清空 ⇒ 又红（"名册在但空"不等于"名册缺席"，两者都必须红）。
    另外三件是名册自己会腐烂的形状：拼错的帧名、空理由/空单号、名册形状读不出来。
    ⚠ 陈旧行（这台机器此刻不漂）**只报数不判** —— 漂移是按机器的，把它判红等于逼人在两台机器之间来回删行；
      这一格故意写成"断言它不红"，这样哪天有人顺手把陈旧也判红，这里会红一次给他看。
    """

    def setup(self, root):
        frames_dir = os.path.join(root, "frames")
        os.mkdir(frames_dir)
        make_frame(frames_dir, "a.png", b"1")
        make_frame(frames_dir, "b.png", b"2")
        make_frame(frames_dir, "c.png", b"3")
        # 基线：a/c 与当前逐字相同，b 故意不同 ⇒ 这个夹具里**只有一态**是变帧，missing/added 都是 0。
        baseline = dict(collect(frames_dir))
        baseline["b.png"] = "0" * 64
        write_baseline(manifest_path(root), baseline)
        return frames_dir

    def registry(self, root, rows):
        path = os.path.join(root, "docs", "frame_drift_registry.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Path(path).write_text(json.dumps({"schema": 1, "rows": rows}, ensure_ascii=False), encoding="utf-8")
        return path

    def row(self, name, kind="changed", reason="合成：这一帧的差有名字有出处", ticket="655"):
        return {"frame": name, "kind": kind, "reason": reason, "ticket": ticket}

    def test_changed_frame_without_registration_is_red(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            rc = main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 1, "b.png 变了而名册缺席 ⇒ 必须红（旧语义在这里返回 0）")

    def test_registration_makes_it_green_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [self.row("b.png")])
            rc = main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 0, "登记过就该绿 —— 绿要由名册给，不是由「不判」给")

    def test_empty_registry_is_red_not_absent_ok(self):
        """③ 名册在、rows 为空 ⇒ 一样红。"我建了个空名册"不是登记。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [])
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1)

    def test_partially_registered_counts_the_registered_part(self):
        """⑵ 的 N 必须是「changed∪added 里被登记的那部分」，不是名册行数。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            make_frame(frames_dir, "d.png", b"4")             # 新帧（未登记）
            baseline = load_baseline(manifest_path(root))
            current = collect(frames_dir)
            changed, missing, added = compare(baseline, current)
            self.assertEqual((changed, missing, added), (["b.png"], [], ["d.png"]))
            self.registry(root, [self.row("b.png")])          # 只登记变帧
            rows = load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json"))
            verdict = judge_drift(changed, added, baseline, current, rows)
            self.assertEqual((verdict["changed"], verdict["added"], verdict["registered"]), (1, 1, 1))
            self.assertEqual(sorted(verdict["unregistered"]), ["d.png"],
                             "N 只数被登记的那部分；没登记的那一张要单独点名")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1)

    def test_added_frame_is_judged_too(self):
        """旧语义里 added 在 check 上谁都不判（注释写"新功能本来就会加帧"）⇒ 本轮把它也接上登记。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            make_frame(frames_dir, "new.png", b"n")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root,
                                   "--drift-registry", os.path.join(root, "absent.json")]), 1,
                             "多出一帧而没人登记 ⇒ 红（这条推翻旧断言里「加帧不该红」那一句）")
            self.registry(root, [self.row("new.png", kind="added", reason="合成：新夹具的第一帧")])
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1,
                             "b.png 仍是未登记的变帧 ⇒ 一码归一码，登记 added 不该顺手赦掉 changed")

    def test_roster_with_unknown_frame_is_red(self):
        """名册里拼错的帧名必须红 —— 这是"名册腐烂成噪声"唯一的可判形状（与机器无关）。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [self.row("b.png"), self.row("b-_typo.png")])
            verdict = judge_drift(["b.png"], [], {"b.png": "9", "c.png": "3"}, collect(frames_dir),
                                  load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json")))
            self.assertEqual(verdict["unknown"], ["b-_typo.png"])
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1)

    def test_roster_row_without_reason_or_ticket_is_red(self):
        """登记是账，不是措辞：理由或单号缺一行都算没登记。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            for bad in (self.row("b.png", reason=""), self.row("b.png", ticket="")):
                self.registry(root, [bad])
                self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1,
                                 "空理由/空单号必须红：%r" % bad)

    def test_stale_row_is_reported_but_not_red(self):
        """这台机器此刻不漂 ≠ 登记写错 ⇒ 陈旧行只报数。哪天有人把它判红，这一格会红给他看。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, "a.png", b"1")
            make_frame(frames_dir, "b.png", b"2")
            write_baseline(manifest_path(root), collect(frames_dir))   # 一帧都不漂
            self.registry(root, [self.row("b.png")])                   # 但名册里有一行（另一台漂过）
            verdict = judge_drift([], [], collect(frames_dir), collect(frames_dir),
                                  load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json")))
            self.assertEqual(verdict["stale"], ["b.png"])
            self.assertEqual(verdict["unknown"], [], "b.png 在基线里 ⇒ 它不是拼错，不许被算成对不上")
            self.assertEqual(verdict["unregistered"], [])
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 0,
                             "陈旧行不许拦门：漂移是按机器的，另一台不漂不代表这条登记错了")

    def test_broken_registry_is_an_error_code_not_a_pass(self):
        """名册读不出来 ⇒ 2（用法/环境错），不许退化成「0 条登记」然后红或绿。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            path = self.registry(root, [])
            Path(path).write_text("{not json", encoding="utf-8")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 2)
            Path(path).write_text(json.dumps({"schema": 1, "rows": {"a.png": 1}}), encoding="utf-8")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 2)
            Path(path).write_text(json.dumps({"schema": 1, "rows": [
                {"frame": "b.png", "kind": "wibble", "reason": "x", "ticket": "655"}]}), encoding="utf-8")
            self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 2,
                             "kind 不认识也算名册坏 —— 静默忽略它等于给门留一条旁路")

    def test_pure_verdict_does_not_read_the_filesystem(self):
        """纯函数那一半要能拿内存里的表判：否则正对照测的是文件读法而不是判定。"""
        verdict = judge_drift(["x.png"], ["y.png"], {"x.png": "1"}, {"x.png": "2", "y.png": "3"},
                              [self.row("x.png"), self.row("y.png", kind="added")])
        self.assertEqual((verdict["registered"], verdict["unregistered"], verdict["unknown"],
                          verdict["bad_fields"], verdict["stale"]), (2, [], [], [], []))

    def test_the_committed_registry_frames_exist_in_the_committed_baseline(self):
        """盘上那份名册的每一行都必须对得上盘上那份基线 —— 这条让"名册腐烂"在自测里就红一次。"""
        repo_root = Path(__file__).resolve().parents[2]
        baseline = load_baseline(str(repo_root / BASELINE_RELATIVE))
        rows = load_drift_registry(drift_registry_path(str(repo_root)))
        self.assertGreaterEqual(len(rows), 1,
                                u"盘上名册一行都没有 ⇒ 这一格没有对象，不许读成「没有变帧」")
        for row in rows:
            self.assertIn(row["frame"], baseline,
                          u"名册里 %s 这一行在基线里找不到（拼错或夹具改名后留下的）" % row["frame"])
            self.assertTrue(row["reason"].strip() and row["ticket"].strip(),
                            u"名册里 %s 缺理由或单号" % row["frame"])


if __name__ == "__main__":
    unittest.main()
