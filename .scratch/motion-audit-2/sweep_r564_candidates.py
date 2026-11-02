"""R564 取靶扫（候选生成器，**不是判据**）：三条轴一次扫全部帧。

轴 A「暗档里的近白大块」：暗档 UI 里成片近白（luma>=236）通常 = 写死的颜色没随外观切换。
轴 B「墨顶到右边缘」：最右 1 列有深墨 ⇒ 文字/图形被硬裁（无省略号、无边距）的签名。
轴 C「明暗同色大块」：同一位置在 light/dark 两档里逐通道相同、且那一块既不是白底也不是黑底
   ⇒ 候选的"写死颜色"（比轴 A 宽：任何中等灰度的不切换都算）。

只输出**排序后的可疑名单**；是不是缺陷要逐张看图 + 结构量现读，本脚本不作任何断言。
"""
import os
import sys

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r563-frames"
NEAR_WHITE = 236
MIN_AREA_PX = 900          # 2x 下约 15x60pt 的一块，小于此不当"成片"
EDGE_TOL = 1
INK_VS_WHITE = 60
TILE_ROWS = 12


def arr(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    return a, im.size


def tiles(mask, w, h):
    """把掩码按行切成 TILE_ROWS 带，返回每带内掩码的列区间与计数（粗略定位用）。"""
    out = []
    if not mask.any():
        return out
    ys, xs = np.nonzero(mask)
    band = max(1, h // TILE_ROWS)
    for b in range(0, h, band):
        sel = (ys >= b) & (ys < b + band)
        if not sel.any():
            continue
        cols = xs[sel]
        out.append((b, b + band - 1, int(cols.min()), int(cols.max()), int(sel.sum())))
    return out


def axis_a(darks):
    print("--- 轴 A：暗档近白块（面积降序；>= %d px 才列）---" % MIN_AREA_PX)
    rank = []
    for n in darks:
        a, (w, h) = arr(n)
        alpha = a[:, :, 3]
        luma = a[:, :, :3].mean(axis=2)
        mask = (alpha >= 8) & (luma >= NEAR_WHITE)
        area = int(mask.sum())
        if area >= MIN_AREA_PX:
            ys, xs = np.nonzero(mask)
            rank.append((area, n, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), w, h))
    for area, n, bbox, w, h in sorted(rank, reverse=True):
        a, _ = arr(n)
        luma = a[:, :, :3].mean(axis=2)
        mask = (a[:, :, 3] >= 8) & (luma >= NEAR_WHITE)
        print("A nearwhite=%d(%.2f%%) frame=%s size=%dx%d bbox=x%d..%d y%d..%d"
              % (area, 100.0 * area / (w * h), n, w, h, bbox[0], bbox[2], bbox[1], bbox[3]))
        for r0, r1, c0, c1, cnt in tiles(mask, w, h)[:6]:
            print("    带 y%d..%d 列 x%d..%d 墨=%d" % (r0, r1, c0, c1, cnt))
    if not rank:
        print("A 无（暗档帧里没有 >= %d px 的近白连通面积）" % MIN_AREA_PX)
    return rank


def axis_b(names):
    print("--- 轴 B：墨顶到右边缘（最右 %d 列有深墨的行数 > 0）---" % EDGE_TOL)
    hits = []
    for n in names:
        a, (w, h) = arr(n)
        strip = a[:, w - EDGE_TOL:w, :].astype(np.float64)
        alpha = strip[:, :, 3]
        luma = 0.299 * strip[:, :, 0] + 0.587 * strip[:, :, 1] + 0.114 * strip[:, :, 2]
        ink = (alpha >= 8) & (np.abs(luma - 255.0) >= INK_VS_WHITE)
        rows = np.nonzero(ink.any(axis=1))[0]
        if rows.size:
            hits.append((int(rows.size), n, int(rows.min()), int(rows.max())))
    for cnt, n, r0, r1 in sorted(hits, reverse=True):
        print("B edgeink_rows=%d frame=%s 行 y%d..%d" % (cnt, n, r0, r1))
    if not hits:
        print("B 无（没有任何一帧的墨落在最右 %d 列里 ⇒ 没有硬裁）" % EDGE_TOL)
    return hits


def axis_c(pairs):
    print("--- 轴 C：明暗同色中等灰大块（每对取面积 top1）---")
    rank = []
    for light, dark in pairs:
        la, (w, h) = arr(light)
        da, _ = arr(dark)
        same = (np.abs(la - da).max(axis=2) == 0)
        luma = da[:, :, :3].mean(axis=2)
        mid = (luma >= 90) & (luma <= 200)          # 既非白底也非黑底
        mask = same & mid & (da[:, :, 3] >= 8)
        area = int(mask.sum())
        if area >= MIN_AREA_PX:
            ys, xs = np.nonzero(mask)
            rank.append((area, light, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))))
    for area, n, bbox in sorted(rank, reverse=True)[:25]:
        print("C samecolor_mid=%d frame=%s bbox=x%d..%d y%d..%d" % (area, n, bbox[0], bbox[2], bbox[1], bbox[3]))
    print("C 计数=%d / 配对=%d" % (len(rank), len(pairs)))
    return rank


def main():
    names = sorted(n for n in os.listdir(SRC) if n.endswith(".png"))
    darks = [n for n in names if "-dark" in n]
    lights = [n for n in names if "-light" in n]
    base = {n[: -len("-dark.png")] for n in darks} & {n[: -len("-light.png")] for n in lights}
    pairs = [("%s-light.png" % b, "%s-dark.png" % b) for b in sorted(base)]
    print("SWEEP_FRAMES total=%d dark=%d light=%d pairs=%d dir=%s"
          % (len(names), len(darks), len(lights), len(pairs), SRC))
    axis_a(darks)
    axis_b(names)
    axis_c(pairs)


if __name__ == "__main__":
    main()
