#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R356 的变异表（第 355 轮 / Round 353）：标签墨不许把胶囊劈成两半。

R356 给 `pillRun` 加了 `mergeInk`：只并"既不接近药丸档、也不接近轨道档"的列（字墨），
并在 `movingHoleRowReading` 里打开。现场读数：行带 51.0…58.0pt（7pt）→ 51.0…75.0pt（24pt），
纵向覆盖 14/48px=29% → 48/48px=100%，判定分布 洞太窄×11,过×13 → 过×24。

· M1006 把两处 `mergeInk: true` 改回 `false`（调用点没接新定义）
  ⇒ `testLabelInkInsideThePillDoesNotNarrowTheHole` 必须红（洞宽回到 22% 的碎片，判"洞太窄"）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r356.py [M1006]
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILM = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests", "MotionFilmstripTests.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

CELL = u"MotionPillRampTests/testLabelInkInsideThePillDoesNotNarrowTheHole"
RED_NAME = u"testLabelInkInsideThePillDoesNotNarrowTheHole"

NEEDLE = (u"        guard let holeA = pillRun(profile: rowA, pillLevel: levels.pill, trackLevel: levels.track,\n"
          u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
          u"                                  mergeInk: true),\n"
          u"              let holeB = pillRun(profile: rowB, pillLevel: levels.pill, trackLevel: levels.track,\n"
          u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
          u"                                  mergeInk: true) else { return nil }")
REPL = NEEDLE.replace(u"mergeInk: true", u"mergeInk: false")

# R361 / BACKLOG 367：表自己声明针（rot 做成上界只有这一条路）。值与 ARMS 里用的是同一份常量。
NEEDLES = {'M1006': [NEEDLE]}

ARMS = [
    ("M1006", u"调用点：两处 mergeInk 改回 false ⇒ 被标签墨劈开的行必须重新判洞太窄",
     FILM,
     u"        guard let holeA = pillRun(profile: rowA, pillLevel: levels.pill, trackLevel: levels.track,\n"
     u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
     u"                                  mergeInk: true),\n"
     u"              let holeB = pillRun(profile: rowB, pillLevel: levels.pill, trackLevel: levels.track,\n"
     u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
     u"                                  mergeInk: true) else { return nil }",
     u"        guard let holeA = pillRun(profile: rowA, pillLevel: levels.pill, trackLevel: levels.track,\n"
     u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
     u"                                  mergeInk: false),\n"
     u"              let holeB = pillRun(profile: rowB, pillLevel: levels.pill, trackLevel: levels.track,\n"
     u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
     u"                                  mergeInk: false) else { return nil }",
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
                                   if u"洞太窄" in line or u"洞宽" in line)[:400]
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


if __name__ == u"__main__":
    main(sys.argv[1:])
