#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R142 的变异表：帧间隔那条相对判据的牙（M666-M669），R143 审查轮补了名册的两颗（M673-M674）。

R141 的教训照抄到自己身上：一把刀没有靶不算尺没牙（U-467），而"只红一条"必须被读成红（U-466）。
所以这一轮：① 每一刀都红在**不同**的用例上；② harness 沿用 R141 修好的形状
（多编辑一臂、mtime 逐臂递增、落刀后重读盘上内容自证、失败数按 `tests?/failures?` 匹配、
读不到汇总行 = NOT_RUN）。

  M666 预算从 3.0 抬到 100.0（恒真化）⇒ 真值表里"48.1 必须红"那一格要红
  M667 去掉"分母是 0 就无从判定"那道 guard ⇒ 真值表里 XCTAssertNil 那一格要红
  M668 参照从 max(baseline, off) 换成 min ⇒ 真值表里"取 min 会算错"那一格要红
  M669 把三臂读数从 `emit` 换回 `print` ⇒ 读数通道守卫要红
       （R143 更正：`swift test … > /tmp/ui.log 2>&1` 两条通道都进同一个文件，
         真正的成因是 `print` 的**块缓冲** + 没有任何步骤去 grep 那些行，不是"通道没收集"。）
  —— 以下两把是 R143 审查轮补的：R142 的台账写"三臂 + 比值 + 机器键一律走 emit"，
     而当时只有新增那一行走成了 emit，三行 `FPS-` 原地没动，守卫照绿（U-480）。
  M673 把 `FPS-BASELINE` 那一行写回 `print` ⇒ 名册里冒出一个未登记的标记 ⇒ 红
  M674 把名册里的一条（`RINGVIEWS`）转成 `emit` ⇒ 登记过期 ⇒ 红
       （两把一起才有牙：只挡新写法的话，"退了旧登记却忘了改名册"永远绿。）

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
    # R143 补的两把：读数名册必须**两个方向**都有牙（只挡"新写法"而不挡"旧登记过期"，
    # 就还是 R142 那个形状 —— 台账说全改了，代码只改了一行，而守卫照绿）。
    ("M673", PROBE, [(u'        emit("FPS-BASELINE n=',
                     u'        print("FPS-BASELINE n=')], "CAUGHT"),
    # R383 退役 M674：R303 把这条读数搬进 `emit` 之后，「把 print 转成 emit」这个坏法就是现状；
# 同义坏法试过**改名**（RINGVIEWS → RINGVIEWS 总量）——实测 PASSED：名册只按「每文件条数 +
# 通道」判，不按「登记的标记是否还出现」判。⇒ 这一刀今天没有对象，退役并点名：
# 未登记的 stdout 由 M673 那道方向继续钉；「登记过期」这一格今天确实没有牙，写进 BACKLOG 367 追记。
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
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1).split()[-1].split(".")[-1]
                    for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数 ⇒ 既不算红也不算绿）"]
    return n, (n >= 1 and failures > 0), names


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        # 打错一个臂号就会得到 `CAUGHT=0/0, RESTORE_CLEAN=yes` 与退出码 0 ——
        # 一把刀都没下也算过关（R143 审查轮 #1）。未知名字必须是硬错。
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）" % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print("ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
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
