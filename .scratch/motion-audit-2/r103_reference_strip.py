# -*- coding: utf-8 -*-
"""R103：反方向那条参考带该取哪一段？把候选带子的「有几行被读成字」逐张打出来。

要的性质：① 真页底 ⇒ 必须处处 0（本机六臂）；② 把它挪进卡片 ⇒ 必须能变非 0（否则这一格没有牙）。
"""
from collections import Counter
from PIL import Image

SHOTS = "/tmp/r102_shots"
BANDS = {
    "cardprobe-groupbox-default": (24.0, 672.0),
    "cardprobe-scroll-groupbox": (24.0, 672.0),
    "cardprobe-split-groupbox": (150.0, 570.0),
}


def load(path):
    im = Image.open(path).convert("RGB")
    px = im.load()
    w, h = im.size
    scale = w / 720.0
    return [[int(round(0.2126 * px[x, y][0] + 0.7152 * px[x, y][1] + 0.0722 * px[x, y][2]))
             for x in range(w)] for y in range(h)], scale


def strip(rows, scale, x, y, ww, hh, fill, page):
    y0, y1 = int(y * scale), int((y + hh) * scale)
    x0, x1 = int(x * scale), int((x + ww) * scale)
    n = 0
    mx = 0
    for r in rows[y0:y1]:
        seg = r[x0:x1]
        c = 0
        for v in seg:
            d = min(abs(v - fill), abs(v - page))
            mx = max(mx, d)
            if d > 60:
                c += 1
        if c >= 6:
            n += 1
    return n, mx


for name, (bx, bw) in BANDS.items():
    for tag in ("light", "dark"):
        rows, scale = load("%s/%s-720x140-%s.png" % (SHOTS, name, tag))
        page = 252 if tag == "light" else 28
        fill = 244 if tag == "light" else 36
        a = strip(rows, scale, bx, 4, bw, 8, fill, page)          # 候选：跟着带子的 x
        b = strip(rows, scale, 150, 4, 560, 8, fill, page)        # 现状：写死 x150..710
        c = strip(rows, scale, bx, 30, bw, 8, fill, page)         # 变异对偶：挪进卡片
        d = strip(rows, scale, bx, 60, bw, 8, fill, page)         # 带子中部（卡片以下）
        print("%-26s %s  A带子x@y4..12=%d(max%3d)  B现状=%d(max%3d)  C挪进卡片y30..38=%d(max%3d)  D卡片下y60=%d(max%3d)"
              % (name, tag, a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]))
