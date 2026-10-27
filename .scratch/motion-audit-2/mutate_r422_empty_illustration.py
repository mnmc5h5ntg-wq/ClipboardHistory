#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R422 变异对照：空态的插画档必须真的画叠卡，且只在「还没有记录」时接上。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
EMPTY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/EmptyStateView.swift")
SIDEBAR = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PIXEL = "UICaptureTests/testEmptyStateIllustrationReplacesTheGlyphWithTwoCards"
SOURCE = "EmptyStateIllustrationTests/testIllustrationIsWiredOnlyForTheNoHistoryEmptyState"

DRAW_NEEDLE = "                EmptyStateIllustration()\n"
DRAW_MUTANT = "                EmptyView()\n"
WIRE_NEEDLE = "                    illustration: historyStore.entries.isEmpty,\n"
WIRE_MUTANT = ""

MUTATIONS = [
    ("M1113", "插画档画空（像素判据）", EMPTY, DRAW_NEEDLE, DRAW_MUTANT,
     PIXEL, ["插画墨 0 不到字形"]),
    ("M1114", "侧栏没有传插画档（源判据）", SIDEBAR, WIRE_NEEDLE, WIRE_MUTANT,
     SOURCE, ["侧栏空态没有只在"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r422-mut-shots-")
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
    originals = {}
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        if path not in originals:
            originals[path] = read(path)
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
        original = originals[path]
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
                    if "EMPTY_STATE_ILLUSTRATION" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = all(read(p) == originals[p] for p in originals)
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R422_EMPTY_ILLUSTRATION_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
