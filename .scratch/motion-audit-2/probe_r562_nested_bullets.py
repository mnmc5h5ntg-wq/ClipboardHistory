#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R562 一次性像素探针：三级项目符在帧上的墨 bbox（只看，不当判据；判据要另写）。

用法：python3 .scratch/motion-audit-2/probe_r562_nested_bullets.py [帧目录]
"""
import os
import sys

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r562-frames'
NAME = 'detail-markdown-bullet-nested-720x520-%s.png'
WIDTH_PT = 720.0


def rows_with_ink(px, x0, x1, y0, y1, is_dark):
    out = []
    for y in range(y0, y1):
        hit = False
        for x in range(x0, x1):
            r, g, b = px[x, y][:3]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if (lum >= 70) if is_dark else (lum <= 210):
                hit = True
                break
        out.append(hit)
    return out


def bands(flags, start):
    res = []
    top = None
    for i, h in enumerate(flags):
        if h and top is None:
            top = i
        if not h and top is not None:
            res.append((top + start, i - 1 + start))
            top = None
    if top is not None:
        res.append((top + start, len(flags) - 1 + start))
    return res


def ink_columns(px, x0, x1, y0, y1, is_dark):
    cols = {}
    for x in range(x0, x1):
        n = 0
        for y in range(y0, y1):
            r, g, b = px[x, y][:3]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if (lum >= 70) if is_dark else (lum <= 210):
                n += 1
        if n:
            cols[x] = n
    return cols


def runs(cols):
    xs = sorted(cols)
    out = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1] = (out[-1][0], x)
        else:
            out.append((x, x))
    return out


def main():
    for tag in ('light', 'dark'):
        path = os.path.join(ROOT, NAME % tag)
        if not os.path.exists(path):
            print('MISSING %s' % path)
            continue
        im = Image.open(path).convert('RGB')
        px = im.load()
        scale = im.width / WIDTH_PT
        is_dark = tag == 'dark'
        print('== %s scale=%.1fx size=%dx%d' % (tag, scale, im.width, im.height))
        flags = rows_with_ink(px, int(16 * scale), int(520 * scale), 0, im.height, is_dark)
        bs = [b for b in bands(flags, 0) if b[1] - b[0] >= 3]
        print('   带数=%d 前 12 条=%s' % (len(bs), [(t, b) for t, b in bs[:12]]))
        for (t, b) in bs:
            cols = ink_columns(px, int(14 * scale), int(520 * scale), t, b + 1, is_dark)
            rr = runs(cols)
            # 一行里的第一段墨 = 项目符；后面紧跟的段 = 正文首字
            first = rr[0] if rr else None
            second = rr[1] if len(rr) > 1 else None
            if not first:
                continue
            fh = max(cols[x] for x in range(first[0], first[1] + 1) if x in cols)
            print('   行 y=%d..%d 第一段 x=%d..%d 宽=%dpx(%.2fpt) 高≤%dpx(%.2fpt) 第二段 x=%s 间隙=%s'
                  % (t, b, first[0], first[1], first[1] - first[0] + 1,
                     (first[1] - first[0] + 1) / scale, fh, fh / scale,
                     ('%d..%d' % second) if second else '-',
                     (second[0] - first[1]) if second else '-'))
            # 该段内的真实墨高（只看这一段列范围）
            ys = [y for y in range(t, b + 1)
                  for x in range(first[0], first[1] + 1)
                  if (lambda r, g, bb: ((0.299 * r + 0.587 * g + 0.114 * bb) >= 70) if is_dark
                      else ((0.299 * r + 0.587 * g + 0.114 * bb) <= 210))(*px[x, y][:3])]
            if ys:
                print('        项目符墨 bbox 高=%dpx(%.2fpt) y=%d..%d'
                      % (max(ys) - min(ys) + 1, (max(ys) - min(ys) + 1) / scale, min(ys), max(ys)))


if __name__ == '__main__':
    main()
