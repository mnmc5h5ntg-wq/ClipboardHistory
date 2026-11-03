#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 变异表 M1469：让根常量扫描器"看见但不报" ⇒ 正对照那一格必须红。

刀的对象是 R565 补的第二支路径卫生守卫（`scripts/tests/test_frames_path_hygiene.py` 里的
MachineRootHygieneTests）。这一把钉的是：当"真扫"那一格零命中时，必须还有东西能证明尺没坏
（R490 那一族：正对照缺席 = 假绿）。跑的是 python 电池那一条模块，不是 swift 卷。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
FILE = "scripts/tests/test_frames_path_hygiene.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_frames_path_hygiene"
ARM = "M1469"
OLD = "        if ROOT_CONST_RE.search(line):"
NEW = "        if False:"


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
