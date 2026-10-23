#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 的变异表：本轮新装的三格闸门各自要有牙（M563–M566）。

这一轮做的三件事，每一件都对应"如果没有这一刀，它就只是一句我说的话"：
  ① 产品：给「统计」补了卡片（BACKLOG 131 结案）。补法本身错过一次 ——
     `.settingsCardInset()` 挂到了 `GroupBox` **外面**，节奏尺量出 `边距=7.0/7.0`
     而**没有任何断言会红**（那一屏只有 1 条分隔线，`dividers >= 2` 那道地板让它走 declined）。
     ⇒ 新加一条一边的下界判据，M563 钉它。
  ② 判据：读 R100 的 CI（run 38927822527）发现我上一轮装的 skip 闸门没响 ——
     `materialCells` 把**参照**与**被告**混成一个数，runner 上参照有、被告全无，
     于是 `measured >= min(16, materialCells)` 变成 "0 ≥ 2" ⇒ 三朵红，而 skip 没触发。
     ⇒ 拆成 `defendantMaterial` / `controlMaterial`，M564 与 M565 一边钉一个方向。
  ③ 判据：「统计」空态那一臂的首墨是图标不是文字，量到 6.5pt 对文字参照 5.0/5.5。
     没有放宽等式，改成给这一格一条**有界的**替代判据（侧边距必须落在 [+0.5, +2.0]），
     M566 把名册清空 ⇒ 等式必须红（证明这一格不是免检牌，是换了一条能红的判据）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r101.py [M563 ...]
退出码：0 = 每一臂都拿到**它自己那一条**期望的 verdict，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
PRODUCT = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H_INSET = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
V_RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"

# (编号, 说明, 文件, needle, 替换, 目标测试, 期望 verdict)
ARMS = [
    ("M563", "产品：卡片共享留白归零（= 挂到材质外面那一档的可观测量）⇒ 新的下界判据必须红",
     PRODUCT,
     "    static let cardEdgeInset: CGFloat = 7",
     "    static let cardEdgeInset: CGFloat = 0",
     V_RHYTHM, "CAUGHT"),
    ("M564", "判据：被告材质归零（模拟 runner 那一台）⇒ 必须 skip，不许红在地板上",
     HARNESS,
     "                    if isProbe { controlMaterial += 1 } else { defendantMaterial += 1 }",
     "                    if isProbe { controlMaterial += 1 } else { defendantMaterial += 1 }\n                    defendantMaterial = 0",
     H_INSET, "SKIPPED"),
    ("M565", "判据：参照材质归零而被告保留 ⇒ 对照缺席必须红（M558 的靶在新结构下仍有牙）",
     HARNESS,
     "                    if isProbe { controlMaterial += 1 } else { defendantMaterial += 1 }",
     "                    if isProbe { controlMaterial += 1 } else { defendantMaterial += 1 }\n                    controlMaterial = 0",
     H_INSET, "CAUGHT"),
    ("M566", "判据：清空图标首墨名册 ⇒ 等式必须红（6.5 对 5.0 差 1.5 > 1.0）",
     HARNESS,
     # R314 重钉、R315 又改回去：这根针跟着名册的形状走。
     #   R314 往名册里加了两格 ⇒ 声明漂成两行 ⇒ 旧针命中 0（bad=1、rot 33→34）；
     #   R315 撤掉那张重复臂（BACKLOG 370 出口①）⇒ 声明回到一行 ⇒ 针跟着回原形。
     # 两次都不是"针坏了"，是**名册是手写的**：改名册的人不会想到自己动了刀 —— 见 BACKLOG 369。
     '        let iconFirstRosterMode = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_ICON_FIRST_ROSTER"] ?? "on"',
     '        let iconFirstRosterMode = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_ICON_FIRST_ROSTER"] ?? "off"',
     H_INSET, "CAUGHT"),
    # M567 是**收尾时补的**：多重集包含检查发现 R101 重写角色分账时把 R100 那条
    # 「系统参照必须亮暗两档各一条」**整条弄丢了**（不是决定撤，是编辑掉的）。
    # 原位补回之后必须证明它能红 —— 否则"补回来了"只是我的一句话。
    # 刀不动那条断言本身，动的是**它的来源**：让参照只在暗档落进 `control`。
    ("M567", "判据：系统参照只亮一档 ⇒ 「亮暗两档各一条」必须红（补回的那条断言自己要有牙）", HARNESS,
     "                    control[tag] = inset",
     '                    if tag == "dark" { control[tag] = inset }',
     H_INSET, "CAUGHT"),
]

PREFLIGHT = [(V_RHYTHM, "PASSED"), (H_INSET, "PASSED")]


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

    print("=== 预检（不注入：两处都必须是 PASSED）===", flush=True)
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
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, expect,
                            "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, evidence = run(test)
        except subprocess.TimeoutExpired:
            verdict, evidence = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        note = (u"对  期望 " + expect + (u"｜" + evidence[-160:] if evidence else u"")) \
            if verdict == expect else \
            (u"!! 期望 %s，拿到 %s｜%s" % (expect, verdict, evidence[-260:]))
        results.append((mid, verdict, title, expect, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R101 汇总（每臂按自己的期望判定）===")
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
