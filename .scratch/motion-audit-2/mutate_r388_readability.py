#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R388 变异对照：禁用「恢复默认」的标签必须停在可读的 secondary（对比 ≥2.2）。

R388 的产品位：R387 的 wrapper opacity 把禁用标签压到 1.88（比系统 disabled 的 2.9 更淡），
修复是让 `ResetDefaultButtonStyle` 自己画 primary↔secondary（现读亮 2.77 / 暗 4.21），
并在 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault` 里加 2.2 的地板。
M1019 把样式的禁用前景从 `.secondary` 换回 `.tertiary` ⇒ 地板必须红。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
STYLE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/PressableStyle.swift")
FILTER = "testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE = "            .foregroundStyle(isEnabled ? AnyShapeStyle(.primary) : AnyShapeStyle(.secondary))\n"
MUTANT = "            .foregroundStyle(isEnabled ? AnyShapeStyle(.primary) : AnyShapeStyle(.tertiary))  // MUTANT\n"

MUTATIONS = [
    ("M1019", "禁用标签退回 tertiary（比 secondary 更淡）", STYLE,
     NEEDLE, MUTANT, FILTER, ["禁用态标签对填充只有"]),
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
    original = read(STYLE)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        if read(path).count(old) != 1:
            raise SystemExit("预检中止：%s 的针出现 %d 次（要 1 次）" % (mid, read(path).count(old)))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2000:]))
    print("预检 OK " + FILTER)

    stamp = time.time() + 2
    with open(STYLE, "w", encoding="utf-8") as handle:
        handle.write(original.replace(NEEDLE, MUTANT, 1))
    os.utime(STYLE, (stamp, stamp))
    landed = NEEDLE not in read(STYLE) and MUTANT in read(STYLE)
    try:
        code, out, failed = run()
    finally:
        with open(STYLE, "w", encoding="utf-8") as handle:
            handle.write(original)
        os.utime(STYLE, (stamp + 1, stamp + 1))
    hit = "禁用态标签对填充只有" in out
    right = code == "CAUGHT" and hit and landed
    clean = read(STYLE) == original
    print("M1019 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s" % (code, right, hit, failed, clean))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R388_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (1 if code == "CAUGHT" else 0, 0 if right else 1, "yes" if clean else "NO"))
    return 0 if (right and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())