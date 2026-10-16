#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R91 的看图仪器（焦点环 / 选中带的主语是谁）：BACKLOG 127 的第一步正对照。

红话里写的是"一行变成两个半宽 KeyViewProxy"，那句是**无障碍树**的形状，不是像素。
⇒ 先看像素这一侧：焦点环与选中带到底横跨多少 —— 如果环只画半行，那 127 就是产品缺陷；
   如果环横跨整行，那两个半宽代理就只是**可焦点单元**的拆分（Tab 停两次），
   而探针那条"宽 200…290"的期望量的不是像素 ⇒ 127 的两种成因要分开记。
"""
import os, sys
sys.path.insert(0, '/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2')
from r86_heatmap_legend import decode

def px(rows, ch, x, y):
    o = x * ch; l = rows[y]; return l[o], l[o+1], l[o+2]

def blue(p):
    return p[2] - max(p[0], p[1]) >= 40 and p[2] >= 120

def run(path):
    if not os.path.exists(path):
        print('MISSING=%s' % path); return
    w, h, ch, rows = decode(path)
    print('=== %s  %dx%d px' % (os.path.basename(path), w, h))
    # 逐行找蓝：焦点环与选中带都是蓝，分开看每一段
    segs, start = [], None
    for y in range(h):
        xs = [x for x in range(0, w, 2) if blue(px(rows, ch, x, y))]
        if len(xs) >= 3:
            if start is None:
                start = [y, y, min(xs), max(xs), len(xs)]
            else:
                start[1] = y; start[2] = min(start[2], min(xs)); start[3] = max(start[3], max(xs))
                start[4] += len(xs)
        else:
            if start is not None and start[1] - start[0] >= 4:
                segs.append(tuple(start))
            start = None
    if start is not None: segs.append(tuple(start))
    if not segs:
        print('    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了')
        return
    for i, (y0, y1, x0, x1, n) in enumerate(segs):
        print('    带%d px y=%d-%d x=%d-%d  宽=%.0f%%帧宽 高=%dpx 蓝像素=%d'
              % (i + 1, y0, y1, x0, x1, 100.0 * (x1 - x0) / w, y1 - y0 + 1, n))
    leftmost = min(s[2] for s in segs); rightmost = max(s[3] for s in segs)
    print('    蓝区总跨度 x=%d..%d ⇒ 占帧宽 %.0f%%（左/右留白 %d / %d px）'
          % (leftmost, rightmost, 100.0 * (rightmost - leftmost) / w, leftmost, w - rightmost))

for f in ('focus-after-tab-light.png', 'focus-after-tab-dark.png',
          'reveal-after-320x300-light.png'):
    run(os.path.join('/tmp/r91_shots_after2', f))
