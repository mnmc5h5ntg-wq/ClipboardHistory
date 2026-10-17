#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`real_screen_sidebar_icons.py` 的两格解析判据 —— 真机那条通道没法在 CI 里跑，
但它**读回来的东西**是纯字符串/纯数字，可以在本机就被钉住（否则"通道没跑"与"通道读错了"
会共用同一个绿）。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import real_screen_sidebar_icons as probe


class ParseBoundsTests(unittest.TestCase):
    def test_applescript_list_coercion_still_parses(self):
        """正对照（R123 真栽过一次）：System Events 把两个二元列表拼起来会塞空项。"""
        self.assertEqual((375, 101, 720, 572), probe.parse_bounds("375, , 101, , 720, , 572"))

    def test_clean_csv_parses(self):
        self.assertEqual((0, 0, 720, 572), probe.parse_bounds("0,0,720,572"))

    def test_missing_window_is_none_not_zero(self):
        """窗口没开必须读成"没有"，不许读成 (0,0,0,0) —— 后者会截出一张全黑帧，
        再往下就会被读成「真机也看不见」（R91 那一格的原样）。"""
        self.assertIsNone(probe.parse_bounds("NO_WINDOW"))
        self.assertIsNone(probe.parse_bounds("375, 101, 720"))
        self.assertIsNone(probe.parse_bounds(""))


class AppearanceBitTests(unittest.TestCase):
    def test_dark_and_light_are_separated_by_measured_luma(self):
        self.assertEqual("dark", probe.appearance_of(38))
        self.assertEqual("light", probe.appearance_of(246))

    def test_the_boundary_is_stated_not_implied(self):
        """边界两侧各打一次：这一格拦的是"把暗档读数当亮档结论"（U-412）。"""
        self.assertEqual("dark", probe.appearance_of(99))
        self.assertEqual("light", probe.appearance_of(100))


if __name__ == "__main__":
    unittest.main()
