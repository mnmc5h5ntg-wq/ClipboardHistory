#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R559 变异表 M1451：图例那一块**数量对、颜色错**（零次档画成浅蓝而不是灰）⇒ 包含判据必须红。

为什么 M1450 不够：那一把只证"少一块会红"。若判据其实是在数方块个数，
这一块换成别的颜色它照样绿 —— 而产品上的说法是"图例查得到每一种格色"，**颜色身份**才是那条契约。
这一把把颜色换掉而数量不动（仍是 5 块），红才说明判据看的是颜色。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testHeatmapLegendCoversEveryCellColor"
ARM = "M1451"
OLD = """                    .fill(Color.primary.opacity(VisualHeat.empty))
                    .frame(width: VisualHeat.cell - 3, height: VisualHeat.cell - 3)"""
NEW = """                    .fill(Color.accentColor.opacity(VisualHeat.empty))
                    .frame(width: VisualHeat.cell - 3, height: VisualHeat.cell - 3)"""


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
