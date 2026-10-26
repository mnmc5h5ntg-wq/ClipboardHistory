#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R389 变异对照：权重复位必须走 `resetDefaults(in:)` 那一条带动画的路。

产品位：复位九根滑杆时，按钮自己那点色变在演，滑杆却瞬移。R389 把复位收进
`withAnimation(MotionCatalog.animation(for: .slider))`，按钮与胶片都调同一个 helper。
两把刀：
  M1020 摘掉 helper 里的 `withAnimation` ⇒ 源形状守卫必须红（滑杆又瞬移）
  M1021 按钮绕过 helper 直接 `store.restoreDefaults()` ⇒ 源形状守卫必须红（产品/胶片分家）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/RecommendationWeightsView.swift")
FILTER = "testWeightsResetGoesThroughOneAnimatedPath"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE_ANIMATION = """        withAnimation(MotionCatalog.animation(for: .slider)) {
            store.restoreDefaults()
        }
"""
MUTANT_ANIMATION = """        store.restoreDefaults()
"""

NEEDLE_CALL = "                            Self.resetDefaults(in: store)\n"
MUTANT_CALL = "                            store.restoreDefaults()\n"

MUTATIONS = [
    ("M1020", "helper 摘掉 withAnimation ⇒ 滑杆瞬移", VIEW,
     NEEDLE_ANIMATION, MUTANT_ANIMATION, FILTER, ["权重复位没有走"]),
    ("M1021", "按钮绕过 helper 直接改 store ⇒ 产品/胶片分家", VIEW,
     NEEDLE_CALL, MUTANT_CALL, FILTER, ["权重复位没有走"]),
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
    clean = read(VIEW) == original
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R389_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
