#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R13（悬停那一档真的可达 + 三处 `.borderless` 归队）变异对照：五支。

规矩同前四支：基线必须是**指定那条用例 passed**、红必须是这一条用例的红、
`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash。

M58 是这一支里唯一"预期先漏"的一支，而且**故意**留着让它先漏：
`hoverLevel` 是本轮新加的参数，真值表测了函数、白名单测了调用点，
唯独"样式内部把参数转交给持有悬停状态的那一层"这一步没人钉 ——
这正是 R13 抓到的那条缺陷的形状（载荷绿、消费侧坏）在**新参数**上重演一次。
它漏了就把守卫补上，补完再跑一遍，两支都记进台账。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
STYLE = "Sources/ClipboardHistoryApp/Views/PressableStyle.swift"
SIDEBAR = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
P = "PressFeedbackTests"

FILL_CALL = (u"                fillShape.fill(Color.primary.opacity(\n"
             u"                    PressableAppearance.fillOpacity(isPressed: configuration.isPressed,\n"
             u"                                                   isHovered: isHovered,\n"
             u"                                                   hoverLevel: hoverLevel)))")

MUTANTS = [
    # M54：把悬停写死回 false —— 也就是 R13 之前的原样。
    ("M54-hover-hardcoded-off", P, STYLE,
     [(FILL_CALL,
       FILL_CALL.replace(u"isHovered: isHovered,", u"isHovered: false,"))],
     "testHoverArmIsReachableFromTheButtonStyle"),

    # M55：侧栏批量按钮（含删除）退回 `.borderless`。
    ("M55-borderless-back-in-sidebar", P, SIDEBAR,
     [(u"        .pressedStyle(in: VisualShape.rounded(VisualRadius.control),\n"
       u"                      hoverLevel: VisualFill.controlHover)",
       u"        .buttonStyle(.borderless)")],
     "testEveryNonMenuButtonHasPressFeedback"),

    # M56：悬停那一档进了状态、没进事务 —— 硬切。
    ("M56-hover-arm-not-animated", P, STYLE,
     [(u"            .animation(MotionCatalog.animation(for: .hover), value: configuration.isPressed)\n"
       u"            .animation(MotionCatalog.animation(for: .hover), value: isHovered)",
       u"            .animation(MotionCatalog.animation(for: .hover), value: configuration.isPressed)")],
     "testHoverArmIsReachableFromTheButtonStyle"),

    # M57：`hoverLevel` 参数收下不用 —— 小控件抬一档这句话只剩注释。
    ("M57-hover-level-ignored", P, STYLE,
     [(u"        if isPressed { return VisualFill.pressed }\n"
       u"        return isHovered ? hoverLevel : 0",
       u"        if isPressed { return VisualFill.pressed }\n"
       u"        return isHovered ? VisualFill.hover : 0")],
     "testPressAppearanceTruthTable"),

    # M58：样式内部转交时把参数换成默认档（函数对、接线错）。
    # 第一版**全绿通过**（4/5）—— 于是把 `testStyleForwardsItsParametersInsteadOfResupplyingDefaults`
    # 补上：判据取的是 `func makeBody` 的花括号配平区域，不是整文件 contains。
    # 用例名一并从 testHoverArm… 换成新那条：旧那条管"有没有悬停这一半"，新那条才管接缝。
    ("M58-hover-level-not-forwarded", P, STYLE,
     [(u"                     reduceMotion: reduceMotion,\n"
       u"                     hoverLevel: hoverLevel)",
       u"                     reduceMotion: reduceMotion,\n"
       u"                     hoverLevel: VisualFill.hover)")],
     "testStyleForwardsItsParametersInsteadOfResupplyingDefaults"),
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
    first = selected[0]
    baseline = run(first[1], first[4])
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (first[1], first[4]) not in baseline:
        print("BASELINE=NOT-GREEN(%s/%s) —— 不注入" % (first[1], first[4]))
        print(baseline[-1500:])
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
        backup = "/tmp/r13_backup_" + os.path.basename(relative)
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
