#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R6 变异对照：新加的五条判据各自抓得住什么。

规矩（以前栽过跟头之后写下来的）：
- 注入前先跑基线，基线不绿不许注入（否则"红"可能来自别处）；
- 红必须是**这一条**用例的红，而且必须是编译成功的红（编译报错当成抓到 = 自欺）；
- 每个变异用 `cp` 逐文件还原，绝不用 `git checkout -- .`（那会扫掉未提交的工作）；
- 子进程摘掉 SDKROOT：python3 会注入 CLT 的 SDK，和 Xcode 编译器不配对，表现为"0 个用例有效"。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = REPO + "/ClipboardHistory"
SUITE = "MotionDriverTests"

# (名字, 文件, 原文, 变异后, 必须变红的用例)
MUTANTS = [
    ("M9-constant-animation-key",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift",
     u"            Divider()\n            header\n",
     u"            Divider()\n            header\n            // MUTANT M9\n            Color.clear.frame(height: 0)\n                .animation(MotionCatalog.animation(for: .hover), value: true)\n",
     "testNoConstantAnimationKeysAcrossViews"),

    ("M10-count-after-clear",
     "Sources/ClipboardHistoryApp/Managers/SettingsWindowController.swift",
     u"""                let receipt = ClearHistoryReceiptPolicy.receipt(isFavorites: store.entries.map(\\.isFavorite))
                store.perform(.clear)
""",
     u"""                store.perform(.clear)
                let receipt = ClearHistoryReceiptPolicy.receipt(isFavorites: store.entries.map(\\.isFavorite))
""",
     "testReceiptIsComputedBeforeTheStoreIsCleared"),

    ("M11-preview-failure-branch-unfed",
     "Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift",
     u"""            case .failure(let message):
                failureView(message)
                    .transition(MotionCatalog.transition(for: .contentFade))
""",
     u"""            case .failure(let message):
                failureView(message)
""",
     "testPreviewStagesAreFed"),

    ("M12-chevron-name-swap",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift",
     u"""                Image(systemName: "chevron.right")
                    .font(.system(size: VisualGlyph.badge, weight: .semibold))
                    .foregroundStyle(.tertiary)
                    .rotationEffect(.degrees(isExpanded ? 90 : 0))
                    .animation(MultiFilePreviewLayout.animation, value: isExpanded)
""",
     u"""                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .font(.system(size: VisualGlyph.badge, weight: .semibold))
                    .foregroundStyle(.tertiary)
""",
     "testChevronRotatesInsteadOfSwappingSymbolNames"),

    ("M14-receipt-visual-only",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift",
     u"""                    if let clearReceipt { VoiceOverReceipt.announce(clearReceipt) }\n""",
     u"",
     "testClearReceiptIsRenderedAndFaded"),

    ("M13-receipt-without-fade",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift",
     u"            .animation(MotionCatalog.animation(for: .contentFade), value: clearReceipt == nil)\n",
     u"",
     "testClearReceiptIsRenderedAndFaded"),
]


def run(test_filter):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["swift", "test", "--filter", test_filter],
                            cwd=SWIFT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return out


def classify(out, case):
    if "Build complete" not in out:
        return "DID-NOT-RUN=build-failed"
    if "Test Case '-[ClipboardHistoryAppTests.%s " % SUITE not in out:
        return "DID-NOT-RUN=no-test-executed"
    red = "Test Case '-[ClipboardHistoryAppTests.%s %s]' failed" % (SUITE, case)
    green = "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (SUITE, case)
    if red in out:
        return "CAUGHT"
    if green in out:
        return "ESCAPED"
    return "DID-NOT-RUN=case-not-found"


def main():
    baseline = run(SUITE)
    if "0 failures" not in baseline:
        print("BASELINE=NOT-GREEN —— 不注入")
        print(baseline[-1500:])
        return 2
    print("BASELINE=green")

    results = []
    for name, relative, old, new, case in MUTANTS:
        path = os.path.join(SWIFT, relative)
        backup = "/tmp/mutation_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        original = io_read(backup)
        if original.count(old) != 1:
            print("%s: DID-NOT-RUN=anchor-count=%d" % (name, original.count(old)))
            results.append((name, "DID-NOT-RUN"))
            continue
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new, 1))
        verdict = classify(run("%s/%s" % (SUITE, case)), case)
        print("%s: %s" % (name, verdict))
        results.append((name, verdict))
        shutil.copy2(backup, path)
        if io_read(path) != original:
            print("还原失败：%s 与注入前不一致，停止" % relative)
            return 3

    bad = [n for n, v in results if v != "CAUGHT"]
    print("MUTATION_SUMMARY caught=%d/%d %s"
          % (len(results) - len(bad), len(results), ("残留: " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


def io_read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


if __name__ == "__main__":
    sys.exit(main())
