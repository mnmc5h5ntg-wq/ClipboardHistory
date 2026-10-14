#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R48 变异对照：「变化段必须连续」这件事，每一条护栏各拆一次都要有人拦。

为什么这一族特别需要变异：本轮改的全是**尺子**，产品一个像素没动。
尺子悄悄退化时界面上什么都不会变，只有台账上那句话开始说谎。

  M230 分段退化成跨度（永远不断段）        ⇒ 真值表第 ②③④ 格该红
  M231 地板写成严格不等号                  ⇒ 第 ⑥ 格该红（含等号那一格）
  M232 去掉收尾哨格                        ⇒ 第 ⑦ 格该红（变到卷尾的那段没人闭合）
  M233 取**最长**那段而不是含峰值那段      ⇒ 第 ④ 格该红
  M234 取第一段                            ⇒ 第 ③ 格该红
  M235 A/B 的某一臂换回跨度那把尺          ⇒ 调用点守卫该红
  M236 区域助手退化成"整文件"              ⇒ 守卫里那条"区域不许吞下一个成员"该红
  M237 A/B 少一臂（B 直接抄 A）            ⇒ 守卫里的 uses≥3 计数该红

needle 一律从 --measure 那一遍的失败消息原文里抄（R42 立的流程：
上一族"红得不对"犯了三次，根因就是把该红在哪一句推理了一遍没实测）。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILM = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = ("MotionFilmstripTests."
          "(testChangedRunMustBeContiguousNotFirstToLast"
          "|testFadeABReadsTheContiguousRulerNotTheSpan"
          "|testFadeVisibilityJudgesTimeNotFrameCount)")

MOVING = "            let moving = index < fractions.count && fractions[index] >= floor"
PICKER = ("        contiguousChangedRuns(stamps: stamps, fractions: fractions)\n"
          "            .max { $0.peak == $1.peak ? $0.elapsedMilliseconds < $1.elapsedMilliseconds : $0.peak < $1.peak }")
LOOP = "        for index in 0...fractions.count {"
ARM_A = "        let elapsedA = runA?.elapsedMilliseconds"
ARM_B = "        let elapsedB = runB?.elapsedMilliseconds"
GATE = ("        if declaredMilliseconds > 0,\n"
        "           max(worstOnA, worstOnB) > declaredMilliseconds * unresolvableIntervalRatio {")
THRESH = "max(worstOnA, worstOnB) > declaredMilliseconds * unresolvableIntervalRatio {"
BREAK = "            if opened, depth <= 0 { break }"

MUTATIONS = [
    ("M230", "分段退化成跨度", FILM, MOVING,
     "            let moving = index < fractions.count   // MUTANT：永不断段",
     [('("356.0") is not equal to ("24.0")')]),
    ("M231", "地板写成严格不等号", FILM, MOVING,
     "            let moving = index < fractions.count && fractions[index] > floor   // MUTANT",
     ['写成严格不等式会让这一格随浮点误差翻脸']),
    ("M232", "去掉收尾哨格", FILM, LOOP,
     "        for index in 0..<fractions.count {         // MUTANT",
     [('("-1.0") is not equal to ("16.0")')]),
    ("M233", "取最长而不是含峰值", FILM, PICKER,
     "        contiguousChangedRuns(stamps: stamps, fractions: fractions)\n"
     "            .max { $0.elapsedMilliseconds < $1.elapsedMilliseconds }   // MUTANT",
     ['380ms 那段峰值只有']),
    ("M234", "取第一段", FILM, PICKER,
     "        contiguousChangedRuns(stamps: stamps, fractions: fractions).first   // MUTANT",
     ['峰值那一段是 fractions']),
    ("M235", "A/B 的一臂换回跨度那把尺", FILM, ARM_A,
     "        let elapsedA = Self.changedSpanElapsedMilliseconds(stamps: onFilmA.motionStamps,\n"
     "                                                           fractions: onA)   // MUTANT",
     ['不再是 `runA` 那一段的时长']),
    ("M236", "区域助手退化成整文件", FILM, BREAK,
     "            if opened, depth <= -1000 { break }    // MUTANT",
     ['区域把下一个成员也吞了']),
    ("M237", "A/B 少一臂（抄别的臂）", FILM, ARM_B,
     "        let elapsedB = elapsedA                    // MUTANT",
     ['不再是 `runB` 那一段的时长']),
    ("M238", "拆掉分辨率门", FILM, GATE,
     "        if false, declaredMilliseconds > 0,\n"
     "           max(worstOnA, worstOnB) > declaredMilliseconds * unresolvableIntervalRatio {   // MUTANT",
     ['is not equal to ("clockTooCoarse']),
    ("M239", "分辨率阈值用错档（0.3 当 0.5）", FILM, THRESH,
     "max(worstOnA, worstOnB) > declaredMilliseconds * Self.coarseRunRatio {   // MUTANT",
     ['worstOnA: 125.0']),
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
    print("预检 OK（未变异时这两条判据全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        if code in ('BROKEN-MUTATION', 'DID-NOT-RUN'):
            open('/tmp/r48-broken-%s.log' % mid, 'w', encoding='utf-8').write(out)
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
