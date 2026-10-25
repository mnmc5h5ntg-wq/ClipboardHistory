#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R54 变异对照：热图相邻档那条判据，以及"轴"这件事本身。

R54 的结论是"梯子的数值不用改，错的是我的尺"——这种结论必须有牙，
否则它和"把判据调松然后宣布通过"在日志里长得一模一样。

  M264 产品侧：把梯子第 1 级压到与 `empty` 几乎相同（0.18 → 0.06）
       ⇒ 相邻档判据该红。这一支证明"两档并成一档"确实有人看着 —— 而它改的是**产品像素**。
  M265 尺子侧：把"最大通道差"换成现成的"均值通道差"
       ⇒ 该红（暗档空→第 1 档实测 17.33 < 地板 18）。
       这一支是本轮的核心：它证明**轴**选错就等于判据没了，而不是"数稍微小一点"。
  M266 尺子侧：`fillBand` 返回描边带（把内部与那一圈混起来）
       ⇒ 真值表该红（重叠 / 面积两条都会撞）。
  M267 判据侧：1× 那一臂从循环里删掉
       ⇒ 读数条数那条该红（16 → 8 ⇒ 有一整臂没被量）。
  M268 夹具侧：`flatRep` 忽略 blue 参数（两幅图变成同一幅）
       ⇒ 真值表该红（"最大通道差该读到 30"读到 0）。
       这一支钉的是"尺子的夹具自己会坏" —— R54 第一版它就是坏的（`setColor` 不落地，读到 0.00）。

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift")
TOKENS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

JUDGE = "HeatmapHoverEvidenceTests.testAdjacentHeatLevelsAreSeparableOnTheRightAxis"
TABLE = "HeatmapHoverEvidenceTests.testAdjacentLevelRulersAreATruthTable"

MUTATIONS = [
    ("M264", "产品侧：梯子第 1 级压到与空格子几乎相同", TOKENS,
     # R372 / BACKLOG 367：顶档从 0.85 抬到 0.92 之后针就腐烂了（M264 在 rot 名单上）。
     "    static let ladder: [Double] = [0.18, 0.34, 0.56, 0.92]",
     "    static let ladder: [Double] = [0.06, 0.34, 0.56, 0.92]   // MUTANT",
     JUDGE, ['低于地板']),
    ("M265", "尺子侧：最大通道差换成均值通道差", TESTS,
     "                    let maxDelta = Self.meanMaxChannelDelta(renders[i - 1], renders[i], over: band, size: size)",
     "                    let maxDelta = Self.meanChannelDelta(renders[i - 1], renders[i], over: band, size: size)   // MUTANT",
     JUDGE, ['低于地板']),
    ("M266", "尺子侧：填充带返回描边带", TESTS,
     "                guard sdf < -strokePx - allowance else { continue }",
     "                guard sdf >= -strokePx - allowance, sdf <= 0.5 else { continue }   // MUTANT",
     # R372：这条断言今天的正文是「填充带压到了描边上 ⇒ 两档之差会被那一圈的抗锯齿污染」，
     # 旧的两根期望串（重叠 / 漏了太多格子像素）已随措辞一起过期 —— 红本来就落在对的那格。
     TABLE, ['压到了描边上', '重叠', '漏了太多格子像素']),
    ("M267", "判据侧：1× 那一臂不再量", TESTS,
     "            for scale in [1, 2] {\n                // 每一档画一次",
     "            for scale in [2] {   // MUTANT\n                // 每一档画一次",
     JUDGE, ['读数必须是 4 对']),
    ("M268", "夹具侧：flatRep 忽略 blue", TESTS,
     "                data[offset + 2] = UInt8(blue)",
     "                data[offset + 2] = UInt8(red)   // MUTANT",
     TABLE, ['最大通道差该读到']),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or "error: -[" in line or "XCTAssert" in line]


def run(filter_name):
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=1800)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:120]))
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
    # 锚点先数一遍：电池跑到第三支才发现锚点不唯一，前面烧掉的构建就白烧了。
    for mid, desc, path, old, new, filter_name, needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:120]))
    for filter_name in (JUDGE, TABLE):
        code, out, _ = run(filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检 %s 失败：%s\n%s" % (filter_name, code, out[-2500:]))
        print("预检 OK " + filter_name.split(".")[-1])
    results = []
    for mid, desc, path, old, new, filter_name, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(filter_name)
        finally:
            ok = restore(path, original)
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in m for m in messages)]
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 还原干净=%s" % (mid, desc, code, right, failed, ok))
        if measure or not right or code != "CAUGHT":
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:320])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, out, _ = run(JUDGE)
    print("还原后复跑（判据）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R54_MUTATION_PROBLEM")


main()
