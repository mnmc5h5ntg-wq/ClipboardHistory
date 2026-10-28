import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R446：代码块语言标签的归一化与落位。
///
/// 像素那一半在 `UICaptureTests.testCodeBlocksShowTheirLanguage`：
/// 同一份代码的有语言臂 vs 无语言臂，只量第一行右区。
/// 这里钉的是帧上读不出来的两件事：标签**文本**对不对（像素只数墨点），
/// 以及放不下时**不许画**（帧里的夹具第一行很短，撞不上长行这一支）。
@MainActor
final class CodeLanguageTagTests: XCTestCase {
    func testKnownLanguagesGetShortLabels() {
        XCTAssertEqual(CodeLanguageTag.label(for: "swift"), "SWIFT")
        XCTAssertEqual(CodeLanguageTag.label(for: "Python"), "PYTHON")
        XCTAssertEqual(CodeLanguageTag.label(for: "py"), "PYTHON")
        XCTAssertEqual(CodeLanguageTag.label(for: "sh"), "SHELL")
        XCTAssertEqual(CodeLanguageTag.label(for: "javascript"), "JS")
        XCTAssertEqual(CodeLanguageTag.label(for: "c++"), "C++")
        XCTAssertEqual(CodeLanguageTag.label(for: "objective-c"), "OBJC")
        XCTAssertEqual(CodeLanguageTag.label(for: "json"), "JSON")
    }

    func testUnknownLanguageFallsBackToUppercasedToken() {
        XCTAssertEqual(CodeLanguageTag.label(for: "zig"), "ZIG")
        XCTAssertEqual(CodeLanguageTag.label(for: "  swift  "), "SWIFT")
        XCTAssertEqual(CodeLanguageTag.label(for: "swift filename=ContentView.swift"), "SWIFT")
    }

    func testNeutralAndEmptyLanguagesGetNoTag() {
        XCTAssertNil(CodeLanguageTag.label(for: nil))
        XCTAssertNil(CodeLanguageTag.label(for: ""))
        XCTAssertNil(CodeLanguageTag.label(for: "   "))
        XCTAssertNil(CodeLanguageTag.label(for: "text"))
        XCTAssertNil(CodeLanguageTag.label(for: "plaintext"))
        XCTAssertNil(CodeLanguageTag.label(for: "输出"))
    }

    func testLongAndSymbolOnlyTokensAreBounded() {
        XCTAssertEqual(CodeLanguageTag.label(for: "verylonglanguage"), "VERYLONGLANG")
        XCTAssertNil(CodeLanguageTag.label(for: "🙂🙂"))
    }

    func testTagIsSkippedWhenTheFirstLineWouldCollide() {
        let label = "SWIFT"
        let width = CodeLanguageTag.width(of: label)
        // 短行：正文右沿离容器右沿还很远，放得下。
        XCTAssertTrue(CodeLanguageTag.fits(codeRightEdge: 80,
                                           containerWidth: 600,
                                           label: label))
        // 临界：正文右沿 + 间隙刚好越过标签左沿 ⇒ 不画。
        let tagLeft = 600 - CodeLanguageTag.rightInset - width
        XCTAssertFalse(CodeLanguageTag.fits(codeRightEdge: tagLeft - CodeLanguageTag.minimumGap + 0.5,
                                            containerWidth: 600,
                                            label: label))
        XCTAssertTrue(CodeLanguageTag.fits(codeRightEdge: tagLeft - CodeLanguageTag.minimumGap - 0.5,
                                           containerWidth: 600,
                                           label: label))
    }

    func testTagSitsAtTheRightInsetAndIsCenteredOnTheLine() {
        let label = "SWIFT"
        let width = CodeLanguageTag.width(of: label)
        XCTAssertEqual(CodeLanguageTag.originX(containerWidth: 600, label: label),
                       600 - CodeLanguageTag.rightInset - width, accuracy: 0.01)
        let height = ("SWIFT" as NSString).size(withAttributes: [.font: CodeLanguageTag.font]).height
        XCTAssertEqual(CodeLanguageTag.originY(lineTop: 100, lineHeight: 20, tagHeight: height),
                       100 + (20 - height) / 2, accuracy: 0.01)
        XCTAssertEqual(CodeLanguageTag.originY(lineTop: 100, lineHeight: 8, tagHeight: height),
                       100, accuracy: 0.01)
    }
}
