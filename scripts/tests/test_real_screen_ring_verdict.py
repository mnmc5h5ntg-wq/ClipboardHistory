# -*- coding: utf-8 -*-
"""真机描边判据的真值表（R141 / BACKLOG 179）—— `scripts/real_screen_recorder_ring.py` 的纯函数。

为什么单独测这个函数：脚本那一半要真窗口、真截图、真权限（在 CI 上多半是 NOT-RUN），
而"两态读数怎么约成一个有名字的出口"这一半是纯的 —— 它必须能在任何机器上被钉住。
判据的形状照 `test_real_screen_chroma_verdict.py`：每一支出口各配一格，
且**不许有一格同时满足两支**（那等于把"没跑"与"没画"混成一个词）。
"""
import importlib.util
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
_spec = importlib.util.spec_from_file_location(
    "ring", os.path.join(REPO, "scripts", "real_screen_recorder_ring.py"))
ring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ring)


class RingVerdictTests(unittest.TestCase):

    def test_the_two_states_that_really_happened_are_ring_present(self):
        # R141 本机原样读数：点过 墨=19312 高色度=1548 ｜ 静置 墨=10154 高色度=0
        self.assertEqual("ring_present", ring.verdict_of(1548, 0, 19312, 10154))

    def test_a_ring_that_never_appears_is_a_product_defect_not_a_missed_run(self):
        # 两态都读得到墨（通道是通的），而点过那一屏没有彩色 ⇒ 产品没画。
        self.assertEqual("ring_absent", ring.verdict_of(0, 0, 19000, 19000))

    def test_an_all_black_frame_is_the_channel_not_the_product(self):
        # R91 那一格的原样：screencapture 拿到全黑（没权限 / 显示器睡着）⇒ 必须走 NOT-RUN 出口。
        self.assertEqual("all_black", ring.verdict_of(0, 0, 0, 10154))
        self.assertEqual("all_black", ring.verdict_of(1548, 0, 19312, 0))

    def test_frames_that_disagree_grossly_are_not_the_same_screen(self):
        # 两幅墨量差一倍 ⇒ 截到的不是同一块屏幕（比如窗口在两次截图之间被别的窗盖住）。
        self.assertEqual("frames_disagree", ring.verdict_of(1548, 0, 4000, 19000))

    def test_a_dirty_reference_is_undecided_rather_than_a_pass(self):
        # 静置那一屏也有大量彩色 ⇒ 对照不干净（比如点过的那扇窗跑到了右边），不许读成"那一圈在"。
        self.assertEqual("undecided", ring.verdict_of(1548, 1548, 19312, 19000))

    def test_the_thresholds_are_one_sided_so_a_weaker_ring_still_counts(self):
        # 高色度像素刚过地板、静置恰好 0 ⇒ 仍然是 ring_present（判据判的是方向，不是绝对值）。
        self.assertEqual("ring_present", ring.verdict_of(ring.STRONG_MIN, 0, 19312, 19000))
        # 静置多一个像素就跨过 DIFFERENCE_MIN ⇒ 变成对照不干净，而不是"那一圈在"。
        self.assertEqual("undecided", ring.verdict_of(ring.STRONG_MIN, ring.DIFFERENCE_MIN + 1,
                                                      19312, 19000))

    def test_the_exit_code_contract_is_the_script_own_object(self):
        """断言必须压在**脚本自己那个字典**上。

        第一版这里写的是 `self.assertEqual(sorted(table.values()), [0, 1, 2, 2, 2])`，
        而 `table` 是测试自己抄的一份字面量 —— 脚本把退出码改坏，这一格照样绿。
        那是"断言初值已经等于期望"的同形错误（U-478）。
        """
        codes = ring.EXIT_CODES
        self.assertEqual(0, codes["ring_present"], "『那一圈在』必须是 0")
        self.assertEqual(1, codes["all_black"], "全黑=通道没跑，必须是 1（不许与通过共用 0）")
        for defect in ("ring_absent", "frames_disagree", "undecided"):
            self.assertEqual(2, codes[defect], "%s 是真机层面的缺陷，必须是 2" % defect)
        # 三种处置必须互不相同：0=有 / 1=没跑 / 2=缺陷。若"没跑"与"缺陷"共用一个码，
        # CI 就无法区分"这台机器不让我看"与"产品真的没画"。
        self.assertEqual({0, 1, 2}, set(codes.values()),
                         "退出码必须正好覆盖 0/1/2 三格，少一格就意味着有两种现实被合并了")
        self.assertEqual(["accent_unusable", "all_black", "frames_disagree", "ring_absent",
                          "ring_present", "undecided"], sorted(codes),
                         "出口名册变了就要同时改这张表与脚本里的 verdict_of（漏一格会被上面那条 set 抓到）")

    def test_a_grey_accent_is_undecided_rather_than_a_product_defect(self):
        """系统强调色是灰的时候，色度轴上没有对手 ⇒ 这一格**无从判定**（R143 #34 / F4）。

        原来只有 `accent_chromatic` 这个参数都不存在：石墨灰下静置与点过都读不到彩色，
        于是 `verdict_of` 会走成 `ring_absent` ⇒ 脚本 exit 2 = "真机层面的缺陷"，
        而实际是这台机器的设置让这条轴失效。给产品记一条不存在的缺陷，比不判更坏。
        """
        self.assertEqual("accent_unusable",
                         ring.verdict_of(0, 0, 19000, 19000, accent_chromatic=False))
        # 有彩色时同一对读数才是"产品没画"。
        self.assertEqual("ring_absent",
                         ring.verdict_of(0, 0, 19000, 19000, accent_chromatic=True))

    def test_the_rect_comes_from_the_thing_under_test_not_from_this_script(self):
        """写死坐标 = 截到哪一态由运气决定。所以矩形必须来自 spike 用例自己印的那个文件。"""
        source = open(os.path.join(REPO, "scripts", "real_screen_recorder_ring.py"),
                      encoding="utf-8").read()
        self.assertIn("RECT_FILE", source)
        self.assertIn("os.remove(RECT_FILE)", source,
                      "上一遍留下的矩形必须删掉，否则这一遍会拿旧坐标作证（临时目录不许跨次复用）")
        self.assertIn("REALSCREEN_NOT_RUN rect", source,
                      "拿不到矩形必须是 NOT-RUN，不许拿一个默认坐标去截")


if __name__ == "__main__":
    unittest.main()
