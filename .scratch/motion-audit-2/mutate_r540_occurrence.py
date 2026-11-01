#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R540 变异表：627 出现率读数把 skip 当执行（M1419）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
FILE = "scripts/motion_red_occurrence.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
OLD = '        if st == "skipped" and fold == "ABSENT":\n            fold = "SKIP"'
NEW = '        if st == "skipped" and fold == "ABSENT":\n            fold = "PASS"'
TEST = ("scripts.tests.test_motion_red_occurrence.MotionRedOccurrenceTests."
        "test_fold_skip_is_not_executed_and_red_beats_pass")


def run():
    proc = subprocess.run([sys.executable, "-m", "unittest", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=600)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "PASSED", out
    return ("CAUGHT" if "FAILED (" in out else "ERROR"), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print("预检:", code)
    if code != "PASSED":
        print(out[-500:])
        return 2
    if text.count(OLD) != 1:
        print("needle", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print("M1419:", code)
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-500:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
