#!/usr/bin/env python3
"""R68 的变异对照：证人那根"合不合格"的轴有没有牙（BACKLOG 104）。

被判的三条判据（都在 `MotionFilmstripTests`，都不开窗、CI 每轮都跑）：
  testTheControlJudgmentIsATruthTable               决定表八格（含新加的 witnessQualifies 那一轴）
  testTheFadeClockWitnessQualificationIsATruthTable 合格线自己的六格（含两条边界）
  testTheFadeClockClassifierIsATruthTable           证人分类器（本轮没动，当回归对照）

三条"电池自己会骗人"的规矩沿用 R64/R66/R67：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数，needle 只能从**实际失败消息原文**里抄。

**本轮特意不收进电池的一刀**：把证人抓帧区域从 190×24 换回整张 320×180。
本机量不到它（证人采样由 0.02s 的 runloop 节奏决定，20ms 前后一样），
只有 runner 上才是"80ms ⇒ 可分数段=1 ⇒ 不合格"那个形状 ⇒
按 M168 的先例记成**本地无判别力、由 runner 判**，不混进 CAUGHT/ESCAPED 的计数里。

用法：`python3 .scratch/motion-audit-2/mutate_r68_witness_qualification.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
LOCK = "/tmp/r68_mutation.lock"

DECISION = "testTheControlJudgmentIsATruthTable"
QUALIFY = "testTheFadeClockWitnessQualificationIsATruthTable"
CLASSIFY = "testTheFadeClockClassifierIsATruthTable"
CASES = [DECISION, QUALIFY, CLASSIFY]
ALL = "MotionFilmstripTests/testThe.*TruthTable"

# (编号, 说明, 文件, 过滤, 原文, 变异后)
MUTATIONS = [
    ("M372", "退回 BACKLOG 104 的原始缺陷形状：`.snaps` 无条件 ⇒ `.notRun`"
             "（证人合不合格这一轴被删掉 ⇒ '我没看清'又能给'它没动'签字）",
     TESTS, ALL,
     "        case .snaps: return witnessQualifies ? .notRun : .witnessCannotAdjudicate",
     "        case .snaps: return .notRun"),

    ("M373", "把合格线放到'只要能切 1 段'（`>= minimumIntermediateFrames + 1` ⇒ `>= 1`）"
             "⇒ runner 那一档的 80ms 会变成'合格'，skip 重新变成免检牌",
     TESTS, ALL,
     "                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames + 1",
     "                sampleMilliseconds: samplingMilliseconds) >= 1"),

    ("M374", "把合格线挪低一格（`+ 1` 去掉）⇒ 51ms 那一格必须红（边界）",
     TESTS, ALL,
     "                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames + 1",
     "                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames"),

    ("M375", "把'能分辨'的证人判成环境（`.resolves ⇒ .notRun`）"
             "⇒ 这是 R66 的 M356 同一张免检牌换了个格子",
     TESTS, ALL,
     "        case .resolves: return .productSnapped",
     "        case .resolves: return .notRun"),

    ("M376", "把 `residual > floor` 改成 `>=`（悄悄改判据的边界）"
             "⇒ 恰好等于地板那一格必须从红变绿 ⇒ 决定表必须红",
     TESTS, ALL,
     "        if residual > controlResidualFloor { return .green }",
     "        if residual >= controlResidualFloor { return .green }"),

    ("M377", "让证人永远不合格（把合格线抬到 100 段）⇒ 必须红在**合格线那张真值表**"
             "（决定表吃的是已经算好的布尔值，它抓不到这一刀 —— 这正是两条表都要在的理由）。"
             "反向的一刀：只测'不合格要红'会漏掉'永远不合格'也是一种免检"
             "（它把 skip 换成红，看起来更严，其实把这台机器上唯一能得出的结论钉死了）。"
             "写法注意：变异文**不能包含原文**，否则电池的回读检查会判'没落地'（M377 第一版就踩了这个）",
     TESTS, ALL,
     "                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames + 1",
     "                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames + 99"),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run(filter_expression):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(["swift", "test", "--filter", filter_expression],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr, proc.returncode


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
            hits.append(line[:220])
    return hits


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        originals = {path: read(path) for _, _, path, _, _, _ in MUTATIONS}
        print("=== 基线（未变异）：三条真值表判据都必须绿 ===")
        text, _ = run(ALL)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-56s = %s" % (case[:56], mark))
        if any(mark != "green" for mark in base.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, CASES)[:6]:
                print("     " + line)
            return 1

        for tag, note, path, case_filter, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
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
                text, _ = run(case_filter)
                marks = verdicts_of(text, CASES)
                reds = [case for case, mark in marks.items() if mark == "red"]
                compile_failed = "error:" in text and not reds
                if reds:
                    print("   CAUGHT 红在：%s" % " ".join(r[:52] for r in reds))
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif any(mark == "skipped" for mark in marks.values()):
                    print("   NOT-RUN 被 skip 了：%s" % marks)
                    results.append((tag, "NOT-RUN"))
                else:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                for line in failure_messages(text, CASES)[:3]:
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
