#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R52 变异对照：动效覆盖地板闸门新加的那三样（SKIPS 命名 / THIN / 地板从清单算）。

为什么这一族特别需要变异：R52 做的事是**把一条登记改松**（`notice-banner` 从 must_judge 改成放行），
理由是它被实测推翻过两次。改松这件事本身极易变成"为了让 CI 变绿"，
所以每一处放宽都要有一支"少了它就会漏"的变异钉住它仍然在管东西：

  M254 拿掉 NO_RESOLVE 时打印 skip 原因           ⇒ 那条红又变成没有名字（R36 的规矩被破）
  M255 拿掉 THIN 那一族检查                      ⇒ "横幅这一族今天一臂都没被看"重新变成没人说
  M256 地板写回常量 2（不再从清单算）             ⇒ 清单改松之后地板不会跟着动 = 恒红或恒绿
  M257 `MOTION_FLOOR_OK` 回到"只有一条结果都没有才打" ⇒ 绿与"什么都没判"在日志里长得一样
  M258 登记表里把 notice-banner 改回 must_judge   ⇒ 本机真日志必须重新红（放宽是有条件的，不是永久）
  M259 skip 解析器只认带 `MOTION_NOT_RUN=` 的行   ⇒ 整族缺席那种原因又被漏掉

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GATE = os.path.join(ROOT, "scripts/motion_floor_gate.py")
EXPECT = os.path.join(ROOT, "scripts/motion_floor_expectations.json")
MODULE = "scripts.tests.test_motion_floor_gate"

SKIPS_BLOCK = re.compile(r"        skips = facts\.get\(\"skips\"\) or \[\].*?        return out\n", re.S)
THIN_BLOCK = re.compile(r"    for group in expectations\.get\(\"thin_warnings\", \[\]\):.*?    floor = len\(must_judge\)\n", re.S)
FLOOR = "    floor = len(must_judge)"
OK = "    if reds == 0:"
SKIP_RE = 'SKIP_LINE = re.compile(r"-\\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\\][^\\n]*?: Test skipped - (.+)")'

MUTATIONS = [
    ("M254", "NO_RESOLVE 不再打印 skip 原因", GATE, SKIPS_BLOCK,
     "        return out\n", "regex",
     ['testSilentRunnerLogRedsAndNamesTheSkips']),
    ("M255", "删掉 THIN 这一族检查", GATE, THIN_BLOCK,
     "    floor = len(must_judge)\n", "regex",
     ['testRealLocalLogIsGreenButThin', 'testThinWarningNeedsARegisteredReasonForEachAbsentArm']),
    ("M256", "地板写回常量 2", GATE, FLOOR,
     "    floor = 2   # MUTANT", "str",
     ['testFloorIsTheMustJudgeCountNotTwo']),
    ("M257", "OK 只在一条结果都没有时才打", GATE, OK,
     "    if not results:   # MUTANT", "str",
     ['testGateExitCodeFollowsTheReds']),
    ("M258", "登记表把 notice-banner 改回必须判到", EXPECT,
     '"notice-banner": {\n      "must_judge": false,',
     '"notice-banner": {\n      "must_judge": true,', "str",
     ['testRealLocalLogIsGreenButThin']),
    ("M259", "skip 解析器只认带自家前缀的行", GATE, SKIP_RE,
     'SKIP_LINE = re.compile(r"-\\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\\][^\\n]*?: Test skipped - (MOTION_NOT_RUN=.+)")   # MUTANT',
     "str", ['testSkipReasonWithoutTheMotionPrefixIsStillSurfaced']),
]


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", MODULE],
                          cwd=ROOT, capture_output=True, text=True, timeout=600)
    out = proc.stdout + proc.stderr
    bad = re.findall(r"^(?:FAIL|ERROR): (\w+)", out, re.M)
    summary = [l for l in out.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, sorted(set(bad)), summary


def apply(path, old, new, mode):
    text = open(path, encoding="utf-8").read()
    if mode == "regex":
        hits = list(re.findall(old, text))
        if len(hits) != 1:
            raise SystemExit("注入中止：正则命中 %d 次，不是 1 次 —— 电池与代码脱节" % len(hits))
        written = re.sub(old, new.replace("\\", "\\\\"), text, count=1)
    else:
        n = text.count(old)
        if n != 1:
            raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:120]))
        written = text.replace(old, new, 1)
    if written == text:
        raise SystemExit("注入中止：替换后文本没变（锚点与替换串相同？）")
    with open(path, "w", encoding="utf-8") as f:
        f.write(written)
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as f:
        f.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    code, out, bad, summary = run_tests()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-3000:])
    print("预检 OK（未变异时全绿）：" + " | ".join(summary))
    results = []
    for mid, desc, path, old, new, mode, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new, mode)
        try:
            code, out, bad, summary = run_tests()
        finally:
            ok = restore(path, original)
        hit = [n for n in needles if n in bad]
        right = code == "CAUGHT" and len(hit) == len(needles)
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO", ",".join(bad)))
        print("\n%s %s ⇒ %s 红得对=%s\n   红在 %s\n   %s" % (mid, desc, code, right, bad, " | ".join(summary)))
        if measure or not right:
            for line in out.splitlines():
                if line.startswith(("FAIL:", "ERROR:", "AssertionError", "ValueError", "  File")):
                    print("   MSG| " + line.strip()[:200])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad_rows = [r for r in results if r[2] != "yes"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对=%d  还原不干净=%d" % (len(bad_rows), len(dirty)))
    # 还原之后必须重新全绿，否则说明电池把文件改坏了
    code, out, _, summary = run_tests()
    print("还原后复跑：" + " | ".join(summary))
    if dirty or bad_rows or code != "ESCAPED":
        raise SystemExit("R52_MUTATION_PROBLEM")


main()
