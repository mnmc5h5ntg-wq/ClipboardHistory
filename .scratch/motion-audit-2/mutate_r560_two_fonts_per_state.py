#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R560 变异表 M1455：两个态**分别**钉到两份都存在、但度量明显不同的字体 ⇒ 判据必须红。

M1454 只证"撤掉钉会红"。若判据其实是在数"两个数字碰巧相等"，那把两个态各自钉到
一份**有该字形**的字体（勾选 Apple Symbols、未勾选 Arial Unicode MS）它就可能还绿 ——
而产品上"同一个控件的两个态必须同一份字体画"这句话就丢了。
⚠ 第一版这里用的是 **Menlo**，实测是**空刀**：Menlo 的 `☐` 墨框 15×15 vs Apple Symbols 16×16，
差 1px 正好落在容差（≤1px）内 ⇒ PASSED 而不是 CAUGHT（R491 那一族：同值空刀不算刀）。
换成 Arial Unicode MS（探针 advance 9.54×18.00）才把差推到肉眼可分辨的量级。
这一格同时说明判据的契约是**像素同尺寸（≤1px = 0.5pt）**，不是"字体名字符串相同"。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testTaskCheckboxStatesShareOneGlyphSize"
ARM = "M1455"
OLD = """        guard case let .unorderedItem(_, task) = block.kind, task != nil else { return base }
        return NSFont(name: taskMarkerFontName, size: base.pointSize) ?? base"""
NEW = """        guard case let .unorderedItem(_, task) = block.kind, let state = task else { return base }
        return NSFont(name: state == .checked ? taskMarkerFontName : "Arial Unicode MS",
                      size: base.pointSize) ?? base"""


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
