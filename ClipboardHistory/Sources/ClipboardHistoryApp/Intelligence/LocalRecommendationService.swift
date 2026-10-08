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
