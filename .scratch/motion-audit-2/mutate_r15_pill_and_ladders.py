#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R15（药丸/命中区的 padding + 令牌必须进梯子 + field 那一族）变异对照：四支。

规矩同前：基线必须是**指定那条用例 passed**、红必须是这一条用例的红、
`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash。

四支各打一层，故意不重复：
* M63 打**调用点**（侧栏把 labelPadding 撤掉）—— 新参数没有消费者就只是类型定义；
* M64 打**接缝**（padding 挂上去了但挂的是常量 0）—— 与 R14 的 M58 同一族；
* M65 打**覆盖守卫**（把 field 那一族从梯子里摘掉）—— 令牌还在、没人量，正是 R13 事故的下一版；
* M66 打**梯子本身**（输入框两档并成一档）—— 证明新加那条梯子真的在量东西。
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
SIDEBAR = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
STYLE = "Sources/ClipboardHistoryApp/Views/PressableStyle.swift"
P = "PressFeedbackTests"
CAP = "UICaptureTests"
LADDER = "testFillLaddersAreVisibleOnBothControlClasses"

MUTANTS = [
    # M63：侧栏那颗把 labelPadding 撤掉 ⇒ "三处小控件都抬了"这句话要红。
    ("M63-sidebar-padding-dropped", P, SIDEBAR,
     [(u"                      hoverLevel: VisualFill.controlHover,\n"
       u"                      labelPadding: 5)",
       u"                      hoverLevel: VisualFill.controlHover)")],
     "testSmallControlsAskForThePillPadding", None),

    # M64：padding 挂上去了，但挂的是常量 0 ⇒ 参数是装饰。
    ("M64-padding-is-a-constant", P, STYLE,
     [(u"            .padding(labelPadding)", u"            .padding(0)")],
     "testHoverArmIsReachableFromTheButtonStyle", None),

    # M65：把 field 那一族从梯子里摘掉 ⇒ 集合相等守卫要红
    #      （"令牌还在、没人量"正是 R13 那种事故的下一个版本）。
    ("M65-field-ladder-dropped", P, PRESS,
     [(u"            Ladder(name: \"field\", size: NSSize(width: 280, height: 28),\n"
       u"                   steps: [(\"fieldIdle\", VisualFill.fieldIdle),\n"
       u"                           (\"fieldActive\", VisualFill.fieldActive)])\n", u"")],
     "testEveryVisualFillTierIsCoveredByALadder", None),

    # M66：输入框两档并成一档 ⇒ field 梯子要红（证明那条梯子真的在量东西）。
    # 这一支**第一次是 ESCAPED**，而且逃逸的原因不是判据松，是尺子自己错了：
    # 梯子从 `level: 0` 起步再 `dropFirst()`，对行/控件没错（第一步就是 idle=0），
    # 但输入框静止态不是 0 —— 于是那条梯子量的是"idle→fieldActive"，
    # `fieldIdle→fieldActive` 这一步根本没比过。改成"从梯子第一步起步"之后，
    # 同一支变异立刻红，并且顺手量出真的缺陷（暗色下 3.98/255，低于地板 4）。
    ("M66-field-tiers-collapsed", P, TOKENS,
     [(u"    static let fieldActive: Double = 0.075", u"    static let fieldActive: Double = 0.035")],
     "testFillLaddersAreVisibleOnBothControlClasses", None),
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
        backup = "/tmp/r15_backup_" + os.path.basename(relative)
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
