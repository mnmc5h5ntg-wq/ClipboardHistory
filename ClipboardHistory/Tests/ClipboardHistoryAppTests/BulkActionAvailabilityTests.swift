import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R513：多选操作栏的动词只在选区里至少有一条适用时才是亮的。
final class BulkActionAvailabilityTests: XCTestCase {
    private func entry(favorite: Bool = false, pinned: Bool = false) -> ClipboardEntry {
        ClipboardEntry(content: .text("x"), timestamp: Date(), thumbnail: nil, sourceURL: nil,
                       isFavorite: favorite, sourceUTIs: [], isPinned: pinned)
    }

    func testAvailabilityFollowsTheSelection() {
        let normal = entry()
        let favorite = entry(favorite: true)
        let pinned = entry(pinned: true)
        let mixed = BulkActionAvailability(selectedEntries: [normal, favorite, pinned])
        XCTAssertTrue(mixed.canFavorite)
        XCTAssertTrue(mixed.canUnfavorite)
        XCTAssertTrue(mixed.canPin)
        XCTAssertTrue(mixed.canUnpin)

        let onlyNormal = BulkActionAvailability(selectedEntries: [normal, entry()])
        XCTAssertTrue(onlyNormal.canFavorite, "普通条目还能被收藏")
        XCTAssertFalse(onlyNormal.canUnfavorite, "没有收藏项时「取消收藏」是空操作")
        XCTAssertTrue(onlyNormal.canPin, "普通条目还能被固定")
        XCTAssertFalse(onlyNormal.canUnpin, "没有固定项时「取消固定」是空操作")

        let onlyPinnedFavorite = BulkActionAvailability(
            selectedEntries: [entry(favorite: true, pinned: true)])
        XCTAssertFalse(onlyPinnedFavorite.canFavorite)
        XCTAssertTrue(onlyPinnedFavorite.canUnfavorite)
        XCTAssertFalse(onlyPinnedFavorite.canPin)
        XCTAssertTrue(onlyPinnedFavorite.canUnpin)
    }

    /// 结构轴：批量栏的四个动词必须真的消费这份可用性（否则策略绿、界面照旧全亮）。
    func testBulkBarConsumesTheAvailability() throws {
        let source = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        for verb in ["canFavorite", "canPin", "canUnpin", "canUnfavorite"] {
            XCTAssertTrue(source.contains(".disabled(!availability.\(verb))"),
                          "批量栏没有按 \(verb) 禁用")
            XCTAssertTrue(source.contains(".opacity(availability.\(verb) ? 1 : 0.35)"),
                          "批量栏没有按 \(verb) 调暗")
        }
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
        throw NSError(domain: "BulkActionAvailabilityTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
