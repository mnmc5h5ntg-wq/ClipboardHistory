#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R16（详情区空 ↔ 内容两臂成对 + 供电键）变异对照：三支。

这一轮的像素判据今天判不了（双向 A/B 两臂读数相同 ⇒ 尺子看不见这条交叉淡），
所以判据是**结构**的：两臂成对 + 容器按"有没有选中"供电 + 不许按"是哪一条"供电。
三支变异各打其中一条。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
DETAIL = "Sources/ClipboardHistoryApp/Views/DetailView.swift"
CAT = "MotionCatalogTests"
CASE = "testDetailEmptyContentSwapHasTransitionsOnBothArms"

CONTENT_ARM = (u"            selectedEntryView(entry)\n"
               u"                .transition(MotionCatalog.transition(for: .contentFade))")

MUTANTS = [
    # M67：内容臂的过渡摘掉 ⇒ 回到"只有一臂在演"，也就是本轮修之前的原样。
    ("M67-content-arm-unpaired", CAT, DETAIL,
     [(CONTENT_ARM, u"            selectedEntryView(entry)")],
     CASE),

    # M68：供电键换成"选中的是哪一条" ⇒ 每次方向键翻记录都整块淡一遍（D-055 M4 的负债）。
    ("M68-driver-key-becomes-entry-id", CAT, DETAIL,
     [(u"                   value: historyStore.selectedEntry == nil)",
       u"                   value: historyStore.selectedEntry?.id)")],
     CASE),

    # M69：整条 `.animation` 摘掉 ⇒ 两臂的过渡变成不执行的声明。
    ("M69-driver-removed", CAT, DETAIL,
     [(u"        .animation(MotionCatalog.animation(for: .contentFade),\n"
       u"                   value: historyStore.selectedEntry == nil)\n", u"")],
     CASE),
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
        backup = "/tmp/r16_backup_" + os.path.basename(relative)
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
