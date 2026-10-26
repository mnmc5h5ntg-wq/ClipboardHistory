#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R394 变异对照：复制失败那一颗必须变成错误红，成功态不许沾红。

产品位：失败态原来只换图标不换色；R394 用动态错误红（亮 Color.red / 暗 1.0,0.48,0.44）。
两把刀：
  M1029 失败色退回 primary ⇒ 失败态红像素 0
  M1030 成功态也涂红 ⇒ 成功态红像素 >0（负半）
"""
import os
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
GLASS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/GlassControls.swift")
FILTER = "testCopyFailurePillTurnsRedAndSuccessDoesNot"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE_COLOR = """                            foregroundStyle: copyFailed
                                ? AnyShapeStyle(colorScheme == .dark
                                    ? Color(red: 1.0, green: 0.48, blue: 0.44)
                                    : Color.red)
                                : AnyShapeStyle(.primary),
"""
MUTANT_NO_RED = """                            foregroundStyle: AnyShapeStyle(.primary),
"""
MUTANT_ALWAYS_RED = """                            foregroundStyle: AnyShapeStyle(Color.red),
"""

MUTATIONS = [
    ("M1029", "失败色退回 primary", GLASS, NEEDLE_COLOR, MUTANT_NO_RED, FILTER,
     ["失败态只有"]),
    ("M1030", "成功态也涂红", GLASS, NEEDLE_COLOR, MUTANT_ALWAYS_RED, FILTER,
     ["成功态读到"]),
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
    original = read(GLASS)
    for mid, _desc, path, old, new, _filter, _needles in MUTATIONS:
        if read(path).count(old) != 1:
            raise SystemExit("预检中止：%s 的针出现 %d 次（要 1 次）" % (mid, read(path).count(old)))
        if old in new:
            raise SystemExit("预检中止：%s 的变异文包含原文" % mid)
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2000:]))
    print("预检 OK " + FILTER)

    caught = 0
    wrong = 0
    for mid, desc, path, old, new, _filter, needles in MUTATIONS:
        stamp = time.time() + 2
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and new in read(path)
        try:
            code, out, failed = run()
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))
    clean = read(GLASS) == original
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R394_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
