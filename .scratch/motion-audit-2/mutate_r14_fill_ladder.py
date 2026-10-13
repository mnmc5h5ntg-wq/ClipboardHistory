#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R14（底色台阶的像素判据 + 两张从没存在过的帧 + 夹具还原自检）变异对照：四支。

规矩同前：基线必须是**指定那条用例 passed**、红必须是这一条用例的红、
`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash。

这一支的靶子分两类，故意的：
* M59/M60 打的是**产品令牌** —— 本轮新判据要抓的就是"两档在屏幕上其实是同一档"，
  所以把两档并到一起必须红；M59 特别重要，它把 R13 自己引入的那一步（0.08→0.10）钉住了。
* M61 打的是**判据自己**（渲染夹具吃掉 `level`）—— 尺子如果画不出差别，
  上面那两支就都是纸上的。M62 打的是**夹具的还原**：污染是静默的，只能这样钉。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
TOKENS = "Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift"
PRESS = "Tests/ClipboardHistoryAppTests/PressFeedbackTests.swift"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
P = "PressFeedbackTests"
CAP = "UICaptureTests"
LADDER = "testFillLaddersAreVisibleOnBothControlClasses"

MUTANTS = [
    # M59：把小控件那一档抬回 R13 的 0.10 ⇒ 悬停与按下在 22pt 上并成一档（实测 3.7/255）。
    ("M59-controlHover-back-to-010", P, TOKENS,
     [(u"    static let controlHover: Double = 0.08",
       u"    static let controlHover: Double = 0.10")],
     LADDER, None),

    # M60：按下那一档并到悬停上（另一侧的同一种塌法）。
    ("M60-pressed-collapsed-onto-hover", P, TOKENS,
     [(u"    static let pressed: Double = 0.12",
       u"    static let pressed: Double = 0.10")],
     LADDER, None),

    # M61：渲染夹具收下 `level` 但不用 ⇒ 三档画出来一模一样，判据必须立刻红。
    ("M61-fixture-ignores-level", P, PRESS,
     [(u"                VisualShape.rounded(VisualRadius.control)\n"
       u"                    .fill(Color.primary.opacity(level))",
       u"                VisualShape.rounded(VisualRadius.control)\n"
       u"                    .fill(Color.primary.opacity(0))")],
     LADDER, None),

    # M62：种了默认值不还原 ⇒ 夹具机械的自检要红（不红就等于污染是静默的）。
    ("M62-seed-not-restored", CAP, HARNESS,
     [(u"                if let restored = previousSeed {\n"
       u"                    if let value = restored.value {\n"
       u"                        UserDefaults.standard.set(value, forKey: restored.key)\n"
       u"                    } else {\n"
       u"                        UserDefaults.standard.removeObject(forKey: restored.key)\n"
       u"                    }\n"
       u"                }\n",
       u"                _ = previousSeed\n")],
     "testCaptureKeyViews", {"CLIPBOARD_HISTORY_UI_SHOTS": "/tmp/r14-mutation-shots"}),
]


def run(suite, case, extra_env=None):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(["swift", "test", "--filter", "%s/%s" % (suite, case)],
                            cwd=SWIFT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return out


def classify(suite, case, out):
    if "Build complete" not in out and "Compiling" not in out:
        return "DID-NOT-RUN=build-failed"
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
    # 元组形状：(name, suite, relative, edits, case, extra_env) —— 索引 0..5。
    # 第一版这里按 0..6 取，直接 IndexError 崩在注入之前（崩得早，没污染任何文件）。
    first = selected[0]
    baseline = run(first[1], first[4], first[5])
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (first[1], first[4]) not in baseline:
        print("BASELINE=NOT-GREEN(%s/%s) —— 不注入" % (first[1], first[4]))
        print(baseline[-1500:])
        return 2
    print("BASELINE=green %s/%s" % (first[1], first[4]))

    results = []
    for name, suite, relative, edits, case, extra_env in selected:
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
        backup = "/tmp/r14_backup_" + os.path.basename(relative)
        shutil.copy2(path, backup)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        verdict = classify(suite, case, run(suite, case, extra_env))
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
