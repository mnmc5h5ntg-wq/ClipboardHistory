#!/usr/bin/env python3
"""R76 的变异对照：浮层搜索框"焦点那一档"的四条断言各有没有牙（U-116 / U-131…U-133 / D-134）。

被判的那一条判据 `testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing` 里有四样东西：
  ① 焦点落进那颗框（读产品对象：窗口响应者是字段编辑器）；
  ② 焦点**有**视觉后果（框内 ≥500 个变化像素）且方向是"让位"（alpha 必须降）；
  ③ 后果留在框内（框外那一圈 0 个像素）⇒ "不加自定义焦点环"是量过的决定；
  ④ 系统环不许被关掉（`focusRingType` 必须是 raw 0）。

五刀分别打在不同地方，其中两刀是**产品侧**的：
  M398 把系统环关掉（`focusRingType = .none`）⇒ 只有④该红。
       而这一刀同时给出另一件事的证据：③在同一刀里**仍然绿** ⇒ 关掉环不改任何像素
       ⇒ 这条通道本来就看不见环，④是唯一防线（那句判据文档里的话不是推测）。
  M399 把 `show()` 里那句 `makeFirstResponder(field)` 删掉 ⇒ 只有源码守卫该红，
       ①②③全绿（夹具那条路径自己会聚焦）⇒ 这一族"产品不聚焦"在帧与行为判据里都没有影子。
三刀是判据侧的，钉的是"读数不是硬编码"：
  M400 拿 `focused` 减自己（本轮真实犯过的那一次，U-131）⇒ ②该红；
  M401 把量尺的带挪到列表那一区 ⇒ ②该红（焦点后果不在那儿）；
  M402 把方向断言翻过来 ⇒ 该红（钉住"让位"而不是"变响"这个方向是有内容的）。

三条电池规矩沿用 R64/R66/R67/R68/R71/R74/R75：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场、变异文不含原文）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。编号从 M398 起（M392–M397 是 R75 的，先在台账查重）。

用法：`python3 .scratch/motion-audit-2/mutate_r76_focus.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
QPC = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
HARNESS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
LOCK = "/tmp/r76_mutation.lock"

FOCUS = "testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing"
TINT = "testOverlayHoverTintIsPaintedAndConfinedToItsRow"
OUTLINE = "testOverlayHoverFillSharesTheSelectionPillsOutline"
POLICY = "testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar"
TYPE = "testQuickPickTypographyComesFromTheLadder"
AXIS = "testTextSizesComeFromTheScale"
BOTH = ("UICaptureTests/testOverlaySearchFieldFocus|UICaptureTests/testOverlayHover|"
        "UICaptureTests/testQuickPickTypography|VisualTokenTests/testTextSizesComeFromTheScale")
CASES = [FOCUS, TINT, OUTLINE, POLICY, TYPE, AXIS]

MUTATIONS = [
    ("M398", "产品侧：把那颗框的系统焦点环关掉（`focusRingType = .none`）"
             "⇒ 只有④该红，而③必须**照旧绿** —— 这一刀顺手证明了'这条通道看不见环'，"
             "所以④不是冗余装饰，它是唯一防线。"
             "（这一刀前两版都 NOT-APPLIED，都是被'变异文包含原文'那条规矩拦下的：\n"
             "             纯插入型的刀（在原行后面加一行）永远包含原行本身 ⇒ 必须顺手把原行改个写法，"
             "             这里给原行尾上加了句注释。R74/R75 记过的那族自缚，本轮撞了两次才绕开）",
     QPC, BOTH,
     '        field.drawsBackground = false\n',
     '        field.focusRingType = .none\n        field.drawsBackground = false  // R76 变异\n'),

    ("M399", "产品侧：把 `show()` 的焦点接收对象换成 nil（产品不聚焦）"
             "⇒ 只有源码守卫该红（①②③④全绿，因为夹具那条路径自己会聚焦）"
             "⇒ 钉的是'产品不聚焦'这一族回归在帧与行为判据里都没有影子，只有这条守卫抓得到",
     QPC, BOTH,
     '        if panel.makeFirstResponder(field) {\n',
     '        if panel.makeFirstResponder(nil) {\n'),

    ("M400", "判据侧：拿 `focused` 减它自己（**本轮真实犯过的那一次**，U-131）"
             "⇒ ②该红：'两态必须不同'那格正对照仍然绿（响应者确实被换掉了），"
             "所以这一刀证明光有响应者对照不够，像素那格必须自己站着",
     HARNESS, BOTH,
     '            let unfocused = shoot()\n',
     '            let unfocused = focused\n'),

    ("M401", "判据侧：把量尺那条带挪到列表区（y 写死 300）"
             "⇒ ②该红：焦点的视觉后果不在那儿 ⇒ 读数不是'任何地方都能找到 500 个像素'",
     HARNESS, BOTH,
     '                              y: (content.bounds.height - inContent.maxY) * CGFloat(scale),\n',
     '                              y: 300,\n'),

    ("M402", "判据侧：把方向断言翻过来（要求聚焦那一格反而更**响**）"
             "⇒ 该红：'焦点让占位符退后'与'焦点把框叫响'是两种设计，这一格钉的是前者",
     HARNESS, BOTH,
     # R382 重钉：R80 把「绝对掉 2.0」的地板拆成方向断言之后，旧针里的 `- 2.0` 没了。
     # 同义坏法：把方向翻过来（要求聚焦那一格反而更响）。
     '            XCTAssertLessThanOrEqual(alphaFocused, alphaUnfocused,',
     '            XCTAssertGreaterThanOrEqual(alphaFocused, alphaUnfocused,'),
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r76_mutation_shots"
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
            hits.append(line[:240])
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
        print("=== 基线（未变异）：六条判据都必须绿 ===")
        text = run(BOTH)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-62s = %s" % (case[:62], mark))
        if any(mark != "green" for mark in base.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, CASES)[:6]:
                print("     " + line)
            return 1

        for tag, note, path, case_filter, needle, replacement in MUTATIONS:
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
                text = run(case_filter)
                marks = verdicts_of(text, CASES)
                reds = [c for c in CASES if marks[c] == "red"]
                compile_failed = "error:" in text and not reds
                if reds == [FOCUS]:
                    print("   CAUGHT 只红在焦点那条判据：%s" % marks)
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
                    print("   ESCAPED 红的不是预期那一条（或连带红了别的）：%s" % marks)
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
