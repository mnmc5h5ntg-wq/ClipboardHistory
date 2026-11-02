#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R559 变异表 M1450：把图例**退回四块**（摘掉新补的零次档那一块）⇒ 包含判据必须红。

钉的是"图例里有五种颜色"这一半：判据数的是「网格画出来的每一种颜色，图例带里必须查得到」。
如果它只数了方块个数（5 个）而没数颜色身份，这一把会绿 —— 那是空刀，所以先看它红不红。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testHeatmapLegendCoversEveryCellColor"
ARM = "M1450"
OLD = """                VisualShape.rounded(VisualRadius.heatCell)
                    .fill(Color.primary.opacity(VisualHeat.empty))
                    .frame(width: VisualHeat.cell - 3, height: VisualHeat.cell - 3)
"""
NEW = ""


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r559-knife-shots"
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
        if "HEAT_LEGEND_COVERAGE" in line:
            print(u"  读数:", line.strip()[:220])
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:200])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
