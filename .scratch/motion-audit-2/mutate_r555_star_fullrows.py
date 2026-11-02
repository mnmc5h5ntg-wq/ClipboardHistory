#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R555 变异表 M1435：整行口径（1x 下界 6.0pt）必须会红（星形 pointSize 8→5）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testQuickPickFavoriteStarIsAtLeastEightPointsTall"
OLD = """        cell.favoriteBadge?.image = entry.isFavorite
            ? NSImage(systemSymbolName: "star.fill", accessibilityDescription: nil)?
                .withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 8, weight: .semibold))"""
NEW = OLD.replace("pointSize: 8", "pointSize: 5")
# 这条刀要红的是**整行口径**那一格（1x 下界），不是跨度那一格。
WANT_RED = "整行口径"


def verdict(out):
    """读**被计数物自己打印的结论行**（`Executed N tests, with M failures`），不靠子串猜。

    为什么不用 `" failed" in out`：swift-testing 那块会打 `✔ Test run with 0 tests in 0 suites
    passed`，而 XCTest 的 `passed (0.005 seconds)` 里也到处是子串 —— 上一版把预检读成了 CAUGHT，
    是假红（R555 实测）。
    """
    import re
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    failures = sum(int(m) for _, m in pairs)
    return "CAUGHT" if failures > 0 else "PASSED"

def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r555-knife-shots"
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", "", out
    reds = [l for l in out.splitlines() if "XCTAssertGreaterThanOrEqual failed" in l]
    hit = [l for l in reds if WANT_RED in l]
    if hit:
        code = "CAUGHT"
    elif reds:
        code = "OTHER-RED"     # 红了，但不是咬在整行口径那一格 ⇒ 这把刀没证到它要证的东西
    else:
        code = "GREEN"
    return code, reds, out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, reds, out = run()
    print("预检:", code, "（预检必须是 GREEN：不红才能开始动刀）")
    if code != "GREEN":
        print(out[-800:])
        return 2
    if text.count(OLD) != 1:
        print("needle", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, reds, out = run()
    finally:
        open(path, "wb").write(orig)
    print("M1435:", code)
    for line in reds:
        print("  红:", line.split(" : ")[-1][:150])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
