#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""悬停取证通道的名册：每一个会画 hover 的产品视图，要么接了取证键，要么在名册里点名为什么没接。

为什么这一卷存在（R248 / BACKLOG 251 第三处）：`MultiFileRow`（`DetailView.swift:609` 那一族）的悬停
**量不到**，成因不是"没有夹具"，是捕获键从来没接到它 —— `.onHover` 的 `isHovered` 在离屏渲染里恒 false，
所以两态帧永远拍不出差别，而"拍不出差别"很容易被记成"这一位没问题"（R90 那一族：量不到 ≠ 没问题）。
本轮把这件事变成一条按文件计数、且能被红掉的守卫：新增一个悬停位点而**没**接通道 ⇒ 名册少一行 ⇒ 红。

形状照仓库的既有做法（`SEAM_READER_ISOLATION` 同一族）：现读文件、现数、结论行先打、判定后做，
名册按**方向**给（未接的才要理由），每条理由 ≥20 字。
"""
import io
import os
import re
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VIEWS = os.path.join(REPO, 'ClipboardHistory', 'Sources', 'ClipboardHistoryApp', 'Views')
KEY = 'hoveredForCapture'

# 现读（R248）：这四个文件画悬停却没有把键接进来。这张表是**欠账名册**，不是豁免 ——
# 每一行必须写清"这一位的悬停今天靠什么被看见"，以及"接上键要动哪里"；下一轮做完一项就从表里删掉一行。
# 名册与代码按**集合**对账：新增未接位点却不登记 ⇒ 红；登记了却已经接上 ⇒ 也红（名册过期）。
DEBT = {
    'DailyCopyHeatmapView.swift': '欠账：格子把 isHovered 当入参交给子视图，亮法本身可拍（heatmap-populated 那两张判的就是它），'
                                  '但 hover 那一档没有独立的两态帧；接法=在夹具里给同一份数据点两下键，别在产品里读键',
    'GlassControls.swift': '欠账：这里只剩注释与 .pressedStyle(hoverLevel:) 的委托，真正的悬停墨换算在 PressableStyle（已接键）里；'
                           '登记的理由是"本文件不再有独立的悬停画法"，若哪天又自己画一层就必须接键',
    'SearchField.swift': '欠账：图标颜色直接读裸 isHovered（controlTargeted vs control），这一条画法离屏拍不到；'
                         '接法=与同文件那颗清除按钮共用一个 isHoveredForDrawing，一行改动',
    'VideoPreview.swift': '欠账：两处 .pressedStyle(hoverLevel:) 委托给已接键的 PressableStyle，'
                          '但预览卡自身没有两态夹具帧；登记是因为它从未进过帧基线，不是因为不需要',
}


def hover_files(views=VIEWS):
    out = []
    for name in sorted(os.listdir(views)):
        if not name.endswith('.swift'):
            continue
        text = io.open(os.path.join(views, name), encoding='utf-8').read()
        if '.onHover' in text or 'hoverLevel' in text or 'HoverInk' in text:
            out.append(name)
    return out


def wiring(views=VIEWS):
    """返回 [(文件, 是否接键)]，按文件名排序 —— 结论行要打印的就是这张表。"""
    rows = []
    for name in hover_files(views):
        text = io.open(os.path.join(views, name), encoding='utf-8').read()
        rows.append((name, KEY in text))
    return rows


def problems(rows):
    bad = []
    for name, wired in rows:
        if wired:
            if name in DEBT:
                bad.append(('HOVER_CHANNEL_DOUBLE', '%s 既接了键又在豁免名册里 ⇒ 名册过期' % name))
            continue
        if name not in DEBT:
            bad.append(('HOVER_CHANNEL_UNPAIRED',
                        '%s 画悬停却没有取证键 ⇒ 这一位拍不出两态帧（量不到不许当没问题）' % name))
        elif len(DEBT[name]) < 20:
            bad.append(('HOVER_CHANNEL_REASON_TOO_SHORT', '%s 的豁免理由不足 20 字' % name))
    return bad


class HoverCaptureChannelTests(unittest.TestCase):
    def test_the_roster_covers_every_hover_bearing_view(self):
        rows = wiring()
        self.assertTrue(rows, 'Views/ 里一个悬停位点都没读到 ⇒ 识别器坏了，不许当成通过')
        codes = [c for c, _ in problems(rows)]
        self.assertEqual([], codes, '取证通道名册与代码不同步：%s' % codes[:6])

    def test_the_declined_roster_is_not_a_trash_bin(self):
        """负对照：把已接通道的文件塞进豁免名册 ⇒ 必须红（名册只登记"故意不接"，不是"没做"）。"""
        rows = wiring()
        wired = [n for n, w in rows if w]
        self.assertTrue(wired, '没有任何已接通道的文件 ⇒ 这张对照没有对象')
        saved = DEBT.pop('DetailView.swift', None)
        try:
            DEBT[wired[0]] = '故意不接（这一格是把名册当垃圾桶的对照，理由本身不算数）'
            codes = [c for c, _ in problems(rows)]
            self.assertIn('HOVER_CHANNEL_DOUBLE', codes,
                          '已接键的文件进豁免名册时不许红 ⇒ 这一格是假的')
        finally:
            DEBT.pop(wired[0], None)
            if saved is not None:
                DEBT['DetailView.swift'] = saved

    def test_an_unrostered_missing_channel_is_named(self):
        """正对照：从表里删掉一行（模拟新增悬停位点却没接键也没登记）⇒ 必须点名。"""
        rows = [r for r in wiring() if r[1]]
        self.assertTrue(rows, '没有已接通道的行可拿来造对照')
        broken = [(rows[0][0], False)] + rows[1:]
        codes = [c for c, _ in problems(broken)]
        self.assertIn('HOVER_CHANNEL_UNPAIRED', codes, '把接了键的说成没接时不许静默通过')


class HoverChannelReadingsTests(unittest.TestCase):
    def test_the_channel_is_present_where_the_hover_is_drawn(self):
        """R248 的那笔产品改动：`MultiFileRow` 的填充与描边共用一个判定。"""
        text = io.open(os.path.join(VIEWS, 'DetailView.swift'), encoding='utf-8').read()
        self.assertIn('@Environment(\\.hoveredForCapture) private var hoveredForCapture', text,
                      'DetailView 里没有取证键 ⇒ 251 第三处仍未接')
        self.assertGreaterEqual(text.count('isHoveredForDrawing'), 3,
                                'isHoveredForDrawing 应当被声明一次、用在填充与描边两处（<3 ⇒ 只接了一半）')
        self.assertNotIn('.fill(.primary.opacity(isHovered\n', text,
                         '还有一处填充直接读 isHovered ⇒ 两态帧里那一半不会亮')


if __name__ == '__main__':
    rows = wiring()
    print('HOVER_CHANNEL_ROSTER 悬停位点=%d 已接键=%d 未接=%d 豁免=%d' % (
        len(rows), sum(1 for _, w in rows if w), sum(1 for _, w in rows if not w), len(DEBT)))
    for name, wired in rows:
        print('  %s %s' % ('接' if wired else '未', name))
    unittest.main(verbosity=2)
