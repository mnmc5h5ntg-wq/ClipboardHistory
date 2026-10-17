#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R125 的变异表：动效档「声明了却没供电」那把尺的两根牙（M627-M628）。

本轮做的事（U-417）：我用 shell grep 数 `for: .bannerOut` 得到 0 个调用点，差点据此开一条
「这条声明是死的」的账；真去数它是 5 处 —— 产品写的是
`asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，我的模式只认得一种写法。
⇒ 计数换成仓库里一把会红、有真值表的尺（`motionKindCallSites` + 九档地板 >=1）。

两刀（都期望 CAUGHT，打在真值表那一格上，秒级）：
  M627 撤掉词边界的先行断言 => `.bannerOutExtra` 会喂饱 `.bannerOut`
  M628 撤掉「剥注释」=> 注释里提一句就算供电（M407 / M411 那一族：守卫被散文喂饱）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r125.py [M627 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
TRUTH = "testMotionKindCallSitesRulerIsATruthTable"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M627", "撤掉词边界 => 更长的名字会把这一档喂饱",
     '+ "(?![A-Za-z0-9_])"',
     '+ ""',
     "CAUGHT"),
    ("M628", "撤掉剥注释 => 注释里提一句就算供电",
     "        let text = Self.codeOnly(rawText)",
     "        let text = rawText",
     "CAUGHT"),
]


def read():
    with open(HARNESS, encoding="utf-8") as handle:
        return handle.read()


def save(text):
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(text)


def run():
    proc = subprocess.run(["swift", "test", "--filter", "UICaptureTests/" + TRUTH],
                          cwd=ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    verdicts = re.findall(r"Test Case '-\[[^\]]*\b%s\]' (passed|failed|skipped)" % TRUTH, out)
    if not verdicts:
        return ("COMPILE-ERROR" if "error:" in out else "DID-NOT-RUN"), out
    return ("CAUGHT" if verdicts[-1] == "failed" else verdicts[-1].upper()), out


def snippet(out):
    for line in out.splitlines():
        if "XCTAssertEqual failed" in line or "error:" in line:
            return line.strip()[:190]
    return ""


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally, mismatch, not_run = [], {}, 0, 0
    for name, note, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = original.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d => 不注入" % hits))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run()
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = verdict == expect
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        results.append((name, expect, verdict, note,
                        ("对 期望 %s|%s" % (expect, snippet(out))) if ok
                        else ("**不符** 期望 %s 实得 %s|%s" % (expect, verdict, snippet(out)))))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R125 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        print("  %s  exp=%-8s got=%-12s %s %s  %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
