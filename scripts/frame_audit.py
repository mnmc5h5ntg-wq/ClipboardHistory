#!/usr/bin/env python3
"""帧级取证工具：把"界面看起来对不对"变成可复算的数字。

只依赖标准库（zlib/struct），Python 3.9 可跑。用途：
  1. `diff A B`     逐帧比较两个目录里同名 PNG，给出变化像素占比与最大通道差；
  2. `stats FILE`   单帧统计：尺寸、不同颜色数、平均亮度、最亮/最暗像素；
  3. `band FILE`    统计某一横行/竖列上的不同颜色数 —— 用来判断"分隔线/描边到底画出来了没有"
                   （亮色下 `.white.opacity(0.18)` 这类 chrome 消失时，这一带的颜色数会掉到 1）。

设计取舍：故意**不做**"看起来像不像设计稿"的判断，只给可复算的量；
判读留给调用者，但每条输出都带命令，便于写进账本。
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import zlib


class PngError(Exception):
    pass


def read_png(path):
    """解码 8-bit 非隔行 PNG，返回 (width, height, channels, bytes)。

    channels: 3 = RGB, 4 = RGBA, 1 = 灰度。其它组合直接报错而不是静默给错数。
    """
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PngError("%s 不是 PNG" % path)

    pos = 8
    width = height = None
    bit_depth = color_type = None
    interlace = 0
    idat = []
    palette = None
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if width is None:
        raise PngError("%s 缺少 IHDR" % path)
    if bit_depth != 8:
        raise PngError("%s 位深 %s，本工具只解 8-bit" % (path, bit_depth))
    if interlace:
        raise PngError("%s 是隔行 PNG，本工具不解" % path)

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise PngError("%s color type %s 不支持" % (path, color_type))

    raw = zlib.decompress(b"".join(idat))
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    offset = 0
    for y in range(height):
        filter_type = raw[offset]
        offset += 1
        line = bytearray(raw[offset:offset + stride])
        offset += stride
        if filter_type == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = prev[i]
                upleft = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(left, up, upleft)) & 0xFF
        elif filter_type != 0:
            raise PngError("%s 第 %d 行 filter 类型 %d 非法" % (path, y, filter_type))
        out[y * stride:(y + 1) * stride] = line
        prev = line

    if color_type == 3:
        if palette is None:
            raise PngError("%s 是索引色但没有 PLTE" % path)
        expanded = bytearray(width * height * 3)
        for i in range(width * height):
            index = out[i] * 3
            expanded[i * 3:i * 3 + 3] = palette[index:index + 3]
        return width, height, 3, bytes(expanded)
    if color_type == 4:
        expanded = bytearray(width * height * 2)
        expanded[:] = out
        return width, height, 2, bytes(expanded)
    return width, height, channels, bytes(out)


def _paeth(left, up, upleft):
    initial = left + up - upleft
    distance_left = abs(initial - left)
    distance_up = abs(initial - up)
    distance_upleft = abs(initial - upleft)
    if distance_left <= distance_up and distance_left <= distance_upleft:
        return left
    if distance_up <= distance_upleft:
        return up
    return upleft


def pixel_rows(width, height, channels, pixels):
    """按行产出像素元组，避免调用方自己算 stride 算错。"""
    stride = width * channels
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        for x in range(width):
            base = x * channels
            yield y, tuple(row[base:base + channels])


def luminance(pixel):
    """Rec.709 相对亮度（0-255 整数），只取颜色通道，忽略 alpha。

    用四舍五入而不是截断：0.2126+0.7152+0.0722 = 1.0，但三个乘积的浮点和是
    254.999…，截断会把纯白算成 254（自测就是这么抓到的）。
    """
    if len(pixel) >= 3:
        return int(round(0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]))
    return pixel[0]


def command_stats(path):
    width, height, channels, pixels = read_png(path)
    colors = {}
    for _, pixel in pixel_rows(width, height, channels, pixels):
        colors[pixel] = colors.get(pixel, 0) + 1
    lums = [luminance(p) for p in colors for _ in range(colors[p])]
    print("%s: %dx%d channels=%d 不同颜色=%d 平均亮度=%.1f 最暗=%d 最亮=%d"
          % (os.path.basename(path), width, height, channels, len(colors),
             sum(lums) / float(len(lums)), min(lums), max(lums)))
    return 0


def command_band(path, row=None, column=None):
    width, height, channels, pixels = read_png(path)
    if row is None and column is None:
        raise PngError("band 需要 --row 或 --column")
    seen = {}
    if row is not None:
        if not 0 <= row < height:
            raise PngError("--row %d 超出高度 %d" % (row, height))
        for y, pixel in pixel_rows(width, height, channels, pixels):
            if y == row:
                seen[pixel] = seen.get(pixel, 0) + 1
        scope = "row=%d/%d" % (row, width)
    else:
        if not 0 <= column < width:
            raise PngError("--column %d 超出宽度 %d" % (column, width))
        stride = width * channels
        for y in range(height):
            base = y * stride + column * channels
            pixel = tuple(pixels[base:base + channels])
            seen[pixel] = seen.get(pixel, 0) + 1
        scope = "column=%d/%d" % (column, height)
    print("%s %s 不同颜色=%d %s"
          % (os.path.basename(path), scope, len(seen),
             " ".join("%s×%d" % (str(k), v) for k, v in sorted(seen.items(), key=lambda kv: -kv[1])[:4])))
    return 0


def command_diff(directory_a, directory_b):
    names_a = set(n for n in os.listdir(directory_a) if n.endswith(".png"))
    names_b = set(n for n in os.listdir(directory_b) if n.endswith(".png"))
    only_a = sorted(names_a - names_b)
    only_b = sorted(names_b - names_a)
    if only_a:
        print("只在 A 有：%s" % ", ".join(only_a))
    if only_b:
        print("只在 B 有：%s" % ", ".join(only_b))
    changed = 0
    for name in sorted(names_a & names_b):
        path_a = os.path.join(directory_a, name)
        path_b = os.path.join(directory_b, name)
        wa, ha, ca, pa = read_png(path_a)
        wb, hb, cb, pb = read_png(path_b)
        if (wa, ha) != (wb, hb):
            print("%-44s 尺寸不同 %dx%d vs %dx%d" % (name, wa, ha, wb, hb))
            changed += 1
            continue
        channels = min(ca, cb)
        total = wa * ha
        differing = 0
        max_delta = 0
        for i in range(total):
            base_a = i * ca
            base_b = i * cb
            delta = 0
            for c in range(channels):
                delta = max(delta, abs(pa[base_a + c] - pb[base_b + c]))
            if delta:
                differing += 1
                if delta > max_delta:
                    max_delta = delta
        if differing:
            changed += 1
            print("%-44s 变化像素 %6.2f%% (%d/%d) 最大通道差 %d"
                  % (name, 100.0 * differing / total, differing, total, max_delta))
    print("合计 %d/%d 帧有变化" % (changed, len(names_a & names_b)))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    diff = sub.add_parser("diff", help="逐帧比较两个目录")
    diff.add_argument("directory_a")
    diff.add_argument("directory_b")

    stats = sub.add_parser("stats", help="单帧统计")
    stats.add_argument("path")

    band = sub.add_parser("band", help="某一行/一列的颜色数（判断分隔线是否画出来）")
    band.add_argument("path")
    band.add_argument("--row", type=int)
    band.add_argument("--column", type=int)

    args = parser.parse_args(argv)
    if args.command == "diff":
        return command_diff(args.directory_a, args.directory_b)
    if args.command == "stats":
        return command_stats(args.path)
    return command_band(args.path, row=args.row, column=args.column)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PngError as error:
        print("错误：%s" % error, file=sys.stderr)
        sys.exit(2)
