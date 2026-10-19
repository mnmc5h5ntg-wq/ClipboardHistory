#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 看图腿的读数器：把浮层/菜单栏那几张帧按**行带**量出来，供台账引用。

为什么要有这个文件而不是"我看了一眼图"：本轮的结论是"没有新的可判项"，
而"没有"必须能被复查 —— 它得交出我读过的那串行带（y 区间、高度、峰值墨像素），
否则就又是一句形容词（这一族已经犯过七次）。
只读帧、不写仓库、不打印任何用户内容（帧本身是合成夹具，这里只输出坐标与计数）。
"""
import io, sys
from PIL import Image


def lum(p):
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def bands(path, step=2, thresh=24, min_ink=3):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    out, cur = [], None
    for y in range(h):
        cnt = {}
        for x in range(0, w, step):
            c = px[x, y]
            cnt[c] = cnt.get(c, 0) + 1
        bg = max(cnt, key=cnt.get)
        ink = sum(n for c, n in cnt.items() if abs(lum(c) - lum(bg)) > thresh)
        on = ink > min_ink
        if on and cur is None:
            cur = [y, y, ink]
        elif on:
            cur[1] = y
            cur[2] = max(cur[2], ink)
        elif cur is not None:
            out.append(tuple(cur))
            cur = None
    if cur is not None:
        out.append(tuple(cur))
    return im.size, out


FRAMES = [
    "/tmp/shots_r197/quickpick-typed-420x300-light.png",
    "/tmp/shots_r197/quickpick-hover-420x300-dark.png",
    "/tmp/shots_r197/quickpick-list-420x300-light.png",
    "/tmp/shots_r197/menubar-recommendations-320x320-dark.png",
]

if __name__ == "__main__":
    missing = 0
    for f in FRAMES:
        try:
            (w, h), bs = bands(f)
        except (IOError, OSError) as e:
            print("BANDS_FRAME_MISSING %s ⇒ %s" % (f, e))
            missing += 1
            continue
        print("BANDS %s 尺寸=%dx%d 行带=%d" % (f.split('/')[-1], w, h, len(bs)))
        for y0, y1, peak in bs:
            print("   y=%d..%d 高=%d 峰值墨=%d" % (y0, y1, y1 - y0 + 1, peak))
    if missing:
        print("BANDS_NOT_RUN 缺 %d 张帧 ⇒ 看图腿这一格不许记成看过" % missing)
        sys.exit(1)
    print("BANDS_OK 帧=%d" % len(FRAMES))
