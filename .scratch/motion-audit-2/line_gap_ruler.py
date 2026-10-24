#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""看图腿的一把尺：**正文行的行距**，用来判"alt 那句话有没有跟相邻段落挤成一坨"。

为什么要有它（R336 看图时眼睛先说出来、随后被要求换成数）：消毒把 `<img>` 换成 alt 文字之后，
那句话是**裸文本**（不在任何块元素里），它后面紧跟一个 `<p>`。屏幕上它看起来"好像少了点空隙"，
但"好像"不是读数 —— 形容词不许进台账（R155 那一族）。这一支尺给的是逐行的 y 带与带间距。

两条通道分开量（R335 的教训：暗档 bg=30 时"比背景暗 40"这把尺是瞎的）：
先取该区域的**众数亮度当背景**，再按 `|luma - bg| > 阈值` 判墨，两档同一把尺。

用法：`python3 .scratch/motion-audit-2/line_gap_ruler.py <帧.png> [x0 x1 y0 y1]`
"""
import sys

from PIL import Image

THRESH = 24
MIN_ROWS = 3


def bands(path, x0, x1, y0, y1):
    im = Image.open(path).convert(u"L")
    px = im.load()
    rows = []
    hist = {}
    for y in range(y0, y1):
        vals = [px[x, y] for x in range(x0, x1)]
        rows.append(vals)
        for v in vals:
            hist[v] = hist.get(v, 0) + 1
    bg = max(hist.items(), key=lambda kv: kv[1])[0]
    out = []
    cur = None
    for i, vals in enumerate(rows):
        ink = sum(1 for v in vals if abs(v - bg) > THRESH)
        if ink >= 3:
            if cur is None:
                cur = [y0 + i, y0 + i, ink]
            else:
                cur[1] = y0 + i
                cur[2] = max(cur[2], ink)
        else:
            if cur is not None and (cur[1] - cur[0]) >= 1:
                out.append(tuple(cur))
            cur = None
    if cur is not None:
        out.append(tuple(cur))
    return bg, out


def main():
    path = sys.argv[1]
    # 帧是 2x 抓的（720×520 pt 的窗口 = 1440×1040 px）⇒ 一律换算回 pt 再报，
    # 否则"行距 44"到底是 pt 还是 px，下一轮引用它的人只能猜（R107 那一族：尺的坐标约定）。
    box = [int(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [40, 1400, 120, 640]
    bg, bs = bands(path, box[0], box[1], box[2], box[3])
    print(u"LINE_GAP 帧=%s 区域=x%d..%d,y%d..%d px（÷2=pt） 背景众数=%d 行数=%d"
          % (path.split(u"/")[-1], box[0], box[1], box[2], box[3], bg, len(bs)))
    prev = None
    for top, bot, ink in bs:
        gap = u"-" if prev is None else u"%.1f" % ((top - prev) / 2.0)
        print(u"  行 y=%.1f..%.1f pt 高=%.1f 间距上一行=%s pt 最粗=%d px"
              % (top / 2.0, bot / 2.0, (bot - top + 1) / 2.0, gap, ink))
        prev = top
    # 结论行：把"间距"排成一行，段落间距 vs 行内间距 一眼比得出来
    tops = [b[0] for b in bs]
    steps = [u"%.1f" % ((tops[i + 1] - tops[i]) / 2.0) for i in range(len(tops) - 1)]
    print(u"LINE_GAP_STEPS_pt " + u",".join(steps))


main()
