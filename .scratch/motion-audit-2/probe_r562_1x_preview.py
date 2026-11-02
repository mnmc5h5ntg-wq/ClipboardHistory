#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R562 一次性 1x 体检（**降采样代理**，不是真 1x 帧）：把 2x 帧缩到 1x 再跑同一把尺的筛子。

为什么要做：这条判据要上 runner（那台机器是 1x），而本机拍不出真 1x 帧 ——
R559/R561 的教训是「新判据上 runner 之前先量一次 1x 上这把尺还剩多少分辨率」，
量不出来就走具名出口，而不是拿降采样当参数改。

它**能**回答的：四道筛（y 窗口、项目符宽度、与正文的间隙、列合并容差）在 1x 的像素预算下还剩多少余量。
它**不能**回答的：runner 的字体渲染与本机不是同一台机器 ⇒ 真读数仍归 R563 ⓪。
"""
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r562-frames'
NAME = 'detail-markdown-bullet-nested-720x520-%s.png'


def flags_and_bands(px, w, h, x0, x1, y0, is_dark):
    def ink(x, y):
        r, g, b = px[x, y][:3]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return (lum >= 70) if is_dark else (lum <= 210)
    bands = []
    top = None
    for y in range(y0, h):
        hit = any(ink(x, y) for x in range(x0, x1))
        if hit and top is None:
            top = y
        if not hit and top is not None:
            bands.append((top, y - 1))
            top = None
    if top is not None:
        bands.append((top, h - 1))
    return bands


def rows(px, bands, x0, x1, is_dark):
    def ink(x, y):
        r, g, b = px[x, y][:3]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return (lum >= 70) if is_dark else (lum <= 210)
    out = []
    for (t, b) in bands:
        cols = [x for x in range(x0, x1) if any(ink(x, y) for y in range(t, b + 1))]
        segs = []
        for x in cols:
            if segs and x == segs[-1][1] + 1:
                segs[-1] = (segs[-1][0], x)
            else:
                segs.append((x, x))
        if len(segs) < 2:
            continue
        out.append((segs[0][1] - segs[0][0] + 1, segs[1][0] - segs[0][1], segs[1][0]))
    return out


def main():
    for tag in ('light', 'dark'):
        path = os.path.join(SRC, NAME % tag)
        im = Image.open(path).convert('RGB')
        is_dark = tag == 'dark'
        for scale in (2.0, 1.0):
            w = int(round(720 * scale))
            small = im if scale == 2.0 else im.resize((w, int(round(520 * scale))), Image.LANCZOS)
            px = small.load()
            x0, x1 = int(round(16 * scale)), int(round(520 * scale))
            y0 = int(round(60 * scale))
            bs = rows_with_min_height(flags_and_bands(px, small.width, small.height, x0, x1, y0, is_dark))
            rr = rows(px, [(t, b) for (t, b) in bs], x0, x1, is_dark)
            wmax = int(round(8.0 * scale))
            gmin = int(round(4.0 * scale))
            kept = [r for r in rr if r[0] <= wmax and r[1] >= gmin]
            cols = sorted(r[2] for r in kept)
            merge = max(1, int(round(0.5 * scale)))
            clusters = []
            for x in cols:
                if clusters and x - clusters[-1][0] <= merge:
                    clusters[-1].append(x)
                else:
                    clusters.append([x])
            lefts = [c[0] for c in clusters]
            steps = [b - a for a, b in zip(lefts, lefts[1:])]
            print('%s %.1fx 带=%d 行=%d 筛后=%d 列=%d 左沿=%s 步进=%s 容差=%dpx 步进地板=%dpx'
                  % (tag, scale, len(bs), len(rr), len(kept), len(clusters), lefts, steps,
                     max(1, int(round(1.0 * scale))), int(round(8.0 * scale))))


def rows_with_min_height(bands):
    return [(t, b) for (t, b) in bands if b - t >= 1]


if __name__ == '__main__':
    main()
