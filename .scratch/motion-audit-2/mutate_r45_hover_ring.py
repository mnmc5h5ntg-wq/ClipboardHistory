#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R45 变异对照：那一圈描边的四种坏法 + 夹具的两种坏法，各该红一次。

  M210 描边整个没了（hoverRingOpacity true→0）           ⇒ 可见性 + 倍率 + 真值表都该红
  M211 描边淡到 0.02（"几乎看不见"那一档）                ⇒ 地板该抓住它，不是只抓"有没有"
  M212 悬停时连**格子内部**一起换色                        ⇒ 归因判据该红（喧宾夺主那一族）
  M213 文件里再画一份那一圈（两处画法分叉）                 ⇒ 源码守卫该红
  M214 夹具把"被悬停的那一格"指到未来格上                   ⇒ 夹具自检该红（两帧会一模一样）
  M215 夹具取回最老三列（本轮真犯过的错）                   ⇒ 夹具自检该红（带里只有一档）

M211 与 M215 是本轮最值钱的两支：
前者证明地板抓的是"淡到看不见"，不是抓"有没有非零"；
后者钉的是**我自己这一轮做错过的那件事** —— 尺子抓不住自己刚犯的错，就等于没有尺。

needle 一律从 --measure 那一遍的失败消息原文里抄（R41/R42 三次踩坑之后的固定流程）。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TOKENS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift")
CELL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift")
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "HeatmapHoverEvidenceTests"

RING_OPACITY = "        isHovered ? 0.55 : 0"
FILL_LINE = """            .fill(cell.count == 0
                  ? Color.primary.opacity(VisualHeat.empty)
                  : Color.accentColor.opacity(VisualHeat.opacity(bucket: cell.bucket)))"""
STROKE_ANCHOR = ("            .animation(MotionCatalog.animation(for: .contentFade), value: cell.bucket)\n"
                 "            .overlay(")
STROKE_DUPLICATE = ("            .animation(MotionCatalog.animation(for: .contentFade), value: cell.bucket)\n"
                    "            .overlay(VisualShape.rounded(VisualRadius.heatCell)\n"
                    "                .strokeBorder(Color.primary.opacity(VisualHeat.hoverRingOpacity"
                    "(isHovered: isHovered)),\n"
                    "                              lineWidth: VisualHeat.hoverStroke))  // MUTANT 第二处画法\n"
                    "            .overlay(")
STRIP_INDEX = "    static let heatmapHoverStripHoveredIndex = 10"
STRIP_COLUMNS = "            .suffix(3).flatMap { $0.cells })"

MUTATIONS = [
    ("M210", "描边整个没了", TOKENS, RING_OPACITY,
     "        isHovered ? 0 : 0  // MUTANT", ["悬停之后描边带只变了 0.00/255"]),
    ("M211", "描边淡到 0.02", TOKENS, RING_OPACITY,
     "        isHovered ? 0.02 : 0  // MUTANT", ["悬停之后描边带只变了 2.11/255"]),
    ("M212", "悬停时连格子内部一起换色", CELL, FILL_LINE,
     """            .fill(isHovered
                  ? Color.accentColor.opacity(VisualHeat.ladder[3])
                  : (cell.count == 0
                     ? Color.primary.opacity(VisualHeat.empty)
                     : Color.accentColor.opacity(VisualHeat.opacity(bucket: cell.bucket))))  // MUTANT""",
     ["带外有一处变了 106.00/255，位置 (11, 11)"]),
    ("M213", "文件里再画一份那一圈", CELL, STROKE_ANCHOR, STROKE_DUPLICATE,
     ["悬停那一圈的画法出现 2 次"]),
    ("M214", "被悬停的那一格指到未来格", HARNESS, STRIP_INDEX,
     "    static let heatmapHoverStripHoveredIndex = 20  // MUTANT", ["被悬停的第 20 格是未来/窗口外的格子"]),
    ("M215", "带取回最老三列（本轮真犯过）", HARNESS, STRIP_COLUMNS,
     "            .prefix(3).flatMap { $0.cells })  // MUTANT", ["这条带里只有 [0] 几档"]),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if ("error: -[" in line and " failed" in line) or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1500:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        messages = failure_messages(out)
        hit = [n for n in needles if any(n in m for m in messages)]
        right = bool(needles) and len(hit) == len(needles) and "待 --measure" not in needles
        ok = restore(path, original)
        results.append((mid, code, "MEASURE" if measure else ("yes" if right else "NO"),
                        "yes" if ok else "NO", ",".join(f.split(".")[-1] for f in failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure or not right or code != "CAUGHT":
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:420])
            print(out[-400:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] not in ("yes", "MEASURE")]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


if __name__ == "__main__":
    main()
