#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R95 视觉腿：设置窗口「快捷键」分区，逐元素重判（含与「数据」分区的语法对照）。

为什么是这一屏：阶段二的范围写着"设置窗口每一个分区每一种控件"，而 R92 判完「数据」之后
「快捷键」这一屏在**这一轮重判里**还没被逐元素量过（R28 只量了说明文字被截断那一格，
R39 只量了禁用态那颗开关）。它又是全 App 唯一一颗"点下去会换状态"的控件（快捷键录制器），
所以"静置时它看起来能不能点"这件事在这里最值钱。

本轮那条**会红的**判据不在这里：卡片竖向节奏住在仓库尺里
（`UICaptureHarness.cardRowKinds` / `cardRhythm` + `testSettingsCardVerticalRhythmIsOneNumber`），
台账里 `CARD_RHYTHM …` 那行读数就是它打的。这一支只负责"把整屏逐元素摊开给我看"，
它不判 —— 证人必须与它作证的判据同一颗尺子（R68 / BACKLOG 104）。

尺全部借 R92 那一支（`r92_data_visual`）：同一颗尺，别造第二把 ——
`boxes()` 是跨行合并成矩形的（逐行中位数看不见按钮），`ink_of()` 拿框自身的中位数当填充。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode
from r92_data_visual import BG_TOL, boxes, column_split, dist, ink_of, median_color_in, px, ratio


def load(path):
    w, h, ch, rows = decode(path)
    return rows, ch, w, h


def card_boxes(rows, ch, w, h, bg, x0):
    """内容列里的容器（卡片）：够宽够高的段。"""
    return [b for b in boxes(rows, ch, x0, w - 2, 0, h - 1, bg)
            if (b[1] - b[0]) / 2.0 > 120 and (b[3] - b[2]) / 2.0 > 60]


def sidebar_rows(rows, ch, w, h, split, s, lines):
    """侧栏逐行：把"某几行的图标看着发虚"这句观感换成每行的墨色 + 对比度 + 颗数。

    为什么要单独量侧栏：这一屏的**选中行**是蓝底蓝字（R92 的 Q3 判过），而未选中行的
    图标是六种不同的 SF Symbol。符号自己的笔画密度不同，所以"颗数"天然不等 ——
    能判的只有**墨色**（同一行文字与图标应当同色）和**对比度**。
    第一版只想用颗数排序，那会把 `gearshape` 这种细笔画符号永远排在最后，
    于是"它是不是被降了透明度"这个问题用一把答不了它的尺就永远得不到回答。
    """
    # `column_split` 返回的是**像素**（148pt 那一列的左界 = 296px），所以再乘一次 s
    # 会把扫描带推到 288pt —— 越过侧栏与内容列的分隔线，把卡片里的文字也当成"侧栏的一行"。
    # 第一版的读数就是这个样子：`段(40..178)`，一个 148pt 宽的"图标"。
    # 这类错不会报错，只会给出一串看着合理的数（R90 那一课的第三种形状：**尺的坐标约定要实测**）。
    band_r = split - 16
    bg = median_color_in(rows, ch, 8, band_r, int(120 * s), int(160 * s))
    # 阈值必须是"墨"而不是"不是背景"：第一版用 BG_TOL+6=10，于是那一颗**选中胶囊**
    # 也被当成墨，六行缝成一行（读数长这样：`侧栏行 y=50..500pt 段(6..148)`），
    # 而"行没分开"和"侧栏只有一行"在同一张报表上长得一模一样 —— R92 那条
    # "漏检和没有检出一模一样"的教训，我在一颗借来的尺上又犯了一次。
    runs = []
    for y in range(int(50 * s), min(h, int(500 * s))):
        xs = [x for x in range(8, band_r) if dist(px(rows, ch, x, y), bg) >= 60]
        if xs:
            runs.append((y, xs))
    bands, cur = [], []
    for i, (y, xs) in enumerate(runs):
        if cur and y - cur[-1][0] > 6:
            bands.append(cur)
            cur = []
        cur.append((y, xs))
    if cur:
        bands.append(cur)
    n_shown = 0
    for b in bands:
        y0, y1 = b[0][0], b[-1][0]
        if (y1 - y0) / s < 8:
            continue
        n_shown += 1
        cols = [x for _, xs in b for x in xs]
        segs, ccur = [], []
        for x in sorted(set(cols)):
            if ccur and x - ccur[-1] > 6:
                segs.append((ccur[0], x))
                ccur = []
            ccur.append(x)
        if ccur:
            segs.append((ccur[0], ccur[-1] + 1))
        out = []
        for (x0, x1) in segs:
            if x1 / s > split / s - 4:
                raise SystemExit('侧栏扫描带越过了内容列左界（%.0f > %.0fpt）⇒ 坐标约定又错了'
                                 % (x1 / s, split / s))
            ink, n, cr = ink_of(rows, ch, x0, x1, y0, y1, bg)
            out.append('段(%.0f..%.0f)墨=%s 颗=%d 对比=%.2f' % (x0 / s, x1 / s, ink, n, cr))
        lines.append('      侧栏行 y=%.0f..%.0fpt 底=%s %s'
                     % (y0 / s, y1 / s, bg, ' | '.join(out)))
    # 自检：侧栏有六个分区 ⇒ 带数应该正好是 6。少了 = 行没分开（第一版就是这个），
    # 多了 = 扫到了别的东西。但**暗档本来就只能检出四带**：未选中五行的标签是黑字黑底，
    # 那是 D-090 / BACKLOG 126 已经登记过的合成前盲区，不是这把尺新坏的证据。
    # 所以这里不 SystemExit，而是把"这一档的侧栏不判"打在读数里 ——
    # 一把只会红或者只会绿的尺都不算尺，它得能区分"没量到"和"量到没问题"。
    lines.append('      侧栏带数=%d%s' % (n_shown, '' if n_shown == 6 else
                 ' ⇒ SIDEBAR_BLIND 这一档的侧栏逐行**不判**（未选中行的墨读不到；'
                 'D-090 合成前极性 / BACKLOG 126 同一列里两种解析，均已登记）'))


def scan(shots, frame, label, lines):
    path = os.path.join(shots, frame)
    if not os.path.exists(path):
        lines.append('  %s NO-FRAME %s' % (label, frame))
        return
    rows, ch, w, h = load(path)
    # 帧名即尺寸（R18 那条规矩），所以 scale 从名字推而不是猜一个 2.0；
    # 第一次跑写成 `frame.split('x')[1]` —— 那是 `540-light.png`，直接 ValueError。
    import re as _re
    m = _re.search(r'-(\d+)x(\d+)-', frame)
    if not m:
        raise SystemExit('帧名里没有 WxH ⇒ 这一帧的尺寸没有出处，别用猜的 scale')
    s = w / float(m.group(1))
    split = column_split(rows, ch, w, h)
    page = median_color_in(rows, ch, split + 40, w - 40, 8, 40)
    lines.append('  %s 尺寸=%dx%dpx(scale=%.3g) 内容列左界=%.1fpt 页面底=%s'
                 % (label, w, h, s, split / s, page))
    cards = card_boxes(rows, ch, w, h, page, split)
    sidebar_rows(rows, ch, w, h, split, s, lines)
    for ci, (cx0, cx1, cy0, cy1) in enumerate(cards, 1):
        fill = median_color_in(rows, ch, cx0 + 6, cx1 - 6, cy0 + 6, cy1 - 6)
        lines.append('    卡片#%d 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=%s'
                     % (ci, cx0 / s, cy0 / s, cx1 / s, cy1 / s, fill))
        inner = [b for b in boxes(rows, ch, cx0 + 3, cx1 - 2, cy0 + 3, cy1 - 1, fill)
                 if (b[1] - b[0]) / s >= 24 and (b[3] - b[2]) / s >= 14]
        for (bx0, bx1, by0, by1) in sorted(inner, key=lambda b: (b[2], b[0])):
            bfill = median_color_in(rows, ch, bx0 + 3, bx1 - 3, by0 + 3, by1 - 3)
            ink, n, cr = ink_of(rows, ch, bx0, bx1, by0, by1, bfill)
            lines.append('      控件 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=%s 墨=%s 颗=%d 对比=%.2f '
                         '左隙=%.1f 右隙=%.1f 上隙=%.1f 下隙=%.1f'
                         % (bx0 / s, by0 / s, bx1 / s, by1 / s, bfill, ink, n, cr,
                            (bx0 - cx0) / s, (cx1 - bx1) / s, (by0 - cy0) / s, (cy1 - by1) / s))
        # 文字带的左轴：卡片里所有"离填充够远"的墨像素按行分段，取每段最左
        lefts = []
        for y in range(cy0 + 4, cy1 - 3, 2):
            seg = [x for x in range(cx0 + 2, cx1 - 2) if dist(px(rows, ch, x, y), fill) >= 60]
            if len(seg) >= 6:
                lefts.append(min(seg))
        if lefts:
            lines.append('      文字带左沿：min=%.1f 众数=%.1f 最大=%.1fpt（散布>2pt 就是没共用一条轴）'
                         % (min(lefts) / s, sorted(lefts)[len(lefts) // 2] / s, max(lefts) / s))


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r94_shots'
    lines = []
    for theme in ('light', 'dark'):
        lines.append('== 主题 %s' % theme)
        scan(shots, 'settings-shortcuts-720x540-%s.png' % theme, '快捷键', lines)
        scan(shots, 'settings-data-720x540-%s.png' % theme, '数据（对照）', lines)
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
