#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`frame_audit.py` 的 `bands` 那把尺（BACKLOG 205 / R175）。

不覆盖管线：这一支量的是**测量工具自己**——它没有产品入口，产品入口是捕获卷里那些帧。
它存在的理由是一条真实失误的形状：`align` 把"每一像素行的第一个有墨列"直接报成簇，
于是两行字号不同的文本会被读成"两行不同轴"。所以这里每条断言都在问一件事：
**这把尺会不会把同一根轴读成两根、或把两根读成一根。**

夹具是手搓的像素缓冲（不走 PNG 解码），因为要问的是聚类与取轴，不是解码；
PNG 那条通道由本轮在真帧上跑 `command_bands` 形成对照（见 AGENT_VISUAL_ITERATION 的 R175 一节）。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import frame_audit  # noqa: E402

BG = (255, 255, 255, 255)
INK = (20, 20, 20, 255)


def canvas(width, height):
    return bytearray(b"".join(bytes(BG) * width for _ in range(height))), width


def paint(buf, width, height, x0, x1, y0, y1, jitter=0):
    """画一个墨块；`jitter` 让带内逐行的 min-x 抖几像素（真实字体的升降部就是这个形状）。"""
    for y in range(y0, y1):
        left = x0 + (y % (jitter + 1) if jitter else 0)
        for x in range(left, min(x1, width)):
            base = (y * width + x) * 4
            buf[base:base + 4] = bytes(INK)


def bands(buf, width, height, **kw):
    return frame_audit.line_bands(width, height, 4, buf, **kw)


class LineBandsTests(unittest.TestCase):

    def test_two_lines_on_the_same_axis_are_one_axis_even_when_lengths_differ(self):
        """正对照（也是 `align` 当年读错的那一格）：两行同左轴、长度不同、字号不同 ⇒ 必须同轴。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 30, 180, 10, 34, jitter=3)   # 大字号那一行
        paint(buf, width, 120, 30, 90, 44, 58, jitter=1)    # 小字号、短得多的一行
        got = bands(buf, width, 120)
        self.assertEqual(2, len(got), "两行字必须聚成两带：%s" % got)
        axes = [b["axis"] for b in got]
        self.assertLessEqual(max(axes) - min(axes), 2,
                             "同一根轴被读成两根（左轴 %s）⇒ 这把尺会造出假的排版缺陷" % axes)

    def test_two_lines_on_different_axes_are_reported_apart(self):
        """反方向：两行真的错开 30px ⇒ 不许被"取众数"抹平成一根。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 24, 170, 10, 30)
        paint(buf, width, 120, 54, 150, 40, 58)
        got = bands(buf, width, 120)
        self.assertEqual(2, len(got))
        axes = sorted(b["axis"] for b in got)
        self.assertGreaterEqual(axes[1] - axes[0], 28,
                                "错开 %s 却读成 %s ⇒ 这把尺会掩盖真缺陷" % (axes, axes[1] - axes[0]))

    def test_single_line_is_not_a_verdict_about_alignment(self):
        """只有一行 ⇒ 谈"同不同轴"没有对象：必须给"无从判定"，不许给"同轴"。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 40, 160, 20, 40)
        got = bands(buf, width, 120)
        self.assertEqual(1, len(got), "一行字聚成了 %d 带" % len(got))
        self.assertLess(len([b["axis"] for b in got]), 2)

    def test_antialiasing_debris_is_not_a_text_line(self):
        """1~2 行的碎屑（描边、阴影、抗锯齿）不许被当成一行字 —— 否则带数虚高、散布被碎屑主导。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 40, 160, 20, 40)
        paint(buf, width, 120, 190, 198, 60, 61)   # 一行高的边角
        paint(buf, width, 120, 190, 198, 90, 91)
        got = bands(buf, width, 120)
        self.assertEqual(1, len(got), "两行一像素的碎屑被聚成了文本行：%s" % got)

    def test_a_leading_icon_owns_the_axis_so_this_ruler_needs_text_only_lines(self):
        """这把尺的**边界**，钉住而不是假装没有：一行里最左的墨是图标时，`axis` 就是图标那一列。

        为什么写成断言而不是注释：R65 之后浮层每行都有图标（标签轴 56.0–57.0pt），
        如果有人拿这把尺去量"标签同不同轴"，它会给出图标轴还答得很稳。
        ⇒ 这条测试的名字就是使用说明书：**只用于不带图标的行**（空态那两行、说明段、纯文字列表）。
        """
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 8, 20, 10, 30)      # 图标
        paint(buf, width, 120, 40, 170, 10, 30)    # 同一行的文字
        got = bands(buf, width, 120)
        self.assertEqual(1, len(got))
        self.assertEqual(8, got[0]["min_x"], "min_x 该如实报最左的墨（图标）")
        self.assertEqual(8, got[0]["axis"],
                         "带图标的行里 axis 就是图标轴 —— 它答不了『标签同不同轴』，别用它问那个问题")


class CommandBandsTests(unittest.TestCase):

    def _say(self, buf, width, height, **kw):
        out = io.StringIO()
        real = sys.stdout
        sys.stdout = out
        try:
            rc = frame_audit.command_bands_from_pixels(buf, width, height,
                                                       name="synthetic.png", **kw)
        finally:
            sys.stdout = real
        return rc, out.getvalue()

    def test_one_band_exits_nonzero_because_it_judged_nothing(self):
        """命令的退出码要跟着判定走：只有一带时不许 exit 0（"没判"不是"判过且没事"）。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 40, 160, 20, 40)
        rc, text = self._say(buf, width, 120, pt_width=100.0)
        self.assertEqual(1, rc, "一带却给了 0 ⇒ 会把'无从判定'打印成'通过'")
        self.assertIn("无从判定", text)

    def test_a_band_holding_two_elements_is_refused_not_judged(self):
        """R175 实测到的那条漂：同一张帧在两档下"众数左沿"从 22.0pt 变成 52.0pt，而 `min_x` 两档都是 22.5pt。

        成因不是产品，是**一带里混了两个元素**（搜索框那一行既有左对齐的查询文字、右边还有别的墨）。
        ⇒ 这一带必须判"不可判"，不许拿众数当轴。夹具照那个形状造：同一带里 8px 处一条细墨 + 90px 起一大块墨。
        """
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 8, 14, 10, 20)      # 细墨只占带的上半：逐行最左墨会从 8px 漂到 90px
        paint(buf, width, 120, 90, 190, 10, 34)    # 大块墨占满整带 ⇒ 众数落在它身上
        got = bands(buf, width, 120)
        self.assertEqual(1, len(got), "两个元素被聚成了两带，这条测试的对象就变了：%s" % got)
        self.assertGreater(got[0]["axis_spread"], 40,
                           "夹具没复现出'逐行最左墨在漂'（散布=%d）⇒ 后面那句拒判断言就没有对象"
                           % got[0]["axis_spread"])
        self.assertEqual(8, got[0]["min_x"])
        self.assertGreaterEqual(got[0]["axis"], 88, "夹具得先真的复现'众数被大块拽走'，否则后面那句断言没对象")

    def test_two_clean_bands_are_judged_on_min_x(self):
        """两带各自只有一个元素 ⇒ 该给判定，且判定必须写在 `min_x` 上（两档稳的那个数）。"""
        buf, width = canvas(200, 120)
        paint(buf, width, 120, 20, 60, 10, 30)
        paint(buf, width, 120, 20, 40, 40, 60)
        rc, text = self._say(buf, width, 120, pt_width=100.0)
        self.assertEqual(0, rc, "两带干净却不给判定：%s" % text)
        self.assertIn("同轴", text)
        self.assertIn("最左墨", text)


if __name__ == "__main__":
    unittest.main()
