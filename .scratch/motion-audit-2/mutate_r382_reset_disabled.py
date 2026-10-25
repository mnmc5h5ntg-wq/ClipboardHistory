#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R382 变异对照：设置「推荐」页「恢复默认」在权重全默认时必须画成禁用态。

R382 的缺陷是看帧发现的：默认权重与动过权重的两帧里，这颗按钮的标签墨**一模一样**——
它永远可点，而默认时点了不产生任何变化。修法是 `.disabled(store.weights == .default)`；
判据 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault` 读两帧标签的最大偏离
（现读 light 62 vs 195、dark 51 vs 170）。

一把刀（期望 CAUGHT）：
  M1013 把 `.disabled(store.weights == .default)` 换成 `.disabled(false)` ⇒ 两帧又变成同一颗按钮，
        标签墨的最大偏离差掉到 20 以下，新判据必须红。

表形状与 r54 相同（`MUTATIONS` 七元组），这样 `mutate_needle_precheck.py` 与
`hidden_arms.py` 都能静态看见 M1013；R382 之前它是一支自写 main 的表，两个名册都看不见它。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/RecommendationWeightsView.swift")
FILTER = "testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE = "                    .disabled(store.weights == .default)"
MUTANT = "                    .disabled(false)"

MUTATIONS = [
    ("M1013", "把禁用条件换成恒 false（默认权重下按钮又变成永远可点）", VIEW,
     NEEDLE, MUTANT, FILTER, ["禁用态没有画出来"]),
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
    hit = "禁用态没有画出来" in out
    right = code == "CAUGHT" and hit and landed
    clean = read(VIEW) == original
    print("M1013 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
          % (code, right, hit, failed, clean))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R382_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (1 if code == "CAUGHT" else 0, 0 if right else 1, "yes" if clean else "NO"))
    return 0 if (right and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
