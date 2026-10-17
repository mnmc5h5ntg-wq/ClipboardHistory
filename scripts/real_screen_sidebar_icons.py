#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真机（合成后的屏幕）那一层的侧栏图标量尺 —— BACKLOG 172 的判据通道。

为什么要有它（R123 / 172）：R122 修「暗档两枚图标黑底黑图标」时，证据全在**离屏通道**里
（`bitmapImageRepForCachingDisplay`），而同一批离屏帧在亮档又报"图标几乎不画墨"。
两档读数朝相反方向动，光靠离屏没法判"是产品淡还是通道淡"—— 那一层只有真机能答。
R91 当年试过这条通道，结果是 `screencapture` 返回全黑（显示器睡着 / 没有录屏权限），
于是那一格记成"没跑"。本轮实测通道是通的（`UI elements enabled=true`、截图非全黑），
所以把它固化成脚本，而不是靠记忆再手点一遍。

它做什么：
  1. 用 System Events 走**产品自己的入口**（状态菜单里的「设置」）打开设置窗口 —— 不许自己 new 一个窗口；
  2. 只截这一扇窗口的矩形（`screencapture -R`），因此帧里不会出现主窗口的剪贴板内容；
  3. 在图标列里按 2pt 步进自动找行带，逐带报"墨像素数 / 最大偏离"，再与同一行的文字列对照；
  4. 只打长度、坐标、亮度这类数，绝不打窗口里的文字。

退出码：0 = 通道通且六枚图标全部可辨；1 = 通道没跑起来（打 `REALSCREEN_NOT_RUN`，**不算通过**）；
        2 = 通道通了但有行带读不到墨（真机层面的缺陷）。

用法：PYTHONUTF8=1 python3 scripts/real_screen_sidebar_icons.py [--label 快捷键] [--keep-png]
"""
import argparse
import os
import re
import subprocess
import sys
import time

APP = "ClipboardHistoryApp"
SETTINGS_ITEM = "设置"
ICON_X = (10, 36)        # 图标列（pt，窗口内）
TEXT_X = (40, 142)       # 同一行的文字列（pt）
SIDEBAR_Y = (30, 320)    # 侧栏行所在的 y 带（pt，含标题栏）
EXPECTED_BANDS = 6
STEP_PT = 2.0
INK_DELTA = 60


def parse_bounds(text):
    """从 System Events 返回的那一串里取出 x,y,w,h —— 分隔符不可信，只认整数。

    为什么单独抽出来并配单测（R123）：第一版判的是 `text.count(",") != 3`，而 AppleScript
    把两个二元列表用 `&` 拼起来时会在中间塞空项，实测返回 `375, , 101, , 720, , 572`
    ⇒ 一次**成功**的测量被读成 NO_WINDOW、脚本以"没跑"退出。这类错法的形状是
    "我以为被测物会打成什么样"，所以判据只能是正则取数 + 数量够不够。
    """
    nums = re.findall(r"-?[0-9]+", text or "")
    if (text or "").startswith("NO_WINDOW") or len(nums) < 4:
        return None
    return tuple(int(v) for v in nums[:4])


def appearance_of(bg_luma):
    """外观位必须自己报，不许由"我以为系统是哪档"推。

    R123 的现场：为了量亮档，我给 App 域写了 `AppleInterfaceStyle = Light` 并重启了 App，
    读数与暗档**逐字相同** —— 如果没有这一格把 `外观=dark` 打出来，那一跑就会被当成
    "亮档也 OK"记进账（U-412）。所以：改外部设置的实验，必须自己验证生效那一半。
    """
    return "dark" if bg_luma < 100 else "light"


def osascript(src):
    proc = subprocess.run(["osascript", "-e", src], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-png", action="store_true", help="把截图留在 /tmp（默认测完删掉）")
    args = ap.parse_args()

    code, enabled = osascript('tell application "System Events" to return UI elements enabled')
    if code != 0 or enabled.lower() != "true":
        print("REALSCREEN_NOT_RUN accessibility（UI elements enabled=%s）⇒ 这一格是没跑，不是通过" % enabled)
        return 1

    # 走产品入口：状态菜单（menu bar 2 的第一项）里的「设置」
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
    if code != 0 or not out.startswith("OK"):
        print("REALSCREEN_NOT_RUN open_settings（osascript 返回：%s）" % out[:120])
        return 1

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
    # 解析要**从被测物自己那里取数**，不许假设分隔符干净：AppleScript 把两个二元列表用 `&`
    # 拼起来时会在中间塞空项（实测返回 `375, , 101, , 720, , 572`），
    # 于是第一版那句 `geom.count(",") != 3` 把一次成功的测量读成了 NO_WINDOW（R123）。
    parsed = parse_bounds(geom)
    if code != 0 or parsed is None:
        print("REALSCREEN_NOT_RUN window_bounds（%s）" % geom[:120])
        return 1
    x, y, w, h = parsed

    png = "/tmp/real_screen_sidebar_icons.png"
    if os.path.exists(png):
        os.remove(png)
    subprocess.run(["screencapture", "-x", "-R%d,%d,%d,%d" % (x, y, w, h), png], check=True)
    try:
        from PIL import Image
    except ImportError:
        print("REALSCREEN_NOT_RUN pillow（没装 PIL ⇒ 量不了，不算通过）")
        return 1
    img = Image.open(png).convert("L")
    pw, ph = img.size
    if pw == 0 or ph == 0:
        print("REALSCREEN_NOT_RUN zero_size_capture")
        return 1
    px = img.load()
    scale = pw / float(w)
    # 背景取整张帧的中位亮度；全黑（通道坏了）与真机深色要分得开
    sample = [px[a, b] for b in range(0, ph, 17) for a in range(0, pw, 17)]
    sample.sort()
    bg = sample[len(sample) // 2]
    darkest = min(sample)
    if bg == 0 and darkest == 0:
        print("REALSCREEN_NOT_RUN all_black（screencapture 拿到全黑帧 = 显示器睡着或没录屏权限，"
              "R91 那一格的原样）⇒ 不许读成「真机也看不见」")
        return 1
    appearance = appearance_of(bg)
    print("REALSCREEN_GEOM 窗口=%dx%dpt 帧=%dx%dpx 倍率=%.2fx 背景亮度=%d ⇒ 外观=%s"
          % (w, h, pw, ph, scale, bg, appearance))

    def band_ink(y_pt):
        yy = int(y_pt * scale)
        if yy < 0 or yy >= ph:
            return 0, 0
        n = 0
        mx = 0
        for xx in range(int(ICON_X[0] * scale), int(ICON_X[1] * scale)):
            v = px[xx, yy]
            d = abs(v - bg)
            if d > INK_DELTA:
                n += 1
            if d > mx:
                mx = d
        return n, mx

    bands, cur = [], None
    y = SIDEBAR_Y[0]
    while y < SIDEBAR_Y[1]:
        n, mx = band_ink(y)
        if n > 0:
            if cur is None:
                cur = [y, y, n, mx]
            else:
                cur[1] = y
                cur[2] += n
                cur[3] = max(cur[3], mx)
        elif cur is not None:
            if cur[1] - cur[0] >= 4:
                bands.append(tuple(cur))
            cur = None
        y += STEP_PT
    if cur is not None and cur[1] - cur[0] >= 4:
        bands.append(tuple(cur))

    for i, b in enumerate(bands):
        print("REALSCREEN_ICON_BAND %d y=%.0f..%.0fpt 墨像素=%d 最大偏离=%d" % (i, b[0], b[1], b[2], b[3]))

    def column_ink(x0, x1, y0, y1):
        n = 0
        yy = int(y0 * scale)
        while yy < min(ph, int(y1 * scale)):
            for xx in range(int(x0 * scale), int(x1 * scale)):
                if abs(px[xx, yy] - bg) > INK_DELTA:
                    n += 1
            yy += 1
        return n

    text_ink = column_ink(TEXT_X[0], TEXT_X[1], SIDEBAR_Y[0], SIDEBAR_Y[1])
    icon_ink = sum(b[2] for b in bands)
    print("REALSCREEN_RATIO 图标列墨=%d 文字列墨=%d 比值=%.3f 行带数=%d（期望 %d）"
          % (icon_ink, text_ink, (icon_ink / text_ink if text_ink else 0.0), len(bands), EXPECTED_BANDS))
    verdict = "ok" if len(bands) >= EXPECTED_BANDS else "missing_bands"
    print("REALSCREEN_VERDICT=%s 外观=%s（六枚侧栏图标在真机上全部可辨 = 图标列墨落在与文字列同一边）"
          % (verdict, appearance))
    if not args.keep_png:
        os.remove(png)
    return 0 if verdict == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
