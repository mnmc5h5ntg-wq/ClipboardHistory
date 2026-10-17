#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R143：给 BACKLOG 178 一个数 —— 快捷键录制器那颗 bezel，到底和卡片底色差多少。

为什么现在才量：R141 那句"暗档里它的 bezel 与卡片底色几乎同色"是**看图看出来的怀疑**，
而同一轮我自己写下"形容词不是读数"。这条脚本把那句话变成两档各一个数。

坐标不目测：先在这一列上扫出**横向分隔线**（卡片底色的连续长段），再按录制器自己的行带取中心；
录制器行带来自台账 R141 的读数（y≈265 / 380 / 522，x≈960–1200，都是 2x 帧像素）。
判"有没有一块填充"用**最长同色段**而不是行众数（R110 那一族：近背景层会劫持众数）。

用法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r143_recorder_bezel.py /tmp/shots_r143
只打长度 / 色号 / 坐标，绝不打用户内容。
"""
import os
import sys

from PIL import Image


def longest_run(row):
    """返回 (色号, 起始 x, 结束 x, 长度) —— 一行里最长的那段同色像素。"""
    best = None
    start = 0
    for i in range(1, len(row) + 1):
        if i == len(row) or row[i] != row[start]:
            length = i - start
            if best is None or length > best[3]:
                best = (row[start], start, i - 1, length)
            start = i
    return best


def rgb_at(px, x, y):
    value = px[x, y]
    return tuple(value[:3]) if isinstance(value, (tuple, list)) else (value, value, value)


def luma(color):
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]


def contrast(a, b):
    la, lb = luma(a), luma(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 5.0) / (lo + 5.0)


def scanline(px, y, x0, x1):
    return [rgb_at(px, x, y) for x in range(x0, x1 + 1)]


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print("RECORDER_BEZEL_NOT_RUN 需要一个帧目录参数（本轮用 /tmp/shots_r143）")
        return 1
    shots = sys.argv[1]
    rows = [265, 380, 522]
    x0, x1 = 950, 1210
    for appearance in ("light", "dark"):
        path = os.path.join(shots, "settings-shortcuts-720x540-%s.png" % appearance)
        if not os.path.exists(path):
            print("RECORDER_BEZEL_NOT_RUN 帧读不到：%s" % path)
            continue
        image = Image.open(path).convert("RGBA")
        px = image.load()
        # 卡片底色：同一行带上、录制器**外面**两小段的长段众数（x 700..940 与 x 1220..1400）
        card = longest_run(scanline(px, rows[1], 700, 940))
        print("  %s 卡片底 色号=%s 亮度=%.1f（x %d..%d 长 %d 的最长同色段）"
              % (appearance, card[0], luma(card[0]), 700 + card[1], 700 + card[2], card[3]))
        for y in rows:
            inside = longest_run(scanline(px, y, x0 + 30, x1 - 30))
            fill = (inside[0][0], inside[0][1], inside[0][2])
            left_edge = x0 + inside[1]
            # bezel：填充段左沿往外 6px 里，与卡片底差最大的那一格
            band = [rgb_at(px, x, y) for x in range(max(0, left_edge - 6), left_edge + 1)]
            bezel = max(band, key=lambda c: abs(luma(c) - luma(card[0])))
            print("    y=%d 填充=%s 长=%d 填充↔卡片 Δ亮度=%.1f 对比=%.2f:1 ｜ bezel=%s Δ亮度=%.1f 对比=%.2f:1"
                  % (y, fill, inside[3], abs(luma(fill) - luma(card[0])), contrast(fill, card[0]),
                     bezel, abs(luma(bezel) - luma(card[0])), contrast(bezel, card[0])))
        # 参照：同一帧里那颗「恢复默认」按钮（右下角，按文字列右侧推）
        print("  %s 参照 恢复默认那一行取 y=980 的长段：%s" % (
            appearance, longest_run(scanline(px, 980, 950, 1210))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
