#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R558 一次性探针（不入库、不是刀）：这条胶片的读数到底依不依赖「标签的过渡」本身。

为什么要问：M1446（摘 `.id(title)`）之后本机读数与未变异**逐字节相同**（过渡帧数 5、峰值 0.0097、
相邻差序列一致）。两种解释修法相反：①这条动效今天不靠 `.id`/`.transition` 也在演（那把尺读对了对象，
只是产品有第二条动画路径）；②这卷胶片量的根本不是标签过渡（那 (B) 落到了错的对象上）。
分岔办法：把标签的三条动画线一根根拆掉，看读数动不动。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/DetailView.swift"
TEST = "MotionFilmstripTests/testMarkdownModeLabelChangeIsAVisibleProcess"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
ENV["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r558-probe-shots"

ARMS = [
    ("A 只摘 .id(title)",
     "                    .id(title)\n", ""),
    ("B 摘 .transition(.opacity)",
     "                    .transition(.opacity)\n", ""),
    ("C 摘 .animation(value: title)",
     "                    .animation(MotionCatalog.animation(for: .contentFade), value: title)\n", ""),
    ("D 三条全摘",
     "                    .id(title)\n                    .transition(.opacity)\n                    .animation(MotionCatalog.animation(for: .contentFade), value: title)\n", ""),
]


def run_once():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=3600)
    out = proc.stdout + proc.stderr
    fails = sum(int(b) for _, b in re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out))
    ran = sum(int(a) for a, _ in re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out))
    line = ""
    for l in out.splitlines():
        if "MOTION_MARKDOWN_MODE_FADE" in l:
            line = l.strip()
            break
    return ("NOT_RUN" if ran == 0 else ("RED" if fails else "GREEN")), line


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, line = run_once()
    print(u"未变异:", code, line[:150])
    for name, old, new in ARMS:
        if text.count(old) != 1:
            print(u"%s ⇒ needle 命中 %d，跳过" % (name, text.count(old)))
            continue
        open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
        try:
            code, line2 = run_once()
        finally:
            open(path, "wb").write(orig)
        same = u"读数相同" if line2[:150] == line[:150] else u"读数变了"
        print(u"%s ⇒ %s %s ｜ %s" % (name, code, same, line2[:230]))
        clean = open(path, "rb").read() == orig
        if not clean:
            print(u"  RESTORE_DIRTY")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
