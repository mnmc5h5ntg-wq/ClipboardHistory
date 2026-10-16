# -*- coding: utf-8 -*-
"""R103：把「一行里有几个墨像素」这条分布打出来，给新证人的 minPixels 定地板（不许猜）。"""
from collections import Counter
from PIL import Image

SHOTS = "/tmp/r102_shots"
PAGE_STRIP = (150.0, 4.0, 560.0, 8.0)


def load(path, decimate):
    im = Image.open(path).convert("RGB")
    if decimate:
        w, h = im.size
        im = im.resize((w // 2, h // 2), Image.NEAREST)
    px = im.load()
    w, h = im.size
    return [[int(round(0.2126 * px[x, y][0] + 0.7152 * px[x, y][1] + 0.0722 * px[x, y][2]))
             for x in range(w)] for y in range(h)], w / 720.0


def region(rows, rect, scale):
    x, y, ww, hh = rect
    return [r[int(x * scale):int((x + ww) * scale)]
            for r in rows[int(y * scale):int((y + hh) * scale)]]


def modal(row):
    return Counter(v // 8 for v in row).most_common(1)[0][0] * 8 + 4


for name in ("cardprobe-groupbox-default", "cardprobe-split-groupbox"):
    for tag in ("light", "dark"):
        for dec in (False, True):
            rows, scale = load("%s/%s-720x140-%s.png" % (SHOTS, name, tag), dec)
            page = modal([v for r in region(rows, PAGE_STRIP, scale) for v in r])
            band = region(rows, (150.0 if "split" in name else 24.0, 24.0, 400.0, 100.0), scale)
            fill = 36 if tag == "dark" else 244
            counts = []
            for r in band:
                counts.append(sum(1 for v in r
                                  if min(abs(v - fill), abs(v - page)) > 60))
            strip = region(rows, PAGE_STRIP, scale)
            scounts = [sum(1 for v in r if min(abs(v - fill), abs(v - page)) > 60) for r in strip]
            hist = Counter(counts)
            top = sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
            print("%-26s %s %s page=%3d fill=%3d 带内每行墨像素分布(行数:个数)=%s 带内最大=%d 页面条最大=%d"
                  % (name, tag, "1x" if dec else "2x", page, fill, top, max(counts), max(scounts)))
