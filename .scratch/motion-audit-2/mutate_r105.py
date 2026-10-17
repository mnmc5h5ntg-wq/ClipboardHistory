#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R105 的变异表：左轴判据的"没有对象"这一格要有牙（M581 / M582 / M583）。

本轮的起因是读 R104 的 CI（run `38975204376`）：那条新判据在 runner 上**红了**，
红在"搜索那一行一个墨像素都没有"—— 也就是**等式的另一边在那台机器上不存在**，
而参照物（药丸）两档都读得到。这不是产品坏了，是判据在那台机器上无从判起。
处置照 D-166 的形状做：**没有对象 ⇒ 有名字的 skip + 一行能力读数 + 本机可模拟**。

三刀各钉哪一句：
  M581 在本机**模拟出 runner 那一台**（把搜索带的证人读数强行归零）⇒ 期望 **SKIPPED**
       —— 不红、也不许静默通过；这一刀是"skip 这条通道本身能被证伪"的证明。
  M582 同一注入 + 再把 `judged == 0` 那道 skip 摘掉 ⇒ 期望 **CAUGHT**（红在未判守卫）
       —— 只有 M581 的话，"skip"会变成新的万能挡箭牌；D-166 的后半条必须有独立的刀。
  M583 把 `QUICKPICK_AXIS_DECLINED` 那行打印摘掉 ⇒ 本机期望 **PASSED（逃掉，按实登记）**：
       本机未判名单本来就是空的 ⇒ 没有任何断言读它，牙在 runner 上人读那几行（与 M570 同规则）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r105.py [M581 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

AXIS = "UICaptureTests/testQuickPickSearchLineSharesTheRowsColumn"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
# R106 追：这一支的针跟着 D-172 改了形状（`strip.rows > 0` → `strip.maxDelta >= 20`）。
# 不改这里就会静默 not_run=2 —— 本轮 pass-1 正是被 `mutate_needle_precheck.py` 的 bad=2 抓出来的（U-332）。
GUARD = "            guard strip.maxDelta >= 20, let ink = search else {"
SIM = ('            if true {   // M581：在本机模拟 runner 那一台（搜索带读不到字）\n'
       '                declined.append("\\(tag)[M581 模拟：带内墨行被强行归零]")\n'
       '                continue\n'
       '            }\n' + GUARD)
# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M581", "本机模拟 runner：搜索带归零 ⇒ 必须 SKIPPED（不红、也不许静默通过）", HARNESS,
     GUARD, SIM, AXIS, "SKIPPED"),
    ("M582", "同一归零 + 摘掉 skip ⇒ 必须红在未判守卫（skip 不是万能挡箭牌）", HARNESS,
     [(GUARD, SIM),
      ('        if judged == 0 {\n            throw XCTSkip("这台机器上浮层搜索那一行画不出字',
       '        if false {\n            throw XCTSkip("这台机器上浮层搜索那一行画不出字')],
     None, AXIS, "CAUGHT"),
    ("M583", "摘掉未判名单那行打印 ⇒ 本机无判别力（牙在 runner，人读那几行）", HARNESS,
     '        if !declined.isEmpty { emit("QUICKPICK_AXIS_DECLINED " + declined.joined(separator: " ")) }',
     "        // M583：摘掉打印",
     AXIS, "PASSED"),
]

PREFLIGHT = [(AXIS, "PASSED")]


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

    print("=== 预检（不注入：目标必须是 PASSED）===", flush=True)
    ok = True
    for test, want in PREFLIGHT:
        verdict, out, note = run(test)
        print("  %-72s %s" % (test, verdict), flush=True)
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
        # `needle` 可以是一串 (原文, 变异文)：M582 要同时造两个条件
        sites = [(needle, mutant)] if isinstance(needle, str) else needle
        hits = [text.count(n) for n, _ in sites]
        if any(c != 1 for c in hits):
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中 %s，每处期望 1 ⇒ 不注入" % hits))
            print("%s: DID-NOT-RUN needle 命中 %s" % (mid, hits), flush=True)
            continue
        for n, m in sites:
            text = text.replace(n, m)
        write(path, text)
        try:
            verdict, out, evidence = run(test)
        except subprocess.TimeoutExpired:
            verdict, evidence = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        if verdict != "DID-NOT-RUN" and read(path).find(sites[0][0]) < 0:
            evidence = "回读失败：原文不在了（还原步骤坏了？）" + evidence
        note = (u"对  期望 " + expect + (u"｜" + evidence[-200:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-300:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R105 汇总（每臂按自己的期望判定）===")
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
