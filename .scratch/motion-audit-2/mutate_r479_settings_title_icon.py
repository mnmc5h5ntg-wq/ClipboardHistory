#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R479 变异表：设置页标题图标（M1302–M1303）。

产品：`SettingsPageTitle` 在标题左侧画侧栏同一枚图标；捕获缝 `settingsPageTitleIconForCapture`
只给负向帧用。判据 `testSettingsPageTitlesCarryTheCategoryIcon` 读标题行末墨列（+52px）。

  M1302 产品：条件恒 false（永不画）⇒ 判据必须红
  M1303 产品：条件恒 true（负向帧也画）⇒ 判据必须红（两臂末列差 0）
"""
import os, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testSettingsPageTitlesCarryTheCategoryIcon"
COND = "            if pageTitleIconForCapture ?? true {"
ARMS = [
    ("M1302", "条件恒 false（标题图标永不画）⇒ 判据必须红", VIEW,
     COND, "            if false {", TEST, "CAUGHT"),
    ("M1303", "条件恒 true（负向帧也画）⇒ 判据必须红", VIEW,
     COND, "            if true {", TEST, "CAUGHT"),
]
PREFLIGHT = [(TEST, "PASSED")]


def run(f):
    p = subprocess.run(["swift", "test", "--filter", f], cwd=ROOT,
                       capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = p.stdout + p.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and
                ("passed" in l or " failed" in l or "skipped" in l)]
    if not verdicts:
        return "DID-NOT-RUN", out
    if any(" failed" in l for l in verdicts):
        return "CAUGHT", out
    return "PASSED", out


def main():
    path = os.path.join(ROOT, VIEW)
    original = open(path, encoding="utf-8").read()
    if original.count(COND) != 1:
        print("PREFLIGHT_FAILED cond=%d" % original.count(COND)); return 2
    code, out = run(TEST)
    print("预检:", code)
    if code != "PASSED":
        print(out[-800:]); return 2
    results = []
    for mid, desc, _p, _old, new, _t, _e in [(a[0], a[1], a[2], a[3], a[4], a[5], a[6]) for a in ARMS]:
        open(path, "w", encoding="utf-8").write(original.replace(COND, new))
        try:
            code, out = run(TEST)
        finally:
            open(path, "w", encoding="utf-8").write(original)
        err = next((l.strip()[:200] for l in out.splitlines() if "error:" in l), "")
        results.append((mid, code, err)); print("%s: %s｜%s" % (mid, code, err))
    clean = open(path, "rb").read() == original.encode("utf-8")
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    return 0 if clean and all(v == "CAUGHT" for _, v, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
