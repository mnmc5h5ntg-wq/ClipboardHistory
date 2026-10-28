#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R475 的变异表：图片行「可搜索文字」标记（M1291–M1292）。

产品位在 `HistoryRowViews.RowTextColumn`：`entry.ocrText` 非空时，时间行末尾画一枚
`text.viewfinder`。判据 `testImageRowsCarryASearchableBadgeWhenOCRLanded` 用成对帧
（row-image 负臂 / row-image-ocr 正臂）读最后墨列与墨量差。

  M1291 产品：条件改成恒 false（标记不画）⇒ 判据必须红（末列差 0、墨差 0）
  M1292 产品：条件改成恒 true（每行都画）⇒ 判据必须红（负臂也长出标记，末列差 0）
        M1292 是「不做空」那一半：只证明「删掉会红」会把"标记本来就在所有行上"当成正确。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r475_row_ocr_badge.py [M1291 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TEST = "UICaptureTests/testImageRowsCarryASearchableBadgeWhenOCRLanded"
COND = "                if entry.ocrText?.isEmpty == false {"

ARMS = [
    ("M1291", "产品：条件恒 false（标记不画）⇒ 判据必须红", VIEW,
     COND,
     "                if false {",
     TEST, "CAUGHT"),
    ("M1292", "产品：条件恒 true（每行都画）⇒ 判据必须红（负臂也长标记）", VIEW,
     COND,
     "                if true {",
     TEST, "CAUGHT"),
]

PREFLIGHT = [(TEST, "PASSED")]


def run(test_filter, timeout=2400):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True,
                          env=BASE_ENV, timeout=timeout)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        errs = [l.strip()[:200] for l in lines if "error:" in l][:4]
        return "DID-NOT-RUN", out, " || ".join(errs) or "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and
                 ("passed" in l or " failed" in l or "skipped" in l)]
    if not concluded:
        return "DID-NOT-RUN", out, "整条被跳过到没有结论行：" + (lines[-1][:200] if lines else "")
    skipped = any("skipped" in l for l in concluded)
    failed = any(" failed" in l for l in concluded)
    passed = any("passed" in l for l in concluded)
    if skipped and not failed and not passed:
        why = [l.strip()[:220] for l in out.splitlines() if "XCTSkip" in l]
        return "SKIPPED", out, (why[0] if why else "")
    if failed:
        why = [l.strip()[:300] for l in out.splitlines() if "error:" in l]
        return "CAUGHT", out, (why[0] if why else "")
    return "PASSED", out, ""


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    only = set(sys.argv[1:])
    results = []
    paths = sorted({a[2] for a in ARMS})
    originals = {p: read(p) for p in paths}
    snapshots = {p: open(os.path.join(ROOT, p), "rb").read() for p in paths}

    print("=== 预检（不注入：目标必须 PASSED）===", flush=True)
    ok = True
    for test, want in PREFLIGHT:
        verdict, out, note = run(test)
        print("  %-70s %s" % (test, verdict), flush=True)
        if verdict != want:
            ok = False
            print("      期望 %s，拿到 %s｜%s" % (want, verdict, note[:220]), flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    for mid, title, path, needle, mutant, test, expect in ARMS:
        if only and mid not in only:
            continue
        text = originals[path]
        count = text.count(needle)
        if count != 1:
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中 %d 次，期望 1 ⇒ 不注入" % count))
            print("%s: DID-NOT-RUN needle 命中 %d" % (mid, count), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, evidence = run(test)
        except subprocess.TimeoutExpired:
            verdict, evidence = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        if verdict != "DID-NOT-RUN" and read(path).find(needle) < 0:
            evidence = "回读失败：原文不在了（还原步骤坏了？）" + evidence
        note = (u"对  期望 " + expect + (u"｜" + evidence[-200:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-300:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R475 汇总（每臂按自己的期望判定）===")
    for mid, verdict, line, expect, reason in results:
        mark = "OK " if verdict == expect else "!! "
        print("  %-5s exp=%-8s got=%-12s %s%s  %s"
              % (mid, expect, verdict, mark, line, reason))
    dirty = [p for p in paths
             if open(os.path.join(ROOT, p), "rb").read() != snapshots[p]]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    good = sum(1 for _, v, _, e, _ in results if v == e)
    bad = sum(1 for _, v, _, e, r in results if v != e and r.startswith(u"!!"))
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), good, bad,
             sum(1 for _, v, _, _, _ in results if v == "DID-NOT-RUN")))
    want = len(ARMS) if not only else len(only)
    return 0 if not dirty and good == want and len(results) == want else 1


if __name__ == "__main__":
    sys.exit(main())
