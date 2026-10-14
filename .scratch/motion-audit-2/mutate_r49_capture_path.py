#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R49 变异对照：采集路径那两条判据，每一条都要能被"产品真的变坏"顶红。

这一族与前面几轮不同：**M240 改的是产品代码**（`DailyCopyLedger.recordCopy` 里加一次同步写盘）。
理由很直接 —— 目标里那句"采集路径上不许有同步磁盘写"如果只有一条"看起来在管"的判据，
那它等于没有；能证明它在管的唯一办法，就是把被禁的事做出来，看它红不红。

  M240 产品侧：`recordCopy` 里同步写盘一次        ⇒ 「没写盘」那条判据该红（**这是本轮最重要的一支**）
  M241 `percentile` 改成最近秩（取 `count/2`）    ⇒ 真值表第 ① 格该红（25 变 30）
  M242 空样本返回 0 而不是 NaN                    ⇒ 第 ⑤ 格该红（"没采到"被读成"0ms"）
  M243 样本数 40 → 5                              ⇒ 地板那条该红（p95 退化成最大值）
  M244 目录快照永远是空（探针坏掉）                ⇒ 对照组那条该红（不许"没写盘"靠"没接上盘"来绿）

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift")
LEDGER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "CapturePathWriteBudgetTests"

RECORD = ("        counts[key, default: 0] += 1\n"
          "        scheduleSave()")
INTERP = "        return sorted[lower] * (1 - fraction) + sorted[upper] * fraction"
EMPTY = "        guard !values.isEmpty else { return .nan }"
COUNT = "    static let sampleCount = 40"
WALK = "        for case let url as URL in walked {"

MUTATIONS = [
    ("M240", "产品侧：recordCopy 同步写盘", LEDGER, RECORD,
     "        counts[key, default: 0] += 1\n"
     "        scheduleSave()\n"
     "        try? Self.write(counts, to: fileURL)   // MUTANT",
     ['账本在 `add` 返回之前就已经落盘']),
    ("M241", "percentile 改成最近秩", TESTS, INTERP,
     "        return sorted[sorted.count / 2]   // MUTANT",
     [('("30.0") is not equal to ("25.0")')]),
    ("M242", "空样本返回 0", TESTS, EMPTY,
     "        guard !values.isEmpty else { return 0 }   // MUTANT",
     ['空样本必须报']),
    ("M243", "样本数掉到 5", TESTS, COUNT,
     "    static let sampleCount = 5   // MUTANT",
     ['样本掉到']),
    ("M244", "目录快照永远是空", TESTS, WALK,
     "        for case let url as URL in [] as [URL] {   // MUTANT",
     ['对照组里盘上仍然一个字节没多']),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or "error: -[" in line or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
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
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-2000:])
    print("预检 OK（未变异时这三条判据全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in m for m in messages)]
        right = bool(needles) and len(hit) == len(needles) and "待 --measure" not in needles
        ok = restore(path, original)
        results.append((mid, code, "MEASURE" if measure else ("yes" if right else "NO"),
                        "yes" if ok else "NO", ",".join(f.split(".")[-1] for f in failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure or not right or code != "CAUGHT":
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:400])
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


main()
