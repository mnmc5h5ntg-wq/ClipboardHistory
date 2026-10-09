import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 N-1 / 账本 R2-01：存档里出现"同 id 两条、内容不同"时，**整条产品管线**不许崩。
///
/// 为什么这条必须走 `HistoryStore` 而不是直接调引擎：上一轮的守卫测试
/// （`RecommendationBoundaryTests`）调的是 `RuleBasedRecommendationEngine.recommend(entries:)`，
/// 绕过了 `LocalRecommendationService` → `ClipboardEntryIntelligenceAdapter.intelligenceByEntryID`，
/// 而崩溃点正在 adapter 的 `Dictionary(uniqueKeysWithValues:)` 里（重复键 = `fatalError`）。
/// 结果就是：引擎层去重的测试全绿，产品在任何一次预测刷新（菜单打开 / 新复制 / 前台切换）时 trap。
///
/// 可达性：`HistoryStore.collapsingDuplicates` 只按**内容**合并，同 id 不同内容会原样留下；
/// 而"存档可被手改、或从半截恢复里出现同 id 两条"正是 R-55 自己的动机。
@MainActor
final class DuplicateIDPredictionPipelineTests: XCTestCase {
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

    func testPredictionRefreshSurvivesArchiveWithTwoEntriesSharingOneID() {
        let sharedID = UUID()
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            makeClipboardEntry(id: sharedID, content: .text("较新的一条"), timestamp: Date(timeIntervalSince1970: 3)),
            makeClipboardEntry(content: .text("无关的一条"), timestamp: Date(timeIntervalSince1970: 2)),
            makeClipboardEntry(id: sharedID, content: .text("较旧的一条"), timestamp: Date(timeIntervalSince1970: 1))
        ])
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )

        // 夹具前提必须先自证：同 id 不同内容的两条都还活着（去重只按内容合并）。
        // 少了这一句，"预测没崩"可能只是"触发条件根本没被构造出来"。
        XCTAssertEqual(
            store.entries.filter { $0.id == sharedID }.count, 2,
            "夹具前提不成立：同 id 两条应当都留在库里，否则这条用例测不到 adapter 的重复键路径"
        )

        store.refreshPredictions()

        // 崩溃发生在 Task.detached 里，一旦 trap 就是整个测试进程没了（不是可捕获的失败），
        // 所以"能等到候选出现"本身就是主要判据。
        waitUntil("预测刷新应产出候选（若 adapter 仍在用 uniqueKeysWithValues，进程会在这里 trap）") {
            !store.predictionSuggestionEntries.isEmpty
        }

        let duplicated = store.predictionSuggestionEntries.filter { $0.id == sharedID }
        XCTAssertEqual(duplicated.count, 1, "同一个 id 在推荐结果里只应出现一次，实际 \(duplicated.count) 次")
        XCTAssertEqual(
            duplicated.first?.content, .text("较新的一条"),
            "保留的应是首条（较新的一条），而不是重复项里随机的一条"
        )
        XCTAssertNotNil(store.predictionReasonByEntryID[sharedID], "该 id 应当有推荐理由")
    }
}
