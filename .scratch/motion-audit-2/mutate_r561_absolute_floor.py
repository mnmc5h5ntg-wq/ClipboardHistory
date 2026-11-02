#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R561 变异表 M1457：把图例地板退回**绝对常数 8** ⇒ 几何真值表必须红。

这正是 R559 那版的形状（`minHits: 8`）。它在本机 2x 上看不出问题，
到 runner 的 1x 上就把五档读到两档 ⇒ 报「缺三种」的假红。
登记前自检（R560 那把 Menlo 空刀的教训）：变化量 = 8 vs 派生值 4（1x 臂）与 18（2x 臂），
两臂都远在容差之外 ⇒ 不是空刀。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testLegendSolidRulerFloorsAreDerivedFromGeometry"
ARM = "M1457"
OLD = "        var legendFloor: Int { max(2, legendPositions / 2) }"
NEW = "        var legendFloor: Int { 8 }"


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
