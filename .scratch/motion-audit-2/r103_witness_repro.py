# -*- coding: utf-8 -*-
"""R103：能不能在**本机**复现 runner 那朵「暗档 墨行=0 / 卡片段=0」？

runner 是非 Retina（scale=1），本机是 2x。这里把本机帧按 2x2 抽成 1x（最近邻），
再用**旧证人**（逐行 kind：先看 cardRun 是不是卡片里，再看 |luma-fill|>=60 的像素数 >=8）
和**新证人**（存在性：min(|l-fill|,|l-page|)>60 的像素数 >=6）各读一遍。

能复现 ⇒ 修完能在本机证明；不能复现 ⇒ 只能靠 CI，要分开记账。
"""
from collections import Counter
from PIL import Image

SHOTS = "/tmp/r102_shots"
BANDS = {
    "cardprobe-groupbox-default": (24.0, 24.0, 672.0, 100.0),
    "cardprobe-scroll-groupbox": (24.0, 24.0, 672.0, 100.0),
    "cardprobe-split-groupbox": (150.0, 24.0, 570.0, 100.0),
}
WINDOW_W = 720.0
PAGE_STRIP = (150.0, 4.0, 560.0, 8.0)


def load(path, decimate):
    im = Image.open(path).convert("RGB")
    if decimate:
        w, h = im.size
        im = im.crop((0, 0, w, h)).resize((w // 2, h // 2), Image.NEAREST)
    px = im.load()
    w, h = im.size
    rows = []
    for y in range(h):
        rows.append([int(round(0.2126 * px[x, y][0] + 0.7152 * px[x, y][1] + 0.0722 * px[x, y][2]))
                     for x in range(w)])
    return rows, w / WINDOW_W


def modal(row):
    if not row:
        return 0
    return Counter(v // 8 for v in row).most_common(1)[0][0] * 8 + 4


def region(rows, rect, scale):
    x, y, ww, hh = rect
    y0, y1 = int(y * scale), int((y + hh) * scale)
    x0, x1 = int(x * scale), int((x + ww) * scale)
    return [r[x0:x1] for r in rows[max(0, y0):min(len(rows), y1)]]


def card_fill(modals, page, scale):
    counts = Counter(m for m in modals if abs(m - page) > 3)
    if not counts:
        return -1
    top, n = sorted(counts.items(), key=lambda kv: (-kv[1], abs(kv[0] - page)))[0]
    return top if n / max(scale, 1e-9) >= 20 else -1


def old_kinds(band_rows, fill, page, scale):
    """复刻 cardRowKinds + cardRowKind 的三个量。"""
    kinds = []
    if fill < 0:
        return ["outside"] * len(band_rows), -1
    for row in band_rows:
        ink = sum(1 for v in row if abs(v - fill) >= 60)
        line = sum(1 for v in row if 6 <= abs(v - fill) < 48)
        run = best = 0
        for v in row:
            if abs(v - fill) < abs(v - page):
                run += 1
                best = max(best, run)
            else:
                run = 0
        width = len(row)
        if best * 10 < width * 3:
            k = "outside"
        elif ink >= 8:
            k = "ink"
        elif line * 10 >= width * 8:
            k = "line"
        else:
            k = "card"
        kinds.append(k)
    segs = 0
    start = -1
    for i, k in enumerate(kinds + ["outside"]):
        if k != "outside":
            if start < 0:
                start = i
        else:
            if start >= 0 and (i - start) / max(scale, 1e-9) >= 20:
                segs += 1
            start = -1
    return kinds, segs


def new_witness(band_rows, fill, page, gate=60, min_pixels=6):
    n_rows = 0
    max_delta = 0
    for row in band_rows:
        c = 0
        for v in row:
            d = min(abs(v - fill), abs(v - page)) if fill >= 0 else abs(v - page)
            max_delta = max(max_delta, d)
            if d > gate:
                c += 1
        if c >= min_pixels:
            n_rows += 1
    return n_rows, max_delta


for decimate in (False, True):
    print("=== %s" % ("模拟 runner：1x（2x2 抽 1）" if decimate else "本机：2x 原帧"))
    for name, band in BANDS.items():
        for tag in ("light", "dark"):
            rows, scale = load("%s/%s-720x140-%s.png" % (SHOTS, name, tag), decimate)
            page = modal([v for r in region(rows, PAGE_STRIP, scale) for v in r])
            band_rows = region(rows, band, scale)
            fill = card_fill([modal(r) for r in band_rows], page, scale)
            kinds, segs = old_kinds(band_rows, fill, page, scale)
            old_ink = kinds.count("ink")
            n_rows, max_delta = new_witness(band_rows, fill, page)
            strip_rows, _ = new_witness(region(rows, PAGE_STRIP, scale), fill, page)
            print("%-28s %s scale=%.1f page=%3d fill=%3d 旧:墨行=%2d 段=%d | 新:墨行=%2d "
                  "最大偏离=%3d | 新:页面条=%d" % (name, tag, scale, page, fill, old_ink, segs,
                                                   n_rows, max_delta, strip_rows))
