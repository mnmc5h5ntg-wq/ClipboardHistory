"""`scripts/frame_baseline.py` 的自测（第三轮审计 §3 C-2）。

这里测的是**分类**：变了 / 少了 / 多了 必须分开，因为三者的处置完全不同。
如果只报一个"diff 不为零"，那这条守卫和没有一样 —— reviewer 仍然不知道看哪张图。
"""
import ast
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.frame_baseline import (  # noqa: E402
    BASELINE_RELATIVE,
    DRIFT_REGISTRY_RELATIVE,
    baseline_digest,
    baseline_owner,
    collect,
    compare,
    drift_registry_path,
    judge_drift,
    latest_released_baseline,
    load_baseline,
    load_baseline_document,
    load_drift_registry,
    machine_baseline_path,
    machine_key,
    main,
    manifest_path,
    released_baselines,
    sanitize_machine,
    snapshot,
    verify_provenance,
    version_key,
    write_baseline,
)


@contextlib.contextmanager
def pinned_machine(key):
    """把 `machine_key()` 的取值钉成常量再跑。

    凡是判"机器维度"的格子都必须走这里：上一轮 R565 那朵红就是"守卫写死本机口径 ⇒
    本机绿而 runner 注定红"，测机器的仪器自己先不许依赖它所在的那台机器。
    """
    saved = dict(os.environ)
    os.environ["MOTION_FLOOR_MACHINE_KEY"] = key
    try:
        yield key
    finally:
        os.environ.clear()
        os.environ.update(saved)


def make_frame(directory: str, name: str, payload: bytes) -> str:
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(payload)
    return path


def run_main(argv):
    """跑 `main()` 并把它的 stdout 一起拿回来 —— 这一卷新加的判定大多要读**印出来的形状**，
    只看退出码就会把「判=不判」与「判=判而恰好没东西要判」混成同一个绿。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = main(argv)
    return rc, buffer.getvalue()


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
            # R584：登记的键是 (机器, 帧)。这一格先按旧形状（没有 machine）跑一次 ⇒ 必须红并指名，
            #      再补上机器字段跑一次 ⇒ 才许绿。红指的是"这一行没写它豁免哪台机器"，不是判决坏了。
            Path(registry).write_text(json.dumps({"schema": 1, "rows": [
                {"frame": "row-a.png", "kind": "changed", "ticket": "655",
                 "reason": "合成用例：这张帧在本测试里确实变了"}]}), encoding="utf-8")
            with pinned_machine(u"local:fixture-host") as key:
                self.assertEqual(main(["check", frames_dir, "--repo-root", root]), 1,
                                 "登记行缺 machine 字段 ⇒ 门红（那一行等于让本机替所有机器背书）")
                Path(registry).write_text(json.dumps({"schema": 1, "rows": [
                    {"frame": "row-a.png", "kind": "changed", "machine": key, "ticket": "655",
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


class DriftFixture(unittest.TestCase):
    """R583 / 655：`check` 里 changed 与 added 两态从"没人判"变成"逐张登记否则红"。

    三件场景是派单点名的，各自钉一条相反的坏法：
    ① 塞一张改动帧而**不登记** ⇒ 红；
    ② 登记之后 ⇒ 绿，**且**报出「已登记 N 张」，N 等于 changed 里被登记的那部分；
    ③ 把登记名单清空 ⇒ 又红（"名册在但空"不等于"名册缺席"，两者都必须红）。
    另外三件是名册自己会腐烂的形状：拼错的帧名、空理由/空单号、名册形状读不出来。
    ⚠ 陈旧行与「他机行」（这台机器此刻不漂）**只报数不判** —— 漂移是按机器的，把它判红等于
      逼人在两台机器之间来回删行；这一格故意写成"断言它不红"，哪天有人顺手把不判改成判红，这里会红一次。
    ⚠ 本卷把机器键**钉成常量**（`FIXTURE_KEY`），不读宿主：上一轮 R565 那朵"守卫写死绝对根 ⇒
      本机绿而 runner 红"就是这么来的，测机器的仪器自己先不许依赖机器。
    """

    FIXTURE_KEY = "local:fixture-machine"

    def setUp(self):
        self._saved_env = dict(os.environ)
        os.environ["MOTION_FLOOR_MACHINE_KEY"] = self.FIXTURE_KEY

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved_env)

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

    def stamped_row(self, root, frames_dir, name, kind="changed",
                    reason="合成：这一帧的差有名字有出处，且带本机当轮观测到的哈希", ticket="655"):
        """R585：一行"正在豁免漂移"的登记必须带出处，而出处只能按工具自己的算法算。

        在测试里复现它 = 复现 `register-drift` 写的那两个哈希；这不是把判据放宽，
        而是把夹具从"手抄一行"升级成"命令会写成的那一行"。
        """
        baseline = load_baseline(manifest_path(root))
        current = collect(frames_dir)
        return {"frame": name, "kind": kind, "machine": self.FIXTURE_KEY, "reason": reason,
                "ticket": ticket,
                "observed": {"frame_sha": current.get(name, ""),
                             "baseline_sha": baseline_digest(baseline)}}

    def row(self, name, kind="changed", reason="合成：这一帧的差有名字有出处", ticket="655",
            machine=None):
        return {"frame": name, "kind": kind, "machine": self.FIXTURE_KEY if machine is None else machine,
                "reason": reason, "ticket": ticket}

class DriftRegistryTests(DriftFixture):
    """登记名册那一半的判定（R583 / 655）：三态都得有人判。"""

    def test_changed_frame_without_registration_is_red(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            rc = main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 1, "b.png 变了而名册缺席 ⇒ 必须红（旧语义在这里返回 0）")

    def test_registration_makes_it_green_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [self.stamped_row(root, frames_dir, "b.png")])
            rc = main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 0, "登记过就该绿 —— 绿要由名册给，不是由「不判」给")
            rc2, out2 = run_main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc2, 0)
            self.assertIn(u"名册无出处=0", out2, "带出处的行不许再被算成手抄")

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
            verdict = judge_drift(changed, added, baseline, current, rows, self.FIXTURE_KEY)
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
                                  load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json")),
                                  self.FIXTURE_KEY)
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
                                  load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json")),
                                  self.FIXTURE_KEY)
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
                              [self.row("x.png"), self.row("y.png", kind="added")], self.FIXTURE_KEY)
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

class MachineDimensionTests(DriftFixture):
    """R584 / BACKLOG 658：登记的键收成 (机器, 帧)，基线带署名。

    动机是一条实测：runner 自己印 `倍率=1.0x`、本机同一帧是 1440×1040（名义 720×520 的两倍），
    而它拿本机烤的那份工作基线比时 `FRAME_BASELINE_CHANGED=356` —— **每一帧都不同**。
    上一版没有机器字段，于是本机那 8 行事实上在给任何机器的漂移背书放行；
    反过来把整条判据在第二台机器上判红又是一张没法逐张处置的红。两条都不许。
    """

    def test_a_foreign_row_does_not_bless_the_local_drift(self):
        """纯函数那一半：只有「这台机器那一行」能放行这一帧。"""
        baseline, current = {"b.png": "9"}, {"b.png": "2"}
        other = judge_drift(["b.png"], [], baseline, current,
                            [self.row("b.png", machine="local:other")], self.FIXTURE_KEY)
        self.assertEqual(other["unregistered"], ["b.png"], "他机行不许豁免本机的漂移")
        self.assertEqual((other["registered"], other["mine"], other["foreign"]), (0, 0, 1))
        mine = judge_drift(["b.png"], [], baseline, current,
                           [self.row("b.png")], self.FIXTURE_KEY)
        self.assertEqual((mine["registered"], mine["unregistered"], mine["mine"], mine["foreign"]),
                         (1, [], 1, 0), "同一行换个机器字段就该从放行变成不放行")

    def test_end_to_end_a_foreign_row_does_not_mute_the_local_drift(self):
        """端到端那一半：只测纯函数会漏掉「门有没有真把机器传进判定」。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [self.row("b.png", machine="local:other")])
            rc, out = run_main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 1, "他机行放行本机漂移 ⇒ 必须红（这就是上一版那个洞）")
            self.assertIn(u"他机行=1", out)
            self.assertIn(u"未登记=1", out)
            self.assertIn(u"FRAME_BASELINE_RESULT=red", out)

    def test_row_without_machine_field_is_red_and_names_the_row(self):
        """缺 `machine` 字段不许当成「适用所有机器」：那是本机给全局背书。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            bad = self.row("b.png")
            bad.pop("machine")
            self.registry(root, [bad])
            rc, out = run_main(["check", frames_dir, "--repo-root", root])
            self.assertNotEqual(rc, 0, "缺机器字段的行必须让门退非 0")
            self.assertIn(u"名册缺机器  b.png", out, "红要指名是哪一行，否则下一轮只能整册重读")
            self.assertIn(u"缺机器1", out)

    def test_foreign_row_alone_is_counted_but_not_red(self):
        """他机行（本机此刻不漂）只报数不判 —— 与陈旧行同一族，「不判」也得有证人。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            self.registry(root, [self.stamped_row(root, frames_dir, "b.png"),
                                 self.row("a.png", machine="local:other")])
            rc, out = run_main(["check", frames_dir, "--repo-root", root])
            self.assertEqual(rc, 0, "别的机器登记过 a.png 不等于本机那行写错了")
            self.assertIn(u"他机行=1", out)
            self.assertIn(u"陈旧行=0", out, "他机行不该被算成本机的陈旧行")

    def test_baseline_from_another_machine_is_not_judged_but_reports_the_count(self):
        """署名不符 ⇒ 变帧维度**具名不判**：数目照报、出路照印，但这一维不拦门。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            write_baseline(manifest_path(root), load_baseline(manifest_path(root)),
                           machine="local:other")     # 同一批哈希，换个署名
            self.registry(root, [])                    # 一台都不许拿空名册放行
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 0, "这台机器没有义务为别人的基线判漂移")
            self.assertIn(u"判=不判", out)
            # 值槽走 sanitize_machine（只抹标点、大小写照留）⇒ 逐字键在表头，通道值无空格无冒号
            self.assertIn(u"FRAME_BASELINE_DRIFT_NOT_JUDGED=baseline-owned-by:local_other", out)
            self.assertIn(u"基线署名=local:other", out, "表头那一行必须还能读到逐字的键")
            self.assertIn(u"变帧=1", out, "不判也要报数：把 356 张这类数藏起来就是重新变成「没人判」")
            self.assertIn(u"未登记（不判）=1", out, "数不许靠措辞变小（R565 那一族），标签里必须带着「不判」")
            self.assertIn(u"未登记不判", out, "拦路明细里不许出现一个不参与拦路的数字")
            self.assertIn(u"出路", out)
            self.assertIn(u"by_machine/%s.json" % sanitize_machine(self.FIXTURE_KEY), out)

    def test_missing_frames_are_still_judged_when_drift_is_not(self):
        """不判只豁免「变帧」这一维：夹具不再产出一帧与机器无关，照红。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            write_baseline(manifest_path(root), load_baseline(manifest_path(root)),
                           machine="local:other")
            os.remove(os.path.join(frames_dir, "c.png"))
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 1, "署名不符不许把缺席一起赦掉（⑷ 那一族：skip 型出口要自带负半证人）")
            self.assertIn(u"缺席1", out)
            self.assertIn(u"FRAME_BASELINE_RESULT=red", out)

    def test_unsigned_baseline_is_not_judged_and_is_named_as_unsigned(self):
        """没署名 ≠ 适用所有机器：它得被读成「不知道这是谁的产物」。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            path = manifest_path(root)
            document = dict(load_baseline_document(path))
            document["machine"] = ""
            write_baseline(path, document["frames"], machine="")
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 0)
            self.assertIn(u"FRAME_BASELINE_DRIFT_NOT_JUDGED=baseline-unsigned", out)
            self.assertIn(u"基线署名=（未署名）", out)

    def test_a_machine_with_its_own_baseline_gets_judged(self):
        """不判不是永久出口：这台机器一旦有自己的基线（by_machine/），它的漂移就归它判。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            drifted = dict(collect(frames_dir))
            for name in drifted:
                drifted[name] = "f" * 64
            write_baseline(machine_baseline_path(root, self.FIXTURE_KEY), drifted,
                           machine=self.FIXTURE_KEY)
            self.registry(root, [])
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 1, "有了自己的基线还一帧不登记 ⇒ 必须红")
            self.assertIn(u"FRAME_BASELINE_AGAINST=by_machine:%s" % self.FIXTURE_KEY, out)
            self.assertIn(u"判=判", out)
            self.assertIn(u"未登记=3", out)

    def test_by_machine_file_whose_signature_disagrees_with_its_name_is_an_error(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            write_baseline(machine_baseline_path(root, self.FIXTURE_KEY), collect(frames_dir),
                           machine="local:other")
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 2, "文件名说一台、里面署另一台 ⇒ 这份东西不可信，谁也不判")
            self.assertIn(u"自相矛盾", out)

    def test_sanitize_keeps_case_so_two_letterings_are_two_files(self):
        """657 的咬口在这里：只抹标点可以，抹大小写就会把两份键 join 成一台。"""
        self.assertEqual(sanitize_machine(self.FIXTURE_KEY), "local_fixture_machine")
        self.assertNotEqual(sanitize_machine("local:MacBook-Air.local"),
                            sanitize_machine("local:macbook-air.local"),
                            "两份只差大小写的键必须落到两个文件名上（BACKLOG 657）")

    def test_not_judged_channel_value_carries_no_bare_space(self):
        """R565 那一族：含裸空格的通道值会打死解析它的尺；逐字值留在表头那一行。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.setup(root)
            write_baseline(manifest_path(root), load_baseline(manifest_path(root)),
                           machine="local:My Air")
            rc, out = run_main(["check", frames_dir, "--against", "working", "--repo-root", root])
            self.assertEqual(rc, 0)
            line = [l for l in out.splitlines() if u"FRAME_BASELINE_DRIFT_NOT_JUDGED=" in l][0]
            self.assertNotIn(" ", line.split(u"=", 1)[1], "通道值那一格不许有空格：%r" % line)
            self.assertIn(u"基线署名=local:My Air", out, "表头要能读到逐字的键，包括空格")

    def test_python_machine_key_implementations_agree(self):
        """这台仓库里 python 侧有三份 machine_key（本文件、motion_floor_gate、test_surface_left_axes）。
        它们**必须**同字 —— 否则按机器登记的名册会各认各的机器。Swift 那份只差大小写，
        已由 BACKLOG 657 具名、且只与本文件写的行 join，不与这里三份互认。
        """
        from scripts.motion_floor_gate import machine_key as floor_key
        from scripts.tests.test_surface_left_axes import machine_key as axis_key
        for env in ({}, {"GITHUB_ACTIONS": "true"}, {"GITHUB_ACTIONS": "TRUE"}):
            saved = dict(os.environ)
            os.environ.update(env)
            os.environ.pop("MOTION_FLOOR_MACHINE_KEY", None)
            os.environ.pop("LEFT_AXIS_MACHINE_KEY", None)
            try:
                self.assertEqual(machine_key(), floor_key(), "两份实现漂移：%r" % env)
                self.assertEqual(machine_key(), axis_key(), "三份实现漂移：%r" % env)
            finally:
                os.environ.clear()
                os.environ.update(saved)

    def test_the_committed_baseline_is_signed_and_rows_match_its_owner(self):
        """盘上那两份必须自洽：基线有署名、每一行都有 machine、且 machine 就是署名的那台。
        ⚠ 这条**不读宿主**（R565：写死本机口径的守卫在 runner 上注定红），只对账两份文件自己。
        """
        repo_root = Path(__file__).resolve().parents[2]
        document = load_baseline_document(os.path.join(repo_root, BASELINE_RELATIVE))
        owner = baseline_owner(document)
        self.assertTrue(owner, "docs/frame_baseline.json 没署名 ⇒ 变帧维度在谁那里都不判，等于把洞留回来")
        rows = load_drift_registry(drift_registry_path(repo_root))
        self.assertTrue(rows, "盘上名册不该是空的（空名册 = 那 8 张又没人判）")
        for row in rows:
            self.assertTrue(row["machine"], "登记行缺机器：%s" % row["frame"])
            self.assertEqual(row["machine"], owner,
                             "行上写的机器与基线署名不符（%s vs %s）⇒ 这一行在给谁背书？" % (row["machine"], owner))

class RemedyDriveTests(unittest.TestCase):
    """R585 / 658 的前置：**印给读者的那条出路必须真做得到**。

    上一轮的证人（`test_a_machine_with_its_own_baseline_gets_judged`）是手摆文件 ⇒
    它测的是"文件名对了会怎么走"，测不到"照 stdout 印的那条命令跑一遍到底落不落在那个文件里"
    —— 那一族叫「对照只测正则不测流水线」。本卷的正臂是：**把那一行原文里的命令抽出来、只把
    占位的帧目录换成真目录，然后原样跑**。负臂是：**照旧那条不带 `--for-machine` 的命令跑完，
    必须仍然 `判=不判`**（否则"两条命令有区别"这句话就没证人）。
    ⚠ 一律用 `MOTION_FLOOR_MACHINE_KEY` 钉机器键（既有约定），测的是"另一台"这一支，
      不读宿主、不改这台机器的任何全局外观。
    """

    SCRIPT = os.path.join(str(Path(__file__).resolve().parents[2]), "scripts", "frame_baseline.py")
    OWNER = u"local:owner-machine"
    OTHER = u"local:other-machine"

    def build(self, root, owner=None):
        """一份**别人**烤的工作基线 + 这台"别的机器"拍出来的漂移帧。

        `owner` 要能改：证伪那一族测的是"本机对自己的行"，那时基线必须署名为**正在跑的那台**，
        否则门先落在 `判=不判` 上，证伪那一支根本没被执行（红对格才许改期望，这里是夹具署错了主）。
        """
        frames_dir = os.path.join(root, "frames")
        os.mkdir(frames_dir)
        make_frame(frames_dir, "a.png", b"1")
        make_frame(frames_dir, "b.png", b"2")
        baseline = dict(collect(frames_dir))
        baseline["b.png"] = "0" * 64
        write_baseline(manifest_path(root), baseline, machine=owner or self.OWNER)
        return frames_dir

    def run_cli(self, argv, machine):
        import subprocess
        env = dict(os.environ)
        env["MOTION_FLOOR_MACHINE_KEY"] = machine
        proc = subprocess.Popen([sys.executable, self.SCRIPT] + argv, cwd=str(Path(__file__).resolve().parents[2]),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                universal_newlines=True)
        out, _ = proc.communicate(timeout=300)
        return proc.returncode, out

    def remedy_command(self, out):
        """从 stdout 的「出路」那一行里抽出它印的命令（只把占位符换成真目录，别的字一律不改）。"""
        for line in out.splitlines():
            if u"出路" not in line:
                continue
            quoted = re.findall(u"`([^`]*frame_baseline\.py[^`]*)`", line)
            if quoted:
                return quoted[0]
        raise AssertionError("出路那一行里没抽到命令：%r" % out[-400:])

    def test_printed_remedy_flips_the_verdict_to_judged(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            rc, out = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], self.OTHER)
            self.assertEqual(rc, 0, "不判那一支不该拦门")
            self.assertIn(u"判=不判", out)
            cmd = self.remedy_command(out)
            self.assertIn("--for-machine", cmd,
                          u"印出来的出路必须带着真能落笔的那个旗标；少了它这句话就是假的（658 追记）")
            real = cmd.replace(u"<那一台的帧目录>", frames_dir)
            argv = real.split()[2:]                      # 丢掉 `python3` 与脚本路径，只留参数
            # ⚠ 印出来的那条命令是**相对仓库根**写的，本身不带 `--repo-root`：
            #   第一版我没补这一句，结果这一趟直接落到真仓库，写出了一份假的
            #   `docs/frame_baselines/by_machine/local_other_machine.json`（自伤，已删）。
            #   夹具根目录是测试自己的参数，补它不改变那条命令的语义。
            argv = argv + ["--repo-root", root]
            rc2, out2 = self.run_cli(argv, self.OTHER)
            self.assertEqual(rc2, 0, "出路那条命令跑完必须成功：%s" % out2[-300:])
            self.assertIn(u"FRAME_BASELINE_MACHINE_BASELINE=", out2)
            self.assertTrue(os.path.exists(machine_baseline_path(root, self.OTHER)),
                            "命令说好写 by_machine/<本机键>.json ⇒ 文件必须真在那儿")
            rc3, out3 = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], self.OTHER)
            self.assertIn(u"判=判", out3, "第二次读必须翻成判（这就是 658 出路 ⑵ 的前置）")
            self.assertIn(u"FRAME_BASELINE_AGAINST=by_machine:%s" % self.OTHER, out3)

    def test_plain_update_still_leaves_it_not_judged(self):
        """负臂：不带 `--for-machine` 的那条命令**不许**顺手产出逐机器基线。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            rc, out = self.run_cli(["update", frames_dir, "--repo-root", root], self.OTHER)
            self.assertEqual(rc, 0)
            self.assertFalse(os.path.exists(machine_baseline_path(root, self.OTHER)),
                             "旧命令一旦也开始写 by_machine/，上面那条正臂就失去对照 ⇒ 这一格先红")
            rc2, out2 = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], self.OTHER)
            # 这条不是"出路做不到"的证据，而是另一件事：`update` 会把**工作基线**改署给跑它的那台。
            # 那正是 655 的重烤归用户的原因（谁跑谁拥有那份共享基线），不是本轮要修的形状。
            self.assertIn(u"FRAME_BASELINE_OWNER=%s" % self.OTHER, out2,
                          u"跑 update 的那台会拿走工作基线的署名 ⇒ 这一格要把这件事写清楚，别藏进断言里")
            self.assertIn(u"FRAME_BASELINE_CHANGED=0", out2)
            self.assertFalse(os.path.exists(machine_baseline_path(root, self.OTHER)))

    def test_register_drift_stamps_the_running_machine_and_provenance(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root,
                                    u"--reason", u"合成：这一张在别的机器上确实漂", u"--ticket", u"655"],
                                   self.OTHER)
            self.assertEqual(rc, 0, out[-300:])
            self.assertIn(u"FRAME_BASELINE_REGISTER=1", out)
            rows = load_drift_registry(os.path.join(root, "docs", "frame_drift_registry.json"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["machine"], self.OTHER, "键只能取运行时那台，命令行里没有 --machine 的口子")
            self.assertTrue((rows[0].get("observed") or {}).get("frame_sha"), "登记必须带出处")
            self.assertTrue((rows[0].get("observed") or {}).get("baseline_sha"))

    def test_register_drift_refuses_an_empty_reason_or_ticket(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            for argv in ([u"--reason", u"   ", u"--ticket", u"655"], [u"--ticket", u"655"]):
                rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root] + argv, self.OTHER)
                self.assertEqual(rc, 2, "空理由/空单号不算登记 ⇒ 退 2：%s" % out[-200:])
            self.assertFalse(os.path.exists(os.path.join(root, "docs", "frame_drift_registry.json")),
                             "拒绝的时候一行都不许落盘")

    def test_register_drift_has_no_machine_flag(self):
        """`--machine` 这种"我自己说是哪台"的口子必须不存在（否则 env 就是免检通道）。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root,
                                    "--machine", self.OWNER, u"--reason", u"x", u"--ticket", u"655"], self.OTHER)
            self.assertNotEqual(rc, 0, "argparse 必须把它当未知参数")
            self.assertIn(u"unrecognized", out.lower())

    def test_hand_copied_row_without_provenance_is_red_and_named(self):
        """手抄一行（有 machine、没 observed）⇒ 门红并点名：那正是"洗掉未登记而一朵红都不许有"的形状。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root, owner=self.OTHER)
            rows = [{"frame": "b.png", "kind": "changed", "machine": self.OTHER,
                     "reason": u"手抄的：这一行没有出处", "ticket": u"655"}]
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with io.open(os.path.join(root, "docs", "frame_drift_registry.json"), "w", encoding="utf-8") as h:
                h.write(json.dumps({"schema": 1, "rows": rows}, ensure_ascii=False))
            rc, out = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], self.OTHER)
            self.assertEqual(rc, 1, "本机行没出处 ⇒ 这一行分不清是谁写的，不许拿它豁免")
            self.assertIn(u"名册无出处  b.png", out)
            self.assertIn(u"无出处1", out)

    def test_row_whose_provenance_does_not_match_this_run_is_red(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root, owner=self.OTHER)
            rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root,
                                    u"--reason", u"合成：带出处的登记", u"--ticket", u"655"], self.OTHER)
            self.assertEqual(rc, 0, out[-200:])
            path = os.path.join(root, "docs", "frame_drift_registry.json")
            doc = json.load(io.open(path, encoding="utf-8"))
            doc["rows"][0]["observed"]["frame_sha"] = "e" * 64      # 冒充"我看过这一张"
            with io.open(path, "w", encoding="utf-8") as h:
                h.write(json.dumps(doc, ensure_ascii=False))
            rc2, out2 = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], self.OTHER)
            self.assertEqual(rc2, 1, "出处对不上就是手抄/过期，不许当登记用")
            self.assertIn(u"出处对不上  b.png", out2)

    def test_foreign_rows_are_not_falsified_by_this_machine(self):
        """本机不证伪他机行（本机没有那一台的帧），但数目照报、也不许拦门。"""
        baseline = {"b.png": "0" * 64}
        current = {"b.png": "2"}
        rows = [{"frame": "z.png", "kind": "changed", "machine": self.OWNER,
                 "reason": u"别人那台的登记", "ticket": u"655", "observed": None}]
        verdict = judge_drift(["b.png"], [], baseline, current, rows, self.OTHER,
                              verify_provenance(rows, self.OTHER, current, baseline_digest(baseline)))
        self.assertEqual(verdict["no_proof"], [], "他机行不进本机的出处判定")
        self.assertEqual(verdict["foreign"], 1)

    def test_restamp_keeps_the_human_note_and_appends_once(self):
        """R585 自伤：第一次 --restamp 把 R583 那句「本名册不是重烤基线的替代品」冲掉了。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            registry = os.path.join(root, "docs", "frame_drift_registry.json")
            with io.open(registry, "w", encoding="utf-8") as h:
                h.write(json.dumps({"schema": 1, "note": u"人写的原文：本名册不是重烤基线的替代品。", "rows": [
                    {"frame": "b.png", "kind": "changed", "machine": self.OTHER,
                     "reason": u"合成", "ticket": u"655"}]}, ensure_ascii=False))
            rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root, "--restamp"], self.OTHER)
            self.assertEqual(rc, 0, out[-200:])
            note = json.load(io.open(registry, encoding="utf-8"))["note"]
            self.assertIn(u"本名册不是重烤基线的替代品", note, "人写的原文不许被生成器覆盖")
            self.assertEqual(note.count(u"observed"), 1, "新句只许补一次（重跑不许越堆越多）")

    def test_the_committed_registry_rows_carry_provenance(self):
        """盘上那 8 行必须都带出处，且 `written_by_machine` 与行上的机器同一台。"""
        repo_root = Path(__file__).resolve().parents[2]
        path = os.path.join(str(repo_root), DRIFT_REGISTRY_RELATIVE)
        doc = json.load(io.open(path, encoding="utf-8"))
        rows = doc["rows"]
        self.assertTrue(rows)
        for row in rows:
            proof = row.get("observed")
            self.assertIsInstance(proof, dict, "%s 缺出处" % row["frame"])
            self.assertTrue(len(str(proof.get("frame_sha"))) == 64, "%s 的帧哈希不像 sha256" % row["frame"])
            self.assertTrue(len(str(proof.get("baseline_sha"))) == 64)
            self.assertEqual(row["machine"], doc.get("written_by_machine"))

    def test_a_hand_copied_github_runner_row_is_red_on_that_machine(self):
        """派单 ② 的正臂，照**真实流水线**搭：runner 先有自己的基线，再手抄一行冒充它观测的。

        顺序不能反：`判=不判` 那一支本来就不拦门（上一版我把场景搭在它上面，于是那一格假绿）。
        真流水线是 ① `update --for-machine`（模拟 runner）⇒ ② 那一台真的漂了一张 ⇒ 门红在未登记；
        ③ 手抄一行 `machine=github-runner` 把未登记洗成 0 ⇒ 出处必须被证伪，红要留下来。
        模拟一律走既有约定 `MOTION_FLOOR_MACHINE_KEY=github-runner`，不改这台机器的任何全局外观。
        """
        runner = u"github-runner"
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root, owner=self.OTHER)
            rc, out = self.run_cli(["update", frames_dir, "--for-machine", "--repo-root", root], runner)
            self.assertEqual(rc, 0, out[-200:])
            make_frame(frames_dir, "b.png", b"9")          # 那一台之后真的漂了
            rc2, out2 = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], runner)
            self.assertIn(u"FRAME_BASELINE_AGAINST=by_machine:%s" % runner, out2)
            self.assertIn(u"判=判", out2, "有了自己的基线就归它判 ⇒ 不判那一支不能当挡箭牌")
            self.assertEqual(rc2, 1, "漂了一张而名册没有 runner 的行 ⇒ 必须红在未登记")
            self.assertIn(u"未登记=1", out2)
            path = os.path.join(root, "docs", "frame_drift_registry.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with io.open(path, "w", encoding="utf-8") as h:
                h.write(json.dumps({"schema": 1, "rows": [
                    {"frame": "b.png", "kind": "changed", "machine": runner,
                     "reason": u"手抄：这一行不是那一台观测的", "ticket": u"655",
                     "observed": {"frame_sha": "a" * 64, "baseline_sha": "b" * 64}}]},
                                   ensure_ascii=False))
            rc3, out3 = self.run_cli(["check", frames_dir, "--against", "working", "--repo-root", root], runner)
            self.assertEqual(rc3, 1, u"手抄行把未登记洗成 0 之后，红必须由**出处**接住：%s" % out3[-320:])
            self.assertIn(u"未登记=0", out3)
            self.assertIn(u"出处对不上  b.png", out3)
            self.assertIn(u"出处不符1", out3)

    def test_the_committed_note_grows_only_by_appending(self):
        """名册 note 的规矩：**保留人写原文 + 只在尾部追加**，重排也算改原文。

        R585 第一次 `--restamp` 把 R583 那句「本名册不是重烤基线的替代品」冲掉；补回时又把
        R584 那句挪到了它后面 ⇒ 监工指出"顺序变了"。这一格把"只许追加"钉成会红的证人。
        """
        import subprocess
        repo_root = str(Path(__file__).resolve().parents[2])
        shown = subprocess.Popen(["git", "show", "HEAD:" + DRIFT_REGISTRY_RELATIVE], cwd=repo_root,
                                 stdout=subprocess.PIPE, universal_newlines=True).communicate()[0]
        head_note = json.loads(shown)["note"]
        now_note = json.load(io.open(os.path.join(repo_root, DRIFT_REGISTRY_RELATIVE),
                                     encoding="utf-8"))["note"]
        self.assertTrue(now_note.startswith(head_note),
                        u"名册 note 不是 HEAD 那份的前缀延伸 ⇒ 有人重排或改写了人写的原文")
        self.assertEqual(now_note.count(u"重烤基线"), head_note.count(u"重烤基线"),
                        u"那句「不是重烤基线的替代品」被复制或删改了")

    def test_register_drift_leaves_the_working_baseline_untouched(self):
        """655 的护栏：补登记**只改名册**，工作基线那份一个字节都不许动。"""
        with tempfile.TemporaryDirectory() as root:
            frames_dir = self.build(root, owner=self.OTHER)
            before = io.open(manifest_path(root), encoding="utf-8").read()
            rc, out = self.run_cli(["register-drift", frames_dir, "--repo-root", root,
                                    u"--reason", u"合成：只补名册", u"--ticket", u"655"], self.OTHER)
            self.assertEqual(rc, 0, out[-200:])
            self.assertEqual(io.open(manifest_path(root), encoding="utf-8").read(), before,
                             u"register-drift 碰了工作基线 ⇒ 那就成了绕过 655 的重烤通道")

if __name__ == "__main__":
    unittest.main()


try:
    from PIL import Image as _PILImage
    NO_PIL = False
except ImportError:                                  # 与两态差尺那一卷同一口径：缺库要点名，不许静默绿
    _PILImage = None
    NO_PIL = True


class BakeProvenanceTests(unittest.TestCase):
    """R586 / 靶 A：**名册有出处了，基线那一侧当时还没有** —— 这一类把它补成会红的。

    为什么这一格值得单独有（监工现读 `write_baseline` 的文档字段只有
    `schema/count/machine/note/frames`）：`update --for-machine` 拿**刚捕的那批帧**烤一份
    `by_machine/<键>.json`，下一次 `check` 必然 `变帧=0` —— 而"没人改过界面"与"刚用它自烤了一遍"
    在输出里**逐字相同**。上一轮给名册每行补了 `observed`（手抄行从此可证伪），
    同一个洞在基线这一侧却没有同一个药。
    三个字段全部**运行时观测**（`git rev-parse HEAD` / 台账轮次标题 / PNG 头 vs 帧名里的逻辑尺寸），
    命令行一个口子都不开 ⇒ 出处不是声明，是观测。
    """

    SCRIPT = os.path.join(str(Path(__file__).resolve().parents[2]), "scripts", "frame_baseline.py")
    KEY = u"local:bake-fixture"

    def git(self, root, *args):
        import subprocess
        base = ["git", "-C", root, "-c", "commit.gpgsign=false", "-c", "advice.detachedHead=false"]
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
        proc = subprocess.Popen(base + ["-c", "core.autocrlf=false"] + list(args),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                universal_newlines=True)
        out, _ = proc.communicate(timeout=120)
        self.assertEqual(0, proc.returncode, out[-400:])
        return out.strip()

    def make_repo(self, root):
        """真 git 仓：`baked_from_commit` 要由 `git rev-parse HEAD` 取 ⇒ 这一格的隔离前提是真的有一笔。"""
        self.git(root, "init", "-q")
        io.open(os.path.join(root, "seed.txt"), "w", encoding="utf-8").write(u"seed\n")
        io.open(os.path.join(root, "AGENT_STATE.md"), "w", encoding="utf-8").write(u"## R500 状态（占位）\n")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "c1")
        return self.git(root, "rev-parse", "HEAD")

    def frames(self, root, names=(u"a-10x10-dark.png", u"b-10x10-light.png")):
        d = os.path.join(root, "frames")
        if not os.path.isdir(d):
            os.mkdir(d)
        for n in names:
            make_frame(d, n, n.encode("utf-8"))
        return d

    def cli(self, argv, machine=KEY):
        import subprocess
        env = dict(os.environ)
        env["MOTION_FLOOR_MACHINE_KEY"] = machine
        proc = subprocess.Popen([sys.executable, self.SCRIPT] + argv,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                universal_newlines=True)
        out, _ = proc.communicate(timeout=300)
        return proc.returncode, out

    # ── 落笔那一侧 ──────────────────────────────────────────────────────────
    def test_update_for_machine_stamps_the_three_runtime_observations(self):
        with tempfile.TemporaryDirectory() as root:
            sha = self.make_repo(root)
            frames_dir = self.frames(root)
            rc, out = self.cli([u"update", frames_dir, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            doc = json.load(io.open(machine_baseline_path(root, self.KEY), encoding="utf-8"))
            self.assertEqual(sha, doc["baked_from_commit"], u"commit 那一格必须等于 git 自己说的 HEAD")
            self.assertEqual(u"R501", doc["baked_by_round"],
                             u"轮次由台账标题派生（仓里那份写着 `## R500 状态` ⇒ 正在烤它的是 R501）")
            self.assertIn(u"FRAME_BASELINE_BAKE 出处=有", out,
                          u"落笔那一趟要把**回读**出来的出处印出来，不是印我以为写进去的那些")

    def test_no_flag_can_name_the_bake(self):
        """手填口子一律不存在：出处一旦被声明，它就退化成措辞（R585「登记是账，不是措辞」同族）。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            frames_dir = self.frames(root)
            for flag in (u"--baked-by", u"--commit", u"--baked-from-commit", u"--capture-scale"):
                rc, out = self.cli([u"update", frames_dir, u"--for-machine",
                                    u"--repo-root", root, flag, u"R1"])
                self.assertEqual(2, rc, u"%s 竟然被接受了：\n%s" % (flag, out[-400:]))

    # ── 判定那一侧：同批自烤 ────────────────────────────────────────────────
    def test_same_bake_is_named_and_blocks_even_when_nothing_drifted(self):
        """这一格的靶心：`变帧=0` 而基线就是拿这批帧烤的 ⇒ 不许签绿，要具名并**照报数**。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            frames_dir = self.frames(root)
            rc, out = self.cli([u"update", frames_dir, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            rc, out = self.cli([u"check", frames_dir, u"--against", u"working", u"--repo-root", root])
            self.assertEqual(1, rc, u"同批自烤却给了绿：\n" + out[-700:])
            self.assertIn(u"FRAME_BASELINE_SAME_BAKE=", out, out[-700:])
            self.assertIn(u"FRAME_BASELINE_CHANGED=0", out, u"数照报 —— 具名不是把读数藏起来")
            self.assertIn(u"同批1", out, out[-700:])

    def test_a_different_commit_judges_the_dimension_normally(self):
        """负半证人①：基线与被判帧出自**不同**一笔 ⇒ 不许有 SAME_BAKE 那一格，也不许多拦路。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            frames_dir = self.frames(root)
            rc, out = self.cli([u"update", frames_dir, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            io.open(os.path.join(root, "seed.txt"), "a", encoding="utf-8").write(u"second\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-q", "-m", "c2")
            rc, out = self.cli([u"check", frames_dir, u"--against", u"working", u"--repo-root", root])
            self.assertNotIn(u"FRAME_BASELINE_SAME_BAKE=", out,
                             u"下一笔判上一笔烤的基线，本来就是正常流向，不该被这一格拦：%s" % out[-700:])
            self.assertIn(u"同批0", out, out[-700:])

    def test_same_bake_never_masks_an_existing_red(self):
        """负半证人②：同批 + 真有未登记漂移 ⇒ 两朵红都要在，具名不许把已有的红改成「不判」。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            frames_dir = self.frames(root)
            rc, out = self.cli([u"update", frames_dir, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            # 不新增一笔 ⇒ HEAD 仍等于 baked_from_commit（同批成立），而此刻 a 帧自己变了
            make_frame(frames_dir, u"a-10x10-dark.png", b"different")
            rc, out = self.cli([u"check", frames_dir, u"--against", u"working", u"--repo-root", root])
            self.assertEqual(1, rc, out[-700:])
            self.assertIn(u"未登记  a-10x10-dark.png", out, u"同批那一格不许吃掉未登记的那朵")
            self.assertIn(u"FRAME_BASELINE_SAME_BAKE=", out, out[-700:])
            self.assertIn(u"同批1", out, out[-700:])

    # ── 旧文档那一侧 ────────────────────────────────────────────────────────
    def test_a_legacy_baseline_still_judges_and_is_named_not_treated_as_new(self):
        """③ 的证人：R586 之前烤的文档没有那三个字段 ⇒ 形状照读、判定照旧，但必须**具名**。

        ⚠ 这一格**必须跑在真 git 仓里**：临时目录不是仓 ⇒ `HEAD` 取不到 ⇒ "缺出处就默认成此刻这一笔"
        那个坏法会退化成"默认成空串"，什么数都不改 ⇒ 这一格对 M1543 天生瞎（本轮刀的输出教的）。
        """
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)          # 有了 HEAD，"默认成这一笔"才是一个能被抓到的动作
            frames_dir = self.frames(root)
            baseline = dict(collect(frames_dir))
            baseline[u"b-10x10-light.png"] = u"0" * 64
            write_baseline(manifest_path(root), baseline, machine=self.KEY)   # 2 参 = 旧形状
            doc = json.load(io.open(manifest_path(root), encoding="utf-8"))
            self.assertEqual(u"", str(doc.get("baked_from_commit") or ""), u"旧文档不该被偷偷补字段")
            rc, out = self.cli([u"check", frames_dir, u"--against", u"working", u"--repo-root", root])
            self.assertIn(u"FRAME_BASELINE_BAKE 出处=无", out, out[-700:])
            self.assertIn(u"FRAME_BASELINE_BAKE_PROVENANCE=absent", out, out[-700:])
            self.assertIn(u"FRAME_BASELINE_RESULT=red", out, u"旧文档照判：那一帧是真漂移")
            self.assertIn(u"同批0", out, u"「不知道」不许被读成「同批」，那是另一种伪造：%s" % out[-700:])
            self.assertIn(u"FRAME_BASELINE_DRIFT ", out, u"判定那一维照旧要有人判，具名不许把判本身撤掉")

    def test_missing_provenance_is_never_defaulted_to_this_commit(self):
        """反面对照：缺字段默认成 HEAD 的话，每一旧文档都会被判成同批自烤 ⇒ 把红改成另一种红。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            frames_dir = self.frames(root)
            write_baseline(manifest_path(root), collect(frames_dir), machine=self.KEY)
            rc, out = self.cli([u"check", frames_dir, u"--against", u"working", u"--repo-root", root])
            self.assertNotIn(u"FRAME_BASELINE_SAME_BAKE=", out,
                             u"没有出处就被判成同批 ⇒ 这一支会把所有旧基线一起误红：%s" % out[-700:])

    @unittest.skipIf(NO_PIL, "缺 PIL：造不出能被 IHDR 读出尺寸的帧，这一格要能被点名")
    def test_scale_mismatch_is_a_reading_not_a_new_blocker(self):
        """倍率那一格的目的：R584 那 356 张变帧的成因（本机 2x 烤、runner 1x 判）从此由基线自己说出来。"""
        with tempfile.TemporaryDirectory() as root:
            self.make_repo(root)
            big = os.path.join(root, "frames_2x")
            os.mkdir(big)
            for n in (u"a-10x10-dark.png", u"b-10x10-light.png"):
                _PILImage.new("RGB", (20, 20), (10, 10, 10)).save(os.path.join(big, n))
            rc, out = self.cli([u"update", big, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            small = os.path.join(root, "frames_1x")
            os.mkdir(small)
            for n in (u"a-10x10-dark.png", u"b-10x10-light.png"):
                _PILImage.new("RGB", (10, 10), (10, 10, 10)).save(os.path.join(small, n))
            # 先让 HEAD 走一笔（否则同一批帧既触发倍率对照又触发同批自烤，两件事混在一条红里，
            # 这一格就不是单边的证人（R577 那一课：一臂里捆两件产品各自会做的事，永远判不出必需是哪一件））
            io.open(os.path.join(root, "seed.txt"), "a", encoding="utf-8").write(u"second\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-q", "-m", "c2")
            rc, out = self.cli([u"check", small, u"--against", u"working", u"--repo-root", root])
            self.assertIn(u"FRAME_BASELINE_SCALE_MISMATCH 基线=2.00x 当轮=1.00x", out, out[-700:])
            self.assertIn(u"同批0", out, out[-700:])
            self.assertEqual(1, rc, u"两批帧的哈希本来就不同（2x 与 1x），未登记那一朵该红：%s" % out[-700:])
            blockers = int(re.search(r"拦路=(\d+)", out).group(1))
            unregistered = int(re.search(r"未登记(\d+|不判)", out).group(1))
            self.assertEqual(unregistered, blockers,
                             u"倍率不合这一格只许报数，不许进拦路：拦路=%d 未登记=%d\n%s" % (blockers, unregistered, out[-700:]))


class BakeSnapshotInheritanceTests(unittest.TestCase):
    """`snapshot()` 冻的是"那份基线对应的那一笔"，不是"此刻跑 snapshot 的这一笔"。

    没有这一格的话，发布快照会把出处改写成跑它的那台机器/那一笔 ⇒ 逐版本基线从此说不出
    自己是哪个版本烤的，而 `--against release` 那一支判的正是这件事。
    """

    def test_snapshot_inherits_the_source_provenance(self):
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, u"a.png", b"1")
            write_baseline(manifest_path(root), collect(frames_dir), machine=u"local:snap-owner",
                           repo_root=root, frames_dir=frames_dir)
            src = json.load(io.open(manifest_path(root), encoding="utf-8"))
            # 临时目录不是 git 仓 ⇒ commit 该是空串（"不知道"），这一格顺便钉住那条口径
            self.assertEqual(u"", src["baked_from_commit"], u"取不到 HEAD 时不许猜一个数")
            target = snapshot(root, u"9.9.9")
            self.assertTrue(target and os.path.exists(target), target)
            doc = json.load(io.open(target, encoding="utf-8"))
            self.assertEqual(src["machine"], doc["machine"], u"署名照继承")
            for key in ("baked_from_commit", "baked_by_round", "capture_scale"):
                self.assertEqual(src[key], doc[key], key)


class PrintedFlagTests(unittest.TestCase):
    """R586 / ⑨·7 的证人：本轮新写的那条「出路」里我抄错了一个旗标值。

    派单 ③ 的原话就是这一族的定义：**印出来的东西就是契约**（R585 那一整轮都在还这一笔债），
    而我在本轮新加的 SAME_BAKE 出路行里写了 `--against release`，真值是 `latest-release`
    ⇒ 照那句话跑的人会得到 argparse 的 usage 错（退 2），和 R584 那条空头支票同形。
    所以这里不是加一句注释，而是加两格会红的证人。
    """

    SCRIPT = os.path.join(str(Path(__file__).resolve().parents[2]), "scripts", "frame_baseline.py")

    def choices_from_argparse(self):
        """从**源码**里读 `--against` 的 choices，而不是从我记忆里读（抄常量那一族）。"""
        src = io.open(self.SCRIPT, encoding="utf-8").read()
        m = re.search(r'add_argument\("--against"[^)]*choices=\[([^\]]+)\]', src)
        self.assertTrue(m, "读不到 --against 的 choices ⇒ 这一格没有可对账的对象")
        return {s.strip().strip('"\'') for s in m.group(1).split(",")}

    def printed_strings(self, path):
        """只取**真的被 print 出去**的字符串常量（AST 级），docstring 与注释一律不算。

        上一稿这里扫的是整份源码文本，于是我在 docstring 里描述"上一轮写错了哪个值"也被抓成红 ——
        那是守卫读错了对象（R580 那一课的形状：读到 1 要区分「对象在」与「字面在」）。
        判据的契约是"读者会看到什么"，所以范围就是 print 的参数。
        """
        tree = ast.parse(io.open(path, encoding="utf-8").read(), filename=path)
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                for arg in node.args:
                    for lit in ast.walk(arg):
                        if isinstance(lit, ast.Constant) and isinstance(lit.value, str):
                            out.append(lit.value)
                        elif isinstance(lit, ast.JoinedStr):          # f-string 的各段
                            for part in ast.walk(lit):
                                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                                    out.append(part.value)
        return out

    def test_every_printed_against_value_is_a_real_choice(self):
        printed = u"\n".join(self.printed_strings(self.SCRIPT))
        values = set(re.findall(r"--against ([A-Za-z][A-Za-z0-9_-]*)", printed))
        self.assertTrue(values, u"print 里一条 `--against …` 都没印 ⇒ 这一格的扫描对象读错了")
        choices = self.choices_from_argparse()
        bad = sorted(values - choices)
        self.assertEqual([], bad, u"印给读者的旗标值 argparse 不认：%s（可用：%s）" % (bad, sorted(choices)))

    def test_the_release_branch_actually_runs(self):
        """出路说了改判哪一支，就得真跑一次那一支：退 2（用法错）与退 0/1（判定）是两种东西。"""
        import subprocess
        with tempfile.TemporaryDirectory() as root:
            frames_dir = os.path.join(root, "frames")
            os.mkdir(frames_dir)
            make_frame(frames_dir, u"a.png", b"1")
            os.makedirs(os.path.join(root, "docs", "frame_baselines"))
            write_baseline(os.path.join(root, "docs", "frame_baselines", "v9.9.9.json"),
                           collect(frames_dir), machine=u"local:snap-owner")
            env = dict(os.environ)
            env["MOTION_FLOOR_MACHINE_KEY"] = u"local:printer"
            proc = subprocess.Popen([sys.executable, self.SCRIPT, u"check", frames_dir,
                                     u"--against", u"latest-release", u"--repo-root", root],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                    universal_newlines=True)
            out, _ = proc.communicate(timeout=300)
            self.assertNotEqual(2, proc.returncode, u"用法错（argparse 不认这个值）：\n%s" % out[-400:])
            self.assertIn(u"FRAME_BASELINE_AGAINST=v9.9.9", out,
                          u"那一支跑到了别的东西上（说明它没读逐版本基线）：\n%s" % out[-400:])


class ScaleDistributionTests(unittest.TestCase):
    """R587 / 靶 A：`capture_scale` 取众数没有并列检测 ⇒ 混批会印一个抛硬币来的倍率。

    监工现读到的三处形状（本轮逐一变成读数）：
      ① `mode = max(set(ratios), key=ratios.count)` 没有任何并列检测；
      ② 两轴推不出同一倍率的帧 `bad += 1` **之后仍 `ratios.append`**；
      ③ `_bad` 在两个调用点被下划线丢掉 ⇒ 这个量算了却没人看。
    """

    SCRIPT = os.path.join(str(Path(__file__).resolve().parents[2]), "scripts", "frame_baseline.py")
    KEY = u"local:scale-fixture"

    def dir_with(self, root, spec):
        """spec = [(逻辑宽, 逻辑高, 倍率), ...] ⇒ 造出帧名与像素尺寸一致/不一致的帧。"""
        from PIL import Image
        d = os.path.join(root, "frames_%d" % len(os.listdir(root)))
        os.mkdir(d)
        for k, (lx, ly, scale) in enumerate(spec):
            px, py = int(lx * scale), int(ly * scale)
            name = u"shot-%dx%d-dark.png" % (lx, ly)
            if name in os.listdir(d):                     # 同尺寸的帧要换个前缀
                name = u"shot%d-%dx%d-dark.png" % (k, lx, ly)
            Image.new("RGB", (px, py), (9, 9, 9)).save(os.path.join(d, name))
        return d

    def info(self, d):
        from scripts.frame_baseline import capture_scale
        return capture_scale(d)

    def test_a_mixed_batch_still_names_the_majority_but_the_distribution_is_printed(self):
        """355:1 那种混批：众数仍是 2.00x（这不是猜），但**分布必须一起交出去**。"""
        with tempfile.TemporaryDirectory() as root:
            d = self.dir_with(root, [(10, 10, 2.0)] * 3 + [(20, 20, 1.0)])
            info = self.info(d)
            self.assertEqual(u"2.00x", info["scale"])
            self.assertEqual(u"2.00x:3,1.00x:1", u",".join(u"%s:%d" % kv for kv in info["dist"]))
            self.assertEqual(u"ok", info["reason"])

    def test_a_tie_is_not_reported_as_a_confident_scale(self):
        """两档各半 ⇒ 上一版印的是 `set` 遍历顺序决定的那一个；现在一律「不知道」。"""
        with tempfile.TemporaryDirectory() as root:
            d = self.dir_with(root, [(10, 10, 2.0), (12, 12, 2.0), (10, 10, 1.0), (12, 12, 1.0)])
            info = self.info(d)
            self.assertEqual(u"", info["scale"], u"并列还印一个看起来确定的倍率：%r" % (info,))
            self.assertEqual(u"tie", info["reason"])
            self.assertEqual(2, len(info["dist"]), info["dist"])

    def test_unreadable_png_is_counted_as_bad_not_dropped(self):
        """`px<=0`（读不出 IHDR）那一条 `bad += 1` 当时**没有任何证人** ⇒ M1549 落下去是空刀。

        这一格补的就是那位证人：一张名字合法、内容不是 PNG 的文件。
        记下来是因为它暴露了一件事：`mutate_needle_precheck.py` 只保证 needle 命中一次，
        不保证那条分支有人测 ⇒ 落刀之前除了问「我只动了一边吗」，还要问「这一边有证人吗」。
        """
        with tempfile.TemporaryDirectory() as root:
            d = os.path.join(root, "frames_unreadable")
            os.mkdir(d)
            from PIL import Image
            Image.new("RGB", (20, 20), (9, 9, 9)).save(os.path.join(d, u"ok-10x10-dark.png"))
            io.open(os.path.join(d, u"broken-10x10-dark.png"), "wb").write(b"not a png at all")
            info = self.info(d)
            self.assertEqual(1, info["bad"], u"读不出像素尺寸的那张必须进 bad：%r" % (info,))
            self.assertEqual(1, info["frames"], u"能读出的那一张照常进分布：%r" % (info,))
            self.assertEqual(u"ok", info["reason"], info)

    def test_sizeless_frame_names_are_counted_not_silently_skipped(self):
        """**合成**一个没有逻辑尺寸段的帧名 ⇒ 它进不了倍率，但必须照报数。

        名字的来历要说清：`settings-general-min-orphan-dark.png` **不在**现读语料里（现读那一批帧全部带
        `-宽x高-档` 那一段，真实存在的近似名是 `general-min-orphan-640x540-dark.png`）。
        我第一版把这个编出来的名字当成"现读确有这种命名"写进了 print 与注释 —— 那是本轮顺账要防的
        同一种空头支票（措辞里的名字不存在），本轮自己扫出来并撤掉了。
        这一格的来历同样诚实：它是被测试自己挖出来的 —— 上一稿我把这种形状放进"两侧应给出同一个档"
        的名单里，结果倍率正则匹配不到它 ⇒ 旧版 `capture_scale` 对它是**静默 continue**，
        分布的分母少了多少张没人知道（`bad` 之外第二种"算了却没人看"）。
        """
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            d = os.path.join(root, "frames_sizeless")
            os.mkdir(d)
            Image.new("RGB", (20, 20), (9, 9, 9)).save(os.path.join(d, u"a-10x10-dark.png"))
            Image.new("RGB", (16, 8), (9, 9, 9)).save(os.path.join(d, u"settings-general-min-orphan-dark.png"))
            info = self.info(d)
            self.assertEqual(1, info["frames"], info)
            self.assertEqual(1, info.get("sizeless"), u"没有尺寸段的那张必须被计数：%r" % (info,))
            self.assertEqual(u"ok", info["reason"], u"只有一张可量时不该报并列")

    def test_inconsistent_frames_are_counted_and_reported(self):
        """`bad` 不许再被 `_bad` 丢掉：两轴推不出同一倍率的那张要照报。"""
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            d = os.path.join(root, "frames_bad")
            os.mkdir(d)
            Image.new("RGB", (20, 20), (9, 9, 9)).save(os.path.join(d, u"a-10x10-dark.png"))   # 2x 对 x 与 y
            Image.new("RGB", (20, 10), (9, 9, 9)).save(os.path.join(d, u"b-10x10-dark.png"))   # x 是 2x、y 是 1x ⇒ bad
            info = self.info(d)
            self.assertEqual(1, info["bad"], info)
            self.assertEqual(2, info["frames"], u"bad 帧以前也照进分布；现在两边都要看得见")

    def test_check_prints_tie_and_bad_instead_of_a_confident_scale(self):
        """端到端：拿一批并列的帧跑 `check` ⇒ 印 `SCALE_TIE` + `SCALE_NOT_RUN=tie…`，不印 `倍率=2.00x`。"""
        import subprocess
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            docs = os.path.join(root, "docs")
            os.makedirs(docs)
            frames = os.path.join(root, "frames")
            os.mkdir(frames)
            for n, size in ((u"a-10x10-dark.png", (20, 20)), (u"b-30x30-dark.png", (30, 30))):
                Image.new("RGB", size, (9, 9, 9)).save(os.path.join(frames, n))
            # 先烤一份基线（这批是并列的 ⇒ 烤出来的 scale 该是"不知道"）
            env = dict(os.environ)
            env["MOTION_FLOOR_MACHINE_KEY"] = self.KEY
            def run(argv):
                proc = subprocess.Popen([sys.executable, self.SCRIPT] + argv,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                        universal_newlines=True)
                out, _ = proc.communicate(timeout=300)
                return proc.returncode, out
            rc, out = run([u"update", frames, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-400:])
            doc = json.load(io.open(os.path.join(docs, "frame_baselines", "by_machine",
                                                 "local_scale_fixture.json"), encoding="utf-8"))
            self.assertEqual(u"", doc["capture_scale"], u"并列批次不该被烤成一个确定倍率：%r" % doc)
            self.assertEqual(u"tie", doc["capture_scale_reason"], doc)
            # 分布是**排序后**的：先按计数降序、再按倍率名升序 ⇒ 并列时也有确定形状，
            # 不再依赖 `set` 的遍历顺序（那正是上一版印出抛硬币倍率的根）。
            self.assertEqual(u"1.00x:1,2.00x:1", doc["capture_scale_dist"], doc)
            rc, out = run([u"check", frames, u"--against", u"working", u"--repo-root", root])
            self.assertIn(u"FRAME_BASELINE_SCALE_TIE", out, out[-600:])
            self.assertIn(u"FRAME_BASELINE_SCALE_NOT_RUN=tie", out, out[-600:])
            self.assertNotIn(u"倍率=2.00x", out, out[-600:])
            self.assertIn(u"原因=tie", out, out[-600:])

    FOUR_SCALE_CELLS = (u"FRAME_BASELINE_SCALE_BASELINE_UNKNOWN", u"FRAME_BASELINE_SCALE_MATCH",
                        u"FRAME_BASELINE_SCALE_MISMATCH", u"FRAME_BASELINE_SCALE_NOT_RUN")

    def _run_check(self, frames, root, baseline_scale, baseline_reason):
        """烤一份基线、把它的 `capture_scale` 改成要测的那一边、再跑 `check` ⇒ 返回印出来的正文。"""
        saved = os.environ.get("MOTION_FLOOR_MACHINE_KEY")
        os.environ["MOTION_FLOOR_MACHINE_KEY"] = self.KEY
        try:
            rc, out = run_main([u"update", frames, u"--for-machine", u"--repo-root", root])
            self.assertEqual(0, rc, out[-500:])
            path = os.path.join(root, "docs", "frame_baselines", "by_machine",
                                "local_scale_fixture.json")
            doc = json.load(io.open(path, encoding="utf-8"))
            doc["capture_scale"] = baseline_scale
            doc["capture_scale_reason"] = baseline_reason
            io.open(path, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))
            rc, out = run_main([u"check", frames, u"--against", u"working", u"--repo-root", root])
            return out
        finally:
            os.environ.pop("MOTION_FLOOR_MACHINE_KEY", None)
            if saved is not None:
                os.environ["MOTION_FLOOR_MACHINE_KEY"] = saved

    def test_the_four_scale_cells_each_have_exactly_one_named_line(self):
        """R589 / 靶 A ①：`bake["scale"] × current_scale` 这四格**每格都要有自己的读数行**，而且互斥。

        旧写法是两条互不相干的 `if` ⇒「当轮说得出、基线说不出」与「两边都说得出且相等」两格一行都不印，
        于是"静默"与"量了没问题"在输出里逐字相同 —— R588 ⓪·3 在 runner 的门那一步现读到
        `FRAME_BASELINE_SCALE*` 行数=0 而同一行里 `FRAME_BASELINE_BAKE … 倍率=（不知道）`，就是这一格。
        这一格判的是**穷尽性**（四格各有名），不是四行内容的对错，所以它同时钉住：
        少一条分支 ⇒ 那格没人出声 ⇒ 红；把兜底 `else` 摘掉 ⇒ 相等那格又变静默 ⇒ 红。
        """
        cases = [
            (u"当轮说得出、基线说不出（旧文档 / 混烤）",
             [(10, 10, 2.0)], u"", u"", u"FRAME_BASELINE_SCALE_BASELINE_UNKNOWN"),
            (u"两边都说得出且相等 ⇒ 兜底分支",
             [(10, 10, 2.0)], u"2.00x", u"ok", u"FRAME_BASELINE_SCALE_MATCH"),
            (u"两边都说得出且不等",
             [(10, 10, 1.0)], u"2.00x", u"ok", u"FRAME_BASELINE_SCALE_MISMATCH"),
            (u"当轮说不出（并列批次），基线说得出",
             [(10, 10, 2.0), (30, 30, 1.0)], u"2.00x", u"ok", u"FRAME_BASELINE_SCALE_NOT_RUN"),
        ]
        for title, spec, base_scale, base_reason, expect in cases:
            with self.subTest(title=title):
                with tempfile.TemporaryDirectory() as root:
                    frames = self.dir_with(root, spec)
                    out = self._run_check(frames, root, base_scale, base_reason)
                    fired = [c for c in self.FOUR_SCALE_CELLS if c in out]
                    self.assertEqual([expect], fired,
                                     u"这一格应该且只应该印一条：%s；实际 %s\n正文尾部：%s"
                                     % (expect, fired, out[-900:]))

    def test_channel_roster_matches_what_is_actually_printed(self):
        """通道名册要**双向**对账（R579 那一族：名册要靠被引用才红，单向只红一半）。

        加一条通道必须同时改名册 —— 这是"新造一条不判出口"的唯一入口，
        于是它至少要在这一格里被看见一次；名册里留着一条不再印的通道也算红（腐烂的名册会掩护新通道）。
        """
        found = set()
        for lit in self.printed_of(self.SCRIPT):
            found |= set(re.findall(r"FRAME_BASELINE_[A-Z_]+", lit))
        self.assertTrue(found, u"print 里一条 FRAME_BASELINE_* 通道都没有 ⇒ 扫描器读错了对象")
        missing = sorted(found - set(self.KNOWN_CHANNELS))
        stale = sorted(set(self.KNOWN_CHANNELS) - found)
        self.assertEqual([], missing, u"这些通道被印出来但没登记进名册：%s" % missing)
        self.assertEqual([], stale, u"名册里这些通道已经不再被印：%s（要么删要么改回 print）" % stale)

    def printed_of(self, path):
        tree = __import__("ast").parse(io.open(path, encoding="utf-8").read(), filename=path)
        out = []
        for node in __import__("ast").walk(tree):
            if isinstance(node, __import__("ast").Call) and isinstance(node.func, __import__("ast").Name) \
                    and node.func.id == "print":
                for lit in __import__("ast").walk(node):
                    if isinstance(lit, __import__("ast").Constant) and isinstance(lit.value, str):
                        out.append(lit.value)
        return out

    KNOWN_CHANNELS = frozenset([
        u"FRAME_BASELINE_AGAINST", u"FRAME_BASELINE_MACHINE", u"FRAME_BASELINE_OWNER",
        u"FRAME_BASELINE_COMPARED", u"FRAME_BASELINE_ALLOW_MISSING", u"FRAME_BASELINE_CHANGED",
        u"FRAME_BASELINE_MISSING", u"FRAME_BASELINE_ADDED", u"FRAME_BASELINE_BAKE",
        u"FRAME_BASELINE_BAKE_PROVENANCE", u"FRAME_BASELINE_SAME_BAKE",
        u"FRAME_BASELINE_SCALE_MISMATCH", u"FRAME_BASELINE_SCALE_NOT_RUN",
        u"FRAME_BASELINE_SCALE_BASELINE_UNKNOWN", u"FRAME_BASELINE_SCALE_MATCH",
        u"FRAME_BASELINE_SCALE_TIE", u"FRAME_BASELINE_SCALE_BAD",
        u"FRAME_BASELINE_SCALE_SIZELESS",
        u"FRAME_BASELINE_DRIFT", u"FRAME_BASELINE_DRIFT_NOT_JUDGED",
        u"FRAME_BASELINE_DRIFT_REGISTRY", u"FRAME_BASELINE_REGISTRY_DIGEST",
        u"FRAME_BASELINE_RESULT", u"FRAME_BASELINE_ERROR", u"FRAME_BASELINE_UPDATED",
        u"FRAME_BASELINE_MACHINE_BASELINE", u"FRAME_BASELINE_REGISTER", u"FRAME_BASELINE_RESTAMP",
        u"FRAME_BASELINE_SNAPSHOT",
    ])
