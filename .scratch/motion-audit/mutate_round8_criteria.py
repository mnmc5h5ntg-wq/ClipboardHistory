#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 变异对照：排除名单与结果文案那四条判据各自抓得住什么。

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
    # M20：把"系统默认已覆盖"那一支删掉 ⇒ 用户加 `com.apple.keychainaccess` 会被当成加成功，
    #      写进用户名单、看起来"能移除"，而行为一点没变 —— 正是审计说的"我加的那条去哪了"。
    ("M20-default-excluded-treated-as-added",
     "Sources/ClipboardHistoryApp/Utilities/ExcludedAppListPolicy.swift",
     u"""        if defaults.contains(id) {
            return Result(raw: raw, outcome: .coveredByDefault(id),
                          receipt: "「\\(id)」属于系统默认排除项，本来就不入库，不用再加。")
        }
""",
     u"",
     "testExcludedListPolicyTruthTable"),

    # M21：删掉名单那一行的过渡（驱动还在）⇒ 添加/移除变成整块瞬间塌位。
    ("M21-list-row-transition-removed",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift",
     u"""                            // 行会真的消失：这里不是 `List`（`List` 的行过渡在 macOS 上
                            // 四种写法都跑不出来，账本 M1 / D-055），是普通 `VStack`，
                            // 所以过渡**能**演 —— 前提是别只挂一臂（R5 的 A2 那一族）。
                            .transition(MotionCatalog.transition(for: .contentFade))
""",
     u"",
     "testSettingsReceiptLinesAreDismissibleAndDoNotVanish"),

    # M22：收起按钮被摘 ⇒ 回到"永不清空"。
    ("M22-receipt-not-dismissible",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift",
     u"""            Button(action: dismiss) {
                Image(systemName: "xmark.circle")
                    .font(.system(size: VisualGlyph.badge))
            }
            .buttonStyle(.borderless)
            .helpLabel("收起这条提示")
""",
     u"",
     "testSettingsReceiptLinesAreDismissibleAndDoNotVanish"),

    # M23：把"自动消失"装回来（这是最容易被顺手加错的一种"改进"）。
    ("M23-receipt-auto-vanishes",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift",
     u"""        .transition(MotionCatalog.transition(for: .contentFade))
    }
}""",
     u"""        .transition(MotionCatalog.transition(for: .contentFade))
        .onAppear {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.1) { dismiss() }
        }
    }
}""",
     "testSettingsReceiptLinesAreDismissibleAndDoNotVanish"),
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
