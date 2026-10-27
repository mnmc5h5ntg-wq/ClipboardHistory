#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R417 变异对照：暂停状态的图标/墨档/动作必须由 StatePresentation 唯一决定。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
STATE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/StatePresentation.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PURE = "PauseBannerTests/testPausedStateHasItsOwnPresentation"

ACTION_NEEDLE = '        case .paused: return provided ?? "继续记录"\n'
ACTION_MUTANT = '        case .paused: return provided ?? "知道了"\n'
SYMBOL_NEEDLE = '        case .paused: return "pause.circle.fill"\n'
SYMBOL_MUTANT = '        case .paused: return "exclamationmark.triangle.fill"\n'
INK_NEEDLE = """        case .warning, .error, .paused: return .prominent
        case .loading, .empty: return .subdued
"""
INK_MUTANT = """        case .warning, .error: return .prominent
        case .loading, .empty, .paused: return .subdued
"""

MUTATIONS = [
    ("M1093", "暂停动作退回「知道了」（纯判据）", STATE, ACTION_NEEDLE, ACTION_MUTANT,
     PURE, ["继续记录"]),
    ("M1094", "暂停状态借用警告图标（纯判据）", STATE, SYMBOL_NEEDLE, SYMBOL_MUTANT,
     PURE, ["pause.circle.fill"]),
    ("M1095", "暂停那句落在 subdued 档（纯判据）", STATE, INK_NEEDLE, INK_MUTANT,
     PURE, ["prominent"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r417-mut2-shots-")
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
    original = read(STATE)
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
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))

    clean = read(STATE) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R417_STATE_PAUSED_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
