#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACKLOG 353 的门：「产品面连续零改动轮数」这一格只能由 `scripts/product_streak.py` 派生。

R298 现读的账目事故（不是假想）：同一件事在台账里有四种短语形状，数出四个数（7 / 8 / 「第十一轮」），
而报告 §13 那句「上一次落到 Sources 的改动是 R263 的收藏星字形墨」被 `git log` 当场驳回 ——
最后一次是 2f8b1e0（R290 / 第 289 轮），它之后还有 R275、R289、R290 三笔动过产品目录的说法全部作废。
按短语数只能数出「我在正文里写没写过这句话」，数不出「产品有没有动」。

这一支钉四件事：
① 派生本身不许静默失败 —— `derive()` 有 problems 就直接把原文摆出来红；
② 台账那两格的数**必须等于**派生值，**且同一行必须引用本命令** —— 数对了但没引用同样红
   （那说明这个数是抄来的，抄来的数下一轮就烂，正是 353 要防的形状）；
③ 数**缺席**算红，不算通过（R140 的空对账：`X=0` 形式的通过要先问分母是不是空的）；
④ STATE 新节在上，当前轮只认**第一**节（R223 那一课：取末会读到最老一节）。

正对照全部走**合成文本**，不碰真台账；期望值取派生值做偏移，红的原因是「与派生值不等」而不是偏移量本身。
真台账那两格由最后一格直接跑 CLI `--check` 签字。
"""
import io
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import product_streak as ps  # noqa: E402

REPORT_HEAD = u"# 报告\n\n## 13. 收尾\n\n"
STATE_HEAD = u"## R299 状态（第 298 轮 / Round 296 · 2026-10-23）\n\n"


def read(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def report_cell(n, cite=True):
    tail = u"（现读 `python3 scripts/product_streak.py`）" if cite else u"（按 ITERATION 短语数）"
    return u"- **产品面**：产品面连续零改动轮数 = **%d**%s\n" % (n, tail)


def state_cell(n, cite=True):
    tail = u"（现读 `scripts/product_streak.py` 的 streak）" if cite else u"（连续多轮 0 产品改动）"
    return u"产品文件 0 个，连续零改动 **%d** 轮%s。\n" % (n, tail)


class ProductStreakCellTests(unittest.TestCase):

    def setUp(self):
        self.info, self.problems = ps.derive()
        # ① 派生本身：有 problems 就没什么可对账的，让原文把尺坏在哪印出来。
        self.assertEqual(self.problems, [], u"git 派生这一格失败：%s" % (self.problems,))
        self.assertIsInstance(self.info["streak"], int)
        self.assertEqual(self.info["sources_after"].strip(), u"0")

    def test_ledger_cells_agree_with_git(self):
        probs = ps.check_ledger(read(u"AGENT_FINAL_REPORT.md"),
                                read(u"AGENT_STATE.md"), self.info["streak"])
        self.assertEqual(probs, [], u"台账那一格与 git 派生不符：%s" % (probs,))

    def test_wrong_number_is_red_even_with_citation(self):
        bad = self.info["streak"] + 3
        probs = ps.check_ledger(REPORT_HEAD + report_cell(bad),
                                STATE_HEAD + state_cell(bad), self.info["streak"])
        self.assertTrue(any(u"git 派生" in p for p in probs), probs)
        self.assertTrue(any(u"STATE" in p for p in probs), probs)

    def test_hand_copied_number_without_citation_is_red(self):
        # 数写对了但没引用本命令 ⇒ 仍然红：这一格要的是「只能由该命令派生」，不是「碰巧对上」。
        probs = ps.check_ledger(REPORT_HEAD + report_cell(self.info["streak"], cite=False),
                                STATE_HEAD + state_cell(self.info["streak"], cite=False),
                                self.info["streak"])
        self.assertEqual(len(probs), 2, probs)
        for p in probs:
            self.assertIn(u"手抄", p)

    def test_absent_cell_is_red_not_pass(self):
        # 两篇都空：**没有一格的文本与每一格都写对的文本必须不同形**（R140 的空对账）。
        # STATE 那一格在解析不到当前轮节时直接返回，所以这里恰好两朵红 —— 数量也钉住，
        # 免得「只报了一种成因」把另一种吞掉（R90 那一族：读不到结论有几种成因而闸门只印一种）。
        probs = ps.check_ledger(u"# 报告\n\n什么也没写\n", u"## 没有状态节\n", self.info["streak"])
        self.assertEqual(len(probs), 2, probs)
        self.assertIn(u"算红", probs[0])
        self.assertIn(u"无从判定", probs[1])
        # 有节、但节里没那一格 ⇒ 必须换成第二朵红，不能被"节找到了"喂饱成绿。
        probs = ps.check_ledger(REPORT_HEAD + report_cell(self.info["streak"]),
                                STATE_HEAD + u"本轮没写这一格。\n", self.info["streak"])
        self.assertEqual(len(probs), 1, probs)
        self.assertIn(u"AGENT_STATE.md", probs[0])

    def test_two_candidates_must_be_the_same_number(self):
        text = REPORT_HEAD + report_cell(self.info["streak"]) + report_cell(self.info["streak"] + 1)
        probs = ps.check_ledger(text, STATE_HEAD + state_cell(self.info["streak"]),
                                self.info["streak"])
        self.assertTrue(any(u"同一格" in p for p in probs), probs)

    def test_state_reads_the_newest_section_first(self):
        # STATE 新节在上：当前轮写对了、后面那节历史写着旧数 ⇒ 不许因为「文件里能找到旧数」而红，
        # 也不许反过来拿 [-1] 读到最老一节（那样历史里每一个旧数都能把它顶红，判据就废了）。
        newest = STATE_HEAD + state_cell(self.info["streak"])
        older = u"\n## R260 状态（第 259 轮）\n\n连续零改动 **11** 轮（历史说法，不作数）。\n"
        probs = ps.check_ledger(REPORT_HEAD + report_cell(self.info["streak"]),
                                newest + older, self.info["streak"])
        self.assertEqual(probs, [], probs)
        self.assertIn(u"R299", ps._state_top_section(newest + older))

    def test_subject_label_parser_rejects_ambiguous_and_missing(self):
        # derive() 的两条拒绝路径靠这两种输入成立：无标签 / 多标签都不许变成一个数。
        self.assertEqual(ps.rounds_in_subject(u"R290 收尾：把一维拆成两层两尺"), [])
        self.assertEqual(ps.rounds_in_subject(u"R298（第 297 轮 / Round 295）：锚点腐烂"), [297])
        self.assertEqual(ps.rounds_in_subject(u"引用第 103 轮，本轮第 297 轮"), [103, 297])

    def test_cli_check_signs_the_real_ledger(self):
        proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "product_streak.py"),
                                 u"--check"], cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out = proc.communicate()[0].decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn(u"PRODUCT_STREAK_LEDGER_OK", out)
        self.assertIn(u"streak=%d" % self.info["streak"], out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
