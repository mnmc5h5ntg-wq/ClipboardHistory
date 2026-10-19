#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 的变异表：新加的那道**能力出口**有没有牙（出口最容易坏在"变成唯一出路"）。

臂的形状按 `mutate_needle_precheck.arm_sites` 认的那一种：(编号, 说明, 文件, needle, 变异文, 该跑的卷)。
还原走内存快照（工作树是脏的，绝不 git checkout），每臂跑完立刻核对字节。

为什么 M706 比 M705 更要紧：把能力判据换成常量 `true`，本机那条像素判据**照样绿**（暗档本来就能判），
唯一会红的是"接线扫描"—— 那正是这类出口的真实坏法：代码还在、名字还在、牙没了。
"""
import io
import os
import subprocess
import sys
import tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
GEO = "Sources/ClipboardHistoryApp/Views/FilterPillGeometry.swift"
TEST = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
PURE = "FilterPillGeometryTests"
PIXEL = "UICaptureTests/testFilterPillBrightBandFollowsTheSelectedSegment"

ARMS = [
    ("M703", "宽度那半前提被摘掉（整列都是背景也能说找到了底轨）", GEO,
     "if Double(trackWidth) / Double(columnWidth) < trackMustCoverColumnFraction { return false }",
     "if false { return false }", PURE),
    ("M704", "对比地板被摘掉（任何机器都说自己看得见材质）", GEO,
     "return contrast >= materialContrastFloor",
     "return true", PURE),
    ("M705", "占比地板降到 0（边界那一格失去意义）", GEO,
     "static let trackMustCoverColumnFraction: Double = 0.4",
     "static let trackMustCoverColumnFraction: Double = 0.0", PURE),
    ("M706", "判据不再问能力谓词（出口变成装饰）", TEST,
     "let canSeeMaterial = FilterPillGeometry.channelCanSeeMaterial(\n"
     "                trackWidth: bestTrack.1 - bestTrack.0, columnWidth: colW, contrast: materialContrast)",
     "let canSeeMaterial = true", PURE),
    ("M707", "能力出口反号（能判的档被跳过、判不了的档去判）", TEST,
     "if !canSeeMaterial {",
     "if canSeeMaterial {", PIXEL),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name, shots_dir):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots_dir
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
            print("%s NOT_RUN needle 命中 %d 次（要 1）on %s" % (arm_id, hits, target), flush=True)
            continue
        shots = tempfile.mkdtemp(prefix="r190-mut-")
        try:
            write(target, original.replace(needle, repl))
            code = run_test(filt, shots)
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
            print("%s ESCAPED %s 仍绿 ⇒ %s（这一支没有牙）" % (arm_id, filt, why), flush=True)
    total = caught + escaped + not_run
    print("MUTATE_R190 CAUGHT=%d/%d, RESTORE_CLEAN=yes" % (caught, total))
    print("SUMMARY caught=%d escaped=%d not_run=%d" % (caught, escaped, not_run))
    if only:
        return 0
    return 0 if (escaped == 0 and not_run == 0 and total == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
