#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R413 变异对照：跨视口长跳的滚动到位动画必须真的从计划走到 AppKit bounds。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
REVEALER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SelectedRowRevealer.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

PURE_MOTION = "SelectedRowRevealTests/testSelectionRevealMotionTruthTable"
PRODUCT_TIME = "SelectionRevealAnimationTests/testProductDurationRevealStillMovesOverTime"
SLOW_FRAME = "SelectionRevealAnimationTests/testAnimatedRevealProducesIntermediateOffsets"

PLAN_NEEDLE = "        return Plan(isAnimated: true, duration: MotionCatalog.duration(for: .slider))\n"
PLAN_MUTANT = "        return Plan(isAnimated: false, duration: 0)\n"
REDUCE_NEEDLE = "        guard !reduceMotion, viewportHeight > 0, distance > viewportHeight else {\n"
REDUCE_MUTANT = "        guard viewportHeight > 0, distance > viewportHeight else {\n"
DURATION_NEEDLE = "                context.duration = duration\n"
DURATION_MUTANT = "                context.duration = 0\n"
RESET_NEEDLE = "            clip.setBoundsOrigin(start)\n"
RESET_MUTANT = ""
SCROLL_CALL_NEEDLE = """            table.scrollRowToVisible(row)
            // List 的行高是物化后才定下来的：第一次滚只能拿到旧估计，目标会在 layout 后跳
            // （R413 在屏：2191 → 3211）。先 layout 再滚一次，读**物化后的**系统目标。
            table.layoutSubtreeIfNeeded()
            table.scrollRowToVisible(row)
            scroll.layoutSubtreeIfNeeded()
"""
SCROLL_CALL_MUTANT = """            // List 的行高是物化后才定下来的：第一次滚只能拿到旧估计，目标会在 layout 后跳
            // （R413 在屏：2191 → 3211）。先 layout 再滚一次，读**物化后的**系统目标。
            table.layoutSubtreeIfNeeded()
            scroll.layoutSubtreeIfNeeded()
"""

MUTATIONS = [
    ("M1070", "计划永远 instant（产品时长行为）", REVEALER, PLAN_NEEDLE, PLAN_MUTANT,
     PRODUCT_TIME, ["产品时长下没有任何中间 origin"]),
    ("M1071", "减弱动态也演（真值表）", REVEALER, REDUCE_NEEDLE, REDUCE_MUTANT,
     PURE_MOTION, ["减弱动态仍演"]),
    ("M1073", "AppKit 时长归零（慢放行为）", REVEALER, DURATION_NEEDLE, DURATION_MUTANT,
     SLOW_FRAME, ["0.15s 时已经到落点"]),
    ("M1074", "动画前不回起点（慢放行为）", REVEALER, RESET_NEEDLE, RESET_MUTANT,
     SLOW_FRAME, ["0.15s 时已经到落点"]),
    ("M1075", "不调系统滚动/物化（产品时长行为）", REVEALER, SCROLL_CALL_NEEDLE, SCROLL_CALL_MUTANT,
     PRODUCT_TIME, ["产品时长下没有任何中间 origin"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r413-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    out = proc.stdout + proc.stderr
    verdicts = [line for line in out.splitlines()
                if "Test Case" in line and ("passed" in line or " failed" in line)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in line for line in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [line.split("]")[0].replace("Test Case '-[", "")
              for line in verdicts if " failed" in line]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(REVEALER)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    filters = []
    for row in MUTATIONS:
        if row[5] not in filters:
            filters.append(row[5])
    for filter_name in filters:
        code, out, _ = run(filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检失败 %s %s\n%s" % (filter_name, code, out[-2000:]))
    print("预检 OK " + ",".join(filters))

    caught = wrong = 0
    for mid, desc, path, old, new, filter_name, needles in MUTATIONS:
        stamp = time.time() + 2
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and new in read(path)
        try:
            code, out, failed = run(filter_name)
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        readings = ([line for line in out.splitlines() if "SCROLL_REVEAL_TIME" in line]
                    + [line for line in out.splitlines() if "SCROLL_REVEAL_OFFSET" in line]
                    + [line for line in out.splitlines() if "SCROLL_REVEAL_INSTANT" in line])[-2:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(REVEALER) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R413_SCROLL_REVEAL_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
