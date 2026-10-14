#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R47 变异对照：那条 A/B 的每一个门槛，各拆掉一次都要有用例拦住。

这一族特别需要变异，因为它判的是"尺子能不能看见"——
判据如果悄悄退化，没有任何用户界面会变，只有台账上那句话开始说谎。

  M223 拆掉**上限**（比声明还长的变化段也算看见）    ⇒ 真值表第 ⑨ 格该红
  M224 拆掉**下限**（短于 0.3×声明也算）              ⇒ 第 ⑪ 格该红
  M225 拆掉**归因门**（不比对照臂也算看见）            ⇒ 第 ⑤⑥⑫ 格该红
  M226 拆掉 **A/A 矛盾检测**（两遍不一致照旧下结论）    ⇒ 第 ⑦ 格该红
  M227 "读不出"当成看见                              ⇒ 第 ④ 格该红
  M228 拆掉峰值地板（无对照物也下结论）                ⇒ 第 ① 格该红
  M229 归因只看运气好的那一遍                        ⇒ 第 ⑫ 格该红

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILM = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "testFadeVisibilityJudgesTimeNotFrameCount"

UPPER = ("        return elapsed >= declaredMilliseconds * coarseRunRatio\n"
         "            && elapsed <= declaredMilliseconds + 2 * max(intervalMilliseconds, 1)")
ATTRIB = ("        return min(first, second) - off >= intervalMilliseconds\n"
          "            ? .visibleToThisRuler : .notVisibleToThisRuler")
CONTRA = "        if a != b { return .inconsistent(onA: elapsedOnA, onB: elapsedOnB) }"
NIL_SEEN = "        guard let elapsed else { return false }      // 读不出变化段 = 没看见，不是\"看不见也算数\""
PEAK_FLOOR = "        guard peakOn >= minimumVisibleChange else { return nil }"

MUTATIONS = [
    ("M223", "拆掉上限", FILM, UPPER,
     "        return elapsed >= declaredMilliseconds * coarseRunRatio  // MUTANT",
     ['259ms 比声明的 160ms 长出一截']),
    ("M224", "拆掉下限", FILM, UPPER,
     "        return elapsed <= declaredMilliseconds + 2 * max(intervalMilliseconds, 1)  // MUTANT",
     ['短于 0.3×声明的一段变化不许因为']),
    ("M225", "拆掉归因门", FILM, ATTRIB,
     "        return true ? .visibleToThisRuler : .notVisibleToThisRuler  // MUTANT",
     ['两臂时长差不到一个采样间隔', '对照臂也这么长']),
    ("M226", "拆掉 A/A 矛盾检测", FILM, CONTRA,
     "        if false { return .inconsistent(onA: elapsedOnA, onB: elapsedOnB) }  // MUTANT",
     ['inconsistent(onA: Optional(265.0), onB: Optional(7.0))']),
    ("M227", "读不出当成看见", FILM, NIL_SEEN,
     "        guard let elapsed else { return true }   // MUTANT", ['inconsistent(onA: nil, onB: Optional(120.0))']),
    ("M228", "拆掉峰值地板", FILM, PEAK_FLOOR,
     "        guard peakOn >= 0 else { return nil }    // MUTANT", ['没有对照物时说「看不见」']),
    ("M229", "归因只看第一遍", FILM, ATTRIB,
     "        return first - off >= intervalMilliseconds\n"
     "            ? .visibleToThisRuler : .notVisibleToThisRuler  // MUTANT",
     ['两臂里较短的那个没超过对照臂一个间隔']),
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
        raise SystemExit("预检失败：" + code + "\n" + out[-1500:])
    print("预检 OK（未变异时这条判据全绿）")
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
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:360])
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
