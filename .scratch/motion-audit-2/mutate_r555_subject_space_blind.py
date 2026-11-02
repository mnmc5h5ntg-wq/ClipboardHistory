#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R555 变异表 M1439：把 SUBJECT 的中段退回 `(\\S+?)` ⇒ 带空格的那笔再次失明（BACKLOG 616 的退场条件）。"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
FILE = ".scratch/motion-audit-2/review_round_claims.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
OLD = u'SUBJECT = re.compile(u"^R(\\\\d{2,4})(?: (.+?))?（.*?产品 (\\\\d+) 文件")'
NEW = u'SUBJECT = re.compile(u"^R(\\\\d{2,4})(?: (\\\\S+?))?（.*?产品 (\\\\d+) 文件")'
TEST = ("scripts.tests.test_round_claim_consistency.RoundClaimConsistency."
        "test_positive_control_names_a_contradiction_and_an_unparsed_subject")


def run():
    proc = subprocess.run([sys.executable, "-m", "unittest", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=900)
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
    print("M1439:", code)
    for line in out.splitlines():
        if "AssertionError" in line:
            print(u"  红:", line.strip()[:170])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
