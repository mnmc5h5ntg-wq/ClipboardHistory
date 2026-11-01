#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R539 变异表：625 的 key-view 链结构判据（M1417 / M1418）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MainWindowCollapseTests/testCollapseHintDismissButtonIsAnAppKitButtonWithFocusRingAndAction"
OLD = "        last?.nextKeyView = self"
NEW = "        _ = last"
OLD2 = "    override var canBecomeKeyView: Bool { true }"
NEW2 = "    override var canBecomeKeyView: Bool { false }"


def run():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if " failed" in out else "PASSED"), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print("预检:", code)
    if code != "PASSED":
        print(out[-800:])
        return 2
    ok = True
    for mid, old, new in (("M1417", OLD, NEW), ("M1418", OLD2, NEW2)):
        orig2 = open(path, "rb").read()
        text2 = orig2.decode("utf-8")
        if text2.count(old) != 1:
            print("%s needle=%d" % (mid, text2.count(old)))
            ok = False
            continue
        open(path, "w", encoding="utf-8").write(text2.replace(old, new, 1))
        try:
            code, out = run()
        finally:
            open(path, "wb").write(orig2)
        clean = open(path, "rb").read() == orig2
        print("%s: %s RESTORE_CLEAN=%s" % (mid, code, "yes" if clean else "NO"))
        if code != "CAUGHT" or not clean:
            print(out[-800:])
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
