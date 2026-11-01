#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R543 变异表：receipt 回退到 0.16 让 copy receipt 1x 掉帧（M1422）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Utilities/MotionCatalog.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MotionCatalogTests/testReceiptFadeSurvivesOneXSampling"
OLD = "        case .receipt: return 0.20"
NEW = "        case .receipt: return 0.16"


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
    print("M1422:", code)
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
