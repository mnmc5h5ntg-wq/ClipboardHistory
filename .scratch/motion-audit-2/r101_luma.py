#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置「统计」那一屏的边界强度尺（R101 收尾落盘，R102 与判据对账）。

为什么要这么麻烦（R101 / U-287）：Round 101 §4 那组灰阶原本量自一段没落盘的
`python3 - <<PY`，而它量的「改前那一帧」随后被验证电池的 `rm -rf /tmp/r100_shots` 删掉了
⇒ 台账里留着一组**没有任何产物能复查**的数（与 U-278 那一族同形：引用的与留下的是两份）。
这一版把尺落盘，只量**已经落盘的产物**（帧基线钉着的那 130 张）。

R102 补的第二件事（BACKLOG 151 的结案）：这把尺与判据 `CARD_BAND` 曾经各报一个数
（判据 252/244 与 28/36；这把尺 255/247 与 30/37）。追下去之后**两把尺都没有坏**，
差在三处口径，而每一处都写在下面：
  ① 判据的 `modalLuma` 把灰阶按 8 量化并返回**桶心** `(v//8)*8+4`
    （255→252、247→244、30→28、37→36），这把尺返回**精确值**；
  ② 判据用 **Rec.709** 权重 + `rounded()`，这把尺原本用 **BT.601** + 取整
    —— 中性灰上两者只差 1，彩色上同样差 1（最淡那档蓝：601 给 220，709 给 221）；
  ③ 判据的「页底」取的是**窗口顶部 y 4..12pt** 那一条，这把尺原本取**卡片之上** y 60..109pt。
⇒ 现在权重跟判据一致，并且 `--judge` 会**逐字复现** `CARD_BAND` 打的那两个数：
   对不上就非 0 退出。这就是 151 要的「要么一致、要么响」，不是「再打印一遍」。

用法：
    PYTHONUTF8=1 python3 .scratch/motion-audit-2/r101_luma.py <帧目录>
    PYTHONUTF8=1 python3 .scratch/motion-audit-2/r101_luma.py <帧目录> --judge 252,244 28,36

坐标口径：帧是 720x540pt @2x ⇒ 位图 1440x1080px；pt 一律乘 2。
"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SCALE = 2

# 判据 `CARD_BAND` 在同一批帧（与 `docs/frame_baseline.json` 逐字节相同的那一版）上打印的
# (页面底, 卡片底)。带 `--judge` 时这是等式自检的靶子。
EXPECTED = {"light": (252, 244), "dark": (28, 36)}

# 判据自己的页底采样带（`UICaptureHarness.swift:6516`）：x 150..710pt、y 4..12pt。
JUDGE_PAGE_BAND_PT = (150.0, 4.0, 710.0, 12.0)

# 卡片几何来自判据自己的打印，不是我目测的：
#   CARD_INSET settings-stats-populated light 卡片顶=109.0pt 卡片底=417.0pt 卡片左沿=172.0pt
CARD_TOP, CARD_BOTTOM, CARD_LEFT, WIN_RIGHT = 109.0, 417.0, 172.0, 720.0
CARD_BAND = (CARD_LEFT, CARD_TOP + 2, WIN_RIGHT, CARD_BOTTOM - 2)

# 网格区与图例行由「逐行扫描找色块」定位：亮档图例四格在 y 约 268..276pt，
# 网格最后一行到 y 约 254pt，y 约 292pt 那条 2056px 的同色横带是卡片内的 Divider。
GRID = (CARD_LEFT + 10, CARD_TOP + 40, WIN_RIGHT - 10, 260.0)
LEGEND = (CARD_LEFT + 10, 266.0, WIN_RIGHT - 10, 278.0)

# 一格 12pt@2x 约 576px；低于这个量的「档」是抗锯齿混色，不算一档（R101 第一版就踩过）。
MIN_STEP_PIXELS = 5000


def luma(rgb):
    """Rec.709 + 四舍五入 —— 与 `modalLuma` 一颗尺（R68：证人要与它作证的判据同一颗尺子）。"""
    r, g, b = rgb
    return int((0.2126 * r + 0.7152 * g + 0.0722 * b) + 0.5)


def bucket_centre(value):
    """判据返回的不是像素灰阶，是桶心。台账里引用判据的数时必须记得这一点。"""
    return (value // 8) * 8 + 4


def load(path):
    im = Image.open(path).convert("RGB")
    return im.load(), im.size


def modal_judge(px, x0, y0, x1, y1):
    """逐字复现 `modalLuma`：Rec.709 → rounded → //8 直方图 → 众数桶 → 桶心。"""
    h = Counter()
    for y in range(int(y0 * SCALE), int(y1 * SCALE)):
        for x in range(int(x0 * SCALE), int(x1 * SCALE)):
            h[luma(px[x, y][:3]) // 8] += 1
    if not h:
        return -1
    return bucket_centre(max(h, key=lambda k: h[k]) * 8)


GRAY = lambda r, g, b: max(r, g, b) - min(r, g, b) <= 8
BLUE = lambda r, g, b: b - r >= 12


def rect_channels(px, x0, y0, x1, y1, want, top=6):
    """按**颜色族**分类后的 RGB 众数（`want` 是判别函数）。

    为什么要分族（R102 用实测钉住这句话，而不是像第一版那样写一个没量过的断言）：
    暗档「没有记录的空格」是灰 (48,48,48)，「最淡一档有记录」是蓝 (34,54,77)，
    两者灰阶只差 **2**（48 对 50）；亮档差 **14**（235 对 221）。
    ⇒ 只看灰阶众数，暗档那两格根本分不开谁是谁 —— 区别全在色相上。
    （第一版这里写的是「灰与蓝亮度完全相同，本机实测都是 234」，那是**没量过的话**：
    实测两族没有同值，R102 换成上面这组有出处的数。）
    对比度另给一个 RGB 欧氏距离 / 441（= sqrt(3*255^2)）的 0…1 量，与灰阶差并列报，不互相替代。
    """
    c = Counter()
    for y in range(int(y0 * SCALE), int(y1 * SCALE)):
        for x in range(int(x0 * SCALE), int(x1 * SCALE)):
            rgb = px[x, y][:3]
            if want(*rgb):
                c[rgb] += 1
    return c.most_common(top)


def dist(a, b):
    return (sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5) / 441.0


def measure(px, name, reconcile=None):
    page_rgb = rect_channels(px, *JUDGE_PAGE_BAND_PT, GRAY, 1)[0][0]
    card_rgb = rect_channels(px, *CARD_BAND, GRAY, 1)[0][0]
    page_exact, card_exact = luma(page_rgb), luma(card_rgb)
    page_judge = modal_judge(px, *JUDGE_PAGE_BAND_PT)
    card_judge = modal_judge(px, *CARD_BAND)
    print("== %s" % name)
    print("   页面底：判据口径=%d（桶心）精确=%d RGB=%s ｜ 卡片底：判据口径=%d 精确=%d RGB=%s"
          % (page_judge, page_exact, page_rgb, card_judge, card_exact, card_rgb))
    print("   ⇒ 卡片这条边界：灰阶差=%d，RGB 距离=%.3f" % (abs(page_exact - card_exact), dist(page_rgb, card_rgb)))
    rc = 0
    if reconcile:
        got = (page_judge, card_judge)
        ok = got == tuple(reconcile)
        print("   等式自检：这把尺复现判据 %s ⇒ %s" % (str(tuple(reconcile)), "一致" if ok else "**不一致：先怀疑尺**"))
        if not ok:
            rc = 1
    grid_gray = rect_channels(px, *GRID, GRAY, 4)
    grid_blue = rect_channels(px, *GRID, BLUE, 6)
    leg_blue = rect_channels(px, *LEGEND, BLUE, 4)
    # 灰族里**第一档就是卡片底本身**（格子之间的缝就是卡片底，约 14 万像素），
    # 所以「空格」要取第一个与卡片底不同的档 —— 直接取 [0] 会报出「空格 vs 卡片底 = 0」这种假读数。
    empty = next(((rgb, n) for rgb, n in grid_gray if dist(rgb, card_rgb) > 0.005), None)
    if empty:
        print("   空格（无记录，灰族）=%s（%dpx）vs 卡片底：灰阶差=%d，RGB 距离=%.3f"
              % (empty[0], empty[1], abs(luma(empty[0]) - card_exact), dist(empty[0], card_rgb)))
    else:
        print("   空格：灰族里找不到与卡片底不同的档 ⇒ 不判（不是 0）")
    real = [(rgb, n) for rgb, n in grid_blue if n >= MIN_STEP_PIXELS]
    if not real:
        print("   色档：蓝族里没有 >=%dpx 的档 ⇒ 不判（不是 0）" % MIN_STEP_PIXELS)
    else:
        # 标签用「离卡片底最近/最远」而不是「最淡/最深」：后者按通道和排序，
        # 在暗档会把语义整个反过来（最贴卡片底的那一档通道和最小，却是最淡的一档）。
        near = min(real, key=lambda t: dist(t[0], card_rgb))
        far = max(real, key=lambda t: dist(t[0], card_rgb))
        for label, (rgb, n) in (("离卡片底最近的色档", near), ("离卡片底最远的色档", far)):
            print("   %s=%s（%dpx）vs 卡片底：灰阶差=%d，RGB 距离=%.3f"
                  % (label, rgb, n, abs(luma(rgb) - card_exact), dist(rgb, card_rgb)))
        if empty:
            print("   空格与最近色档：灰阶差=%d，RGB 距离=%.3f ⇒ 只看灰阶会不会分错，看的就是这一格"
                  % (abs(luma(empty[0]) - luma(near[0])), dist(empty[0], near[0])))
    same = bool(real) and {rgb for rgb, _ in leg_blue} == {rgb for rgb, _ in real}
    print("   图例四档与网格四档逐色相同 = %s（图例灰阶 %s）"
          % ("是" if same else "否", sorted(luma(rgb) for rgb, _ in leg_blue)))
    return rc


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    root = Path(argv[0])
    judge = dict(EXPECTED)
    if "--judge" in argv:
        i = argv.index("--judge")
        try:
            judge = {"light": tuple(int(x) for x in argv[i + 1].split(",")),
                     "dark": tuple(int(x) for x in argv[i + 2].split(","))}
        except Exception as exc:
            print("--judge 用法：--judge 252,244 28,36（%s）" % exc)
            return 2
    rc = 0
    for name in ("light", "dark"):
        path = root / ("settings-stats-populated-720x540-%s.png" % name)
        if not path.exists():
            print("MISSING %s" % path)
            rc = 1
            continue
        px, size = load(path)
        print("   （%s：%dx%d px）" % (path.name, size[0], size[1]))
        rc |= measure(px, name, judge.get(name))
    print("LUMA_RECONCILE=" + ("ok" if rc == 0 else "FAILED"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
