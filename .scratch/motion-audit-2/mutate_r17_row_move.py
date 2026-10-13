#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R17（顶到最前从整表硬刷新升成一次 moveRow）变异对照：三支。

三支各打一层：M70 打纯函数（不再识别"一行挪位"）、M71 打接线（算出来了没人执行）、
M72 打 `isNoop`（把移动当成"没变化"，于是界面永远留在旧顺序 —— 最安静的一种坏法）。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
DIFF = "QuickPickRowDiffTests"
DIFFFILE = "Tests/ClipboardHistoryAppTests/QuickPickRowDiffTests.swift"
PLANNER = "Sources/ClipboardHistoryApp/Utilities/QuickPickRowDiff.swift"
CONTROLLER = "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
CAT = "QuickPickRowDiffTests"
CASE = "testDetailEmptyContentSwapHasTransitionsOnBothArms"

CONTENT_ARM = (u"            selectedEntryView(entry)\n"
               u"                .transition(MotionCatalog.transition(for: .contentFade))")

MUTANTS = [
    # M70：`singleMove` 一律返回 nil ⇒ 顶到最前又回到整表硬刷新。
    ("M70-single-move-always-nil", DIFF, PLANNER,
     [(u"        guard old.count == new.count, !old.isEmpty else { return nil }",
       u"        guard false else { return nil }\n"
       u"        guard old.count == new.count, !old.isEmpty else { return nil }")],
     "testSingleRowPromotionBecomesAMoveNotAHardReload"),

    # M71：计划算出了移动，控制器不执行 ⇒ "载荷绿、消费侧坏"。
    ("M71-controller-drops-the-move", CAT, CONTROLLER,
     [(u"                table.moveRow(at: move.from, to: move.to)\n", u"")],
     "testRebuildRowsIsWiredToTheAnimatedAPI"),

    # M72：`isNoop` 不看 moves ⇒ 控制器在 `guard !plan.isNoop` 那里早退，行永远不挪。
    ("M72-isNoop-ignores-moves", DIFF, PLANNER,
     [(u"                && moves.isEmpty && !needsFullReload",
       u"                && !needsFullReload")],
     "testSingleRowPromotionBecomesAMoveNotAHardReload"),
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
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (suite, case) in out:
        return "ESCAPED"
    if "skipped" in out:
        return "DID-NOT-RUN=skipped"
    return "DID-NOT-RUN=case-not-found"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    selected = [m for m in MUTANTS if not only or only in m[0]]
    if not selected:
        print("没有匹配的变异：%s" % only)
        return 2
    # 元组形状：(name, suite, relative, edits, case) —— 索引 0..4。
    # 上一版按 0..3 取，把"edits 列表"当成用例名去跑，于是基线永远 NOT-GREEN
    # （崩在注入之前，没污染任何文件 —— 这一族的"早退比晚退好"）。
    first = selected[0]
    baseline = run(first[1], first[4])
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (first[1], first[4]) not in baseline:
        print("BASELINE=NOT-GREEN(%s/%s) —— 不注入" % (first[1], first[4]))
        print(baseline[-1200:])
        return 2
    print("BASELINE=green %s/%s" % (first[1], first[4]))
    results = []
    for name, suite, relative, edits, case in selected:
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
        backup = "/tmp/r17_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        verdict = classify(suite, case, run(suite, case))
        print("%s: %s" % (name, verdict))
        results.append((name, verdict))
        shutil.copy2(backup, path)
        with io.open(path, encoding="utf-8") as fh:
            if fh.read() != original:
                print("还原失败：%s" % relative)
                return 3
    bad = [n for n, v in results if v not in ("CAUGHT", "CAUGHT=crash")]
    print("MUTATION_SUMMARY caught=%d/%d %s"
          % (len(results) - len(bad), len(results), ("残留: " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
