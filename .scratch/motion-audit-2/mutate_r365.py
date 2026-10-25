#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R365 的变异表（第 364 轮 / Round 362）：384 的覆盖地板（两机 100%）。

R365 在胶片里加了一条地板：取用带至少盖住候选纵向跨度的 90%（本机 48/48、runner 24/24）。
把"并墨"关掉（M1009）时它掉到 29%（14/48）⇒ `testFilterPillRampIsMonotone` 必须红。
（M1006 已用同一刀钉过行读数那一格；这一刀钉的是**胶片里的覆盖地板**，两个不同判据。）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r365.py [M1009]
"""
import os, re, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILM = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests", "MotionFilmstripTests.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
CELL = u"MotionFilmstripTests/testFilterPillRampIsMonotone"
RED = u"testFilterPillRampIsMonotone"
NEEDLE = (u"        guard let holeA = pillRun(profile: rowA, pillLevel: levels.pill, trackLevel: levels.track,\n"
          u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
          u"                                  mergeInk: true),\n"
          u"              let holeB = pillRun(profile: rowB, pillLevel: levels.pill, trackLevel: levels.track,\n"
          u"                                  delta: delta, extent: extent, minPillPixels: minHolePixels,\n"
          u"                                  mergeInk: true) else { return nil }")
REPL = NEEDLE.replace(u"mergeInk: true", u"mergeInk: false")
ARMS = [("M1009", u"产品尺：并墨关掉 ⇒ 纵向覆盖掉到 29%，胶片覆盖地板必须红", FILM, NEEDLE, REPL, RED, CELL)]
S = {}
def sh(cmd):
    p = subprocess.run(cmd, cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def red_in(out, name):
    return any(name in l and (u"error:" in l or u"' failed" in l) for l in out.splitlines())
def run(cell):
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", cell])
    ex = re.findall(r"Executed (\d+) tests?, with (\d+) failures?", out)
    if not ex: return (True, u"?", out)
    n, f = ex[-1]
    return (int(f) > 0 or "Test Suite 'Selected tests' failed" in out, n, out)
def main(argv):
    picked = [a for a in ARMS if not argv or a[0] in argv]
    if not picked:
        print(u"ARG_ERROR"); return 2
    ok = True
    for cell in sorted({a[6] for a in picked}):
        red, n, out = run(cell)
        print(u"BASELINE %s %s Executed=%s" % (cell, u"RED" if red else u"green", n))
        if red: ok = False; print(out[-1500:])
    if not ok: print(u"PRECHECK_FAILED"); return 1
    caught = 0; last = 0
    for a in ARMS: S.setdefault(a[2], rd(a[2]))
    for arm, desc, path, needle, repl, expect, cell in picked:
        text = rd(path)
        if text.count(needle) != 1:
            print(u"%s NOT_RUN 命中=%d" % (arm, text.count(needle))); continue
        wr(path, text.replace(needle, repl))
        if rd(path).count(repl) != 1:
            print(u"%s NOT_RUN 回读不匹配" % arm); wr(path, text); continue
        st = os.path.getmtime(path)
        if st <= last: os.utime(path, (time.time()+2, time.time()+2))
        last = os.path.getmtime(path)
        red, n, out = run(cell)
        if n == u"?":
            print(u"%s NOT_RUN 编译不过：%s" % (arm, out.strip().splitlines()[-1][:140])); wr(path, text); continue
        if red and red_in(out, expect):
            caught += 1
            reading = u" ｜ ".join(l.strip() for l in out.splitlines() if u"纵向覆盖" in l or u"取用带只盖住" in l)[:400]
            print(u"%s CAUGHT %s（Executed=%s）" % (arm, desc, n))
            if reading: print(u"  %s" % reading)
        else:
            print(u"%s %s（Executed=%s）" % (arm, u"MISMATCH" if red else u"PASSED", n)); print(out[-800:])
        wr(path, text)
        if rd(path) != text: print(u"%s RESTORE_DIRTY" % arm); return 1
    clean = all(rd(a[2]) == S.get(a[2], object()) for a in ARMS)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(picked), u"yes" if clean else u"no"))
    return 0 if caught == len(picked) and clean else 1
if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
