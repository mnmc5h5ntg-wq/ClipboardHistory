#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R385 变异对照：两颗「恢复默认」的禁用切换必须有 `.selection` 过渡驱动。

R385 的产品位：R382/R383 把「恢复默认」画成了禁用态，但默认↔动过之间是**硬切**；
给两颗按钮挂 `MotionCatalog.animation(for: .selection)`，源形状守卫
`MotionDriverTests.testResetButtonDisabledTransitionsAreDriven` 钉住
（静态帧看不到过程，过渡本身记 NOT-RUN）。

两把刀（都期望 CAUGHT）：
  M1016 删权重页的动画行 ⇒ 权重页那条断言红
  M1017 删快捷键页的动画行 ⇒ 快捷键页那条断言红
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
WEIGHTS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/RecommendationWeightsView.swift")
SETTINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
FILTER = "MotionDriverTests"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

W_NEEDLE = "                    .animation(MotionCatalog.animation(for: .selection), value: store.weights == .default)\n"
W_MUTANT = "                    // MUTANT：权重页过渡撤掉\n"
S_NEEDLE = "                .animation(MotionCatalog.animation(for: .selection), value: shortcut == settings.action.defaultShortcut)\n"
S_MUTANT = "                // MUTANT：快捷键页过渡撤掉\n"

MUTATIONS = [
    ("M1016", "删权重页恢复默认的过渡", WEIGHTS, W_NEEDLE, W_MUTANT, FILTER,
     ["权重页「恢复默认」的禁用切换没有"]),
    ("M1017", "删快捷键页恢复默认的过渡", SETTINGS, S_NEEDLE, S_MUTANT, FILTER,
     ["快捷键页「恢复默认」的禁用切换没有"]),
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
    originals = {path: read(path) for _mid, _desc, path, _old, _new, _f, _n in MUTATIONS}
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        if read(path).count(old) != 1:
            raise SystemExit("预检中止：%s 的针出现 %d 次（要 1 次）" % (mid, read(path).count(old)))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2000:]))
    print("预检 OK " + FILTER)

    results, stamp = [], time.time()
    try:
        for mid, desc, path, old, new, _filter, needles in MUTATIONS:
            stamp += 2
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(originals[path].replace(old, new, 1))
            os.utime(path, (stamp, stamp))
            landed = old not in read(path) and new in read(path)
            try:
                code, out, failed = run()
            finally:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(originals[path])
                os.utime(path, (stamp + 1, stamp + 1))
            hit = [n for n in needles if n in out]
            right = code == "CAUGHT" and bool(hit) and landed
            results.append((mid, code, right, failed))
            print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s" % (mid, desc, code, right, hit, failed))
    finally:
        for path, text in originals.items():
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
    clean = all(read(p) == originals[p] for p in originals)
    bad = [r for r in results if not r[2]]
    print("R385_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(results), sum(1 for r in results if r[1] == "CAUGHT"), len(bad),
             "yes" if clean else "NO"))
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    return 0 if (results and not bad and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())