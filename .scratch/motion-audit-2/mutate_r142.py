#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R142 的变异表：帧间隔那条相对判据的四颗牙（M666-M669）。

R141 的教训照抄到自己身上：一把刀没有靶不算尺没牙（U-467），而"只红一条"必须被读成红（U-466）。
所以这一轮：① 每一刀都红在**不同**的用例上；② harness 沿用 R141 修好的形状
（多编辑一臂、mtime 逐臂递增、落刀后重读盘上内容自证、失败数按 `tests?/failures?` 匹配、
读不到汇总行 = NOT_RUN）。

  M666 预算从 3.0 抬到 100.0（恒真化）⇒ 真值表里"48.1 必须红"那一格要红
  M667 去掉"分母是 0 就无从判定"那道 guard ⇒ 真值表里 XCTAssertNil 那一格要红
  M668 参照从 max(baseline, off) 换成 min ⇒ 真值表里"取 min 会算错"那一格要红
  M669 把三臂读数从 `emit` 换回 `print` ⇒ 读数通道守卫要红
       （那三行 `FPS-` 在 CI 里从来没被收集到过，就是因为它们走的是块缓冲的 stdout）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r142.py [M666 ...]
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
TESTS_DIR = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests")
# 两把刀落在两个文件上（R142 / U-474：那两条纯函数用例被我从探针卷里搬出来过 ——
# 留在原地会让"在屏探针覆盖率"那道闸门数错东西）。所以 ARMS 现在带自己的目标文件。
PROBE = os.path.join(TESTS_DIR, "UIInteractionProbeTests.swift")
BUDGET = os.path.join(TESTS_DIR, "FrameIntervalBudgetTests.swift")
TARGET = BUDGET
FILTER = "FrameIntervalBudgetTests"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M666", BUDGET, [(u"    static let ratio: Double = 3.0",
               u"    static let ratio: Double = 100.0")], "CAUGHT"),
    ("M667", BUDGET, [(u"        guard reference > 0 else { return nil }",
               u"        guard reference >= 0 else { return nil }")], "CAUGHT"),
    ("M668", BUDGET, [(u"        let reference = max(baselineP95, offP95)",
               u"        let reference = min(baselineP95, offP95)")], "CAUGHT"),
    ("M669", PROBE, [(u'        emit("PROBE_FPS 机器=',
                     u'        print("PROBE_FPS 机器=')], "CAUGHT"),
]


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=os.path.join(ROOT, "ClipboardHistory"), env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1).split()[-1].split(".")[-1]
                    for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数 ⇒ 既不算红也不算绿）"]
    return n, (n >= 1 and failures > 0), names


def main():
    want = sys.argv[1:]
    arms = [a for a in ARMS if not want or a[0] in want]
    originals = {path: read(path) for path in (PROBE, BUDGET)}
    clock = [time.time() + 10.0]

    def restore():
        for path, base in originals.items():
            save(path, base, bump=clock[0])
        clock[0] += 10.0

    restore()
    n, red, names = run_suite()
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1

    caught = 0
    for arm_id, target, edits, expect in arms:
        text = read(target)
        ok = True
        for old, new in edits:
            if text.count(old) != 1:
                print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:40]))
                ok = False
                break
            text = text.replace(old, new)
        if not ok:
            continue
        save(target, text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != text:
            restore()
            print("%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names = run_suite()
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            print("%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif red:
            caught += 1
            print("%s CAUGHT 红在（Executed=%d）：%s" % (arm_id, n, ", ".join(names)))
        else:
            print("%s PASSED 刀等于没下（Executed=%d，全绿）" % (arm_id, n))

    n, red, names = run_suite()
    restored = "yes" if (not red and n >= 1
                         and all(read(q) == base for q, base in originals.items())) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s" % (n, ", ".join(names)))
    return 0 if caught == len(arms) and restored == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
