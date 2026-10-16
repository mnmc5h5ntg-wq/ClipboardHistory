# -*- coding: utf-8 -*-
"""地板那一格必须精确：把六臂里**非零行的最小墨像素数**与 1..10 这几档的行数打出来。

`r103_witness_floor.log` 打的是直方图前 6 档，低频的小计数可能被截掉 ⇒ 那句话没有凭据。
这一份把「最小的非零值」直接数出来，真值表与文档串里引用的就是它。
"""
from PIL import Image

SHOTS = "/tmp/r102_shots"
BANDS = {
    "cardprobe-groupbox-default": (24.0, 672.0),
    "cardprobe-scroll-groupbox": (24.0, 672.0),
    "cardprobe-split-groupbox": (150.0, 570.0),
}
for name, (bx, bw) in sorted(BANDS.items()):
    for tag in ("light", "dark"):
        for dec in (False, True):
            im = Image.open("%s/%s-720x140-%s.png" % (SHOTS, name, tag)).convert("RGB")
            if dec:
                w, h = im.size
                im = im.resize((w // 2, h // 2), Image.NEAREST)
            px = im.load()
            w, h = im.size
            scale = w / 720.0
            page = 252 if tag == "light" else 28
            fill = 244 if tag == "light" else 36
            x0, x1 = int(bx * scale), int((bx + bw) * scale)
            y0, y1 = int(24 * scale), int(124 * scale)
            low = []
            for y in range(y0, y1):
                c = 0
                for x in range(x0, x1):
                    v = int(round(0.2126 * px[x, y][0] + 0.7152 * px[x, y][1]
                                  + 0.0722 * px[x, y][2]))
                    if min(abs(v - fill), abs(v - page)) > 60:
                        c += 1
                if 0 < c < 20:
                    low.append(c)
            nz = sorted(low)
            print("%-26s %s %s 非零且<20 的行: %s | 其中 <6 的行数=%d | 全部非零行的最小值=%s"
                  % (name, tag, "1x" if dec else "2x", nz[:14],
                     sum(1 for v in nz if v < 6), nz[0] if nz else "无(>=20)"))
