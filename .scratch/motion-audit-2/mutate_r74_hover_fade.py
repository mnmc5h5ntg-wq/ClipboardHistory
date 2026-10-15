#!/usr/bin/env python3
"""R74 的变异对照：浮层悬停「不加淡入」这条决定的三样东西各有没有牙（U-115 / U-128）。

被这条判据判的三样东西（都在 `testOverlayHoverHasNoFadeAndTheReasonIsMeasuredOnTwoCorpora` 里）：
  ① 两个语料的**重排读数**：整列变了几个前缀、指针那一格换了几次记录；
  ② **结论守卫**：`QuickPickRowView` 那一段里不许出现动画 API（决定是量过才做的）；
  ③ **机制守卫 + 扫描器自己的正/反/右边界对照**：`rebuildRows` 里必须还看得见拆灰那一句。

这一批最有意思的是 M387：它**只挪机制、不改行为**？不 —— 它把「重排时把那层灰拆掉」换成
「重排时只重画」，于是产品行为真的变了（灰会留在错误的行上），而**像素判据全绿**，
因为离屏捕获从来不走 `hovered`（走 `rowHoveredForCapture`，见 BACKLOG 95 那条通道边界）。
⇒ 这一刀钉住的是「机制守卫与像素判据不是重叠的冗余，是同一条决定的两条独立证据」：
   只有一条会红的那一类改动确实存在，而它就是决定过期那一类。

三条「电池自己会骗人」的规矩沿用 R64/R66/R67/R68/R71：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场）；
③ 汇总把「没抓到 / 没跑成 / 没落地」分开设计数。
另外沿用 R71 那条教训：变异文**不许包含原文**（否则回读必然判「没落地」），
所以 M390 那一刀写成「换一种写法」而不是「在原句尾巴上改返回值」。

**编号从 M386 起，不是 M385**：M385 已经被 R72 那一批用掉（证人节拍 0.004→0.02，
D-130 里记的是"本地无判别力、由 runner 判"）。第一版我顺手从 M385 开始排，
写完才在台账里撞上 —— 两把不同的刀共用一个号，等于以后谁按号去找证据都会找错。

用法：`python3 .scratch/motion-audit-2/mutate_r74_hover_fade.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
QPC = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
HARNESS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
LOCK = "/tmp/r74_mutation.lock"

FADE = "testOverlayHoverHasNoFadeAndTheReasonIsMeasuredOnTwoCorpora"
PIXEL = "testOverlayHoverTintIsPaintedAndConfinedToItsRow"
OUTLINE = "testOverlayHoverFillSharesTheSelectionPillsOutline"
POLICY = "testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar"
BOTH = "UICaptureTests/testOverlayHover"
CASES = [FADE, PIXEL, OUTLINE, POLICY]

# 每一刀**期望红在哪些判据上**（默认：只红在淡入那一条）。
# 期望写成表而不是写死一条规则，是因为「红的比预期多」也必须有名字：
# M387 一进来就是这一格 —— 它同时红在两条读同一机制的守卫上，那不是失控，是这两条本来同族。
EXPECTED = {"M387": [FADE, POLICY]}

MUTATIONS = [
    ("M386", "给悬停那一段**真的加上一条动画**（`mouseMoved` 走 `NSAnimationContext`）"
             "⇒ 只有结论守卫该红，三条像素/几何判据必须照旧绿（它们量的不是过渡）",
     QPC, BOTH,
     '    override func mouseMoved(with event: NSEvent) { hovered = true }',
     '    override func mouseMoved(with event: NSEvent) {\n'
     '        NSAnimationContext.runAnimationGroup { _ in self.hovered = true }\n'
     '    }'),

    ("M387", "把「重排时拆掉那层灰」换成「重排时只重画」——**机制被撤，函数还在**"
             "⇒ 读这个机制的**两条**守卫（淡入那条 + R67 的真值表那条）都必须红，而像素判据全绿："
             "离屏捕获从不走 `hovered`（BACKLOG 95 的通道边界）。"
             "这一刀一开始记的是 ESCAPED，因为电池要求「只红一条」—— 那是我的期望写错了，不是网写错了："
             "两条守卫确实判同一件事，于是 R74 把它们改成**共用 `Self.functionBody`**（一处坏），"
             "并把这一刀的期望改成「两条一起红」。"
             "留这一格在日志里是因为它顺手证了另一件事：这两条守卫**不是冗余**——"
             "有一条真会漏的改动只有源码守卫抓得到，像素判据对它完全无感",
     QPC, BOTH,
     '            (rowView as? QuickPickRowView)?.clearHover()',
     '            (rowView as? QuickPickRowView)?.refreshFromOutside()'),

    ("M388", "把嵌套前缀语料改成**不嵌套**的（每条开头都换字）⇒ 「每个字都往下切一层」这个观察没了"
             "⇒ 两条读数断言（整列 7/8、指针那格 6/8）必须一起红：读数不是硬编码的常数",
     HARNESS, BOTH,
     '        let stems = ["一", "一二", "一二三", "一二三四", "一二三四五", "一二三四五六", '
     '"一二三四五六七", "一二三四五六七八"]',
     '        let stems = ["甲一", "乙二", "丙三", "丁四", "戊五", "己六", "庚七", "辛八"]'),

    ("M389", "把**反面语料**那条对照指到嵌套语料上（`visual` → `nested`）"
             "⇒ 必须红：两个语料不是可互换的，帧夹具那个「只剩一条命中所以不重排」是真的反面",
     HARNESS, BOTH,
     '        XCTAssertLessThan(visual.changed, visual.prefixes - 1,',
     '        XCTAssertLessThan(nested.changed, nested.prefixes - 1,'),

    ("M390", "让扫描器在**没找到签名**时返回整份源码（而不是空串）⇒ 负对照必须红。"
             "没有这一格，`contains(clearHover)` 会在函数改名之后仍然绿 —— 那是「永远看得见」的守卫",
     HARNESS, BOTH,
     '        guard let start = source.range(of: signature) else { return "" }',
     '        let found = source.range(of: signature)\n'
     '        guard let start = found else { return source }'),

    ("M391", "让扫描器**不截方法结尾**（把签名之后的整个文件后半都当成方法体）"
             "⇒ 右边界对照必须红：它说明 `contains(clearHover)` 量的不再是这一个函数，而是这个文件",
     HARNESS, BOTH,
     '        guard let end = rest.range(of: "\\n    }") else { return "" }\n'
     '        return String(rest[rest.startIndex..<end.lowerBound])',
     '        return rest'),
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r74_mutation_shots"
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
        print("=== 基线（未变异）：四条判据都必须绿 ===")
        text, _ = run(BOTH)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-64s = %s" % (case[:64], mark))
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
                text, _ = run(case_filter)
                marks = verdicts_of(text, CASES)
                expected = EXPECTED.get(tag, [FADE])
                reds = [c for c in CASES if marks[c] == "red"]
                # 「期望之外还红了」与「期望的那条没红」是两种不同的失效，都要算没抓到：
                # 前者说明这一刀波及了不该动的判据（它量的不是那一格），
                # 后者就是真的逃掉了。
                extra = [c for c in reds if c not in expected]
                missed = [c for c in expected if c not in reds]
                not_green_elsewhere = [c for c in CASES if c not in expected and marks[c] != "green"]
                compile_failed = "error:" in text and not reds
                if reds == expected and not not_green_elsewhere:
                    print("   CAUGHT 红在的正好是期望那 %d 条，其余照旧绿：%s" % (len(expected), marks))
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif missed and not reds:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                elif missed:
                    print("   ESCAPED 期望红的那条没红（%s），却红了别的：%s" % (missed, marks))
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 连带红了不该动的判据 %s ⇒ 这一刀量的不是那一格：%s"
                          % ([c[:40] for c in extra + not_green_elsewhere], marks))
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
