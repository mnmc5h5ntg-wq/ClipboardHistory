#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACKLOG 71 的**预览**测量：暗/亮两档下，热图格子的相邻台阶差多少。

这不是判据，是**看图时顺手把话说明白**：R47 我看到暗档图例最左那一格"几乎与背景同色"，
但"几乎"不是一个数。这个脚本把帧里出现最多的几种颜色连同它们的**位置框**一起打出来 ——
位置框是防上一轮那一族错误的：整窗像素会把颜色归给错的元素。

**第一版把台阶归错了位**（R51 自己抓到，已写进台账）：它按亮度排序，于是
"空格子"（`primary.opacity(0.055)`，是**灰**的）与"第 1 档"（`accent.opacity(0.18)`，是**蓝**的）
在亮档里被排成了相邻的两级，暗档里又排成了另外两级 —— 同一张图，两档外观给出两套台阶次序。
现在改成**按身份配对**：
  ① 每种颜色的**像素数**是它的指纹（同一档在亮/暗两帧里占的像素数完全相同）；
  ② 台阶次序由令牌决定，不由亮度决定：`empty` 是灰（`primary`），
     四档数据是蓝（`accent`），暗档 α 越大越亮、亮档 α 越大越暗 ——
     所以暗档按亮度升序、亮档按亮度降序，两边必须配成同一串像素数，配不上就报错。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from frame_audit import read_png, luminance   # noqa: E402

# 令牌顺序（`VisualHeat`）：empty 是 primary，四档是 accent。
TOKENS = ["empty(primary 0.055)", "L1(accent 0.18)", "L2(accent 0.34)",
          "L3(accent 0.56)", "L4(accent 0.85)"]


def color_boxes(width, height, channels, pixels):
    stride = width * channels
    boxes = {}
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        for x in range(width):
            base = x * channels
            pixel = tuple(row[base:base + channels])
            box = boxes.get(pixel)
            if box is None:
                boxes[pixel] = [x, y, x, y, 1]
            else:
                box[0] = min(box[0], x)
                box[1] = min(box[1], y)
                box[2] = max(box[2], x)
                box[3] = max(box[3], y)
                box[4] += 1
    return boxes


def steps(path, minimum_pixels=60):
    """返回 (背景, [(像素数, 亮度, 颜色, 框), …] 按令牌顺序)。"""
    width, height, channels, pixels = read_png(path)
    boxes = color_boxes(width, height, channels, pixels)
    ranked = sorted(boxes.items(), key=lambda kv: -kv[1][4])
    background_color, background_box = ranked[0]
    cells = [(box[4], luminance(color), color, box[:4])
             for color, box in ranked[1:] if box[4] >= minimum_pixels]
    if len(cells) < len(TOKENS):
        raise SystemExit("HEAT_PREVIEW_TOO_FEW：只认出 %d 种格子色，需要 %d 种（%s）"
                         % (len(cells), len(TOKENS), path))
    # 暗档 α↑ ⇒ 亮度↑；亮档 α↑ ⇒ 亮度↓。方向由"与背景的差"决定，不靠猜。
    toward_brighter = sum(1 for c in cells if c[1] > luminance(background_color)) \
        >= sum(1 for c in cells if c[1] < luminance(background_color))
    ordered = sorted(cells, key=lambda c: c[1] if toward_brighter else -c[1])
    return (luminance(background_color), background_color, background_box), ordered[:len(TOKENS)]


def preview(paths):
    per_file = [(p, steps(p)) for p in paths]
    # 配对自检：两帧的**像素数序列**必须一模一样，否则"同一个台阶"这个说法不成立。
    fingerprints = [[c[0] for c in ordered] for _, (_, ordered) in per_file]
    if len(per_file) > 1 and any(f != fingerprints[0] for f in fingerprints[1:]):
        raise SystemExit("HEAT_PREVIEW_MISMATCH：两帧认出的格子像素数不一致 ⇒ "
                         "它们在比的不是同一批台阶，下面的 Δ 全部作废\n  %s" % fingerprints)
    for (path, (background, ordered)) in per_file:
        print("\n=== %s ===" % os.path.basename(path))
        print("背景 %s 亮度=%d 框=%s" % (background[1], background[0], background[2]))
        previous_lum = background[0]
        previous_color = background[1]
        for token, (count, lum, color, box) in zip(TOKENS, ordered):
            channels = [abs(int(color[i]) - int(previous_color[i])) for i in range(3)]
            print("  %-20s 像素=%5d 颜色=%s 亮度=%3d  Δ亮度=%+d  Δ各通道=%s（最大 %d）"
                  % (token, count, color, lum, lum - previous_lum, channels, max(channels)))
            previous_lum = lum
            previous_color = color
        print("  相邻档：Δ亮度 / Δ最大通道")
        previous_color = background[1]
        previous_lum = background[0]
        for count, lum, color, box in ordered:
            channels = [abs(int(color[i]) - int(previous_color[i])) for i in range(3)]
            print("    %+4d / %3d" % (lum - previous_lum, max(channels)))
            previous_lum = lum
            previous_color = color


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    preview(sys.argv[1:])
    return 0


main()
