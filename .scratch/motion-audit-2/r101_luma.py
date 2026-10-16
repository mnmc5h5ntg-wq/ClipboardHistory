#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 §4 那组灰阶读数的**可复查**版本（替代我已经跑丢的那把临时尺）。

为什么要这么麻烦（U-287）：Round 101 §4 里原本写着
"卡片对页面底 亮 247 对 255 = 8、暗 37 对 30 = 7"与"空格对卡片底 亮 12 / 暗 11"，
那两个数是一次性 `python3 - <<PY` 里量出来的 —— 脚本没落盘，
而它量的那一份"改前帧"随后被验证电池的 `rm -rf /tmp/r100_shots` 删掉了
⇒ 台账里留着一组**没有任何产物能复查**的数。这与 U-278 那一族（引用的与留下的是两份）同形。

这一版把尺落盘，并且只量**已经落盘的产物**：
- 卡片底 / 页面底：与判据 `CARD_BAND` 同一对定义（带内众数），用来对账；
- 热图空格：网格区里"最接近卡片底的那个显著众数"（也就是"没有记录的那些格"）；
- 图例最淡那一格：图例行里最淡的一块。

用法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r101_luma.py <帧目录>
坐标口径：帧是 720x540pt @2x ⇒ 位图 1440x1080px；pt 一律乘 2。
"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SCALE = 2

# 判据 `CARD_BAND` 在同一批帧上打印的 (页面底, 卡片底)。**这把尺必须与它对得上**，
# 否则"我这把尺量到的差"与"闸门判的那个差"就是两件事（R80 那一族：证人要与它作证的判据同一颗尺子）。
EXPECTED = {"light": (252, 244), "dark": (28, 36)}


def luma(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    return px, w, h


def rect_modes(px, x0, y0, x1, y1, top=6):
    """区域内灰阶众数，按出现次数排序（灰阶 = 0.299R+0.587G+0.114B 取整）。"""
    c = Counter()
    for y in range(int(y0 * SCALE), int(y1 * SCALE)):
        for x in range(int(x0 * SCALE), int(x1 * SCALE)):
            r, g, b = px[x, y][:3]
            c[int(0.299 * r + 0.587 * g + 0.114 * b)] += 1
    return c.most_common(top)


def rect_channels(px, x0, y0, x1, y1, want, top=6):
    """按**颜色族**分类后的众数（`want` 是判别函数）。

    为什么不能只看灰阶：热图的"空格"是**灰**、最淡那一档数据格是**淡蓝**，
    两者的亮度可以完全相同（本机实测都是 234）。用亮度轴判"灰 vs 蓝"
    会得到一个假的"空格与最淡一档分不开"—— 这正是 R77/R78 记过的那一族错法
    （轴与量对不上），所以这里按通道关系先分族，再在族内比。
    对比度用 RGB 欧氏距离 ÷ 441（= √(3·255²)），给的是一个 0…1 的"可感知距离"，
    与亮度差并列报出，不互相替代。
    """
    c = Counter()
    for y in range(int(y0 * SCALE), int(y1 * SCALE)):
        for x in range(int(x0 * SCALE), int(x1 * SCALE)):
            r, g, b = px[x, y][:3]
            if want(r, g, b):
                c[(r, g, b)] += 1
    return c.most_common(top)


GRAY = lambda r, g, b: max(r, g, b) - min(r, g, b) <= 8
BLUE = lambda r, g, b: b - r >= 12


def dist(a, b):
    return (sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5) / 441.0


def luma_of(rgb):
    """**与判据同一颗灰阶公式**（BT.601 加权）。

    第一版这里用的是"三通道取平均"，于是同一格最淡蓝报出 Δ22 而不是 Δ27 ——
    两个数都不算错，但台账里只能有一个，而且必须是**闸门用的那颗**
    （R68：证人要与它作证的判据同一颗尺子）。
    """
    r, g, b = rgb
    return int(0.299 * r + 0.587 * g + 0.114 * b)


def main():
    root = Path(sys.argv[1])
    # 这些 pt 坐标来自本轮判据自己的打印，不是我目测的：
    #   CARD_INSET settings-stats-populated light 卡片顶=109.0pt 卡片底=417.0pt 卡片左沿=172.0pt
    #   fixture 声明窗口 720x540pt，带子=60..540（左侧 60pt 是侧栏）
    CARD_TOP, CARD_BOTTOM, CARD_LEFT, WIN_RIGHT = 109.0, 417.0, 172.0, 720.0
    BAND_TOP = 60.0
    # 网格区与图例行：由"逐行扫描找色块"定位，不是估的 ——
    # 亮档图例四格在 y≈268..276pt（同一批颜色 164/197/220/234 也出现在网格里），
    # 网格最后一行到 y≈254pt，y≈292pt 那一整条 2056px 的同色横带是卡片内的 `Divider()`。
    GRID = (CARD_LEFT + 10, CARD_TOP + 40, WIN_RIGHT - 10, 260.0)
    LEGEND = (CARD_LEFT + 10, 266.0, WIN_RIGHT - 10, 278.0)
    for name in ("light", "dark"):
        path = root / ("settings-stats-populated-720x540-%s.png" % name)
        if not path.exists():
            print("MISSING %s" % path)
            continue
        px, w, h = luma(path)
        page = rect_modes(px, CARD_LEFT, BAND_TOP, WIN_RIGHT, CARD_TOP, top=1)[0][0]
        card = rect_modes(px, CARD_LEFT, CARD_TOP + 2, WIN_RIGHT, CARD_BOTTOM - 2, top=1)[0][0]
        # 卡片底与页面底是**中性灰**，取该族里最亮/最暗的代表 RGB 值来算距离
        card_rgb = rect_channels(px, CARD_LEFT, CARD_TOP + 2, WIN_RIGHT, CARD_BOTTOM - 2, GRAY, 1)[0][0]
        page_rgb = rect_channels(px, CARD_LEFT, BAND_TOP, WIN_RIGHT, CARD_TOP, GRAY, 1)[0][0]
        grid_gray = rect_channels(px, *GRID, GRAY, 4)
        grid_blue = rect_channels(px, *GRID, BLUE, 6)
        leg_blue = rect_channels(px, *LEGEND, BLUE, 4)
        print("== %s 尺寸=%dx%d" % (name, w, h))
        exp = EXPECTED.get(name)
        print("   与判据对账：这把尺(页面底,卡片底)=(%d,%d) 判据 CARD_BAND=%s ⇒ %s"
              % (page, card, exp, "一致" if exp == (page, card) else "不一致（先怀疑尺，再怀疑产品）"))
        print("   页面底=%d RGB=%s / 卡片底=%d RGB=%s ⇒ 亮度差=%d，RGB 距离=%.3f"
              % (page, page_rgb, card, card_rgb, abs(page - card), dist(page_rgb, card_rgb)))
        print("   网格里中性灰族（=没有记录的格子）=%s" % grid_gray)
        print("   网格里蓝族（=有记录的四档）=%s" % grid_blue)
        print("   图例行的蓝族四档=%s" % leg_blue)
        # 灰族里**第一档就是卡片底本身**（格子之间的缝就是卡片底，13.9 万像素），
        # 所以"空格"要取第一个与卡片底不同的档 —— 直接取 [0] 会得到"空格 vs 卡片底 = 0"这种假读数
        #（第一版就是这样，报出 Δ0 差点被写成"空格与卡片完全分不开"）。
        empty = next(((rgb, n) for rgb, n in grid_gray if dist(rgb, card_rgb) > 0.005), None)
        if empty:
            print("   空格（无记录）=%s（%dpx）vs 卡片底：亮度差=%d，RGB 距离=%.3f"
                  % (empty[0], empty[1],
                     abs(luma_of(empty[0]) - luma_of(card_rgb)), dist(empty[0], card_rgb)))
        else:
            print("   空格：灰族里找不到与卡片底不同的档 ⇒ 不判（不是 0）")
        if grid_blue:
            # **必须带像素量下限**：第一版在这里取"通道和最大"的那一档当最淡档，
            # 结果抓到的是一个只有 320px 的抗锯齿混色（(227,237,249)），
            # 报了个假的"最淡一档 Δ9"。真正的四档各有 1.0–1.8 万像素 ⇒ 先按量筛，再比色。
            #
            # 而且**标签不许叫"最淡/最深"**：那一版按通道和排序，在暗档会把语义整个反过来
            #（暗档里"最贴卡片底"的那一档 (34,54,77) 通道和最小，它其实是最淡的一档）。
            # 这一格要回答的问题是"卡片这条边界，比它包着的东西的边界强还是弱"，
            # 所以要的是**与卡片底距离最近 / 最远**的两档 —— 距离是对称量，两档同一口径。
            real = [(rgb, n) for rgb, n in grid_blue if n >= 5000]
            if not real:
                print("   色档：蓝族里没有 >=5000px 的档 ⇒ 不判（不是 0）")
            else:
                near = min(real, key=lambda t: dist(t[0], card_rgb))
                far = max(real, key=lambda t: dist(t[0], card_rgb))
                for label, (rgb, n) in (("离卡片底最近的色档", near), ("离卡片底最远的色档", far)):
                    print("   %s=%s（%dpx）vs 卡片底：亮度差=%d，RGB 距离=%.3f"
                          % (label, rgb, n,
                             abs(luma_of(rgb) - luma_of(card_rgb)), dist(rgb, card_rgb)))


if __name__ == "__main__":
    main()
