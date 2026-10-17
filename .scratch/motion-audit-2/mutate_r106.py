#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R106 的变异表：浮层那张"名字叫 typed、其实整条查询被选中"的帧要有牙（M584–M587）。

本轮的起因是 R105 看图翻出的 BACKLOG 159：`quickpick-typed` / `-empty` 两张帧上，
查询底下有一块**真实使用里不存在的灰色选中底**（本机读数：`有editor=true 选中=(0,2) 覆盖整串=true
窗口是key=false`，灰块 32 行 / 1115 像素 / 纯灰行最宽 52px 对最宽墨行 37px）。
机制证实之后修的是**捕获通道**（`collapsePhantomSelections`，与 `silenceCarets` 同族），产品路径一行未动。

三刀各钉哪一句：
  M584 摘掉 `collapsePhantomSelections(in:)` 那一次调用 ⇒ 期望 **CAUGHT**
       （两档都该红：机制那一格读到长度 2 的选中区间，像素那一格读到比字还宽的纯灰行）。
  M585 同一摘除 + 再把**机制那一格**断言摘掉 ⇒ 期望 **CAUGHT**
       —— 只有 M584 的话，红可能全部来自①，②"填充比字宽"这条独立牙就没被证过（两格断言不许互相顶班）。
  M586 摘掉 `QUICKPICK_PHANTOM_CAPABILITY` 那行结论打印 ⇒ 本机期望 **PASSED（逃掉，按实登记）**：
       本机两档都有对象 ⇒ 没有断言读这一行，它的牙在 runner 上人读那几行（与 M570 / M583 同规则）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r106.py [M584 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

AXIS = "UICaptureTests/testOverlayTypedFrameCarriesNoPhantomSelectionFill"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
COLLAPSE = "        Self.collapsePhantomSelections(in: host)"
NO_COLLAPSE = "        // M584：摘掉那一次抹除 ⇒ 通道又给字段装了个全选"
MECH = "            XCTAssertEqual(selectionLength, 0,"
# 刀必须是**能编译的一句话**：整行删掉会把那条断言剩下的 4 行消息悬空 ⇒ 语法错 ⇒ DID-NOT-RUN
# （本机实测第一版就是这样，U-186 那一族的复发：刀坏与判据没牙是两种病，这里坏的是刀）。
# 换成同参数自等 ⇒ 这一格恒真，而消息行照旧合法，像素那一格成为唯一的牙。
NO_MECH = "            XCTAssertEqual(selectionLength, selectionLength,"
ARMS = [
    ("M584", "摘掉 collapsePhantomSelections 调用 ⇒ 两格都必须红", HARNESS,
     COLLAPSE, NO_COLLAPSE, AXIS, "CAUGHT"),
    ("M585", "同一摘除 + 摘掉机制那一格 ⇒ 必须仍红在像素那一格（两格不许互相顶班）", HARNESS,
     [(COLLAPSE, NO_COLLAPSE), (MECH, NO_MECH)],
     None, AXIS, "CAUGHT"),
    ("M587", "把这一档的地板钉回全局 60（=R106 之前的形状）⇒ 本机无判别力，牙在 runner", HARNESS,
     "            let bandFloor = max(20, strip.maxDelta / 2)",
     "            let bandFloor = Self.textInkMinDelta",
     AXIS, "PASSED"),
    ("M586", "摘掉未判名单那行打印 ⇒ 本机无判别力（牙在 runner，人读那几行）", HARNESS,
     '        if !declined.isEmpty { emit("QUICKPICK_PHANTOM_DECLINED " + declined.joined(separator: " ")) }',
     "        // M586：摘掉未判名单那行打印",
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
