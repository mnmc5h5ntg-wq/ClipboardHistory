#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R348 的变异表（第 347 轮 / Round 345）：空态淡出与药丸必须是同一个节奏。

R348 把 `HistorySidebarView` 里那格空态淡出从 `contentFade`(0.16) 换成 `FilterPillMotion.slideAnimation`(0.20)
—— 切筛选把列表切空/切回时，内容与药丸是同一个手势的两半，落点差 1–2 格（R328 的 6–7 对 12）。
这一刀把那行换回去：源码形状守卫必须红。

· M1003 把 `.animation(FilterPillMotion.slideAnimation(reduceMotion: shouldReduce), …isEmpty)` 换回 `contentFade`
  ⇒ `testEmptyStateFadeSharesThePillRhythm` 必须红（两条断言都会红：缺正的、出现反的）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r348.py [M1003]
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOB = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                    "Views", "PressableStyle.swift")
VIEW = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp", "Views", "HistorySidebarView.swift")
TOKENS = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "VisualTokens.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIXEL_CELL = u"FilterPillMotionTests/testEmptyStateFadeSharesThePillRhythm"
PURE_CELL = u"FilterPillMotionTests/testEmptyStateFadeSharesThePillRhythm"
CELL = PURE_CELL + u"|" + PIXEL_CELL
# `expect` 用**裸方法名**：失败行打的是 `-[Bundle.Class methodName] : XCTAssert…`，
# 带 `Class/` 前缀的写法在失败行里根本不存在 ⇒ 每一刀都会被判成打空。
PIXEL_RED = u"testEmptyStateFadeSharesThePillRhythm"
PURE_RED = u"testEmptyStateFadeSharesThePillRhythm"

NEEDLE_RHYTHM = u"        .animation(FilterPillMotion.slideAnimation(reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)"
REPL_1003 = u"        .animation(MotionCatalog.animation(for: .contentFade), value: historyStore.filteredEntries.isEmpty)"

ARMS = [
    ("M1003", u"产品：空态淡出换回 contentFade(0.16) ⇒ 与药丸(0.20)不同节奏，源码形状守卫必须红",
     VIEW, NEEDLE_RHYTHM, REPL_1003, PIXEL_RED, PIXEL_CELL),
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
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", out)
    if not executed:
        return (True, u"?", out)   # 一行汇总都没有（单数 `1 test` 也要认） ⇒ 编译没过 / 根本没跑
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
