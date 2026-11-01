#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R539 变异表：628 的 git 缩写钉死（M1415 / M1416）。"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PS = "scripts/product_streak.py"
HY = "scripts/tests/test_commit_subject_hygiene.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

ARMS = [
    ("M1415", "产品提交短 sha 不再钉 7 位", PS,
     u'git("log", "-%d" % limit, "--date=short", u"--abbrev=7",',
     u'git("log", "-%d" % limit, "--date=short",',
     "scripts.tests.test_product_streak_cell.ProductStreakCellTests."
     "test_shorts_are_pinned_to_seven_digits_on_an_eight_digit_runner"),
    ("M1416", "subject 扫描不再钉 7 位", HY,
     u'return [u"log", u"--abbrev=7", u"--format=%h%x00%s", sha + u"~1..HEAD"]',
     u'return [u"log", u"--format=%h%x00%s", sha + u"~1..HEAD"]',
     "scripts.tests.test_commit_subject_hygiene.CommitSubjectHygiene."
     "test_scan_is_pinned_to_seven_digits_on_an_eight_digit_runner"),
]


def run(test):
    proc = subprocess.run([sys.executable, "-m", "unittest", test], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=600)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "PASSED", out
    if "FAILED (" in out:
        return "CAUGHT", out
    return "ERROR", out


def main():
    print("PRECHECK:", ", ".join("%s=%s" % (a[0], run(a[5])[0]) for a in ARMS))
    ok = True
    for mid, why, rel, old, new, test in ARMS:
        path = os.path.join(ROOT, rel)
        orig = open(path, "rb").read()
        text = orig.decode("utf-8")
        if text.count(old) != 1:
            print("%s ANCHOR_BAD hits=%d" % (mid, text.count(old)))
            ok = False
            continue
        open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
        try:
            code, out = run(test)
        finally:
            open(path, "wb").write(orig)
        clean = open(path, "rb").read() == orig
        print("%s %s: %s RESTORE_CLEAN=%s" % (mid, why, code, "yes" if clean else "NO"))
        if code != "CAUGHT" or not clean:
            print(out[-800:])
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
