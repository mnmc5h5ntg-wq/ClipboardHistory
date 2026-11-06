# -*- coding: utf-8 -*-
"""R589 / 靶 B：638② 那道门的判据卷 —— 逐字节副本必须登记、方向要分得开、副本不许当唯一像素证人。

每一格都用**合成语料**（临时目录里两张内容相同的 png），所以：
· 它是正对照的来源 —— 门的 0 必须先在这里被证明"看得见违规"，否则现读那个 0 不算数；
· 它不许被读成"真语料的组数"（真语料那一格由 `docs/frame_identical_pairs.json` 与本轮重捕的帧另判）。
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.identical_frame_witness import (REPO, frame_key, judge, load_roster, main,   # noqa: E402
                                             sha_groups, copy_groups)
from scripts.frame_baseline import machine_key          # noqa: E402

SCRIPTS_DIR = os.path.join(REPO, "scripts")
HARNESS = os.path.join(REPO, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                       "UICaptureHarness.swift")
ROSTER_PATH = os.path.join(REPO, "docs", "frame_identical_pairs.json")


def png_bytes(seed: int) -> bytes:
    """一张最小合法 PNG 的头尾（内容只由 seed 决定 ⇒ seed 相同就是逐字节同一）。"""
    return (b"\x89PNG\r\n\x1a\n" + ("%08x" % seed).encode("ascii"))[:16] + b"|%d" % seed


def make_corpus(root, spec):
    """spec = [(文件名, seed)] ⇒ 落一批 png。"""
    d = os.path.join(root, "shots")
    os.mkdir(d)
    for name, seed in spec:
        with open(os.path.join(d, name), "wb") as handle:
            handle.write(png_bytes(seed))
    return d


def make_roster(root, rows):
    path = os.path.join(root, "roster.json")
    io.open(path, "w", encoding="utf-8").write(json.dumps({"schema": 1, "rows": rows}, ensure_ascii=False))
    return path


def row(a, b, should=u"是", **over):
    base = {"members": [a, b], "should_be_identical": should,
            "cause": u"合成成因（这一格的帧是测试自己造的，不在真语料里）",
            "cause_refs": [u"U-TEST"], "ticket": u"638",
            "observed": {"sha": u"0" * 12, "members": 2, "corpus_frames": 2},
            "registered_by_round": u"R589", "machine": machine_key()}
    base.update(over)
    return base


class RegistrationTests(unittest.TestCase):
    def test_identical_pair_without_a_row_is_red_and_named(self):
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)])
        rc, out = _capture(main, [u"--shots", d, u"--roster", make_roster(self.tmp, []),
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(2, rc, out)                      # 空名册 ⇒ not-run，不许"0 行=全绿"
        self.assertIn(u"IDENTICAL_PAIR_RESULT=not-run", out)
        rows = load_roster(make_roster(self.tmp, [row(u"z-10x10-dark.png", u"y-10x10-dark.png")]))
        copies = copy_groups(sha_groups(d)[1])
        counts, reds = judge(copies, rows, set(x for x in os.listdir(d)))
        self.assertEqual(1, counts["未登记"])
        self.assertIn(u"a-10x10-dark.png + b-10x10-dark.png", reds[0])

    def test_registered_pair_is_green(self):
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)])
        rows = load_roster(make_roster(self.tmp, [row(u"a-10x10-dark.png", u"b-10x10-dark.png")]))
        copies = copy_groups(sha_groups(d)[1])
        counts, reds = judge(copies, rows, set(os.listdir(d)))
        self.assertEqual([], reds, str(counts))
        self.assertEqual(1, counts["同图组"])

    def test_count_of_groups_and_count_of_rows_must_be_equal(self):
        """监工要的那把刀的证人：`同图组 == 名册覆盖` —— 多一张新副本、名册没跟上 ⇒ 红。"""
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7),
                                   (u"c-10x10-dark.png", 9), (u"dd-10x10-dark.png", 9)])
        rows = load_roster(make_roster(self.tmp, [row(u"a-10x10-dark.png", u"b-10x10-dark.png")]))
        copies = copy_groups(sha_groups(d)[1])
        counts, reds = judge(copies, rows, set(os.listdir(d)))
        self.assertEqual(2, counts["同图组"], counts)
        self.assertEqual(1, counts["名册行"], counts)
        self.assertEqual(1, counts["未登记"], counts)
        self.assertEqual(1, len(reds))

    def test_appearance_twins_are_two_groups_not_one(self):
        """暗/亮各一组 ⇒ 名册要两行。第一版按抹掉色档的键归组，两行塌成一行、loader 当场拒绝。"""
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7),
                                   (u"a-10x10-light.png", 11), (u"b-10x10-light.png", 11)])
        rows = load_roster(make_roster(self.tmp, [
            row(u"a-10x10-dark.png", u"b-10x10-dark.png"),
            row(u"a-10x10-light.png", u"b-10x10-light.png")]))
        copies = copy_groups(sha_groups(d)[1])
        counts, reds = judge(copies, rows, set(os.listdir(d)))
        self.assertEqual([], reds, str(counts))
        self.assertEqual(2, counts["同图组"])
        self.assertEqual(2, counts["夹具键数"], u"键数是抹掉色档之后的数，只许用来说话、不许用来归组")

    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name
        os.mkdir(os.path.join(self.tmp, "empty_scripts"))

    def tearDown(self):
        self._ctx.cleanup()


class DirectionTests(unittest.TestCase):
    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name

    def tearDown(self):
        self._ctx.cleanup()

    def _judge(self, spec, rows):
        d = make_corpus(self.tmp, spec)
        counts, reds = judge(copy_groups(sha_groups(d)[1]), load_roster(make_roster(self.tmp, rows)),
                             set(os.listdir(d)))
        return counts, reds

    def test_should_be_same_but_now_different_is_named_as_drift(self):
        counts, reds = self._judge([(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 8)],
                                   [row(u"a-10x10-dark.png", u"b-10x10-dark.png")])
        self.assertEqual(1, counts["漂了"], counts)
        self.assertIn(u"该相同而不同", reds[0])

    def test_should_differ_but_is_same_is_named_as_a_defect(self):
        counts, reds = self._judge([(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)],
                                   [row(u"a-10x10-dark.png", u"b-10x10-dark.png", should=u"否")])
        self.assertEqual(1, counts["不该相同"], counts)
        self.assertIn(u"不该相同而相同", reds[0])
        self.assertIn(u"状态没画", reds[0])

    def test_the_two_directions_are_not_merged_into_one_message(self):
        """两个方向的成因相反 ⇒ 必须各报各的；同一趟里两格都要出声。"""
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7),
                                   (u"c-10x10-dark.png", 3), (u"dd-10x10-dark.png", 4)])
        rows = load_roster(make_roster(self.tmp, [
            row(u"a-10x10-dark.png", u"b-10x10-dark.png", should=u"否"),
            row(u"c-10x10-dark.png", u"dd-10x10-dark.png", should=u"是")]))
        counts, reds = judge(copy_groups(sha_groups(d)[1]), rows, set(os.listdir(d)))
        self.assertEqual(1, counts["不该相同"], counts)
        self.assertEqual(1, counts["漂了"], counts)
        self.assertEqual(2, len(reds), reds)

    def test_roster_row_naming_a_vanished_frame_is_red(self):
        counts, reds = self._judge([(u"a-10x10-dark.png", 7)],
                                   [row(u"a-10x10-dark.png", u"gone-10x10-dark.png")])
        self.assertEqual(1, counts["名册帧缺失"], counts)
        self.assertIn(u"不在现读语料里", reds[0])


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name

    def tearDown(self):
        self._ctx.cleanup()

    def _must_raise(self, rows, needle):
        path = make_roster(self.tmp, rows)
        with self.assertRaises(ValueError) as got:
            load_roster(path)
        self.assertIn(needle, str(got.exception))

    def test_loader_rejects_missing_cause(self):
        r = row(u"a.png", u"b.png")
        r.pop("cause")
        self._must_raise([r], u"缺字段")

    def test_loader_rejects_empty_cause_text(self):
        self._must_raise([row(u"a.png", u"b.png", cause=u"   ")], u"成因是空的")

    def test_loader_rejects_cause_without_refs(self):
        self._must_raise([row(u"a.png", u"b.png", cause_refs=[])], u"cause_refs")

    def test_loader_rejects_row_without_observed_sha(self):
        self._must_raise([row(u"a.png", u"b.png", observed={})], u"observed.sha")

    def test_loader_rejects_unknown_direction_word(self):
        self._must_raise([row(u"a.png", u"b.png", should=u"也许")], u"should_be_identical")

    def test_loader_rejects_two_rows_for_the_same_group(self):
        self._must_raise([row(u"a.png", u"b.png"), row(u"a.png", u"b.png")], u"同组只准一行")

    def test_loader_rejects_row_without_machine(self):
        """名册是**一台机器**的观测：没有 machine 的行不参与判定，所以缺这一格要在 loader 就红。"""
        r = row(u"a.png", u"b.png")
        r.pop("machine")
        self._must_raise([r], u"缺字段")
        self._must_raise([row(u"a.png", u"b.png", machine=u"")], u"machine")


class MachineTests(unittest.TestCase):
    """658 那一族在这张名册上的对应物：本机没有自己的行 ⇒ 具名不判，不许拿别台的行来判。"""

    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name
        os.mkdir(os.path.join(self.tmp, "empty_scripts"))

    def tearDown(self):
        self._ctx.cleanup()

    def test_rows_from_another_machine_are_not_judged_here(self):
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)])
        roster = make_roster(self.tmp, [row(u"a-10x10-dark.png", u"b-10x10-dark.png",
                                            machine=u"github-runner")])
        rc, out = _capture(main, [u"--shots", d, u"--roster", roster,
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(2, rc, out)
        self.assertIn(u"IDENTICAL_PAIR_RESULT=not-run 本机行=0 他机行=1 本机组=1", out)
        self.assertIn(u"逐字节同图组=1", out)      # 组数照报 —— 不判不等于不说

    def test_this_machines_rows_are_judged(self):
        d = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)])
        roster = make_roster(self.tmp, [row(u"a-10x10-dark.png", u"b-10x10-dark.png")])
        rc, out = _capture(main, [u"--shots", d, u"--roster", roster,
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(0, rc, out)
        self.assertIn(u"IDENTICAL_PAIR_MACHINE 本机=%s 名册本机行=1 他机行=0" % machine_key(), out)


class WitnessTests(unittest.TestCase):
    """R-c：判据若只拿同一组里的副本作证 ⇒ 恒真门，必须红并点名。"""

    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name

    def tearDown(self):
        self._ctx.cleanup()

    def _scripts_with(self, body):
        d = os.path.join(self.tmp, "scripts")
        if not os.path.isdir(d):
            os.mkdir(d)
        io.open(os.path.join(d, "fake_criterion.py"), "w", encoding="utf-8").write(body)
        return d

    def test_criterion_whose_only_witnesses_are_copies_is_red(self):
        rows = load_roster(make_roster(self.tmp, [
            row(u"qa-focus-420x300-dark.png", u"qa-hover-420x300-dark.png")]))
        scripts = self._scripts_with(
            u"# 合成判据\nTARGETS = [u\"qa-focus\", u\"qa-hover\"]\nprint(u\"FAKE 对照=%s\" % TARGETS)\n")
        from scripts.identical_frame_witness import witness_reds
        reds = witness_reds(rows, scripts, os.path.abspath(__file__))
        self.assertEqual(1, len(reds), reds)
        self.assertIn(u"恒真", reds[0])
        self.assertIn(u"qa-focus+qa-hover", reds[0])

    def test_criterion_with_a_third_frame_outside_the_group_is_green(self):
        rows = load_roster(make_roster(self.tmp, [
            row(u"qa-focus-420x300-dark.png", u"qa-hover-420x300-dark.png")]))
        scripts = self._scripts_with(
            u"TARGETS = [u\"qa-focus\", u\"qa-hover\", u\"qc-list\"]\nprint(u\"FAKE\")\n")
        from scripts.identical_frame_witness import witness_reds
        self.assertEqual([], witness_reds(rows, scripts, os.path.abspath(__file__),
                                         corpus_keys=[u"qa-focus", u"qa-hover", u"qc-list"]))

    def test_criterion_using_a_single_copy_is_not_accused(self):
        """引用组里**一张**是允许的（它仍在替那条断言作证）—— 这条负半防的是把名册当成"这些帧不许用"。"""
        rows = load_roster(make_roster(self.tmp, [
            row(u"qa-focus-420x300-dark.png", u"qa-hover-420x300-dark.png")]))
        scripts = self._scripts_with(u"TARGET = u\"qa-focus\"\nprint(u\"FAKE\")\n")
        from scripts.identical_frame_witness import witness_reds
        self.assertEqual([], witness_reds(rows, scripts, os.path.abspath(__file__)))

    def test_plain_words_are_not_mistaken_for_frame_keys(self):
        """键必须带连字符才参与匹配 —— 否则一句 `print("focus")` 就被判成"拿副本作证"，
        那条误伤会把整个名册变成"这些词不许出现在判据里"。"""
        rows = load_roster(make_roster(self.tmp, [
            row(u"qa-focus-420x300-dark.png", u"qa-hover-420x300-dark.png")]))
        scripts = self._scripts_with(u"WORD = u\"focus\"\nprint(u\"FAKE\")\n")
        from scripts.identical_frame_witness import witness_reds
        self.assertEqual([], witness_reds(rows, scripts, os.path.abspath(__file__)))


class NotRunTests(unittest.TestCase):
    def setUp(self):
        self._ctx = tempfile.TemporaryDirectory()
        self.tmp = self._ctx.name
        os.mkdir(os.path.join(self.tmp, "empty_scripts"))
        self.roster = make_roster(self.tmp, [row(u"a-10x10-dark.png", u"b-10x10-dark.png")])

    def tearDown(self):
        self._ctx.cleanup()

    def test_missing_shots_dir_refuses_instead_of_passing(self):
        rc, out = _capture(main, [u"--shots", os.path.join(self.tmp, "nope"),
                                  u"--roster", self.roster,
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(2, rc, out)
        self.assertIn(u"IDENTICAL_PAIR_REFUSED=no-shots", out)

    def test_empty_shots_dir_refuses(self):
        d = os.path.join(self.tmp, "shots")
        os.mkdir(d)
        rc, out = _capture(main, [u"--shots", d, u"--roster", self.roster,
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(2, rc, out)
        self.assertIn(u"IDENTICAL_PAIR_REFUSED=no-png", out)

    def test_missing_roster_refuses(self):
        rc, out = _capture(main, [u"--shots", make_corpus(self.tmp, [(u"a.png", 1)]),
                                  u"--roster", os.path.join(self.tmp, "nope.json"),
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts")])
        self.assertEqual(2, rc, out)
        self.assertIn(u"IDENTICAL_PAIR_REFUSED=roster-missing", out)

    def test_control_switch_reports_whether_the_scanner_can_see_violations(self):
        """`--fixture-dir` 那一格是**盲不盲**的读数：合成语料里放一组没登记的副本 ⇒ 正对照必须>0。"""
        good = make_corpus(self.tmp, [(u"a-10x10-dark.png", 7), (u"b-10x10-dark.png", 7)])
        bad = os.path.join(self.tmp, "control")
        os.mkdir(bad)
        for n, seed in ((u"new-copy-10x10-dark.png", 21), (u"new-copy2-10x10-dark.png", 21)):
            with open(os.path.join(bad, n), "wb") as handle:
                handle.write(png_bytes(seed))
        rc, out = _capture(main, [u"--shots", good, u"--roster", self.roster,
                                  u"--scripts", os.path.join(self.tmp, "empty_scripts"),
                                  u"--fixture-dir", bad])
        self.assertEqual(0, rc, out)
        self.assertIn(u"IDENTICAL_CONTROL 合成语料组=1 判成红=", out)
        self.assertIn(u"新增副本没登记：new-copy-10x10-dark.png + new-copy2-10x10-dark.png", out)


class CommittedRosterTests(unittest.TestCase):
    """盘上那一份名册自己也要被问一遍 —— 合成语料的绿不等于真语料登记齐了。"""

    def test_committed_roster_rows_and_directions(self):
        rows = load_roster(ROSTER_PATH)
        self.assertEqual(8, len(rows), u"现读那一批是 8 组（U-2440 / R588 两次同数）")
        for r in rows:
            self.assertEqual(u"638", r[u"ticket"], r)
            self.assertEqual(u"是", r[u"should_be_identical"],
                             u"逐组排除过：没有一组是产品缺陷，所以名册里不该出现「否」%r" % (r,))
            self.assertEqual(u"R589", r[u"registered_by_round"], r)
            self.assertTrue(any(x.startswith(u"U-2440") or x.startswith(u"R") for x in r[u"cause_refs"]), r)

    def test_committed_roster_members_are_declared_in_the_harness(self):
        """每一行的帧名要能在夹具源码里找到那颗声明/引用 —— 否则名册登记的是一个不存在的键。"""
        src = io.open(HARNESS, encoding="utf-8").read()
        for r in load_roster(ROSTER_PATH):
            for m in r[u"members"]:
                key = frame_key(m)
                self.assertIn(u'"%s' % key, src,
                              u"名册里的 %s 在夹具源码里找不到字面量（键拼错或夹具改名）" % key)

    def test_frame_key_strips_only_the_appearance_tail(self):
        self.assertEqual(u"content-paused-idle", frame_key(u"content-paused-idle-750x560-dark.png"))
        self.assertEqual(u"detail-3-files-row0", frame_key(u"detail-3-files-row0-720x520-light.png"))
        self.assertEqual(u"general-min-orphan-legacy",
                         frame_key(u"general-min-orphan-legacy-640x540-dark.png"))

    def test_working_corpus_either_judges_or_names_why_it_did_not(self):
        """真语料那一格：**有帧就判组数==名册行，没帧就具名「没跑」** —— 两个分支都是断言，没有 skip。

        这一格是 runner 与本机的分水岭：CI 把捕获步骤那批帧交给电池（`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci`），
        本机若不设这个变量就只能读到 `REFUSED=no-shots`。把"本机没帧"读成"名册没问题"就是 R470 那一族。
        """
        shots = os.environ.get(u"CLIPBOARD_HISTORY_UI_SHOTS") or u""
        argv = [u"--shots", shots, u"--roster", ROSTER_PATH, u"--scripts", SCRIPTS_DIR]
        rc, out = _capture(main, argv)
        if not shots or not os.path.isdir(shots):
            self.assertEqual(2, rc, out)
            self.assertIn(u"IDENTICAL_PAIR_REFUSED=no-shots", out)
            return
        self.assertIn(u"IDENTICAL_PAIR_RESULT=ok", out, out[-1500:])
        counts = dict((k, int(v)) for k, v in
                      re.findall(u"(未登记|漂了|名册帧缺失|不该相同|唯一证人)=(\\d+)", out))
        self.assertEqual({k: 0 for k in counts}, counts, out[-1500:])
        self.assertEqual(8, int(re.search(u"逐字节同图组=(\\d+)", out).group(1)),
                         u"真语料现在应当仍是 8 组（U-2440 / R588 / 本笔三次同数）")


def _capture(fn, argv):
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(argv)
    return rc, buf.getvalue()


if __name__ == "__main__":
    unittest.main()
