#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`real_screen_sidebar_icons.py` 的两格解析判据 —— 真机那条通道没法在 CI 里跑，
但它**读回来的东西**是纯字符串/纯数字，可以在本机就被钉住（否则"通道没跑"与"通道读错了"
会共用同一个绿）。"""
import io
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


class DisplayChannelCauseTests(unittest.TestCase):
    """R332：真机那一格的"读不到"必须**分成修法相反的几种**（D-322 那一族的第四颗）。

    现场：用户授权我退出 App 跑 393 的 before/after，我退了、显示器也开着（`pmset` 现读
    21:51 turned on），而 `screencapture -R0,0,64,64` 报 could not create image from rect，
    `ioreg` 的 `kCGSSessionSecureInputPID` 属主是 loginwindow —— 会话是锁着的。
    旧的那一句把它报成"探针截图失败（CalledProcessError）"，读起来像**通道坏了**；
    按那句去"修尺"就会去动一条没坏的尺，而真正的缺席要人来解锁。
    """

    def test_the_three_absences_get_three_different_causes(self):
        # 三种缺席的输入形状各自独立：电源日志、会话属主、区域探针。
        self.assertEqual((False, "display_off"),
                         probe.classify_display_channel("off", None, False),
                         "显示器关着 ⇒ 必须先报 display_off：这时候锁屏与否根本看不出来，"
                         "而动作是一样的（等它开），不许把顺序反过来让 screen_locked 抢走这一格")
        self.assertEqual((False, "screen_locked"),
                         probe.classify_display_channel("on", "loginwindow", False),
                         "显示器开着而会话被登录窗锁住 ⇒ 这一格的成因是**没人解锁**，"
                         "不是通道坏了：把它报成 capture_failed 会引出一次不存在的修尺")
        self.assertEqual((False, "capture_failed"),
                         probe.classify_display_channel("on", None, False),
                         "开着、没锁、还是截不出来 ⇒ 这才是通道/屏幕录制授权坏了")
        self.assertEqual((True, "ok"),
                         probe.classify_display_channel("on", None, True),
                         "三项都过 ⇒ 必须放行；这一句是负对照，少了它上面三条可以随便红")

    def test_another_app_holding_secure_input_is_not_a_lock_screen(self):
        """SecureInput 的属主**不是** loginwindow 时不许报锁屏（密码管理器/输入法也会拿它）。

        这一格拦的是"把一个新名字接进分类器时顺手把整类都判死"：如果 other 也被当成锁屏，
        那么任何开着 SecureInput 的 App 都会让真机通道永久 NOT-RUN，而那是尺的假阴性。
        """
        self.assertEqual((False, "capture_failed"),
                         probe.classify_display_channel("on", "other", False),
                         "属主=other ⇒ 不能算锁屏；剩下的缺席只能是通道/权限")
        self.assertEqual((True, "ok"),
                         probe.classify_display_channel("unknown", "other", True),
                         "读不到电源日志但探针成功 ⇒ 放行，且不许因为 owner=other 就报锁屏")

    def test_the_classifier_is_metadata_only(self):
        """分类用的那颗 `secure_input_owner()` 只读 IORegistry/进程名，**不截屏**。

        为什么单独钉：锁屏时全屏截图是**成功**的（它拍到的是用户的桌面），
        所以"再截一张看看"是一条能走通但不许走的路 —— 这条仓库的红线是不碰用户屏幕上的内容。
        """
        with io.open(str(Path(probe.__file__)), encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.index("def secure_input_owner("):src.index("def classify_display_channel(")]
        self.assertNotIn("screencapture", body,
                         "secure_input_owner 里出现了截屏调用 ⇒ 它开始采集用户屏幕内容了")
        self.assertIn("ioreg", body, "分类器不再读会话元数据 ⇒ 上面那格的真值表是在替一条空函数作证")


if __name__ == "__main__":
    unittest.main()
