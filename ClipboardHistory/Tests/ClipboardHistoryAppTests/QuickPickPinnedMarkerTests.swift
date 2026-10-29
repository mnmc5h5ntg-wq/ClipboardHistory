import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class QuickPickPinnedMarkerTests: XCTestCase {
    private func entry(isPinned: Bool) -> ClipboardEntry {
        ClipboardEntry(
            content: .text("没有来源的记录"),
            timestamp: Date(timeIntervalSince1970: 1_760_000_000),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            isPinned: isPinned)
    }

    /// R477：置顶状态不再写进标题文本 —— 它由类型符号上的图钉表示。
    /// 这一格钉的是**文本预算**：如果前缀回来，标题会重新被吃掉一截，像素判据的第二句会红。
    func testPinnedStateDoesNotConsumeTitleText() {
        XCTAssertEqual(QuickPickController.rowTitle(for: entry(isPinned: true)),
                       "没有来源的记录")
        XCTAssertEqual(QuickPickController.rowTitle(for: entry(isPinned: false)),
                       "没有来源的记录")
    }
}
