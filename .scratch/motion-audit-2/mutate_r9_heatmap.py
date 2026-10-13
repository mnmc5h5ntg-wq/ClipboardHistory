#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R9（阶段二第 1 轮 · 热图自检）变异对照：八支各钉一条判据。

规矩沿用 `.scratch/motion-audit/mutate_daily_copy_feature.py`（基线不绿不注入 /
红必须是**这一条用例**的红 / `cp` 逐文件还原 / 子进程摘 SDKROOT / 崩溃算 CAUGHT 不算没跑）。

**这一份修掉了上一份自己的一处坏**：上一份的基线步跑的是
`testQuickPickEmptyMessageTruthTable` —— 那是**别的套件**的用例名，
`--filter DailyCopyHeatmapTests/那个名字` 什么都选不到，输出里
"Executed 0 tests ... 0 failures" 照样含 "0 failures" ⇒ 基线步永远绿，
它其实什么都没基线。这一份要求**指定用例本人 passed**，选不到就是没基线。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
SUITE = "DailyCopyHeatmapTests"
VIEW = "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift"
POLICY = "Sources/ClipboardHistoryApp/Utilities/DailyCopyHeatPolicy.swift"
SETTINGS = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"

MUTANTS = [
    # M33：把悬停的事务撤掉 ⇒ 描边回到"硬生硬灭"（阶段一那条假动画的原状）。
    ("M33-hover-transaction-removed", VIEW,
     u"""                    withAnimation(MotionCatalog.animation(for: .hover)) {
                        hovered = inside ? cell : (hovered?.dayKey == cell.dayKey ? nil : hovered)
                    }""",
     u"""                    hovered = inside ? cell : (hovered?.dayKey == cell.dayKey ? nil : hovered)""",
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M34：键从 bucket 换成 count ⇒ 同档内的复制也会起事务，而"该动的没动、不该动的白动"。
    ("M34-cell-driven-by-count", VIEW,
     u"                .animation(MotionCatalog.animation(for: .contentFade), value: cell.bucket)",
     u"                .animation(MotionCatalog.animation(for: .contentFade), value: cell.count)",
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M35：把那条"声明了但空转"的页脚动画装回来 ⇒ 判据必须拒绝装饰性的 `.animation`。
    ("M35-footer-fake-animation-back", VIEW,
     u"""                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .font(.system(size: VisualFont.meta))""",
     u"""                .frame(maxWidth: .infinity, alignment: .leading)
                .animation(MotionCatalog.animation(for: .hover), value: hovered?.dayKey ?? "")
        }
        .font(.system(size: VisualFont.meta))""",
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M36：只给网格臂留过渡、把空态臂那半条摘掉 ⇒ "只演一半"必须红。
    ("M36-one-arm-only", VIEW,
     u"""                StateLine(kind: .empty, message: "还没有可统计的记录 —— 复制几条之后这里会长出一张日历。")
                    .transition(MotionCatalog.transition(for: .contentFade))""",
     u"""                StateLine(kind: .empty, message: "还没有可统计的记录 —— 复制几条之后这里会长出一张日历。")""",
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M37：两臂的过渡留着、驱动键摘掉 ⇒ 这正是"代码里有、屏幕上没有"那一族。
    ("M37-transition-undriven", VIEW,
     u"        .animation(MotionCatalog.animation(for: .contentFade), value: counts.isEmpty)",
     u"        // (驱动键被摘掉)",
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M38：空记录时也返回一句 ⇒ 空屏又会同时说"共 0 次"和"还没有记录"。
    ("M38-zeros-line-returns", POLICY,
     u"        guard hasRecords else { return nil }",
     u"        guard hasRecords || true else { return nil }",
     "testHeatmapSummaryLineTruthTable"),

    # M39：把被守卫的成员改名 ⇒ 区域取不到时必须**当场红**，
    #        不许安静返回哨兵串（那会让所有 XCTAssertFalse(contains:) 全绿）。
    #        **改名要连调用点一起改**：上一版只改声明，那一支根本没编译过 ——
    #        它报 `DID-NOT-RUN=build-failed`，那既不是"抓住了"也不是"放过了"，是**没跑**。
    #        而 `heatCellView` 仍然不含 needle `func cellView`（子串在中间不算命中），
    #        所以这一支测的确实是"守卫会不会在看不到目标时喊"。
    ("M39-guard-loses-its-target", VIEW,
     [(u"    private func cellView(_ cell: DailyCopyHeatPolicy.Cell) -> some View {",
       u"    private func heatCellView(_ cell: DailyCopyHeatPolicy.Cell) -> some View {"),
      (u"                                cellView(cell)",
       u"                                heatCellView(cell)")],
     "testHeatmapMotionIsDrivenNotJustClaimed"),

    # M40：汇总文案退回视图里拼 ⇒ 决定回到排版里，真值表管不到。
    ("M40-summary-copy-back-in-view", VIEW,
     u"""            if let line = DailyCopyHeatPolicy.summaryLine(for: summary,
                                                          hasRecords: !counts.isEmpty) {""",
     u"""            if let line = Optional("最近 \\(DailyCopyHeatPolicy.defaultWindowWeeks) 周共 \\(summary.total) 次 · 日均 0.0 次 · 连续 \\(summary.currentStreak) 天") {""",
     "testHeatmapSummaryDecisionIsAuthoredByThePolicy"),

    # M41：闸门摘掉 ⇒ 空屏又会同时说"还没有记录"和"这张图怎么读"。
    ("M41-guide-gate-removed", SETTINGS,
     u"            if !ledger.counts.isEmpty {\n                Divider()\n                readingGuide",
     u"            if true {\n                Divider()\n                readingGuide",
     "testHeatmapReadingGuideFollowsTheChart"),

    # M42：同一段说明出现第二份（比如有人把它复制回 `statsSection`）⇒ 两份会各自漂移。
    ("M42-guide-duplicated", SETTINGS,
     u"    private var statsSection: some View {\n        VStack(alignment: .leading, spacing: 16) {",
     u"    private var statsSection: some View {\n        VStack(alignment: .leading, spacing: 16) {\n            Text(\"这张图怎么读\")",
     "testHeatmapReadingGuideFollowsTheChart"),
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
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' failed" % (SUITE, case) in out:
        return "CAUGHT"
    if "Exited with unexpected signal code" in out:
        return "CAUGHT=crash"
    if "tests skipped" in out and "Executed 1 test" in out:
        return "DID-NOT-RUN=skipped"
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (SUITE, case) in out:
        return "ESCAPED"
    return "DID-NOT-RUN=case-not-found"


def main():
    # 基线：这一轮的**一条真用例**必须是绿的，而且必须是"这一条 passed"，
    # 不是"0 failures"（上一份就是被这一点骗成"永远有基线"的）。
    baseline_case = MUTANTS[0][4]
    baseline = run(baseline_case)
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (SUITE, baseline_case) not in baseline:
        print("BASELINE=NOT-GREEN(%s) —— 不注入" % baseline_case)
        print(baseline[-1500:])
        return 2
    print("BASELINE=green %s" % baseline_case)

    results = []
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for mutant in MUTANTS:
        # 一支可以改多处（改名必须连调用点一起改）；五元组是"只改一处"的简写。
        if len(mutant) == 5:
            name, relative, old, new, case = mutant
            edits = [(old, new)]
        else:
            name, relative, edits, case = mutant
        if only and only not in name:
            continue
        # 允许一支改多处（改名必须连调用点一起改，否则那一支编译不过 = 没跑）。
        pairs = edits if isinstance(edits, list) else [(edits, None)]
        path = os.path.join(SWIFT, relative)
        with io.open(path, encoding="utf-8") as fh:
            original = fh.read()
        mutated = original
        anchors = []
        for pair in pairs:
            old, new = pair
            if original.count(old) != 1:
                anchors.append("%d" % original.count(old))
                continue
            anchors.append("1")
            mutated = mutated.replace(old, new, 1)
        if mutated == original or any(a != "1" for a in anchors):
            print("%s: DID-NOT-RUN=anchor-count=%s" % (name, "/".join(anchors)))
            results.append((name, "DID-NOT-RUN"))
            continue
        backup = "/tmp/r9_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
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
