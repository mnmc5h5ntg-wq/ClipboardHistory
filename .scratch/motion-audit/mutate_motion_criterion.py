#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异 M8（R5）：把侧栏空态的**驱动**摘掉，新的时长判据必须当场打红。

为什么这一支比"改阈值"重要：R5 换判据的理由是"帧数跟着采样相位翻脸"，
而换判据之后最容易犯的错是把它换成一条**永远绿**的判据。
唯一能证伪这件事的是：产品真的不动了，它必须红。
"""
import os, shutil, subprocess, sys

REPO = "/Users/wangziyi/Codex_Project0"
TARGET = os.path.join(REPO, "ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
NEEDLE = ".animation(MotionCatalog.animation(for: .contentFade), value: historyStore.filteredEntries.isEmpty)"
TEST = "MotionFilmstripTests/testTransitionsAreActuallyRunning"
RED_MARK = "这是一帧跳变，不是过渡"


def run_test():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    # 这条判据是**门控**的（不开环境变量就整条 skip）。忘了设它，`swift test` 会
    # 照样打出"0 failures"——那是"没跑"，不是"没抓到"。分类器必须把这两种分开。
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r5-m8"
    proc = subprocess.Popen(["swift", "test", "--filter", TEST],
                            cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return proc.returncode, out


def main():
    original = open(TARGET, encoding="utf-8").read()
    backup = "/tmp/sidebar_before_m8.swift"
    shutil.copy2(TARGET, backup)
    if NEEDLE not in original:
        print("M8: DID-NOT-RUN=anchor-missing")
        return 2
    code, out = run_test()
    if "0 failures" not in out or "tests skipped" in out:
        print("M8: DID-NOT-RUN=baseline-not-green-or-skipped")
        print(out[-1200:])
        return 2
    print("BASELINE=green")

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(original.replace(NEEDLE, "// MUTANT M8: 驱动摘掉", 1))
    code, out = run_test()
    if RED_MARK in out:
        verdict = "CAUGHT"
    elif "tests skipped" in out and "Executed 1 test" in out:
        verdict = "DID-NOT-RUN=skipped"
    elif "0 failures" in out:
        verdict = "ESCAPED"
    elif "error:" in out and "Build complete" not in out:
        verdict = "DID-NOT-RUN=build-failed"
    else:
        verdict = "AMBIGUOUS"
    for line in out.splitlines():
        if line.startswith("MOTION empty-state") or line.startswith("MOTION_NOT_RUN") or line.startswith("MOTION_RESOLVE"):
            print("  " + line[:200])
    print("M8-sidebar-driver-removed: %s" % verdict)
    shutil.copy2(backup, TARGET)
    print("RESTORED=%s" % (open(TARGET, encoding="utf-8").read() == original))
    return 0 if verdict == "CAUGHT" else 1


if __name__ == "__main__":
    sys.exit(main())
