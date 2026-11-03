#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 变异表 M1473：在 `make_info_plist.sh` 里写死一个绝对根 ⇒ 守卫必须红（非 .py 那一支）。这一把钉的是：上一版扫描器只会 `ast.parse`，喂给它 shell 就报 parse-error —— CI 真跑的 `.sh` 完全在尺外。

刀的对象是 R565 补段 C 的统一卫生守卫 `scripts/ci_channel_hygiene.py`
（同族两次事故：R564 的绝对根打死 runner 的 STEP[9]、R565 的通道裸空格打死判它的测试）。
跑的是 python 那一条模块，不是 swift 卷 ⇒ 可以与别的卷并行。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = "scripts/make_info_plist.sh"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_ci_channel_hygiene"
ARM = "M1473"
OLD = 'set -eu'
NEW = 'set -eu\nREPO="/Users/wangziyi/Codex_Project0"'


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
        if "AssertionError" in line or "FAIL:" in line or "CI_CHANNEL_HYGIENE " in line:
            print("  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
