#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真机那一层的「录制中」描边判据 —— BACKLOG 179 的判据通道。

为什么要有它（R141 / 179）：这条描边挂在 `NSViewRepresentable` **外面**（SwiftUI 的 `.overlay`），
而离屏通道 `cacheDisplay` 量不到那一层 —— 本机实测：同一时刻、同一份代码，
点下去之后**真机截图有 1548 个高色度像素**（强调色那一圈），而 `cacheDisplay` 抓到的两帧
"新增墨 = 0"（它只看见 AppKit 那颗按钮自己换了标题）。
⇒ 于是"屏幕上有没有那一圈"这句话**不能**由离屏通道签，只能问真机（R123 那条通道的兄弟）。

它做什么：
  1. 起一次带 `CLIPBOARD_HISTORY_SPIKE_ONSCREEN=1` 的 spike 用例（它把两扇窗并排摆到屏幕上：
     一扇点过、一扇没点，各 12 秒）；
  2. 读用例写下的矩形（**由被测物自己印**，不写死坐标 —— 写死会把"截到哪一态"变成运气）；
  3. 各截一张，报"墨像素数 / 高色度像素数"，两态互相作对照；
  4. 只打长度、坐标、颜色数字，绝不打窗口里的文字。

退出码：0 = 通道通、点过那一屏有描边而静置那屏没有；
        1 = 通道没跑起来（`REALSCREEN_NOT_RUN`，**不算通过**：没权限 / 全黑 / 拿不到矩形）；
        2 = 通道通了但点过那一屏读不到描边（真机层面的缺陷）。

用法：PYTHONUTF8=1 python3 scripts/real_screen_recorder_ring.py [--keep-png]
"""
import argparse
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "ClipboardHistory")
RECT_FILE = "/tmp/spike_ring_rect.txt"
SPIKE_TEST = "HotKeyRecorderEvidenceTests/testSpikeOnScreenRingCapture"
IDLE_X_OFFSET = 320          # spike 用例里两扇窗的横向间距（点过在左、静置在右）
CHROMA_MIN = 60              # max-min 通道差超过它 = 有彩色（灰 bezel 与底色都到不了）
STRONG_MIN = 200             # 点过那一屏至少要有这么多高色度像素才算"那一圈在"
DIFFERENCE_MIN = 20          # 静置那一屏必须**几乎没有**彩色

# 与 real_screen_sidebar_icons.py 共用同一套基础件（辅助功能闸门、矩形解析、外观判定）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_screen_sidebar_icons import osascript  # noqa: E402


def count_ink(path):
    """返回 (墨像素数, 高色度像素数, 是否全黑)。没装 PIL 就抛出去让调用方记 NOT-RUN。"""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    step = max(1, w // 60)
    samp = sorted(px[x, y] for y in range(0, h, step) for x in range(0, w, step))
    bg = samp[len(samp) // 2]
    bg_luma = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    ink = 0
    strong = 0
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if abs(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] - bg_luma) > 12:
                ink += 1
            if max(c) - min(c) > CHROMA_MIN:
                strong += 1
    all_black = ink == 0
    return ink, strong, all_black


def verdict_of(clicked_strong, idle_strong, clicked_ink, idle_ink):
    """把两态读数约成一个**有名字**的出口（判据只能用方向与比值，不用绝对像素）。

    三种"没画"要分得开：整幅读不到（通道坏）、点过与静置一样（这一圈没画）、
    点过有彩色而静置没有（这一圈在）。所以每一支都有自己的名字与修法。
    """
    if clicked_ink == 0 or idle_ink == 0:
        return "all_black"                      # 通道坏（没权限 / 显示器睡着）⇒ 不是产品结论
    if clicked_ink < idle_ink * 0.5:
        return "frames_disagree"                # 两幅差得离谱 ⇒ 截到的不是同一块屏幕
    if clicked_strong >= STRONG_MIN and idle_strong <= DIFFERENCE_MIN:
        return "ring_present"
    if clicked_strong <= DIFFERENCE_MIN:
        return "ring_absent"                    # 真机层面：点下去屏幕上没有那一圈
    return "undecided"                          # 静置也有彩色 ⇒ 对照不干净，不能下结论


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-png", action="store_true", help="把两张截图留在 /tmp")
    args = ap.parse_args()

    code, enabled = osascript('tell application "System Events" to return UI elements enabled')
    if code != 0 or enabled.lower() != "true":
        print("REALSCREEN_NOT_RUN accessibility（UI elements enabled=%s）⇒ 这一格是没跑，不是通过" % enabled)
        return 1

    if os.path.exists(RECT_FILE):
        os.remove(RECT_FILE)                    # 上一遍的矩形不许替这一遍作证

    env = dict(os.environ, CLIPBOARD_HISTORY_SPIKE_ONSCREEN="1", PYTHONUTF8="1")
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["swift", "test", "--filter", SPIKE_TEST],
                            cwd=PKG, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + 150
        rect = None
        while time.time() < deadline and rect is None:
            time.sleep(1.0)
            if os.path.exists(RECT_FILE):
                try:
                    text = open(RECT_FILE, encoding="utf-8").read().strip()
                except OSError:
                    continue
                nums = [int(v) for v in re.findall(r"-?[0-9]+", text)]
                if len(nums) >= 4:
                    rect = nums[:4]
        if rect is None:
            print("REALSCREEN_NOT_RUN rect（拿不到 spike 用例自己印的矩形 ⇒ 窗口没摆上屏幕）")
            return 1
        x, y, w, h = rect
        time.sleep(2.0)                         # 等淡入落定（0.16s）+ 两扇窗都画完
        clicked_png, idle_png = "/tmp/real_screen_ring_clicked.png", "/tmp/real_screen_ring_idle.png"
        subprocess.run(["screencapture", "-x", "-R%d,%d,%d,%d" % (x, y, w, h), clicked_png], check=True)
        subprocess.run(["screencapture", "-x", "-R%d,%d,%d,%d" % (x + IDLE_X_OFFSET, y, w, h), idle_png],
                       check=True)
        try:
            c_ink, c_strong, c_black = count_ink(clicked_png)
            i_ink, i_strong, i_black = count_ink(idle_png)
        except ImportError:
            print("REALSCREEN_NOT_RUN pillow（没装 PIL ⇒ 量不了，不算通过）")
            return 1
        verdict = "all_black" if (c_black or i_black) else verdict_of(c_strong, i_strong, c_ink, i_ink)
        print("REALSCREEN_RING 矩形=%d,%d,%d,%d 点过：墨=%d 高色度=%d ｜ 静置：墨=%d 高色度=%d ⇒ %s"
              % (x, y, w, h, c_ink, c_strong, i_ink, i_strong, verdict))
        print("REALSCREEN_RING_VERDICT=%s（点过那一屏有强调色描边、静置那一屏没有 = 那一圈真的在屏幕上）"
              % verdict)
        for path in (clicked_png, idle_png):
            if not args.keep_png and os.path.exists(path):
                os.remove(path)
        return {"ring_present": 0, "ring_absent": 2, "frames_disagree": 2,
                "undecided": 2, "all_black": 1}.get(verdict, 1)
    finally:
        if proc.poll() is None:
            proc.terminate()                    # spike 自己会在 12 秒后收窗；这里只兜住它卡住的情况


if __name__ == "__main__":
    sys.exit(main())
