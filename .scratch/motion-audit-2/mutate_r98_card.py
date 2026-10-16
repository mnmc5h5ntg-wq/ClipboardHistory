#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R98 的产品腿变异对照：「推荐」那张卡片的留白档（两刀，全部期望 CAUGHT）。

R98 的高夹具第一次把这张卡片的**底边**拍进画面，量出 `边距=11.5/9.5` 对
`内侧=16.5/18.0` ⇒ 首末行贴边、比彼此之间紧 5~9pt（R95 在「快捷键」上修过的同一个形状，
当时没轮到它，因为数卡片的源码守卫只扫 `SettingsView.swift`，而这张卡片长在
`RecommendationWeightsView.swift` 里 —— 见 BACKLOG 143）。
修法：`spacing: 16 → 12` + 孤儿 `.padding(.vertical, 4)` 换成共享的 `.settingsCardInset()`。

两刀各钉一半，而且第二刀是**一条变异、两条账**：
  M550 把行距改回 16（只动内侧）      ⇒ 节奏判据必须红在「同一张卡片里最大的留白…」
  M551 把共享留白换回 `.padding(.vertical, 0)`（只动边）
        ⇒ 节奏判据**与**调用点守卫都要红（守卫那一条是 143 的证人：
           卡片数 7、补留白处数 6 ⇒ 少一处就红，且要点名在哪个文件）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r98_card.py
退出码：0 = 两刀全 CAUGHT 且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/RecommendationWeightsView.swift")
SHOTS = "/tmp/r98-card-mut-shots"

BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
BASE_ENV["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS

RHYTHM = "UICaptureTests/testSettingsCardVerticalRhythmIsOneNumber"
CALLSITES = "UICaptureTests/testEverySettingsCardAppliesTheSharedEdgeInset"

# (编号, 标题, 锚点, 变异后, 跑哪支, 期望红在哪句话, 是否还要跑第二支)
MUTATIONS = [
    ("M550", "把「推荐」那行的行距改回 16（内侧那一档又比四边大 4pt）",
     "                VStack(spacing: 12) {",
     "                VStack(spacing: 16) {",
     RHYTHM, "同一张卡片里最大的留白", CALLSITES),
    ("M551", "把共享留白换回 `.padding(.vertical, 0)`（四边贴到卡片边上）",
     "                .settingsCardInset()",
     "                .padding(.vertical, 0)",
     RHYTHM, "同一张卡片里最大的留白", CALLSITES),
]


def run(test_filter):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not concluded:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:200] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {path: open(path, encoding="utf-8").read() for path in (VIEW,)}
    snapshots = {path: open(path, "rb").read() for path in (VIEW,)}

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
    for mid, title, needle, mutant, test, expect_text, second in MUTATIONS:
        text = originals[VIEW]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        with open(VIEW, "w", encoding="utf-8") as handle:
            handle.write(text.replace(needle, mutant))
        extra, reason = "", ""
        try:
            verdict, out = run(test)
            # 第二支必须在还原**之前**跑：它读的是同一份被改过的源码。
            if second:
                v2, o2 = run(second)
                extra = " | 调用点守卫=%s" % v2
                if mid == "M551" and v2 != "CAUGHT":
                    reason = "!! 撤掉一处共享留白却没被调用点守卫抓到"
                if mid == "M550" and v2 == "CAUGHT":
                    reason = "!! 只改行距却把调用点守卫也弄红了（那条守卫数的是调用点，不该管间距）"
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
            extra, reason = "", ""
        finally:
            with open(VIEW, "wb") as handle:
                handle.write(snapshots[VIEW])
        if verdict == "CAUGHT" and expect_text and not reason.startswith("!!"):
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = "对  「" + hit[0].strip()[-150:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else out[-150:])
        results.append((mid, verdict, title, reason + extra))
        print("%s: %s %s %s%s" % (mid, verdict, title, reason, extra), flush=True)

    print("\n=== R98 产品腿变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, line, reason))
    dirty = [p for p, snap in snapshots.items() if open(p, "rb").read() != snap]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v == "ESCAPED" or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    return 0 if not dirty and caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
