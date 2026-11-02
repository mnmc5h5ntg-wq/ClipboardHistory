#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R561 变异表 M1458：把「分辨不出就不判」那道门写成恒真 ⇒ 真值表第三臂必须红。

没有这道门，尺在极小倍率上会安静地给出「缺=[]」的绿（一个采样点都数不出来时，
两边都是空集 ⇒ 包含关系恒成立）。第三臂 cellW=6 钉的就是这件事：
`legendPositions` 只有 1 个 ⇒ 必须 `resolvable=false`。
登记前自检：这一改让一条断言从绿翻红（False vs 期望 False 的 XCTAssertFalse 翻成通过形状）⇒ 变化在容差之外。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testLegendSolidRulerFloorsAreDerivedFromGeometry"
ARM = "M1458"
OLD = "        var resolvable: Bool { legendPositions >= 4 }"
NEW = "        var resolvable: Bool { true }"


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=3600)
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
    print(ARM + ":", code)
    for line in out.splitlines():
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
