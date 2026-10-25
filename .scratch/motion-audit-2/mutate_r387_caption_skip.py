#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R387 变异对照：BACKLOG 435 的 skip 出口必须有负半证人 —— 尺坏了必须红。

R387 的量法把 caption 的「探针列 0 墨」拆成三种：有墨（判）/ 页也 0 墨（机器画不出，NOT-RUN）/
页有墨而列没有（框搬走了/尺坏了，必须红）。真值表 `testCaptionDrawabilityHasANegativeHalf`
钉住负半；本表用刀把 `.rulerBroken` 换回 `.machineFlat`，真值表必须红。

一把刀（期望 CAUGHT）：
  M1018 `return pagePixels >= pageFloor ? .rulerBroken : .machineFlat` → `return .machineFlat`
        ⇒ 页有墨、列无墨也被 skip 吞掉，负半那一格必须红。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
FILTER = "UICaptureTests/testCaptionDrawabilityHasANegativeHalf"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE = "        return pagePixels >= pageFloor ? .rulerBroken : .machineFlat\n"
MUTANT = "        return .machineFlat  // MUTANT：尺坏了也 skip\n"

MUTATIONS = [
    ("M1018", "skip 吞红：rulerBroken 退回 machineFlat", HARNESS,
     NEEDLE, MUTANT, FILTER, ["页有墨而探针列没有"]),
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
    original = read(HARNESS)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        if read(path).count(old) != 1:
            raise SystemExit("预检中止：%s 的针出现 %d 次（要 1 次）" % (mid, read(path).count(old)))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2000:]))
    print("预检 OK " + FILTER)

    stamp = time.time() + 2
    with open(HARNESS, "w", encoding="utf-8") as handle:
        handle.write(original.replace(NEEDLE, MUTANT, 1))
    os.utime(HARNESS, (stamp, stamp))
    landed = NEEDLE not in read(HARNESS) and MUTANT in read(HARNESS)
    try:
        code, out, failed = run()
    finally:
        with open(HARNESS, "w", encoding="utf-8") as handle:
            handle.write(original)
        os.utime(HARNESS, (stamp + 1, stamp + 1))
    hit = "页有墨而探针列没有" in out
    right = code == "CAUGHT" and hit and landed
    clean = read(HARNESS) == original
    print("M1018 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
          % (code, right, hit, failed, clean))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R387_CAPTION_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (1 if code == "CAUGHT" else 0, 0 if right else 1, "yes" if clean else "NO"))
    return 0 if (right and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())