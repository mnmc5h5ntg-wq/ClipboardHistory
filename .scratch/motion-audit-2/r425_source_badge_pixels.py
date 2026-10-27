#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R425：详情状态条来源图标的旧/新像素读数（同一张 detail-0-text，同一块带子）。

旧帧目录 = R424 落盘的那份捕获（没有图标）；新帧目录 = R425 重捕。
读数全部从 PNG 现数：图标格（20..34 × 36..50 pt）的彩色/墨、头部带（x 全宽，y 36..48 pt）
的首/末墨沿与墨量、文字起点（跳过图标格后的首墨沿）。坐标按图宽 / 720 推倍率，不写死 2x。
"""
import sys
from PIL import Image


def load(path):
    image = Image.open(path).convert("RGB")
    return image, image.width / 720.0


def paper(image):
    px = image.load()
    counts = {}
    for y in range(image.height):
        for x in range(min(8, image.width)):
            v = sum(px[x, y]) // 3
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def box_read(image, density, rect, skip_left=None):
    px = image.load()
    x0 = int(rect[0] * density)
    x1 = int(rect[2] * density)
    y0 = int(rect[1] * density)
    y1 = int(rect[3] * density)
    base = paper(image)
    ink = colored = 0
    first = last = None
    for y in range(y0, min(y1, image.height)):
        for x in range(x0, min(x1, image.width)):
            r, g, b = px[x, y]
            luma = round(0.2126 * r + 0.7152 * g + 0.0722 * b)
            if skip_left is not None and x < int(skip_left * density):
                continue
            if abs(luma - base) > 24:
                ink += 1
                first = x if first is None else min(first, x)
                last = x if last is None else max(last, x)
            if max(r, g, b) - min(r, g, b) > 40:
                colored += 1
    return ink, colored, first, last


def main(old_dir, new_dir):
    old, od = load(old_dir + "/detail-0-text-720x520-light.png")
    new, nd = load(new_dir + "/detail-0-text-720x520-light.png")
    for tag, image, density in (("旧", old, od), ("新", new, nd)):
        badge = box_read(image, density, (20, 36, 34, 50))
        band = box_read(image, density, (0, 36, 720, 48))
        text = box_read(image, density, (36, 36, 720, 48))
        print("%s 图标格 墨=%d 彩色=%d｜头部带 墨=%d 首=%s 末=%s｜文字起点=%s"
              % (tag, badge[0], badge[1], band[0],
                 "%.1fpt" % (band[2] / density) if band[2] is not None else "无",
                 "%.1fpt" % (band[3] / density) if band[3] is not None else "无",
                 "%.1fpt" % (text[2] / density) if text[2] is not None else "无"))
    print("R425_SOURCE_BADGE_PIXELS 旧彩色=%d 新彩色=%d" % (
        box_read(old, od, (20, 36, 34, 50))[1],
        box_read(new, nd, (20, 36, 34, 50))[1]))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法：python3 r425_source_badge_pixels.py <旧帧目录> <新帧目录>")
        raise SystemExit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
