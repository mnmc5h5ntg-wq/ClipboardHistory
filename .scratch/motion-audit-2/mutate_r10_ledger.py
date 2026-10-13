#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R10（写盘失败的发布通道 + 探针名单从产品推导）变异对照：四支。

规矩同 `mutate_r9_heatmap.py`：基线必须是**指定那条用例 passed**（不是"0 failures"）、
红必须是这一条用例的红、`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash。
差别只有一条：这一轮的被测点跨两个套件，所以每支自带 suite 字段。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
LEDGER = "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift"
PROBE = "Tests/ClipboardHistoryAppTests/OffscreenSymbolInkProbeTests.swift"
HEAT = "DailyCopyHeatmapTests"
INK = "OffscreenSymbolInkProbeTests"

# (名字, 套件, 文件, [(旧, 新)...], 用例)
MUTANTS = [
    # M43：不排"回头看一眼盒子"那件事 ⇒ 失败值还在盒子里，但没人让它上屏。
    ("M43-no-visibility-check", HEAT, LEDGER,
     [(u"        saveQueue.asyncAfter(deadline: .now() + debounceSeconds, execute: workItem)\n        scheduleVisibilityCheck()",
       u"        saveQueue.asyncAfter(deadline: .now() + debounceSeconds, execute: workItem)")],
     "testWriteFailureBecomesVisibleWithoutAnotherCopy"),

    # M44：退出路径不自己同步 ⇒ flush 失败仍然一言不发。
    #      锚点只取"flush 里那一行 + 收尾大括号"：`syncWriteFailure` 在文件里出现两次
    #      （另一次是 work item 里的 `self?.syncWriteFailure() }`，同一行、不同缩进），
    #      锚点不唯一的话这一支会改到别处去，报出来的红就不是它该红的那条。
    ("M44-flush-does-not-sync", HEAT, LEDGER,
     [(u"\n        syncWriteFailure()\n    }", u"\n    }")],
     "testFlushReportsAFailedWrite"),

    # M45：拿掉"值变了才发"那句比较 ⇒ 每复制一条都为一条不存在的错误重排一次设置页。
    ("M45-always-publish", HEAT, LEDGER,
     [(u"        let message = failureBox.message\n"
       u"        if message != lastWriteError {\n"
       u"            lastWriteError = message\n"
       u"        }",
       u"        lastWriteError = failureBox.message")],
     "testASuccessfulWriteDoesNotRepublish"),

    # M46：探针名单退回手抄字面量（少 chart.bar、多一个早就不用的 sparkles）。
    ("M46-probe-list-hand-copied", INK, PROBE,
     [(u"    private static var symbolNames: [String] { SettingsCategory.allCases.map(\\.icon) }",
       u"    private static var symbolNames: [String] {[\"command\", \"gearshape\", \"hand.raised\", \"sparkles\", \"folder\"]}")],
     "testProbeCoversEveryCategoryIcon"),
]


def run(suite, case):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["swift", "test", "--filter", "%s/%s" % (suite, case)],
                            cwd=SWIFT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return out


def classify(suite, case, out):
    if "Build complete" not in out:
        return "DID-NOT-RUN=build-failed"
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' failed" % (suite, case) in out:
        return "CAUGHT"
    if "Exited with unexpected signal code" in out:
        return "CAUGHT=crash"
    if "tests skipped" in out and "Executed 1 test" in out:
        return "DID-NOT-RUN=skipped"
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (suite, case) in out:
        return "ESCAPED"
    return "DID-NOT-RUN=case-not-found"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    first = MUTANTS[0]
    baseline = run(first[1], first[4])
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (first[1], first[4]) not in baseline:
        print("BASELINE=NOT-GREEN(%s/%s) —— 不注入" % (first[1], first[4]))
        print(baseline[-1500:])
        return 2
    print("BASELINE=green %s/%s" % (first[1], first[4]))

    results = []
    for name, suite, relative, edits, case in MUTANTS:
        if only and only not in name:
            continue
        path = os.path.join(SWIFT, relative)
        with io.open(path, encoding="utf-8") as fh:
            original = fh.read()
        mutated = original
        anchors = []
        for old, new in edits:
            anchors.append("%d" % original.count(old))
            if original.count(old) == 1:
                mutated = mutated.replace(old, new, 1)
        if mutated == original or any(a != "1" for a in anchors):
            print("%s: DID-NOT-RUN=anchor-count=%s" % (name, "/".join(anchors)))
            results.append((name, "DID-NOT-RUN"))
            continue
        backup = "/tmp/r10_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        verdict = classify(suite, case, run(suite, case))
        print("%s: %s" % (name, verdict))
        results.append((name, verdict))
        shutil.copy2(backup, path)
        with io.open(path, encoding="utf-8") as fh:
            if fh.read() != original:
                print("还原失败：%s 与注入前不一致，停止" % relative)
                return 3

    bad = [n for n, v in results if v not in ("CAUGHT", "CAUGHT=crash")]
    print("MUTATION_SUMMARY caught=%d/%d %s"
          % (len(results) - len(bad), len(results), ("残留: " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
