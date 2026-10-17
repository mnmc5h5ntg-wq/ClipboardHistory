#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R108 的变异表：BACKLOG 160 那条"按表面"的判据自己要有三格牙（M591 / M592 / M593）。

本轮做的事：把"非 key ⇒ 选中一律画成灰"这句全局话拆成**按表面**的两臂读数
（列表 = 有彩度、字段 editor = 无彩度），判据走色度轴而不是亮度轴。
表上每一格钉的是判据里的一句话，三刀的期望都是从**当轮实测**来的，不是推的：
  M591 撤掉字段臂"装回选中"那一行 ⇒ 期望 CAUGHT —— 红在 `无彩度段宽 < 12pt` 那一格证人。
       没有这一格，字段那一臂就永远"有对象"（字形的横画也能凑 ≥4pt 的同色段），
       两臂的对比就退化成"列表有彩度 vs 列表没彩度"，问不到字段头上。
  M592 把尺的色度门限 `spread >= 6` 抬到 `>= 200` ⇒ 期望 CAUGHT —— 侧栏胶囊的色度是 34/36，
       抬到 200 之后 `chromaticRun` 归零 ⇒ 列表那一臂失去对象。这一格钉的是"色度这道门有牙"，
       与亮度无关（R38：亮度轴上灰与蓝只差约 27，永远分不开）。
  M593 把两个分支的判断**对调**（`spread >= 6` 换成 `spread <= 4`）⇒ 期望 CAUGHT：
       这样"最彩段"会挑到一段纯黑/纯白（色度 0），列表那侧 `色度 > 8` 立刻红。
       这一格是反向牙的等价物 —— 它证明判据读的是**色度最大的那一段**，不是"有没有填充"。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r108.py [M591 ...]
退出码：0 = 每一臂都拿到它自己那一条期望，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

JUDGE = "UICaptureTests/testSelectionFillUnderInactiveWindowIsPerSurface"

ARMS = [
    ("M591", "撤掉字段臂「装回选中」⇒ 字段那一臂必须失去对象（12pt 段宽那一格证人）", HARNESS,
     '                editor.setSelectedRange(NSRange(location: 0, length: length))',
     '                // M591：故意不装回选中，这一臂应当没有对象',
     JUDGE, "CAUGHT"),
    ("M592", "把尺的色度门限从 ≥6 抬到 ≥200 ⇒ 侧栏胶囊（34/36）不再算彩度，列表那一臂失去对象", HARNESS,
     '            if spread >= 6 {\n                s.chromaticRows += 1'.replace('\n', chr(10)),
     '            if spread >= 200 {\n                s.chromaticRows += 1'.replace('\n', chr(10)),
     JUDGE, "CAUGHT"),
    ("M593", "两个分支对调（>=6 换成 <=4）⇒「最彩段」会挑到纯黑/纯白，列表那侧的色度等式必须红", HARNESS,
     '            if spread >= 6 {\n                s.chromaticRows += 1'.replace('\n', chr(10)),
     '            if spread <= 4 {\n                s.chromaticRows += 1'.replace('\n', chr(10)),
     JUDGE, "CAUGHT"),
]


def read():
    return open(os.path.join(ROOT, HARNESS), encoding="utf-8").read()


def write(text):
    open(os.path.join(ROOT, HARNESS), "w", encoding="utf-8").write(text)


def run():
    env = dict(BASE_ENV)
    r = subprocess.run(["swift", "test", "--filter", JUDGE], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "with 0 failures" in out and "Executed 1 test" in out:
        if "Test Case '-[" in out and "' failed" in out:
            return "CAUGHT", out
        return "PASSED", out
    if "' failed" in out:
        return "CAUGHT", out
    if "Executed 0 tests" in out:
        return "DID-NOT-RUN", out
    if "skipped" in out and "failed" not in out:
        return "SKIPPED", out
    return "DID-NOT-RUN", out


def main():
    original = read()
    # 预检：不注入时目标必须是 PASSED
    verdict, out = run()
    print("=== 预检（不注入：目标必须是 PASSED）===")
    print("  %s %s" % (JUDGE, verdict))
    if verdict != "PASSED":
        print("PREFLIGHT_FAILED：判据在干净树上不是绿的，变异表无从判起（先修判据/夹具）")
        return 1
    wanted = sys.argv[1:]
    tally = {"CAUGHT": 0, "PASSED": 0, "SKIPPED": 0, "DID-NOT-RUN": 0}
    mismatch = 0
    not_run = 0
    results = []
    for name, note, fkey, needle, replacement, target, expect in ARMS:
        if wanted and name not in wanted:
            continue
        text = original
        if text.count(needle) != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, text.count(needle)))
            tally["DID-NOT-RUN"] += 1
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d，每处期望 1 ⇒ 不注入"
                            % text.count(needle)))
            continue
        write(text.replace(needle, replacement, 1))
        verdict, out = run()
        write(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        if not ok:
            mismatch += 1
        if verdict == "DID-NOT-RUN":
            not_run += 1
        snippet = ""
        for line in out.splitlines():
            if "error:" in line and "XCTAssert" in line:
                snippet = line.strip()[:150]
                break
        results.append((name, expect, verdict, note, ("对  期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s %s" % (name, verdict, note, results[-1][4]))
    if read() != original:
        write(original)
        restored = "二次还原仍不干净"
    else:
        restored = "yes"
    print("\n=== R108 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes") else 1


if __name__ == "__main__":
    sys.exit(main())
