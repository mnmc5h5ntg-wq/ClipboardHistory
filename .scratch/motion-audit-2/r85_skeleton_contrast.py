#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R85 的看图仪器：静帧骨架区域的条/背景亮度差，以及条带图的尺寸对账。

为什么单独成一个脚本而不是在终端里手量：台账里那两个数（暗 11/255、亮 13/255）
必须能追到一条可重放的命令（这一族的规矩）。跑法：

    python3 .scratch/motion-audit-2/r85_skeleton_contrast.py \
        /tmp/r85/shots /tmp/r85/motion

输出（stdout，同时写 `.scratch/motion-audit-2/r85_contrast_readings.log`）：
    SKELETON_CONTRAST_DARK=<Δ>/255（…） 背景=… 条峰值=… 峰值行 y=…px 偏离行=… 帧=…
    SKELETON_CONTRAST_LIGHT=<Δ>/255（…） …
    BAND_STRIP skeleton-band-strip.png 整图=… ⇒ 6 列 × 4 行 = 24 格，每格 …
（数字全部现算，脚本里不留任何"上次读到几"的常量。）
"""
import os
import struct
import statistics
import sys
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r85_contrast_readings.log')
# 详情区骨架那一块（源帧 1440×1040 = 720×520pt @2×）：
# 条在 y 40…83pt ⇒ 80…166px；x 从详情区左轴 20pt=40px 起，最长那条到 604pt=1208px。
# 取 x 60…1100px 是为了**避开左边缘与右边缘**（那里有别的视图），y 70…190px 覆盖三根条与它们的间距。
X0, X1, Y0, Y1 = 60, 1100, 70, 190


def decode(path):
    """纯标准库解 PNG（只支持本机帧用的 8bit RGB/RGBA + 五种过滤）。"""
    data = open(path, 'rb').read()
    pos, idat, w, h, col = 8, b'', None, None, None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, _bit, col = struct.unpack('>IIBB', payload[:10])
        elif typ == b'IDAT':
            idat += payload
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[col]
    stride = w * ch
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
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
    return w, h, ch, rows, col


def contrast(path):
    w, h, ch, rows, col = decode(path)
    lums = {}
    for y in range(Y0, min(Y1, h)):
        row = rows[y]
        vals = []
        for x in range(X0, min(X1, w), ch):
            r, g, b = row[x], row[x + 1], row[x + 2]
            vals.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        lums[y] = statistics.median(vals)
    bg = statistics.median(sorted(lums.values()))
    # 条所在的行 = 与区域中位差 1 级以上的那些；峰值取偏离最大的那一行
    off = [(y, m) for y, m in sorted(lums.items()) if abs(m - bg) > 1.0]
    if not off:
        return None
    peak = max(off, key=lambda t: abs(t[1] - bg))
    return dict(bg=bg, peak=peak[1], delta=abs(peak[1] - bg), y=peak[0],
                rows=len(off), size=(w, h))


def png_size(path):
    d = open(path, 'rb').read()
    return struct.unpack('>II', d[16:24])


def main():
    shots, motion = sys.argv[1], sys.argv[2]
    lines = []
    for tag, name in (('DARK', 'detail-loading-720x520-dark.png'),
                      ('LIGHT', 'detail-loading-720x520-light.png')):
        p = os.path.join(shots, name)
        if not os.path.exists(p):
            lines.append('SKELETON_CONTRAST_%s=not-run（%s 不在，先跑捕获那一卷）' % (tag, p))
            continue
        c = contrast(p)
        if c is None:
            lines.append('SKELETON_CONTRAST_%s=not-found（区域里找不到偏离背景 1 级以上的行）' % tag)
            continue
        lines.append('SKELETON_CONTRAST_%s=%.1f/255（%.1f%%） 背景=%.1f 条峰值=%.1f '
                     '峰值行 y=%dpx=%.0fpt 偏离行=%d 帧=%dx%d'
                     % (tag, c['delta'], 100.0 * c['delta'] / 255.0, c['bg'], c['peak'],
                        c['y'], c['y'] / 2.0, c['rows'], c['size'][0], c['size'][1]))
    strip = os.path.join(motion, 'skeleton-band-strip.png')
    if os.path.exists(strip):
        w, h = png_size(strip)
        # 判据打的那一行说"前 24 帧排成条带（六列）"⇒ 6 列 × 4 行；每格尺寸由整图反推，
        # 不许照抄"源帧尺寸"（第一版我在这里写了 840×440px/格，而 2520/6 明明是 420 —— 抄来的数会自己骗人）。
        cols, rows_n = 6, 4
        lines.append('BAND_STRIP %s 整图=%dx%dpx ⇒ %d 列 × %d 行 = %d 格，每格 %dx%dpx'
                     '（条带把源帧缩过；本轮没有单独落盘源帧，所以不写源帧尺寸）'
                     % (os.path.basename(strip), w, h, cols, rows_n, cols * rows_n,
                        w // cols, h // rows_n))
    else:
        lines.append('BAND_STRIP=not-run（%s 不在）' % strip)
    text = '\n'.join(lines) + '\n'
    sys.stdout.write(text)
    open(OUT, 'w').write(text)


if __name__ == '__main__':
    main()
