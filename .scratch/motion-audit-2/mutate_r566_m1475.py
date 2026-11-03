#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R566 变异表 M1475：把 adhoc 那一支的读数打印删掉 ⇒ "静默回退"必须红（R553 修的就是这个洞，不许它长回来）

刀的对象是 R566 落的那格**现读真钥匙串**的正对照
（`scripts/tests/test_sign_bundle.py::test_this_machine_actually_takes_the_identity_branch`，
它把"这台机器今天走得通哪一支"变成会红的事实 —— 上面两臂喂的是桩，答不了这句）。
跑的是 python 那一条模块，不是 swift 卷。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = "scripts/sign_bundle.sh"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_sign_bundle"
ARM = "M1475"
OLD = 'echo "SIGNATURE_KIND=adhoc"'
NEW = 'true'


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
        print(out[-900:])
        return 2
    if text.count(OLD) != 1:
        print("needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print(ARM + ":", code)
    for line in out.splitlines():
        if "AssertionError" in line or "FAIL:" in line or "SKIP" in line:
            print("  读数:", line.strip()[:200])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
