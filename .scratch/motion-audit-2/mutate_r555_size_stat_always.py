#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R555 变异表 M1437：把「样本读满才探大小」的条件拿掉 ⇒ 小文件也白 stat 一次路径。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/DetailView.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "ProtectedFileAccessTests/testHeightEstimateSkipsTheSizeStatWhenTheSampleIsWhole"
OLD = "        if data.count >= textSampleLimit {"
NEW = "        if data.count >= 0 {"


def verdict(out):
    """读**被计数物自己打印的结论行**（`Executed N tests, with M failures`），不靠子串猜。

    为什么不用 `" failed" in out`：swift-testing 那块会打 `✔ Test run with 0 tests in 0 suites
    passed`，而 XCTest 的 `passed (0.005 seconds)` 里也到处是子串 —— 上一版把预检读成了 CAUGHT，
    是假红（R555 实测）。
    """
    import re
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    failures = sum(int(m) for _, m in pairs)
    return "CAUGHT" if failures > 0 else "PASSED"

def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r555-knife-shots"
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
    print("M1437:", code)
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
