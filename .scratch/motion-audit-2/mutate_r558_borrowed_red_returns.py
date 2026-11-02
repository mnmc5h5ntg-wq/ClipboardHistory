#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R558 变异表 M1449：把内层读数**合回两种**（「内层有红」又说成「没有结论行」）

坏法：`inner_summary_verdict` 里 `failed` 那一支改回返回 `no-summary` —— 这正是 634 记的那条自伤：
观察者只认 `OK (…)` 那一种形状，被观察者的红就被记成观察者自己的缺席，
一个成因在红名册里变成两朵，还替那朵红做伪证。真值表那一格必须红。
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
FILE = "scripts/tests/test_skip_roster.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
OLD = """    if failed:
        return 'inner-red', u'、'.join(RED_NAMES.findall(text)) or u'未解析到'"""
NEW = """    if failed:
        return 'no-summary', u''"""


def verdict(out):
    u"""Python 的结论行是 `Ran N tests` + `OK`/`FAILED (…)`，两行都要抄它自己打的。"""
    ran = re.findall(r"^Ran (\d+) tests?", out, re.M)
    if not ran:
        return "DID-NOT-RUN"
    if sum(int(a) for a in ran) == 0:
        return "NOT_RUN"
    return "CAUGHT" if re.search(r"^FAILED", out, re.M) else "PASSED"


def run():
    proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover",
                           "-s", "scripts/tests", "-p", "test_skip_roster.py",
                           "-k", "three_readings", "-v"],
                          cwd=REPO, capture_output=True, text=True, env=ENV, timeout=1200)
    out = proc.stdout + proc.stderr
    if "test_inner_summary" not in out:
        return "DID-NOT-RUN", out
    return verdict(out), out


def main():
    path = os.path.join(REPO, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print(u"预检:", code)
    if code != "PASSED":
        print(out[-900:])
        return 2
    if text.count(OLD) != 1:
        print(u"needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print("M1449:", code)
    for line in out.splitlines():
        if "AssertionError" in line or "内层红却被读成" in line:
            print(u"  红:", line.strip()[:190])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
