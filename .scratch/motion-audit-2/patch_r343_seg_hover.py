#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R343 / BACKLOG 399：亮档那颗「未选中但被悬停」的段，落在空闲与选中之间的一格（产品 + 尺 + 真值表）。"""
import io

ROOT = u"/Users/wangziyi/Codex_Project0/ClipboardHistory/"
TOK = ROOT + u"Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift"
SID = ROOT + u"Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
HAR = ROOT + u"Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
TST = ROOT + u"Tests/ClipboardHistoryAppTests/FilterPillMotionTests.swift"


def swift_ok(text):
    u"""Swift 源不能过 Python 的 ast：这里只查最容易写坏的形状（括号/花括号配平、没有中文引号）。"""
    # 花括号在这两个文件里本来就不配平（Swift 字符串插值 `\(…)` 带括号），所以只查空里没有
    if not text.strip():
        raise SystemExit(u"补丁把文件写空了")
    return text


def patch(path, pairs):
    s = io.open(path, encoding=u"utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, s.count(old), old[:60])
        s = s.replace(old, new, 1)
    swift_ok(s)
    io.open(path, u"w", encoding=u"utf-8").write(s)
    print(u"PATCHED " + path.split(u"/")[-1])


TOK_ANCHOR = u"    static let pillHover: Double = 0.045\n"
TOK_NEW = TOK_ANCHOR + u'''
    /// 0.020：**亮档**「全部 / 收藏」那颗未选中段的悬停档（R343 / BACKLOG 399）。
    ///
    /// 为什么亮档要自己一支、不再借 `controlHover + 整条梯抬量`：那一支画出来是 **207**，
    /// 而选中那颗是 **220** —— 悬停比选中还深，鼠标一停就像把这一段按了下去（R334 量到的 1.136）。
    /// 亮档的空闲 230 与选中 220 之间只有 **10 级**，任何"与两端各差 ≥4/255"的第三档只能落进
    /// **224…226** 这三个整数里（`SegmentHoverLadder` 把这句话算成一格判据）。
    /// 0.020 压出来是 `round(230 × 0.98) = 225` ⇒ 与空闲差 5、与选中差 5，两边都 ≥4。
    /// 方向也说得通：暗档的悬停（66）本来就停在空闲 52 与选中 70 **之间**，亮档这一支把同一句
    /// "朝选中走、但不到选中"落到另一条数轴上；两档仍然是**同一个意思**，只是不再共用同一个数。
    static let segHoverLight: Double = 0.020
'''

LADDER = u'''
/// 段按钮悬停档的**可行窗口**：落在空闲与选中之间，且与两端各差至少 `step255` 级。
///
/// 为什么窗口是判据而不是口味（R343 / BACKLOG 399）：亮档 空闲 230 / 选中 220 只差 10 级，
/// 于是"与两端都看得见地不同"的档位只剩 224…226 —— 之前借 1.20 对比度线去找，算什么都落空，
/// 因为**这条线比这段控件自己的选中↔空闲（1.099）还高**：要求悬停比"选中"离"空闲"更远，
/// 等于要悬停来跟选中争身份。窗口这条判据问的是同一件事，用的是这块平面自己的台阶地板。
/// 暗档（52 / 70）同一句算出 56…66，产品画在 66（R334 实测），两档都收在同一把尺里。
enum SegmentHoverLadder {
    static let step255 = 4

    static func feasible(idle: Int, selected: Int, step: Int = step255) -> [Int] {
        let lo = min(idle, selected), hi = max(idle, selected)
        return Array((lo + step)...(hi - step)).filter { $0 > lo && $0 < hi }
    }

    /// 选一个离空闲最近的那一格（悬停是"轻"的，先贴着空闲走）。
    static func preferred(idle: Int, selected: Int, step: Int = step255) -> Int? {
        let window = feasible(idle: idle, selected: selected, step: step)
        return window.min(by: { abs($0 - idle) < abs($1 - idle) })
    }
}
'''


def main():
    # ① 令牌 + 窗口判据
    s = io.open(TOK, encoding=u"utf-8").read()
    assert s.count(TOK_ANCHOR) == 1
    stem = s.replace(TOK_ANCHOR, TOK_NEW, 1)
    # 判据必须住在**类型外面**：插在 VisualFill 体内会把它后面的 token 全变成嵌套成员
    stem = stem.rstrip(u"\n") + u"\n\n" + LADDER.strip(u"\n") + u"\n"
    swift_ok(stem)
    io.open(TOK, u"w", encoding=u"utf-8").write(stem)
    print(u"PATCHED VisualTokens.swift")

    # ② 产品：亮档走自己那一支
    patch(SID, [(
        u"""        return dark ? VisualFill.pillHover
                    : HoverInk.opacity(level: VisualFill.controlHover, dark: dark)""",
        u"""        // R343 / BACKLOG 399：亮档不再借「全局悬停 + 整条梯抬量」（那一支画到 207，比选中的 220
        // 还深，鼠标一停就像把这一段按下去了）。亮档单独一支，只朝选中走 5/255，仍停在两档之间。
        return dark ? VisualFill.pillHover : VisualFill.segHoverLight""",
    )])

    # ③ 尺：亮档从「只印」升成窗口门（暗档原样，另加同一格窗口读数当第二证人）
    patch(HAR, [(
        u"            let selVsIdle = Self.contrastRatio(segIdleR.grey, segIdleL.grey)\n",
        u"""            let selVsIdle = Self.contrastRatio(segIdleR.grey, segIdleL.grey)
            // R343 / 399：**窗口门**（两档都量）。悬停必须落在空闲与选中之间、与两端各差 ≥4/255。
            // 亮档以前「只印不判」，因为借来的 1.20 对比度线比这段控件自己的选中↔空闲（1.099）还高
            // —— 那条线要的不是"悬停看得见"，是"悬停别跟选中抢身份"，而它用的刻度做不到这件事。
            // 窗口这条问的是同一件事，用的是这块平面自己的台阶地板（`SegmentHoverLadder`）。
            let hoverWindow = SegmentHoverLadder.feasible(idle: segIdleR.grey, selected: segIdleL.grey)
            emit("SEG_HOVER_WINDOW \\(tag) 空闲=\\(segIdleR.grey) 选中=\\(segIdleL.grey)"
                 + " 步=\\(SegmentHoverLadder.step255) 窗口="
                 + (hoverWindow.isEmpty ? "空集" : "\\(hoverWindow.first!)…\\(hoverWindow.last!)灰阶")
                 + " 产品画在=\\(segHovR.grey)"
                 + " 判定=" + (hoverWindow.contains(segHovR.grey) ? "在窗口内" : "越界（该修产品）"))
            XCTAssertFalse(hoverWindow.isEmpty,
                "\\(tag)：悬停窗口空了 ⇒ 这块控件放不下第三档，该换轴（399）")
            XCTAssertTrue(hoverWindow.contains(segHovR.grey),
                "\\(tag)：悬停画在 \\(segHovR.grey)，窗口是 \\(hoverWindow) ⇒ 越界："
                + "要么压过了选中（像按下），要么轻到看不见")
""",
    ), (
        u"            // 亮档**不**按这条门断言（只印）。理由是一条可算的秩序，不是口味：",
        u"            // 亮档这条对比度门**不**断言（只印）。理由是一条可算的秩序，不是口味：",
    ), (
        u'                 + (appearance == .darkAqua ? "（门）" : "（只印不判：同向且更弱的可行集是空集，见 399）")',
        u'                 + (appearance == .darkAqua ? "（对比度门）" : "（对比度线只印；亮档的门是 SEG_HOVER_WINDOW）")',
    )])

    # ④ 真值表：窗口是判据，不是装饰
    patch(TST, [(
        u"    func testSegmentKnobLiftSplitsByAppearanceAndReadsTheToken() {",
        u"""    /// R343 / BACKLOG 399：窗口判据的真值表。三档都从**实测的那几个数**来，不自己编边界。
    func testSegmentHoverWindowIsArithmeticNotTaste() {
        // 亮档实测：空闲 230 / 选中 220 ⇒ 只剩 224…226 三格
        XCTAssertEqual(SegmentHoverLadder.feasible(idle: 230, selected: 220), [224, 225, 226])
        // 暗档实测：空闲 52 / 选中 70 ⇒ 56…66（产品画在 66，落在窗口里）
        let dark = SegmentHoverLadder.feasible(idle: 52, selected: 70)
        XCTAssertEqual(dark.first, 56)
        XCTAssertEqual(dark.last, 66)
        XCTAssertTrue(dark.contains(66))
        // 亮档那一支压出来的电平必须真的落在窗口里（token 与判据不是两份权威）
        let painted = Int((230.0 * (1.0 - VisualFill.segHoverLight)).rounded())
        XCTAssertTrue(SegmentHoverLadder.feasible(idle: 230, selected: 220).contains(painted),
                      "0.020 压出来是 \\(painted) ⇒ 不在 224…226 里")
        // 负对照：两档挨得太近（差 ≤ 2×步）⇒ 窗口必须是空集，不许硬塞一格
        XCTAssertTrue(SegmentHoverLadder.feasible(idle: 230, selected: 225).isEmpty)
        // 方向：窗口里的每一格都在空闲与选中之间（不是"越深越好"）
        for v in SegmentHoverLadder.feasible(idle: 230, selected: 220) {
            XCTAssertGreaterThan(v, 220)
            XCTAssertLessThan(v, 230)
        }
    }

    func testSegmentKnobLiftSplitsByAppearanceAndReadsTheToken() {""",
    )])


if __name__ == u"__main__":
    main()
