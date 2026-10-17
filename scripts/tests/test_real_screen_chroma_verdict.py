#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`verdict_of` 的真值表（R132 / BACKLOG 139 的那把尺）。

为什么单独一支：这条判据决定 139 是"通道"还是"产品缺陷"，两种结论的修法**相反**
（前者不改产品，后者要改上色）。所以四个出口必须各自能被证伪，
而且"参照自己坏了"这一格必须**优先**于比值 —— 否则参照坏掉时那一次测量会被读成
「内容区也没色」，等于把没跑记成一条产品结论（这个仓库里同一族栽过多次：U-317、批次 78.6）。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import real_screen_control_chroma as rsc  # noqa: E402


class VerdictTruthTableTests(unittest.TestCase):

    def test_reference_that_paints_nothing_is_not_a_verdict(self):
        """参照坏了 ⇒ 无论内容区读到什么都只能 `no_reference`（优先于比值）。"""
        self.assertEqual("no_reference", rsc.verdict_of(ref_max=0, content_max=0))
        self.assertEqual("no_reference", rsc.verdict_of(ref_max=rsc.REF_MIN - 1, content_max=200),
                         "参照没色却给内容区定罪 ⇒ 这条判据会把「没跑」记成产品结论")

    def test_content_as_blue_as_the_reference_is_a_channel_finding(self):
        self.assertEqual("accent_in_content", rsc.verdict_of(ref_max=100, content_max=90))

    def test_content_missing_the_accent_is_a_product_finding(self):
        self.assertEqual("accent_missing", rsc.verdict_of(ref_max=100, content_max=10))

    def test_the_middle_band_has_its_own_name(self):
        """落在 0.25..0.5 之间 ⇒ 不许四舍五入到任一侧（那正是"把判据调成想要的结论"的形状）。"""
        self.assertEqual("undecided", rsc.verdict_of(ref_max=100, content_max=40))

    def test_the_two_boundaries_are_stated_not_implied(self):
        """边界值本身归哪一侧要钉住：改 HIGH/LOW 会让这两格翻面。"""
        self.assertEqual("accent_in_content", rsc.verdict_of(ref_max=100, content_max=int(100 * rsc.HIGH)))
        self.assertEqual("undecided", rsc.verdict_of(ref_max=100, content_max=int(100 * rsc.HIGH) - 1))
        self.assertEqual("accent_missing", rsc.verdict_of(ref_max=100, content_max=int(100 * rsc.LOW) - 1))
        self.assertEqual("undecided", rsc.verdict_of(ref_max=100, content_max=int(100 * rsc.LOW)))

    def test_the_four_exits_are_four_different_words(self):
        got = {
            rsc.verdict_of(ref_max=0, content_max=0),
            rsc.verdict_of(ref_max=100, content_max=90),
            rsc.verdict_of(ref_max=100, content_max=10),
            rsc.verdict_of(ref_max=100, content_max=40),
        }
        self.assertEqual(4, len(got), "四个出口塌成同一个词 ⇒ 读数没有区分力")

    def test_press_outcome_has_four_named_exits(self):
        """点之前/点之后/本来就选中/没量到 —— 四种出口的修法相反，不许塌成两种。"""
        self.assertEqual("already_selected", rsc.press_outcome(before=88.0, after=None, target=88.0))
        self.assertEqual("moved", rsc.press_outcome(before=50.5, after=82.0, target=88.0))
        self.assertEqual("not_landed", rsc.press_outcome(before=50.5, after=51.0, target=88.0))
        self.assertEqual("unmeasured", rsc.press_outcome(before=None, after=None, target=88.0))
        self.assertEqual("unmeasured", rsc.press_outcome(before=50.5, after=None, target=None))

    def test_the_pre_click_probe_is_not_read_as_a_broken_ruler(self):
        """U-438：点之前那次"目标行本来选中了吗"不许复用需要 after 的那个出口。

        本轮真实翻车形状：目标行已经选中，我却把 `after=None` 喂进判定 ⇒
        返回 `unmeasured`，一次**成功**的测量被印成"参照那一列没量到任何蓝色（尺坏了）"。
        这类假阴性的坏处是它会让人去修没坏的尺。
        """
        self.assertEqual("already_selected", rsc.press_outcome(before=88.0, after=None, target=88.0))

    def test_a_bounding_box_that_is_upside_down_names_itself(self):
        """包围盒的恒等式：min <= max。第一版把四个数印成 `x=177..98` 而读数仍然"像结论"。"""
        self.assertTrue(rsc.box_is_wellformed((17.0, 82.0, 64.0, 95.0)))
        self.assertTrue(rsc.box_is_wellformed([None, None, None, None]), "空盒不是错")
        self.assertFalse(rsc.box_is_wellformed((177.0, 192.0, 98.0, 219.0)))
        self.assertIn("BAD_BOX", rsc._box_text((177.0, 192.0, 98.0, 219.0)))
        self.assertEqual("x=17..64 y=82..95pt", rsc._box_text((17.0, 82.0, 64.0, 95.0)))

    def test_the_script_is_not_a_copy_of_the_sidebar_ruler(self):
        """两条正对照不许互相替代：139 问的是**色度**，172 问的是**墨量**，
        所以色度那把尺必须自己存在、且自己有一支真值表（这一支）。"""
        self.assertTrue(os.path.exists(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "real_screen_control_chroma.py")))
        self.assertNotEqual(rsc.CONTENT_X, rsc.REF_X, "两块区域同一条矩形 ⇒ 参照与被判物是同一个东西")


if __name__ == "__main__":
    unittest.main()
