import Foundation

struct LocalRecommendationService {
    var adapter: ClipboardEntryIntelligenceAdapter
    var engine: RuleBasedRecommendationEngine

    init(
        adapter: ClipboardEntryIntelligenceAdapter = ClipboardEntryIntelligenceAdapter(),
        engine: RuleBasedRecommendationEngine = RuleBasedRecommendationEngine()
    ) {
        self.adapter = adapter
        self.engine = engine
    }

    /// 只接受字符串快照：可以在后台线程调用，不需要把带 NSImage 的条目送过 actor 边界。
    func recommend(
        snapshots: [ClipboardEntryRawSnapshot],
        selectedEntryID: UUID? = nil,
        feedback: [RecommendationFeedback] = [],
        frontmostApplication: RunningApplicationContext? = nil,
        limit: Int = 5,
        capturedAt: Date = Date(),
        enablePrivacyFilter: Bool = true
    ) -> RecommendationResult {
        let summaries = adapter.summaries(for: snapshots)
        var context = ContextSnapshot.minimal(
            recentEntries: summaries,
            selectedEntryID: selectedEntryID,
            capturedAt: capturedAt
        )
        context.frontmostApplication = frontmostApplication

        return engine.recommend(
            entries: summaries,
            intelligenceByEntryID: adapter.intelligenceByEntryID(for: snapshots, analyzedAt: capturedAt),
            feedback: feedback,
            request: RecommendationRequest(
                context: context,
                limit: limit,
                allowsAIReRanking: false,
                privacyScope: .localOnly,
                enablePrivacyFilter: enablePrivacyFilter
            )
        )
    }

    func recommend(
        entries: [ClipboardEntry],
        selectedEntryID: UUID? = nil,
        feedback: [RecommendationFeedback] = [],
        frontmostApplication: RunningApplicationContext? = nil,
        limit: Int = 5,
        capturedAt: Date = Date(),
        enablePrivacyFilter: Bool = true
    ) -> RecommendationResult {
        let summaries = adapter.summaries(for: entries)
        var context = ContextSnapshot.minimal(
            recentEntries: summaries,
            selectedEntryID: selectedEntryID,
            capturedAt: capturedAt
        )
        context.frontmostApplication = frontmostApplication

        return engine.recommend(
            entries: summaries,
            intelligenceByEntryID: adapter.intelligenceByEntryID(for: entries, analyzedAt: capturedAt),
            feedback: feedback,
            request: RecommendationRequest(
                context: context,
                limit: limit,
                allowsAIReRanking: false,
                privacyScope: .localOnly,
                enablePrivacyFilter: enablePrivacyFilter
            )
        )
    }
}
