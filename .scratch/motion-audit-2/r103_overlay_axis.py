#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R103 / BACKLOG 148：浮层三条左轴的**证人级**尺（R100 那把 `r100_overlay_axis.py` 只配诊断）。

R100 那把尺自己登记过「只作诊断不作证人 —— 它没有正对照」，而它那句登记本轮被证实是必要的：
它判"这一带有没有墨"用的是**与填充差 ≥40 灰阶**这一条门限，而实测
"选中胶囊 vs 页面底"的灰阶差是 暗 **40.0**（70,70,70 对 30,30,30）/ 亮 **35.0**（220,220,220 对 255,255,255）
⇒ **同一把尺在暗档量到、在亮档量不到**，于是它报出「亮档没有胶囊」这种**格式像结论、内容来自门限**的假话
（R102 / U-284、U-302 同族；R100 的「门限 12..64 是平台」不可外推到另一对颜色）。

这一版的三条硬要求：
  ① **结构判据**：胶囊是"横跨 ≥55% 面板宽、纵向 ≥18pt 的一整块同色区域"，
     文字与图标是窄块 ⇒ 不需要靠"差多少灰阶"把两者分开（灰阶只用来与页面底做**非等**判断，门限取 12）；
  ② **正对照**：合成一张已知几何的图（页面底 + 胶囊 22.0..397.5 + 占位语 12.5 + 图标 35.5），
     两档各合成一次（暗 30/70，亮 255/220），尺必须把这三个数在 ±0.5pt 内读回来；
  ③ **负对照**：只有页面底的图必须报「没有胶囊」，**不许报 0、不许报"通过"**
     （R99 那一族：「没找到」被报成距离 0 是最贵的一种假绿）。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/r103_overlay_axis.py --selftest
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/r103_overlay_axis.py <帧目录>
退出码：0=自检通过且（真帧那一跑）读到了对象；1=自检失败或某档读不到；2=用法错。
"""
import sys
from collections import Counter
from io import BytesIO

from PIL import Image

SCALE = 2
PANEL_PT = 420.0
GREY = lambda r, g, b: int(0.2126 * r + 0.7152 * g + 0.0722 * b)   # 与判据同族：Rec.709


def _px(im):
    im = im.convert("RGB")
    return im.load(), im.size[0], im.size[1]


def page_grey(px, w, h):
    """页面底 = 整幅的**众数灰阶**（浮层面板里绝大多数像素就是底）。"""
    c = Counter()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c[GREY(*px[x, y])] += 1
    return c.most_common(1)[0][0]


def band_rows(px, w, h, page):
    """把纵向切成"有内容的带"：一行的非底像素 ≥ 8% 宽度才算带内。"""
    rows, out = [], []
    for y in range(h):
        n = sum(1 for x in range(0, w, 4) if abs(GREY(*px[x, y]) - page) >= 12)
        rows.append(n >= (w // 4) * 0.08)
    y = 0
    while y < h:
        if rows[y]:
            y0 = y
            while y < h and rows[y]:
                y += 1
            out.append((y0 / SCALE, y / SCALE))
        else:
            y += 1
    return out


def capsule(px, w, h, page):
    """结构判据找胶囊：返回 (左沿 pt, 右沿 pt, 顶 pt, 底 pt) 或 None（**不是 0**）。"""
    best = None
    for (y0, y1) in band_rows(px, w, h, page):
        if (y1 - y0) < 18:
            continue
        cols = [x for x in range(w)
                if sum(1 for y in range(int(y0 * SCALE), int(y1 * SCALE))
                       if abs(GREY(*px[x, y]) - page) >= 12) >= (y1 - y0) * SCALE * 0.6]
        if not cols:
            continue
        left, right = min(cols) / SCALE, max(cols) / SCALE
        if (right - left) < 0.55 * PANEL_PT:
            continue          # 窄块 = 文字/图标那一类，不是行背景
        if best is None or (right - left) > (best[1] - best[0]):
            best = (left, right, y0, y1)
    return best


def leftmost_ink(px, w, h, page, y0, y1, exclude=None):
    """某一带里最左的**墨**（排除胶囊本体：与页面底差 ≥12 且不属于胶囊的同色大块）。"""
    for x in range(w):
        if exclude and exclude[0] - 0.5 <= x / SCALE <= exclude[1] + 0.5:
            pass
        for y in range(int(y0 * SCALE), int(y1 * SCALE)):
            if abs(GREY(*px[x, y]) - page) >= 12:
                return x / SCALE
    return None


def measure(src):
    """`src` 可以是路径，也可以是已经打开的 `Image`（自检走后者，不落盘临时文件）。"""
    im = src if hasattr(src, "convert") else Image.open(src)
    px, w, h = _px(im)
    page = page_grey(px, w, h)
    cap = capsule(px, w, h, page)
    rows = band_rows(px, w, h, page)
    return {"page": page, "capsule": cap, "bands": len(rows),
            "first_band": rows[0] if rows else None}


def synth(page_v, cap_v, text_v):
    """合成一张已知几何的浮层：胶囊 22.0..397.5（y 46..80pt），占位语墨在 x=12.5（y 14..26pt），
    图标墨在 x=35.5（y 91..103pt）。"""
    w, h = int(PANEL_PT * SCALE), int(300 * SCALE)
    im = Image.new("RGB", (w, h), (page_v, page_v, page_v))
    px = im.load()

    def rect(x0, y0, x1, y1, v):
        for x in range(int(x0 * SCALE), int(x1 * SCALE)):
            for y in range(int(y0 * SCALE), int(y1 * SCALE)):
                px[x, y] = (v, v, v)
    rect(22.0, 46.0, 397.5, 80.0, cap_v)          # 行背景
    rect(12.5, 14.5, 120.0, 26.5, text_v)         # 搜索框文字（故意比胶囊靠左）
    rect(35.5, 91.5, 47.0, 103.0, text_v)         # 第二行图标
    return im


def selftest():
    ok = []
    for page_v, cap_v, tag in ((30, 70, "dark"), (255, 220, "light")):
        im = synth(page_v, cap_v, 8 if page_v > 128 else 250)
        buf = BytesIO()
        im.save(buf, format="PNG")
        buf.seek(0)
        m = measure_from_bytes(buf.read())
        c = m["capsule"]
        good = c is not None and abs(c[0] - 22.0) <= 0.5 and abs(c[1] - 397.5) <= 0.6
        ok.append(good)
        print("  正对照 %s（页面 %d / 胶囊 %d）⇒ 读到 %s ⇒ %s"
              % (tag, page_v, cap_v,
                 ("%.1f..%.1f" % (c[0], c[1])) if c else "None", "对" if good else "!! 错"))
    # 负对照：只有页面底 ⇒ 必须 None，不许 0
    empty = Image.new("RGB", (int(PANEL_PT * SCALE), int(300 * SCALE)), (30, 30, 30))
    buf = BytesIO()
    empty.save(buf, format="PNG")
    buf.seek(0)
    m = measure_from_bytes(buf.read())
    neg = m["capsule"] is None
    ok.append(neg)
    print("  负对照（纯页面底）⇒ 胶囊=%s ⇒ %s（报 0 或报「通过」都算错）"
          % (m["capsule"], "对" if neg else "!! 错"))
    print("SELFTEST=%s" % ("ok" if all(ok) else "FAILED"))
    return 0 if all(ok) else 1


def measure_from_bytes(data):
    return measure(Image.open(BytesIO(data)))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--selftest":
        return selftest()
    from pathlib import Path
    root = Path(args[0])
    bad = 0
    for name in ("quickpick-list-420x300-light.png", "quickpick-list-420x300-dark.png"):
        p = root / name
        if not p.exists():
            print("MISSING %s" % p)
            bad += 1
            continue
        m = measure(str(p))
        c = m["capsule"]
        print("%-34s 页面底=%d 带数=%d 胶囊=%s"
              % (name, m["page"], m["bands"],
                 ("左 %.1f 右 %.1f y %.1f..%.1f" % c) if c else "!! 没有（不是 0）"))
        if c is None:
            bad += 1
    print("AXIS_READ_BAD=%d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
