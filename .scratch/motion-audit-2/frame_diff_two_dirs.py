#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""两帧目录逐张比：数出"变了哪几张"，并对指定那张给出**差集 bbox 与像素数**。

R338 需要它是因为两个读数长得像但意思相反：
① 与上一轮那 182 张逐张比 ⇒ 变了 4 张（全是 HTML 两档 × 渲染/原文）；
② 改前构建 vs 改后构建（同一份夹具）⇒ 只有 alt 那一行变，bbox=(40,460)..(358,487)。
只报 ① 会说错话（让人以为修法改了四张画面），只报 ② 也一样。所以这把尺**两种比法都要跑**，
并且把差集的 bbox 打出来 —— 位置才是"变了什么"的证人，个数不是。

它不进门（不 exit 1），它只给数。跑法：
  python3 .scratch/motion-audit-2/frame_diff_two_dirs.py <目录A> <目录B> [要细看的前缀...]
"""
from __future__ import annotations

import os
import sys

STEP = 3                    # 逐张"变没变"用 3px 采样（全像素太慢；变了 4 张这件事不需要逐位）


def main(argv):
    if len(argv) < 3:
        sys.stdout.write(u"用法：frame_diff_two_dirs.py <目录A> <目录B> [前缀...]\n")
        return 2
    from PIL import Image, ImageChops
    a_dir, b_dir = argv[1], argv[2]
    prefixes = argv[3:] or [u"detail-html-rendered"]
    names = sorted(n for n in os.listdir(b_dir) if n.endswith(u".png"))
    changed = []
    for n in names:
        a = os.path.join(a_dir, n)
        if not os.path.exists(a):
            changed.append(n)
            continue
        ia = Image.open(a).convert(u"RGB")
        ib = Image.open(os.path.join(b_dir, n)).convert(u"RGB")
        if ia.size != ib.size:
            changed.append(n)
            continue
        pa, pb = ia.load(), ib.load()
        if any(pa[x, y] != pb[x, y]
               for y in range(0, ia.size[1], STEP) for x in range(0, ia.size[0], STEP)):
            changed.append(n)
    sys.stdout.write(u"FRAME_DIFF 比了=%d 变了=%d\n" % (len(names), len(changed)))
    for n in changed:
        sys.stdout.write(u"  changed " + n + u"\n")
    for n in names:
        if not any(n.startswith(p) for p in prefixes):
            continue
        a, b = os.path.join(a_dir, n), os.path.join(b_dir, n)
        if not os.path.exists(a):
            sys.stdout.write(u"FRAME_DIFF_BBOX %s A 侧缺帧 ⇒ 不给数\n" % n)
            continue
        d = ImageChops.difference(Image.open(a).convert(u"RGB"),
                                  Image.open(os.path.join(b_dir, n)).convert(u"RGB"))
        g = d.convert(u"L").load()
        pts = [(x, y) for y in range(d.size[1]) for x in range(d.size[0]) if g[x, y] > 24]
        if not pts:
            sys.stdout.write(u"FRAME_DIFF_BBOX %s 变了=0 bbox=无\n" % n)
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        sys.stdout.write(u"FRAME_DIFF_BBOX %s 变了=%d bbox=(%d,%d)..(%d,%d)\n"
                         % (n, len(pts), min(xs), min(ys), max(xs), max(ys)))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv))
