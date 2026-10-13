#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R12（筛选胶囊归目录 + 合成 reduce 闸门 + 悬停底色）变异对照：四支。

规矩同前三支：基线必须是**指定那条用例 passed**、红必须是这一条用例的红、
`cp` 逐文件还原、子进程摘 SDKROOT、崩溃算 CAUGHT=crash、注释行在字面量扫描前先摘掉。

M51 故意打到**另一个套件**（`MotionCatalogTests` 的白名单闸）：
"把参数迁回视图里写"这件事，抓它的不是本模块的判据，而是目录那条"例外集合相等"。
"""
import io
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SWIFT = os.path.join(REPO, "ClipboardHistory")
SIDEBAR = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
PILL = "FilterPillMotionTests"
CAT = "MotionCatalogTests"

MUTANTS = [
    # M50：过冲的旧值回来 ⇒ 真值表与"旧字面量不许回来"两条都要红。
    ("M50-overshoot-damping-back", PILL, SIDEBAR,
     [(u"                          response: MotionCatalog.duration(for: .slider),\n"
       u"                          damping: MotionCatalog.criticalDamping)",
       u"                          response: MotionCatalog.duration(for: .slider),\n"
       u"                          damping: 0.72)")],
     "testSlideMotionIsCriticallyDampedAndSourcedFromTheCatalog"),

    # M51：曲线在视图里就地构造（虽然参数还是目录的）⇒ 目录的白名单集合要红。
    ("M51-spring-built-in-the-view", CAT, SIDEBAR,
     [(u"        return MotionCatalog.animation(for: .slider, reduceMotion: reduceMotion)",
       u"        return .spring(response: MotionCatalog.duration(for: .slider),\n"
       u"                       dampingFraction: MotionCatalog.criticalDamping)")],
     "testMotionParametersOutsideTheCatalogAreWhitelisted"),

    # M52：悬停底色没人读 ⇒ 减弱动态时这一段又回到"只有缩放"，也就是零反馈。
    ("M52-hover-fill-unwired", PILL, SIDEBAR,
     [(u"""                .background(
                    // 减弱动态时缩放归 1.0，这一层就是**唯一**的悬停表达 ——
                    // 以前这一段只剩缩放一种说法，于是"开了减弱动态 = 悬停没有反馈"。
                    VisualShape.rounded(VisualRadius.control)
                        .fill(Color.primary.opacity(
                            FilterPillMotion.hoverFill(isHovered: isHovered, isSelected: isSelected)))
                )
""", u"")],
     "testSidebarConsumesTheMotionPolicyInsteadOfHardcodingSpring"),

    # M53：段按钮退回单源闸门（只读系统开关，不读 VoiceOver）。
    ("M53-single-source-gate", PILL, SIDEBAR,
     [(u"    /// 同 `SegmentedFilterPicker.shouldReduce`：系统开关 ∪ VoiceOver。\n"
       u"    private var shouldReduce: Bool { reduceMotion || MotionCatalog.motionShouldBeReduced }",
       u"    /// 同 `SegmentedFilterPicker.shouldReduce`：系统开关 ∪ VoiceOver。\n"
       u"    private var shouldReduce: Bool { reduceMotion }")],
     "testSidebarConsumesTheMotionPolicyInsteadOfHardcodingSpring"),
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
    first = MUTANTS[0]
    baseline = run(first[1], first[4])
    if "Test Case '-[ClipboardHistoryAppTests.%s %s]' passed" % (first[1], first[4]) not in baseline:
        print("BASELINE=NOT-GREEN(%s/%s) —— 不注入" % (first[1], first[4]))
        print(baseline[-1500:])
        return 2
    print("BASELINE=green %s/%s" % (first[1], first[4]))

    results = []
    for name, suite, relative, edits, case in MUTANTS:
        if only and only not in name:
            continue
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
        backup = "/tmp/r12_backup_" + os.path.basename(relative)
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
