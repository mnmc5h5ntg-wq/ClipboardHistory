// R420：侧栏搜索结果计数的数字滚动 —— 源接线。
// 像素在 UICaptureHarness（sidebar-history / sidebar-favorites 的同带读数）；
// 过程在 MotionFilmstripTests 的 sidebar-count-change 场景里判。
import XCTest
@testable import ClipboardHistoryApp

final class SidebarCountTransitionTests: XCTestCase {

    func testCountUsesTheNumericTransitionAndItsOwnAnimation() throws {
        let source = codeOnly(try productSourceText(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(source.contains("countTextLabel"),
                      "header 没有走 countTextLabel ⇒ 计数还是硬换")
        XCTAssertTrue(source.contains(".contentTransition(.numericText())"),
                      "没有数字滚动 ⇒ 15→1 会整句跳")
        XCTAssertTrue(source.contains(".animation(MotionCatalog.animation(for: .contentFade), value: countText)"),
                      "数字滚动没有事务 ⇒ contentTransition 不会演")
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
        throw NSError(domain: "SidebarCountTransitionTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
