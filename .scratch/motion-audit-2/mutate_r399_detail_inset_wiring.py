#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R399 变异对照（DetailView.swift）：尾距策略必须真的接在预览上。"""
import os
import shutil
import subprocess
import tempfile
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
DETAIL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/DetailView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
NEEDLE = """                .padding(.trailing, DetailTypography.previewTrailingInset(forDetailWidth: detailWidth))"""
MUTANT = """                // MUTANT: 尾距被删"""
MUTATIONS = [
    ("M1040", "详情预览不接窄列尾距（源判据）", DETAIL, NEEDLE, MUTANT,
     "Round3DetailTypographyTests/testDetailViewAppliesTheNarrowDetailInset",
     ["DetailView 没有把详情列宽交给尾距策略"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r399-wire-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name], cwd=ROOT,
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
    filters = []
    for row in MUTATIONS:
        if row[5] not in filters:
            filters.append(row[5])
    for name in filters:
        code, out, _ = run(name)
        if code != "ESCAPED":
            raise SystemExit("预检失败：%s %s\n%s" % (name, code, out[-2000:]))
    print("预检 OK " + ",".join(filters))
    caught = 0
    wrong = 0
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
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))
    clean = read(DETAIL) == original
    reruns = []
    for name in filters:
        code2, out2, _ = run(name)
        reruns.append("%s=%s" % (name, code2))
    print("还原后复跑：" + " ".join(reruns))
    print("R399_WIRING_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(s.endswith("=ESCAPED") for s in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
