#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R562 变异表 M1462：把正文列的合并容差从 0.5pt 抬到 20pt ⇒ 三个正文列塌成两列 ⇒ 列数断言必须红。

这一把钉的是「列数不是聚类的产物」：判据把六行的正文左沿按 `merge` 合并成"级"，
如果合并窗口被抬到能把相邻两级并成一列，`columns.count == parsedDepths.count` 必须红 ——
否则"数到三级"这句话就只是聚类参数说的一句话，不是帧上的一句话。

⚠ 同一格的**第一版是空刀**（已撤，不登记）：那版把「项目符宽度 ≤8pt」这道筛抬到 40pt，
读数逐字不变（行=6 列=3）。原因是窗口工具栏那一行在 y=73..93px，而判据从 `60pt×scale`=120px
才开始扫 ⇒ 它是被 **y 窗口**筛掉的，不是被宽度筛掉的 ⇒ 宽度这道筛在当前帧上是冗余的。
登记前自检（④）抓到的正是这种"改了筛子但读数不动"。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
TEST = "UICaptureTests/testNestedBulletLevelsKeepOneUniformTextColumn"
ARM = "M1462"
OLD = "            let merge = max(1, Int((0.5 * scale).rounded()))"
NEW = "            let merge = max(1, Int((20.0 * scale).rounded()))"


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r562-knife-shots"
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
    print(ARM + ":", code)
    for line in out.splitlines():
        if ("XCTAssert" in line and "failed" in line) or line.startswith("BULLET_LEVELS"):
            print(u"  ", line.strip()[:240])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
