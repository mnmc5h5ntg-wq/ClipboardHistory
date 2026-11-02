#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R564 变异表 M1463：把「前缀 vs 第 N 轮」这条一致性判据摘掉（= 只印不判）⇒ 真值表里那条 64d3192 形状的对照必须不再红。这一把钉的是：守卫真的在算那个减法，而不是靠别的格子蒙对。

刀的对象是 R564 新落的 `scripts/commit_round_identity.py`（commit subject 前缀与轮次身份行的
只管未来的一致性守卫）。跑的是 python 电池那一条模块，不是 swift 卷 —— 与 R544 的 M1423 同形。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
FILE = "scripts/commit_round_identity.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_commit_round_identity"
ARM = "M1463"
OLD = '        if seen != declared - 1:'
NEW = '        if False:'


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
        if "AssertionError" in line or "COMMIT_ROUND_IDENTITY" in line:
            print("  红:", line.strip()[:200])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
