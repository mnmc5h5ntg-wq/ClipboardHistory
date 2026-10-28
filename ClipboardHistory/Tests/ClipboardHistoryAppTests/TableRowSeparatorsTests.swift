import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R448：Markdown 表格体行分隔线的纯策略与属性契约。
///
/// 像素那一半在 `UICaptureTests.testMarkdownTablesSeparateTheirBodyRows`：
/// 四行体行要读出 3 条线、单行体行臂 0 条、线与表宽同轴。
/// 这里钉"哪一行之后画"（表头后不画、末行后不画）与属性串上的行数。
@MainActor
final class TableRowSeparatorsTests: XCTestCase {
    func testLineCount() {
        XCTAssertEqual(TableRowSeparators.lineCount(in: ""), 0)
        XCTAssertEqual(TableRowSeparators.lineCount(in: "| 甲 | 乙 |"), 1)
        XCTAssertEqual(TableRowSeparators.lineCount(in: "a\nb\nc"), 3)
    }

    func testDrawsOnlyBetweenBodyRows() {
        XCTAssertFalse(TableRowSeparators.shouldDraw(afterRow: 1, totalRows: 5),
                       "表头之后不许画线（表头由字重区分）")
        XCTAssertTrue(TableRowSeparators.shouldDraw(afterRow: 2, totalRows: 5))
        XCTAssertTrue(TableRowSeparators.shouldDraw(afterRow: 3, totalRows: 5))
        XCTAssertTrue(TableRowSeparators.shouldDraw(afterRow: 4, totalRows: 5))
        XCTAssertFalse(TableRowSeparators.shouldDraw(afterRow: 5, totalRows: 5),
                       "最后一行之后不许画线")
        XCTAssertFalse(TableRowSeparators.shouldDraw(afterRow: 2, totalRows: 2),
                       "单行体行的表不许出现线")
    }

    func testRectIsAHairlineAtTheRowBottom() {
        let rect = TableRowSeparators.rect(containerOriginX: 20, width: 100, lineBottom: 50)
        XCTAssertEqual(rect.origin.x, 20, accuracy: 0.01)
        XCTAssertEqual(rect.origin.y, 49, accuracy: 0.01)
        XCTAssertEqual(rect.width, 100, accuracy: 0.01)
        XCTAssertEqual(rect.height, 1, accuracy: 0.01)
    }

    func testRectNeverGoesNegative() {
        let rect = TableRowSeparators.rect(containerOriginX: 20, width: -5, lineBottom: 50)
        XCTAssertEqual(rect.width, 0)
        XCTAssertEqual(rect.height, 1, accuracy: 0.01)
    }

    func testTableRowCountAttributeMatchesTheBlock() {
        let body = """
        | 名称 | 数量 |
        | --- | --- |
        | 苹果 | 3 |
        | 梨 | 5 |
        | 桃 | 8 |
        | 杏 | 13 |
        """
        let storage = MarkdownPresentation.attributedString(for: MarkdownParser.parse(body))
        var counts: [Int] = []
        storage.enumerateAttribute(MarkdownPresentation.tableRowCountAttribute,
                                   in: NSRange(location: 0, length: storage.length)) { value, _, _ in
            if let count = value as? Int { counts.append(count) }
        }
        XCTAssertEqual(counts, [5], "表格的行数属性应恰好一段且为表头+四行")

        let oneRow = """
        | 甲 | 乙 |
        | --- | --- |
        | 甲 | 乙 |
        """
        let oneStorage = MarkdownPresentation.attributedString(for: MarkdownParser.parse(oneRow))
        var oneCounts: [Int] = []
        oneStorage.enumerateAttribute(MarkdownPresentation.tableRowCountAttribute,
                                      in: NSRange(location: 0, length: oneStorage.length)) { value, _, _ in
            if let count = value as? Int { oneCounts.append(count) }
        }
        XCTAssertEqual(oneCounts, [2], "表头+一行体行仍是 2，只是不画线")
    }
}
