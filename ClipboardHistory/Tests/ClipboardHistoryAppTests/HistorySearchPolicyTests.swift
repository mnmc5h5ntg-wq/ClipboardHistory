import XCTest
@testable import ClipboardHistoryApp

/// R445：侧栏搜索匹配**内容 + 来源 App 名**（R437 的欠账；R444 把来源显示在行里）。
///
/// 两条腿：纯谓词（来源/内容/空查询/归零）与**产品入口**（`HistoryStore.perform(.updateSearch)`）。
/// 像素那一半在 `UICaptureTests.testSidebarSearchMatchesTheSourceAppName`：
/// 查询 "Safari" 只命中来源、不命中正文 —— 行数 0→1 就是来源匹配的证人。
final class HistorySearchPolicyTests: XCTestCase {
    private func entry(_ text: String, source: String?) -> ClipboardEntry {
        makeClipboardEntry(content: .text(text), sourceAppName: source)
    }

    func testSourceAppNameMatchesAlongsideTheContent() {
        let safari = entry("hello world", source: "Safari")
        XCTAssertTrue(HistorySearchPolicy.matches(entry: safari, query: "Safari", ocrIndex: [:]),
                      "来源 App 名没有参与匹配")
        XCTAssertTrue(HistorySearchPolicy.matches(entry: safari, query: "safari", ocrIndex: [:]),
                      "来源匹配不是大小写不敏感")
        XCTAssertTrue(HistorySearchPolicy.matches(entry: safari, query: "HELLO", ocrIndex: [:]),
                      "正文匹配被来源匹配挤掉了")
        XCTAssertFalse(HistorySearchPolicy.matches(entry: safari, query: "Firefox", ocrIndex: [:]))
    }

    func testNilOrBlankSourceFallsBackToTheContent() {
        let noSource = entry("hello world", source: nil)
        XCTAssertFalse(HistorySearchPolicy.matches(entry: noSource, query: "Safari", ocrIndex: [:]),
                       "没有来源却命中了来源名")
        XCTAssertTrue(HistorySearchPolicy.matches(entry: noSource, query: "hello", ocrIndex: [:]))
        let blank = entry("hello", source: "  ")
        XCTAssertFalse(HistorySearchPolicy.matches(entry: blank, query: "  ", ocrIndex: [:]),
                       "空白查询/空白来源凑出了一个匹配")
    }

    func testEmptyQueryMatchesEverythingAndOtherContentStillWorks() {
        let safari = entry("hello", source: "Safari")
        XCTAssertTrue(HistorySearchPolicy.matches(entry: safari, query: "", ocrIndex: [:]))
        // 图片/OCR 那一档由既有搜索测试覆盖（这里不造 PNG 夹具，免得把策略测试变成渲染测试）。
        let file = makeClipboardEntry(content: .file(URL(fileURLWithPath: "/tmp/合同 v3.pdf")))
        XCTAssertTrue(HistorySearchPolicy.matches(entry: file, query: "合同", ocrIndex: [:]))
        XCTAssertTrue(HistorySearchPolicy.matches(entry: file, query: "v3", ocrIndex: [:]))
    }

    /// 产品入口：`HistoryStore` 真的会把"只命中来源"的行搜出来（旧口径 0 行）。
    @MainActor
    func testStoreSearchFindsARowByItsSourceAppName() {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        store.add(ClipboardIntake.Entry(
            content: .text("hello world"), thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"),
            timestamp: Date(timeIntervalSince1970: 1_000))
        store.add(ClipboardIntake.Entry(
            content: .text("other row"), thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"),
            timestamp: Date(timeIntervalSince1970: 900))
        store.perform(.updateSearch("Safari"))
        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("hello world")],
                       "store 没把「只命中来源」的行搜出来")
        store.perform(.updateSearch("hello"))
        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("hello world")])
        store.perform(.updateSearch("SafariX"))
        XCTAssertTrue(store.filteredEntries.isEmpty)
    }
}
