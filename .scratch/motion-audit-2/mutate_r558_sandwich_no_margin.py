#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R558 变异表 M1447：夹逼计数**摘掉余量**（只要离两端都非零就算过程帧）

坏法：`dBefore >= margin && dAfter >= margin` 改成 `dBefore > 0 && dAfter > 0`。
真胶片里满是抗锯齿与光标闪烁，这种写法会把它们全数成「在动」⇒ 判据恒绿。
合成真值表里那一臂「只离前态 1/255」必须被数出来变多 ⇒ 这一格必须红。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MotionFilmstripTests/testSandwichCountJudgesInterpolationNotSamplingPhase"
OLD = """            if dBefore >= margin && dAfter >= margin { count += 1 }"""
NEW = """            if dBefore > 0 && dAfter > 0 { count += 1 }"""


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
    print("M1447:", code)
    for line in out.splitlines():
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:190])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
