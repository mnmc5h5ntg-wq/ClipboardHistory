#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R384 变异对照：「开机启动失败」的回执必须是错误色，不能与「本机不支持」的静态说明同色。

R384 的缺陷是看帧 + 模型查出来的：两条 message 在视图里都是 `.secondary`；
失败帧与说明帧的 message 颜色完全一样。修法给 `LoginItemSettings` 加 `lastActionFailed`，
失败回执用红色；判据 `testLoginFailureReceiptIsVisuallyDistinctFromTheUnsupportedNote`
数整帧红占优像素（失败 2370/2116，说明 0）。

一把刀（期望 CAUGHT）：
  M1015 把回执颜色改回恒 `.secondary` ⇒ 失败帧红=0，新判据必须红。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
FILTER = "testLoginFailureReceiptIsVisuallyDistinctFromTheUnsupportedNote"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE = "                                .foregroundStyle(loginItemSettings.lastActionFailed\n                                                 ? AnyShapeStyle(colorScheme == .dark\n                                                     ? Color(red: 1.0, green: 0.48, blue: 0.44)\n                                                     : Color.red)\n                                                 : AnyShapeStyle(.secondary))"
MUTANT = "                                .foregroundStyle(AnyShapeStyle(.secondary))  // R384 变异：失败也灰"

MUTATIONS = [
    ("M1015", "把失败回执的颜色改回恒 secondary", VIEW,
     NEEDLE, MUTANT, FILTER, ["它又被画成了和静态说明一样的次级灰"]),
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
    hit = "次级灰" in out
    right = code == "CAUGHT" and hit and landed
    clean = read(VIEW) == original
    print("M1015 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
          % (code, right, hit, failed, clean))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R384_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (1 if code == "CAUGHT" else 0, 0 if right else 1, "yes" if clean else "NO"))
    return 0 if (right and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())