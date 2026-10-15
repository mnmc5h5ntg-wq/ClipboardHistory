#!/usr/bin/env python3
"""R85 的变异对照：登记表那一层（`loops`）与它读的两行状态。

背景（读 R84 的 CI 读出来的，run 38798408040 = 这一族第一次在 runner 上判到）：
  * 常驻循环那一族（扫光的运动判据 + R84 新加的位置判据）不在覆盖地板的 `arms` 形状里 ——
    它红的时候走 SUITE_RED，它**整行消失**的时候没人知道今天判没判 ⇒ BACKLOG 118 开在 R83。
  * 本轮的修法：判据各自打一行状态（`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`，
    取值 ok / productRed / notRunEnvironment / witnessDead / skipped + 一个名字），
    登记表 `loops` 那一节只判两格：点名在登记之内 ⇒ 不红但打一行看得见的未覆盖；
    状态行整行缺席 ⇒ LOOP_SILENT 红。

七刀（M461/M462 在第一版**逃掉过**，见 U-174：守卫只断言"函数体里出现过这个串"时，
删掉正常路径那一行仍有 skip 分支那一行喂饱它 ⇒ 改成数次数要等于 2。
于是这一批必须两边各删一次，才叫"两条出口各自都要打"真的被钉住）：
  M458 LOOP_SILENT 从红改成不红（缺席被放行）      ⇒ 新那格 python 用例 + 真日志那格都该红
  M459 LOOP_NOT_JUDGED 改成红（点名也拦发布）      ⇒ 新那格该红（登记是放行，不是等号）
  M460 理由匹配不剥括号后缀                        ⇒ 新那格该红（换一种"读不出"就冒红，
                                                     结果是有人把后缀删掉 —— 后缀正是有用的一半）
  M461 位置判据不再打状态行（正常路径那条出口）    ⇒ 镜像守卫那格该红（登记表读的东西消失了）
  M462 循环判据不再打状态行（正常路径那条出口）    ⇒ 同上
  M463 位置判据不再打状态行（能力闸门 skip 那条）  ⇒ 同上（第一版就是这一行把断言喂饱的）
  M464 循环判据不再打状态行（能力闸门 skip 那条）  ⇒ 同上
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
GATE = "scripts/motion_floor_gate.py"
LOCK = "/tmp/r85_mutation.lock"

LOOP = "testLoopStateLinesAreCountedNotGuessed"
REAL = "testRealLocalLogIsRedUnderTheTightenedRegistry"
PY_TESTS = [LOOP, REAL]
MIRROR = "testTheLoopWitnessStillMirrorsTheProductLoop"
BAND = "testSkeletonSweepIsOneBand"
SHIM = "testSkeletonSweepActuallySweeps"
CASES = [MIRROR, BAND, SHIM]
FILTER = "|".join("MotionFilmstripTests/" + c for c in CASES)

EXPECTED = {
    "M458": [LOOP, REAL],
    "M459": [LOOP],
    "M460": [LOOP],
    "M461": [MIRROR],
    "M462": [MIRROR],
    "M463": [MIRROR],
    "M464": [MIRROR],
}

MUTATIONS = [
    ("M458", "状态行整行缺席时不红（把 LOOP_SILENT 变成一行废话）", GATE,
     '                        "（只有退出码的红等于没有红）在循环这一族的形状" % (line, name), True))',
     '                        "（只有退出码的红等于没有红）在循环这一族的形状" % (line, name), False))'),
    ("M459", "登记过的点名也拦发布（登记表就从放行变成另一道恒红）", GATE,
     '                            "不许因为不红就当成验过了%s" % (base, suffix), False))',
     '                            "不许因为不红就当成验过了%s" % (base, suffix), True))'),
    ("M460", "理由匹配不剥括号后缀（换一种读不出就冒红 ⇒ 逼人删掉有用的那半截）", GATE,
     '        base = reason.split("(")[0]',
     '        base = reason  # R85 变异：后缀也参加匹配'),
    ("M461", "位置判据不再打状态行（登记表那一族从此没有可读状态）", MFT,
     '        emit("MOTION_SHIMMER_BAND_STATE 判定=\\(Self.bandStateLabel(bandDisposition)) '
     '原因=\\(bandReason)")',
     '        // R85 变异：状态行被删掉'),
    ("M462", "循环判据不再打状态行（同上，另一条判据）", MFT,
     '        emit("MOTION_SHIMMER_STATE 判定=\\(Self.loopStateLabel(disposition)) "\n'
     '            + "原因=\\(Self.loopStateReason(disposition))")',
     '        // R85 变异：状态行被删掉'),
    # M463/M464：另一条出口。第一版守卫只断言"出现过"，这两行就是当时把断言喂饱的那两行；
    # 现在两边各删一次，才证明"两条出口各自都要打"这句话真的会红，而不是只钉住了一条。
    ("M463", "位置判据在能力闸门那条出口不再打状态行（第一版逃掉的那条路）", MFT,
     '            emit("MOTION_SHIMMER_BAND_STATE 判定=skipped 原因=capability-gate")\n',
     ''),
    ("M464", "循环判据在能力闸门那条出口不再打状态行（同上，另一条判据）", MFT,
     '            emit("MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate")\n',
     ''),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_swift_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r85_mutation_motion"
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
    # U-164 那一课：模块级导入/语法失败时每条用例名都不出现，旧分类器会读成"全绿"。
    if any(k in text for k in ("unittest.loader._FailedTest", "ImportError", "SyntaxError")):
        return dict((c, "import-error") for c in PY_TESTS)
    out = {}
    for case in PY_TESTS:
        if ("FAIL: %s" % case) in text or ("ERROR: %s" % case) in text:
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
        originals = {}
        for _, _, path, _, _ in MUTATIONS:
            originals.setdefault(path, read(path))
        print("=== 基线（未变异）：两条 python 用例 + 三条 Swift 判据都必须绿 ===")
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
                results.append((tag, "NOT-APPLIED")); continue
            write(path, text.replace(needle, replacement, 1))
            if needle in read(path):
                print("   NOT-APPLIED 回读证明没落地")
                write(path, originals[path]); results.append((tag, "NOT-APPLIED")); continue
            try:
                if path == GATE:
                    out = run_python_once()
                    pymarks = python_verdicts(out)
                    reds = [c for c in PY_TESTS if pymarks[c] in ("red", "import-error")]
                    marks = {}
                else:
                    out = run_swift_once()
                    marks = swift_verdicts(out)
                    reds = [c for c in CASES if marks[c] in ("red", "crashed")]
                    pymarks = {}
                want = EXPECTED[tag]
                if "error:" in out and not reds and path != GATE:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in out.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif reds == want:
                    print("   CAUGHT 只红在预期那几条：%s" % (marks or pymarks))
                    results.append((tag, "CAUGHT"))
                else:
                    print("   ESCAPED 红的不是预期那几条：%s 预期=%s" % (marks or pymarks, want))
                    results.append((tag, "ESCAPED"))
                for line in [l[:200] for l in out.splitlines()
                             if "error: -[" in l or l.startswith("FAIL:")][:3]:
                    print("     " + line)
            finally:
                write(path, originals[path])
                print("   已还原（逐字节相同：%s）" % (read(path) == originals[path]))
        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0),
                 counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        bad = sum(counts.get(k, 0) for k in ("ESCAPED", "NOT-RUN", "NOT-APPLIED"))
        return 0 if bad == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
