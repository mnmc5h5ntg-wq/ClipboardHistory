#!/usr/bin/env python3
"""R71 的变异对照：字号梯子那条守卫的"AppKit 那一半网"与产品路径那条判据有没有牙（BACKLOG 99）。

被判的两条判据：
  testQuickPickTypographyComesFromTheLadder   从产品入口读真的 NSTextField.font（捕获卷）
  testTextSizesComeFromTheScale               源码守卫：字面量不许就地写（令牌卷，R71 扩了半边网）

两条判据判的是**两种不同的错**，这正是把它们分开写的理由：
  · 守卫抓"就地写字号"（不管写成几）；
  · 判据抓"写了另一档令牌"（守卫对它必须是绿的）。
M381 就是这一格的正面证据：把 `VisualFont.row` 换成 `VisualFont.body` ——
守卫必须**不红**（它仍是令牌），产品路径判据必须红。

三条"电池自己会骗人"的规矩沿用 R64/R66/R67/R68：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场、且变异文不含原文）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。

用法：`python3 .scratch/motion-audit-2/mutate_r71_type_ladder.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
QPC = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
TOKENS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/VisualTokenTests.swift"
LOCK = "/tmp/r71_mutation.lock"

VIEW = "testQuickPickTypographyComesFromTheLadder"
GUARD = "testTextSizesComeFromTheScale"
BOTH = "UICaptureTests/testQuickPickTypographyComesFromTheLadder|VisualTokenTests/testTextSizesComeFromTheScale"
CASES = [VIEW, GUARD]

MUTATIONS = [
    ("M378", "把行标签字号退回本轮改之前的样子：就地写 13 ⇒ 守卫与产品路径判据**两条都必须红**"
             "（守卫红是因为它又是字面量，判据红是因为它不是 `row` 那一档）",
     QPC, BOTH,
     "            text.font = .systemFont(ofSize: VisualFont.row)",
     "            text.font = .systemFont(ofSize: 13)"),

    ("M379", "把搜索框字号退回 14（比主窗口那颗响一档）⇒ 两条都必须红",
     QPC, BOTH,
     "        field.font = .systemFont(ofSize: VisualFont.body)",
     "        field.font = .systemFont(ofSize: 14)"),

    ("M381", "把行标签换成**另一档合法令牌** `VisualFont.body` ⇒ 守卫必须**不红**（它仍是令牌），"
             "产品路径判据必须红 ⇒ 这一刀钉住两条判据的分工：守卫管字面量，判据管档位",
     QPC, BOTH,
     "            text.font = .systemFont(ofSize: VisualFont.row)",
     "            text.font = .systemFont(ofSize: VisualFont.body)"),

    ("M382", "把守卫那半边新网拆掉（共享名单里删掉 `.systemFont(ofSize:` 这一条）"
             "⇒ 正对照必须红：它再也看不见 AppKit 那半边的字面量。"
             "**这一刀第一版逃掉了**：那时守卫读自己那份数组、正对照读另一份，"
             "删一半什么都不会红 ⇒ 修法是两边共用 `Self.fontLiteralPatterns`（R57 那一课，我犯在十分钟前）",
     TOKENS, BOTH,
     '    static let fontLiteralPatterns = [".font(.system(size: ", ".systemFont(ofSize: "]',
     '    static let fontLiteralPatterns = [".font(.system(size: "]'),

    ("M383", "把正对照的喂法换错（给『AppKit 半边』那一格喂一段 SwiftUI 形状的代码）"
             "⇒ 该红的没红 ⇒ 说明那条断言其实什么都没测（它只是在读一段永远匹配不上的文本）",
     TOKENS, BOTH,
     '        let appKitOnly = "        text.font = .systemFont(ofSize: 13)\\n"',
     '        let appKitOnly = "        .font(.system(size: 13))\\n"'),
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
        print("=== 基线（未变异）：两条判据都必须绿 ===")
        text, _ = run(BOTH)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-52s = %s" % (case[:52], mark))
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
            if needle in replacement:
                print("   DRIFT-NOT-APPLIED 变异文包含原文 ⇒ 回读检查必然判『没落地』，先改刀")
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
                # M381 的期望是"守卫不红、判据红"，其它刀是"至少一条红"。
                expect_guard_green = tag == "M381"
                reds = [c for c, m in marks.items() if m == "red"]
                greens = [c for c, m in marks.items() if m == "green"]
                compile_failed = "error:" in text and not reds
                if expect_guard_green:
                    if reds == [VIEW] and GUARD in greens:
                        print("   CAUGHT 只红在产品路径判据，守卫照旧绿（分工成立）：%s" % marks)
                        results.append((tag, "CAUGHT"))
                    else:
                        print("   ESCAPED 分工没成立：%s" % marks)
                        results.append((tag, "ESCAPED"))
                elif reds:
                    print("   CAUGHT 红在：%s" % " ".join(r[:50] for r in reds))
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif any(m == "skipped" for m in marks.values()):
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
