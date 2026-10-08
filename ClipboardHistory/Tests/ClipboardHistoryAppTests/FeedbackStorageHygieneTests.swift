import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// 审计 A-5 / R-06：反馈记录曾把完整 ContextSnapshot（含最多 500 条 ×160 字的
/// 剪贴板正文预览）写进 UserDefaults。用户机器上实测该 plist 为 66,724,574 字节，
/// 其中同一个键的 blob 就有 66,716,424 字节 —— 每次启动都要在主线程解码它。
/// 这些测试锁住三件事：新记录不含正文、旧 blob 会被收窄、删历史要级联删反馈。
@MainActor
final class FeedbackStorageHygieneTests: XCTestCase {
    private let secret = "只有这一次复制里出现过的口令 Sup3r-XYZ-1234567890"

    /// 独立 suite，用完立刻移除持久域，避免污染用户默认值。
    private func makeDefaults() -> (UserDefaults, String) {
        let suite = "clipboardhistory.tests.feedback.\(UUID().uuidString)"
        return (UserDefaults(suiteName: suite)!, suite)
    }

    private func summary(preview: String) -> ClipboardEntrySummary {
        ClipboardEntrySummary(
            id: UUID(),
            contentKind: "text",
            preview: preview,
            isFavorite: false,
            copiedAt: Date(),
            sourceUTIs: [],
            sourceAppBundleID: "com.apple.Safari"
        )
    }

    /// 构造"旧格式"载荷：context 字段是完整的 ContextSnapshot（带正文预览）。
    private func legacyBlob(entryID: UUID, preview: String) throws -> Data {
        var snapshot = ContextSnapshot.minimal(
            recentEntries: [summary(preview: preview), summary(preview: "另一条正文片段-XYZ")],
            capturedAt: Date(timeIntervalSince1970: 1_700_000_000)
        )
        snapshot.frontmostApplication = RunningApplicationContext(
            localizedName: "Safari",
            bundleIdentifier: "com.apple.Safari",
            processIdentifier: nil
        )
        snapshot.recentEvents = [ContextEvent(kind: .copy, timestamp: Date(timeIntervalSince1970: 1_700_000_000))]
        let snapshotObject = try JSONSerialization.jsonObject(
            with: JSONEncoder().encode(snapshot)
        )
        let record: [String: Any] = [
            "entryID": entryID.uuidString,
            "kind": "accepted",
            "createdAt": 1_700_000_000,
            "context": snapshotObject,
        ]
        return try JSONSerialization.data(withJSONObject: [record])
    }

    func testLegacyBlobIsDecodedThenCompactedAndLosesClipboardText() throws {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let entryID = UUID()
        let legacy = try legacyBlob(entryID: entryID, preview: secret)
        defaults.set(legacy, forKey: RecommendationFeedbackStore.storageKey)
        XCTAssertTrue(String(data: legacy, encoding: .utf8)!.contains(secret), "夹具本身应含正文")

        let store = RecommendationFeedbackStore(defaults: defaults)
        XCTAssertEqual(store.entries.count, 1, "旧格式必须仍能读出记录")
        XCTAssertEqual(store.entries.first?.entryID, entryID)
        XCTAssertEqual(store.entries.first?.kind, .accepted)
        XCTAssertEqual(store.entries.first?.context.frontmostApplication?.bundleIdentifier, "com.apple.Safari",
                       "排序需要的元数据要留下")
        XCTAssertEqual(store.entries.first?.context.recentEvents.count, 1, "事件数量这类元数据要保留")
        XCTAssertTrue(store.didCompactLegacyBlob)
        XCTAssertGreaterThan(store.legacyBlobByteCount, legacy.count - 1)

        let rewritten = try XCTUnwrap(defaults.data(forKey: RecommendationFeedbackStore.storageKey))
        let text = try XCTUnwrap(String(data: rewritten, encoding: .utf8))
        XCTAssertFalse(text.contains(secret), "收窄后不得再留存剪贴板正文")
        XCTAssertFalse(text.contains("preview"), "收窄后不应再有 recentEntries 预览字段")
        XCTAssertLessThan(rewritten.count, 1_000, "单条瘦记录应远小于旧载荷")
    }

    func testNewlyRecordedFeedbackNeverContainsClipboardText() throws {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = RecommendationFeedbackStore(defaults: defaults)
        let context = ContextSnapshot.minimal(
            recentEntries: (0..<50).map { summary(preview: "正文片段 \($0) " + secret) },
            capturedAt: Date()
        )

        for index in 0..<20 {
            store.recordAccepted(entryID: UUID(), context: context)
            _ = index
        }

        let data = try XCTUnwrap(defaults.data(forKey: RecommendationFeedbackStore.storageKey))
        let text = try XCTUnwrap(String(data: data, encoding: .utf8))
        XCTAssertFalse(text.contains(secret), "新写入的反馈载荷不得含剪贴板正文")
        XCTAssertLessThan(data.count, 20 * 512, "20 条瘦记录应远小于 10KB")
        XCTAssertEqual(store.entries.count, 20)
    }

    func testRemoveEntriesPrunesMatchingFeedbackOnly() throws {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = RecommendationFeedbackStore(defaults: defaults)
        let kept = UUID()
        let dropped = UUID()
        let context = ContextSnapshot.minimal(recentEntries: [], capturedAt: Date())
        store.recordAccepted(entryID: kept, context: context)
        store.recordDismissed(entryID: dropped, context: context)

        store.removeEntries(withID: dropped)

        XCTAssertEqual(store.entries.map(\.entryID), [kept])
        let reread = RecommendationFeedbackStore(defaults: defaults)
        XCTAssertEqual(reread.entries.map(\.entryID), [kept], "剪枝必须已落盘")
    }

    func testDeletingHistoryEntryAlsoRemovesItsFeedback() throws {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let persistence = RecordingHistoryPersistence()
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        store.feedbackStore = RecommendationFeedbackStore(defaults: defaults)

        store.add(
            ClipboardIntake.Entry(content: .text("将被删除的一条"), thumbnail: nil, sourceUTIs: []),
            timestamp: Date()
        )
        let entry = try XCTUnwrap(store.entries.first)
        store.perform(.recordRecommendationAccepted(entry.id))
        XCTAssertEqual(store.feedbackStore.entries.count, 1)

        store.perform(.delete(entry))

        XCTAssertEqual(store.feedbackStore.entries.count, 0, "删除条目后其反馈必须一起清掉")
    }

    func testClearHistoryRemovesFeedbackForClearedEntries() throws {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        store.feedbackStore = RecommendationFeedbackStore(defaults: defaults)

        store.add(ClipboardIntake.Entry(content: .text("ordinary"), thumbnail: nil, sourceUTIs: []), timestamp: Date())
        store.add(ClipboardIntake.Entry(content: .text("favorite"), thumbnail: nil, sourceUTIs: []), timestamp: Date())
        let favorite = try XCTUnwrap(store.entries.first { $0.content == .text("favorite") })
        store.perform(.toggleFavorite(favorite))
        store.perform(.recordRecommendationAccepted(favorite.id))
        let ordinary = try XCTUnwrap(store.entries.first { $0.content == .text("ordinary") })
        store.perform(.recordRecommendationAccepted(ordinary.id))
        XCTAssertEqual(store.feedbackStore.entries.count, 2)

        store.perform(.clear)

        XCTAssertEqual(store.entries.map(\.content), [.text("favorite")])
        XCTAssertEqual(store.feedbackStore.entries.map(\.entryID), [favorite.id], "收藏项的反馈留下，被清掉的反馈要走")
    }

    func testExportWithoutDataThrowsInsteadOfPretendingSuccess() {
        let (defaults, suite) = makeDefaults()
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = RecommendationFeedbackStore(defaults: defaults)
        XCTAssertThrowsError(try store.exportToFile()) { error in
            XCTAssertEqual(error as? RecommendationFeedbackStore.ExportError, .noData)
        }
    }
}
