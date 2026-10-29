#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R478 变异表：文件兜底态的父目录路径（M1300–M1301）。

产品：`DetailFileView.fallbackView` 在文件名下补一行父目录（长路径中间截断）。
判据 `testFallbackFileShowsWhereTheFileLives` 读同一张帧：图标带下方最宽一行 ≥90pt。
旧形状最宽行是文件名本身（约 60pt）。

  M1300 产品：整段删掉（路径不画）⇒ 判据必须红
  M1301 产品：路径置空串（占位但不画字）⇒ 判据必须红

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r478_fallback_path.py
"""
import os, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = "Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "UICaptureTests/testFallbackFileShowsWhereTheFileLives"
PATH_TEXT = "                Text(fallbackParentPathForCapture\n                     ?? preview.url.deletingLastPathComponent().path)"

ARMS = [
    ("M1300", "产品：删掉父目录那一行 ⇒ 判据必须红", VIEW,
     PATH_TEXT, "                EmptyView()", TEST, "CAUGHT"),
    ("M1301", "产品：父目录置空串 ⇒ 判据必须红", VIEW,
     PATH_TEXT, '                Text("")', TEST, "CAUGHT"),
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
    for mid, _d, _p, old, _n, _t, _e in ARMS:
        if original.count(old) != 1:
            print("PREFLIGHT_FAILED %s needle=%d" % (mid, original.count(old))); return 2
    code, out = run(TEST)
    print("预检:", code)
    if code != "PASSED":
        print(out[-1000:]); return 2
    results = []
    for mid, desc, _p, old, new, _t, expect in ARMS:
        open(path, "w", encoding="utf-8").write(original.replace(old, new))
        try:
            code, out = run(TEST)
        finally:
            open(path, "w", encoding="utf-8").write(original)
        err = next((l.strip()[:220] for l in out.splitlines() if "error:" in l), "")
        results.append((mid, code, expect, err))
        print("%s: %s 期望 %s｜%s" % (mid, code, expect, err))
    clean = open(path, "rb").read() == original.encode("utf-8")
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    ok = all(v == e for _, v, e, _ in results) and clean
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
