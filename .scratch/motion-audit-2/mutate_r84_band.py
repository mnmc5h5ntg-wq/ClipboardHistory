#!/usr/bin/env python3
"""R84 的变异对照：位置那把尺（`bandFramePeaks` / `bandReading` / `bandAdjudication`）与产品那一处画法。

背景：
  * R83 手量到骨架的亮带是"三条各扫各的"（同一帧内绝对中心差 170pt、归一化只差 0.003），
    R84 把渐变抬到容器层（`SkeletonBarsShape`），并把手量换成会红的判据。
  * 本轮实测：判据读产品 可用帧=9-10、绝对散布 **0.0pt**、归一化 0.448、行程 121-133pt；
    同一把尺读粗节拍证人 可用帧=16、0.0pt；`.scratch/motion-audit-2/r84_band_fanout.py`
    在 before/after 两卷上分别读 169pt/0.005 与 0pt/0.450（两份实现同结论）。

八刀，每刀都指着一条"这句话没有牙"的怀疑：
  M451 产品改回 R83 的画法（每根条一个形状、渐变落在条的单位空间里）
       ⇒ 位置判据必须红。**本轮的主刀**：它证明那条新判据抓的是真缺陷，不是一台机器的读数形状。
  M452 条端内边距 10pt → 0pt ⇒ 被条端切掉的假峰重新进散布（本轮实测那个 19.5pt）⇒ 位置判据该红。
  M453 行程地板 20pt → 0pt ⇒ 正对照失效：静止画面也能读成"整组一条带" ⇒ 真值表第④格该红。
  M454 幅度地板 4 灰阶 → 0 ⇒ **本地无独立判别力**（第一版期望 [BAND]，实测全绿）：
       无噪声的渲染里"亮带不在这根条里"会退化成贴边的峰，而那一格已被 M452 拦住 ⇒ 两格前提是冗余的。
       这一条按实存活，不许改期望冒充有牙。
  M454b 幅度地板与条端内边距**一起**拆 ⇒ 检验"两格里至少一格必须有牙"这句话本身可不可证伪。
  M455 证人"有资格签"改成恒真 ⇒ 没人看见亮带时也敢判产品红 ⇒ 真值表第⑫⑬格该红。
  M456 一条带的天花板 6pt → 50pt ⇒ 两个地板互相取消 ⇒ 真值表第⑥⑦格该红。
  M457 位置判据忽略循环那一族的处置 ⇒ "只能收窄、不能放大指控"那条（真值表⑭⑮格）该红。

用法：`python3 .scratch/motion-audit-2/mutate_r84_band.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
SHIMMER = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift"
LOCK = "/tmp/r84_mutation.lock"

BAND = "testSkeletonSweepIsOneBand"
TABLE = "testTheBandPositionRulerTruthTable"
SHIM = "testSkeletonSweepActuallySweeps"
CASES = [BAND, TABLE, SHIM]
FILTER = "|".join("MotionFilmstripTests/" + c for c in CASES)

EXPECTED = {
    "M451": [BAND],
    "M452": [BAND],
    "M453": [TABLE],
    "M454": [],          # 本地无独立判别力（被 M452 那一格吸收）—— 见文件头
    "M454b": [BAND],     # 两格一起拆必须有牙；这一刀是对 M454 那句解释的检验
    "M455": [TABLE],
    "M456": [TABLE],
    "M457": [TABLE],
}
NO_POWER_NOTE = {
    "M454": "幅度地板被条端内边距那一格吸收 ⇒ 由 M454b（两格同拆）证明这句话本身可证伪",
}

FLOOR = '    static let bandAmplitudeFloor: Double = 4'
MARGIN = '    static let bandInteriorMarginPoints: Double = 10'

# 产品那一刀：把 `bars` 换回 R83 的画法（每根条一个形状，渐变按条宽归一化）。
PRODUCT_NEW = """    private var bars: some View {
        SkeletonBarsShape()
            .fill(bandGradient)
    }"""
PRODUCT_OLD = """    private var bars: some View {
        GeometryReader { proxy in
            VStack(alignment: .leading, spacing: SkeletonMotion.barSpacing) {
                ForEach(Array(SkeletonMotion.barFractions.enumerated()), id: \\.offset) { _, fraction in
                    VisualShape.rounded(VisualRadius.chip)
                        .fill(bandGradient)
                        .frame(width: max(1, proxy.size.width * fraction),
                               height: SkeletonMotion.barHeight)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }"""

# 每条：(tag, note, [(path, needle, replacement), ...])
MUTATIONS = [
    ("M451", "产品改回『每根条一个形状、渐变按条宽归一化』（= BACKLOG 117 那个缺陷本身）",
     [(SHIMMER, PRODUCT_NEW, PRODUCT_OLD)]),
    ("M452", "条端内边距 10pt → 0pt ⇒ 贴在条端的假峰重新进散布",
     [(MFT, MARGIN, '    static let bandInteriorMarginPoints: Double = 0  // R84 变异：拦不住贴边假峰')]),
    ("M453", "行程地板 20pt → 0pt ⇒ 正对照失效（静止画面也读成一条带）",
     [(MFT, '    static let sweepTravelFloorPoints: Double = 20',
       '    static let sweepTravelFloorPoints: Double = 0  // R84 变异：正对照不再要求走过距离')]),
    ("M454", "幅度地板 4 灰阶 → 0（单拆这一格）",
     [(MFT, FLOOR, '    static let bandAmplitudeFloor: Double = 0  // R84 变异：单拆幅度地板')]),
    ("M454b", "幅度地板与条端内边距**一起**拆 ⇒ 检验『两格里至少一格必须有牙』这句话",
     [(MFT, FLOOR, '    static let bandAmplitudeFloor: Double = 0  // R84 变异：两格一起拆'),
      (MFT, MARGIN, '    static let bandInteriorMarginPoints: Double = 0  // R84 变异：两格一起拆')]),
    ("M455", "证人『有资格签』改成恒真 ⇒ 没人看见亮带时也敢判产品红",
     [(MFT, '        verdict == .oneBand || verdict == .fanOut', '        return true  // R84 变异：空支票')]),
    ("M456", "一条带的天花板 6pt → 50pt ⇒ 两个地板互相取消",
     [(MFT, '    static let oneBandCeilingPoints: Double = 6',
       '    static let oneBandCeilingPoints: Double = 50  // R84 变异：天花板高过下限')]),
    ("M457", "位置判据忽略循环那一族的处置（`loopCapable` 不再收窄断言）⇒ 一个会翻脸的读数可以定罪产品",
     [(MFT, '        guard loopCapable else { return .notRunEnvironment }',
       '        // R84 变异：循环判不动也照判（BACKLOG 119 禁止的那种放大指控）')]),
]


def read(path):
    return open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_swift_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r84_mutation_motion"
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=2400)
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


def apply(edits, originals):
    """落地一组编辑。任何一处锚点不唯一 / 回读还在 ⇒ 整组回滚（半把刀不算刀）。"""
    for path, needle, replacement in edits:
        # 每次都从**磁盘当前内容**读：一格里有多处编辑时，第二处必须看见第一处已经落地，
        # 否则第二处是在原始文本上做的替换，写回去会把第一处覆盖掉（M454b 就是两处同文件）。
        text = read(path)
        if text.count(needle) != 1:
            print("   NOT-APPLIED %s 锚点出现 %d 次（要 1 次）" % (path, text.count(needle)))
            return False
        originals.setdefault(path, text)
        write(path, text.replace(needle, replacement, 1))
    for path, needle, _ in edits:
        if needle in read(path):
            print("   NOT-APPLIED %s 回读证明锚点还在" % path)
            return False
    return True


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在" % LOCK)
        return 2
    open(LOCK, "w").write(str(os.getpid()))
    results = []
    paths = sorted(set(p for _t, _n, edits in MUTATIONS for p, _a, _b in edits))
    try:
        originals = {p: read(p) for p in paths}
        pristine = dict(originals)
        print("=== 基线（未变异）：三条都必须绿 ===")
        marks = swift_verdicts(run_swift_once())
        print("   swift=%s" % marks)
        if any(v != "green" for v in marks.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 整批作废")
            return 1
        for tag, note, edits in MUTATIONS:
            print("\n%s %s" % (tag, note))
            working = {}
            if not apply(edits, working):
                for path, text in pristine.items():
                    write(path, text)
                results.append((tag, "NOT-APPLIED")); continue
            try:
                out = run_swift_once()
                marks = swift_verdicts(out)
                reds = [c for c in CASES if marks[c] in ("red", "crashed")]
                want = EXPECTED[tag]
                if "error:" in out and not reds:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in out.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif reds == want and want:
                    print("   CAUGHT 只红在预期那几条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif reds == want:
                    print("   LOCAL-NO-POWER 本地全绿（%s）" % NO_POWER_NOTE.get(tag, ""))
                    results.append((tag, "LOCAL-NO-POWER"))
                else:
                    print("   ESCAPED 红的不是预期那几条：%s 预期=%s" % (marks, want))
                    results.append((tag, "ESCAPED"))
                for line in [l[:220] for l in out.splitlines() if "error: -[" in l][:3]:
                    print("     " + line)
            finally:
                for path, text in pristine.items():
                    write(path, text)
                print("   已还原（逐字节相同：%s）"
                      % all(read(p) == pristine[p] for p in paths))
        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 本地无独立判别力(按实存活)=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("LOCAL-NO-POWER", 0),
                 counts.get("ESCAPED", 0), counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        bad = sum(counts.get(k, 0) for k in ("ESCAPED", "NOT-RUN", "NOT-APPLIED"))
        return 0 if bad == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
