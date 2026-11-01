import XCTest
@testable import ClipboardHistoryApp

/// R538（626）：行右键菜单改挂 List 的选区菜单。
/// 旧值：行上的 `.contextMenu` 被 SwiftUI Text/cell 的系统文本菜单盖住（真机 117×165）；
/// 新值：`contextMenu(forSelectionType:)` 在 macOS 13+ 由列表层接管右键。
final class RowContextMenuTests: XCTestCase {
    func testTitlesAndSymbolsUseFavoritePresentation() {
        XCTAssertEqual(RowContextMenu.title(for: .copy, isFavorite: false), "复制")
        XCTAssertEqual(RowContextMenu.systemImage(for: .copy, isFavorite: false), "doc.on.doc")
        XCTAssertEqual(RowContextMenu.title(for: .favorite, isFavorite: false),
                       FavoriteTogglePresentation.helpText(isFavorite: false))
        XCTAssertEqual(RowContextMenu.title(for: .favorite, isFavorite: true),
                       FavoriteTogglePresentation.helpText(isFavorite: true))
        XCTAssertEqual(RowContextMenu.systemImage(for: .favorite, isFavorite: false),
                       FavoriteTogglePresentation.symbolName(isFavorite: false))
        XCTAssertEqual(RowContextMenu.systemImage(for: .favorite, isFavorite: true),
                       FavoriteTogglePresentation.symbolName(isFavorite: true))
    }

    func testPerformRoutesCopyAndFavorite() {
        var copied = 0
        var favorited = 0
        RowContextMenu.perform(.copy, copy: { copied += 1 }, favorite: { favorited += 1 })
        XCTAssertEqual(copied, 1)
        XCTAssertEqual(favorited, 0)
        RowContextMenu.perform(.favorite, copy: { copied += 1 }, favorite: { favorited += 1 })
        XCTAssertEqual(copied, 1)
        XCTAssertEqual(favorited, 1)
    }

    func testHistoryListAttachesSelectionContextMenu() throws {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
        let source = try String(contentsOf: url, encoding: .utf8)
        XCTAssertTrue(source.contains("contextMenu(forSelectionType: HistoryStore.Entry.ID.self)"),
                      "List 没有挂选区右键菜单（macOS 13+）")
        XCTAssertTrue(source.contains("RowContextMenu.perform(.copy"),
                      "菜单没有复制项或没走共用模型")
        XCTAssertTrue(source.contains("RowContextMenu.perform(.favorite"),
                      "菜单没有收藏项或没走共用模型")
        XCTAssertTrue(source.contains("historyStore.perform(.copyAndPromote(entry))"))
        XCTAssertTrue(source.contains("historyStore.perform(.toggleFavorite(entry))"))
    }
}
