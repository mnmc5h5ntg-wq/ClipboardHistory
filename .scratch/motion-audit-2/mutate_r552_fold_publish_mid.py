#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R552 变异表：切换途中再发布一次中间进度（M1433）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MainWindowFoldMotionTests/testFoldProgressOnlyEverTakesTheTwoEndpoints"
OLD = '        isCollapsed = collapsed\n        setProgress(collapsed ? 1 : 0)'
NEW = '        isCollapsed = collapsed\n        setProgress(0.5)\n        setProgress(collapsed ? 1 : 0)'


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r552-knife-shots"
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if " failed" in out else "PASSED"), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print(u"预检:", code)
    if code != "PASSED":
        print(out[-800:])
        return 2
    if text.count(OLD) != 1:
        print(u"needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print("M1433:", code)
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
