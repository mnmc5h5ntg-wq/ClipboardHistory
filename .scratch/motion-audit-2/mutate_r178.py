#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R178 的变异表：R176 欠的那三把刀（M693–M695）。

R176 把 `worst ≤ 120ms` 的绝对锚点改成"要颗数撑着"时，真值表写了、刀没跑（当时显式记成 NOT-RUN）。
这一支把那格账补齐 —— 否则"锚点没删、只是要求样本数"这句话只有纸上证人。

  M693 `worstFrameOutlierTolerance = 1` 改成 999 ⇒ 真卡顿（一批帧超锚点）再也判不红
  M694 `overAnchorCount == 0 { return true }` 改成 `false` ⇒ "worst 超锚点却数到 0 颗"这把矛盾尺被静音
  M695 探针里的 `XCTAssertFalse(...)` 改成 `XCTAssertTrue(...)` ⇒ 接线被反装（扫描那格要红，不是恒真）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r178.py [M693 ...]
退出码：0 = 选中的刀全 CAUGHT 且还原干净；1 = 有刀没下 / 还原后仍红；2 = 臂号不认识。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
TARGET = os.path.join(PKG, "Tests", "ClipboardHistoryAppTests", "FrameIntervalBudgetTests.swift")
PROBE = os.path.join(PKG, "Tests", "ClipboardHistoryAppTests", "UIInteractionProbeTests.swift")
FILTER = "FrameIntervalBudgetTests"
BASELINE_MIN = 5
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M693", TARGET,
     u"static let worstFrameOutlierTolerance = 1",
     u"static let worstFrameOutlierTolerance = 999", "CAUGHT"),
    ("M694", TARGET,
     u"if overAnchorCount == 0 { return true }",
     u"if overAnchorCount == 0 { return false }", "CAUGHT"),
    ("M695", PROBE,
     u"XCTAssertFalse(FrameIntervalBudget.isWorstFrameJank(worstMs: loaded.worst, overAnchorCount: overAnchor)",
     u"XCTAssertTrue(FrameIntervalBudget.isWorstFrameJank(worstMs: loaded.worst, overAnchorCount: overAnchor)", "CAUGHT"),
]


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text):
    open(path, "w", encoding="utf-8").write(text)


def run_filter():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failure", out)
    ran = int(executed[-1][0]) if executed else 0
    names = sorted({m.group(1) for m in
                    re.finditer(r"Test Case '-\[.*\.\w+ (\w+)\]' failed", out)})
    return ran, names, ("error:" in out and ran == 0)


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print(u"ARG_ERROR 不认识这些臂号：%s（认识的是 %s）" % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print(u"ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    original = read(TARGET)
    ran, names, broke = run_filter()
    if ran < BASELINE_MIN or names or broke:
        save(TARGET, original)
        print(u"PRECHECK_FAILED 未落刀时已红或跑不满 %d 格：ran=%d red=%s broke=%s"
              % (BASELINE_MIN, ran, names, broke))
        return 1
    print(u"BASELINE_GREEN ran=%d" % ran)
    caught = 0
    for arm_id, target, old, new, expect in arms:
        text = read(target)
        hits = text.count(old)
        if hits != 1:
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1）—— 刀没下，不许记成 CAUGHT" % (arm_id, hits))
            continue
        save(target, text.replace(old, new))
        ran, names, broke = run_filter()
        save(target, original)
        if broke:
            print(u"%s NOT_RUN 编译崩（刀形不对），不记 CAUGHT" % arm_id)
        elif names and expect == "CAUGHT":
            caught += 1
            print(u"%s CAUGHT 红在：%s（ran=%d）" % (arm_id, ", ".join(names), ran))
        else:
            print(u"%s PASSED 刀等于没下（ran=%d 全绿）" % (arm_id, ran))
    ran, names, broke = run_filter()
    restored = u"yes" if (not names and not broke and ran >= BASELINE_MIN and read(TARGET) == original) else u"no"
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == u"no":
        print(u"RESTORE_FAILED red=%s ran=%d broke=%s" % (names, ran, broke))
    return 0 if caught == len(arms) and restored == u"yes" else 1


if __name__ == "__main__":
    sys.exit(main())
