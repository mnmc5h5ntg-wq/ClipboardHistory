#!/usr/bin/env python3
"""R83 的变异对照：前提尺（`FilmPremise`）、处置豁免、以及闸门那格 NAMELESS 的比较单位。

背景（读 R82 的 CI 读出来的，run 38781113064）：
  * 114 的答案是**第一支**：runner 那一遍产品 `帧数=21 变化帧对=0 峰值=0.000`、
    等节拍证人 `帧对=35 在变=2 coverage=0.284`、粗节拍证人 `帧对=26 在变=23 coverage=1.000`
    ⇒ 处置正确走了 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`。
  * 但那一步仍然红，红在**我自己上一轮加的两条**：
      - `XCTAssertEqualWithAccuracy ("0.0") vs ("2500.0")` —— 卷长钉子挂在
        `LoopShape.recordedMilliseconds` 上，而它在峰值 0 时被 guard 归零
        ⇒ "这台机器看不见运动"被改写成"探针坏了"（假红）。
      - `XCTAssertGreaterThan ("0.0") is not greater than ("0.005")` —— 绝对峰值地板不管处置说话
        ⇒ 同一件事被报两次，其中一次把环境说成产品。
  * 另外 `MOTION_FLOOR_SUITE_NAMELESS_RED=1` 也是一朵假红：汇总行数的单位是**失败断言行**，
    而旧算法拿它去减**用例名**个数（一条用例里两句断言一起红 ⇒ 2-1=1 "没名字"）。

五刀（两刀本地有牙、两刀本地无判别力由 CI 判、一刀量的是 python 闸门）：
  M446 `paired` 丢掉时刻条数那条等式            ⇒ LOOP 真值表第⑧格该红（本地有牙）
  M447 卷长少乘一个 1000（ms 算成 s）       ⇒ LOOP + SHIM 都该红（两处都吃这个数）
  M448 卷长钉子改回挂在 `shape.recordedMilliseconds` ⇒ **本地无判别力**：本机有运动，两把尺都给 2450
  M449 峰值地板改回不管处置（无条件判）          ⇒ **本地无判别力**：本机处置是 .ok，两条路径同结果
  M450 闸门的 NAMELESS 比较退回"用例名个数"      ⇒ 新增那格 python 回归测试该红（本地有牙）

用法：`python3 .scratch/motion-audit-2/mutate_r83_premise.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
GATE = "scripts/motion_floor_gate.py"
LOCK = "/tmp/r83_mutation.lock"

LOOP = "testTheLoopShapeClassifierIsATruthTable"
SHIM = "testSkeletonSweepActuallySweeps"
CASES = [LOOP, SHIM]
FILTER = "|".join("MotionFilmstripTests/" + c for c in CASES)
EXPECTED = {
    "M446": {"swift": [LOOP], "python": []},
    # 卷长单位错一位，本机也拦得住两条：真值表第⑧格与扫光那一条的卷长钉子**都**吃这个数。
    # 第一版只写了 [LOOP]，于是这一刀被报成 ESCAPED —— 与 U-149 同形（期望太窄是我的错，不是刀的错）。
    "M447": {"swift": [LOOP, SHIM], "python": []},
    # 本地无判别力的两刀：期望就是"全绿"，被抓到的地方是 runner（R82 的 CI 已经现场演示过一次）。
    "M448": {"swift": [], "python": [], "note": "本地无判别力（本机有运动 ⇒ 两把尺同数）⇒ 由 CI 判"},
    "M449": {"swift": [], "python": [], "note": "本地无判别力（本机处置=.ok ⇒ 两条路径同结果）⇒ 由 CI 判"},
    "M450": {"swift": [], "python": ["testTwoAssertionsInOneCaseAreNotCalledNameless"]},
}

MUTATIONS = [
    # 第一版这一刀写的是把 `==` 放宽成 `>=`，结果**逃掉**：少一根时 20 >= 21 仍然是假，
    # 那一格照样绿 —— 又是一次"我以为我在测的那件事和刀真的改的那件事不是同一件"（U-149 同形）。
    ("M446", "`paired` 干脆不看时刻条数（等式整条丢掉）⇒ 时刻少一根也算配对（U-155 的形状回来了）",
     MFT,
     '        let paired = stamps.count == frames && frames > 1',
     '        let paired = frames > 1  // R83 变异：等式整条丢掉'),
    ("M447", "卷长少乘 1000（秒当成毫秒）⇒ 真值表第⑧格必须红",
     MFT,
     '            ? max(0, ((stamps.last ?? 0) - (stamps.first ?? 0)) * 1000) : 0',
     '            ? max(0, ((stamps.last ?? 0) - (stamps.first ?? 0)) * 100) : 0  // R83 变异：单位错'),
    ("M448", "卷长钉子改回挂在**结论尺**的输出上（R82 第一版的形状）",
     MFT,
     '        XCTAssertEqual(premise.spanMilliseconds, loopFilmSeconds * 1000, accuracy: loopFilmSeconds * 250,',
     '        XCTAssertEqual(shape.recordedMilliseconds, loopFilmSeconds * 1000, accuracy: loopFilmSeconds * 250,'),
    ("M449", "峰值地板改回**不管处置**无条件判（R82 的 CI 上就是这么把环境说成产品的）",
     MFT,
     '        if disposition == .ok || disposition == .productRed {',
     '        if true {  // R83 变异：处置不再豁免绝对地板'),
    ("M450", "闸门的 NAMELESS 比较退回拿**用例名个数**当可归因数 ⇒ 新那格回归测试必须红",
     GATE,
     '    attributable = max(facts.get("failure_lines", 0), len(named))',
     '    attributable = len(named)  # R83 变异：单位又对不上了'),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_swift_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r83_mutation_motion"
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
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
PY_TESTS = ["testTwoAssertionsInOneCaseAreNotCalledNameless",
            "testLostFailureLinesStillAreCalledNameless",
            "testNamelessRedIsRed", "testPartialNameLossIsStillRed"]


def swift_verdicts(text):
    out = {}
    crashed = any(marker in text for marker in CRASH_MARKERS)
    for case in CASES:
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
    # 第四种形状（M450 第一版现场教的，与 U-151 / U-158 同族）：**模块级导入失败**时
    # unittest 只打一条 `ERROR: test_motion_floor_gate (unittest.loader._FailedTest…)`，
    # 每条用例的名字都不出现 ⇒ 旧分类器把四个都读成 green，于是"刀把被测脚本改崩了"
    # 被报成"刀没抓到"。导入失败必须算红（它就是这一刀的后果）。
    if "unittest.loader._FailedTest" in text or "ImportError" in text or "SyntaxError" in text:
        return dict((c, "import-error") for c in PY_TESTS)
    out = {}
    for case in PY_TESTS:
        if re.search(r"\b%s\b.*\(.*FAIL", text) or ("FAIL: %s" % case) in text:
            out[case] = "red"
        elif ("ERROR: %s" % case) in text:
            out[case] = "red"
        else:
            out[case] = "green"
    return out


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在" % LOCK)
        return 2
    open(LOCK, "w").write(str(os.getpid()))
    results = []
    try:
        originals = {p: read(p) for _, _, p, _, _ in MUTATIONS}
        print("=== 基线（未变异）：Swift 两条 + 闸门那格都必须绿 ===")
        marks = swift_verdicts(run_swift_once())
        pymarks = python_verdicts(run_python_once())
        print("   swift=%s python=%s" % (marks, pymarks))
        if any(v != "green" for v in marks.values()) or any(v != "green" for v in pymarks.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 整批作废")
            return 1
        for tag, note, path, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            text = read(path)
            if needle not in text:
                print("   NOT-APPLIED 锚点没找到")
                results.append((tag, "NOT-APPLIED")); continue
            write(path, text.replace(needle, replacement, 1))
            if needle in read(path):
                print("   NOT-APPLIED 回读证明没落地")
                write(path, originals[path]); results.append((tag, "NOT-APPLIED")); continue
            try:
                if path == GATE:
                    out = run_python_once()
                    marks = python_verdicts(out)
                    reds = [c for c in PY_TESTS if marks[c] in ("red", "import-error")]
                    if reds and marks[PY_TESTS[0]] == "import-error":
                        # 整模块崩：算抓到，但按实报"是以导入失败的形式"
                        reds = list(want) if want else reds
                else:
                    out = run_swift_once()
                    marks = swift_verdicts(out)
                    reds = [c for c in CASES if marks[c] in ("red", "crashed")]
                expect = EXPECTED[tag]
                want = expect["python"] if path == GATE else expect["swift"]
                if "error: " in out and not reds and "swift" in str(path):
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in out.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif reds == want:
                    if want:
                        print("   CAUGHT 只红在预期那几条：%s" % marks)
                        results.append((tag, "CAUGHT"))
                    else:
                        print("   LOCAL-NO-POWER 本地全绿（%s）⇒ 这一刀的牙在 runner 上，已按实存活"
                              % expect.get("note", ""))
                        results.append((tag, "LOCAL-NO-POWER"))
                else:
                    print("   ESCAPED 红的不是预期那几条：%s 预期=%s" % (marks, want))
                    results.append((tag, "ESCAPED"))
                for line in [l[:220] for l in out.splitlines() if "error: -[" in l or "FAIL:" in l][:3]:
                    print("     " + line)
            finally:
                write(path, originals[path])
                print("   已还原（逐字节相同：%s）" % (read(path) == originals[path]))
        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 本地无判别力(按实存活)=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("LOCAL-NO-POWER", 0),
                 counts.get("ESCAPED", 0), counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        bad = sum(counts.get(k, 0) for k in ("ESCAPED", "NOT-RUN", "NOT-APPLIED"))
        return 0 if bad == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
