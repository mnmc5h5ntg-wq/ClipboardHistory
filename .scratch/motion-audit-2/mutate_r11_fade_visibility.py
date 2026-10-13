#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R11（热图淡入的可测性 + 说明块的过渡配对 + 冷采样闸门）变异对照：三支。

规矩同前两支：基线必须是**指定那条用例 passed**、红必须是这一条用例的红、
`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash、一支可以改多处。

这一支特别记一句：M49 打的是**尺子自己的闸门**，不是产品。
一条"看不见"的结论如果建立在冷采样上，那它既不能算产品没做，也不能算尺子有极限 ——
所以这个闸门必须会红，否则 R11 那条结论没有根。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
SETTINGS = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"
FILM = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
HEAT = "DailyCopyHeatmapTests"
MOTION = "MotionFilmstripTests"

MUTANTS = [
    # M47：说明块的过渡被摘掉 ⇒ 它又变成整块硬蹦出来，而驱动键还在（"键在、声明没了"也要红）。
    ("M47-guide-transition-removed", HEAT, SETTINGS,
     [(u"                    readingGuide\n                }\n                .transition(MotionCatalog.transition(for: .contentFade))",
       u"                    readingGuide\n                }")],
     "testStatsGuideTransitionIsPairedWithADriver"),

    # M48：驱动键被摘掉 ⇒ 又是一条"代码里有、屏幕上没有"。
    ("M48-guide-driver-removed", HEAT, SETTINGS,
     [(u"        .animation(MotionCatalog.animation(for: .contentFade), value: ledger.counts.isEmpty)",
       u"        // (驱动键被摘掉)")],
     "testStatsGuideTransitionIsPairedWithADriver"),

    # M49：冷采样闸门设成"永远不算热" ⇒ 那条"尺子看不见淡入"的结论必须**当场作废**，
    #      而不是拿一段冷采样继续宣称这是尺子的极限。
    ("M49-warm-gate-unreachable", MOTION, FILM,
     [(u"    static let warmIntervalMilliseconds: Double = 120",
       u"    static let warmIntervalMilliseconds: Double = -1")],
     "testHeatmapFadeIsNotVisibleToThisRuler"),
]


def run(suite, case):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
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
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (suite, case) in out:
        return "ESCAPED"
    if "skipped" in out:
        return "DID-NOT-RUN=skipped"
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
        backup = "/tmp/r11_backup_" + os.path.basename(relative)
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
