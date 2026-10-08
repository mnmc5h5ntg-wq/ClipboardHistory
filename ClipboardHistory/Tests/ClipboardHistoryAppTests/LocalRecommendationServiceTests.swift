import XCTest
@testable import ClipboardHistoryApp

final class LocalRecommendationServiceTests: XCTestCase {
    func testServiceProducesLocalRecommendationsFromClipboardEntries() {
        let now = Date(timeIntervalSince1970: 10_000)
        let github = ClipboardEntry(
            id: UUID(),
            content: .text("https://github.com/mnmc5h5ntg-wq/ClipboardHistory"),
            timestamp: now.addingTimeInterval(-600),
            thumbnail: nil,
            sourceURL: nil,
            isFavorite: false,
            sourceUTIs: ["public.utf8-plain-text"]
        )
        let plain = ClipboardEntry(
            id: UUID(),
            content: .text("plain note"),
            timestamp: now.addingTimeInterval(-600),
            thumbnail: nil,
            sourceURL: nil,
            isFavorite: false,
            sourceUTIs: ["public.utf8-plain-text"]
        )

        let result = LocalRecommendationService(
            engine: RuleBasedRecommendationEngine(now: now)
        ).recommend(
            entries: [plain, github],
            frontmostApplication: RunningApplicationContext(
                localizedName: "Safari",
                bundleIdentifier: "com.apple.Safari",
                processIdentifier: nil
            ),
            limit: 2,
            capturedAt: now
        )

        XCTAssertFalse(result.usedAI)
        XCTAssertEqual(result.candidates.first?.entryID, github.id)
        XCTAssertEqual(result.explanation, "使用本地规则排序，未调用 AI 模型。")
    }

    func testServiceLimitsCandidateCount() {
        let now = Date(timeIntervalSince1970: 10_000)
        let entries = (0..<4).map { index in
            ClipboardEntry(
                id: UUID(),
                content: .text("item \(index)"),
                timestamp: now.addingTimeInterval(Double(-index)),
                thumbnail: nil,
                sourceURL: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            )
        }

        let result = LocalRecommendationService(
            engine: RuleBasedRecommendationEngine(now: now)
        ).recommend(entries: entries, limit: 2, capturedAt: now)

        XCTAssertEqual(result.candidates.count, 2)
    }
}
