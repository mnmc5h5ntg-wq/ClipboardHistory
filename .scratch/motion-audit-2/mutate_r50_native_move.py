#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R50 变异对照：`nativeMoveVerdict` 的三态，每一态各拆一次都要有人拦。

为什么这一族特别需要变异：这条判据**本机从来跑不到**（进程无法激活 ⇒ skip），
它唯一一次出结论是在 runner 上，而那次给的是红。
一条"只在别的机器上、偶尔才跑、跑出来是红"的判据，如果它的三态分界是错的，
没有任何人会在本机发现 —— 所以分界必须由真值表 + 变异钉死。

  M245 把"瞬移"永远判成"采样错过"   ⇒ 第 ② 格该红（runner 今天的真读数被洗成噪声）
  M246 把"采样错过"永远判成"瞬移"   ⇒ 第 ③⑦ 格该红（把探针的问题算到产品头上）
  M247 帧数门槛写成严格大于          ⇒ 第 ⑤ 格该红（正好 2 帧时翻脸）
  M248 峰值差去掉绝对值              ⇒ 第 ⑦ 格该红（开臂变得比对照还少时被读成"一致"）

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILM = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "MotionFilmstripTests.testNativeMoveVerdictSeparatesJumpFromMissedSampling"

PICK = ("        return sameShape\n"
        "            ? .notAnimated(animatedSpan: animatedSpan, animatedPeak: animatedPeak,\n"
        "                           instantSpan: instantSpan, instantPeak: instantPeak)\n"
        "            : .samplingMissed(animatedSpan: animatedSpan, animatedPeak: animatedPeak,\n"
        "                              instantSpan: instantSpan, instantPeak: instantPeak)")
FRAME_GATE = "        if animatedSpan >= minimumFrames { return .animated }"
SHAPE = "        let sameShape = abs(animatedPeak - instantPeak) <= nativeMovePeakTolerance"

MUTATIONS = [
    ("M245", "瞬移永远判成采样错过", FILM, PICK,
     "        return .samplingMissed(animatedSpan: animatedSpan, animatedPeak: animatedPeak,\n"
     "                              instantSpan: instantSpan, instantPeak: instantPeak)  // MUTANT",
     ['is not equal to ("notAnimated']),
    ("M246", "采样错过永远判成瞬移", FILM, PICK,
     "        return .notAnimated(animatedSpan: animatedSpan, animatedPeak: animatedPeak,\n"
     "                           instantSpan: instantSpan, instantPeak: instantPeak)  // MUTANT",
     ['animatedPeak: 0.09']),
    ("M247", "帧数门槛写成严格大于", FILM, FRAME_GATE,
     "        if animatedSpan > minimumFrames { return .animated }   // MUTANT",
     ['is not equal to ("animated")']),
    ("M248", "峰值差去掉绝对值", FILM, SHAPE,
     "        let sameShape = (animatedPeak - instantPeak) <= nativeMovePeakTolerance   // MUTANT",
     ['animatedPeak: 0.03']),
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
    print("预检 OK（未变异时这条真值表全绿）")
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
                print("   MSG| " + line.strip()[:420])
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
