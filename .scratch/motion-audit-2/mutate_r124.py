#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R124 的变异表：盲区名单按机器分键之后，四种关系各自有没有牙（M624–M626）。

本轮做的事（BACKLOG 171）：`darkSidebarTextBlindSpots` 从 R29d 起被当"全局权威"用，
而它量的是 **vibrant 子树 + cacheDisplay 不走合成**这一台机器的行为。runner 上这条判据
判了 13/13、`gone` 那朵红按 R120 的预言落地（run 39025878222）⇒ 名单必须按机器分键。
键只准用**量出来**的事实：`arch / macOS 主次版本 / 帧倍率`（R118 已证明绝对坐标是机器相关的）。
新形状：`sidebarRosterVerdict` 四种关系（未登记 / 一致 / 新盲区 / 登记过的不再反侧），
"没登记的那台"必须红 —— 否则任何一台新机器都会白拿一个绿。

三刀（全部期望 CAUGHT，都打在真值表那一格上，秒级）：
  M624 键里丢掉倍率（恒写 2x）⇒ 真值表那条"Retina 与非 Retina 不许共用一行"红
  M625 未登记改成"当成一致"⇒ 两行 .unkeyed 的期望拿不到（静默通过正是 171 要拦的通道）
  M626 撤掉新盲区那一格（extra 直接落到 gone/clean）⇒ 登记之外的反侧不再被点名

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r124.py [M624 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
TRUTH = "testSidebarRosterVerdictIsATruthTable"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M624", "键里丢掉倍率（恒写 2x）⇒ Retina 与非 Retina 会共用同一行名单",
     '        let scaleText = scale >= 1.75 ? "2x" : (scale <= 1.25 ? "1x" : "other")',
     '        let scaleText = "2x"',
     "CAUGHT"),
    ("M625", "未登记改成「当成一致」⇒ 新机器白拿一个绿（171 要拦的正是这条通道）",
     "        guard let registered = registered else { return .unkeyed }",
     "        guard let registered = registered else { return .clean }",
     "CAUGHT"),
    ("M626", "撤掉「新盲区」那一格 ⇒ 登记之外的反侧不再被点名",
     "        if !extra.isEmpty { return .extra(extra) }",
     "        if false { return .extra(extra) }",
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
            return line.strip()[:200]
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
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run()
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = verdict == expect
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet(out))) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet(out)))))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R124 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        print("  %s  exp=%-8s got=%-12s %s %s  %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
