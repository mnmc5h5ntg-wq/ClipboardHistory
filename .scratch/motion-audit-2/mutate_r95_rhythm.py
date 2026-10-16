#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R95 变异对照：卡片竖向节奏那两条守卫有没有牙。

四支（两支动产品、两支动尺）：
  M528 `cardEdgeInset` 7 → 0（= 把本轮的修复整块撤掉）
       ⇒ 必须红在"卡片四边与分隔线两侧必须是同一档"
  M529 删掉「快捷键」那一处 `.settingsCardInset()`
       ⇒ 帧判据与调用点守卫**都**要红（一处漏补，两条账各抓各的）
  M530 `.line` 的宽度门槛 80% → 99%（尺读不到分隔线）
       ⇒ 必须红在"实测 0 条"那条前提，不许安静地退化成"只比边距"
  M531 页面底容差 3 → 40（卡片内的行被当成卡片外）
       ⇒ 必须红在"读不出边距 ⇒ 尺没压住卡片"

模板四件套沿用 R29d 那一支：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、
读失败消息确认**红得对**。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r95-mut-shots"

RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"
CALLSITES = "UICaptureTests/testEverySettingsCardAppliesTheSharedEdgeInset"

MUTATIONS = [
    ("M528", "把 cardEdgeInset 从 7 改成 0（撤掉本轮修复）", VIEW,
     "static let cardEdgeInset: CGFloat = 7",
     "static let cardEdgeInset: CGFloat = 0",
     RHYTHM, "必须是同一档"),
    ("M529", "删掉「快捷键」那张卡片补的留白", VIEW,
     """                        shortcut: $quickPickShortcut
                    )
                }
                .settingsCardInset()""",
     """                        shortcut: $quickPickShortcut
                    )
                }""",
     RHYTHM, "必须是同一档"),
    # M530 的锚点在 R97 换了形状：那一格从 `cardRowKinds` 里搬进了纯函数 `cardRowKind`
    # （`if line * 10 >= width * lineShareTenths`）。**刀还是同一刀**（把线的宽度门槛抬到读不到），
    # 只是必须跟着代码走 —— 上一版留旧锚点，它"needle 命中 0 次"，于是这一格安静地没了证人。
    ("M530", "把 .line 的宽度门槛抬到 99%（尺读不到分隔线）", HARNESS,
     "        if line * 10 >= width * lineShareTenths { return .line }",
     "        if line * 10 >= width * 99 { return .line }",
     RHYTHM, "尺瞎了"),
    # M531 **退役**（R97）：它的锚点是"这一行的众数离页面底 ≤3 就算卡片外"，
    # 而那一条判据在 R97 被整体换掉了（换成"最长一段连续卡片材质占带宽的比例"，见 `cardRowKind`），
    # 于是它连注入的对象都没有了。它想守的那个失败模式**没有消失**，
    # 换到了 `mutate_r97_card.py` 的 M538/M539 两刀上（地板撤 0 / 抬 60%）⇒ 那里有证人。
    # 留旧锚点的后果就是这一格"needle 命中 0 次"而表上看不出来 —— 所以退役要写在这里，
    # 而不是从列表里安静地删一行。
    ("M542", "把墨的门槛抬到读不到（inkMin 8 ⇒ 9999：满带卡片段却零墨）", HARNESS,
     "                            outsideTenths: Int = 3, inkMin: Int = 8,",
     "                            outsideTenths: Int = 3, inkMin: Int = 9999,",
     RHYTHM, "墨那一档瞎了"),
]

BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}


def run(test_filter):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not concluded:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:200] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {path: open(path, encoding="utf-8").read() for path in (VIEW, HARNESS)}
    snapshots = {path: open(path, "rb").read() for path in (VIEW, HARNESS)}

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    ok = True
    for test in (RHYTHM, CALLSITES):
        verdict, out = run(test)
        print("  %-62s %s" % (test, verdict), flush=True)
        if verdict != "ESCAPED":
            ok = False
            print("  " + (out.splitlines() or [""])[-1][:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, path, needle, mutant, test, expect_text in MUTATIONS:
        text = originals[path]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(needle, mutant))
        try:
            verdict, out = run(test)
            # M529 顺带要看调用点守卫：同一支变异它也必须红（一条变异、两条账）。
            # 必须在 `finally` 还原**之前**跑 —— 第一版写在还原之后，于是它读的是干净源码，
            # 报出"漏补一处却没被调用点守卫抓到"，而真相是我的 harness 自己晚了半步。
            extra, reason = "", ""
            if mid == "M529" and verdict == "CAUGHT":
                v2, _ = run(CALLSITES)
                extra = " | 调用点守卫=%s" % v2
                if v2 != "CAUGHT":
                    reason = "!! 漏补一处却没被调用点守卫抓到"
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
            extra, reason = "", ""
        finally:
            with open(path, "wb") as handle:
                handle.write(snapshots[path])
        if verdict == "CAUGHT" and expect_text and not reason.startswith("!!"):
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = "对  「" + hit[0].strip()[-140:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else out[-150:])
        results.append((mid, verdict, title, reason + extra))
        print("%s: %s %s %s%s" % (mid, verdict, title, reason, extra), flush=True)

    print("\n=== R95 节奏变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, line, reason))
    dirty = [p for p, snap in snapshots.items() if open(p, "rb").read() != snap]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d intended_escaped=0 mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v == "ESCAPED" or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    return 0 if not dirty and caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
