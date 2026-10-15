#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R86 的看图仪器（热图）：图例那四个色块与网格档位色、以及"没有记录"那一格的颜色对不对得上。

为什么单独成脚本：台账里那句"图例的『少』指的是最低一档**非零**，而灰格不在图例里"
必须能重放。跑法：

    python3 .scratch/motion-audit-2/r86_heatmap_legend.py /tmp/r86/shots

输出同时写 `.scratch/motion-audit-2/r86_heatmap_readings.log`。
"""
import os
import struct
import sys
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r86_heatmap_readings.log')


def decode(path):
    d = open(path, 'rb').read()
    pos, idat, w, h, col = 8, b'', None, None, None
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos + 4])[0]
        typ = d[pos + 4:pos + 8]
        pay = d[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, _b, col = struct.unpack('>IIBB', pay[:10])
        elif typ == b'IDAT':
            idat += pay
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[col]
    stride = w * ch
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if ft == 1:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + a) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b, c = prev[i], (prev[i - ch] if i >= ch else 0)
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, ch, rows


# 采样点：这些坐标是**手工对过帧之后钉下来的**（不是自动搜出来的 —— 自动搜的第一版
# 把网格最后一行搜成了"图例"，因为它只数蓝块个数）。每个点都带一条断言：
# 取到的色必须与它声称的那个角色一致，否则报 not-found 而不是安静地写一个错数。
LEGEND_Y = 400
LEGEND_X = (78, 110, 142, 174)          # 图例那四个色块的中心
EMPTY_CELL = (85, 366)                  # 网格里"没有记录"那一格的中部
FRAMES = (('heatmap-populated-430x250-dark.png', 'dark', (30, 30, 30)),
          ('heatmap-populated-430x250-light.png', 'light', (255, 255, 255)))


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r86/shots'
    lines = []
    for name, tag, bg in FRAMES:
        path = os.path.join(shots, name)
        if not os.path.exists(path):
            lines.append('HEATMAP_%s=not-run（%s 不在，先跑捕获那一卷）' % (tag, path))
            continue
        w, h, ch, rows = decode(path)
        px = lambda x, y: (rows[y][x * ch], rows[y][x * ch + 1], rows[y][x * ch + 2])
        legend = [px(x, LEGEND_Y) for x in LEGEND_X]
        empty = px(*EMPTY_CELL)
        # 断言一：图例四块必须是**单调变蓝**的四个不同色（同色或反向 ⇒ 采样点漂了）
        if len(set(legend)) != 4 or any(c[2] <= c[0] + 25 for c in legend):
            lines.append('HEATMAP_LEGEND_%s=not-found（采到 %s ⇒ 坐标漂了，别改台账，改这里）'
                         % (tag, legend))
            continue
        lines.append('HEATMAP_LEGEND_%s y=%d 四档=%s（从左到右：少→多）'
                     % (tag, LEGEND_Y, ' '.join('%d,%d,%d' % c for c in legend)))
        # 断言二：空格子取色必须是中性灰，且不等于背景
        if abs(empty[0] - empty[1]) > 5 or abs(empty[1] - empty[2]) > 5 or empty == bg:
            lines.append('HEATMAP_EMPTY_%s=not-found（采到 %s）' % (tag, empty))
            continue
        lines.append('HEATMAP_EMPTY_%s 没有记录那一格=%s 背景=%s ⇒ 与背景的差=%d'
                     % (tag, '%d,%d,%d' % empty, '%d,%d,%d' % bg,
                        max(abs(empty[0] - bg[0]), abs(empty[1] - bg[1]), abs(empty[2] - bg[2]))))
        lines.append('HEATMAP_EMPTY_IN_LEGEND_%s=%s（图例四档里没有这一色 ⇒ "少"指的是最低一档**非零**）'
                     % (tag, 'yes' if empty in legend else 'no'))
    text = '\n'.join(lines) + '\n'
    sys.stdout.write(text)
    open(OUT, 'w').write(text)


if __name__ == '__main__':
    main()
