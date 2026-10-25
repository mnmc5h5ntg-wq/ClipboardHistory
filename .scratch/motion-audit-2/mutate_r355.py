#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R355 的变异表（第 354 轮 / Round 352）：减弱动态下空态淡入不能归零。

R348 把空态淡出的驱动换成了 `FilterPillMotion.slideAnimation`（借药丸的 0.20 节奏），
而那个 helper 在 reduce 下返回 `.linear(duration: 0)` —— 对药丸成立（位置就是内容），
对内容淡入就是一帧硬切。runner 从 R348 起就是这台机器：`empty-state` 本臂只变 36ms/1 帧
（`MOTION_NOT_RUN=witness-snaps-here`），而改前 run 40186459168 同一臂是 3 帧。
R355 把产品改回目录的 `.slider` 动画（reduce 下 0.20 淡入，不归零），并加一条行为判据。

· M1005 把产品那一行改回 `FilterPillMotion.slideAnimation`
  ⇒ `testEmptyStateStillFadesWhenMotionIsReduced` 必须红（注入 reduce 后只变 1 帧）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r355.py [M1005]
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIEW = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp", "Views", "HistorySidebarView.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"

CELL = u"MotionFilmstripTests/testEmptyStateStillFadesWhenMotionIsReduced"
RED_NAME = u"testEmptyStateStillFadesWhenMotionIsReduced"

NEEDLE = u"        .animation(MotionCatalog.animation(for: .slider, reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)"
REPL = u"        .animation(FilterPillMotion.slideAnimation(reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)"

ARMS = [
    ("M1005", u"产品：空态淡出改回 slideAnimation（reduce 下 = .linear(duration: 0)）⇒ reduce 播放必须红",
     VIEW,
     u"        .animation(MotionCatalog.animation(for: .slider, reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)",
     u"        .animation(FilterPillMotion.slideAnimation(reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)",
     RED_NAME, CELL),
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
    u"""『红在这一格』必须能在**同一行**里同时看到那一格的名字与失败字样。"""
    for line in out.splitlines():
        if name in line and (u"error:" in line or u"' failed" in line):
            return True
    return False


def run_cell(filter_name):
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", filter_name])
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", out)
    if not executed:
        return (True, u"?", out)
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
            reading = u" ｜ ".join(line.strip() for line in out.splitlines()
                                   if line.strip().startswith(u"MOTION_REDUCE"))
            print(u"%s CAUGHT %s（Executed=%s）红在：%s" % (arm, desc, n, expect))
            if reading:
                print(u"  %s" % reading)
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
