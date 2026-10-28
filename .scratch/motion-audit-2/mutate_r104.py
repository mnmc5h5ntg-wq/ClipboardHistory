#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R104 的变异表：浮层左轴这一改，四刀各钉一角（M577 / M578 / M579 / M580）。

本轮产品改一样东西：浮层那颗搜索框的字，从面板的 12pt 内缩挪到**列表自己那一列**（药丸左沿 22pt）。
判据 `testQuickPickSearchLineSharesTheRowsColumn` 读的是同一张帧上药丸自己的左沿，
参照物与等式两边都是像素 —— 所以这一轮的刀必须证明三件事：产品常数有牙、尺子的两道地板有牙、
以及**参照点**本身有牙。

  M577 产品：`searchFieldLeadingInset` 10 → 0（撤掉本轮修复）⇒ 等式必须红（差回 19px）
       这一刀同时证明判据读的不是那个常数 —— 拿被约束的常量推期望值，改常量等于改判据（M367 那一课）。
  M578 尺子：药丸的宽度地板 0.55 → 0.05 ⇒ 真值表第 ③ 格必须红
       （没有这一格，"30% 宽的一段行内图标"也能当上药丸，参照物就不是参照物）
  M579 尺子：药丸与页底的最小差 12 → 4 ⇒ 真值表第 ④ 格必须红
       （这一道地板就是 R100 那把 python 尺翻车的地方：它用"差 ≥40"，于是亮档那对 35 灰阶整档读不到。
        地板太高会瞎，太低会把噪声当带子 —— 两边各要一刀。）
  M580 判据：参照物从"药丸左沿"换成常量 0 ⇒ 正对照那一格必须红
       （拦的是"参照点选错"这一族：读成 0 时等式会退化成『0 与 0 相等』的假绿，R37 那一课）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r104.py [M577 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
CONTROLLER = "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

AXIS = "UICaptureTests/testQuickPickSearchLineSharesTheRowsColumn"
TRUTH = "UICaptureTests/testOverlayPillAndStripRulersReadStructure"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M577", "产品：撤掉搜索框的列内缩（10 → 0）⇒ 等式必须红，且红在 19px 那一格", CONTROLLER,
     "    static let searchFieldLeadingInset: CGFloat = hoverFillInset",
     "    static let searchFieldLeadingInset: CGFloat = 0",
     AXIS, "CAUGHT"),
    ("M578", "尺子：药丸的宽度地板 0.55 → 0.05 ⇒ 真值表第 ③ 格必须红（短段不能当药丸）", HARNESS,
     "                            minDelta: Int = 12, minWidthShare: Double = 0.55,\n                            maxGap: Int = 0)",
     "                            minDelta: Int = 12, minWidthShare: Double = 0.05,\n                            maxGap: Int = 0)",
     TRUTH, "CAUGHT"),
    ("M579", "尺子：药丸与页底的最小差 12 → 4 ⇒ 真值表第 ④ 格必须红（地板太低会把噪声当带子）", HARNESS,
     "                            minDelta: Int = 12, minWidthShare: Double = 0.55,\n                            maxGap: Int = 0)",
     "                            minDelta: Int = 4, minWidthShare: Double = 0.55,\n                            maxGap: Int = 0)",
     TRUTH, "CAUGHT"),
    ("M580", "判据：参照物从药丸左沿换成常量 0 ⇒ 正对照那一格必须红（参照点选错=假绿）", HARNESS,
     "            let pillPt = Double(pill.left) / scale",
     "            let pillPt = 0.0",
     AXIS, "CAUGHT"),
]

PREFLIGHT = [(AXIS, "PASSED"), (TRUTH, "PASSED")]


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

    print("=== 预检（不注入：两个目标都必须 PASSED）===", flush=True)
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

    print("\n=== R104 汇总（每臂按自己的期望判定）===")
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
