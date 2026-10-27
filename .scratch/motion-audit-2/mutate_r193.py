#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 的变异表：时间轴那把新尺（`armProcessInIntervals` + `processReadingVerdict`）有没有牙。

臂的形状按 `mutate_needle_precheck.arm_sites` 认的那一种：(编号, 说明, 文件, needle, 变异文, 该跑的卷)。
还原走内存快照（工作树是脏的，绝不 git checkout）。

本轮的靶不是"跨臂比"而是**同一臂的两个数对不上**：真卷读到
`row-insert 开 帧数=9 … 过程=1.4个间隔 帧对1` —— 九帧是散着抖出来的，不是一段一直在演的过程。
所以刀分两类：M721/M722 打的是"合读法的界与措辞"（真值表抓），
M723/M724/M725 打的是"读数有没有送到日志、有没有拿错自己那一臂的钟"（接线扫描抓）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
TRUTH = "MotionFilmstripTests/testContiguousProcessDiffersFromScatteredChanges"
WIRING = "MotionFilmstripTests/testNativeRowAbSitesPrintTheTimeAxis"

ARMS = [
    ("M721", "散点撑绿的界被放到 0 ⇒ 任何一臂都算'演了一段过程'", TEST,
     "        if intervals < 2.0 { return \"散点撑绿",
     "        if intervals < 0.0 { return \"散点撑绿", TRUTH),
    ("M722", "矛盾那格替帧数背书（把'只有散点'说成'有一段过程'）", TEST,
     "return \"散点撑绿：帧数 \\(span) 够，但含峰值那段只跨",
     "return \"有一段一直在演的过程：帧数 \\(span) 够，含峰值那段跨", TRUTH),
    ("M723", "时间轴不再打进日志（runner 那一跑没有读数，下一轮又只能拿本机单次签字）", TEST,
     'emit("MOTION_NATIVE row-insert 开 帧数=\\(animatedSpan) 峰值=\\(String(format: "%.3f", Self.peak(animated))) '
     '采样≈\\(animatedInterval)ms 过程=\\(Self.processReading(animatedProcess, span: animatedSpan))")',
     'emit("MOTION_NATIVE row-insert 开 帧数=\\(animatedSpan) 峰值=\\(String(format: "%.3f", Self.peak(animated))) '
     '采样≈\\(animatedInterval)ms")', WIRING),
    ("M724", "序列那处退回把 `recordProductSequence` 直接喂给差分 ⇒ 第一臂量到第二臂的钟", TEST,
     "var sameRow = Self.deltas(sameFilm)",
     "var sameRow = Self.deltas(probe.recordProductSequence(selectionChanges: false))", WIRING),
    ("M725", "一臂退回只看帧数（站点只量了一臂的过程）", TEST,
     "let movedProcess = Self.armProcessInIntervals(stamps: movedStamps, fractions: moved)",
     "let movedProcess: (intervals: Double, run: ChangedRun)? = nil", WIRING),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name):
    """返回 (退出码, 跑了几条, 失败几条)。0 条 / 名单没露面 ⇒ 不算 CAUGHT。"""
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    executed = failures = None
    for line in text.splitlines():
        if line.strip().startswith("Executed "):
            m = re.search(r"Executed (\d+) tests?, with (\d+) failures?", line)
            if m:
                executed, failures = int(m.group(1)), int(m.group(2))
    return proc.returncode, executed, failures


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
            code, executed, failures = run_test(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        if not executed:
            not_run += 1
            print("%s NOT_RUN 该跑的卷没露面 ⇒ 不算 CAUGHT：%s" % (arm_id, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s（跑到 %d 条 / 失败 %d）" % (arm_id, filt, why, executed, failures), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R193_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
