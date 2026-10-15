#!/usr/bin/env python3
"""R79 的变异对照：存在性闸门换成"量宽度"之后，那道闸门还分得开东西吗。

背景（读 R78 的 CI 读出来的，run 38757049151）：R78 那道闸门用的是
"占位区里 ≥20 个有墨像素"，结果它在 runner 上**没拦住** —— 那四条红原样还在。
原因：那颗放大镜符号就住在搜索框左边 10–24pt，AppKit 画得出它，
而占位字那串画不出来 ⇒ 计数过了地板，闸门恒开。
R79 换成**有墨像素的 x 包围盒宽度**（本机实测：图标自己 17.0pt，图标 + 占位字 86.5 / 87.0pt，
地板 40pt），并加一条对照：只框住图标那一小块时，宽度必须**过不了**闸门。

四刀：
  M419 地板从 40pt 降到 10pt（图标一个人就能开门）  ⇒ 只有 FOCUS 该红（图标那一格）
  M420 把图标探针的矩形换成整条 band（对照失去对象）⇒ 只有 FOCUS 该红
  M421 `alphaInkSpan` 的地板从 8/255 抬到 250/255    ⇒ 只有 FOCUS 该红（2× 上闸门会误关）
  M422 第二根证人（文字独占区 ≥20 个像素）抬到 100000 ⇒ 只有 FOCUS 该红（那根证人承重）

用法：`python3 .scratch/motion-audit-2/mutate_r79_span_gate.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
UCH = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
LOCK = "/tmp/r79_mutation.lock"

FOCUS = "testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing"
GUARD = "testEveryTwoStateRulerReadsBothAxes"
CASES = [FOCUS, GUARD]
FILTER = "|".join(["UICaptureTests/" + FOCUS, "MotionFilmstripTests/" + GUARD])
EXPECTED = {"M419": [FOCUS], "M420": [FOCUS], "M421": [FOCUS], "M422": [FOCUS]}

MUTATIONS = [
    ("M419", "把存在性的地板从 40pt 降到 10pt ⇒ 那颗放大镜一个人就能把门开掉，"
             "而这条判据看起来仍然'有存在性证人'",
     UCH,
     '    static let placeholderMinSpanPoints: Double = 40\n',
     '    static let placeholderMinSpanPoints: Double = 10  // R79 变异：图标也够开门了\n'),
    ("M420", "把图标探针的矩形换成整条 band ⇒ 对照读的不是它要读的那个量（'正对照读判据自己那个量'那一课）",
     UCH,
     '                                  width: 17 * CGFloat(scale), height: band.height)\n',
     '                                  width: band.width, height: band.height)  // R79 变异\n'),
    ("M421", "把 `alphaInkSpan` 的 alpha 地板从 8/255 抬到 250/255 ⇒ 什么都量不到，"
             "2× 上闸门会误判成'没画'而红 —— 钉的是这把新尺承重",
     UCH,
     '    static func alphaInkSpan(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 8) -> (min: Int, max: Int) {',
     '    static func alphaInkSpan(_ rep: NSBitmapImageRep, rect: CGRect, floor: Int = 250) -> (min: Int, max: Int) {  // R79 变异'),

    ("M422", "把第二根证人的地板从 20 抬到 100000 ⇒ 本机 2× 上闸门误关而红。"
             "这一格证明'文字独占区'那一列不是陪着打的读数：一圈描边骗得过包围盒宽度，骗不过它",
     UCH,
     '            let placeholderDrawn = spanWidthPt >= Self.placeholderMinSpanPoints && textOnlyInk >= 20\n',
     '            let placeholderDrawn = spanWidthPt >= Self.placeholderMinSpanPoints && textOnlyInk >= 100000  // R79 变异\n'),
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r79_mutation_shots"
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
    return [line[:260] for line in text.splitlines()
            if "error: -[" in line and any(case in line for case in cases)]


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
                print("   DRIFT-NOT-APPLIED 变异文包含原文")
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
                reds = [c for c in CASES if marks[c] == "red"]
                if reds == EXPECTED[tag]:
                    print("   CAUGHT 只红在预期那一条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif "error:" in text and not reds:
                    print("   NOT-RUN 编译没过")
                    print("     " + "\n     ".join([l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif not reds:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 红的不是预期那一条：%s 预期=%s" % (marks, EXPECTED[tag]))
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
