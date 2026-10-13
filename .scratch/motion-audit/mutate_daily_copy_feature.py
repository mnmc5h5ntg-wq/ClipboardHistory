#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段一（每日复制热图）变异对照：八支变异各钉一条判据。

与 R6 那份同一套规矩（基线不绿不注入 / 红必须是这一条用例的红 / `cp` 逐文件还原 /
子进程摘 SDKROOT / skip 单独分类），差别只在这轮的用例都不门控 —— 不开任何环境变量，
所以 `DID-NOT-RUN=skipped` 那一支在这里不该出现，出现了就是脚本自己坏了。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
SUITE = "DailyCopyHeatmapTests"

MUTANTS = [
    # M25：把计数挪到入库之后 ⇒ 去重/晋升那两条早退会把真实发生的复制从统计里吞掉。
    ("M25-count-after-insert",
     "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift",
     u"""        dailyCopyLedger?.recordCopy(at: timestamp)

        if promoteExistingEntryIfNeeded(for: intakeEntry, timestamp: timestamp) {""",
     u"""        if promoteExistingEntryIfNeeded(for: intakeEntry, timestamp: timestamp) {""",
     "testCopyingThroughTheStoreGrowsTodaysCell"),

    ("M25b-count-after-insert-placed-late",
     "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift",
     u"""        dailyCopyLedger?.recordCopy(at: timestamp)

        if promoteExistingEntryIfNeeded""",
     u"""        if promoteExistingEntryIfNeeded""",
     "testCopyingThroughTheStoreGrowsTodaysCell"),

    # M26：回填不再只看"空不空" ⇒ 已有账本被 500 条上限的存档倒灌覆盖。
    ("M26-backfill-overwrites",
     "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift",
     u"        guard counts.isEmpty, !dates.isEmpty else { return }",
     u"        guard !dates.isEmpty else { return }",
     "testBackfillOnlyFillsAnEmptyLedger"),

    # M27：退出时不落盘 ⇒ 去抖窗口里的计数被 SIGTERM 掐掉。
    ("M27-flush-is-a-noop",
     "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift",
     u"""    func flushPendingSaves() {
        guard let snapshot = pendingSnapshot else { return }""",
     u"""    func flushPendingSaves() {
        guard false, let snapshot = pendingSnapshot else { return }""",
     "testRecordCopyDoesNotTouchTheDiskOnTheCallingPath"),

    # M28：分档退回绝对阈值 ⇒ 轻度用户整张图都是灰的（读不出自己的节奏）。
    ("M28-absolute-buckets",
     "Sources/ClipboardHistoryApp/Utilities/DailyCopyHeatPolicy.swift",
     u"""        guard count > 0 else { return 0 }
        return min(4, 1 + edges.filter { count >= $0 }.count)""",
     u"""        guard count > 0 else { return 0 }
        return min(4, 1 + [6, 14, 26, 50].filter { count >= $0 }.count)""",
     "testBucketLadderIsRelativeMonotonicAndBounded"),

    # M29：未来那几格画成"没有记录" ⇒ 谎报"那天你一次都没复制"。
    ("M29-future-cells-drawn",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift",
     u"        if cell.dayKey == nil || cell.isFuture {",
     u"        if cell.dayKey == nil {",
     "testHeatmapReadsTheTokenAuthors"),

    # M30：Store 内部默认建账本 ⇒ 每条不注入的测试都会去写用户的数据目录。
    ("M30-store-builds-ledger",
     "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift",
     u"        dailyCopyLedger: DailyCopyLedger? = nil,",
     u"        dailyCopyLedger: DailyCopyLedger? = DailyCopyLedger(),",
     "testStatsCategoryIsWired"),

    # M31：回填当场排写盘 ⇒ 构造期写用户文件（D-002 那条红线的同族）。
    ("M31-backfill-writes-now",
     "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift",
     u"""        counts = Self.pruned(counts: counts, now: now(), calendar: calendar, retentionDays: Self.retentionDays)
        pendingSnapshot = counts""",
     u"""        counts = Self.pruned(counts: counts, now: now(), calendar: calendar, retentionDays: Self.retentionDays)
        scheduleSave()""",
     "testBackfillDoesNotWriteDuringConstruction"),

    # M32：把去抖闭包写回 @MainActor 方法里 ⇒ 第一次到期就 SIGTRAP。
    #      这一支的"红"是**进程崩掉**，不是断言失败 —— 分类器必须认得这个形状，
    #      否则一次真崩溃会被记成"变异没被抓到"。
    ("M32-mainactor-closure-trap",
     "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift",
     u"""        let workItem = Self.makeSaveWorkItem(snapshot: snapshot, url: fileURL, box: failureBox)""",
     u"""        let url = fileURL
        let box = failureBox
        let workItem = DispatchWorkItem {
            try? Self.write(snapshot, to: url)
            box.message = nil
        }""",
     "testDebouncedWriteFiresWithoutMainActorTrap"),
]


def run(case):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["swift", "test", "--filter", "%s/%s" % (SUITE, case)],
                            cwd=SWIFT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return out


def classify(out, case):
    if "Build complete" not in out:
        return "DID-NOT-RUN=build-failed"
    if "tests skipped" in out and "Executed 1 test" in out:
        return "DID-NOT-RUN=skipped"
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' failed" % (SUITE, case) in out:
        return "CAUGHT"
    if "Exited with unexpected signal code" in out:
        # 进程被 SIGTRAP 收掉 = 这条路径确实跑了，而且跑出了运行时错误。
        return "CAUGHT=crash"
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (SUITE, case) in out:
        return "ESCAPED"
    return "DID-NOT-RUN=case-not-found"


def main():
    baseline = run("testQuickPickEmptyMessageTruthTable")
    if "0 failures" not in baseline:
        print("BASELINE=NOT-GREEN —— 不注入")
        print(baseline[-1200:])
        return 2
    print("BASELINE=green")

    results = []
    for name, relative, old, new, case in MUTANTS:
        path = os.path.join(SWIFT, relative)
        with io.open(path, encoding="utf-8") as fh:
            original = fh.read()
        if original.count(old) != 1:
            print("%s: DID-NOT-RUN=anchor-count=%d" % (name, original.count(old)))
            results.append((name, "DID-NOT-RUN"))
            continue
        backup = "/tmp/r7_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new, 1))
        verdict = classify(run(case), case)
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
