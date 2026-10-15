#!/usr/bin/env python3
"""R82 的变异对照：循环那条判据（coverage + 两颗证人）与分辨率那条闸门（P75）是不是真的在承重。

背景（读 R80 / R81 的 CI 读出来的，BACKLOG 113 / 110）：
  * `testSkeletonSweepActuallySweeps` 原来数的是"几对帧在变"。R80 的 CI 上 runner 读到
    `变化帧对=2 / 帧数=23 / 采样≈115ms`、本机 `23 / 48 / 53ms`，而**两边峰值都是 0.015**
    ⇒ 那一列量的是这台机器多久拍一张，不是这条循环有没有在跑。
  * `judgeMotion` 的 `.clockTooCoarse` 原来吃"事件内最粗那一次采样"。本机三遍里
    `detail-kind-change` 的最粗在 61ms 与 81ms 之间跳，而线是 0.5×160=80ms
    ⇒ 同一份代码、同一台机器，一臂红一臂 not-run，而中位数一直是 50–51ms。
  * R81 的 CI 又把**单颗证人**打回了：runner 上产品 2 对在变，那颗证人（20Hz、抬 0.39）
    13 对在变。两颗差的正是节拍与对比度 ⇒ 加一颗**等节拍**证人（30Hz、抬 0.12），
    它决定"产品红 / 环境不行"那一分界；粗节拍那颗只留作"签字的人来没来上班"的守卫。

八刀（前六刀是形状尺与闸门，后两刀钉本轮现场发现的两个坑）：
  M437 coverage 地板 0.5 ⇒ 0.02（"只动了一下"不再被拦）      ⇒ LOOP 真值表该红
  M438 coverage 的分母从"整卷"换成"变化段自己"（恒 1.0）      ⇒ LOOP 真值表该红
  M439 粗节拍证人整卷没拍到东西时改走"环境看不见"那支（空支票）  ⇒ LOOP 真值表该红
  M440 `LoopShape.minPeak` 挪离全卷那条地板（漂移）        ⇒ LOOP + SHIM 都该红（实测：粗节拍证人也翻成 notMoving）
  M443 结构等式 `stamps.count == 帧对+1` 改成 `== 帧对`     ⇒ LOOP + SHIM 都该红（所有真卷都算"没量到"）
  M441 分辨率闸门改回"最粗那一次"（=q 1.0）                    ⇒ P75 那格该红
  M442 `loopAdjudication` 产品没动也返回 .ok（恒过）            ⇒ LOOP 真值表该红
  M443 把产品那卷的形状改回吃 `probe.lastStamps`（=后一卷的时刻） ⇒ SHIM 的"时刻同一卷"钉子该红
  M444 guard 分支把峰值原样报出去（不返回 0）                  ⇒ LOOP 第⑥格该红
  M445 等节拍证人的节拍偷偷改回 0.05（与产品分家）              ⇒ MIRROR 该红

用法：`python3 .scratch/motion-audit-2/mutate_r82_loop_shape.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
LOCK = "/tmp/r82_mutation.lock"

LOOP = "testTheLoopShapeClassifierIsATruthTable"
P75 = "testTheClockGateUsesARobustStatisticNotTheSingleWorstSample"
SHIM = "testSkeletonSweepActuallySweeps"
MIRROR = "testTheLoopWitnessStillMirrorsTheProductLoop"
CASES = [LOOP, P75, SHIM, MIRROR]
FILTER = "|".join("MotionFilmstripTests/" + c for c in CASES)
EXPECTED = {
    "M437": [LOOP],
    "M438": [LOOP],
    "M439": [LOOP],
    "M440": [LOOP, SHIM],
    "M441": [P75],
    "M442": [LOOP],
    "M443": [LOOP, SHIM],
    "M444": [LOOP],
    "M445": [MIRROR],
}

MUTATIONS = [
    ("M437", "coverage 地板从 0.5 降到 0.02 ⇒ 一次跳变也算『一直在动』（这条判据从此恒绿）",
     MFT,
     '        static let minCoverage = 0.5',
     '        static let minCoverage = 0.02  // R82 变异：地板抬到地板下了'),
    ("M438", "coverage 的分母从『整卷时长』换成『变化段时长』⇒ 它恒等于 1.0，"
             "而『一直在动』与『只动了一下』的分别正在分母上",
     MFT,
     '        let covered = total > 0 ? max(0, (stamps[last + 1] - stamps[first]) * 1000) / total : 0',
     '        let covered = 1.0  // R82 变异：分母没了'),
    ("M439", "粗节拍证人整卷没拍到任何变化时改走『环境看不见』那一支 ⇒ 那是一张空支票"
             "（谁都可以说看不见，因为签字的人自己没上班）",
     MFT,
     '        if coarseWitness == .notMoving { return .witnessDead }',
     '        if coarseWitness == .notMoving { return .notRunEnvironment }  // R82 变异：空支票'),
    ("M440", "把结构体里那条峰值地板挪离全卷那条（两个数分家）⇒ 漂移钉子必须红",
     MFT,
     '        static let minPeak: Double = 0.005',
     '        static let minPeak: Double = 0.05  // R82 变异：与全卷那条分家'),
    ("M441", "分辨率闸门改回『最粗那一次』（把分位数取成 1.0）⇒ P75 那一格必须红"
             "（这一刀钉的是 BACKLOG 110 的修法在承重，不是新写的装饰）",
     MFT,
     '        let index = min(sorted.count - 1, max(0, Int((q * Double(sorted.count - 1)).rounded())))',
     '        let index = sorted.count - 1  // R82 变异：永远取最粗那一次'),
    ("M442", "产品没在动也返回 .ok ⇒ 真值表里那四格必须红（恒过的判据）",
     MFT,
     '        if product == .looping { return .ok }',
     '        _ = product; return .ok  // R82 变异：恒过'),
    # 第一版这一刀是"把形状改回吃 probe.lastStamps"，结果**四条判据全绿**（见
    # r82_mutation_battery_v1.log 与 U-155）：两卷等长时任何断言都分不开，所以修法换了层
    # —— 探针改成返回 `GrabbedFilm(frames:stamps:)`，那句话今天在类型上拼不出来。
    # 这一刀因此改钉**结构等式**本身。
    ("M443", "把 `stamps.count == 帧对 + 1` 这条结构等式挪成 `== 帧对` ⇒ 今天每一卷真胶片"
             "都会被判成『没量到』：真值表第①格与扫光那一条都必须红",
     MFT,
     '        guard maximum > 0, fractions.count > 1, stamps.count == fractions.count + 1 else {',
     '        guard maximum > 0, fractions.count > 1, stamps.count == fractions.count else {  // R82 变异：等式挪一格'),
    ("M444", "guard 分支把峰值原样报出去（不返回 0）⇒ 前提故障会被冒充成『只动了一下』"
             "，真值表第⑥格必须红",
     MFT,
     '            return LoopShape(pairs: max(0, fractions.count), changingPairs: 0, peak: 0,',
     '            return LoopShape(pairs: max(0, fractions.count), changingPairs: 0, peak: maximum,'),
    ("M445", "等节拍证人的节拍偷偷改回 0.05（与产品的 1/30 分家）⇒ MIRROR 那条钉子必须红",
     MFT,
     '        GradientTickView(tickSeconds: 1.0 / 30.0,',
     '        GradientTickView(tickSeconds: 0.05,  // R82 变异：与产品分家'),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r82_mutation_motion"
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=2400)
    return proc.stdout + proc.stderr


# 分类器的第四、第五种形状（M443 现场教的，见 U-158）：用例跑到一半**整个进程死掉**时，
# 它既没有 `failed` 行也没有 `passed` 行 —— 旧分类器把它归成 `absent`（="这条没跑"），
# 于是"这一刀把判据崩掉了"被报成"这一刀没落地"。
# 但"给崩溃让路"不能一把抓：`swift test` 不打 "started" 行，所以能用来归因的证据只有
# **这条用例自己说过话**（日志里有它的 `error: -[…方法]`）。
# 说过话又没结论 = 被这一刀崩掉（算红）；从头到尾没提过 = **没轮到**（不算红，
# 否则一条崩掉的用例会把排在它后面的每一条都签字成红 —— 那是 U-151 的镜像方向）。
CRASH_MARKERS = ("Fatal error", "Precondition failure", "index out of range",
                 "Exited with unexpected signal", "signal code ")


def verdicts_of(text):
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
            # 这一条用例**开口说过话**（有 `error: -[…方法]` 行）却没有结论行，
            # 再加上整份日志里有崩溃痕迹 ⇒ 它是**被这一刀崩掉的**，算红。
            out[case] = "crashed" if crashed else "errored"
        else:
            # 既没结论、也没说过话：它只是**没轮到**（前面的用例把进程带走了）。
            # 不许把它算成红 —— 那是拿"进程死了"给一条没跑过的用例签字。
            out[case] = "absent"
    return out


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在" % LOCK)
        return 2
    open(LOCK, "w").write(str(os.getpid()))
    only = set(sys.argv[1:])
    results = []
    try:
        original = read(MFT)
        print("=== 基线（未变异）：四条都必须绿（扫光那一条在本机是绿）===")
        marks = verdicts_of(run_once())
        print("   " + str(marks))
        if any(v != "green" for v in marks.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 整批作废")
            return 1
        for tag, note, path, needle, replacement in MUTATIONS:
            if only and tag not in only:
                continue
            print("\n%s %s" % (tag, note))
            if needle in replacement:
                print("   NOT-APPLIED 变异文包含原文")
                results.append((tag, "NOT-APPLIED")); continue
            text = read(path)
            if needle not in text:
                print("   NOT-APPLIED 锚点没找到")
                results.append((tag, "NOT-APPLIED")); continue
            write(path, text.replace(needle, replacement, 1))
            if needle in read(path):
                print("   NOT-APPLIED 回读证明没落地")
                write(path, original); results.append((tag, "NOT-APPLIED")); continue
            try:
                out = run_once()
                marks = verdicts_of(out)
                reds = [c for c in CASES if marks[c] in ("red", "crashed")]
                crashed = any(marks[c] == "crashed" for c in CASES)
                compile_error = "error: " in out and not reds and not crashed
                if compile_error:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in out.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif crashed and not reds:
                    print("   CAUGHT(崩溃) 变异直接把进程打崩：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif reds == EXPECTED[tag]:
                    print("   CAUGHT 只红在预期那几条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif reds:
                    print("   ESCAPED 红的不是预期那几条：%s 预期=%s" % (marks, EXPECTED[tag]))
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                for line in [l[:230] for l in out.splitlines() if "error: -[" in l][:3]:
                    print("     " + line)
            finally:
                write(path, original)
                print("   已还原（逐字节相同：%s）" % (read(path) == original))
        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0),
                 counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-RUN", 0) == 0 \
            and counts.get("NOT-APPLIED", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
