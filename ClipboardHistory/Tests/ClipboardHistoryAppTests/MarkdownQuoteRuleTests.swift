import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R439：引用块的左侧导引线。
///
/// 两件事分两层钉：几何是**纯函数**（第 1、2 条），"哪些字符算引用"是**产品属性串**里的事实
/// （第 3 条）。像素那一半在 `UICaptureTests.testMarkdownQuotesCarryALeadingRule` ——
/// 它读的是 `detail-markdown-rendered` 帧上规则带里的最长竖墨段，源模式帧是负对照。
@MainActor
final class MarkdownQuoteRuleTests: XCTestCase {
    func testRuleSitsAtTheGutterPlusOffsetAndClearsTheText() {
        let gutter = DetailTypography.containerGutter
        XCTAssertEqual(MarkdownQuoteRule.ruleX(containerOriginX: gutter, level: 1),
                       gutter + 5, accuracy: 0.01,
                       "一级引用的线没有落在 gutter 右侧 5pt")
        XCTAssertEqual(MarkdownQuoteRule.ruleX(containerOriginX: gutter, level: 2),
                       gutter + 5 + MarkdownPresentation.quoteIndent, accuracy: 0.01,
                       "二级引用的线没有按 quoteIndent 再进一级")
        XCTAssertEqual(MarkdownQuoteRule.textClearance, 11, accuracy: 0.01,
                       "线右沿到引用文字左沿的净距不是 18-5-2=11pt")
        XCTAssertGreaterThan(MarkdownQuoteRule.textClearance, 8,
                             "净距 ≤8pt 时线和文字会粘成一条边，引用读起来像被划掉")
    }

    func testNestedQuotesGetOneRulePerLevel() {
        let span = CGRect(x: 0, y: 40, width: 600, height: 80)
        let single = MarkdownQuoteRule.ruleRects(containerOriginX: 20, textSpan: span, quoteDepth: 1)
        XCTAssertEqual(single.count, 1)
        XCTAssertEqual(single[0].minX, 25, accuracy: 0.01)
        XCTAssertEqual(single[0].minY, 40, accuracy: 0.01)
        XCTAssertEqual(single[0].height, 80, accuracy: 0.01)
        XCTAssertEqual(single[0].width, MarkdownQuoteRule.width, accuracy: 0.01)

        let nested = MarkdownQuoteRule.ruleRects(containerOriginX: 20, textSpan: span, quoteDepth: 2)
        XCTAssertEqual(nested.count, 2, "二级引用只画了一条线 ⇒ 外层那条会断在嵌套处")
        XCTAssertEqual(nested[1].minX - nested[0].minX, MarkdownPresentation.quoteIndent, accuracy: 0.01)
    }

    func testZeroDepthOrEmptySpanDrawsNothing() {
        let span = CGRect(x: 0, y: 40, width: 600, height: 80)
        XCTAssertTrue(MarkdownQuoteRule.ruleRects(containerOriginX: 20, textSpan: span, quoteDepth: 0).isEmpty)
        XCTAssertTrue(MarkdownQuoteRule.ruleRects(containerOriginX: 20,
                                                  textSpan: CGRect(x: 0, y: 0, width: 0, height: 0),
                                                  quoteDepth: 1).isEmpty)
    }

    /// 属性串这一层：引用深度必须**逐块**落在字符串上，正文段落不许带这个属性。
    /// 它也是像素判据的上游 —— 线画在哪儿由这里的深度决定。
    func testAttributedStringMarksQuoteDepthsAndLeavesBodyUnmarked() {
        let source = """
        正文前的一段。

        > 外层引用
        > > 内层引用

        正文后的一段。
        """
        let attributed = MarkdownPresentation.attributedString(for: MarkdownParser.parse(source))
        let text = attributed.string as NSString

        func depth(at needle: String) -> Int? {
            let range = text.range(of: needle)
            guard range.location != NSNotFound else {
                XCTFail("属性串里找不到「\(needle)」⇒ 这条判据没有对象")
                return nil
            }
            return attributed.attribute(MarkdownPresentation.quoteDepthAttribute,
                                        at: range.location, effectiveRange: nil) as? Int
        }

        XCTAssertEqual(depth(at: "外层引用"), 1)
        XCTAssertEqual(depth(at: "内层引用"), 2)
        XCTAssertNil(depth(at: "正文前的一段"))
        XCTAssertNil(depth(at: "正文后的一段"))
    }

    /// 导引线颜色必须是**动态色本身**：`withAlphaComponent` 会在调用那一刻把
    /// 动态色按当前外观烤死（暗档拿到 aqua 的黑），这一族坑的原文在
    /// `MarkdownPresentation.quoteColor` 的注释里。这里只钉"两档能翻面"。
    func testRuleColorFollowsBothAppearances() {
        func resolved(_ name: NSAppearance.Name) -> CGFloat {
            var value: CGFloat = 0
            NSAppearance(named: name)?.performAsCurrentDrawingAppearance {
                let color = MarkdownQuoteRule.color.usingColorSpace(.deviceRGB) ?? .black
                value = color.redComponent
            }
            return value
        }
        XCTAssertLessThan(resolved(.aqua), 0.75, "亮档的线不是深色 ⇒ 在白底上看不见")
        XCTAssertGreaterThan(resolved(.darkAqua), 0.25, "暗档的线不是浅色 ⇒ 在深底上看不见")
    }
}
