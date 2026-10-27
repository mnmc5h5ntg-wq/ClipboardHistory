#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R116 的变异表：列级矩形与视图树行带那条对账的两格牙（M610–M611）。

本轮做的事：把 BACKLOG 169 结案 —— 台账里 `settingsSidebarTextColumn` 的 y 带从
**五行时代**的 96..250 换成实测行带 60..252，并新增 `testSettingsSidebarRosterRectCoversEveryRow`
把"矩形"钉在"树给的行带"上（U-383 那一族的钉子：读数是绿的，量的可能已经不是同一块东西）。

两刀：
  M610 把矩形改回 y 96 h 154（就是本轮改掉的那一版）⇒ 期望 **CAUGHT**
       —— 这一刀钉的是"这条守卫真的会为一行没盖住而红"，不是恒真。
  M611 让 `sidebarRowRects` 丢掉最后一行 ⇒ 期望 **CAUGHT**
       —— 模拟"产品加了一行而尺没跟着走"：数量守卫与下界差必须一起红。
       它同时是 M610 的对照：M610 是**矩形**过期，M611 是**树**少给一行。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r116.py [M610 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import subprocess
import sys

SWIFT_ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(SWIFT_ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
TARGET = "UICaptureTests/testSettingsSidebarRosterRectCoversEveryRow"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M610", "矩形改回本轮之前的 y 96 h 154 ⇒ 第一行又不在尺里",
     "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 224)",
     "static let settingsSidebarTextColumn = CGRect(x: 40, y: 96, width: 102, height: 154)", "CAUGHT"),
    ("M611", "树只给前五行 ⇒ 数量与下界差必须一起红",
     "            kept.append(r)\n        }\n        return kept",
     "            kept.append(r)\n        }\n        return Array(kept.dropLast())", "CAUGHT"),
]


def read():
    with open(HARNESS, encoding="utf-8") as handle:
        return handle.read()


def save(text):
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(text)


def run():
    proc = subprocess.run(["swift", "test", "--filter", TARGET], cwd=SWIFT_ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if "cannot find" in out or "error: cannot" in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "SURVIVED", out
    for line in out.splitlines():
        if "XCTAssert" in line:
            return "CAUGHT", out
    return "CAUGHT", out


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally = [], {}
    mismatch = not_run = 0
    for name, note, needle, replacement, expect in ARMS:
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
        verdict, out = run()
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
    print("\n=== R116 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
