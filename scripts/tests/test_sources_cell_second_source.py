#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""报告里「最后一次动到 `Sources/` 的轮次」那一格：它必须**永远写得出来**（R340 开）。

为什么要有它（R340 现读的连锁）：上一轮那笔产品提交 `fb2cea0` 的 subject 缺 `R<NNN>`，
`test_commit_subject_hygiene` 走 `NO_LABEL_ROSTER` 登记之后那一格不红了 ——
但 `scripts/report_sources_cell.py` 从 subject 派生轮次，派生不出来就得到 `rnd=None`，
于是 `build_row` 写出 `**R0**`，而复核比的是 `0 == None` ⇒ **那一格连 --write 都写不成**，
报告里"最近一次动源码"停在错的数上，而且没有任何一条守卫会红。
这是 D-329 那条"豁免只买不红、买不到数对"的第三次应验（前两次：R333 的 streak=15、R334 的名册）。

判三格：
  ① 正对照：合成 subject + 合成台账 —— 区间恰好命中一节才给轮次；多段 / 0 节 / 多节一律 None（不许猜）；
  ② 真历史：最近一笔动过 `Sources/` 的提交必须**能派生出轮次**（这一格在我修之前是红的）；
  ③ 账与 git 必须一致（直接调那一格的取数口，不复制它的正则）。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, u"scripts"))   # 与 test_frame_audit_bands 同一写法
import report_sources_cell as T  # noqa: E402


class SourcesCellSecondSource(unittest.TestCase):
    LEDGER = (u"# 台账\n"
              u"## 第 338 轮（R339 · 2026-10-25 · U-1155…U-1162）：甲（U-1155…U-1162 · 产品 3 文件）\n"
              u"正文\n"
              u"## 第 337 轮（R338 · 2026-10-25 · U-1147…U-1154）：乙（U-1147…U-1154 · 产品 1 文件）\n")

    def _with_ledger(self, text, subject):
        path = os.path.join(ROOT, u"__r340_fake_ledger__.md")
        io.open(path, u"w", encoding=u"utf-8").write(text)
        try:
            saved = T.LEDGER
            T.LEDGER = path
            return T.round_from_ledger(subject)
        finally:
            T.LEDGER = saved
            os.remove(path)

    def test_second_source_is_exact_and_refuses_to_guess(self):
        self.assertEqual(339, self._with_ledger(
            self.LEDGER, u"Round 336: 一句话（U-1155…U-1162 · 产品 3 文件，动效主线）"),
            u"subject 没有 R 标签，但它自己写的 U 区间在台账里恰好命中 R339 那一节")
        self.assertIsNone(self._with_ledger(self.LEDGER, u"没有区间的 subject"),
                          u"一段区间都没有 ⇒ 不许猜")
        self.assertIsNone(self._with_ledger(
            self.LEDGER, u"两段区间 U-1155…U-1162 与 U-1147…U-1154"),
            u"多段区间 ⇒ 读者不知道哪一段是本轮的 ⇒ None")
        self.assertIsNone(self._with_ledger(self.LEDGER, u"查无此号 U-9001…U-9002"),
                          u"台账里没有那一节 ⇒ None")
        dup = self.LEDGER + u"## 第 100 轮（R111 · 2026-01-01 · U-1155…U-1162）：同号两节\n"
        self.assertIsNone(self._with_ledger(dup, u"同号两节（U-1155…U-1162）"),
                          u"同一区间命中两节 ⇒ 不许二选一（R304 那一族）")

    def test_the_newest_sources_commit_always_yields_a_round(self):
        u"②真历史：这一格在加第二来源之前是红的（fb2cea0 派生不出轮次）。"
        rows = T.git_rows()
        self.assertTrue(rows, u"git log 读不到动过 Sources 的提交 ⇒ 这一格没有对象")
        sha, rnd, subject = rows[0]
        self.assertIsNotNone(rnd,
                             u"最近一笔动源码的提交 %s 派生不出轮次（subject=%s）⇒ "
                             u"报告那一格会写成 R0 且 --write 也修不好" % (sha, subject[:60]))
        self.assertGreaterEqual(rnd, 1, u"轮次号必须为正，实得 %s" % rnd)

    def test_the_cell_agrees_with_its_own_source(self):
        u"③账与 git 一致：直接调取数口的检查路径，不复制它的正则。"
        rc = T.main([])
        self.assertEqual(0, rc,
                         u"报告里那一格与 git 派生的不一致（rc=%s）⇒ 跑 --write 或改账，别放着" % rc)


if __name__ == u"__main__":
    unittest.main()
