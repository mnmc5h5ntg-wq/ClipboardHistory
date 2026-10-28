import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R453：`~~` 删除线的正文弱化（作者标记的删除内容退后一排）。
///
/// 像素那一半在 `UICaptureTests.testStruckTextIsDeEmphasized`：两段逐字相同的正文，
/// 删除段的文字在亮档更亮、暗档更暗（差 ≥20），同时删除线本身让墨数多 ≥3%。
/// 这里钉属性串：两段颜色不同、删除线属性仍在、可点链接保留链接色、正文文字不变。
@MainActor
final class StrikethroughPresentationTests: XCTestCase {
    private func document() -> MarkdownDocument {
        MarkdownParser.parse("~~同样的字~~\n\n同样的字")
    }

    func testStruckRunColorDiffersFromPlain() {
        let storage = MarkdownPresentation.attributedString(for: document())
        let text = storage.string as NSString
        let first = text.range(of: "同样的字")
        let second = text.range(of: "同样的字", options: [],
                                range: NSRange(location: first.location + first.length,
                                               length: text.length - first.location - first.length))
        XCTAssertNotEqual(first.location, NSNotFound)
        XCTAssertNotEqual(second.location, NSNotFound)
        guard first.location != NSNotFound, second.location != NSNotFound else { return }
        let struckColor = storage.attribute(.foregroundColor, at: first.location, effectiveRange: nil) as? NSColor
        let plainColor = storage.attribute(.foregroundColor, at: second.location, effectiveRange: nil) as? NSColor
        XCTAssertNotNil(struckColor)
        XCTAssertNotNil(plainColor)
        guard let struckColor, let plainColor else { return }
        XCTAssertFalse(struckColor.isEqual(plainColor),
                       "删除段与正常段颜色相同 ⇒ 删除内容没有退后")
        let struckStyle = storage.attribute(.strikethroughStyle, at: first.location, effectiveRange: nil) as? Int
        let plainStyle = storage.attribute(.strikethroughStyle, at: second.location, effectiveRange: nil) as? Int
        XCTAssertNotNil(struckStyle, "删除段的删除线属性被弱化逻辑吃掉了")
        XCTAssertNil(plainStyle, "正常段不该有删除线属性")
    }

    func testStruckLinkKeepsItsLinkColor() {
        let doc = MarkdownParser.parse("~~[官方](https://example.com)~~")
        let storage = MarkdownPresentation.attributedString(for: doc)
        let text = storage.string as NSString
        let range = text.range(of: "官方")
        XCTAssertNotEqual(range.location, NSNotFound)
        guard range.location != NSNotFound else { return }
        XCTAssertNotNil(storage.attribute(.link, at: range.location, effectiveRange: nil),
                        "可点链接被弱化逻辑吃掉了")
        XCTAssertNotNil(storage.attribute(.strikethroughStyle, at: range.location, effectiveRange: nil),
                        "链接内的删除线属性丢了")
        let color = storage.attribute(.foregroundColor, at: range.location, effectiveRange: nil) as? NSColor
        let struck = MarkdownPresentation.struckTextColor
        XCTAssertNotNil(color)
        if let color { XCTAssertFalse(color.isEqual(struck), "可点链接被降成删除线灰 ⇒ 假 affordance") }
    }

    func testTextAndVisibleTextAreUnchanged() {
        let doc = document()
        let storage = MarkdownPresentation.attributedString(for: doc)
        XCTAssertEqual(doc.visibleText, "同样的字\n同样的字")
        XCTAssertEqual(storage.string.contains("~~"), false, "`~~` 标记本身不该进渲染结果")
        XCTAssertTrue(storage.string.contains("同样的字"))
    }
}
