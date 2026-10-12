#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R7 变异对照：浮层与临时状态那五条判据各自抓得住什么。

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
SUITE = "OverlayStateTests"

MUTANTS = [
    ("M15-empty-label-never-refreshed",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift",
     u"        applyEmptyState()\n        guard let table else { return }",
     u"        guard let table else { return }",
     "testQuickPickPanelWiresTheEmptyLabel"),

    ("M16-one-message-for-all-empties",
     "Sources/ClipboardHistoryApp/Utilities/QuickPickModel.swift",
     u'''        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if !needle.isEmpty {
            return "没有匹配「\\(needle)」的记录，换个词或按 Esc 清空。"
        }''',
     u'''        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if !needle.isEmpty {
            return "没有可显示的记录。"
        }''',
     "testQuickPickEmptyMessageTruthTable"),

    ("M17-bulk-bar-one-arm-only",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift",
     u"""                bulkActionButtons
                    .transition(MotionCatalog.transition(for: .contentFade))""",
     u"""                bulkActionButtons""",
     "testBulkBarTransitionsOnBothArms"),

    ("M18-video-one-icon-unwired",
     "Sources/ClipboardHistoryApp/Views/VideoPreview.swift",
     u"""                    .symbolMotion(symbol: playback.isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill",
                                  replacesSymbol: true)
                    .animation(MotionCatalog.animation(for: .contentFade), value: playback.isMuted)
""",
     u"",
     "testVideoControlsShareTheSymbolMotionEntry"),

    ("M19-second-symbol-replacement-author",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift",
     u"            self.focusEffectDisabled()\n",
     # 插在 14+ 那一臂里：这样它**一定编译得过**。
     # 放在 12 那一层会得到 "only available in macOS 13"，于是"抓到了"其实是编译失败
     #（本仓库记过这一族：变异的红必须是断言的红）。
     u"            self.focusEffectDisabled().contentTransition(.symbolEffect(.replace))\n",
     "testSymbolReplacementHasOneAuthor"),
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

    bad = [n for n, v in results if v != "CAUGHT"]
    print("MUTATION_SUMMARY caught=%d/%d %s"
          % (len(results) - len(bad), len(results), ("残留: " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
