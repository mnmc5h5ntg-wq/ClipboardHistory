#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一张 PNG 的某个矩形**放大**成另一张 PNG，用来"真的看一眼"。

为什么要有它：R88 收尾时用眼睛看 720×540 的整帧，侧栏那一列到底是"淡但可读"还是
"跟背景一样"，在缩略图上是分不出来的；而像素读数（峰=28 / 背景=28）说的是另一回事。
两边对不上时，要么我眼睛错，要么我的坐标窗口错 —— 只有一个办法能同时判：
把那块区域裁出来放大再看一次。

不引第三方库（仓库里所有看图仪器都是纯 stdlib，见 r86_heatmap_legend.py 的 decode）。
用法：python3 .scratch/motion-audit-2/r88_crop.py <png> <x0> <y0> <x1> <y1> <scale> <out.png>
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode


def encode_rgb(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(row) for row in rows)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as handle:
        handle.write(png)


def main():
    src, x0, y0, x1, y1, scale, out = (sys.argv[1], int(sys.argv[2]), int(sys.argv[3]),
                                       int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]),
                                       sys.argv[7])
    w, h, ch, rows = decode(src)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    cw, cyh = x1 - x0, y1 - y0
    ow, oh = cw * scale, cyh * scale
    canvas = []
    for oy in range(oh):
        sy = y0 + oy // scale
        line = bytearray()
        for ox in range(ow):
            sx = x0 + ox // scale
            p = rows[sy]
            o = sx * ch
            line += bytes(p[o:o + 3])
        canvas.append(line)
    encode_rgb(out, ow, oh, canvas)
    # 同时把每行的"最亮像素"打出来，眼睛和数字一起对
    print('裁出 %s ← %s  区域(%d,%d)-(%d,%d) 放大 %dx ⇒ %dx%d'
          % (os.path.basename(out), os.path.basename(src), x0, y0, x1, y1, scale, ow, oh))
    for label, (bx0, bx1) in ((u'图标列', (30, 72)), (u'文字列', (78, 300))):
        peaks = []
        for band in range(6):
            yc = 154 + band * 63
            best = 0
            for y in range(max(0, yc - 26), min(h, yc + 26)):
                for x in range(bx0, min(w, bx1)):
                    p = rows[y]
                    m = max(p[x * ch], p[x * ch + 1], p[x * ch + 2])
                    if m > best:
                        best = m
            peaks.append(best)
        print('  %s 六行峰值: %s' % (label, ' '.join(str(v) for v in peaks)))


if __name__ == '__main__':
    main()
