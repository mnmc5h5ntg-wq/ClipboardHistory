# -*- coding: utf-8 -*-
"""R309：`scripts/ledger_readings.py` 的尺真身与两半对照（BACKLOG 348 的「数字对不对」那一格）。

形状照 `test_product_streak_cell.py`：判定写成纯函数，用例喂**已知答案**的合成日志，
并且正反两半各判一次 —— 只测「坏了要红」而不测「没坏要放过」，那道门可以靠永远红蒙过去。
最后一格拿真产物（本轮验证链日志）作证人；日志不在盘上就 skip 并写清原因，不许算通过。
"""
import io
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import ledger_readings as lr  # noqa: E402

CHAIN = "/tmp/r308_chain.log"


def log(capture_first=True):
    """合成一份验证链日志：全量卷 934 / 44 skip / 0，捕帧卷 92 / 4 skip / 0。"""
    parts = [u"### PRECHECK\nNEEDLE_PRECHECK tables=1 bad=0\n"]
    if capture_first:
        parts.append(u"### CAPTURE\n\t Executed 92 tests, with 4 tests skipped and 0 failures (0 unexpected)\n")
    parts.append(u"### FULL SUITE\n\t Executed 934 tests, with 44 tests skipped and 3 failures (0 unexpected)\n")
    parts.append(u"### FULL SUITE 第二遍（修完夹具之后）\n"
                 u"\t Executed 934 tests, with 44 tests skipped and 0 failures (0 unexpected)\n")
    if not capture_first:
        parts.append(u"### CAPTURE\n\t Executed 92 tests, with 4 tests skipped and 0 failures (0 unexpected)\n")
    return u"".join(parts)


class SectionSlicingTests(unittest.TestCase):

    def test_the_body_lives_in_the_same_chunk_as_the_heading(self):
        """`re.split` 只吃分隔符 ⇒ 小节正文必须在**本块**里取（取下一块就拿到下一节）。"""
        parts = lr.section_parts(log(), u"FULL SUITE")
        self.assertEqual(2, len(parts), u"两跑 FULL SUITE 该切出两块")
        title, body = parts[0]
        self.assertEqual(u"FULL SUITE", title)
        self.assertIn(u"934", body, u"正文没落到本块 ⇒ 切片又取了下一块")
        self.assertNotIn(u"CAPTURE", body, u"正文里混进了下一节的标题")

    def test_a_section_with_two_different_lines_is_ambiguous_not_silently_last(self):
        rows, problems = lr.suite_rows(
            u"### FULL SUITE\nExecuted 934 tests, with 44 tests skipped and 0 failures\n"
            u"Executed 900 tests, with 44 tests skipped and 0 failures\n", u"FULL SUITE")
        self.assertEqual([], rows)
        self.assertEqual([u"LEDGER_READINGS_SECTION_AMBIGUOUS"], [c for c, _ in problems])


class PickFullRunTests(unittest.TestCase):

    def test_the_last_pass_is_taken_and_earlier_red_is_recorded_not_erased(self):
        info, problems = lr.pick_full_run(log())
        self.assertEqual(u"934", info[u"run"], u"全量卷该取 934，读到 %s" % info[u"run"])
        self.assertEqual(u"0", info[u"fail"])
        self.assertEqual(u"FULL SUITE 第二遍（修完夹具之后）", info[u"title"])
        self.assertEqual([(u"FULL SUITE", u"3")], info[u"red_passes"],
                         u"早先那一跑的 3 朵红必须原样留档，不许被最后一跑抹掉")
        self.assertEqual([], problems, u"这份日志没写错，却被判红：%s" % problems)

    def test_positive_control_a_subset_line_taken_as_full_is_named(self):
        """反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。"""
        bad = (u"### OTHER SUITE\nExecuted 934 tests, with 1 tests skipped and 0 failures\n"
               u"### FULL SUITE\nExecuted 92 tests, with 4 tests skipped and 0 failures\n")
        info, problems = lr.pick_full_run(bad)
        self.assertEqual([u"LEDGER_READINGS_SUBSET_TAKEN_AS_FULL"], [c for c, _ in problems],
                         u"抄到子集却不点名 ⇒ 这道闸门是假的")

    def test_missing_suite_section_is_red_not_default_zero(self):
        info, problems = lr.pick_full_run(u"### PRECHECK\nNEEDLE_PRECHECK bad=0\n")
        self.assertIsNone(info[u"run"])
        self.assertEqual([u"LEDGER_READINGS_NO_SUITE_LINE"], [c for c, _ in problems],
                         u"读不到结论行应当算红（R140 的空对账）")

    def test_a_red_last_pass_refuses_even_if_earlier_passes_were_green(self):
        info, problems = lr.pick_full_run(
            u"### FULL SUITE\nExecuted 934 tests, with 44 tests skipped and 0 failures\n"
            u"### FULL SUITE 第二遍\nExecuted 934 tests, with 44 tests skipped and 2 failures\n")
        self.assertIn(u"LEDGER_READINGS_LAST_PASS_RED", [c for c, _ in problems])

    def test_a_line_without_skip_count_is_named_not_read_as_zero(self):
        info, problems = lr.pick_full_run(
            u"### FULL SUITE\nExecuted 934 tests, with 0 failures\n")
        self.assertIsNone(info[u"skip"])
        self.assertIn(u"LEDGER_READINGS_SKIP_MISSING", [c for c, _ in problems],
                      u"「没解析到」与「解析到 0」是两件事")


class RealArtifactTests(unittest.TestCase):

    def test_the_round_chain_log_reads_as_the_ledger_claims(self):
        if not os.path.exists(CHAIN):
            self.skipTest(u"本轮验证链日志 %s 不在盘上（/tmp 会被清）⇒ 这一格没有对象，"
                          u"不许拿合成样本替真产物作证" % CHAIN)
        with io.open(CHAIN, encoding="utf-8", errors="replace") as h:
            text = h.read()
        info, problems = lr.pick_full_run(text)
        self.assertEqual([], problems, u"本轮的真日志被判红：%s" % problems)
        self.assertEqual(2, info[u"pass_count"], u"本轮全量卷跑过两遍")
        self.assertEqual(u"934", info[u"run"])
        self.assertEqual([(u"FULL SUITE", u"3")], info[u"red_passes"])


if __name__ == u"__main__":
    unittest.main()
