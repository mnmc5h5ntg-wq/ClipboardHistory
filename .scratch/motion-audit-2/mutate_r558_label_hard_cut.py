#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R558 变异表 M1446：让标签**根本不换字**（夹具把 title 钉成常量）⇒ 新判据必须红

这一把是**负向臂**（空对账探测）：这条判据读的是「标签那一块在两个状态之间有没有中间帧」，
所以把状态差抹平成零之后，它必须说"这一卷没拍到任何交换"，不许照样绿。

为什么不是"摘掉产品的 `.id(title)`/`.transition`/`.animation`"：R558 试过，**砍不到东西** ——
四条臂（分别摘一行、三条全摘）的读数与未变异相同（过渡帧数 5、相邻差帧数 4、峰值 0.0097、
相邻差序列逐格一致，只有 窗口/每格 随时钟抖），见 `probe_r558_what_the_film_measures.py`。
⇒ 这条胶片能为"用户看到有没有中间态"签字，但**不能为那三行接线**签字；
   而现读全仓：除了这条胶片自己，**没有任何** grep/契约守卫钉着那三行
   （`grep -rl "id(title)" ClipboardHistory/Tests/` 只命中 `MotionFilmstripTests.swift`）
   ⇒ 接线那一格新开 BACKLOG 635，这一把刀只证判据不是恒绿机器。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MotionFilmstripTests/testMarkdownModeLabelChangeIsAVisibleProcess"
OLD = '''DetailView.MarkdownModeButton(title: driver.rendered ? "原文" : "渲染",'''
NEW = '''DetailView.MarkdownModeButton(title: "原文",'''


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r558-knife-shots"
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
    print("M1446:", code)
    for line in out.splitlines():
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:200])
    for line in out.splitlines():
        if "MOTION_MARKDOWN_MODE_FADE" in line:
            print(u"  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
