#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R172 的变异表：R171 欠的那两把刀 + 上限那把（M690–M692）。

三把都打在 `ArchiveReloadWait.outcome` / `maxPolls` 这两个**决定要不要继续等**的符号上 ——
R171 我把固定 sleep 换成有界轮询时，真值表写了但刀没跑（当时显式记成 NOT-RUN）。
这一支把那格账补齐，否则"修掉了成因"这句话只有一半证人。

  M690 `reloaded == seeded` 改成 `>=` ⇒ "读到比预期更多的库"会被当成落地（那其实是读到了别的库）
  M691 `elapsed >= timeout` 改成 `>` ⇒ 边界那一拍永远多等，上限形同虚设
  M692 `maxPolls = 60` 改成 100000 ⇒ 一颗永不落地的快照会把这一格挂到 CI 超时（比红更坏）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r172.py [M690 ...]
退出码：0 = 选中的刀全 CAUGHT 且还原干净；1 = 有刀没下 / 还原后仍红；2 = 臂号不认识。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
TARGET = os.path.join(PKG, "Tests", "ClipboardHistoryAppTests", "CapturePathWriteBudgetTests.swift")
FILTER = "CapturePathWriteBudgetTests"
BASELINE_MIN = 6
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M690", TARGET,
     u"if reloaded == seeded { return landed }",
     u"if reloaded >= seeded { return landed }", "CAUGHT"),
    ("M691", TARGET,
     u"return elapsed >= timeout ? timedOut : keepPolling",
     u"return elapsed > timeout ? timedOut : keepPolling", "CAUGHT"),
    ("M692", TARGET,
     u"static let maxPolls = 60",
     u"static let maxPolls = 100000", "CAUGHT"),
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
