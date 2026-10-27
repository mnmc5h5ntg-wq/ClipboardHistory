// R422：列表空态插画的接线 —— 只有"还没有记录"那一档换成叠卡插画；
// 无匹配结果（有搜索词/有记录）保留字形。像素在 UICaptureHarness 的
// empty-state-glyph / empty-state-illustration 两帧 + 产品 frame（content-empty）。
import XCTest
@testable import ClipboardHistoryApp

final class EmptyStateIllustrationTests: XCTestCase {

    func testIllustrationIsWiredOnlyForTheNoHistoryEmptyState() throws {
        let empty = codeOnly(try productSourceText(named: "Views/EmptyStateView.swift"))
        XCTAssertTrue(empty.contains("if illustration"),
                      "EmptyStateView 没有 illustration 分支 ⇒ 插画档是死的")
        XCTAssertTrue(empty.contains("EmptyStateIllustration()"),
                      "插画档没有挂 EmptyStateIllustration")
        let sidebar = codeOnly(try productSourceText(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("illustration: historyStore.entries.isEmpty"),
                      "侧栏空态没有只在「一条记录都没有」时传 illustration ⇒ 无匹配/收藏空态也会换插画")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "EmptyStateIllustrationTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
