import XCTest
@testable import ClipboardHistoryApp

/// M4×边界：推荐引擎在"空 / 极小 / 极大 / 病态输入"下的行为。
///
/// 这些不是凑数：预测现在是**每次复制都会跑**（事件驱动，见 R-11），
/// 所以空历史、limit=0、未来时间戳、权重全 0 都是线上会出现的状态；
/// 其中任何一个抛异常或返回垃圾，都会直接打在用户界面上。
final class RecommendationBoundaryTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 1_700_000_000)

    private func summary(
        _ preview: String,
        id: UUID = UUID(),
        isFavorite: Bool = false,
        age: TimeInterval = 60
    ) -> ClipboardEntrySummary {
        ClipboardEntrySummary(
            id: id,
            contentKind: "text",
            preview: preview,
            isFavorite: isFavorite,
            copiedAt: now.addingTimeInterval(-age),
            sourceUTIs: []
        )
    }

    private func request(limit: Int, privacyFilter: Bool = true) -> RecommendationRequest {
        RecommendationRequest(
            context: ContextSnapshot.minimal(recentEntries: [], capturedAt: now),
            limit: limit,
            allowsAIReRanking: false,
            privacyScope: .localOnly,
            enablePrivacyFilter: privacyFilter
        )
    }

    private func engine(weights: RecommendationWeights = .default) -> RuleBasedRecommendationEngine {
        RuleBasedRecommendationEngine(now: now, weights: weights)
    }

    func testEmptyHistoryProducesNoCandidates() {
        let result = engine().recommend(entries: [], request: request(limit: 3))
        XCTAssertTrue(result.candidates.isEmpty, "空历史必须给出空结果，而不是崩或造出候选")
        XCTAssertFalse(result.usedAI)
    }

    func testSingleEntryHistoryStillProducesOneCandidate() {
        let only = summary("唯一的一条")
        let result = engine().recommend(entries: [only], request: request(limit: 3))
        XCTAssertEqual(result.candidates.map(\.entryID), [only.id], "只有一条时也该能推荐它（Top-N 不能把 N=1 当边界 bug）")
    }

    func testZeroAndNegativeLimitsAreClamped() {
        let entries = (0..<5).map { summary("条目 \($0)", age: Double($0) * 10) }
        for limit in [0, -1, -100] {
            let result = engine().recommend(entries: entries, request: request(limit: limit))
            XCTAssertTrue(result.candidates.isEmpty, "limit=\(limit) 不该返回任何候选")
        }
    }

    func testHugeHistoryReturnsAtMostLimitAndTerminates() {
        let entries = (0..<500).map { summary("大量条目 \($0)", age: Double($0)) }
        let start = Date()
        let result = engine().recommend(entries: entries, request: request(limit: 3))
        let elapsed = Date().timeIntervalSince(start)
        XCTAssertEqual(result.candidates.count, 3)
        XCTAssertLessThan(elapsed, 0.5, "500 条候选的一次排序必须远小于一次交互的等待预算（实测应是个位数毫秒）")
    }

    func testZeroWeightsDoNotCrashAndKeepDeterministicOrder() {
        let zero = RecommendationWeights(
            recency: 0, favorite: 0, appAffinity: 0, contentTypeAffinity: 0,
            finderDirectoryAffinity: 0, finderSelectionAffinity: 0, semanticSimilarity: 0,
            reuseFrequency: 0, negativeFeedback: 0
        )
        let older = summary("较旧", age: 5_000)
        let newer = summary("较新", age: 10)
        let first = engine(weights: zero).recommend(entries: [older, newer], request: request(limit: 2))
        let second = engine(weights: zero).recommend(entries: [older, newer], request: request(limit: 2))
        XCTAssertEqual(first.candidates.map(\.entryID), second.candidates.map(\.entryID),
                       "权重全 0 时顺序也必须稳定（同分要靠次级键，不能靠字典序）")
        XCTAssertEqual(first.candidates.map(\.entryID), [newer.id, older.id],
                       "全 0 分时应退化为「最新优先」的次级排序，而不是随机顺序")
    }

    func testFutureTimestampIsRankedWithoutCrashing() {
        // 系统时间被调过之后，库里会留下"来自未来"的时间戳（与 R-20 同源的场景）。
        let future = summary("未来时间戳", age: -86_400)
        let past = summary("过去时间戳", age: 86_400)
        let result = engine().recommend(entries: [past, future], request: request(limit: 2))
        XCTAssertEqual(result.candidates.count, 2)
        XCTAssertEqual(result.candidates.first?.entryID, future.id, "未来时间戳按更新处理即可，不该被丢弃或打乱")
    }

    func testDuplicateEntryIDsDoNotProduceDuplicateCandidates() {
        let shared = UUID()
        let a = summary("同 id 第一次", id: shared, age: 10)
        let b = summary("同 id 第二次", id: shared, age: 20)
        let result = engine().recommend(entries: [a, b], request: request(limit: 3))
        XCTAssertEqual(Set(result.candidates.map(\.entryID)).count, result.candidates.count,
                       "候选列表里同一个 entryID 出现两次会让界面出现重复行")
    }

    func testPrivacyFilterSettingChangesWhetherSensitiveInputIsOffered() {
        let secret = summary("ghp_" + String(repeating: "A", count: 36), age: 10)   // 与产品规则一致：ghp_ 后需 ≥36 位
        let plain = summary("普通文本内容", age: 30)
        let filtered = engine().recommend(entries: [secret, plain], request: request(limit: 3))
        let unfiltered = engine().recommend(entries: [secret, plain], request: request(limit: 3, privacyFilter: false))

        XCTAssertFalse(filtered.candidates.contains { $0.entryID == secret.id },
                       "开启推荐过滤时，疑似令牌不得出现在候选里")
        XCTAssertTrue(unfiltered.candidates.contains { $0.entryID == secret.id },
                       "关掉开关就该如实给出结果，否则开关是假的")
    }
}
