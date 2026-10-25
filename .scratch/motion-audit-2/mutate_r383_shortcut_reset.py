#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R383 变异对照：快捷键页三颗「恢复默认」在快捷键已是默认值时必须画成禁用态。

R383 的缺陷是两态整页渲染读出来的：默认值页与「第一行改成 ⌃⌥⇧V」页里，右列按钮标签墨**完全相同**
（修前 light 3792/211 对 3792/211、dark 4152/186 对 4152/186）；加
`.disabled(shortcut == settings.action.defaultShortcut)` 后 light 70 对 211、dark 60 对 186。

一把刀（期望 CAUGHT）：
  M1014 把该行 `.disabled(...)` 换成 `.disabled(false)` ⇒ 两页又变成同一颗按钮，新判据必须红。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
FILTER = "testShortcutResetButtonsAreDisabledWhenShortcutsAreDefault"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE = "                .disabled(shortcut == settings.action.defaultShortcut)"
MUTANT = "                .disabled(false)"

MUTATIONS = [
    ("M1014", "把快捷键页恢复默认的禁用条件换成恒 false", VIEW,
     NEEDLE, MUTANT, FILTER, ["禁用态"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT,
                          capture_output=True, text=True, env=BASE_ENV, timeout=900)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in l for l in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(VIEW)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        if read(path).count(old) != 1:
            raise SystemExit("预检中止：%s 的针出现 %d 次（要 1 次）" % (mid, read(path).count(old)))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2000:]))
    print("预检 OK " + FILTER)

    stamp = time.time() + 2
    with open(VIEW, "w", encoding="utf-8") as handle:
        handle.write(original.replace(NEEDLE, MUTANT, 1))
    os.utime(VIEW, (stamp, stamp))
    landed = NEEDLE not in read(VIEW) and MUTANT in read(VIEW)
    try:
        code, out, failed = run()
    finally:
        with open(VIEW, "w", encoding="utf-8") as handle:
            handle.write(original)
        os.utime(VIEW, (stamp + 1, stamp + 1))
    hit = "禁用态" in out
    right = code == "CAUGHT" and hit and landed
    clean = read(VIEW) == original
    print("M1014 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
          % (code, right, hit, failed, clean))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R383_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (1 if code == "CAUGHT" else 0, 0 if right else 1, "yes" if clean else "NO"))
    return 0 if (right and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())