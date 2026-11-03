#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 变异表 M1466：把提示的颜色退回旧值 tertiaryLabel ⇒ 判据必须红（旧值本机现读 light 3.36:1 / dark 4.16:1，两档都跌破 4.5）。这一把钉的是：判据红的确实是**对比度**，不是别的格子。

刀的对象是 R565 的产品位（浮层键盘提示的字芯对比）与新判据
`UICaptureTests/testQuickPickKeyboardHintClearsTheContrastFloor`。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Utilities/QuickPickKeyboardHint.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testQuickPickKeyboardHintClearsTheContrastFloor"
ARM = "M1466"
OLD = '    static var color: NSColor { .secondaryLabelColor }'
NEW = '    static var color: NSColor { .tertiaryLabelColor }'


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r565-knife-shots"
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return verdict(out), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print("预检:", code)
    if code != "PASSED":
        print(out[-900:])
        return 2
    if text.count(OLD) != 1:
        print("needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print(ARM + ":", code)
    for line in out.splitlines():
        if "HINT_CONTRAST" in line:
            print("  读数:", line.strip()[:200])
        if "XCTAssert" in line and "failed" in line:
            print("  红:", line.split(" : ")[-1][:190])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
