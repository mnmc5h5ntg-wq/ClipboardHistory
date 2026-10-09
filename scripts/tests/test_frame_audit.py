"""`scripts/frame_audit.py` 的自测：解码器必须对已知输入给出已知答案。

这个工具是视觉审计的证据来源，所以它自己也要有守卫 —— 一个把 PNG 解错的工具
会产出"看着合理其实假的"数字（历史上踩过：单位后缀、自适应阈值恒真等同类）。
"""

import io
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from frame_audit import (  # noqa: E402
    PngError,
    luminance,
    main,
    read_png,
)


def write_png(path, width, height, rows, color_type=2):
    """按给定像素行写一个 8-bit 非隔行 PNG（filter 0）。"""
    channels = {0: 1, 2: 3, 6: 4}[color_type]
    raw = b""
    for row in rows:
        raw += b"\x00"
        for pixel in row:
            raw += bytes(pixel[:channels])

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", ihdr))
        handle.write(chunk(b"IDAT", zlib.compress(raw)))
        handle.write(chunk(b"IEND", b""))


class FrameAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="frame-audit-tests-")

    def tearDown(self):
        for name in os.listdir(self.directory):
            os.remove(os.path.join(self.directory, name))
        os.rmdir(self.directory)

    def path(self, name):
        return os.path.join(self.directory, name)

    def test_decodes_rgb_pixels_exactly(self):
        target = self.path("rgb.png")
        write_png(target, 2, 2, [
            [(255, 0, 0), (0, 255, 0)],
            [(0, 0, 255), (10, 20, 30)],
        ])
        width, height, channels, pixels = read_png(target)
        self.assertEqual((width, height, channels), (2, 2, 3))
        self.assertEqual(pixels[0:3], b"\xff\x00\x00")
        self.assertEqual(pixels[9:12], b"\x0a\x14\x1e")

    def test_decodes_rgba_and_grayscale(self):
        rgba = self.path("rgba.png")
        write_png(rgba, 1, 1, [[(1, 2, 3, 4)]], color_type=6)
        self.assertEqual(read_png(rgba)[2], 4)

        grey = self.path("grey.png")
        write_png(grey, 1, 1, [[(77,)]], color_type=0)
        width, height, channels, pixels = read_png(grey)
        self.assertEqual((width, height, channels, pixels), (1, 1, 1, b"M"))

    def test_unfilters_a_paeth_scanline(self):
        # 第二行用 paeth(filter 4) 编码，解码器必须还原成绝对值。
        path = self.path("paeth.png")
        channels = 3
        first = b"\x00" + bytes((100, 100, 100) * 2)
        second = b"\x04" + bytes((10, 10, 10) * 2)   # paeth 预测值 = 左邻 = 100 ⇒ 绝对值 110
        raw = first + second
        body = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)

        def chunk(kind, payload):
            return (struct.pack(">I", len(payload)) + kind + payload
                    + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

        with open(path, "wb") as handle:
            handle.write(b"\x89PNG\r\n\x1a\n")
            handle.write(chunk(b"IHDR", body))
            handle.write(chunk(b"IDAT", zlib.compress(raw)))
            handle.write(chunk(b"IEND", b""))
        self.assertEqual(channels, 3)
        _, _, _, pixels = read_png(path)
        self.assertEqual(pixels[6:9], b"\x6e\x6e\x6e")   # 110

    def test_rejects_non_png_and_interlaced(self):
        not_png = self.path("not_png.png")
        with open(not_png, "wb") as handle:
            handle.write(b"GIF89a......")
        with self.assertRaises(PngError):
            read_png(not_png)

        interlaced = self.path("interlaced.png")
        body = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 1)   # interlace = 1
        raw = b"\x00\xff\x00\x00"

        def chunk(kind, payload):
            return (struct.pack(">I", len(payload)) + kind + payload
                    + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

        with open(interlaced, "wb") as handle:
            handle.write(b"\x89PNG\r\n\x1a\n")
            handle.write(chunk(b"IHDR", body))
            handle.write(chunk(b"IDAT", zlib.compress(raw)))
            handle.write(chunk(b"IEND", b""))
        with self.assertRaises(PngError):
            read_png(interlaced)

    def test_luminance_follows_rec709(self):
        self.assertEqual(luminance((255, 255, 255)), 255)
        self.assertEqual(luminance((0, 0, 0)), 0)
        self.assertEqual(luminance((0, 255, 0)), int(0.7152 * 255))
        self.assertEqual(luminance((128,)), 128)

    def test_diff_reports_changed_pixels_and_exit_code(self):
        left = os.path.join(self.directory, "left")
        right = os.path.join(self.directory, "right")
        os.makedirs(left)
        os.makedirs(right)
        write_png(os.path.join(left, "same.png"), 2, 2, [
            [(200, 200, 200), (200, 200, 200)],
            [(200, 200, 200), (200, 200, 200)],
        ])
        write_png(os.path.join(right, "same.png"), 2, 2, [
            [(200, 200, 200), (200, 200, 200)],
            [(200, 200, 200), (200, 200, 200)],
        ])
        write_png(os.path.join(left, "changed.png"), 2, 2, [
            [(200, 200, 200), (200, 200, 200)],
            [(200, 200, 200), (200, 200, 200)],
        ])
        write_png(os.path.join(right, "changed.png"), 2, 2, [
            [(200, 200, 200), (157, 200, 200)],
            [(200, 200, 200), (200, 200, 200)],
        ])

        captured = io.StringIO()
        stdout = sys.stdout
        sys.stdout = captured
        try:
            code = main(["diff", left, right])
        finally:
            sys.stdout = stdout
        text = captured.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("changed.png", text)
        self.assertIn("最大通道差 43", text)
        self.assertIn("合计 1/2 帧有变化", text)
        self.assertNotIn("same.png", text)

        for directory in (left, right):
            for name in os.listdir(directory):
                os.remove(os.path.join(directory, name))
            os.rmdir(directory)

    def test_band_counts_distinct_colors_on_a_row(self):
        target = self.path("band.png")
        write_png(target, 3, 2, [
            [(10, 10, 10), (240, 240, 240), (240, 240, 240)],   # 第 0 行：分隔线可见 ⇒ 2 种颜色
            [(240, 240, 240), (240, 240, 240), (240, 240, 240)],  # 第 1 行：chrome 消失 ⇒ 1 种
        ])
        captured = io.StringIO()
        stdout = sys.stdout
        sys.stdout = captured
        try:
            main(["band", target, "--row", "0"])
            main(["band", target, "--row", "1"])
        finally:
            sys.stdout = stdout
        lines = captured.getvalue().strip().splitlines()
        self.assertIn("不同颜色=2", lines[0])
        self.assertIn("不同颜色=1", lines[1])


if __name__ == "__main__":
    unittest.main()
