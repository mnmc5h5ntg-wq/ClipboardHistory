#!/usr/bin/env python3
"""R80 的变异对照：那把 pt² 尺、那条处置函数、那两道地板，是不是真的在承重。

背景（读 R79 的 CI 读出来的，run 38760347161）：runner 上存在性闸门**开**
（`QUICKPICK_FOCUS_GATE 暗 … 占位整条宽=87.0pt … 闸门开`）而两态差读 0 个像素 ——
命中 BACKLOG 109 预登记的第二个分支（"独占区非 0 而两态差仍是 0 ⇒ 那四条红是真的，
不许再抬地板"）。R80 的答案不是抬地板，是**换尺**：从"数过地板的像素个数"换成
"搬动了多少 pt² 的墨 + 占那一格现有墨的比例"，并加三条证人臂（同态重拍 / 撤占位字 / 打进字），
把"看不见"分成『尺在这一格瞎了』与『这台机器不调淡』两支，各有一个名字。

这一批要打的就是那句"分成两支"：**一条 1× 才走得到的分支，本机永远不执行**，
所以它必须由合成数字钉着，否则"能不能把一条轴说成没跑"这道门就没有红看着。

十一刀：
  M423 归一化从 `÷缩放²` 改成 `÷缩放`        ⇒ INK  红（②⑨ 两格跟着缩放走）
  M424 并集里把 alpha 那一轴摘掉              ⇒ INK  红（② 少一半）
  M425 并集里把三条 RGB 轴摘掉（只读 alpha）  ⇒ INK  红（③ 颜色变化读成没动）
  M426 每像素噪声地板失效（什么都累加）       ⇒ INK  红（⑥ 地板下那一格抬起来）
  M427 α=0 的夹紧摘掉                        ⇒ INK  红（④ 全透的 RGB 被算成搬动）
  M428 焦点地板 40⇒200pt²                     ⇒ FOCUS+DISP 红（本机 98.7 过不了 200）
  M429 占比地板 0.08⇒0.5                      ⇒ FOCUS+DISP 红（本机 0.367/0.343 过不了）
  M430 处置函数无条件回 judged                ⇒ FOCUS+DISP 红（那两支没人钉）
  M431 证人地板 40⇒100000                     ⇒ DISP 红（1× 上会把『行为没有』说成『通道瞎』）
  M432 噪声系数 10⇒0                          ⇒ DISP 红（地板不再随这台机器的噪声抬）
  M433 把证人臂 D 换成"什么都没改"的那一帧     ⇒ FOCUS 红（臂自己作废时必须有人发现）

用法：`python3 .scratch/motion-audit-2/mutate_r80_ink_ruler.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
UCH = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
LOCK = "/tmp/r80_mutation.lock"

INK = "testMovedInkRulerIsGridNormalizedAndReadsBothAxes"
DISP = "testFocusAxisDispositionIsATruthTable"
FOCUS = "testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing"
CASES = [INK, DISP, FOCUS]
FILTER = "|".join(["UICaptureTests/" + c for c in CASES])
EXPECTED = {
    "M423": [INK],
    "M424": [INK],
    "M425": [INK],
    "M426": [INK],
    "M427": [INK],
    "M428": [DISP, FOCUS],
    "M429": [DISP, FOCUS],
    # M430 第一次跑报的是 ESCAPED，而**逃的不是判据，是我对它的期望**：
    # 门恒开之后，2× 那条判据自己仍然全过（本机 98.7pt² 本来就够），所以 FOCUS 是绿的 ——
    # 绿在这里是**正确答案**。只在 1× 走的出口，本机唯一能钉住它的就是 DISP 那几格合成数字。
    # 期望写成 [DISP, FOCUS] 等于以为"本机也能看出一扇门恒开"，那是错的（U-149）。
    "M430": [DISP],
    "M431": [DISP],
    "M432": [DISP],
    "M433": [FOCUS],
}

MUTATIONS = [
    ("M423", "归一化从 ÷缩放² 改成 ÷缩放 ⇒ 这个量又开始跟着像素网格走（R38 那一课的正照）",
     UCH,
     '        return sum / 255.0 / Double(scale * scale)\n    }\n\n    /// 一块矩形里**画着的墨**',
     '        return sum / 255.0 / Double(scale)  // R80 变异：少除一个缩放\n    }\n\n    /// 一块矩形里**画着的墨**'),
    ("M424", "并集里把 alpha 那一轴摘掉 ⇒ 只在透明度上动的墨读成没动（R77 那一族的形状）",
     UCH,
     '                if deltaAlpha > move { move = deltaAlpha }\n',
     '                if deltaAlpha > 1.0e9 { move = deltaAlpha }  // R80 变异：alpha 不参与判定\n'),
    ("M425", "并集里把三条 RGB 轴摘掉、只留 alpha ⇒ 只改颜色的效果读成没动（BACKLOG 108 那一族）",
     UCH,
     '                var move = deltaRed\n                if deltaGreen > move { move = deltaGreen }\n'
     '                if deltaBlue > move { move = deltaBlue }\n',
     '                var move = 0.0  // R80 变异：亮度那一半不参与\n'),
    ("M426", "每像素噪声地板失效（什么都累加）⇒ ⑥ 那一格（每像素只差 1）抬起来",
     UCH,
     '                if move > noiseFloor { sum += move }\n',
     '                if move > -1.0 { sum += move }  // R80 变异：地板拆掉\n'),
    ("M427", "α=0 的夹紧摘掉 ⇒ 全透的 RGB 被算成搬动过的墨（④ 那一格的对象）",
     UCH,
     '                let inkB2 = alphaB == 0 ? 0.0 : Double(pb[q + 2])\n',
     '                let inkB2 = Double(pb[q + 2])  // R80 变异：不夹紧\n'),
    ("M428", "焦点地板从 40pt² 抬到 200pt² ⇒ 本机 98.7/113.3 过不了（这条地板在承重）",
     UCH,
     '    static let focusMinMovedPointsSquared: Double = 40\n',
     '    static let focusMinMovedPointsSquared: Double = 200  // R80 变异\n'),
    ("M429", "占比地板从 0.08 抬到 0.5 ⇒ 本机 0.367/0.343 过不了（第二根轴也在承重）",
     UCH,
     '    static let focusMinDimFraction: Double = 0.08\n',
     '    static let focusMinDimFraction: Double = 0.5  // R80 变异\n'),
    ("M430", "处置函数无条件回 judged ⇒ 那两支 1× 出口从此没人钉（本轮最要害的一刀）",
     UCH,
     '        if focusMovedPt2 >= floorPt2 && dimFraction >= minDimFraction { return .judged }\n',
     '        if true { return .judged }  // R80 变异：门恒开（写成 if true 而不是裸 return：后者会触发 never-be-executed，那一刀就没跑成）\n'),
    ("M431", "证人地板从 40pt² 抬到 100000 ⇒ 1× 上会把『这台机器不调淡』说成『通道失明』（逃命的出口）",
     UCH,
     '    static let competenceMinMovedPointsSquared: Double = 40\n',
     '    static let competenceMinMovedPointsSquared: Double = 100000  // R80 变异\n'),
    ("M432", "噪声系数从 10 改成 0 ⇒ 地板不再随这台机器的抖动抬高（R38 那句『地板从表推导』里的系数）",
     UCH,
     '    static let focusNoiseMargin: Double = 10\n',
     '    static let focusNoiseMargin: Double = 0  // R80 变异\n'),
    ("M433", "证人臂 D 撤掉占位符那一步没生效（拍了同一张帧）⇒ 臂作废必须有红，不能当成'读得出东西'",
     UCH,
     '            field.placeholderString = ""\n            RunLoop.main.run(until: Date().addingTimeInterval(0.05))\n            let noPlaceholder = shoot()\n',
     '            field.placeholderString = ""\n            RunLoop.main.run(until: Date().addingTimeInterval(0.05))\n'
     '            field.placeholderString = placeholderWas  // R80 变异：臂 D 又装回去了\n            let noPlaceholder = shoot()\n'),
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r80_mutation_shots"
    proc = subprocess.run(["swift", "test", "--filter", filter_expression],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr


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
    return [line[:280] for line in text.splitlines()
            if "error: -[" in line and any(case in line for case in cases)]


def main():
    subset = [a for a in sys.argv[1:] if a.startswith("M")]
    if subset:
        print("只跑子集：%s（其余各刀本轮已跑过）" % ",".join(subset))
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        originals = {path: read(path) for _, _, path, _, _ in MUTATIONS}
        print("=== 基线（未变异）：三条判据都必须绿 ===")
        text = run(FILTER)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-62s = %s" % (case[:62], mark))
        if any(mark != "green" for mark in base.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, CASES)[:6]:
                print("     " + line)
            return 1
        for tag, note, path, needle, replacement in MUTATIONS:
            if subset and tag not in subset:
                continue
            print("\n%s %s" % (tag, note))
            if needle in replacement:
                print("   DRIFT-NOT-APPLIED 变异文包含原文（R76 那一族：锚点必须被换掉）")
                results.append((tag, "NOT-APPLIED")); continue
            source = read(path)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文找不到")
                results.append((tag, "NOT-APPLIED")); continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地")
                write(path, originals[path]); results.append((tag, "NOT-APPLIED")); continue
            print("   落地确认（%s）" % os.path.basename(path))
            try:
                text = run(FILTER)
                marks = verdicts_of(text, CASES)
                reds = sorted([c for c in CASES if marks[c] == "red"], key=CASES.index)
                expected = EXPECTED[tag]
                if reds == expected:
                    print("   CAUGHT 只红在预期那几条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif "error:" in text and not reds:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif not reds:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 红的不是预期那几条：%s 预期=%s" % (marks, expected))
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
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 \
            and counts.get("NOT-RUN", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
