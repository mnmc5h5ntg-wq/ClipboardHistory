#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R477 变异表：浮层置顶图钉（M1297–M1298）。

产品：`QuickPickController` 把「置顶」从标题文本挪到类型符号右下角的 `pin.fill` 徽标
（`pinnedBadge.isHidden = !entry.isPinned`）。判据 `testQuickPickPinnedRowsUseTheMainListPinGlyph`
用成对帧（quickpick-no-source / quickpick-pinned）读类型符号列的墨差与标题末列。

  M1297 产品：徽标永不显示（isHidden = true）⇒ 判据必须红（类型列差 0）
  M1298 产品：徽标永远显示（isHidden = false）⇒ 判据必须红（负臂也长图钉，差 0）
        M1298 是"不做空"那一半：只证明"删掉会红"会把"每行都挂图钉"当成正确。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r477_quickpick_pin.py [M1297 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SOURCE = "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TEST = "UICaptureTests/testQuickPickPinnedRowsUseTheMainListPinGlyph"
HIDE = ("        cell.pinnedBadge?.isHidden = !entry.isPinned\n"
        "        cell.pinnedBadge?.image = entry.isPinned\n"
        "            ? NSImage(systemSymbolName: \"pin.fill\", accessibilityDescription: nil)?\n"
        "                .withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 8, weight: .semibold))\n"
        "            : nil")
SHOW = ("        cell.pinnedBadge?.isHidden = false\n"
        "        cell.pinnedBadge?.image = NSImage(systemSymbolName: \"pin.fill\", accessibilityDescription: nil)?\n"
        "            .withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 8, weight: .semibold))")

ARMS = [
    ("M1297", "产品：图钉永不显示 ⇒ 判据必须红", SOURCE,
     HIDE,
     "        cell.pinnedBadge?.isHidden = true\n        cell.pinnedBadge?.image = nil",
     TEST, "CAUGHT"),
    ("M1298", "产品：图钉永远显示 ⇒ 判据必须红（负臂也长图钉）", SOURCE,
     HIDE,
     SHOW,
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

    print("\n=== R477 汇总（每臂按自己的期望判定）===")
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
