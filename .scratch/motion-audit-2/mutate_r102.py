#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 的变异表：容器梯子自己要有三格牙（M568 / M569 / M570）。

**M570 的期望写的是 `PASSED` 不是 `ESCAPED`** —— 这个脚本的 `run()` 只返回
PASSED / CAUGHT / SKIPPED / DID-NOT-RUN 四个词，"按设计逃掉"在它嘴里就是 PASSED。
第一版这里填了 ESCAPED（那是 R9x 另一张表的词表）⇒ 预检之外第一跑就 `mismatch=1`，
与 R100 的 U-279（预检查 `passed` 而函数返回 `ESCAPED`）是同一颗错，方向相反。

本轮做的事只有一件：**把 BACKLOG 150 从"一个猜"变成"一次能读答案的实验"**。
  ① 先纠正猜错的对象：150 写的是"把参照装进 `Form`"，而这扇设置窗口**没有 `Form`**
    （`SettingsView.settingsContent` = `NavigationSplitView { 侧栏 } detail: { ScrollView { … } }`）
    ⇒ 实验改成**容器梯子**：臂 0 裸 `GroupBox` / 臂 1 加 `ScrollView` / 臂 2 加真分栏与真侧栏。
  ② 每一臂交一行 `CARD_PROBE_ARM`（runner 上没有 PNG 可下载，读数就是唯一证据）。
  ③ 每一臂再交一个**与材质无关的证人**：`墨行`。文字与材质是两条通道 ——
    材质可以被容器吃掉（那正是问题），文字不会。于是
    "带子没盖住"（仪器坏了）与"容器没有材质"（答案）第一次分得开。

三刀各钉哪一句：
  M568 把臂 2 的扫描带挪到卡片之外 ⇒ `墨行 > 0` 必须红（**没有这一刀，梯子会把"我框错了"
       当成"容器杀死了材质"报回来** —— 那是比 147 更坏的一种假答案）
  M569 从名册里删掉一臂 ⇒ 名册守卫必须红（加臂不接线、撤臂不改名册，两种都要响）
  M570 把臂 0 那条 declined 的原因措辞改回合并前的"这一带读不到卡片"
       ⇒ **本机期望 ESCAPED，而且这是量出来的**：没有任何断言读 `declined` 里的字符串，
       所以"两种成因分开报"这一格在本地**没有判别力**，它的牙在 runner 上（人读那几行）。
       按实登记，与 M454 / M509 同一族 —— **不为了让它看起来有牙去编一条断言**。
       这一刀只改一处措辞（不是把两处都合并），因为要测的就是"措辞本身有没有被任何东西读"。

R103 追记（改 needle 而不是改期望）：M568 的原文那一行跟着臂 2 的带子从 150/570 挪到了 170/550
（证人不能由侧栏作证，见 `cardprobeBands` 的文档串）。变异文 660/60 不变：它仍然在卡片里、
但那里没有字 —— 这一刀要红的是「带子里没有内容」，不是「带子跑到了卡片外」。
跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r102.py [M568 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H_INSET = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
V_RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M568", "参照臂的扫描带挪出卡片 ⇒ 「墨行>0」必须红（仪器错位不许冒充容器结论）", HARNESS,
     '        "cardprobe-split-groupbox": CGRect(x: 170, y: 24, width: 550, height: 100),',
     '        "cardprobe-split-groupbox": CGRect(x: 660, y: 24, width: 60, height: 100),',
     H_INSET, "CAUGHT"),
    ("M569", "名册里删掉一臂（夹具还在）⇒ 名册守卫必须红", HARNESS,
     '            var expected: Set<String> = ["cardprobe-groupbox-default", "cardprobe-scroll-groupbox"]',
     '            var expected: Set<String> = ["cardprobe-groupbox-default"]',
     H_INSET, "CAUGHT"),
    ("M570", "改回其中一条 declined 的原因措辞（合并前那句）⇒ 本机无判别力（牙在 runner，人读那几行）", HARNESS,
     '                    declined.append("\\(fixture.name) \\(tag)[\\(role)]=这一带没有第二层（fill=-1）")',
     '                    declined.append("\\(fixture.name) \\(tag)[\\(role)]=这一带读不到卡片")',
     H_INSET, "PASSED"),
    # R102 补的两刀钉的是**本轮修掉的那朵 runner 假红**（读 R101 的 CI run 38945656003 学到的）：
    # 竖向判据里「统计这一屏恰好一张卡片」原来无条件断言，runner 读不到被告材质 ⇒ 红四朵。
    ("M571", "把「统计」四格全当成读不到材质（本机其实读得到）⇒ 新的未判守卫必须红", HARNESS,
     "                statsCells += 1\n                if fill < 0 {",
     "                statsCells += 1\n                if fill < 0 || true {",
     V_RHYTHM, "CAUGHT"),
    ("M572", "同一台机器整体读不到材质（本机模拟 runner 那一台）⇒ 必须 skip，不许红", HARNESS,
     [("                statsCells += 1\n                if fill < 0 {",
       "                statsCells += 1\n                if fill < 0 || true {"),
      ("            settingsCells += 1\n            if fill >= 0 { materialCells += 1 }",
       "            settingsCells += 1\n            if fill >= 0 { materialCells += 1 }\n            materialCells = 0")],
     None,
     V_RHYTHM, "SKIPPED"),
]

PREFLIGHT = [(H_INSET, "PASSED"), (V_RHYTHM, "PASSED")]


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
        why = [l.strip()[:260] for l in out.splitlines() if "error:" in l]
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
        # `needle` 可以是**一串** (原文, 变异文)：M572 要同时造两个条件
        # （统计格读不到 + 整机没有材质），单独任何一个都不等于 runner 那一台。
        sites = [(needle, mutant)] if isinstance(needle, str) else needle
        miss = [(n, text.count(n)) for n, _ in sites]
        if any(c != 1 for _, c in miss):
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中次数 %s，每处期望 1 ⇒ 不注入" % [c for _, c in miss]))
            print("%s: DID-NOT-RUN needle 命中 %s" % (mid, [c for _, c in miss]), flush=True)
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
        # 注入型刀必须回读：变异文落地了才谈得上"逃掉"。
        if verdict != "DID-NOT-RUN" and read(path).find(sites[0][0]) < 0:
            evidence = "回读失败：原文不在了（还原步骤坏了？）" + evidence
        note = (u"对  期望 " + expect + (u"｜" + evidence[-160:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-260:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R102 汇总（每臂按自己的期望判定）===")
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
