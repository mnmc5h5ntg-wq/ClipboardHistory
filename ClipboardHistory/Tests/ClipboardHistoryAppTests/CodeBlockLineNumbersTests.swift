import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R441：代码块左侧外边距行号。
///
/// 行数/字号/右对齐是纯函数；"代码块哪些字符算行"是属性串上的事实。
/// 像素那一半在 `UICaptureTests.testCodeBlocksShowLineNumbers` ——
/// 它读 `detail-code` 帧左边距里的行号带数（3）并确认正文左沿没被挪动（仍在 20pt）。
@MainActor
final class CodeBlockLineNumbersTests: XCTestCase {
    func testLineCountAndDigits() {
        XCTAssertEqual(CodeBlockLineNumbers.lineCount(in: ""), 0)
        XCTAssertEqual(CodeBlockLineNumbers.lineCount(in: "a"), 1)
        XCTAssertEqual(CodeBlockLineNumbers.lineCount(in: "a\nb\nc"), 3)
        XCTAssertEqual(CodeBlockLineNumbers.digitCount(forLineCount: 3), 1)
        XCTAssertEqual(CodeBlockLineNumbers.digitCount(forLineCount: 10), 2)
        XCTAssertEqual(CodeBlockLineNumbers.digitCount(forLineCount: 100), 3)
        XCTAssertEqual(CodeBlockLineNumbers.digitCount(forLineCount: 0), 1)
    }

    func testFontShrinksOnlyAtThreeDigits() {
        let two = CodeBlockLineNumbers.font(forLineCount: 99)
        let three = CodeBlockLineNumbers.font(forLineCount: 100)
        XCTAssertEqual(two.pointSize, CodeBlockLineNumbers.fontSize, accuracy: 0.01)
        XCTAssertEqual(three.pointSize, CodeBlockLineNumbers.compactFontSize, accuracy: 0.01)
        XCTAssertTrue(two.isFixedPitch && three.isFixedPitch, "行号字体不是等宽")
        let digits = ("100" as NSString).size(withAttributes: [.font: three]).width
        XCTAssertLessThanOrEqual(digits, 20 - CodeBlockLineNumbers.marginInset,
                                 "三位数在 20pt 外边距里放不下 ⇒ 第一位会被裁掉")
    }

    func testNumbersAreRightAlignedToTheMargin() {
        let font = CodeBlockLineNumbers.font(forLineCount: 10)
        let one = CodeBlockLineNumbers.numberOrigin(containerOriginX: 20, line: 1, font: font,
                                                    lineTop: 0, lineHeight: 20, numberHeight: 12)
        let ten = CodeBlockLineNumbers.numberOrigin(containerOriginX: 20, line: 10, font: font,
                                                    lineTop: 0, lineHeight: 20, numberHeight: 12)
        let oneWidth = ("1" as NSString).size(withAttributes: [.font: font]).width
        let tenWidth = ("10" as NSString).size(withAttributes: [.font: font]).width
        XCTAssertEqual(one.x + oneWidth, 20 - CodeBlockLineNumbers.marginInset, accuracy: 0.01)
        XCTAssertEqual(ten.x + tenWidth, 20 - CodeBlockLineNumbers.marginInset, accuracy: 0.01)
        XCTAssertLessThan(one.x + oneWidth, 20, "行号右沿压到正文容器原点 ⇒ 会盖住正文")
        XCTAssertGreaterThan(one.y, 0)
    }

    /// 产品入口：代码块**不缩进**（正文左沿不动），只带行数属性；标题不缩进也不带属性。
    func testCodeBlockCarriesLineCountWithoutMovingTheText() {
        let source = """
        # 代码

        ```swift
        let a = 1
        let b = 2
        let c = a + b
        ```
        """
        let attributed = MarkdownPresentation.attributedString(for: MarkdownParser.parse(source))
        let text = attributed.string as NSString
        let codeRange = text.range(of: "let a = 1")
        guard codeRange.location != NSNotFound else {
            return XCTFail("属性串里找不到代码正文 ⇒ 这条判据没有对象")
        }
        let style = attributed.attribute(.paragraphStyle, at: codeRange.location,
                                         effectiveRange: nil) as? NSParagraphStyle
        XCTAssertEqual(style?.firstLineHeadIndent ?? 0, 0, accuracy: 0.01,
                       "代码块正文被缩进了 ⇒ 行号槽不该动正文")
        XCTAssertEqual(style?.headIndent ?? 0, 0, accuracy: 0.01)
        XCTAssertEqual(attributed.attribute(MarkdownPresentation.codeBlockLineCountAttribute,
                                            at: codeRange.location, effectiveRange: nil) as? Int, 3)

        let headingRange = text.range(of: "代码")
        let headingStyle = attributed.attribute(.paragraphStyle, at: headingRange.location,
                                                effectiveRange: nil) as? NSParagraphStyle
        XCTAssertEqual(headingStyle?.firstLineHeadIndent ?? 0, 0, accuracy: 0.01)
        XCTAssertNil(attributed.attribute(MarkdownPresentation.codeBlockLineCountAttribute,
                                          at: headingRange.location, effectiveRange: nil))
    }
}
