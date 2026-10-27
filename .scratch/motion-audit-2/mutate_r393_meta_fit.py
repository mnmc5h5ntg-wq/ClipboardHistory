#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R393 变异对照：详情头部在窄窗口必须退到紧凑 meta。

产品位：600pt 窗口里完整 meta 放不下，原来的 middle 截断会把「复制」吃掉。
R393 用 `ViewThatFits` 先试完整文案，放不下再退到去掉冗余「复制」的紧凑版。
两把刀：
  M1027 把紧凑臂也写回 includeCopyVerb: true ⇒ 两臂相同，ViewThatFits 只会选完整版
  M1028 把 ViewThatFits 换成 Group ⇒ 没有「先试再退」这层
"""
import os
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
DETAIL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/DetailView.swift")
FILTER = "Round3DetailTypographyTests/testNarrowDetailHeaderFallsBackToCompactMeta"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

NEEDLE_COMPACT = """                            headerMeta(entry, includeIcon: true, includeCopyVerb: false)
                            headerMeta(entry, includeIcon: false, includeCopyVerb: true)
                            headerMeta(entry, includeIcon: false, includeCopyVerb: false)
"""
MUTANT_COMPACT = """                            headerMeta(entry, includeIcon: true, includeCopyVerb: true)
                            headerMeta(entry, includeIcon: false, includeCopyVerb: true)
                            headerMeta(entry, includeIcon: false, includeCopyVerb: true)
"""
NEEDLE_FITS = "                        ViewThatFits(in: .horizontal)"
MUTANT_FITS = "                        Group"

MUTATIONS = [
    ("M1027", "紧凑臂退回完整文案 ⇒ 两臂相同", DETAIL, NEEDLE_COMPACT, MUTANT_COMPACT, FILTER,
     ["没有紧凑版这一臂"]),
    ("M1028", "ViewThatFits 换成 Group ⇒ 没有先试再退", DETAIL, NEEDLE_FITS, MUTANT_FITS, FILTER,
     ["没有 ViewThatFits"]),
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
    print("R393_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code2 == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
