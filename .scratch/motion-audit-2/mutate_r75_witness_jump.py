#!/usr/bin/env python3
"""R75 的变异对照：把证人接到 `.jump` 那一支之后，四样东西各有没有牙（BACKLOG 104 的答案 / U-129 / D-133）。

被判的四样：
  ① `jumpAdjudication`（纯函数）—— 证人能不能赦免一条"产品跳变"的红；
  ② `testTheJumpAdjudicationIsATruthTable` —— 上面那张表的八格断言；
  ③ `testBandCaptureIsWiredIntoBothBannerArms` 里 R75 新加的那半条 —— **放宽必须带理由与 run 号**；
  ④ `scripts/tests/test_motion_floor_gate.py::testRegistryIsStrictAgain` —— 地板=3、别的臂没被连带放宽。

两刀专门钉"放宽不是免检"：M395 把放行理由从登记表里删掉、M396 把 note 里的 run 号删掉。
这两刀在 R75 之前**根本没有对应判据**（旧的那半条只说"两臂都必须 must_judge=true"），
所以它们钉的是本轮新加的那一格，不是旧账。

一刀按实记成"本地无判别力"（**不收进计数**，沿用 M168/M385 的先例）：
  把真判据里 `.jump` 那一支的证人问话删掉、退回无条件 `XCTFail`。
  本机证人 `判定=能分辨` ⇒ 这条路径今天在本机根本走不到，红不出来；
  它只能由 runner 那一遍回答（下一轮 CI 读 `MOTION_NOT_RUN=witness-snaps-here notice-banner` 在不在）。

三条电池规矩沿用 R64/R66/R67/R68/R71/R74：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场、变异文不含原文）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。

用法：`python3 .scratch/motion-audit-2/mutate_r75_witness_jump.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MOTION = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
REGISTRY = "scripts/motion_floor_expectations.json"
LOCK = "/tmp/r75_mutation.lock"

TRUTH = "testTheJumpAdjudicationIsATruthTable"
BAND = "testBandCaptureIsWiredIntoBothBannerArms"
PY_STRICT = "test_motion_floor_gate.MotionFloorGateTests.testRegistryIsStrictAgain"
SWIFT_BOTH = "MotionFilmstripTests/testTheJumpAdjudicationIsATruthTable|MotionFilmstripTests/testBandCaptureIsWiredIntoBothBannerArms"

# 每一刀期望红在哪些名字上（swift 名或 `py:` 前缀的 unittest 名）
MUTATIONS = [
    ("M392", "让 `jumpAdjudication` **永远放行**（不管证人说什么都给 notRunChannel）"
             "⇒ 真值表必须红：一条只会赦免的表等于把红换成 skip（BACKLOG 49 的免检牌）",
     MOTION, SWIFT_BOTH, [TRUTH],
     '        case .resolves: return .productRed\n'
     '        case .probeDead: return .witnessDead\n'
     '        case .snaps: return witnessQualifies ? .notRunChannel : .witnessUnqualified',
     '        case .resolves: return .notRunChannel\n'
     '        case .probeDead: return .notRunChannel\n'
     '        case .snaps: return .notRunChannel'),

    ("M393", "让 `jumpAdjudication` **永远不放行**（证人说什么都是产品红）"
             "⇒ 真值表必须红：这一格钉的是『赦免恰好有一个形状』，"
             "反过来说明本轮不是为了让 runner 绿才加的证人",
     MOTION, SWIFT_BOTH, [TRUTH],
     '        case .snaps: return witnessQualifies ? .notRunChannel : .witnessUnqualified',
     '        case .snaps: return .productRed'),

    ("M395", "把登记表里那条放行理由删掉（`witness-snaps-here` 从 allowed_not_run_reasons 消失）"
             "⇒ 两半都必须红：Swift 那半条『放宽必须登记理由』、python 那半条『地板=3 且理由在案』",
     REGISTRY, SWIFT_BOTH, [BAND, "py:" + PY_STRICT],
     '        "premise-not-visible",\n        "witness-snaps-here"\n',
     '        "premise-not-visible"\n'),

    ("M396", "把 note 里的两个 run 号抹掉（放宽还在，证据没了）"
             "⇒ Swift 那半条必须红：没有 run 号的放宽就是随口一说",
     REGISTRY, SWIFT_BOTH, [BAND],
     'run 38726667469（R72）与 38726991211（R73）',
     'run 号见 AGENT_STATE 的 R75 那一节'),

    ("M397", "把 notice-banner 的 must_judge 改回 true（清单变严，读数没变）"
             "⇒ python 那格必须红：地板不再是 3 ⇒ 有人动清单却没回来改期望",
     REGISTRY, SWIFT_BOTH, ["py:" + PY_STRICT],
     '    "notice-banner": {\n      "must_judge": false,',
     '    "notice-banner": {\n      "must_judge": true,'),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run_swift(filter_expression):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r75_mutation_shots"
    proc = subprocess.run(["swift", "test", "--filter", filter_expression],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr


def run_python(test_name):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-s", "scripts/tests", "-p", test_name.split(".")[0] + ".py"],
                          cwd=os.path.join(REPO, "ClipboardHistory", ".."), env=env,
                          capture_output=True, text=True, timeout=1200)
    text = proc.stdout + proc.stderr
    short = test_name.split(".")[-1]
    if ("FAIL: %s " % short) in text or ("ERROR: %s " % short) in text:
        return text, "red"
    if "OK" in text:
        return text, "green"
    return text, "absent"


def verdicts_of(text, cases):
    out = {}
    for case in cases:
        if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text):
            out[case] = "red"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text):
            out[case] = "green"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' skipped" % re.escape(case), text):
            out[case] = "skipped"
        else:
            out[case] = "absent"
    return out


def failure_messages(text, cases):
    hits = []
    for line in text.splitlines():
        if "error: -[" in line and any(case in line for case in cases):
            hits.append(line[:240])
    return hits


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    all_names = sorted({n for _, _, _, _, names, _, _ in MUTATIONS for n in names})
    swift_names = [n for n in all_names if not n.startswith("py:")]
    try:
        originals = {path: read(path) for _, _, path, _, _, _, _ in MUTATIONS}
        print("=== 基线（未变异）：Swift 两格与 python 那一格都必须绿 ===")
        text = run_swift(SWIFT_BOTH)
        base = verdicts_of(text, swift_names)
        for case, mark in base.items():
            print("   %-58s = %s" % (case[:58], mark))
        _, py_mark = run_python(PY_STRICT)
        print("   %-58s = %s" % ("testRegistryIsStrictAgain", py_mark))
        if any(mark != "green" for mark in base.values()) or py_mark != "green":
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, swift_names)[:6]:
                print("     " + line)
            return 1

        for tag, note, path, case_filter, expected, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            if needle in replacement:
                print("   DRIFT-NOT-APPLIED 变异文包含原文 ⇒ 回读必然判『没落地』，先改刀")
                results.append((tag, "NOT-APPLIED"))
                continue
            source = read(path)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文找不到 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            print("   落地确认（%s）" % os.path.basename(path))
            try:
                marks = {}
                text = ""
                if any(not n.startswith("py:") for n in expected):
                    text = run_swift(case_filter)
                    marks.update(verdicts_of(text, swift_names))
                if any(n.startswith("py:") for n in expected):
                    _, py_mark = run_python(PY_STRICT)
                    marks["py:" + PY_STRICT] = py_mark
                want = [n if n.startswith("py:") else n for n in expected]
                reds = [c for c, m in marks.items() if m == "red"]
                extra = [c for c in reds if c not in want]
                missed = [c for c in want if c not in reds]
                compile_failed = "error:" in text and not reds
                if reds and not extra and not missed:
                    print("   CAUGHT 红在的正好是期望那 %d 条：%s" % (len(reds), marks))
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif missed:
                    print("   ESCAPED 期望红的那条没红：%s" % marks)
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 连带红了不该动的判据 %s：%s" % (extra, marks))
                    results.append((tag, "ESCAPED"))
                for line in failure_messages(text, swift_names)[:3]:
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
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
