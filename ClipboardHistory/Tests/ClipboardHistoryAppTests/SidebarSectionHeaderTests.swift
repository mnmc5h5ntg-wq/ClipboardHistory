// R429：侧栏固定条目分区头 —— 有固定条目才多一行「已固定」，选中揭示的行号要把它算进去。
// 像素正/负/标记三帧在 UICaptureHarness 的 sidebar-pinned-section{,-flat,-marker}。
import XCTest
@testable import ClipboardHistoryApp

final class SidebarSectionHeaderTests: XCTestCase {

    func testPlanIsIdentityWithoutPinnedEntries() {
        let plan = SidebarSectionPlan(pinnedCount: 0)
        XCTAssertFalse(plan.hasPinnedHeader)
        XCTAssertEqual(plan.displayRowIndex(forFilteredIndex: 0), 0)
        XCTAssertEqual(plan.displayRowIndex(forFilteredIndex: 4), 4)
    }

    func testPlanAddsExactlyTheHeaderRowWhenPinnedExists() {
        let plan = SidebarSectionPlan(pinnedCount: 2)
        XCTAssertTrue(plan.hasPinnedHeader)
        XCTAssertEqual(plan.displayRowIndex(forFilteredIndex: 0), 1, "固定条目前面是分区头")
        XCTAssertEqual(plan.displayRowIndex(forFilteredIndex: 1), 2)
        XCTAssertEqual(plan.displayRowIndex(forFilteredIndex: 2), 3, "普通条目也在这行分区头之后")
    }

    func testHeaderTitleIsTheOnlySectionLabel() {
        XCTAssertEqual(SidebarSectionPlan.pinnedTitle, "已固定")
    }

    func testSidebarWiresTheHeaderAndTheRevealRowIndex() throws {
        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("if sectionHeadersForDrawing, !pinnedEntries.isEmpty"),
                      "侧栏没有「有固定条目才出现分区头」的前提")
        XCTAssertTrue(sidebar.contains("SidebarSectionHeader(title: SidebarSectionPlan.pinnedTitle)"),
                      "侧栏没有挂「已固定」分区头")
        XCTAssertTrue(sidebar.contains("sectionPlanForDrawing.displayRowIndex(forFilteredIndex:"),
                      "选中揭示的行号没有把分区头算进去 ⇒ 固定条目会揭示上一行")

        let header = codeOnly(try productSource(named: "Views/SidebarSectionHeader.swift"))
        XCTAssertTrue(header.contains("Text(title)"),
                      "分区头没有用传入的标题（带扫找不到「已固定」）")
        XCTAssertTrue(header.contains("Color(nsColor: .secondaryLabelColor)"),
                      "分区头没有用动态系统色（vibrant 侧栏里亮档会看不见）")
        XCTAssertTrue(header.contains("accessibilityAddTraits(.isHeader)"),
                      "分区头没有 header 无障碍语义")
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
        throw NSError(domain: "SidebarSectionHeaderTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
