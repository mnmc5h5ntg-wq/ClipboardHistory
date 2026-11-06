# -*- coding: utf-8 -*-
"""R594 靶 4②：抄仪器行到台账这件事的形状守卫，判的是**守卫自己**。

来历：R593 主节 ④ 我把"新表 mutate_r593_paths 进预检名册"后面抄的那一行写成了同一份输出里
**相邻**的另一张表（`mutate_r245  -- 静态抽不出 needle`）⇒ 形状对、话真、对象错，门看不见。
"""
from __future__ import annotations

import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import instrument_quote_guard as q  # noqa: E402

TABLES = [u"mutate_r900_paths", u"mutate_r245"]
ARMS = {u"mutate_r900_paths": [1611, 1612, 1613], u"mutate_r245": []}


def reds(text):
    return [msg for _, _, probs in q.judge_lines([text], TABLES, ARMS) for msg in probs]


class ShapeTest(unittest.TestCase):
    def test_the_good_row_is_not_flagged(self):
        self.assertEqual([], reds(u"新表进预检名册（`mutate_r900_paths  M1611 ok；…；M1613 ok`）"),
                         u"表自己的那一行不许被红；把它判红只会逼人删掉这一格")

    def test_a_file_path_mention_is_not_a_quoted_row(self):
        # R594 本机实测到的第一形：台账 ⑦ 那一格列"本轮动过的文件"，里面就有 precheck 自己的路径。
        text = u"本轮动过的文件 `.scratch/motion-audit-2/mutate_needle_precheck.py、scripts/a.py`。"
        self.assertEqual([], reds(text),
                         u"文件名不是「某张表的那一行」⇒ 把它判红就是尺读错对象，逼人选措辞而不是修尺")

    def test_a_bare_table_name_is_not_a_quoted_row(self):
        # 第二形：只是**提到**这张表（反引号里没有内容），不是抄了它的一行。
        self.assertEqual([], reds(u"预检与捕获并行撞锁 ⇒ `mutate_needle_precheck` 报 NOT_RUN_TIMEOUT"),
                         u"光一个表名不构成抄行")

    def test_a_table_that_is_not_in_the_roster_is_red(self):
        self.assertTrue(reds(u"新表进预检名册（`mutate_r999_ghost  M1611 ok`）"),
                        u"名册里没有这张表 ⇒ 抄的是不存在的对象")

    def test_foreign_arm_numbers_are_red(self):
        problems = reds(u"新表进预检名册（`mutate_r900_paths  M1582 ok`）")
        self.assertTrue(any(u"不属于这张表" in p for p in problems), problems)

    def test_row_starting_at_the_wrong_arm_is_red(self):
        problems = reds(u"新表进预检名册（`mutate_r900_paths  M1612 ok；…；M1613 ok`）")
        self.assertTrue(any(u"第一把" in p for p in problems),
                        u"表的第一把是 1611，引用从 1612 起 ⇒ 这行不是表自己那一行")

    def test_truncation_without_ellipsis_is_red(self):
        problems = reds(u"新表进预检名册（`mutate_r900_paths  M1611 ok；M1612 ok`）")
        self.assertTrue(any(u"把节选写成全文" in p for p in problems), problems)

    def test_the_r593_shape_quoting_the_neighbouring_row_is_red(self):
        # 两张表**都**在名册里 —— 只查"在不在名册"抓不到这一朵。
        problems = reds(u"新表 `mutate_r900_paths` 进预检名册（`mutate_r245  -- 静态抽不出 needle`）")
        self.assertTrue(any(u"另一张表" in p for p in problems),
                        u"R593 ④ 那一朵的形状必须响：%s" % problems)


class RosterTest(unittest.TestCase):
    def test_the_roster_and_arms_come_from_the_precheck_itself(self):
        tables = q.load_tables()
        self.assertGreater(len(tables), 300, u"名册现读不该退成个位数（尺读错了对象）")
        self.assertIn(u"mutate_r593_paths", tables)
        arms = q.load_arms(u"mutate_r593_paths")
        self.assertEqual([1598, 1599, 1600, 1601, 1602, 1603, 1604, 1605,
                          1606, 1607, 1608, 1609, 1610], arms,
                         u"那张表的刀要现读得到，否则这一支只会判"
                          u"“名册在不在”而判不了“抄的是不是这一行”")

    def test_missing_table_file_is_not_silently_empty_ok(self):
        self.assertIsNone(q.load_arms(u"mutate_r1900000_ghost"))

    def test_the_live_ledger_passes_this_guard(self):
        self.assertEqual(0, q.main([]), u"盘上那一行（R593 改掉之后的形状）必须过这一支")
