#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真机那一层「强调色到底解不解析」的量尺 —— BACKLOG 139 的判据通道（R132）。

为什么要有它：139 说「设置里的勾选框在帧里色度为 0：勾上不是强调蓝，而是换一档的灰」，
而这条结论**全部来自离屏通道**（`bitmapImageRepForCachingDisplay`）。同一族里已经有一条
被证伪过方向的先例：126 / 130 / 172 —— 离屏那一层对语义色（accent、vibrant）的解析与真机
不一致，所以"帧里色度 0"既可能是产品没上色，也可能是通道不认得那层材质。
172 是靠 `real_screen_sidebar_icons.py` 结的案；139 欠的是同一次操作，只是问的是**色度**而不是墨量。

它做什么：
  1. 走产品自己的入口打开设置窗口（状态菜单里的「设置」），并按名字按下侧栏的「通用」——
     那一屏有勾选框，别的屏没有 ⇒ 不在这一屏量的色度不算数；
  2. 只截这一扇窗口的矩形（`screencapture -R`），帧里不会出现主窗口的剪贴板内容；
  3. **同一张帧里**取两块：侧栏选中那一行（系统一定在画强调色，它是参照）与内容区（勾选框住在里面），
     各报 `b-r` 色度的均值与最大值；
  4. 只打坐标、长度、色度这类数，绝不打窗口里的文字。

判法（预先登记，两档之间留第三个出口，不许四舍五入到任一侧）：
  参照区最大色度 < REF_MIN ⇒ `no_reference`：参照自己坏了 ⇒ 这一格是没跑，不许读成"内容区也没色"
  内容区最大 ≥ 0.5 × 参照 ⇒ `accent_in_content`：真机上强调色解析出来了 ⇒ 139 是**通道**那一族
  内容区最大 < 0.25 × 参照 ⇒ `accent_missing`：真机上勾选框也不是强调蓝 ⇒ 139 是**产品缺陷**，开修
  其余 ⇒ `undecided`：比值落在中间，只配记成有名字的未覆盖

退出码：0 = 判到了（两种结论都算判到）；1 = 这一格没跑；2 = `undecided`。

用法：PYTHONUTF8=1 python3 scripts/real_screen_control_chroma.py [--keep-png]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from real_screen_sidebar_icons import (  # noqa: E402
    APP, SETTINGS_ITEM, STEP_PT, SIDEBAR_Y, ICON_X, INK_DELTA,
    appearance_of, osascript, parse_bounds)

SIDEBAR_ROW_NAME = "通用"
# 侧栏行的顺序由 `SettingsCategory.allCases` 定（shortcuts, general, privacy, …），
# 「通用」是第 2 行 ⇒ 下标 1。这一格是**读来的**，不是猜的：改那个枚举的顺序会让这里指错行，
# 而指错行的后果是"在别的屏上量勾选框的强调色" —— 所以落地验收（药丸移动）必须留着。
TARGET_ROW_INDEX = 1
REF_X = (8, 150)          # 侧栏那一列（pt，窗口内）：选中行的药丸住在这里
REF_Y = (30, 320)
CONTENT_X = (170, 690)    # 内容区（pt）：勾选框在卡片左侧那一列，最右留 30pt 避开滚动条
CONTENT_Y = (60, 420)
REF_MIN = 10              # 参照区最大 b-r 低于此值 ⇒ 参照坏了（不是"内容区也没色"）
MIN_STRONG_PIXELS = 40     # 8x5 的一小块：勾选框在 2x 下就是这个量级（本机实测见本轮 §8）
HIGH = 0.5                # 内容区/参照 ≥ 0.5 ⇒ 强调色在内容区解析出来了
LOW = 0.25                # < 0.25 ⇒ 真机上也没有


STRONG_DELTA = 100      # 一颗"足够蓝"的像素：与参照区自己读到的量级同一档（本机参照最大 194）


def chroma_stats(px, pw, ph, scale, x0, x1, y0, y1):
    """返回 (最大 b-r, 正的 b-r 均值, 命中像素数, 足够蓝的像素数, 那些像素的包围盒)。

    为什么最大不够：最大值是**单像素**统计量，一颗杂色就能把它顶起来（R100 那一族：
    贴边的极值会躲过判据）。所以同时报"有多少颗"与"它们住在哪" —— 后者能回答
    "那团蓝是不是勾选框那个位置"，而不是"内容区某处有一点蓝"。
    """
    best, total, n, strong = -255, 0, 0, 0
    box = [None, None, None, None]
    yy = int(y0 * scale)
    while yy < min(ph, int(y1 * scale)):
        for xx in range(int(x0 * scale), min(pw, int(x1 * scale))):
            r, g, b = px[xx, yy]
            d = b - r
            if d > best:
                best = d
            if d > 0:
                total += d
                n += 1
            if d >= STRONG_DELTA:
                strong += 1
                cx, cy = xx / scale, yy / scale
                if box[0] is None or cx < box[0]:
                    box[0] = cx
                if box[1] is None or cy < box[1]:
                    box[1] = cy
                if box[2] is None or cx > box[2]:
                    box[2] = cx
                if box[3] is None or cy > box[3]:
                    box[3] = cy
        yy += 1
    return best, (total / float(n) if n else 0.0), n, strong, box


def click_at(screen_x, screen_y):
    """按屏幕坐标点一下（侧栏行没有可寻的名字，只剩这一条路）。"""
    code, out = osascript('''
tell application "System Events"
  tell process "%s"
    set frontmost to true
    click at {%d, %d}
  end tell
end tell''' % (APP, int(screen_x), int(screen_y)))
    return code == 0 and "error" not in out.lower()


def pill_center(px, pw, ph, scale):
    """侧栏那一列里 `b-r` 最大的那一行 ⇒ 选中行药丸的中心（pt，窗口内）。

    参照物与验收物是同一个东西：这条判据拿它当"强调色一定在画"的锚点，
    也拿它**移动没有移动**来验收那一下点击真的落地了。
    """
    best, best_y = -255, None
    yy = int(REF_Y[0] * scale)
    while yy < min(ph, int(REF_Y[1] * scale)):
        row = 0
        for xx in range(int(REF_X[0] * scale), min(pw, int(REF_X[1] * scale))):
            r, g, b = px[xx, yy]
            row = max(row, b - r)
        if row > best:
            best, best_y = row, yy / scale
        yy += 1.0
    return best_y, best


def row_bands(px, pw, ph, scale, bg):
    """图标列里按 2pt 步进找行带（与 `real_screen_sidebar_icons` 同一形状，这里只要 y 区间）。"""
    bands, cur = [], None
    y = SIDEBAR_Y[0]
    while y < SIDEBAR_Y[1]:
        yy = int(y * scale)
        hit = False
        if 0 <= yy < ph:
            for xx in range(int(ICON_X[0] * scale), int(ICON_X[1] * scale)):
                if abs(px[xx, yy] - bg) > INK_DELTA:
                    hit = True
                    break
        if hit:
            cur = [y, y] if cur is None else [cur[0], y]
        elif cur is not None:
            if cur[1] - cur[0] >= 4:
                bands.append((cur[0], cur[1]))
            cur = None
        y += STEP_PT
    if cur is not None and cur[1] - cur[0] >= 4:
        bands.append((cur[0], cur[1]))
    return bands


def press_outcome(before, after, target, tol=8.0):
    """那一下点击算不算落地：只认「药丸从别处移到了目标行中心」。

    为什么不能只看"目标行现在有色"：选中行本来就可能停在目标行（那一次什么都没发生），
    也不能看"内容区变了"—— 内容区变了也可能只是鼠标悬停改了底色。
    四个出口各有名字，是因为这四种修法相反：
      already_selected 目标行本来就选中 ⇒ 不需要点，量就是了
      moved            点下去了，且是**被验收到的**（药丸移动 = 同帧的另一枚读数）
      not_landed       点了但药丸没动 ⇒ 这一格没跑（149 那一格今天又关了一次）
      unmeasured       药丸或行带压根没量到 ⇒ 尺坏了，与上面三种都不同
    """
    if before is None or target is None:
        return "unmeasured"
    if abs(before - target) <= tol:
        return "already_selected"
    if after is None:
        return "unmeasured"
    return "moved" if abs(after - target) <= tol else "not_landed"


def open_settings():
    code, out = osascript('''
tell application "System Events"
  set p to first process whose name is "%s"
  set frontmost of p to true
  try
    click menu bar item 1 of menu bar 2 of p
    delay 0.6
    click menu item "%s" of menu 1 of menu bar item 1 of menu bar 2 of p
  on error errMsg
    return "CLICK_ERR " & errMsg
  end try
  delay 1.0
  return "OK"
end tell''' % (APP, SETTINGS_ITEM))
    return code == 0 and out.startswith("OK")


def window_bounds():
    code, geom = osascript('''
tell application "System Events"
  set p to first process whose name is "%s"
  try
    set w to window "%s" of p
  on error
    return "NO_WINDOW"
  end try
  set a to position of w
  set s to size of w
  return (item 1 of a) & "," & (item 2 of a) & "," & (item 1 of s) & "," & (item 2 of s)
end tell''' % (APP, SETTINGS_ITEM))
    return parse_bounds(geom) if code == 0 else None


def box_is_wellformed(box):
    """包围盒自己就能证伪的一条恒等式：左上必须真的在右下之前。

    为什么需要它（U-439）：第一版把四个数按 (min-x, min-y, max-x, max-y) 存，
    却按 `x=a..b y=c..d` 的顺序印出去 ⇒ 真机那一跑印成 `x=177..98 y=192..219`，
    一个**倒过来的区间**看起来仍然像结论。形状像不像结论拦不住错的对象，
    所以这里要的是会红的那一格，不是注释。
    """
    if box[0] is None:
        return True                      # 空盒不是错
    return box[0] <= box[2] and box[1] <= box[3]


def _box_text(box):
    if box[0] is None:
        return "无"
    if not box_is_wellformed(box):
        return "BAD_BOX（内部顺序错：min/max 被印反了）"
    return "x=%.0f..%.0f y=%.0f..%.0fpt" % (box[0], box[2], box[1], box[3])


def verdict_of(ref_max, content_max):
    """判据本体：先问参照灵不灵，再问比值落在哪一档。"""
    if ref_max < REF_MIN:
        return "no_reference"
    ratio = content_max / float(ref_max)
    if ratio >= HIGH:
        return "accent_in_content"
    if ratio < LOW:
        return "accent_missing"
    return "undecided"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-png", action="store_true", help="把截图留在 /tmp（默认测完删掉）")
    args = ap.parse_args()

    code, enabled = osascript('tell application "System Events" to return UI elements enabled')
    if code != 0 or enabled.lower() != "true":
        print("REALSCREEN_NOT_RUN accessibility（UI elements enabled=%s）⇒ 没跑，不是通过" % enabled)
        return 1
    if not open_settings():
        print("REALSCREEN_NOT_RUN open_settings ⇒ 没跑，不是通过")
        return 1
    bounds = window_bounds()
    if bounds is None:
        print("REALSCREEN_NOT_RUN window_bounds ⇒ 没跑，不是通过")
        return 1
    x, y, w, h = bounds

    png = "/tmp/real_screen_control_chroma.png"
    if os.path.exists(png):
        os.remove(png)
    os.system("screencapture -x -R%d,%d,%d,%d %s" % (x, y, w, h, png))
    if not os.path.exists(png):
        print("REALSCREEN_NOT_RUN screencapture 没产出文件 ⇒ 没跑，不是通过")
        return 1
    try:
        from PIL import Image
    except ImportError:
        print("REALSCREEN_NOT_RUN pillow（没装 PIL ⇒ 量不了，不算通过）")
        return 1

    rgb = Image.open(png).convert("RGB")
    pw, ph = rgb.size
    if pw == 0 or ph == 0:
        print("REALSCREEN_NOT_RUN zero_size_capture")
        return 1
    px = rgb.load()
    scale = pw / float(w)
    gray = Image.open(png).convert("L")
    gx = gray.load()
    sample = [gx[a, b] for b in range(0, ph, 17) for a in range(0, pw, 17)]
    sample.sort()
    bg = sample[len(sample) // 2]
    if bg == 0 and min(sample) == 0:
        print("REALSCREEN_NOT_RUN all_black（通道坏了）⇒ 不许读成「真机上也没色」")
        return 1
    print("REALSCREEN_GEOM 窗口=%dx%dpt 帧=%dx%dpx 倍率=%.2fx 背景亮度=%d ⇒ 外观=%s"
          % (w, h, pw, ph, scale, bg, appearance_of(bg)))

    # ---- 切到目标那一屏，并且**用同一帧里的药丸移动**验收那一下点击落地 ----
    graypx = gray.load()
    bands = row_bands(graypx, pw, ph, scale, bg)
    pill_before, pill_chroma = pill_center(px, pw, ph, scale)
    print("REALSCREEN_ROWS 行带数=%d 药丸中心=%s 药丸处最大b-r=%d"
          % (len(bands), ("%.1fpt" % pill_before) if pill_before is not None else "无", pill_chroma))
    if len(bands) <= TARGET_ROW_INDEX:
        print("REALSCREEN_NOT_RUN 侧栏只量到 %d 条行带（要 ≥%d）⇒ 尺没压住行，色度不算数"
              % (len(bands), TARGET_ROW_INDEX + 1))
        return 1
    t0, t1 = bands[TARGET_ROW_INDEX]
    target = (t0 + t1) / 2.0
    if pill_before is None:
        print("REALSCREEN_NOT_RUN pill_center ⇒ 参照那一列没量到任何蓝色（尺坏了），不许读成「内容区也没色」")
        return 1
    # 点之前先问"目标行本来是不是就选中着"——这一格**不许**喂给 `press_outcome`：
    # 那个函数在"还没点"的时候没有 after 可读，会被读成 unmeasured（本轮就是这么错的，U-438）。
    outcome = "already_selected" if abs(pill_before - target) <= 8.0 else "needs_click"
    if outcome != "already_selected":
        if not click_at(x + 75, y + target):
            print("REALSCREEN_NOT_RUN click_at（osascript 报错）⇒ 149 那一格今天仍然不通")
            return 1
        time.sleep(1.0)
        os.remove(png)
        os.system("screencapture -x -R%d,%d,%d,%d %s" % (x, y, w, h, png))
        rgb = Image.open(png).convert("RGB")
        pw, ph = rgb.size
        px = rgb.load()
        pill_after, _ = pill_center(px, pw, ph, scale)
        outcome = press_outcome(pill_before, pill_after, target)
        print("REALSCREEN_CLICK 目标行中心=%.1fpt 点击前药丸=%s 点击后药丸=%s ⇒ %s"
              % (target, ("%.1f" % pill_before) if pill_before is not None else "无",
                 ("%.1f" % pill_after) if pill_after is not None else "无", outcome))
    if outcome == "not_landed":
        print("REALSCREEN_NOT_RUN click_not_landed ⇒ 坐标点击没落地（BACKLOG 149 那一格），色度不算数")
        return 1

    ref = chroma_stats(px, pw, ph, scale, REF_X[0], REF_X[1], REF_Y[0], REF_Y[1])
    con = chroma_stats(px, pw, ph, scale, CONTENT_X[0], CONTENT_X[1], CONTENT_Y[0], CONTENT_Y[1])
    ref_max, ref_mean, ref_n, ref_strong, ref_box = ref
    con_max, con_mean, con_n, con_strong, con_box = con
    print("REALSCREEN_CHROMA 参照=侧栏选中列 x=%d..%d 最大b-r=%d 正值均值=%.1f 命中像素=%d 强蓝像素=%d 包围盒=%s"
          % (REF_X[0], REF_X[1], ref_max, ref_mean, ref_n, ref_strong, _box_text(ref_box)))
    print("REALSCREEN_CHROMA 内容区 x=%d..%d 最大b-r=%d 正值均值=%.1f 命中像素=%d 强蓝像素=%d 包围盒=%s"
          % (CONTENT_X[0], CONTENT_X[1], con_max, con_mean, con_n, con_strong, _box_text(con_box)))
    # 比值之外还要问"那团蓝是不是成块的东西"：一颗杂色不算内容区上了强调色
    if con_max >= HIGH * ref_max and con_strong < MIN_STRONG_PIXELS:
        print("REALSCREEN_CHROMA_STRONG 强蓝像素只有 %d 颗（<%d）⇒ 最大值是孤点，判成未覆盖"
              % (con_strong, MIN_STRONG_PIXELS))
        con_max = 0
    ratio = (con_max / float(ref_max)) if ref_max > 0 else 0.0
    verdict = verdict_of(ref_max, con_max)
    meaning = {
        "no_reference": "参照区自己没色 ⇒ 这一格没判（侧栏选中那一行没在画强调色，或窗口不在「通用」）",
        "accent_in_content": "真机上内容区也解析强调色 ⇒ BACKLOG 139 判为**离屏通道**那一族（与 126/130/172 同类）",
        "accent_missing": "真机上内容区最大色度远低于参照 ⇒ BACKLOG 139 是**产品缺陷**：勾选框不是强调色",
        "undecided": "比值落在 0.25..0.5 之间 ⇒ 只配记成有名字的未覆盖，不许四舍五入到任一侧",
    }[verdict]
    print("REALSCREEN_CHROMA_RATIO 内容区/参照=%.3f 判法=≥%.2f 有色 / <%.2f 无色 / 参照下限=%d"
          % (ratio, HIGH, LOW, REF_MIN))
    print("REALSCREEN_CHROMA_VERDICT=%s ｜ %s" % (verdict, meaning))
    if not args.keep_png:
        os.remove(png)
    if verdict == "no_reference":
        return 1
    return 0 if verdict in ("accent_in_content", "accent_missing") else 2


if __name__ == "__main__":
    sys.exit(main())
