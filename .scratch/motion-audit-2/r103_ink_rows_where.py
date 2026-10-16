# -*- coding: utf-8 -*-
from collections import Counter
from PIL import Image
SHOTS = "/tmp/r102_shots"
for name in ("cardprobe-groupbox-default", "cardprobe-scroll-groupbox", "cardprobe-split-groupbox"):
    for tag in ("light", "dark"):
        im = Image.open("%s/%s-720x140-%s.png" % (SHOTS, name, tag)).convert("RGB")
        px = im.load(); w, h = im.size; scale = w / 720.0
        page = 252 if tag == "light" else 28
        fill = 244 if tag == "light" else 36
        x0, x1 = (int(24 * scale), int(696 * scale)) if name != "cardprobe-split-groupbox" else (int(150 * scale), int(720 * scale))
        hits = []
        for y in range(h):
            c = sum(1 for x in range(x0, x1)
                    if min(abs(int(round(0.2126*px[x,y][0]+0.7152*px[x,y][1]+0.0722*px[x,y][2])) - fill),
                           abs(int(round(0.2126*px[x,y][0]+0.7152*px[x,y][1]+0.0722*px[x,y][2])) - page)) > 60)
            if c >= 6:
                hits.append(round(y / scale, 1))
        print("%-26s %s 有墨行的 pt 位置: %s .. %s  共 %d 行" % (name, tag,
              hits[0] if hits else "无", hits[-1] if hits else "", len(hits)))
