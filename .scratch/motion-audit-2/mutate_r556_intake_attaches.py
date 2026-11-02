#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R556 变异表 M1440：采集那一步又去补行内缩略图（632 的原形回到 add）"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "FileThumbnailTests/testAddDoesNotReadTheFileWhileRowDisplayRequestsIt"
OLD = """        // 现在由行真正显示时按需请求（见 `HistorySidebarView.historyRow` 的 `.task`）。"""
NEW = """        // 现在由行真正显示时按需请求（见 `HistorySidebarView.historyRow` 的 `.task`）。
        requestThumbnail(for: entry.id)"""


def verdict(out):
    u"""只抄被计数物自己打的结论行（`Executed N tests, with M failures`）。"""
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r556-knife-shots"
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
    print("M1440:", code)
    for line in out.splitlines():
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:170])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
