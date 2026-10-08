import XCTest
@testable import ClipboardHistoryApp

final class RuleBasedRecommendationEngineTests: XCTestCase {
    func testRecentEntriesRankAboveOldEntries() {
        let now = Date(timeIntervalSince1970: 10_000)
        let recent = summary(id: UUID(), preview: "recent", copiedAt: now.addingTimeInterval(-30))
        let old = summary(id: UUID(), preview: "old", copiedAt: now.addingTimeInterval(-8_000))

        let result = RuleBasedRecommendationEngine(now: now).recommend(
            entries: [old, recent],
            request: request(now: now, limit: 2)
        )

        XCTAssertEqual(result.candidates.map(\.entryID), [recent.id, old.id])
        XCTAssertFalse(result.usedAI)
    }

    func testFavoritesReceiveBoost() {
        let now = Date(timeIntervalSince1970: 10_000)
        let favorite = summary(id: UUID(), preview: "favorite", isFavorite: true, copiedAt: now.addingTimeInterval(-400))
        let ordinary = summary(id: UUID(), preview: "ordinary", copiedAt: now.addingTimeInterval(-400))

        let result = RuleBasedRecommendationEngine(now: now).recommend(
            entries: [ordinary, favorite],
            request: request(now: now, limit: 2)
        )

        XCTAssertEqual(result.candidates.first?.entryID, favorite.id)
        XCTAssertEqual(result.candidates.first?.reason, "收藏内容且与当前排序规则匹配。")
    }

    func testFeedbackBoostsPreviouslyAcceptedEntries() {
        let now = Date(timeIntervalSince1970: 10_000)
        let boosted = summary(id: UUID(), preview: "boosted", copiedAt: now.addingTimeInterval(-2_000))
        let newer = summary(id: UUID(), preview: "newer", copiedAt: now.addingTimeInterval(-1_000))
        let feedback = (0..<3).map { _ in
            RecommendationFeedback(
                entryID: boosted.id,
                kind: .accepted,
                context: ContextSnapshot.minimal(recentEntries: [], capturedAt: now),
                createdAt: now
            )
        }

        let result = RuleBasedRecommendationEngine(now: now).recommend(
            entries: [newer, boosted],
            feedback: feedback,
            request: request(now: now, limit: 2)
        )

        XCTAssertEqual(result.candidates.first?.entryID, boosted.id)
        XCTAssertGreaterThan(result.candidates.first?.score.features[.reuseFrequency] ?? 0, 0)
    }

    func testSecretLikeEntriesAreDownranked() {
        let now = Date(timeIntervalSince1970: 10_000)
        let secret = summary(id: UUID(), preview: "sk-...", copiedAt: now.addingTimeInterval(-30))
        let safe = summary(id: UUID(), preview: "safe", copiedAt: now.addingTimeInterval(-30))
        let intelligence = EntryIntelligence(
            entryID: secret.id,
            tags: [.apiKeyCandidate],
            sensitivity: .secret
        )

        let result = RuleBasedRecommendationEngine(now: now).recommend(
            entries: [secret, safe],
            intelligenceByEntryID: [secret.id: intelligence],
            request: request(now: now, limit: 2)
        )

        XCTAssertEqual(result.candidates.first?.entryID, safe.id)
        XCTAssertLessThan(
            result.candidates.first(where: { $0.entryID == secret.id })?.score.value ?? 1,
            result.candidates.first(where: { $0.entryID == safe.id })?.score.value ?? 0
        )
    }

    func testBrowserContextBoostsURLLikeEntries() {
        let now = Date(timeIntervalSince1970: 10_000)
        let urlEntry = summary(
            id: UUID(),
            contentKind: "url",
            preview: "https://github.com/mnmc5h5ntg-wq/ClipboardHistory",
            copiedAt: now.addingTimeInterval(-500)
        )
        let textEntry = summary(id: UUID(), contentKind: "text", preview: "plain", copiedAt: now.addingTimeInterval(-500))
        var context = ContextSnapshot.minimal(recentEntries: [urlEntry, textEntry], capturedAt: now)
        context.frontmostApplication = RunningApplicationContext(
            localizedName: "Safari",
            bundleIdentifier: "com.apple.Safari",
            processIdentifier: nil
        )

        let result = RuleBasedRecommendationEngine(now: now).recommend(
            entries: [textEntry, urlEntry],
            request: RecommendationRequest(
                context: context,
                limit: 2,
                allowsAIReRanking: false,
                privacyScope: .localOnly
            )
        )

        XCTAssertEqual(result.candidates.first?.entryID, urlEntry.id)
        XCTAssertGreaterThan(result.candidates.first?.score.features[.contentTypeAffinity] ?? 0, 0)
    }

    private func summary(
        id: UUID,
        contentKind: String = "text",
        preview: String,
        isFavorite: Bool = false,
        copiedAt: Date
    ) -> ClipboardEntrySummary {
        ClipboardEntrySummary(
            id: id,
            contentKind: contentKind,
            preview: preview,
            isFavorite: isFavorite,
            copiedAt: copiedAt,
            sourceUTIs: []
        )
    }

    private func request(now: Date, limit: Int) -> RecommendationRequest {
        RecommendationRequest(
            context: ContextSnapshot.minimal(recentEntries: [], capturedAt: now),
            limit: limit,
            allowsAIReRanking: false,
            privacyScope: .localOnly
        )
    }
}
