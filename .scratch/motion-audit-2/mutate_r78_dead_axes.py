#!/usr/bin/env python3
"""R78 的变异对照：R77 那条"双向名册"与 R78 新加的存在性闸门，各自有没有牙。

R78 修的是三样东西，每样都会单独坏：
  ① 名册里可以躺着一把**零调用点**的死尺（R77 实测：`paintedXRange` 全仓只有它自己的声明，
     而名册收了它、理由里还替它写了调用者）⇒ 新增"每条登记必须有人调"这一格（U-137）。
  ② "两态"的识别从**减法针脚**换成**签名形状**（R77 漏掉了 `alphaBandDelta`，因为它写的是
     `abs(maxA - maxB) > floor`）⇒ 新检测器必须认折行的签名，也不许把单参函数数成两态
     （`NSBitmapImageRep` 含子串 `Bitmap` —— 第一版就栽在这里，U-138 的姊妹格）。
  ③ 焦点那条判据在 runner 上红了（run 38743276799 与 38751643297：框内变化像素 0、
     alpha 差 0.05；本机 1797 / 3.93）⇒ 加一条**不依赖两态相减的存在性尺**，
     处置按机器分开：2× 上没画 ⇒ 红，1× 上没画 ⇒ 点名 not-run（R60 那一课）。

六刀：
  M413 撤掉"长写法先从串里挖掉"      ⇒ 只有 GUARD 该红（正对照 H：单参电平尺被当成两态尺）
  M414 撤掉折行签名的累加            ⇒ 只有 GUARD 该红（正对照 G：alphaBandDelta 就是这么漏的）
  M415 `callSites` 把声明也算成调用  ⇒ 只有 GUARD 该红（正对照 F：计数器自己必须分得清）
  M416 注入一把零调用点的死尺 + 它的登记 ⇒ 只有 GUARD 该红（名册等式抓不到这一条）
  M417 存在性闸门恒"没画"            ⇒ 只有 FOCUS 该红（永远 NOT_RUN 必须本机付账）
  M418 存在性尺的地板从 8 抬到 250    ⇒ 只有 FOCUS 该红（那把尺是承重的，不是装饰）

三条电池规矩沿用 R64/R66/R67/R68/R71/R74/R75/R76/R77：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场、变异文不含原文）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。编号从 M413 起（M403–M412 是 R77 的，先查重）。

用法：`python3 .scratch/motion-audit-2/mutate_r78_dead_axes.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
UCH = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
LOCK = "/tmp/r78_mutation.lock"

GUARD = "testEveryTwoStateRulerReadsBothAxes"
FOCUS = "testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing"
CASES = [GUARD, FOCUS]
FILTER = "|".join(["MotionFilmstripTests/" + GUARD, "UICaptureTests/" + FOCUS])

EXPECTED = {
    "M413": [GUARD],
    "M414": [GUARD],
    "M415": [GUARD],
    "M416": [GUARD],
    "M417": [FOCUS],
    "M418": [FOCUS],
}

DEAD_RULER = (
    '    /// R78 变异：一把零调用点的死尺（只读亮度、没人调，但扫得到 ⇒ 名册等式抓不到它）。\n'
    '    private static func deadRulerProbe(_ a: Bitmap, _ b: Bitmap, floor: Int) -> Int {\n'
    '        var hit = 0\n'
    '        for i in stride(from: 0, to: max(0, a.pixels.count - 4), by: 28) {\n'
    '            if abs(Int(a.pixels[i + 2]) - Int(b.pixels[i + 2])) > floor { hit += 1 }\n'
    '        }\n'
    '        return hit\n'
    '    }\n'
    '\n'
    '    static func luminanceOnlyExemptions() -> [(qualifiedName: String, reason: String)] {  // R78 变异：锚点行改写，否则变异文包含原文\n'
    '        [\n'
    '            (qualifiedName: "MotionFilmstripTests.swift#deadRulerProbe",\n'
    '             reason: "R78 那一刀造的登记：尺子存在、确实只读一根轴、也确实扫得到，"\n'
    '                    + "但它没有任何调用点 ⇒ 只有\'每条登记必须有人调\'那一格抓得到这一条。"\n'
    '                    + "名册等式抓不到，因为它就在扫到的集合里。"),\n')

MUTATIONS = [
    ("M413", "撤掉『长写法先从串里挖掉』那一步 ⇒ `NSBitmapImageRep` 被同时数成长写法与 `Bitmap`，"
             "只收一张图的水平尺（`meanAlpha` / `meanLuma`）冒充两态尺。R78 第一版真的这么错过",
     MFT,
     '        let longForm = bitmapParameterTypes[0]\n'
     '        let longCount = countOccurrences(parameters, longForm)\n'
     '        let withoutLong = parameters.replacingOccurrences(of: longForm, with: " ")\n'
     '        var seen = longCount\n'
     '        for type in bitmapParameterTypes.dropFirst() { seen += countOccurrences(withoutLong, type) }\n',
     '        var seen = 0\n'
     '        for type in bitmapParameterTypes { seen += countOccurrences(parameters, type) }  // R78 变异\n'),

    ("M414", "撤掉折行签名的累加（签名只取第一行）⇒ 两行写成的 `alphaBandDelta` 不再被认成两态尺。"
             "这一格钉的是正对照 G：名册不能随**排版**变化而漏条目",
     MFT,
     '            while !header.contains("{"), headerEnd + 1 < lines.count, headerEnd - index < 8 {\n'
     '                headerEnd += 1\n'
     '                header += "\\n" + lines[headerEnd]\n'
     '            }\n',
     '            // R78 变异：签名只取第一行\n'),

    ("M415", "`callSites` 不把声明那一次扣掉 ⇒ 一把只有声明的死尺也被数成\'有人用\'。"
             "这一格钉的是正对照 F（调用点计数器自己必须分得清声明与使用）",
     MFT,
     '        return max(0, occurrences - declarations)\n',
     '        return occurrences + declarations  // R78 变异：声明也算调用\n'),

    ("M416", "注入一把**零调用点**的死尺，并把它登记进名册 ⇒ 名册等式仍然成立（扫得到、也登记了），"
             "只有\'每条登记必须有人调\'那一格会红。这就是 R77 真实存在过的状态（`paintedXRange`）",
     MFT,
     '    static func luminanceOnlyExemptions() -> [(qualifiedName: String, reason: String)] {\n        [\n',
     DEAD_RULER),

    ("M417", "存在性闸门恒说\'这一格没画\'⇒ 本机 2× 必须红（\'永远 NOT_RUN\'不能免费）。"
             "这一格拦的是最省事的那种修法：把判据降级成 skip 就当作修好了",
     UCH,
     # R384 重钉：R80 之后这条存在性闸门改成 `spanWidthPt && textOnlyInk` 两个前提。
     # 针钉当前那一行，刀仍把「有没有画」压成恒 false。
     '            let placeholderDrawn = spanWidthPt >= Self.placeholderMinSpanPoints && textOnlyInk >= 20\n',
     '            let placeholderDrawn = spanWidthPt >= Self.placeholderMinSpanPoints && textOnlyInk >= 100000  // R78 变异：永远说没画\n'),

    ("M418", "把存在性尺的地板从 8/255 抬到 250/250 ⇒ 它什么都读不到 ⇒ 闸门在 2× 上误判成\'没画\'而红。"
             "钉的是那把新尺子**承重**：它不是给日志多加一列",
     UCH,
     '    static func alphaInkPixels(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 8) -> Int {',
     '    static func alphaInkPixels(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 250) -> Int {  // R78 变异'),
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r78_mutation_shots"
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
    hits = []
    for line in text.splitlines():
        if "error: -[" in line and any(case in line for case in cases):
            hits.append(line[:260])
    return hits


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        originals = {path: read(path) for _, _, path, _, _ in MUTATIONS}
        print("=== 基线（未变异）：两条判据都必须绿 ===")
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
                text = run(FILTER)
                marks = verdicts_of(text, CASES)
                reds = [c for c in CASES if marks[c] == "red"]
                compile_failed = "error:" in text and not reds
                if reds == EXPECTED[tag]:
                    print("   CAUGHT 只红在预期那一条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif not reds:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 红的不是预期那一条（或连带红了别的）：%s 预期=%s"
                          % (marks, EXPECTED[tag]))
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
