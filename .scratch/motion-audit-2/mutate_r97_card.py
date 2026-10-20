#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R97 的卡片判据变异对照：五刀，全部期望 CAUGHT。

这一支盯的是 R97 新立的那三格（`cardFill` 的地板、`cardRowKind` 的"最长连续卡片材质"、
`cardSegments` 的分段）以及"扫描带跟着夹具尺寸走"那条恒等式。
为什么每一刀都要单独有证人：这三格都是**放宽就安静**的形状 —— 地板拿掉之后尺不会崩，
它会开始把一条 1pt 的分隔线、一颗按钮当成卡片，然后量出一组**看起来很像数**的假读数。
R96 那条 `边距=14.5/8.0` 的假红就是这一族的第一个样本（当时是"填充取到了一条线"）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r97_card.py
退出码：0 = 五刀全 CAUGHT 且还原干净；非 0 = 有刀漏了或没跑。
"""
import os
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
ROOT = os.path.join(REPO, "ClipboardHistory")
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r97-card-mut-shots"

CARD = ("UICaptureTests/(testSettingsCardVerticalRhythmIsOneNumber"
        "|testCardRowKindReadsMaterialNotModal"
        "|testCardSegmentsSplitsCardsAndKeepsTallOnes"
        "|testCardRhythmArithmeticIsATruthTable"
        "|testCardFillNeedsAStableBandNotTheFirstDifferingRow)")

# (编号, 标题, 文件, 锚点, 变异后, 跑哪支, 期望红在哪句话)
MUTATIONS = [
    ("M537", "把 cardSegments 的高度地板从 20pt 撤到 0（1pt 的分隔线又能当卡片段）", HARNESS,
     "static func cardSegments(rows: [CardRowKind], scale: Double, minHeightPt: Double = 20)",
     "static func cardSegments(rows: [CardRowKind], scale: Double, minHeightPt: Double = 0)",
     CARD, "没到 20pt 的地板"),
    ("M538", "把 cardRowKind 的卡片材质地板从 30% 撤到 0（按钮又能当卡片）", HARNESS,
     "                            outsideTenths: Int = 3, inkMin: Int = 8,",
     "                            outsideTenths: Int = 0, inkMin: Int = 8,",
     CARD, "一颗 76pt 宽的按钮横不过带子"),
    ("M539", "把 cardRowKind 的卡片材质地板抬到 60%（输入框那行被判成卡片外 ⇒ 卡片被自己的控件切断）", HARNESS,
     "                            outsideTenths: Int = 3, inkMin: Int = 8,",
     "                            outsideTenths: Int = 6, inkMin: Int = 8,",
     CARD, "这一行当然还在卡片里"),
    ("M540", "把扫描带高度改回写死的 440pt（BACKLOG 140 那个病根）", HARNESS,
     "                              height: fixture.size.height - bandTop)",
     "                              height: 440)",
     CARD, "扫描带必须扫到窗口底"),
    ("M541", "把 cardFill 的地板从 20pt 撤到 0（第一行差 3 又算卡片填充）", HARNESS,
     "minCardHeightPt: Double = 20",
     "minCardHeightPt: Double = 0",
     CARD, "一条 1pt 的分隔线没有资格当卡片填充"),
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
    paths = sorted(set(p for _, _, p, _, _, _, _ in MUTATIONS))
    originals = {p: open(p, encoding="utf-8").read() for p in paths}
    snapshots = {p: open(p, "rb").read() for p in paths}

    print("=== 预检（不注入任何变异，五支判据都必须绿）===", flush=True)
    verdict, out = run(CARD)
    print("  %-70s %s" % (CARD[:70], verdict), flush=True)
    if verdict != "ESCAPED":
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        print((out.splitlines() or [""])[-1][:300], flush=True)
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
            reason = ""
        except subprocess.TimeoutExpired:
            verdict, out, reason = "DID-NOT-RUN", "timeout", ""
        finally:
            with open(path, "wb") as handle:
                handle.write(snapshots[path])
        if verdict == "CAUGHT":
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = ("对  「" + hit[0].strip()[-150:] + "」") if hit \
                else "!! 红得不对（找不到期望文本）"
        if verdict == "CAUGHT" and not reason.startswith("对"):
            # 找不到期望文本时，把**实际**那一条失败断言打出来：上一版只留一句"红得不对"，
            # 于是下一轮要么重跑一遍要么猜 —— 而这一刀到底砍在哪，日志里本来就有。
            real = [l for l in out.splitlines() if "error:" in l and "XCTAssert" in l][:1]
            reason += "  实际红在「" + ((real[0].strip()[-170:]) if real else "（没找到断言行）") + "」"
        elif verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else out[-150:])
        results.append((mid, verdict, title, reason))
        print("%s: %s %s %s" % (mid, verdict, title, reason), flush=True)

    print("\n=== R97 卡片判据变异对照汇总 ===")
    for mid, verdict, title, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, title, reason))
    dirty = [p for p, snap in snapshots.items() if open(p, "rb").read() != snap]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d intended_escaped=0 mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v == "ESCAPED" or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    mismatch = sum(1 for _, v, _, r in results if v == "ESCAPED" or r.startswith("!!"))
    return 0 if not dirty and caught == len(results) and mismatch == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
