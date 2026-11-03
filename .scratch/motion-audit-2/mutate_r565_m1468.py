#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 变异表 M1468：把 `commit_round_identity.py` 的仓库根改回写死的机器绝对路径 ⇒ 守卫必须红（点名文件与行号）。这一把钉的是：守卫真的在扫树，不是只靠正对照活着。

刀的对象是 R565 补的第二支路径卫生守卫（`scripts/tests/test_frames_path_hygiene.py` 里的
MachineRootHygieneTests）—— 它抓的是 R564 那版 `commit_round_identity.py` 写死机器根、
把 runner 的 STEP[9] 打死那一族自伤。跑的是 python 电池那一条模块，不是 swift 卷。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
FILE = "scripts/commit_round_identity.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_frames_path_hygiene"
ARM = "M1468"
OLD = 'ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'
NEW = 'ROOT = "/Users/wangziyi/Codex_Project0"'


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
        if "AssertionError" in line or "FAIL:" in line:
            print("  红:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
