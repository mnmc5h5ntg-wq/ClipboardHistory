#!/usr/bin/env python3
"""R74 的真实视觉复核：浮层那三张帧（静置 / 悬停 / 打字）——**看**，不是读代码。

两张图：
  `hover-band-<mode>.png`   逐行带：静置 / 悬停 / 差值×8 三格竖排。
      差值那一格是本轮最该看的东西：判据说"灰只在这一行"，图上必须只有一条横带；
      要是差值里出现第二条带（或整片糊），那这条判据的读数就不是它声称的那件事。
  `three-up-<mode>.png`     三张帧的列表区并排（×2 放大），看打字那一档候选还剩几行。

**这张图不给「不加淡入」当证据**：那张决定靠的是重排读数 + 源码守卫，两条都不在图上。
图上能看的只有静置结果。把这一点写进图注是因为 R62 那一族记过「拿静置帧当过渡证据」。

用法：python3 .scratch/motion-audit-2/visual_r74_hover.py /tmp/r74_full2 /tmp/r74_visual
"""
import os
import sys

from PIL import Image, ImageChops, ImageOps

src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r74_full2"
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/r74_visual"
os.makedirs(out, exist_ok=True)

LIST = "quickpick-list-420x300"
HOVER = "quickpick-hover-420x300"
TYPED = "quickpick-typed-420x300"
TOP, BOTTOM = 96, 520


def load(name, mode):
    path = os.path.join(src, "%s-%s.png" % (name, mode))
    if not os.path.exists(path):
        return None
    return Image.open(path).convert("RGB")


for mode in ("light", "dark"):
    plain = load(LIST, mode)
    hover = load(HOVER, mode)
    typed = load(TYPED, mode)
    if plain is None or hover is None:
        print("MISSING 帧（%s）⇒ 这一档今天无从看" % mode)
        continue

    # 差值×8：把"哪一行被点亮"变成图上唯一亮的横带
    diff = ImageChops.difference(plain.crop((0, TOP, plain.width, BOTTOM)),
                                 hover.crop((0, TOP, hover.width, BOTTOM)))
    diff = ImageOps.autocontrast(diff, cutoff=0)
    gray = diff.convert("L")
    rows = []
    for y in range(gray.height):
        row = [gray.getpixel((x, y)) for x in range(0, gray.width, 4)]
        lit = sum(1 for p in row if p > 24)
        if lit:
            rows.append((y, lit))
    if rows:
        top_y, max_lit = max(rows, key=lambda r: r[1])
        band = [r[0] for r in rows if r[1] > max_lit * 0.35]
        print("%s 差值×8：亮像素最多的行带 y=%dpx（帧内 %dpx），连续带 %d…%dpx 高 %dpx"
              % (mode, top_y, top_y + TOP, min(band) + TOP, max(band) + TOP,
                 max(band) - min(band) + 1))
        # 落盘 PNG 这一侧独立量一遍**横向**：判据读的是内存里的 rep，
        # 而基线钉的是这张图（R37 那一族：尺读中间态、产物另一回事）。
        # 两边的数应当互相对得上 —— 对不上就是「判据看的不是交付的那张图」。
        xs = [x for x in range(gray.width)
              if any(gray.getpixel((x, y)) > 24 for y in band)]
        print("   灰带横向（落盘 PNG）：%d…%dpx ⇒ 内缩 左 %.1fpt 右 %.1fpt，宽 %dpx"
              % (min(xs), max(xs), min(xs) / 2.0, (hover.width - 1 - max(xs)) / 2.0,
                 max(xs) - min(xs) + 1))
        # 药丸那一族**不在这里重量**：暗档与亮档的"什么算药丸"是两个不同色号，
        # 没量过就写阈值 = 拿噪声当判据（那条规矩记在案）。判据自己已经在
        # 内存 rep 上量过两族，这里只核对**灰带**这一族跨通道一致。


    tiles = []
    for img, label in ((plain, "静置 list"), (hover, "悬停 hover"), (typed, "打字 typed")):
        if img is None:
            print("MISSING %s（%s）" % (label, mode))
            continue
        tiles.append(img.crop((0, TOP, img.width, BOTTOM)).resize(
            (img.width * 2, (BOTTOM - TOP) * 2), Image.LANCZOS))
    band_tiles = [plain.crop((0, TOP, plain.width, BOTTOM)),
                  hover.crop((0, TOP, hover.width, BOTTOM)),
                  diff]
    gap = 14
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + gap * 2, tiles[0].height),
                      (110, 110, 110))
    x = 0
    for tile in tiles:
        sheet.paste(tile, (x, 0))
        x += tile.width + gap
    three = os.path.join(out, "three-up-%s.png" % mode)
    sheet.save(three)
    print("WROTE %s  %dx%d" % (three, sheet.width, sheet.height))

    band_h = BOTTOM - TOP
    stack = Image.new("RGB", (max(t.width for t in band_tiles), band_h * 3 + gap * 2),
                      (110, 110, 110))
    y = 0
    for tile in band_tiles:
        stack.paste(tile, (0, y))
        y += tile.height + gap
    dest = os.path.join(out, "hover-band-%s.png" % mode)
    stack.save(dest)
    print("WROTE %s  %dx%d（自上而下：静置 / 悬停 / 差值×8）" % (dest, stack.width, stack.height))
