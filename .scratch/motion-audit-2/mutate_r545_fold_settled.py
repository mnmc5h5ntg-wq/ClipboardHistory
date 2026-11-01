#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R545 变异表：过渡收尾不把 foldProgress 落回 1（M1424）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MainWindowFoldMotionTests/testCollapseWidthIsMeasuredFrameByFrame"
OLD = """    private func finishTransition(on window: NSWindow) {
        stopTransition()
        foldProgress = transitionToProgress
        applyGeometry(to: window)
    }"""
NEW = """    private func finishTransition(on window: NSWindow) {
        stopTransition()
        foldProgress = transitionToProgress - 0.002
        applyGeometry(to: window)
    }"""


def run():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if " failed" in out else "PASSED"), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print("预检:", code)
    if code != "PASSED":
        print(out[-800:])
        return 2
    if text.count(OLD) != 1:
        print("needle", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print("M1424:", code)
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
