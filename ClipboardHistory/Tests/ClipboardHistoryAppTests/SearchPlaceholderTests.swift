import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R508：主侧栏与快速选择浮层是同一个搜索动作，占位文案必须只有一句。
final class SearchPlaceholderTests: XCTestCase {

    func testBothSearchEntriesShareOnePlaceholder() throws {
        XCTAssertEqual(SearchPlaceholder.text, "搜索历史…")
        let main = codeOnly(try productSource(named: "Views/SearchField.swift"))
        let quick = codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        XCTAssertTrue(main.contains("SearchPlaceholder.text"),
                      "主侧栏搜索框没有走共享占位常量")
        XCTAssertTrue(quick.contains("placeholderString = SearchPlaceholder.text"),
                      "快速选择浮层没有走共享占位常量 ⇒ 两个入口又会各写一句")
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
        throw NSError(domain: "SearchPlaceholderTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
