#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R358 的变异表（第 357 轮 / Round 355）：墨量那颗只印不判（387①）。

R358 把 `appearanceDependenceVerdict` 的判词收回到两颗面积尺（首末面积 ∪ 动过并集），
墨量差仍逐颗印、仍有全局方向行，但**不进 max**：它带一个色档级系统偏移
（本机 11/11、runner 11/11 亮臂更大；偏移大小随机器走，runner 两跑自己翻一格）。

· M1007 把墨量差塞回 max（恢复 R326 的形状）
  ⇒ `testAppearanceDependenceVerdictWordsAndBoundaries` 必须红（墨量抬判定的那两格）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r358.py [M1007]
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

CELL = u"MotionPillRampTests/testAppearanceDependenceVerdictWordsAndBoundaries"
RED_NAME = u"testAppearanceDependenceVerdictWordsAndBoundaries"

NEEDLE = (u"        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),\n"
          u"                            Self.relativeDifference(unionDark, unionLight))")
REPL = (u"        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),\n"
        u"                            Self.relativeDifference(unionDark, unionLight),\n"
        u"                            Self.relativeDifference(inkDark, inkLight))")

ARMS = [
    ("M1007", u"判词：把墨量差塞回 max（恢复 R326）⇒ 墨量抬判定的两格必须红",
     FILM,
     u"        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),\n"
     u"                            Self.relativeDifference(unionDark, unionLight))",
     u"        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),\n"
     u"                            Self.relativeDifference(unionDark, unionLight),\n"
     u"                            Self.relativeDifference(inkDark, inkLight))",
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


if __name__ == u"__main__":
    main(sys.argv[1:])
