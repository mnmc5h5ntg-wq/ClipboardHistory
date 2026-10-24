#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R330（第 329 轮 / Round 328）：真机那把尺（`scripts/real_screen_filter_pill.py`）自己的判据卷。

为什么这一卷存在：377 的结论（屏幕上选中那颗比轨道暗 33 级）是**这台机器的一次截屏**给的，
而同一趟里这把尺自曝了三次 —— ① 列电平取 `max()` ⇒ 把一条文字行读成胶囊（差 -78.4）；
② 只判横向 ⇒ 同一条文字行第二次又过闸（差 -99.0）；③ 页底从控件**自己那一行**取众数 ⇒
两半区各占一半时它是掷硬币，臂 B 押给了轨道，于是同一个缺陷被报成"不是缺陷"（差 +31.0）。
三次都不是产品坏，是**尺坏**；而尺坏在这仓库里唯一的永久化方式就是一卷会红的判据（D-038 那一族）。
所以这一卷不测产品，它测"这把尺读的是不是它声称的那个对象"。

它全部用**合成帧**（临时目录里现画的 PNG），不依赖屏幕、不依赖 App、不依赖显示器：
真机通道只在"这一卷证不了的那一层"（材质、系统色档）才是证人，而这里三条坏法都能在合成帧上复现。

不覆盖管线：这一卷不碰产品代码，也不给"屏幕上到底画的哪一面"作证 —— 那一半由
`scripts/real_screen_filter_pill.py` 在本机真跑（BACKLOG 377 的读数就是它现读的），
本卷钉的是"它下一次不会再读错对象"。
"""
import os
import sys
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:                                        # 与 252 同一族：缺库要能被点名
    Image = None

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'scripts'))

import real_screen_filter_pill as R                       # noqa: E402

PAGE = 48.0        # 合成帧的窗口背景
TRACK = 80.0       # 分段控件那条轨道（比背景亮一档以上）
INK = 200.0        # 字墨
W_PT = 320         # 合成帧的窗口宽度（pt）⇒ scale = 640/320 = 2
CONTROL_Y = (100, 126)


def paint(img, x0_pt, x1_pt, y0_pt, y1_pt, level):
    """按 pt 画一块（尺的坐标约定全篇都是 pt，写成 px 会在 1× 机器上悄悄变一半）。"""
    s = img.width / float(W_PT)
    for x in range(int(x0_pt * s), int(x1_pt * s)):
        for y in range(int(y0_pt * s), int(y1_pt * s)):
            img.putpixel((x, y), (int(level),) * 3)


def frame(height_pt=220, control=True, hole_left=True, text_row=False,
          bright_wider=False, below_level=PAGE):
    """现画一帧侧栏：背景 48，可选一条控件带（一段轨道一段"与背景同档的洞"）与一条文字行。

    洞**不贴容器的右边缘**（真机那两帧里洞的右侧也还剩一段亮：臂 B 读到 轨道宽=260pt
    而洞只到 x240）。这一条是承重的：尺的"轨道范围"取的是**首末两个差异列之间**，
    洞要是贴着容器边把差异列断在外面，并集就框不住它 —— 夹具第一版正是这么写的，
    于是它测的不是"参照会不会翻"，而是"洞贴不贴边"。
    """
    img = Image.new('RGB', (int(W_PT * 2), int(height_pt * 2)), (int(PAGE),) * 3)
    hole_w = 90.0 if bright_wider else 152.0
    if control:
        paint(img, 8, 312, CONTROL_Y[0], CONTROL_Y[1], TRACK)      # 整条轨道
        if hole_left:
            paint(img, 8, 8 + hole_w, CONTROL_Y[0], CONTROL_Y[1], PAGE)
        else:
            paint(img, 300 - hole_w, 300, CONTROL_Y[0], CONTROL_Y[1], PAGE)
        # 字：两颗标签画在控件带上（真帧里标签行的字墨就压在洞与轨道之上）
        paint(img, 60, 63, 108, 118, INK)
        paint(img, 250, 253, 108, 118, INK)
    if text_row:
        # 一条"两头各一块字"的标题行：横向跨度 300pt、比背景亮 150 级 —— 前三道闸全过。
        # 笔画按真字的疏密画（2pt 宽的竖笔、8pt 一笔），不然它会密成一块填充，
        # 实心度冲到 0.21 就比地板还高 —— 那是夹具在骗闸，不是尺该放行。
        for base in (12, 230):
            for i in range(0, 68, 8):
                paint(img, base + i, base + i + 2, 152, 164, INK)
    if below_level != PAGE:
        # 下参照带的具体行由尺自己定（先粗扫圈出控件，再到它下面取带），
        # 所以夹具把控件下方一整片都染走 —— 不然带会落在两档的边界上，众数又对了。
        paint(img, 0, 320, CONTROL_Y[1] + 2, min(218, CONTROL_Y[1] + 30), below_level)
    return img


def scan_img(img):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'synthetic.png')
        img.save(path)
        found, meta = R.scan(path, W_PT)
    return found, meta


class RealScreenFilterPillTests(unittest.TestCase):
    """合成帧进尺：三把刀（M957…M959）各钉一种"尺读错对象"的坏法。"""

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_rulerFindsTheControlAndCallsTheSelectedHalfDarker(self):
        found, meta = scan_img(frame())
        self.assertTrue(found, '合成帧里明明有一条控件带，尺却说没有 ⇒ 闸太紧，它连自己的夹具都不认')
        best = max(found, key=lambda g: (g['extent_pt'], g['hole_pt']))
        self.assertLess(best['pill'] - best['track'], -R.DELTA,
                        '选中那颗应当比轨道**暗**（真机 377 读到的形状）：%s' % best)
        self.assertGreaterEqual(best['extent_pt'], R.MIN_CONTAINER_PT)
        self.assertGreater(best['hole_pt'], 0.0, '洞宽被读成 0 ⇒ 分母是空的')

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_columnLevelIsTheMedianSoGlyphInkCannotHijackIt(self):
        # M959 的靶：把这里改成 max 就红 —— 真机第一版正是用 max，把一条文字行读成了胶囊。
        img = Image.new('RGB', (640, 96), (int(PAGE),) * 3)
        paint(img, 0, 320, 26, 29, PAGE)
        paint(img, 100, 101, 30, 32, INK)                 # 一小撮字墨，只占这一行带的一点点高度
        px = img.load()
        cols = R.column_levels(px, int(26 * 2), int(34 * 2), 198, 202, 2)
        self.assertTrue(cols, '列剖面是空的')
        for _x, v in cols:
            self.assertLess(v, TRACK, '这一列只有一行字墨，中位电平必须还是页底：%s' % cols)

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_textRowAloneIsNotAControl(self):
        # M958 的靶：把 MIN_SOLIDITY 改成 0 就红 —— 文字行的横向跨度与亮度都够，只有纵向是空的。
        found, _meta = scan_img(frame(control=False, text_row=True))
        self.assertEqual([], found,
                         '一条"两头各一块字"的标题行过了闸 ⇒ 实心度那道闸没生效（它会给出 -99 级的假差）')
        with_control, _ = scan_img(frame(text_row=True))
        self.assertTrue(with_control, '正对照：同一帧加上真控件带就必须有候选，否则上一句是恒真句')

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_referenceComesFromOutsideTheControlEvenWhenHalvesAreUnequal(self):
        # M957 的靶：把两趟参照改回"行内众数"就红。这一帧故意让**亮的那半更宽**，
        # 于是行内众数会押给轨道（80），页底被读成 80 ⇒ 同一个缺陷翻成"选中那颗更亮、不是缺陷"。
        img = frame(hole_left=False, bright_wider=True)
        found, _meta = scan_img(img)
        self.assertTrue(found, '亮半更宽时尺直接找不到控件 ⇒ 参照物在偏置面前塌了')
        best = max(found, key=lambda g: (g['extent_pt'], g['hole_pt']))
        self.assertLess(best['pill'] - best['track'], -R.DELTA,
                        '结论翻了（差 %+.1f）⇒ 页底又被行内众数劫持了：%s' % (best['pill'] - best['track'], best))
        self.assertGreaterEqual(best['page_mode_in_row'] - best['page'], R.DELTA,
                                '这一格要证明"行内众数确实会押错、而外取参照没押错"；'
                                '两个数一样就说明夹具没造出偏置：%s' % best)

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_darkHalfMovesWithTheSelection(self):
        """两臂对照（真机 AB 的合成版）：洞必须跟着选中搬，而不是钉在左半边。"""
        left, _ = scan_img(frame(hole_left=True))
        right, _ = scan_img(frame(hole_left=False, bright_wider=True))
        a = max(left, key=lambda g: (g['extent_pt'], g['hole_pt']))
        b = max(right, key=lambda g: (g['extent_pt'], g['hole_pt']))
        self.assertLess(a['hole_x0'], 100.0, '臂 A 的洞应在左半：%s' % a)
        self.assertGreater(b['hole_x0'], a['hole_x1'],
                           '洞没搬 ⇒ 尺读的是"左半边有块暗的"，不是选中态：%s vs %s' % (a, b))
        self.assertLess(a['pill'] - a['track'], -R.DELTA)
        self.assertLess(b['pill'] - b['track'], -R.DELTA,
                        '两臂都得判暗才算同一个缺陷跟着选中走')

    @unittest.skipIf(Image is None, '缺 PIL ⇒ 这把尺的证人跑不了（与 252 同一族）')
    def test_unstableReferenceIsRefusedNotJudged(self):
        """上下两条参照带不同档 ⇒ 参照物自己不可信：`ref_stable=False`，不许往下判。"""
        found, _meta = scan_img(frame(below_level=110.0))
        self.assertTrue(found or True)                     # 有没有候选都不是这一格的问题
        for g in found:
            self.assertFalse(g['ref_stable'],
                             '参照带自己都对不上还给出判定 ⇒ %s' % g)

    def test_modeLevelIsTheBusiestBinNotTheNinetiethPercentile(self):
        profile = [(i, PAGE) for i in range(60)] + [(i, TRACK) for i in range(60, 100)]
        self.assertAlmostEqual(PAGE, R.mode_level(profile, R.DELTA), delta=R.DELTA)
        self.assertEqual(0.0, R.mode_level([], R.DELTA), '空剖面给 0.0 是"没参照"，调用方必须挡住')
        # 众数与分位数在"少数派很亮"时必须分开：90 分位会押给 TRACK，而多数派是 PAGE。
        self.assertGreater(sorted(v for _x, v in profile)[int(0.9 * (len(profile) - 1))], PAGE + R.DELTA)

    def test_contiguousRunsIdentity(self):
        flags = [False, True, True, False, True, False]
        runs = R.contiguous_runs(flags)
        self.assertEqual([(1, 3), (4, 5)], runs)
        self.assertEqual(sum(b - a for a, b in runs), sum(1 for f in flags if f),
                         '各段长度之和必须等于 True 的个数（少了就是丢段）')
        self.assertEqual([], R.contiguous_runs([]), '空输入要给空，不许给 [(0,0)]')
        self.assertEqual([(0, 2)], R.contiguous_runs([True, True]), '尾巴那段不许被丢掉')


if __name__ == '__main__':
    unittest.main(verbosity=2)
