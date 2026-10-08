import XCTest
@testable import ClipboardHistoryApp

/// 预测刷新的驱动方式（R-11/R-21）与"显露偏好窗口"的语义。
@MainActor
final class PredictionSchedulingTests: XCTestCase {
    private func intake(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text), thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
        )
    }

    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    private func waitUntil(
        _ description: String = "条件",
        timeout: TimeInterval = 5.0,
        condition: @MainActor () -> Bool
    ) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立")
    }

    func testNewCopyTriggersPredictionRefreshWithoutAnyTimer() {
        let store = makeStore()
        store.add(intake("第一条"), timestamp: Date())
        waitUntil { store.predictionSuggestionEntries.count == 1 }

        store.add(intake("第二条"), timestamp: Date())
        waitUntil { store.predictionSuggestionEntries.count == 2 }
    }

    /// 只有"推荐确实露出过"之后，手动复制才算隐式采纳/否定信号。
    /// 否则每次复制都会写一条 copiedManually 反馈，而它被引擎当作复用信号 ⇒ 排序自我强化。
    func testManualCopyAfterVisibleSuggestionsCountsAsRevealedPreference() {
        let suite = "clipboardhistory.tests.revealed.\(UUID().uuidString)"
        let feedbackDefaults = UserDefaults(suiteName: suite)!
        defer { feedbackDefaults.removePersistentDomain(forName: suite) }
        let store = makeStore()
        store.feedbackStore = RecommendationFeedbackStore(defaults: feedbackDefaults)

        // 冷启动：还没有任何推荐露出 ⇒ 复制不得产生反馈
        store.add(intake("冷启动复制"), timestamp: Date())
        waitUntil { !store.predictionSuggestionEntries.isEmpty }
        XCTAssertEqual(store.feedbackStore.entries.count, 0, "首次复制之前没有推荐可见，不得记 copiedManually")

        // 此时 Top-1 已经显示 ⇒ 再复制别的内容 ⇒ 记一次隐式反馈
        // （若窗口在"开始计算"时就开，这里会是 0 条；若在每次刷新都开，则冷启动那一次也会记）
        store.add(intake("又复制了别的"), timestamp: Date())
        waitUntil { store.feedbackStore.entries.contains { $0.kind == .copiedManually } }
        XCTAssertFalse(
            store.feedbackStore.entries.filter { $0.kind == .copiedManually }.isEmpty,
            "推荐可见之后的手动复制应被记录"
        )
    }

    func testStaleGenerationResultsAreDiscarded() {
        // 代际守卫的可观察面：连续两次刷新后，界面必须与"最后一次刷新时的数据"一致。
        let store = makeStore()
        store.add(intake("甲"), timestamp: Date())
        store.add(intake("乙"), timestamp: Date())
        store.add(intake("丙"), timestamp: Date())
        store.add(intake("丁"), timestamp: Date())
        waitUntil { store.predictionSuggestionEntries.count == 3 }
        // 候选上限 3；同分时按复制时间由新到旧 ⇒ 必须是最后一次刷新（含 4 条数据）的结果，
        // 而不是某个中途的陈旧代。
        XCTAssertEqual(
            store.predictionSuggestionEntries.map(\.shortPreview),
            ["丁", "丙", "乙"],
            "最终界面必须是最新一代输入的结果"
        )
    }
}
