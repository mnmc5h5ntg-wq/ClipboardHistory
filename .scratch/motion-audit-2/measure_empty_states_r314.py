# -*- coding: utf-8 -*-
"""R314 的前置测量：空状态那一句墨，落在框的哪个高度上？

为什么要量：R313 的看图腿记了一句读数 —— 热图空状态的文字行在 150pt 高的框里位于 y≈46，
下方留白约 69%。当时**没有**把它变成工单，理由是"在与同框其他空状态对比之前，偏多不构成缺陷"。
这一支就是那步对比：把所有 `*empty*` 帧的墨带（相对本帧众数背景、最大通道差 > 阈值）
的垂直范围与中心比例量出来，让"是不是异类"变成一个读数而不是形容词。

只读不改；不打印任何用户内容（这些帧本来就是夹具造的空状态/占位状态）。
用法：python3 .scratch/motion-audit-2/measure_empty_states_r314.py [帧目录]
结论行：`EMPTY_INK <帧名> 尺寸=WxH 墨带=[y0..y1] 高=.. 中心比例=.. 底部留白比例=..`
"""
import os
import sys
from collections import Counter

from PIL import Image

THRESHOLD = 20  # 与近背景像素的判定沿用仓库那把尺（近墨像素 ≥20）


def mode_background(pixels, w, h):
    """众数背景：按 4x 下采样取点，避免整帧扫描（这些帧很小，但保持便宜）。"""
    c = Counter()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            c[pixels[x, y]] += 1
    return c.most_common(1)[0][0]


def ink_band(path):
    img = Image.open(path).convert(u"RGB")
    w, h = img.size
    px = img.load()
    bg = mode_background(px, w, h)
    rows = []
    for y in range(h):
        hit = 0
        for x in range(w):
            p = px[x, y]
            if max(abs(p[0] - bg[0]), abs(p[1] - bg[1]), abs(p[2] - bg[2])) > THRESHOLD:
                hit += 1
        if hit >= 3:  # 单像素噪声不算一行墨
            rows.append(y)
    if not rows:
        return w, h, None, None, 0
    y0, y1 = rows[0], rows[-1]
    return w, h, y0, y1, len(rows)


def main(directory):
    names = sorted(n for n in os.listdir(directory)
                   if n.endswith(u".png") and u"empty" in n)
    if not names:
        print(u"EMPTY_INK_NO_FRAMES 目录=%s 里没有 empty 帧 ⇒ 这条测量没在量任何东西" % directory)
        return 1
    for n in names:
        w, h, y0, y1, k = ink_band(os.path.join(directory, n))
        if y0 is None:
            print(u"EMPTY_INK %s 尺寸=%dx%d 墨带=无（阈值 %d 之下）" % (n, w, h, THRESHOLD))
            continue
        center = (y0 + y1) / 2.0 / h
        bottom = 1.0 - (y1 + 1) / float(h)
        print(u"EMPTY_INK %s 尺寸=%dx%d 墨带=[%d..%d] 高=%d 中心比例=%.3f 底部留白比例=%.3f"
              % (n, w, h, y0, y1, y1 - y0 + 1, center, bottom))
    print(u"EMPTY_INK_DONE 帧数=%d 阈值=%d" % (len(names), THRESHOLD))
    return 0


if __name__ == u"__main__":
    d = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith(u"-") else u"/tmp/r313_verify/frames"
    sys.exit(main(d))
