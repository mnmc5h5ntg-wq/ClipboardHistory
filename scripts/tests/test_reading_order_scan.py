# -*- coding: utf-8 -*-
"""R593 / 靶 4：读数行顺序扫描器的判据卷（含"本轮那一处真的修对了"的证人）。"""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import reading_order_scan as ros  # noqa: E402


class TableTest(unittest.TestCase):
    def test_the_bad_shape_is_red_and_the_good_shape_is_ok(self):
        self.assertTrue(ros.selfcheck(ROOT), u"四把正对照里有一把没响 ⇒ 这把尺认不出它声称的那种坏法")

    def test_an_unregistered_function_is_not_found_not_ok(self):
        rc, why = ros.judge_one(os.path.join(ROOT, ros.ROSTER[0][0]), u"没有这个函数", u"SKIP_ROSTER 键=")
        self.assertEqual(u"not-found", rc, u"找不到函数不许读成 ok：%s" % why)


class LiveRepoTest(unittest.TestCase):
    def test_the_skip_roster_reading_line_is_now_before_its_gates(self):
        """本轮那一处（`SKIP_ROSTER 键=` 印在 `inner-red` 的 fail 之后）现在必须在门之前。

        这一格就是 R592 主笔那一跑上 `SKIP_ROSTER 键=github-runner` 出现 **0 次** 的那件事的证人：
        修之前它红，修之后它绿 —— 不是我把注释改好了，是那一行的位置改了。
        """
        rel, name, token, allow = ros.ROSTER[0]
        rc, why = ros.judge_one(os.path.join(ROOT, rel), name, token, allow)
        self.assertEqual(u"ok", rc, why)

    def test_every_registered_reading_token_still_exists(self):
        """名册不许悄悄过期：登记的每一处都必须还能找到 token。"""
        bad = []
        for rel, name, token, allow in ros.ROSTER:
            path = os.path.join(ROOT, rel)
            self.assertTrue(os.path.exists(path), u"名册里的文件不在盘上：%s" % rel)
            rc, why = ros.judge_one(path, name, token, allow)
            if rc != u"ok":
                bad.append(why)
        self.assertEqual([], bad, u"这些读数行还坐在门后面（或名册过期）：\n" + u"\n".join(bad))


if __name__ == u"__main__":
    unittest.main(verbosity=2)
