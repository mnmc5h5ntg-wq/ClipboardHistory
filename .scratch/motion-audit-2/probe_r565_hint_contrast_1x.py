#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 补段 一次性探针：同一把尺的口径搬到 1x 代理上，secondary 与 tertiary 还分得出吗？

为什么要做：runner 那一跑把新判据 `HINT_CONTRAST` 判红在 light（3.84:1），而本机 2x 是 10.37:1。
两条解释（产品真的淡了 / 1x 判的不是同一个对象）必须用数分开，不许赌。
已知的两个数：tertiary（旧值）1x 代理 = light 3.15:1 / dark 4.34:1（`/tmp/r565-1x-preview.log`，
同一把尺、同一套筛）；secondary（新值）2x = light 10.37:1 / dark 10.92:1。
本探针补的是缺的那一格：secondary 在 1x 代理上是多少。

它**不能**回答的：这是 LANCZOS 降采样代理，不是 runner 的真 1x 帧 ⇒ 那一半只能由含新口径那一笔的
跑在 runner 上作证。
"""
import sys

from PIL import Image

INSET = 12.0     # QuickPickKeyboardHint.horizontalInset
BAND = 26.0      # 与判据同一条带：底部 26pt
LOGICAL_W, LOGICAL_H = 420.0, 300.0


def lin(v):
    c = v / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def rel_luma(p):
    return 0.2126 * lin(p[0]) + 0.7152 * lin(p[1]) + 0.0722 * lin(p[2])


def contrast(a, b):
    l1, l2 = rel_luma(a), rel_luma(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def read(img, tag):
    w, h = img.size
    s = w / LOGICAL_W
    x0, x1 = int(round(INSET * s)), min(w, int(round((LOGICAL_W - INSET) * s)))
    y0 = int(round((LOGICAL_H - BAND) * s))
    px = img.load()
    greys = {}
    rows = []
    for y in range(y0, h):
        for x in range(x0, x1):
            r, g, b = px[x, y][:3]
            grey = int(round(0.299 * r + 0.587 * g + 0.114 * b))
            greys[grey] = greys.get(grey, 0) + 1
            rows.append(((r, g, b), grey))
    bg_grey = max(greys.items(), key=lambda kv: kv[1])[0]
    # 偏差必须在同一个空间里量（线性光 vs 线性光）—— 与判据同一条规矩
    bg_lin = rel_luma((bg_grey, bg_grey, bg_grey))
    # ⚠ 与判据同一个筛：线性光偏差 > 0.01 才算"偏差像素"。少了这道筛读的是另一个量
    #   （整带都算 ⇒ 字芯被背景边稀释成 97，报 6.19:1 —— 那正是本轮撤掉的那把空刀的读数）。
    devs = sorted(((abs(rel_luma(p) - bg_lin), p) for p, _ in rows if abs(rel_luma(p) - bg_lin) > 0.01),
                  key=lambda t: -t[0])
    # 判据的字芯集合：偏差按降序取 min(len, max(40, len/20)) —— 1x 上小集合会塌到地板 40
    n = min(len(devs), max(40, len(devs) // 20))
    picked = [p for _, p in devs[:n]]
    core = tuple(int(sorted(p[i] for p in picked)[len(picked) // 2]) for i in range(3))
    ratio = contrast(core, (bg_grey, bg_grey, bg_grey))
    print('%-6s %-22s 尺寸=%dx%d 带底众数=%d 偏差像素=%d 字芯群=%d 字芯=%s 对比=%.2f:1'
          % (tag, '1x 代理(不签字)' if s < 1.5 else '2x 原帧', w, h, bg_grey, len(devs), n,
             str(core), ratio))
    return ratio


def main(argv):
    for tag, suffix in (('light', 'light'), ('dark', 'dark')):
        path = argv[1] % suffix
        full = Image.open(path).convert('RGB')
        half = full.resize((int(LOGICAL_W), int(LOGICAL_H)), Image.LANCZOS)
        read(full, tag)
        read(half, tag)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
