#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R87 的变异电池：位置尺的行程证据到底有没有牙（`loopAdjudication` 新那一支）。

背景（读 R86 的 CI 读出来的，run 38811457259 = main 红）：同一份产品代码，coverage 三遍
0.522 / 0.842 / **0.032**，而位置尺在同一卷上量到的行程是 109pt / 134pt / **134pt**
（可用帧 11 / 12 / 12）。第三遍 coverage 把产品判成红，而样本多 6 倍的那把尺说亮带走完了整幅。
⇒ 新那一支 `notRunRulerBlind` 的作用是：**两把尺矛盾时，样本少的那把不许定罪产品**，
而它自己也不许被读成"验过了"（点名成有名字的未覆盖 + 登记在 `loops` 那一节）。

八刀（先 `--measure` 再抄 EXPECTED，R42 定的流程）：
  M473 删掉矛盾那一支（coverage 又能单独定罪）        ⇒ 真值表那格红
  M474 矛盾那一支从"未覆盖"改成"判绿"（放行成验过了）  ⇒ 同一格红，且红得不同
  M475 行程证据不看可用帧数（1 帧也算读过）            ⇒ travelEvidence 那格红
  M476 行程地板失效（走 0pt 也算走过）                 ⇒ notSweeping 那格红
  M477 矛盾检查排在证人之前（坏掉的尺反过来替产品开脱）⇒ 顺序那格红
  M478 新理由借用旧名字（登记表看不出多了一种病）      ⇒ 两条理由断言红
  M479 登记表里删掉新理由（两边不同步）                ⇒ 闸门那一格红
  M480 没登记的理由不红（BAD_REASON 变哑）             ⇒ 闸门两格红
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
GATE = "scripts/motion_floor_gate.py"
EXPECT = "scripts/motion_floor_expectations.json"
LOCK = "/tmp/r87_mutation.lock"

TRUTH = "testTheLoopShapeClassifierIsATruthTable"
GATE_LOOP = "testLoopStateLinesAreCountedNotGuessed"
GATE_REAL = "testRealLocalLogIsRedUnderTheTightenedRegistry"
BAND = "testSkeletonSweepIsOneBand"
SHIM = "testSkeletonSweepActuallySweeps"
MIRROR = "testTheLoopWitnessStillMirrorsTheProductLoop"
SWIFT_CASES = [TRUTH, MIRROR, BAND, SHIM]
SWIFT_FILTER = "|".join("MotionFilmstripTests/" + c for c in SWIFT_CASES)
PY_CASES = [GATE_LOOP, GATE_REAL]

EXPECTED = {
    # 每一行都是从 `--measure` 那一遍的输出里抄的（R42 定的流程：期望只能从实测抄）。
    "M473": [TRUTH],
    "M474": [TRUTH],
    "M475": [TRUTH],
    "M476": [TRUTH],
    "M477": [TRUTH],
    "M478": [TRUTH],
    "M479": [GATE_LOOP],
    "M480": [GATE_LOOP],
}

MUTATIONS = [
    ("M473", "删掉『两把尺矛盾时不许定罪产品』那一支（coverage 又能单独判红）", MFT,
     "        if travel == .sweeping { return .notRunRulerBlind }\n",
     ""),
    ("M474", "矛盾那一支从『有名字的未覆盖』改成『判绿』⇒ 尺的账被写成产品验过了", MFT,
     "        if travel == .sweeping { return .notRunRulerBlind }",
     "        if travel == .sweeping { return .ok }"),
    ("M475", "行程证据不看可用帧数（一帧也算读过）", MFT,
     "        guard reading.framesUsed >= minimumBandFrames else { return .unreadable }",
     "        guard reading.framesUsed >= 1 else { return .unreadable }  // R87 变异"),
    ("M476", "行程地板失效（亮带钉在原地也算走过整幅）", MFT,
     "        return reading.travelPoints >= sweepTravelFloorPoints ? .sweeping : .notSweeping",
     "        return reading.travelPoints >= 0 ? .sweeping : .notSweeping  // R87 变异"),
    ("M477", "矛盾检查排到证人签字之前 ⇒ 一把坏掉的尺反过来替产品开脱", MFT,
     "        if coarseWitness == .notMoving { return .witnessDead }",
     "        if travel == .sweeping { return .notRunRulerBlind }\n"
     "        if coarseWitness == .notMoving { return .witnessDead }"),
    ("M478", "新理由借用旧名字（登记表看不出多了一种坏法）", MFT,
     '        case .notRunRulerBlind: return "loop-coverage-contradicted-by-travel"',
     '        case .notRunRulerBlind: return "loop-clock-not-sustainable-at-product-rate"'),
    ("M479", "登记表里删掉新理由（判据改了名字而表没跟着改）", EXPECT,
     '        "loop-coverage-contradicted-by-travel",\n',
     ""),
    ("M480", "没登记的理由不红（BAD_REASON 那一格变哑）", GATE,
     '                            "同一臂换了一种坏法就是新缺陷，要先写清它是什么再放行%s"\n'
     '                            % (base or "-", ",".join(sorted(allowed)) or "-", suffix), True))',
     '                            "同一臂换了一种坏法就是新缺陷，要先写清它是什么再放行%s"\n'
     '                            % (base or "-", ",".join(sorted(allowed)) or "-", suffix), False))'),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_swift_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r87_mutation_motion"
    proc = subprocess.run(["swift", "test", "--filter", SWIFT_FILTER],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=2400)
    return proc.stdout + proc.stderr


def run_python_once():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests",
                           "-p", "test_motion_floor_gate.py"],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr


CRASH_MARKERS = ("Fatal error", "Precondition failure", "index out of range",
                 "Exited with unexpected signal", "signal code ")


def swift_verdicts(text):
    out = {}
    crashed = any(marker in text for marker in CRASH_MARKERS)
    for case in SWIFT_CASES:
        if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text):
            out[case] = "red"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text):
            out[case] = "green"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' skipped" % re.escape(case), text):
            out[case] = "skipped"
        elif re.search(r"error: -\[[^\]]*\b%s\b" % re.escape(case), text):
            out[case] = "crashed" if crashed else "errored"
        else:
            out[case] = "absent"
    return out


def python_verdicts(text):
    if any(k in text for k in ("unittest.loader._FailedTest", "ImportError", "SyntaxError")):
        return dict((c, "import-error") for c in PY_CASES)
    out = {}
    for case in PY_CASES:
        out[case] = "red" if (("FAIL: %s" % case) in text or ("ERROR: %s" % case) in text) else "green"
    return out


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
        print("=== 基线（未变异）：四格 Swift 判据 + 两格 python 用例都必须绿 ===")
        pymarks = python_verdicts(run_python_once())
        marks = swift_verdicts(run_swift_once())
        print("   python=%s swift=%s" % (pymarks, marks))
        if any(v != "green" for v in pymarks.values()) or any(v != "green" for v in marks.values()):
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
            if read(path) == text:
                print("   NOT-APPLIED 回读证明文件没变")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            try:
                if path == MFT:
                    out = run_swift_once()
                    marks = swift_verdicts(out)
                    reds = [c for c in SWIFT_CASES if marks[c] in ("red", "crashed")]
                    pymarks = {}
                else:
                    out = run_python_once()
                    pymarks = python_verdicts(out)
                    reds = [c for c in PY_CASES if pymarks[c] in ("red", "import-error")]
                    marks = {}
                want = EXPECTED.get(tag, [])
                if "error:" in out and not reds and path == MFT:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in out.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif measure:
                    print("   MEASURE 红在：%s" % (", ".join(reds) or "（没有一条红）"))
                    results.append((tag, "MEASURED" if reds else "ESCAPED"))
                elif reds == want:
                    print("   CAUGHT 只红在预期那几条：%s" % (marks or pymarks))
                    results.append((tag, "CAUGHT"))
                else:
                    print("   MISMATCH 实际=%s 预期=%s" % (reds, want))
                    results.append((tag, "MISMATCH"))
                for line in [l[:200] for l in out.splitlines()
                             if "error: -[" in l or l.startswith(("FAIL:", "ERROR:"))][:3]:
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
