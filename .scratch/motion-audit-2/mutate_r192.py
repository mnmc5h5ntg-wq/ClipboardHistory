#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 的变异表：两处"两臂相同吗"的比较有没有牙（BACKLOG 216）。

臂的形状按 `mutate_needle_precheck.arm_sites` 认的那一种：(编号, 说明, 文件, needle, 变异文, 该跑的卷)。
还原走内存快照（工作树是脏的，绝不 git checkout）。

这张表的存在理由与 R191 同一条：**退回旧口径在本机跑测试抓不到** —— 本机两臂峰值实测相等
（row-star `0.268/0.268`、detail `0.051/0.051`），新旧口径给同一个数，两种写法都绿。
可证伪性来自形状（接线扫描 + 合成真值表），不来自结果。

刀名里写明"这是跨臂**相同性**比较"，不是"任何跨臂比较"：216 的原提案（推广到 :2916 与 :2332）
经实测被驳回 —— 幅度不对称那一族（MOTION_SEQUENCE 两臂 0.027/0.234）套同一条线会把小臂判成 0 帧，
那是把"没量到"说成"落定了"。这条区分由 M719/M720 钉在真值表上。
"""
import io
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WIRING = "MotionFilmstripTests/testCrossArmSamenessComparisonsUseBothRulers"
TRUTH = "MotionFilmstripTests/testCrossArmRulerAgreementIsATruthTable"

ARMS = [
    ("M712", "row-star 的一臂退回各自归一化（跨臂相同性比较比的不是同一个量）", TEST,
     "let onShared = Self.transitionFrameCount(on, sharedFloor: sharedLineSymbol)",
     "let onShared = Self.transitionFrameCount(on)", WIRING),
    ("M713", "detail 的一臂退回各自归一化（同上，另一处站点）", TEST,
     "let offSpanShared = Self.transitionFrameCount(off, sharedFloor: sharedLineDetail)",
     "let offSpanShared = Self.transitionFrameCount(off)", WIRING),
    ("M714", "同一条线只由一臂导出（'共享'名不副实）", TEST,
     "let sharedLineSymbol = Self.sharedMovingFloor([on, off])",
     "let sharedLineSymbol = Self.sharedMovingFloor([on])", WIRING),
    ("M715", "合读法算了但不打进日志（两把尺的关系只剩在代码里）", TEST,
     r'             + " ⇒ \(agreementSymbol)")',
     r'             + " ⇒ 合读法已省略")', WIRING),
    ("M716", "旧口径不再打印（换判据口径没有证人，R146 那一课）", TEST,
     r'             + " ｜ 旧口径（各自归一化）开=\(onPerArm) 关=\(offPerArm)"',
     r'             + " ｜ 旧口径已省略"', WIRING),
    ("M717", "硬判据退回单把尺（只问新口径，免责的门变松）", TEST,
     "XCTAssertTrue(onShared == offShared && onPerArm == offPerArm,",
     "XCTAssertTrue(onShared == offShared,", WIRING),
    ("M718", "detail 的免责分支退回只问一把尺", TEST,
     "if onSpan == offSpan && onSpanShared == offSpanShared && abs(Self.peak(on) - Self.peak(off)) < 0.02 {",
     "if onSpan == offSpan, abs(Self.peak(on) - Self.peak(off)) < 0.02 {", WIRING),
    ("M719", "共用线适用域恒判'安全'（幅度不对称把小臂判成不存在这件事就没有证人）", TEST,
     "        return lo >= sharedMovingFloor(regions)",
     "        return true", TRUTH),
    ("M720", "矛盾格替一把尺背书（把'线吃掉了小臂'说成'这把尺看得见'）", TEST,
     '                    + "⇒ 这是幅度不对称把小臂判成不存在，不是这条 A/B 真的可见（BACKLOG 217）"',
     '                    + "⇒ 这把尺看得见这条动效，升级成硬判据"', TRUTH),
]

SUMMARY = re.compile(r"Executed (\d+) tests?, with (\d+) failures?(?: \(0 unexpected\))?"
                     r"(?:, with (\d+) tests? skipped)?")


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name):
    """返回 (退出码, 跑了几条, skip 了几条)。skip>0 或 0 条 ⇒ 这一刀不算 CAUGHT。"""
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    executed = skipped = None
    for line in text.splitlines():
        if line.strip().startswith("Executed "):
            m = re.search(r"Executed (\d+) tests?, with (\d+) failures?", line)
            if m:
                executed, skipped = int(m.group(1)), int(m.group(2))
        s = re.search(r"with (\d+) tests? skipped", line)
        if s:
            skipped = int(s.group(1))
    return proc.returncode, executed, skipped


def main():
    only = sys.argv[1:] or None
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        if only and arm_id not in only:
            continue
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）" % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl))
            code, executed, skipped = run_test(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        summary = "跑到 %s 条 / 失败 %s" % (executed, skipped)
        if executed in (None, 0):
            not_run += 1
            print("%s NOT_RUN 该跑的卷没露面（%s）⇒ 不算 CAUGHT：%s" % (arm_id, summary, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s（%s）" % (arm_id, filt, why, summary), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R192_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
