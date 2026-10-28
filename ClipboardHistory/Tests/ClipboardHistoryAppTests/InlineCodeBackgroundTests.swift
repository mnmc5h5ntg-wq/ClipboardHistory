import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R455：行内代码底色的内边距。
///
/// 旧形状是 `.backgroundColor` 只按字形 advance 涂：底色带 94.5pt、字宽 92.0pt，
/// 左右各 ~1pt。像素那一半在 `UICaptureTests.testInlineCodeBackgroundHasPadding`；
/// 这里钉属性契约（不再背 `.backgroundColor`、只标 run）与纯几何。
@MainActor
final class InlineCodeBackgroundTests: XCTestCase {
    private func attributes(for marks: MarkdownInline.Mark) -> [NSAttributedString.Key: Any] {
        let block = MarkdownBlock(kind: .paragraph, runs: [
            MarkdownInline(marks: marks, text: "swift build")
        ])
        return MarkdownPresentation.attributes(for: block.runs[0], in: block)
    }

    func testInlineCodeCarriesTheBandAttributeNotABackgroundColor() {
        let code = attributes(for: .code)
        XCTAssertNotNil(code[MarkdownPresentation.inlineCodeAttribute])
        XCTAssertNil(code[.backgroundColor], "行内码不应再由属性串背底色（它没有内边距）")

        let plain = attributes(for: .plain)
        XCTAssertNil(plain[MarkdownPresentation.inlineCodeAttribute])
        XCTAssertNil(plain[.backgroundColor])
    }

    func testRectAddsPaddingOnWhitespaceSidesOnly() {
        let paddings = InlineCodeBackground.horizontalPaddings(previousIsWhitespace: true,
                                                               nextIsWhitespaceOrEnd: false)
        XCTAssertEqual(paddings.left, InlineCodeBackground.horizontalPadding, accuracy: 0.01)
        XCTAssertEqual(paddings.right, 0, accuracy: 0.01)
        let rect = InlineCodeBackground.rect(lineRect: CGRect(x: 0, y: 10, width: 200, height: 18),
                                             startX: 100, endX: 192,
                                             leftPadding: paddings.left,
                                             rightPadding: paddings.right,
                                             containerOrigin: CGPoint(x: 20, y: 50))
        XCTAssertEqual(rect.origin.x, 20 + 100 - InlineCodeBackground.horizontalPadding, accuracy: 0.01)
        XCTAssertEqual(rect.origin.y, 50 + 10 - InlineCodeBackground.verticalPadding, accuracy: 0.01)
        XCTAssertEqual(rect.width, 92 + InlineCodeBackground.horizontalPadding, accuracy: 0.01)
        XCTAssertEqual(rect.height, 18 + InlineCodeBackground.verticalPadding * 2, accuracy: 0.01)
    }

    func testPunctuationSideGetsNoPadding() {
        let paddings = InlineCodeBackground.horizontalPaddings(previousIsWhitespace: false,
                                                               nextIsWhitespaceOrEnd: true)
        XCTAssertEqual(paddings.left, 0, accuracy: 0.01)
        XCTAssertEqual(paddings.right, InlineCodeBackground.horizontalPadding, accuracy: 0.01)
        let both = InlineCodeBackground.horizontalPaddings(previousIsWhitespace: true,
                                                           nextIsWhitespaceOrEnd: true)
        XCTAssertEqual(both.left, InlineCodeBackground.horizontalPadding, accuracy: 0.01)
        XCTAssertEqual(both.right, InlineCodeBackground.horizontalPadding, accuracy: 0.01)
    }

    func testTextIsUnchanged() {
        let storage = MarkdownPresentation.attributedString(for: MarkdownParser.parse("行 `code` 行"))
        XCTAssertTrue(storage.string.contains("code"))
        var ranges: [NSRange] = []
        storage.enumerateAttribute(MarkdownPresentation.inlineCodeAttribute,
                                   in: NSRange(location: 0, length: storage.length)) { value, range, _ in
            if value != nil { ranges.append(range) }
        }
        XCTAssertEqual(ranges.count, 1)
        if let range = ranges.first {
            XCTAssertEqual((storage.string as NSString).substring(with: range), "code")
        }
    }
}
