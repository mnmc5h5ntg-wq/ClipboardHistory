#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R391 变异对照：自绘「恢复默认」的按下态只准在启用态亮。

产品位：R388 的 `ResetDefaultButtonStyle` 按下只缩 2%，底色不动。R391 加
`pressedForCapture` 取证通道 + `isEnabled` 闸门 + 填充 0.08→0.17（缩放也走同一个判定）。
两把刀：
  M1025 按下填充退回 idle（0.17→0.08）⇒ 启用态两帧差 0，像素判据必须红
  M1026 摘掉 `isEnabled &&` 闸门 ⇒ 禁用态按下也变，负半必须红
"""
import os
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
STYLE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/PressableStyle.swift")
FILTER = "testResetDefaultButtonShowsPressedOnlyWhenEnabled"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE_FILL = "isPressedForDrawing ? 0.17"
MUTANT_FILL = "isPressedForDrawing ? 0.08"
NEEDLE_GATE = "isEnabled && (configuration.isPressed"
MUTANT_GATE = "(configuration.isPressed"

MUTATIONS = [
    ("M1025", "按下填充退回 idle ⇒ 启用态看不出按下", STYLE, NEEDLE_FILL, MUTANT_FILL, FILTER,
     ["启用态按下只差"]),
    ("M1026", "摘掉 isEnabled 闸门 ⇒ 禁用态也参与按下", STYLE, NEEDLE_GATE, MUTANT_GATE, FILTER,
     ["禁用态按下也变了"]),
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
    clean = read(STYLE) == original
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R391_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
