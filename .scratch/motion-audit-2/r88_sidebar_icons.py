#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R88 的看图仪器（设置侧栏）：那一列六个图标，是不是每个都和它的兄弟一样看得见。

为什么要有这个脚本：刚才用眼睛看 `settings-data-720x540-dark.png`，
"推荐"那一行的图标明显比上下几行淡，而"看起来淡"不是一条可以被证伪的读数。
⇒ 把它量出来：每行分别量**图标框**与**文字框**，两者都要报，
   因为"整行都淡"（行被禁用）与"只有图标淡"（图标自己的着色问题）是两种不同的病。

参照点用侧栏自己的空白行（不是角点、不是另一张图的数），
判据用**最大通道值**而不是亮度 —— 灰和蓝在亮度轴上可以很近（R54 / U-80 那一课）。

用法：python3 .scratch/motion-audit-2/r88_sidebar_icons.py /tmp/r87/shots
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode   # 同一个 PNG 解码器，不引第三方依赖

# 侧栏在 720pt 宽的帧（2x = 1440px）里的列位置：先扫出来再钉死，见下面的自检。
SIDEBAR_ICON_X = (88, 150)
SIDEBAR_LABEL_X = (170, 420)
INK_DELTA = 40          # 与背景的最大通道差，超过才算"有墨"
MIN_BAND_ROWS = 3       # 一行文字至少要有这么多个含墨行才算一个带


def px(rows, ch, x, y):
    line = rows[y]
    o = x * ch
    return line[o], line[o + 1], line[o + 2]


def maxc(p):
    return max(p[0], p[1], p[2])


def background(rows, ch, w, h, x0, x1):
    """侧栏背景：在图标列左边那条没有字的窄带上取中位数。"""
    vals = []
    for y in range(int(h * 0.10), int(h * 0.90), 7):
        for x in range(20, 60):
            vals.append(maxc(px(rows, ch, x, y)))
    vals.sort()
    return vals[len(vals) // 2]


def bands(rows, ch, x0, x1, h, bg):
    """把文字列按"这一行有没有墨"切成若干水平带，返回每带的 (y0, y1)。"""
    inked = []
    for y in range(h):
        n = sum(1 for x in range(x0, x1) if maxc(px(rows, ch, x, y)) - bg >= INK_DELTA)
        inked.append(n)
    out, start = [], None
    for y, n in enumerate(inked):
        if n >= 2 and start is None:
            start = y
        elif n < 2 and start is not None:
            if y - start >= MIN_BAND_ROWS:
                out.append((start, y))
            else:
                start = None
    if start is not None:
        out.append((start, h))
    # 合并相邻带（同一行文字里字与字之间的空隙会把带切开）
    merged = []
    for b in out:
        if merged and b[0] - merged[-1][1] <= 12:
            merged[-1] = (merged[-1][0], b[1])
        else:
            merged.append(list(b))
            merged[-1] = b
    return [tuple(m) for m in merged]


def measure(rows, ch, w, h, bg, box, band):
    x0, x1 = box
    y0, y1 = band
    pad = 6
    ys = range(max(0, y0 - pad), min(h, y1 + pad))
    best, ink, hist = 0, 0, []
    for y in ys:
        row_ink = 0
        for x in range(x0, x1):
            p = px(rows, ch, x, y)
            d = maxc(p) - bg
            if d >= INK_DELTA:
                row_ink += 1
                best = max(best, maxc(p))
                hist.append(p)
        ink += row_ink
    # 色相：墨最重的那批像素里，哪个通道最高（蓝=2，灰=三通道接近）
    dom = 'gray'
    if hist:
        r = sum(p[0] for p in hist) / len(hist)
        g = sum(p[1] for p in hist) / len(hist)
        b = sum(p[2] for p in hist) / len(hist)
        dom = 'blue' if b - max(r, g) >= 25 else 'gray'
    return ink, best, dom


LABELS = ['快捷键', '通用', '隐私', '推荐', '数据', '统计']


def report(path):
    if not os.path.exists(path):
        print('MISSING=%s' % path)
        return
    w, h, ch, rows = decode(path)
    bg = background(rows, ch, w, h, *SIDEBAR_LABEL_X)
    bs = bands(rows, ch, *SIDEBAR_LABEL_X, h, bg)
    print('--- %s  %dx%d  侧栏背景最大通道=%d  文字带=%d 个' % (os.path.basename(path), w, h, bg, len(bs)))
    if len(bs) != len(LABELS):
        print('BAND_COUNT_MISMATCH=%d 期望=%d ⇒ 带切法在这张图上不成立，下面的数不许引用'
              % (len(bs), len(LABELS)))
        return
    for name, b in zip(LABELS, bs):
        icon_ink, icon_max, icon_dom = measure(rows, ch, w, h, bg, SIDEBAR_ICON_X, b)
        text_ink, text_max, text_dom = measure(rows, ch, w, h, bg, SIDEBAR_LABEL_X, b)
        print('ROW %-4s 带y=%d-%d  图标 墨=%-5d 峰=%-3d 色=%-4s  文字 墨=%-6d 峰=%-3d 色=%s'
              % (name, b[0], b[1], icon_ink, icon_max, icon_dom, text_ink, text_max, text_dom))


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r87/shots'
    for f in ('settings-data-720x540-dark.png', 'settings-data-720x540-light.png',
              'settings-stats-720x540-dark.png', 'settings-general-720x540-dark.png'):
        report(os.path.join(shots, f))


if __name__ == '__main__':
    main()
