#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R120 的变异表：能力闸门改吃侧栏之后，两格牙（M614–M615）。

本轮做的事：R118 的 CI 读数（run 39023798233）暴露了一件事 ——
runner 上侧栏那一列**读得到墨、而且在期望侧**（`TEXT_SIDE settings-general dark 亮侧=1503 暗侧=0`），
可同跑的内容区是 0 墨，而旧闸门写的是 `if contentInkTotal == 0 { skip }`
⇒ **整条守卫在 runner 上被 skip 掩盖**：名单在那台机器上根本不成立，这条真信息没人看见（BACKLOG 171）。
闸门因此改成吃**侧栏自己**的墨（`sidebarInkTotal`），内容区那个数降级成"分辨环境还是尺"的附注。

两刀（期望不是"红"，而是"跑没跑" —— 闸门坏了的表现就是它悄悄 skip）：
  M614 把内容区矩形挪到帧内空白 ⇒ 期望 **PASSED**
       （旧写法在这里会变成 SKIPPED；这一刀证明闸门不再被内容区牵着走）
  M615 把侧栏文字列的 x 带挪进分栏阴影那条无内容带 ⇒ 期望 **SKIPPED**
       （新闸门必须自己认怂并报 NOT_RUN，而不是拿一份空名单冒充"13/13 通过"）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r120.py [M614 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

SWIFT_ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(SWIFT_ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
TEST = "testDarkSettingsSidebarTextIsACountedBlindSpot"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M614", "内容区矩形挪到帧内空白 ⇒ 闸门不许再被它牵着 skip",
     "static let settingsContentPane = CGRect(x: 160, y: 70, width: 400, height: 200)",
     "static let settingsContentPane = CGRect(x: 700, y: 520, width: 8, height: 8)",
     "PASSED"),
    ("M615", "侧栏文字列的 x 带挪进分栏阴影（148..160，实测无内容）⇒ 新闸门必须自己报未运行",
     "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 192)",
     "static let settingsSidebarTextColumn = CGRect(x: 152, y: 60, width: 6, height: 192)",
     "SKIPPED"),
]


def read():
    with open(HARNESS, encoding="utf-8") as handle:
        return handle.read()


def save(text):
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(text)


def run():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=SWIFT_ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    verdicts = re.findall(r"Test Case '-\[[^\]]*\b%s\]' (passed|failed|skipped)" % TEST, out)
    if not verdicts:
        return "DID-NOT-RUN", out
    verdict = "CAUGHT" if verdicts[-1] == "failed" else verdicts[-1].upper()
    return verdict, out


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
            if "TEXT_SIDE_CAPABILITY" in line or "TEXT_SIDE_NOT_RUN all" in line:
                snippet = line.strip()[:170]
                break
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R120 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
