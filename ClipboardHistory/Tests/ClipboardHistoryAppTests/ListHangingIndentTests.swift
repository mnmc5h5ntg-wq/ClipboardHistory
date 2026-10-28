import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R451：列表项的悬挂缩进（制表位与 headIndent 同轴）。
///
/// 像素/看图那一半在 `UICaptureTests.testWrappedListItemsAlignTheirContinuation`
/// （夹具 `detail-list-wrap` 的两条折行列表项）；这里钉纯策略与段落样式：
/// ① 窄标记（1 位数字/项目符号）走 16pt 最小列；② 宽标记（三位数编号）把正文列推出去；
/// ③ 列表块的制表位位置 == headIndent；④ 普通段落没有列表制表位。
@MainActor
final class ListHangingIndentTests: XCTestCase {
    func testMinimumAdvanceForNarrowMarkers() {
        XCTAssertEqual(ListHangingIndent.advance(firstLineIndent: 0, markerWidth: 7), 16, accuracy: 0.01)
        XCTAssertEqual(ListHangingIndent.advance(firstLineIndent: 16, markerWidth: 7), 32, accuracy: 0.01)
    }

    func testWideMarkerPushesTheTextColumn() {
        XCTAssertEqual(ListHangingIndent.advance(firstLineIndent: 0, markerWidth: 28), 30, accuracy: 0.01)
    }

    func testListParagraphStylePutsTheTabOnTheHangingIndent() {
        let document = MarkdownParser.parse("1. 甲\n\n100. 乙")
        let items = document.blocks.filter {
            if case .orderedItem = $0.kind { return true } else { return false }
        }
        XCTAssertEqual(items.count, 2)
        for block in items {
            let style = MarkdownPresentation.paragraphStyle(for: block)
            XCTAssertEqual(style.tabStops.count, 1, "列表块没有显式制表位")
            XCTAssertEqual(style.tabStops[0].location, style.headIndent, accuracy: 0.01,
                           "制表位与 headIndent 不同轴 ⇒ 首行正文与续行会错开")
            XCTAssertGreaterThan(style.headIndent, style.firstLineHeadIndent)
        }
        let first = MarkdownPresentation.paragraphStyle(for: items[0])
        let wide = MarkdownPresentation.paragraphStyle(for: items[1])
        XCTAssertGreaterThan(wide.headIndent, first.headIndent,
                             "三位数编号的正文列没有跟着标记变宽")
    }

    func testParagraphStyleHasNoHangingIndent() {
        let document = MarkdownParser.parse("正文")
        guard let block = document.blocks.first else { return XCTFail("没有正文块") }
        let style = MarkdownPresentation.paragraphStyle(for: block)
        XCTAssertEqual(style.headIndent, style.firstLineHeadIndent, accuracy: 0.01,
                       "普通段落不该有悬挂缩进")
    }
}
