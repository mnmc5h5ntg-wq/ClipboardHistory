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
import re
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
        # as-of 口径：streak 是「台账最大节那一轮」的答案，不是「此刻最新产品提交」的答案
        self.assertEqual(self.info["streak"],
                         self.info["ledger_round"] - int(re.search(
                             u"last_round=(\d+)", self.info[u"note"]).group(1)))
        self.assertGreaterEqual(self.info["streak"], 0)

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

    def test_a_streak_cell_is_answered_as_of_its_own_round(self):
        # R300 现读的坑：代码半先提交、台账半后提交。若拿"此刻最新产品提交"去判上一轮写对的格，
        # 会把历史判成假红（与 355 同一族：期望值必须与它问的那一笔同时代）。
        rows = [(u"shaA", 299, u"aaa1111", u"2026-10-23", u"R300 代码半"),
                (u"shaB", 289, u"2f8b1e0", u"2026-10-21", u"R290 代码半"),
                (u"shaC", 263, u"15c6a56", u"2026-10-21", u"R263 代码半")]
        # R334 改口径：分界取**严格小于**本轮的最后一笔产品提交 ⇒ 本轮自己那一笔不算分界。
        # 于是 shaA（第 299 轮自己）被跳过，答案 298 − 289 = 10（旧口径在这里答 0，
        # 而"0"要等 commit 落盘才出现 —— 同一格在提交前后答两个数，就是 R334 撞上的那朵持久红）。
        self.assertEqual((10, u"last=2f8b1e0 last_round=289"), ps.streak_at(299, rows))
        self.assertEqual((9, u"last=2f8b1e0 last_round=289"), ps.streak_at(298, rows))
        # 期望值一律**手算给死**再写进测试（R298 那一课：心算出来的期望会把对的代码判成错的）
        self.assertEqual((8, u"last=2f8b1e0 last_round=289"), ps.streak_at(297, rows))
        self.assertEqual((7, u"last=15c6a56 last_round=263"), ps.streak_at(270, rows))
        # 标签多义/缺失的提交跳过，但不许被当成"没有产品改动"
        noisy = [(u"shaD", None, u"ddd0000", u"2026-10-23", u"没有轮次标签的一笔"),
                 (u"shaB", 289, u"2f8b1e0", u"2026-10-21", u"R290 代码半")]
        self.assertEqual(9, ps.streak_at(298, noisy)[0])
        self.assertEqual((None, u"标签 < 第 300 轮的产品提交一笔都没有（跳过 0 笔标签多义/缺失的）"),
                         ps.streak_at(300, [(u"shaE", 400, u"eee", u"2026-12-31", u"未来的笔")]))

    def test_the_answer_does_not_depend_on_commit_shape(self):
        """同一轮在"本轮那一笔落盘之前 / 之后"必须答同一个数（R334 改口径的理由）。

        仓库里两种提交形状并存：代码半 + 账半两笔（R329…），以及整轮一笔（`117f45d`）。
        旧口径（`≤`）下，两笔形状的轮在写账时本轮那一笔**已在** git ⇒ 答 0；
        一笔形状的轮写账时本轮那一笔**还没在** ⇒ 答 14。于是 R333 那格在它的 commit 落盘之后
        被同一颗尺改判成 0 —— 电池里 12 朵红，而那一句账并没有写错。
        这一格钉的就是"红的原因是口径，不是账"：把本轮自己那一笔拿掉再问，答案不许变。
        """
        with_own = [(u"shaA", 331, u"aaa1111", u"2026-10-25", u"第 331 轮 代码半"),
                    (u"shaB", 318, u"84c5468", u"2026-10-24", u"第 318 轮 代码半")]
        without_own = with_own[1:]
        self.assertEqual(ps.streak_at(331, with_own), ps.streak_at(331, without_own),
                         u"本轮自己那一笔落没落盘改变了答案 ⇒ 口径又依赖提交形状了")
        self.assertEqual((13, u"last=84c5468 last_round=318"), ps.streak_at(331, with_own))
        # 而**下一轮**的分界就是本轮 —— 这一半证明 `<` 不是"永远往前看一格"的偏移错误：
        self.assertEqual((1, u"last=aaa1111 last_round=331"), ps.streak_at(332, with_own))

    def test_the_second_label_source_is_a_derivation_not_a_roster(self):
        """标签的第二个来源：subject 缺「第 N 轮」时，用台账节标题里同一段 U 区间**派生**。

        为什么不是 sha→轮次的手抄表（D-329）：表只买"不红"，买不到"数对" ——
        `product_streak` 会跳过没有标签的那一笔、拿更早的提交当分界，于是 `--streak-for 333`
        在只有豁免的版本里答 **15**，而真值是 **1**（`117f45d` 就是第 332 轮）。
        四种歧义各给 None（不许猜），且真台账必须真的能命中那一笔。
        """
        table = {(1105, 1109): {332}}
        ok = u"Round 330: 选中那颗站到轨道之上（U-1105…U-1109 · 产品 2 文件，动效主线）"
        self.assertEqual(332, ps.round_from_uranges(ok, table))
        self.assertIsNone(ps.round_from_uranges(u"没有 U 区间的 subject", table),
                          u"区间都没有就不许编一个轮次")
        self.assertIsNone(ps.round_from_uranges(u"引用 U-100…U-109 与 U-1105…U-1109 两段", table),
                          u"两段区间 ⇒ 读者不知道哪一段是本轮的，宁可不答")
        self.assertIsNone(ps.round_from_uranges(ok, {(1105, 1109): {332, 300}}),
                          u"同一区间命中两节 ⇒ 台账自己重复了，不许挑一节")
        self.assertIsNone(ps.round_from_uranges(ok, {}), u"台账里没有那一节 ⇒ 引用悬空")
        # 真台账的证人：`117f45d` 的区间确实唯一命中第 332 轮，且这一笔被标成"补自台账"。
        real = ps.ledger_round_by_urange()
        self.assertEqual({332}, real.get((1105, 1109)),
                         u"真台账里 U-1105…U-1109 应当唯一命中第 332 轮，实得 %s" % (real.get((1105, 1109)),))
        hit = [r for r in ps.product_commits() if r[2] == u"117f45d"]
        self.assertEqual(1, len(hit), u"git 里读不到 117f45d ⇒ 这一格没有对象")
        self.assertEqual(332, hit[0][1], u"第二个来源没把它补成第 332 轮")
        self.assertTrue(ps.label_came_from_ledger(hit[0][4], hit[0][1]),
                        u"来源没标出来 ⇒ 派生会变成静默的（derive 必须印 标签补自台账=N）")
        # 反方向的证人：把第二个来源关掉，同一轮的答案就是那个"看起来像结论的错数"。
        rows_no_source = [(s, None if sh == u"117f45d" else l, sh, d, su)
                          for (s, l, sh, d, su) in ps.product_commits()]
        self.assertEqual(1, ps.streak_at(333, ps.product_commits())[0])
        self.assertEqual(15, ps.streak_at(333, rows_no_source)[0],
                         u"没有第二个来源时 333 轮答 15 —— 这一格是 D-329 的证人：豁免不改变数，派生才改变")

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
