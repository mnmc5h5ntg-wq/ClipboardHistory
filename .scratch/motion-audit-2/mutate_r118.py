#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R118 的变异表：机器无关的行带那两格牙（M612–M613）。

本轮做的事：R116 那条对账守卫在 runner 上第一次跑就红 ——
`SIDEBAR_ROSTER_RECT 台账=60..252 树给=342..534 上界差=282.0pt`，
也就是**同一份代码、同一个 720×540 帧，整条侧栏在 runner 上往下挪了 282pt**（行高、行数一点没变）。
⇒ 绝对 y 是机器相关的，不能当契约：判据改成吃 `sidebarTextBands`（x 来自台账、y 来自树），
对账守卫改成比**高度与行数**，偏移只报不判。

两刀：
  M612 把台账矩形高度改回五行时代的 154 ⇒ 期望 **CAUGHT**（钉在"尺盖住的范围对不对"）
  M613 让行带助手返回空数组 ⇒ 期望 **CAUGHT**
       —— 逐行求和之后 `TEXT_SIDE` 全为 0 ⇒ 反侧名单空、而 vibrant 子树仍是 13 条 ⇒ 等式必须红。
       这一格证明"吃行带"不是装饰：把它摘掉，盲区名单会静默变成一份空名单。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r118.py [M612 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import subprocess
import sys

SWIFT_ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(SWIFT_ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
GUARD = "UICaptureTests/testSettingsSidebarRosterRectCoversEveryRow"
ROSTER = "UICaptureTests/testDarkSettingsSidebarTextIsACountedBlindSpot"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M612", "台账矩形高度改回 154（五行时代）⇒ 高度对账必须红",
     "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 192)",
     "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 154)",
     GUARD, "CAUGHT"),
    ("M613", "行带助手返回空 ⇒ 盲区名单静默变空，等式必须红",
     "        return sidebarRowRects(in: host, column: settingsSidebarIconColumn)\n"
     "            .map { CGRect(x: x, y: $0.minY, width: w, height: $0.height) }",
     "        return [CGRect]()\n"
     "        // 原式：sidebarRowRects(in:column:).map",
     ROSTER, "CAUGHT"),
]


def read():
    with open(HARNESS, encoding="utf-8") as handle:
        return handle.read()


def save(text):
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(text)


def run(target):
    proc = subprocess.run(["swift", "test", "--filter", target], cwd=SWIFT_ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if "cannot find" in out or "No such module" in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "SURVIVED", out
    return "CAUGHT", out


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally = [], {}
    mismatch = not_run = 0
    for name, note, needle, replacement, target, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = original.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            tally["DID-NOT-RUN"] = tally.get("DID-NOT-RUN", 0) + 1
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run(target)
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        snippet = ""
        for line in out.splitlines():
            if "XCTAssert" in line:
                snippet = line.strip()[:180]
                break
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R118 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
