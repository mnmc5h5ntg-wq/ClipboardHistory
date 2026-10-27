// R423：搜索无结果态的文案/图标真值表 + 侧栏接线。
// 像素在 UICaptureHarness 的 search-empty-before/after 两帧与产品
// content-no-results / sidebar-no-results 帧里判。
import XCTest
@testable import ClipboardHistoryApp

final class SearchNoResultsPresentationTests: XCTestCase {

    func testIconOnlyBecomesAMagnifierForARealMiss() {
        XCTAssertEqual(icon(search: "abc"), "magnifyingglass")
        XCTAssertEqual(icon(entriesEmpty: true, search: "abc"), "clipboard",
                       "没有历史不是搜不到 ⇒ 仍是剪贴板")
        XCTAssertEqual(icon(isFavorites: true, favoriteCount: 0, search: "abc"), "clipboard",
                       "收藏为空是状态，不是搜不到")
        XCTAssertEqual(icon(search: "   \n"), "clipboard")
        XCTAssertEqual(icon(isFavorites: true, favoriteCount: 2, search: "abc"), "magnifyingglass")
    }

    func testTitleCarriesTheQueryAndKeepsTheStateCases() {
        XCTAssertEqual(title(search: "不存在的词"), "没有找到「不存在的词」")
        XCTAssertEqual(title(search: "  不存在的词 \n"), "没有找到「不存在的词」",
                       "查询词两端的空白不该被画进标题")
        XCTAssertEqual(title(search: ""), "无匹配结果")
        XCTAssertEqual(title(isFavorites: true, favoriteCount: 0, search: "x"), "暂无收藏")
        XCTAssertEqual(title(isFavorites: true, favoriteCount: 2, search: "x"), "没有找到「x」")
        XCTAssertEqual(title(entriesEmpty: true, search: "x"), "暂无剪贴板历史")
        let long = String(repeating: "长", count: 40)
        XCTAssertEqual(title(search: long),
                       "没有找到「" + String(long.prefix(24)) + "…」",
                       "长查询词必须截断到 24 字加省略号，否则侧栏标题会挤出两行")
    }

    func testSidebarUsesThePolicyInsteadOfHardcodedText() throws {
        let sidebar = codeOnly(try productSourceText(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("SearchNoResultsPresentation.iconName("),
                      "侧栏没有用 policy 的图标 ⇒ 搜不到时还画剪贴板")
        XCTAssertTrue(sidebar.contains("SearchNoResultsPresentation.title("),
                      "侧栏没有用 policy 的标题 ⇒ 查询词不会出现在无结果态")
        XCTAssertFalse(sidebar.contains("emptyTitle"),
                       "旧的 emptyTitle 还留着 ⇒ 有两条并行的空态文案路径")
    }

    private func icon(entriesEmpty: Bool = false, isFavorites: Bool = false,
                      favoriteCount: Int = 0, search: String) -> String {
        SearchNoResultsPresentation.iconName(entriesEmpty: entriesEmpty,
                                             isFavoritesFilter: isFavorites,
                                             favoriteCount: favoriteCount,
                                             searchText: search)
    }

    private func title(entriesEmpty: Bool = false, isFavorites: Bool = false,
                       favoriteCount: Int = 0, search: String) -> String {
        SearchNoResultsPresentation.title(entriesEmpty: entriesEmpty,
                                          isFavoritesFilter: isFavorites,
                                          favoriteCount: favoriteCount,
                                          searchText: search)
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
        throw NSError(domain: "SearchNoResultsPresentationTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
