import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R506：状态菜单（macOS 13+ SwiftUI `MenuBarExtra`）会把菜单项标签拍平成单个文本 ——
/// 推荐行原来用 HStack 把理由放在右侧第二列，系统只留下第一列，理由整段消失。
/// 这里钉住「理由并进同一个 Text」这件事的文本侧与接线侧。
final class MenuRecommendationPresentationTests: XCTestCase {

    func testReasonSuffixKeepsTheReasonAndItsColumnGap() {
        XCTAssertEqual(MenuRecommendationPresentation.reasonSuffix("文本 · 常用文本"),
                       "  文本 · 常用文本")
        XCTAssertEqual(MenuRecommendationPresentation.reasonSuffix(" 文本 "), "  文本")
        XCTAssertEqual(MenuRecommendationPresentation.reasonSuffix("   "), "")
        XCTAssertEqual(MenuRecommendationPresentation.reasonSuffix(""), "")
    }

    func testTheRecommendationRowJoinsTheReasonIntoOneText() throws {
        let source = codeOnly(try productSource(named: "Views/MenuBarRecommendationsView.swift"))
        XCTAssertTrue(source.contains("MenuRecommendationPresentation.reasonSuffix(reasonText)"),
                      "推荐行没有把理由并进同一个 Text ⇒ 真实 MenuBarExtra 会把它拍掉")
        XCTAssertFalse(source.contains("Spacer(minLength: 12)"),
                       "推荐行仍用 HStack 两列 ⇒ 真实菜单只留下第一列，理由不可见")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "MenuRecommendationPresentationTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
