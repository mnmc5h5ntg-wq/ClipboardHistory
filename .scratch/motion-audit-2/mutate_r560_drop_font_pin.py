#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R560 变异表 M1454：把任务标记的字体钉撤掉 ⇒ 两态又回到两份字体，判据必须红。

这一把复现的是**改动前的旧形状**（`☑` 走系统字体、`☐` 被 AppKit 换到 Apple Symbols，
框子实测 21×20 vs 16×16）。它不红就说明那条钉是装饰，不是门。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testTaskCheckboxStatesShareOneGlyphSize"
ARM = "M1454"
OLD = """        guard case let .unorderedItem(_, task) = block.kind, task != nil else { return base }
        return NSFont(name: taskMarkerFontName, size: base.pointSize) ?? base"""
NEW = """        return base"""


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r560-knife-shots"
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
        if "TASK_BOX" in line:
            print(u"  读数:", line.strip()[:240])
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
