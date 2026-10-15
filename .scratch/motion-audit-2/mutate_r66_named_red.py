#!/usr/bin/env python3
"""R66 的变异对照：动效那一步的"红必须有名字"这一层，到底有没有牙（BACKLOG 100）。

被判的两族判据：

  python 侧 `scripts/motion_floor_gate.py`（跑 `scripts/tests/test_motion_floor_gate.py`
  里的 `MotionSuiteRedTests` 与那条被改动的既有格子）
    M350 NAMELESS 那一格关掉            → 必须红在 testNamelessRedIsRed
    M351 未登记的红永远算 0 条          → 必须红在 testRealRunnerRedIsRedAndNamed
    M352 用例级判据从 verdicts 里摘掉    → 必须红在 testSuiteRedSurvivesTheMissingResolveLine
    M353 `]' failed` 改成 `]' passed`   → 必须红在 testParserFindsTheNameAndTheReason
    M354 复刻本轮真踩过的正则 bug（少 `with `）→ 必须红在 testSummaryFailureLineIsParsedInBothShapes
    M355 登记过的红仍然挡发布（反向）     → 必须红在 testRegisteredRedIsVisibleButNotBlocking

  swift 侧 `MotionFilmstripTests`（跑两条**不开窗口**的纯判据）
    M356 证人能分辨时改成"报 skip"      → 必须红在 testTheControlJudgmentIsATruthTable
    M357 地板从 `>` 改成 `>=`           → 必须红在 testTheControlJudgmentIsATruthTable
    M358 把"读不到的帧"(-1) 当成电平     → 必须红在 testTheFadeClockClassifierIsATruthTable
    M359 分类器永远说"能分辨"           → 必须红在 testTheFadeClockClassifierIsATruthTable
    M360 分类器永远不说"探针坏了"        → 必须红在 testTheFadeClockClassifierIsATruthTable
    M361 端点也算中间态（跳变读成斜坡）   → 必须红在 testTheFadeClockClassifierIsATruthTable
    M362 **动产品**：撤掉提示条淡入的驱动 → 必须红在 testListRowsDoNotAnimate…，
         且红在"这台机器看得见 150ms 的淡入"那一句（`.productSnapped`），
         而不是被 `fade-clock-snaps-here` 登记掉 —— 这一刀才是"新登记不是免检牌"的正面证据

三条"电池自己会骗人"的规矩沿用 R64/R65：
① 基线必须先全绿，否则后面每一条"红"都不是证据；
② 每一刀落地要回读确认（原文不在了 **且** 变异文在场），没落地就记 NOT-APPLIED 而不是 CAUGHT；
③ 汇总里"没抓到"与"没跑成"必须分开写（R65 那次一个尾随空格把 6 条抓到的说成 6 条没抓到）。

用法：`python3 .scratch/motion-audit-2/mutate_r66_named_red.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
GATE = "scripts/motion_floor_gate.py"
SWIFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
CONTENT = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/ContentView.swift"
LOCK = "/tmp/r66_mutation.lock"
MOTION_OUT = "/tmp/r66_mut_motion"

PY_CLASS = "scripts.tests.test_motion_floor_gate.MotionSuiteRedTests."

# (编号, 说明, 种类, 文件, 目标用例, 原文, 变异后)
MUTATIONS = [
    ("M350", "NAMELESS 那一格永远不触发 ⇒ 汇总说有 1 条红、日志里 0 个名字时闸门闭嘴",
     "py", GATE, "testNamelessRedIsRed",
     "    if summary > len(named):",
     "    if False and summary > len(named):"),

    ("M351", "未登记的红永远算 0 条 ⇒ runner 那两次 exit 1 会第三次绿过去",
     "py", GATE, "testRealRunnerRedIsRedAndNamed",
     "    unregistered = [name for name in named if name not in registry]",
     "    unregistered = []"),

    ("M352", "把用例级判据从 verdicts 里摘掉 ⇒ 复现旧形状：臂级全绿而这一卷红着",
     "py", GATE, "testSuiteRedSurvivesTheMissingResolveLine",
     "    out.extend(suite_verdicts(facts, expectations))",
     "    pass"),

    ("M353", "红用例的名字根本捞不上来（正则改成只认 passed）",
     "py", GATE, "testParserFindsTheNameAndTheReason",
     r'''FAILED_CASE = re.compile(r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' failed")''',
     r'''FAILED_CASE = re.compile(r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' passed")'''),

    ("M354", "复刻本轮真踩过的正则 bug：`Executed … with N failures` 少了 `with ` ⇒ 恒读成 0",
     "py", GATE, "testSummaryFailureLineIsParsedInBothShapes",
     r'''SUMMARY_FAILURES = re.compile(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?\b")''',
     r'''SUMMARY_FAILURES = re.compile(r"Executed \d+ tests?, (?:\d+ tests? skipped and )?(\d+) failures?\b")'''),

    ("M355", "登记过的红仍然挡发布（反向：判据过严也是缺陷）",
     "py", GATE, "testRegisteredRedIsVisibleButNotBlocking",
     "    registered = [name for name in named if name in registry]",
     "    registered = []"),

    ("M356", "证人能分辨时把'产品跳变'判成 skip ⇒ 这就是那张新免检牌",
     "swift", SWIFT, "testTheControlJudgmentIsATruthTable",
     "        case .resolves: return .productSnapped",
     "        case .resolves: return .notRun"),

    ("M357", "地板从 `>` 改成 `>=` ⇒ '刚好等于地板'的读数从红变成绿",
     "swift", SWIFT, "testTheControlJudgmentIsATruthTable",
     "        if residual > controlResidualFloor { return .green }",
     "        if residual >= controlResidualFloor { return .green }"),

    ("M358", "把 -1（那一帧没读到像素）当成真电平 ⇒ '一半帧抓取失败'冒充'夹具动得很厉害'",
     "swift", SWIFT, "testTheFadeClockClassifierIsATruthTable",
     "        let readable = levels.filter { $0 >= 0 }",
     "        let readable = levels"),

    ("M359", "分类器永远说'能分辨' ⇒ 跳变与斜坡分不开，阳性对照的红就没人信",
     "swift", SWIFT, "testTheFadeClockClassifierIsATruthTable",
     "            return intermediate >= Self.minimumIntermediateFrames ? .resolves : .snaps",
     "            return .resolves"),

    ("M360", "分类器永远不说'探针坏了' ⇒ 证人是个摆设时没人发现",
     "swift", SWIFT, "testTheFadeClockClassifierIsATruthTable",
     "            if frames < 4 || span < Self.deadSpan { return .probeDead }",
     "            if frames < -1 || span < -1 { return .probeDead }"),

    ("M361", "端点也算中间态 ⇒ 一步跳变被读成'这台机器看得见过程'，于是那条红变成永远的红",
     "swift", SWIFT, "testTheFadeClockClassifierIsATruthTable",
     "        let low = lo + span * FadeClockReading.endpointMargin\n"
     "        let high = hi - span * FadeClockReading.endpointMargin",
     "        let low = lo\n"
     "        let high = hi"),

    # M362 动的是**产品**，不是判据：这一刀才是 BACKLOG 100 那句话的正面证据 ——
    # "把淡入的驱动撤掉"必须让阳性对照在本机判红，而且必须红在 `.productSnapped` 那一句上，
    # 而不是被新加的 `fade-clock-snaps-here` 顺手登记掉（那才是免检牌）。
    ("M362", "撤掉提示条淡入的驱动（`.animation(MotionCatalog.animation(for: .bannerIn), …)` → `nil`）"
             "⇒ 产品真的跳变了：本机必须红在『这台机器看得见 150ms 的淡入…』那一句",
     "swift", CONTENT, "testListRowsDoNotAnimateAndNothingClaimsTheyDo",
     "        .animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)",
     "        .animation(nil, value: noticeSignature)"),
]

BASELINE = [
    ("py", "testRealRunnerRedIsRedAndNamed"),
    ("py", "testArmLevelRulesAloneWouldHavePassedIt"),
    ("py", "testSummaryFailureLineIsParsedInBothShapes"),
    # 这一格在**另一个类**里（它盯的是臂一级的地板）：R66 之后那份本机真日志会多红一格
    # NAMELESS，原因写在夹具与那一格的注释里。基线里带着它，是为了让"两层判据互不污染"
    # 这件事在变异电池跑之前就先绿一次。
    ("py", "scripts.tests.test_motion_floor_gate.MotionFloorGateTests."
            "testRealLocalLogIsRedUnderTheTightenedRegistry"),
    ("swift", "testTheControlJudgmentIsATruthTable"),
    ("swift", "testTheFadeClockClassifierIsATruthTable"),
    # M362 的靶子：开窗口的阳性对照。基线里带着它，才允许把"M362 之后它红了"当成证据。
    ("swift", "testListRowsDoNotAnimateAndNothingClaimsTheyDo"),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run_py(target):
    proc = subprocess.run([sys.executable, "-m", "unittest", target],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr, proc.returncode


def run_swift(target):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    # M362 那一格是开窗口的：不开 `CLIPBOARD_HISTORY_UI_MOTION` 它会被 skip 掉，
    # 而 skip 在这份电池里一律记 NOT-RUN —— 不许把"没跑"读成"抓到了"。
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = MOTION_OUT
    os.makedirs(MOTION_OUT, exist_ok=True)
    # 每一遍之前删掉上一遍的读数文件（R65 的 M341 就是被留着的那份撑成 ESCAPED 的）。
    stale = os.path.join(MOTION_OUT, "motion-readings.log")
    if os.path.exists(stale):
        os.unlink(stale)
    proc = subprocess.run(["swift", "test", "--filter", "MotionFilmstripTests/" + target],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=2400)
    return proc.stdout + proc.stderr, proc.returncode


def verdict_for(kind, target, text, code):
    """'红'必须是**这一格**红，而不是编译失败、跑挂了、或别的格子红。"""
    short = target.split(".")[-1]
    if kind == "py":
        if "Ran 0 tests" in text:
            return "not-run"
        if "FAILED (" in text:
            return "red" if ("FAIL: %s " % short in text) else "other-red"
        return "green" if "\nOK" in text or text.startswith("OK") or "OK" in text else "not-run"
    failed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(target), text)
    passed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(target), text)
    if failed:
        return "red"
    if passed:
        return "green"
    if "error:" in text and "Compiling" in text:
        return "not-run"      # 编译不过 ⇒ 这一刀没测到任何东西
    return "not-run"


def run_case(kind, target):
    """跑一格，返回 ('green'|'red'|'not-run'|'other-red', 全文)。"""
    if kind == "py":
        full = target if target.startswith("scripts.") else PY_CLASS + target
        text, code = run_py(full)
        return verdict_for(kind, full, text, code), text
    text, code = run_swift(target)
    return verdict_for(kind, target, text, code), text


def failing_cells(text, target):
    short = target.split(".")[-1]
    return [line[:170] for line in text.splitlines()
            if ("error: -[" in line and short in line) or ("XCTAssert" in line and short in line)]


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑，不共享同一份源码" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        touched = sorted({path for _, _, _, path, _, _, _ in MUTATIONS})
        originals = {path: read(path) for path in touched}

        print("=== 基线（未变异）：这些格子必须先全绿 ===")
        baseline_ok = True
        for kind, target in BASELINE:
            verdict, text = run_case(kind, target)
            print("   %-58s = %s" % (target.split(".")[-1][:58], verdict))
            if verdict != "green":
                baseline_ok = False
                if kind == "py":
                    print("     " + "\n     ".join(text.splitlines()[-14:]))
                else:
                    for cell in failing_cells(text, target)[:3]:
                        print("     " + cell)
        if not baseline_ok:
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不算证据，整批作废")
            return 1

        for tag, note, kind, path, target, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            source = read(path)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文在 %s 里找不到 ⇒ 这条没跑" % os.path.basename(path))
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地 ⇒ 结论作废")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            print("   落地确认（%s）" % os.path.basename(path))
            try:
                verdict, text = run_case(kind, target)
                mark = {"red": "CAUGHT", "green": "ESCAPED",
                        "not-run": "NOT-RUN", "other-red": "RED-ELSEWHERE"}[verdict]
                print("   %s verdict=%s 期望红在=%s" % (mark, verdict, target.split(".")[-1]))
                cells = failing_cells(text, target)
                print("     红在这一格：" + (cells[0] if cells else
                                            "（没有断言行：看下面这段尾巴）"))
                if not cells:
                    print("     " + "\n     ".join(text.strip().splitlines()[-6:]))
                results.append((tag, mark))
            finally:
                write(path, originals[path])
                back = read(path)
                print("   已还原（与原始逐字节相同：%s）" % (back == originals[path]))

        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 红在别处=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0), counts.get("NOT-RUN", 0),
                 counts.get("RED-ELSEWHERE", 0), counts.get("NOT-APPLIED", 0)))
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
