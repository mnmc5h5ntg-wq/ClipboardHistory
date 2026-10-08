import XCTest
@testable import ClipboardHistoryApp

/// 审计新发现（本轮实测定位）：推荐分数用 `features.values.reduce(0, +)` 累加，
/// 而 `features` 是 Dictionary —— 迭代顺序按进程随机播种，加上候选之间存在
/// 1 ULP 级别的分数差，导致同一份历史在不同启动之间排出不同推荐次序。
/// 表现为 `HistoryStoreTests` 的排序断言随机失败（实测 5 次挂 3 次）。
@MainActor
final class RecommendationDeterminismTests: XCTestCase {
    private func entry(
        _ text: String,
        ageSeconds: TimeInterval,
        id: UUID? = nil
    ) -> ClipboardEntry {
        ClipboardEntry(
            id: id ?? UUID(),
            content: .text(text),
            timestamp: Date().addingTimeInterval(-ageSeconds),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
    }

    private func recommend(_ entries: [ClipboardEntry], now: Date) -> RecommendationResult {
        LocalRecommendationService(
            engine: RuleBasedRecommendationEngine(now: now, weights: .default)
        ).recommend(
            entries: entries,
            feedback: [],
            frontmostApplication: RunningApplicationContext(
                localizedName: "Safari", bundleIdentifier: "com.apple.Safari", processIdentifier: nil
            ),
            limit: 5,
            capturedAt: now,
            enablePrivacyFilter: true
        )
    }

    func testIdenticalInputsProduceIdenticalOrderAndScores() {
        // 三条同内容类型、同来源、时间递增的候选：次序与分数必须完全可重复。
        let entries = (0..<3).map { entry("same-shape-\($0)", ageSeconds: 60) }
        let now = Date()
        let first = recommend(entries, now: now)
        for _ in 0..<20 {
            let again = recommend(entries, now: now)
            XCTAssertEqual(
                again.candidates.map(\.entryID), first.candidates.map(\.entryID),
                "同一输入在同一进程内多次调用必须给出同一次序"
            )
            XCTAssertEqual(
                again.candidates.map { $0.score.value },
                first.candidates.map { $0.score.value },
                "分数必须是确定顺序求和的结果，不能依赖字典迭代顺序"
            )
        }
    }

    func testTiedCandidatesFallBackToNewestFirst() {
        // 三条候选都落在同一个新鲜度区间（<60s）⇒ 分数完全相等，
        // 次序必须由显式的 copiedAt 次级键决定，而不是 sorted 的稳定性运气。
        // 固定 UUID，且让"按 uuid 排序"与"按时间排序"给出相反次序 ——
        // 这样一旦去掉 copiedAt 次级键、退化成 uuid 兜底，本用例必然变红。
        let entries = [
            entry("tie-oldest", ageSeconds: 55, id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!),
            entry("tie-middle", ageSeconds: 45, id: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!),
            entry("tie-newest", ageSeconds: 5, id: UUID(uuidString: "00000000-0000-0000-0000-000000000003")!),
        ]
        let result = recommend(entries, now: Date())
        let values = Set(result.candidates.map { $0.score.value })
        XCTAssertEqual(values.count, 1, "夹具应产生完全同分：\(result.candidates.map(\.score.value))")
        XCTAssertEqual(
            result.candidates.map { candidate in entries.first { $0.id == candidate.entryID }?.shortPreview },
            ["tie-newest", "tie-middle", "tie-oldest"],
            "同分且同理由时必须按复制时间由新到旧排序"
        )
    }

    func testScoreSummationDoesNotDependOnDictionaryOrder() {
        // 极端量级让"加法顺序"产生可见差异（1e16 ± 1 在 Double 里会被吃掉）。
        let features: [RecommendationFeature: Double] = [
            .recency: 1e16,
            .favorite: 1,
            .appAffinity: -1e16,
            .contentTypeAffinity: 1e-16,
            .semanticSimilarity: 1,
        ]
        var inOrder = 0.0
        for feature in RecommendationFeature.allCases { inOrder += (features[feature] ?? 0) }
        XCTAssertEqual(
            RuleBasedRecommendationEngine.summedScore(from: features),
            inOrder,
            accuracy: 0,
            "求和必须走 allCases 固定顺序"
        )
        // 说明：这条守卫是概率性的 —— 字典迭代顺序按进程播种，若某个进程里它恰好
        // 等于 allCases 顺序，两种实现会得到相同结果。因此主守卫放在下面那条
        // 确定性的"同分候选按时间排序"用例上（变异检查已证实它能抓住退化）。
    }

    func testEqualFeatureSetsProduceBitwiseEqualScores() {
        // 两个仅在 ID 上不同的候选，特征集合相同 ⇒ 分数必须逐位相等（不应有 ULP 抖动）。
        let a = entry("alpha", ageSeconds: 120)
        let b = entry("alpha", ageSeconds: 120)
        let result = recommend([a, b], now: Date())
        let values = result.candidates.map { $0.score.value }
        XCTAssertEqual(Set(values).count, 1, "同特征候选的分数应完全相等：\(values)")
    }
}
