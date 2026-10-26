#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R400 变异对照：详情「原文/渲染」标签切换必须有过程，不能一帧硬换。"""
import os
import shutil
import subprocess
import tempfile
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
DETAIL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/DetailView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
BASE_ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
NEEDLE = """                    .id(title)
                    .transition(.opacity)
                    .animation(MotionCatalog.animation(for: .contentFade), value: title)"""
MUTANT = """                    // MUTANT: 标签过渡被拆"""
FILTER = "MotionFilmstripTests/testMarkdownModeLabelChangeIsAVisibleProcess"
MUTATIONS = [
    ("M1042", "原文/渲染标签退回一帧硬换", DETAIL, NEEDLE, MUTANT, FILTER,
     ["按钮标签是硬切"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run():
    shots = tempfile.mkdtemp(prefix="r400-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT,
                              capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in l for l in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(DETAIL)
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
    clean = read(DETAIL) == original
    code2, out2, _ = run()
    print("还原后复跑：" + code2)
    print("R400_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
