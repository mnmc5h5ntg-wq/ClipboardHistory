import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R447：Markdown 主题分隔线的**复制语义**与几何。
///
/// 像素那一半在 `UICaptureTests.testThematicBreaksAreDrawnAsALine`：帧上必须有一条
/// ≥450pt、≤4pt 厚的通栏线。这里钉的是帧上读不出来的两件事：
/// ① 属性串里不许再有 24 个 `─`（复制渲染结果时不许把装饰带进剪贴板）；
/// ② 线的矩形是通栏、1pt、落在行中 —— 与视图层用的是同一个纯函数。
@MainActor
final class ThematicBreakRuleTests: XCTestCase {
    private func document() -> MarkdownDocument {
        MarkdownParser.parse("甲\n\n---\n\n乙")
    }

    func testCopiedTextHasNoBoxDrawingCharacters() {
        let document = document()
        let storage = MarkdownPresentation.attributedString(for: document)
        XCTAssertFalse(storage.string.contains("─"),
                       "渲染结果的文本存储里还有 `─` ⇒ 复制会把装饰性字符带进剪贴板")
        XCTAssertTrue(storage.string.contains("甲"))
        XCTAssertTrue(storage.string.contains("乙"))
        XCTAssertEqual(document.visibleText, "甲\n\n乙",
                       "可见文字契约不该把装饰线算成内容")
    }

    func testOnlyTheBreakCarriesTheAttribute() {
        let document = document()
        let storage = MarkdownPresentation.attributedString(for: document)
        var ranges: [NSRange] = []
        storage.enumerateAttribute(MarkdownPresentation.thematicBreakAttribute,
                                   in: NSRange(location: 0, length: storage.length)) { value, range, _ in
            if value != nil { ranges.append(range) }
        }
        XCTAssertEqual(ranges.count, 1, "主题分隔线的属性不是恰好一段（实际 \(ranges.count)）")
        guard let range = ranges.first else { return }
        XCTAssertEqual((storage.string as NSString).substring(with: range),
                       ThematicBreakRule.placeholder,
                       "分隔线在文本里应只剩一个占位空格（保住行高）")
    }

    func testRuleRectIsFullWidthHairlineCenteredOnTheLine() {
        let rect = ThematicBreakRule.rect(containerOriginX: 20, containerWidth: 600,
                                          lineTop: 100, lineHeight: 20)
        XCTAssertEqual(rect.origin.x, 20, accuracy: 0.01)
        XCTAssertEqual(rect.width, 600, accuracy: 0.01)
        XCTAssertEqual(rect.height, 1, accuracy: 0.01)
        XCTAssertEqual(rect.origin.y, 100 + (20 - 1) / 2, accuracy: 0.01)
    }

    func testRuleRectNeverGoesNegative() {
        let rect = ThematicBreakRule.rect(containerOriginX: 20, containerWidth: -5,
                                          lineTop: 100, lineHeight: 0.5)
        XCTAssertEqual(rect.width, 0)
        XCTAssertEqual(rect.height, 1, accuracy: 0.01)
        XCTAssertEqual(rect.origin.y, 100, accuracy: 0.01)
    }
}
