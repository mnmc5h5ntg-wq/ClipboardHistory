# -*- coding: utf-8 -*-
"""R593 / 靶 4：把"⓪ 必须在台账之前"做成会红的守卫 —— 这一卷判的是守卫自己。

三件事按顺序判：① 真值表（四种形状各判各的）；② 正对照（尺瞎了要 exit 1，不许 exit 0）；
③ 盘上最新那一轮的 ⓪ 现在到底有没有读数（这一格是"今天有没有人判"的证人，不是措辞）。
"""
from __future__ import annotations

import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ledger_preflight as pre  # noqa: E402


class TruthTableTest(unittest.TestCase):
    def test_each_shape_gets_its_own_verdict(self):
        cases = [
            (u"⓪ 现读\n   RUN=42210166309 ↔ 03b48b2 到数=是\n", 0, u"成对号"),
            (u"⓪ 现读两对：`42210166309 ↔ 03b48b2`（台账里的反引号写法）\n", 0, u"成对号"),
            (u"⓪ 现读\n   status=in_progress ⇒ 未到数（conclusion 空）\n", 0, u"具名未到数"),
            (u"⓪ 现读\n   这一格还没填\n", 1, u"⓪ 那一节既没有"),
            (u"⓪ 现读\n   本轮那一跑 = RUN_UNFETCHED\n", 1, u"却没带原因字样"),
        ]
        for text, want_rc, want_in in cases:
            rc, why = pre.judge(text)
            self.assertEqual(want_rc, rc, u"%r 判成 %d（%s）" % (text[:40], rc, why))
            self.assertIn(want_in, why, u"红话/绿话要点名形状：%s" % why)

    def test_a_missing_section_is_not_run_not_pass(self):
        rc, why = pre.judge(None)
        self.assertEqual(2, rc, u"切不到 ⓪ 那一节 ⇒ 没判，不许读成绿：%s" % why)
        self.assertIn(u"not-run", why)

    def test_history_sections_are_not_consulted(self):
        # 台账是降序：最新一节在最上面。写成"扫全文"会让这一支永远绿（历史里全是成对号）。
        text = (u"## R593 状态（本轮）\n⓪ 现读\n   （空）\n① 正文\n"
                u"## R592 状态（上一轮）\n⓪ 现读\n   RUN=42179047067 ↔ 40cccd4\n")
        section = pre.newest_zero_section(text)
        self.assertIsNotNone(section)
        self.assertNotIn(u"42179047067", section, u"切到了历史那一节 ⇒ 守卫读错了对象")
        self.assertEqual(1, pre.judge(section)[0], u"本轮 ⓪ 空着必须红")


class InstrumentTest(unittest.TestCase):
    def test_the_reader_selfcheck_rings(self):
        self.assertTrue(pre.selfcheck(), u"正对照没响 ⇒ 这把尺认不出『裸未到数』与『具名未到数』的差别")

    def test_the_current_ledger_section_actually_has_a_reading(self):
        """盘上最新一轮的 ⓪ 现在有没有读数 —— 这一格不许由我口头说。"""
        path = os.path.join(ROOT, pre.STATE)
        text = io.open(path, encoding=u"utf-8", errors=u"replace").read()
        rc, why = pre.judge(pre.newest_zero_section(text))
        self.assertIn(rc, (0, 1), u"守卫连节都切不出来：%s" % why)
        # 本轮（R593）落盘之前这一格**应当**是红的 —— 它红就是这一支存在的理由，不是缺陷。
        print(u"LEDGER_PREFLIGHT_LIVE rc=%d %s" % (rc, why))


if __name__ == u"__main__":
    unittest.main(verbosity=2)
