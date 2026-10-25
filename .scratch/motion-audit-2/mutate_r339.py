#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R339 的变异表（第 338 轮 / Round 336）：选中那颗的抬量，三条轴各钉一把。

R339 修的是 runner 从 `117f45d` 起**连续 8 跑**的那朵红（STEP[15] executed-count gate +
STEP[17] Capture gate，三条断言全在 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces`
的暗档）。两机同格的读数把这件事说清了：

· 本机离屏 页底 30 → 轨道 52、不透明基准 70 ⇒ 差 **+18**（R333 落地时量到的就是这一档）
· runner 离屏 页底 50 → 轨道 70、基准还是 70 ⇒ 差 **+0.0**（`SEGREF_POLARITY dark` 同一跑里
  系统那颗是 差=+49.0 ⇒ 通道画得出选中，只画不出自家那颗 ⇒ **不是**通道限制，不能按出口处理）
· R330 真机 页底 51 → 轨道 81 ⇒ 差 **−11**（选中又变回轨道上的一个暗洞，就是 377 那颗）

修法是给暗档那枚语义基准**再盖一层**固定抬量（`selectedSegmentLiftWhite` α=0.20 ⇒ 那颗 ≈107）。
本轮新增的 `SEG_PILL_BACKING` 把页底变成能点名的自变量，所以这三条轴在**本机**就有红有绿。
（第一版写法是"整颗改成跟着轨道走的叠加"，被另一条判据当场否掉：叠加压在侧栏那条现读 255 的
假轨道上等于没画，两态帧之间一个字都不差 ⇒ `FILTER_PILL_BAND dark 候选带数=0` 红。
这条红留在账上，见 BACKLOG 413。）

三把刀各打一条轴（只钉一条，另外两条会漂）：

· M996 两支对调（暗档不盖、亮档盖）⇒ 像素判据必须红：页底 50 那档又塌成 差=0。
  这一刀就是 R333 那一版原样，而它在**本机**是绿的 —— 正是本轮要修的盲区形状。
· M997 抬量 0.20→0.05（太小，那颗算到 ≈79）⇒ 盖不过最亮那条轨道（97）⇒ 必须红。
· M998 抬量 0.20→0.40（太大，那颗 ≈144）⇒ 像素判据反而更宽（不会红），
  红必须落在**夹出它的那两条边界**那一格（②超过系统那颗 109）⇒ 必须红在那一格。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r339.py [M996 M997 M998]
（结论只准由 XCTest 的汇总行说；编译不过 = NOT_RUN，不算过关 = D-243。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOB = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                    "Views", "PressableStyle.swift")
TOKENS = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "VisualTokens.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIXEL_CELL = u"UICaptureTests/testSelectedPillStaysAboveItsTrackOnEveryBacking"
PURE_CELL = u"FilterPillMotionTests"
CELL = PURE_CELL + u"|" + PIXEL_CELL
# `expect` 用**裸方法名**：失败行打的是 `-[Bundle.Class methodName] : XCTAssert…`，
# 带 `Class/` 前缀的写法在失败行里根本不存在 ⇒ 每一刀都会被判成打空。
PIXEL_RED = u"testSelectedPillStaysAboveItsTrackOnEveryBacking"
PURE_RED = u"testSelectedSegmentLiftAlphaIsTheSandwichSolvedFromMeasuredTracks"

NEEDLE_996 = u"        dark ? VisualMaterial.selectedSegmentLiftWhite : nil"
REPL_996 = u"        dark ? nil : VisualMaterial.selectedSegmentLiftWhite"

NEEDLE_ALPHA = u"    static let selectedSegmentLiftWhite: Double = 0.20"
REPL_997 = u"    static let selectedSegmentLiftWhite: Double = 0.05"
REPL_998 = u"    static let selectedSegmentLiftWhite: Double = 0.40"

ARMS = [
    ("M996", u"产品：两支对调（暗档不盖、亮档盖）⇒ runner 那档 差=0 必须被像素判据抓住",
     KNOB, NEEDLE_996, REPL_996, PIXEL_RED, CELL),
    ("M997", u"产品：抬量 0.20→0.05（太小）⇒ 盖不过最亮那条实测轨道，必须红",
     TOKENS, NEEDLE_ALPHA, REPL_997, PIXEL_RED, CELL),
    ("M998", u"产品：抬量 0.20→0.40（太大）⇒ 像素判据反而过线，红必须落在夹出它的那两条边界",
     TOKENS, NEEDLE_ALPHA, REPL_998, PURE_RED, CELL),
]

SNAPSHOT = {}
_MISSING = object()


def sh(cmd):
    p = subprocess.run(cmd, cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


def read(path):
    with open(path, encoding="utf-8") as h:
        return h.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as h:
        h.write(text)


def red_in(out, name):
    u"""『红在这一格』必须能在**同一行**里同时看到那一格的名字与失败字样。

    只判 `name in out` 会被"这一格跑过并且 passed"喂饱（swift test 两种都打名字），
    于是刀打空也报 CAUGHT —— 与 R262 那三根腐烂针同一族：结果通道本身会坏。
    """
    for line in out.splitlines():
        if name in line and (u"error:" in line or u"' failed" in line):
            return True
    return False


def run_cell(filter_name):
    u"""红不红只准由 XCTest 的汇总行说，不许由「日志里有没有 error: 字样」说：
    产品自己会往 stderr 倒系统噪声（`CoreData: error: …AddressBook…`，本机每次跑都有）。
    """
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", filter_name])
    executed = re.findall(r"Executed (\d+) tests, with (\d+) failures", out)
    if not executed:
        return (True, u"?", out)                      # 一行汇总都没有 ⇒ 编译没过 / 根本没跑
    n, fails = executed[-1]
    red = int(fails) > 0 or "Test Suite 'Selected tests' failed" in out
    return (red, n, out)


def main(argv):
    picked = [a for a in ARMS if not argv or a[0] in argv]
    if not picked:
        print(u"ARG_ERROR 认不出臂号：" + u" ".join(argv))
        return 2
    print(u"===== 基线（未落刀）")
    baseline_ok = True
    for cell in sorted(set(a[6] for a in picked)):
        red, n, out = run_cell(cell)
        print(u"BASELINE %s %s Executed=%s" % (cell, u"RED" if red else u"green", n))
        if red:
            baseline_ok = False
            print(out[-1500:])
    if not baseline_ok:
        print(u"PRECHECK_FAILED 基线不绿，这一轮的 CAUGHT 一律不作数")
        return 1

    caught = 0
    last_mtime = 0
    for a in ARMS:
        SNAPSHOT.setdefault(a[2], read(a[2]))
    for arm, desc, path, needle, repl, expect, cell in picked:
        text = read(path)
        hits = text.count(needle)
        if hits != 1:
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm, hits, path))
            continue
        write(path, text.replace(needle, repl))
        if read(path).count(repl) != 1:
            print(u"%s NOT_RUN 落刀后回读不匹配" % arm)
            write(path, text)
            continue
        stamp = os.path.getmtime(path)
        if stamp <= last_mtime:
            os.utime(path, (time.time() + 2, time.time() + 2))
        last_mtime = os.path.getmtime(path)
        red, n, out = run_cell(cell)
        if n == u"?":
            print(u"%s NOT_RUN 变异之后编译不过：%s" % (arm, out.strip().splitlines()[-1][:160]))
            write(path, text)
            continue
        ok = red and red_in(out, expect)
        if ok:
            caught += 1
            print(u"%s CAUGHT %s（Executed=%s）红在：%s" % (arm, desc, n, expect))
        else:
            print(u"%s %s %s —— 期望红在 %s，实得 Executed=%s"
                  % (arm, u"MISMATCH" if red else u"PASSED", desc, expect, n))
            print(out[-1200:])
        write(path, text)
        if read(path) != text:
            print(u"%s RESTORE_DIRTY 还原没回到原文" % arm)
            return 1

    clean = all(read(a[2]) == SNAPSHOT.get(a[2], _MISSING) for a in ARMS)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(picked), u"yes" if clean else u"no"))
    if caught == len(picked) and clean:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
