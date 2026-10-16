#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R89 的真实视觉审查腿：把菜单栏面板那三个状态 × 两个模式**量一遍再看一眼**。

为什么这一轮要回到产品像素上：R85–R89 连着五轮都在修仪器，而目标要求每轮都有
"看渲染出来的画面"这一腿。本轮零产品改动 ⇒ 上一轮（R87）那次捕获就是当前产品的像素，
不需要重新构建（重新构建也做不到 —— 验证卷正在跑，`.build` 有锁）。

量三件事，都是**没有现成判据覆盖**的（现成的那些在 Swift 侧，管的是行/详情/热图）：
1. 每一行墨的水平跨度：左边距是不是同一条轴，右边距有没有哪一行被切到容器边（R34 那一族的回归）；
2. 每行峰值亮度对**同一行左右两侧的背景**的 WCAG 比（说明档那一族的地板，菜单栏面板此前没量过）；
3. 状态之间的差别是否真的看得见（empty / refreshing / recommendations 三态）。

亮度用 `scripts/frame_audit.py` 的 `luminance()`（Rec.709），与既有 Python 判据同一颗尺；
对比度比是标准 WCAG 公式，**这里只是审查读数，不是登记判据** —— 判据本体在 Swift 侧。

用法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r89_menubar_review.py [shots目录]
"""
import os
import sys

sys.path.insert(0, '/Users/wangziyi/Codex_Project0/scripts')
from frame_audit import read_png, luminance  # 同一颗尺

INK_DELTA = 6          # 与同行中位数亮度差这么多才算"有墨"（抗噪）
MIN_INK = 3            # 一行至少 3 个墨像素才算一条文字带


def median(values):
    s = sorted(values)
    return s[len(s) // 2] if s else 0


def ratio(a, b):
    hi, lo = (a, b) if a >= b else (b, a)
    return (hi + 0.05) / (lo + 0.05)


def norm(lum255):
    return lum255 / 255.0


def analyse(path):
    width, height, channels, pixels = read_png(path)
    stride = width * channels
    bands, cur = [], None
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        lums = []
        for x in range(width):
            base = x * channels
            lums.append(luminance(row[base:base + channels]))
        bg = median(lums)
        ink = [x for x, l in enumerate(lums) if abs(l - bg) >= INK_DELTA]
        if len(ink) >= MIN_INK:
            peak = max(ink, key=lambda x: abs(lums[x] - bg))
            if cur is None or y - cur['y1'] > 2:
                if cur:
                    bands.append(cur)
                cur = {'y0': y, 'y1': y, 'x0': min(ink), 'x1': max(ink),
                       'bg': bg, 'peak': lums[peak]}
            else:
                cur['y1'] = y
                cur['x0'] = min(cur['x0'], min(ink))
                cur['x1'] = max(cur['x1'], max(ink))
                p = max(ink, key=lambda x: abs(lums[x] - bg))
                if abs(lums[p] - cur['bg']) > abs(cur['peak'] - cur['bg']):
                    cur['peak'] = lums[p]
    if cur:
        bands.append(cur)
    return width, height, bands


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r87/shots'
    # 前缀可换：正对照要拿**已知有内边距**的帧来跑（settings-data-* / content-with-history-*），
    # 否则这颗尺报出的"左边距=0"到底是产品贴边还是尺坏了，分不开。
    prefix = sys.argv[2] if len(sys.argv) > 2 else 'menubar-'
    names = [n for n in sorted(os.listdir(shots)) if n.startswith(prefix) and n.endswith('.png')]
    if not names:
        print('MENUBAR_REVIEW=no_frames %s' % shots)
        return 1
    print('%s_REVIEW frames=%d' % (prefix.rstrip('-'), 0) if False else 'MENUBAR_REVIEW frames=%d 尺=frame_audit.luminance(Rec.709) INK_DELTA=%d' % (len(names), INK_DELTA))
    left_axes = []
    for n in names:
        w, h, bands = analyse(os.path.join(shots, n))
        print('== %s  %dx%d(px)  文字带=%d' % (n, w, h, len(bands)))
        for b in bands:
            c = ratio(norm(max(b['peak'], 0)), norm(b['bg']))
            left = b['x0']
            right_gap = w - 1 - b['x1']
            left_axes.append((n, b['y0'], left))
            print('   y=%3d-%3d  x=%3d-%3d  左边距=%3d 右边距=%3d  墨=%3d 背景=%3d 对比=%.2f:1'
                  % (b['y0'], b['y1'], b['x0'], b['x1'], left, right_gap, b['peak'], b['bg'], c))
    # 同一张帧里左边距必须一致（左轴统一那一族），跨帧也报出来给人看
    print('MENUBAR_LEFT_AXIS_MIN=%d MAX=%d' % (min(l for _, _, l in left_axes),
                                               max(l for _, _, l in left_axes)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
