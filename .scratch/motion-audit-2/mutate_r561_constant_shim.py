#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R561 变异表 M1459：把像素判据里的 `SolidRuler` 换成**等价的写死常数** ⇒ 契约钉子必须红。

这一把专门钉"钉子有没有牙"：换成的常数（30 / 8 / 25 / 36 / true）在本机 2x 上与派生值
**判定结果完全相同**（实测 `格色=8 图例色=5 缺=[]` 不变）⇒ 像素判据不会红，
只有真值表里那条"函数体必须出现 `SolidRuler(`"的契约钉子红。
这正是 R560 M1455 那把空刀的反面教材用法：**先确认读数不变、钉子单独红**，才登记它。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testLegendSolidRulerFloorsAreDerivedFromGeometry"
ARM = "M1459"
OLD = "            let ruler = Self.SolidRuler(cellW: cellW)"
NEW = ("            let ruler = (cellSolid: max(4, cellW * 3 / 5), swatchSolid: max(3, cellW / 4),\n"
       "                           cellPositions: 25, legendPositions: 36,\n"
       "                           cellFloor: 30, legendFloor: 8, resolvable: true)")


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
