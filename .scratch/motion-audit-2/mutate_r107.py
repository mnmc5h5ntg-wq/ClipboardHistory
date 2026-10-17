#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R107 的变异表：157 的实验对象必须自己在帧内（M588 / M589 / M590）。

本轮做的事：给容器梯子装上三行新读数（整窗墨、整窗填充行 y 段、分栏内容包围盒/溢出），
并据此把臂 2 的夹具从 720×140 改成 720×300 —— 因为包围盒读数说：分栏的内容盒是 258pt 高，
140pt 的夹具拍到的是"裁出来的一条窗口"，而裁在哪儿取决于窗口装饰高度（本机实测溢出 85pt）。
那正是 157 在 runner 上"整带 0 行墨、最大偏离 2"与"容器吃掉材质"长得一样的来源。

三刀各钉哪一句：
  M588 摘掉 `CARD_PROBE_WHOLE_FILL` 那行打印 ⇒ 期望 **PASSED（按实登记）**：
       它是纯读数，本机没有断言读它，牙在 runner 上人读那几行（与 M570 / M583 / M586 同规则）。
  M589 把整窗那一遍的扫描矩形改成 1pt 高 ⇒ 期望 **CAUGHT**
       —— 钉的是本轮给新读数装的那条结构不变量（整窗包含带子 ⇒ 整窗极值与墨像素不可能更低）。
       没有它，"整窗"这一行可以随便扫错地方而没人发现（尺自检也要有牙）。
  M590 把臂 2 的夹具高度改回 140pt ⇒ 期望 **CAUGHT**
       —— 钉的是"实验对象必须在帧内"这条新断言：内容盒 258pt 塞回 140pt 的窗 ⇒ 溢出 85pt ⇒ 红。
       这一刀是本轮最值钱的一格：它证明 157 的堵点**已经变成会红的**，而不是只写在注释里。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r107.py [M588 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

AXIS = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
WHOLE_EMIT = '                    emit("CARD_PROBE_WHOLE_FILL \\(fixture.name) \\(tag) 整窗材质=\(wholeFill >= 0 ? "有" : "无")"'
ARMS = [
    ("M588", "摘掉整窗填充那一行打印 ⇒ 本机无判别力（牙在 runner，人读那几行）", HARNESS,
     WHOLE_EMIT,
     '                    emit("M588_RETIRED "',
     AXIS, "PASSED"),
    ("M589", "整窗那一遍只扫 1pt 高 ⇒ 必须红在结构不变量（整窗包含带子）", HARNESS,
     "                    let wholeRect = CGRect(x: 0, y: 0, width: fixture.size.width,\n                                           height: fixture.size.height)",
     "                    let wholeRect = CGRect(x: 0, y: 0, width: fixture.size.width,\n                                           height: 1)",
     AXIS, "CAUGHT"),
    ("M590", "把臂 2 的夹具高度改回 140pt ⇒ 必须红在「实验对象必须在帧内」", HARNESS,
     "                                   NSSize(width: 720, height: 300)) {",
     "                                   NSSize(width: 720, height: 140)) {",
     AXIS, "CAUGHT"),
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
