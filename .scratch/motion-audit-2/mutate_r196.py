#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 的变异表：key-view 结构量法（`testSidebarKeyViewChainStructureIsPrinted`）有没有牙。

两把刀，catcher 不同：
M730 打在**量法自己**（环走不到 ⇒ 那条 `XCTAssertFalse(loop.isEmpty)` 要红）；
M731 打在**读数通道**（把 FKA 那行 print 的标记改名 ⇒ `FrameIntervalBudgetTests` 的 print 名册要红，
     那正是 R143 立"名册不是计数"时要防的形状：没人打印的读数等于没有读数）。
"""
import io, os, re, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"
MEASURE = "UIInteractionProbeTests/testSidebarKeyViewChainStructureIsPrinted"
ROSTER = "FrameIntervalBudgetTests/testProbeFilePrintReadingsAreARosterNotACount"

ARMS = [
    ("M730", "环从 contentView 走不到任何一站（量法把起点弄丢 ⇒ 空环必须红）", TEST,
     "var cursor: NSView? = window.contentView",
     "var cursor: NSView? = nil", MEASURE),
    ("M731", "FKA 分辨实验的标记被改名（读数还在，名册看不见 ⇒ 静默免检）", TEST,
     'CaptureReadings.emit("KEYCHAIN_FKA 开关=',
     'CaptureReadings.emit("KEYCHAIN_FKAX 开关=', ROSTER),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run(filter_name):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_INTERACTION"] = "1"
    proc = subprocess.run(["swift", "test", "--filter", filter_name], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    executed = failures = skipped = None
    for line in text.splitlines():
        if line.strip().startswith("Executed "):
            m = re.search(r"Executed (\d+) tests?, with (\d+) failures?", line)
            if m:
                executed, failures = int(m.group(1)), int(m.group(2))
            s = re.search(r"(\d+) tests? skipped", line)
            if s:
                skipped = int(s.group(1))
    return proc.returncode, executed, failures, skipped


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）" % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl))
            code, executed, failures, skipped = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        if not executed or skipped:
            not_run += 1
            print("%s NOT_RUN 跑到=%s skip=%s ⇒ 不算 CAUGHT：%s" % (arm_id, executed, skipped, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s（失败 %d）" % (arm_id, filt, why, failures), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R196_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
