#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACKLOG 71 的**预览**测量：暗/亮两档下，热图格子的相邻台阶差多少。

这不是判据，是**看图时顺手把话说明白**：R47 我看到暗档图例最左那一格"几乎与背景同色"，
但"几乎"不是一个数。这个脚本把帧里出现最多的几种颜色连同它们的**位置框**一起打出来 ——
位置框是防上一轮那一族错误的：整窗像素会把颜色归给错的元素，
所以每个颜色必须能对上"它确实在某一格里"。

用法：heat_ladder_preview.py <png> [<png> …]
台阶怎么认：格子是这张图里唯一的大块纯色，所以按像素数排序后，
背景是第一名，其余按 y 坐标分组成"行"，每行的众数就是那一档的填充色。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from frame_audit import read_png, pixel_rows, luminance   # noqa: E402


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


def preview(path):
    width, height, channels, pixels = read_png(path)
    boxes = color_boxes(width, height, channels, pixels)
    ranked = sorted(boxes.items(), key=lambda kv: -kv[1][4])
    print("\n=== %s (%dx%d) ===" % (os.path.basename(path), width, height))
    top = [(c, b) for c, b in ranked if b[4] >= 60][:10]
    background = top[0]
    print("背景候选 %s 亮度=%d 像素=%d 框=%s"
          % (background[0], luminance(background[0]), background[1][4], background[1][:4]))
    steps = []
    for color, box in top[1:]:
        steps.append((luminance(color), color, box))
    steps.sort()
    print("格子填充色按亮度排序（Δ = 与前一档的亮度差；这把尺沿用 perceptibleBand255=18）：")
    previous = luminance(background[0])
    for lum, color, box in steps:
        print("  L=%3d  %s  像素=%5d  框=[%d,%d,%d,%d]  距上一档 Δ=%+d"
              % (lum, color, box[4], box[0], box[1], box[2], box[3], lum - previous))
        previous = lum


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for path in sys.argv[1:]:
        preview(path)
    return 0


main()
