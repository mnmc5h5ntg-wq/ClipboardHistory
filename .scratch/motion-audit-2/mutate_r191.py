#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 的变异表：④ 那条"同一条线"的比较有没有牙。

臂的形状按 `mutate_needle_precheck.arm_sites` 认的那一种：(编号, 说明, 文件, needle, 变异文, 该跑的卷)。
还原走内存快照（工作树是脏的，绝不 git checkout）。

M709 是这张表的存在理由：把"同一条线"换回各自归一化，**跑测试抓不到**（本机两种口径都绿），
只有接线扫描抓得到 —— 这条判据的可证伪性来自形状，不来自结果。
"""
import io
import os
import subprocess
import sys
import tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WIRING = "MotionFilmstripTests/testBandProcessComparisonUsesOneSharedLine"
BAND = "MotionFilmstripTests/testBandCaptureIsCheaperAndStillSeesTheMotion"

ARMS = [
    ("M708", "同线计数恒等于 0（带那一臂什么都看不到，比较却仍然写在那里）", TEST,
     "        fractions.filter { $0 >= sharedFloor }.count",
     "        return 0", BAND),
    ("M709", "退回各自归一化的线（两臂比的不是同一个量）", TEST,
     "Self.transitionFrameCount(Self.deltas(film.motionFrames), sharedFloor: sharedMoving)",
     "Self.transitionFrameCount(Self.deltas(film.motionFrames), sharedFloor:"
     " (Self.deltas(film.motionFrames).max() ?? 0) * Self.stepFloorRatio)", WIRING),
    ("M710", "比较方向反号", TEST,
     "XCTAssertGreaterThanOrEqual(bandShared, fullShared,\n            \"同一条绝对线",
     "XCTAssertLessThanOrEqual(bandShared, fullShared,\n            \"同一条绝对线", BAND),
    ("M711", "新口径不再打印旧口径（换判据口径没有证人）", TEST,
     '             + "｜ 旧口径（各自归一化）带=\\(bandOld) 整窗=\\(fullOld)")',
     '             + "｜ 旧口径已省略")', WIRING),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode


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
            code = run_test(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s" % (arm_id, filt, why), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s 仍绿 ⇒ %s" % (arm_id, filt, why), flush=True)
    total = caught + escaped + not_run
    print("MUTATE_R191 CAUGHT=%d/%d, RESTORE_CLEAN=yes" % (caught, total))
    print("SUMMARY caught=%d escaped=%d not_run=%d" % (caught, escaped, not_run))
    if only:
        return 0
    return 0 if (escaped == 0 and not_run == 0 and total == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
