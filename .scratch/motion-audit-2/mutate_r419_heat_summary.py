#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R419 变异对照：热图汇总行的数字滚动必须接 contentTransition + 自己的事务。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILM = "MotionFilmstripTests/testHeatSummaryNumberChangeIsAVisibleProcess"
SOURCE = "HeatmapSummaryTransitionTests/testSummaryUsesTheNumericTransitionAndItsOwnAnimation"

TRANSITION_NEEDLE = "                .contentTransition(.numericText())\n"
TRANSITION_MUTANT = ""
ANIMATION_NEEDLE = "                .animation(MotionCatalog.animation(for: .contentFade), value: line)\n"
ANIMATION_MUTANT = ""
CALL_NEEDLE = "                summaryText(line)\n"
CALL_MUTANT = "                Text(line)\n"

MUTATIONS = [
    # M1103 的证人只能是源守卫：删掉 numericText 之后，999→1000 的**宽度变化**仍会被
    # `.animation(value: line)` 分摊成 3 帧（胶片读得到过程，读不出"这是数字滚动还是整行重排"）。
    ("M1103", "汇总行没有数字滚动（源判据）", VIEW, TRANSITION_NEEDLE, TRANSITION_MUTANT,
     SOURCE, ["没有数字滚动"]),
    ("M1104", "数字滚动没有自己的事务（胶片判据）", VIEW, ANIMATION_NEEDLE, ANIMATION_MUTANT,
     FILM, ["汇总行数字是硬切"]),
    ("M1105", "header 绕过 summaryText（胶片判据）", VIEW, CALL_NEEDLE, CALL_MUTANT,
     FILM, ["汇总行数字是硬切"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r419-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    motion_out = tempfile.mkdtemp(prefix="r419-mut-motion-")
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = motion_out
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
        shutil.rmtree(motion_out, ignore_errors=True)
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
    original = read(VIEW)
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
        landed = old not in read(path) and (new in read(path) or new == "")
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
        readings = [line for line in out.splitlines()
                    if "MOTION_HEAT_SUMMARY" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(VIEW) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R419_HEAT_SUMMARY_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
