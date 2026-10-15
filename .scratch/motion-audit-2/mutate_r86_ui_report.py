#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R86 的变异电池：`scripts/ui_probe_report.py` 那一格真值表到底有没有牙。

跑法：

    python3 .scratch/motion-audit-2/mutate_r86_ui_report.py --measure   # 先看每刀实际红在哪
    python3 .scratch/motion-audit-2/mutate_r86_ui_report.py            # 再对着实测结果判 CAUGHT/ESCAPED

为什么先 `--measure`（R42 定下的流程，本轮第三次用）：
"该红在哪一句"是**推理**，而推理错过三次了 —— 把"我以为它会红"当成"它红了"，
电池就会把一刀没落地的变异报成抓到。`EXPECTED` 里的用例名只能从 `--measure` 的输出抄。

八刀的形状分两类：
  · 判据本身坏（M465 差集算反、M466 不完整日志放行、M467 拿错文件不拦、M468 空日志当结论、
    M470 重复 started 双报）
  · 通道/退出码坏（M469 红不落到退出码、M471 `--quiet` 把结论行也吞掉）
  · 元层（M472 给"两支闸门不冗余"那道守卫自己喂一个假阳性 ⇒ 证明它会红，而不是恒绿）
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
SCRIPT = "scripts/ui_probe_report.py"
GATE = "scripts/probe_coverage_gate.py"
TESTS = "scripts/tests/test_ui_probe_report.py"
LOCK = "/tmp/r86_mutation.lock"

# 每刀预期**只**红在这些用例上（先 --measure 再抄进来）。
EXPECTED = {
    # 下面每一行都是从 `--measure` 那一遍的输出里抄的，不是推出来的（R42 定的流程）。
    "M465": ["testDuplicateStartedLinesCountOnce", "testHungCaseIsNamed",
             "testNamedExitsZeroAndPrintsMarker", "testQuietStillPrintsTheVerdict"],
    "M466": ["testConcludedWithoutStartIsRed"],
    "M467": ["testStepEchoIsNotTheRawLog", "testUnnamedExitsOne"],
    "M468": ["testEmptyLogIsInstrumentFailure"],
    "M469": ["testUnnamedExitsOne"],
    "M470": ["testDuplicateStartedLinesCountOnce"],
    "M471": ["testQuietStillPrintsTheVerdict"],
    "M472": ["testGateAndReportAnswerDifferentQuestions"],
}

MUTATIONS = [
    ("M465", "挂死集合算反（concluded 减 started）⇒ 把跑完的说成挂死、把挂死的说成没事", SCRIPT,
     "    hung = [n for n in started if n not in concluded]",
     "    hung = [n for n in concluded if n not in started]"),
    ("M466", "日志不完整（有结论没 started）从红改成放行 ⇒ started 差集被成块丢时照样报点名成功", SCRIPT,
     "    if orphans:\n        return lines, False",
     "    if orphans:\n        return lines, True"),
    ("M467", "不再区分『步骤摘要』与『原始日志』（拿错文件时自信地报产品结论）", SCRIPT,
     "    if ECHO_MARKERS.search(text):",
     "    if False:"),
    ("M468", "空日志不再算仪器故障，直接往下走成『一条用例都没开始』", SCRIPT,
     "        return ([\"UI_PROBE_LOG_EMPTY=1 日志是空的 ⇒ 这不是『探针没跑』，是『我没有它的输出』\"], False)",
     "        pass  # R86 变异：空日志继续往下判"),
    ("M469", "红不落到退出码（CI 那一步就再也拿不到『说不出』这件事）", SCRIPT,
     "    return 0 if named else 1",
     "    return 0"),
    ("M470", "重复的 started 不去重 ⇒ 同一条挂死被报两次，计数也不再可信", SCRIPT,
     "            if name not in started:          # 同一条重复出现（重跑或被两遍并进来）只算一次\n"
     "                started.append(name)",
     "            started.append(name)  # R86 变异：不去重"),
    ("M471", "`--quiet` 连结论行一起吞 ⇒ 报告型那一步看起来『什么都没发生』", SCRIPT,
     "        if args.quiet and line.startswith(\"UI_PROBE_PROGRESS\"):",
     "        if args.quiet:"),
    # 第一版这一刀"逃掉"是我自己的错：插进去的那行注释里**根本没有 started 这个词**，
    # 于是守卫不红是正确行为，而我把它记成了"守卫没牙"。⇒ 判"刀落地了没有"要看内容，
    # 不能只看文件变了没有（M472 的 replacement 现在真的带上那个词）。
    ("M472", "元层：往不冗余守卫读的那支闸门里塞一行真的含 started 的注释 ⇒ 守卫必须红", GATE,
     "def source_cases(text):",
     "# R86 变异：这一行里有 started 这个词，那道『两支闸门不冗余』的守卫必须因此红\n"
     "def source_cases(text):"),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests",
                           "-p", "test_ui_probe_report.py"],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr


def verdicts(text):
    if any(k in text for k in ("unittest.loader._FailedTest", "ImportError", "SyntaxError")):
        # 形状要一致：调用方按三元组解包（R85 那一课 —— 分类器自己返回两种形状，
        # 于是"模块级就崩了"这一支会把整批电池炸成 TypeError 而不是报成 ESCAPED）。
        return {"<import-error>": "red"}, 0, False
    out = {}
    for name in re.findall(r"^(?:FAIL|ERROR): (\w+) ", text, re.M):
        out[name] = "red"
    ran = re.search(r"Ran (\d+) tests", text)
    ok = "\nOK" in text
    return out, (int(ran.group(1)) if ran else 0), ok


def main():
    measure = "--measure" in sys.argv
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在（同一时间只准跑一个电池）" % LOCK)
        return 2
    open(LOCK, "w").write(str(os.getpid()))
    results = []
    try:
        originals = {}
        for _, _, path, _, _ in MUTATIONS:
            originals.setdefault(path, read(path))
        print("=== 基线（未变异）：这一族用例必须全绿 ===")
        base = run_tests()
        reds, ran, ok = verdicts(base)
        print("   Ran=%d OK=%s 红=%s" % (ran, ok, sorted(reds)))
        if reds or not ok:
            print("DRIFT-BASELINE 基线不绿 ⇒ 整批作废")
            return 1
        for tag, note, path, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            text = read(path)
            if text.count(needle) != 1:
                print("   NOT-APPLIED 锚点出现 %d 次（要 1 次）" % text.count(needle))
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, text.replace(needle, replacement, 1))
            # 回读只问"文件变了没有"，不问"原串还在不在"：
            # 纯插入型的刀（M472 就是）变异文里**必然**包含原串，用后者会把落地成功的刀报成未落地
            # （R76 的 M398 / M399 同一族，本轮第三次撞上，所以这次改判据而不是改刀）。
            if read(path) == text:
                print("   NOT-APPLIED 回读证明文件没变")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            try:
                out = run_tests()
                reds, ran, ok = verdicts(out)
                names = sorted(reds)
                if not names:
                    print("   ESCAPED 变异落地了却一条用例都没红（Ran=%d OK=%s）" % (ran, ok))
                    results.append((tag, "ESCAPED"))
                elif measure:
                    print("   MEASURE 红在：%s" % ", ".join(names))
                    results.append((tag, "MEASURED"))
                elif names == sorted(EXPECTED.get(tag, [])):
                    print("   CAUGHT 只红在预期那几条：%s" % ", ".join(names))
                    results.append((tag, "CAUGHT"))
                else:
                    print("   MISMATCH 实际=%s 预期=%s（先跑 --measure 再抄）"
                          % (", ".join(names), ", ".join(sorted(EXPECTED.get(tag, [])))))
                    results.append((tag, "MISMATCH"))
                for line in [l[:170] for l in out.splitlines()
                             if l.startswith(("FAIL:", "ERROR:"))][:3]:
                    print("     " + line)
            finally:
                write(path, originals[path])
                print("   已还原（逐字节相同：%s）" % (read(path) == originals[path]))
        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d 与预期不符=%d 量过=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0), counts.get("NOT-RUN", 0),
                 counts.get("NOT-APPLIED", 0), counts.get("MISMATCH", 0), counts.get("MEASURED", 0)))
        if measure:
            return 0
        bad = sum(counts.get(k, 0) for k in ("ESCAPED", "NOT-RUN", "NOT-APPLIED", "MISMATCH"))
        return 0 if bad == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
