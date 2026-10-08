import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class HistoryStoreTests: XCTestCase {
    func testAddKeepsNewestFirstAndSelectsNewestEntry() {
        let store = makeStore(maxEntries: 10)

        store.add(intakeEntry(text: "old"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "new"), timestamp: Date(timeIntervalSince1970: 2))

        XCTAssertEqual(store.entries.map(\.content), [.text("new"), .text("old")])
        XCTAssertEqual(store.selectedEntry?.content, .text("new"))
    }

    func testAddDropsAdjacentDuplicateContent() {
        let store = makeStore(maxEntries: 10)

        store.add(intakeEntry(text: "same"))
        store.add(intakeEntry(text: "same"))

        XCTAssertEqual(store.entries.map(\.content), [.text("same")])
    }

    func testAddDropsAdjacentDuplicateImageContent() throws {
        let store = makeStore(maxEntries: 10)
        let image = try makeStoredImage()
        let pngData = try XCTUnwrap(image.pngData())
        let firstImage = try XCTUnwrap(StoredImage(pngData: pngData))
        let secondImage = try XCTUnwrap(StoredImage(pngData: pngData))

        store.add(intakeEntry(image: firstImage))
        store.add(intakeEntry(image: secondImage))

        XCTAssertEqual(store.entries.count, 1)
        XCTAssertEqual(store.entries.first?.content, .image(firstImage))
    }

    func testAddPromotesExistingImageContentInsteadOfAddingDuplicate() throws {
        let store = makeStore(maxEntries: 10)
        let image = try makeStoredImage()
        let pngData = try XCTUnwrap(image.pngData())
        let firstImage = try XCTUnwrap(StoredImage(pngData: pngData))
        let secondImage = try XCTUnwrap(StoredImage(pngData: pngData))

        store.add(intakeEntry(image: firstImage), timestamp: Date(timeIntervalSince1970: 1))
        let originalImageID = try XCTUnwrap(store.entries.first?.id)
        store.add(intakeEntry(text: "between"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(intakeEntry(image: secondImage), timestamp: Date(timeIntervalSince1970: 3))

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.id, originalImageID)
        XCTAssertEqual(store.entries.first?.content, .image(firstImage))
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.map(\.content), [.image(firstImage), .text("between")])
        XCTAssertEqual(store.selectedEntry?.id, originalImageID)
    }

    func testAddPromotesExistingTextContentInsteadOfAddingDuplicate() throws {
        let store = makeStore(maxEntries: 10)

        store.add(intakeEntry(text: "repeat me"), timestamp: Date(timeIntervalSince1970: 1))
        let originalTextID = try XCTUnwrap(store.entries.first?.id)
        store.add(intakeEntry(text: "between"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(intakeEntry(text: "repeat me"), timestamp: Date(timeIntervalSince1970: 3))

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.id, originalTextID)
        XCTAssertEqual(store.entries.first?.content, .text("repeat me"))
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.map(\.content), [.text("repeat me"), .text("between")])
        XCTAssertEqual(store.selectedEntry?.id, originalTextID)
    }

    func testAddPromotesExistingFileContentInsteadOfAddingDuplicate() throws {
        let store = makeStore(maxEntries: 10)
        let url = URL(fileURLWithPath: "/tmp/repeat.pdf")

        store.add(intakeEntry(file: url), timestamp: Date(timeIntervalSince1970: 1))
        let originalFileID = try XCTUnwrap(store.entries.first?.id)
        store.add(intakeEntry(text: "between"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(intakeEntry(file: url), timestamp: Date(timeIntervalSince1970: 3))

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.id, originalFileID)
        XCTAssertEqual(store.entries.first?.content, .file(url))
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.map(\.content), [.file(url), .text("between")])
        XCTAssertEqual(store.selectedEntry?.id, originalFileID)
    }

    func testAddPromotesImageRoundTrippedThroughPasteboardInsteadOfAddingDuplicate() throws {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        let store = makeStore(maxEntries: 10)
        var intake = ClipboardIntake(pasteboard: pasteboard)
        let writer = SystemClipboardWriter(pasteboard: pasteboard)
        let image = try makeStoredImage(size: NSSize(width: 4, height: 5))
        let pngData = try XCTUnwrap(image.pngData())

        pasteboard.setData(pngData, forType: .png)
        let firstEntry = try XCTUnwrap(intake.refresh(from: pasteboard))
        store.add(firstEntry, timestamp: Date(timeIntervalSince1970: 1))
        let originalImageID = try XCTUnwrap(store.entries.first?.id)

        store.add(intakeEntry(text: "between"), timestamp: Date(timeIntervalSince1970: 2))
        try writer.write(store.entries[1].content)
        let roundTrippedEntry = try XCTUnwrap(intake.refresh(from: pasteboard))
        store.add(roundTrippedEntry, timestamp: Date(timeIntervalSince1970: 3))

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.id, originalImageID)
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.map(\.content), [firstEntry.content, .text("between")])
        XCTAssertEqual(store.selectedEntry?.id, originalImageID)
    }

    func testAddPromotesMatchingImageFileThumbnailEvenWhenURLChanges() throws {
        let store = makeStore(maxEntries: 10)
        let image = try makeStoredImage(size: NSSize(width: 4, height: 5))
        let firstURL = URL(fileURLWithPath: "/tmp/first-copy.png")
        let secondURL = URL(fileURLWithPath: "/tmp/second-copy.png")

        store.add(
            intakeEntry(file: firstURL, thumbnail: image),
            timestamp: Date(timeIntervalSince1970: 1)
        )
        let originalImageID = try XCTUnwrap(store.entries.first?.id)
        store.add(intakeEntry(text: "between"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(
            intakeEntry(file: secondURL, thumbnail: image),
            timestamp: Date(timeIntervalSince1970: 3)
        )

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.id, originalImageID)
        XCTAssertEqual(store.entries.first?.content, .file(secondURL))
        XCTAssertEqual(store.entries.first?.thumbnail, image)
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.map(\.content), [.file(secondURL), .text("between")])
        XCTAssertEqual(store.selectedEntry?.id, originalImageID)
    }

    func testAddTrimsHistoryToMaxEntries() {
        let store = makeStore(maxEntries: 2)

        store.add(intakeEntry(text: "one"))
        store.add(intakeEntry(text: "two"))
        store.add(intakeEntry(text: "three"))

        XCTAssertEqual(store.entries.map(\.content), [.text("three"), .text("two")])
    }

    func testFilteredEntriesCacheReflectsEveryKindOfMutation() throws {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "alpha"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "beta"), timestamp: Date(timeIntervalSince1970: 2))

        // 1) entries 变化后必须立刻可见
        store.perform(.updateSearch("alpha"))
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["alpha"])
        store.add(intakeEntry(text: "alphabet"), timestamp: Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["alphabet", "alpha"], "新增条目必须让缓存失效")

        // 2) 删除后不得留在缓存里
        let target = try XCTUnwrap(store.entries.first { $0.content == .text("alpha") })
        store.perform(.delete(target))
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["alphabet"])

        // 3) 筛选条件变化
        store.perform(.updateSearch(""))
        store.perform(.updateFilter(.favorites))
        XCTAssertTrue(store.filteredEntries.isEmpty, "没有收藏项时收藏筛选应为空")
        let kept = try XCTUnwrap(store.entries.first)
        store.perform(.toggleFavorite(kept))
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["alphabet"], "收藏变化后必须重新求值")

        // 4) 清空
        store.perform(.updateFilter(.all))
        store.perform(.clear)
        XCTAssertEqual(store.filteredEntries.count, 1)
    }

    func testPerformUpdatesSearchAndFiltersEntries() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "hello"))
        store.add(intakeEntry(text: "world"))

        store.perform(.updateSearch("wor"))

        XCTAssertEqual(store.searchText, "wor")
        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("world")])
    }

    func testPerformCopyWritesThroughClipboardWriter() {
        let writer = RecordingClipboardWriter()
        let store = makeStore(clipboardWriter: writer, maxEntries: 10)
        store.add(intakeEntry(text: "copy me"))

        store.perform(.copy(store.entries[0]))

        XCTAssertEqual(writer.writtenContents, [.text("copy me")])
    }

    func testPerformCopyFailureRecordsErrorMessage() {
        let writer = RecordingClipboardWriter()
        writer.errorToThrow = ClipboardWriteError.failedToWriteText
        let store = makeStore(clipboardWriter: writer, maxEntries: 10)
        store.add(intakeEntry(text: "copy me"))

        store.perform(.copy(store.entries[0]))

        XCTAssertEqual(writer.writtenContents, [.text("copy me")])
        XCTAssertEqual(store.clipboardWriteErrorMessage, ClipboardWriteError.failedToWriteText.localizedDescription)
    }

    /// 原来这条叫 "...AreHiddenUntilToggled..."：开关 `showsPredictionSuggestions`
    /// 在全仓没有任何调用者（README 却宣传"侧边栏 Magic 可展开"），随死代码一起删除；
    /// 保留的意图是 Top-3 上限与排序，改为直接触发 refreshPredictions()。
    func testPredictionsAreCappedToTopThreeInRecencyOrder() {
        let store = makeStore(maxEntries: 10)
        for index in 0..<5 {
            store.add(
                intakeEntry(text: "item \(index)"),
                timestamp: Date(timeIntervalSince1970: Double(index))
            )
        }

        store.refreshPredictions()

        // 预测是在后台任务里算完再回主线程赋值的，用"等到真的有结果"取代固定 sleep：
        // 固定 0.3s 的写法在机器负载变化时会随机失败（本轮实测 5 次挂 3 次）。
        waitUntil(description: "预测结果就绪", timeout: 5.0) {
            store.predictionSuggestionEntries.count == 3
        }

        XCTAssertEqual(store.predictionSuggestionEntries.count, 3)
        XCTAssertEqual(store.predictionSuggestionEntries.first?.shortPreview, "item 4")
    }

    /// 轮询直到条件成立（在主线程 runloop 上跑，让 MainActor.run 回调有机会执行）。
    private func waitUntil(
        description: String,
        timeout: TimeInterval,
        condition: @MainActor () -> Bool
    ) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：在 \(timeout)s 内未成立")
    }

    func testSelectingPredictionSuggestionUsesNormalSelectionState() throws {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "older"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "newer"), timestamp: Date(timeIntervalSince1970: 2))
        store.refreshPredictions()

        waitUntil(description: "预测结果就绪", timeout: 5.0) {
            !store.predictionSuggestionEntries.isEmpty
        }

        let suggestion = try XCTUnwrap(store.predictionSuggestionEntries.first)
        store.perform(.selectOnly(suggestion))

        XCTAssertEqual(store.selectedEntry?.id, suggestion.id)
        XCTAssertEqual(store.selectedEntryIDs, Set([suggestion.id]))
    }

    func testPerformCopyAndPromoteWritesAndMovesEntryToTop() {
        let writer = RecordingClipboardWriter()
        let store = makeStore(clipboardWriter: writer, maxEntries: 10)
        store.add(intakeEntry(text: "old"))
        store.add(intakeEntry(text: "new"))
        let old = store.entries[1]

        store.perform(.copyAndPromote(old))

        XCTAssertEqual(writer.writtenContents, [.text("old")])
        XCTAssertEqual(store.entries.first?.content, .text("old"))
        XCTAssertEqual(store.selectedEntry?.content, .text("old"))
    }

    func testPerformCopyAndPromoteFailureDoesNotMoveEntryOrPersist() {
        let writer = RecordingClipboardWriter()
        writer.errorToThrow = ClipboardWriteError.failedToWriteText
        let persistence = RecordingHistoryPersistence()
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        store.add(intakeEntry(text: "old"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "new"), timestamp: Date(timeIntervalSince1970: 2))
        let old = store.entries[1]
        let saveCountBeforeCopy = persistence.savedEntriesSnapshots.count

        store.perform(.copyAndPromote(old))

        XCTAssertEqual(writer.writtenContents, [.text("old")])
        XCTAssertEqual(store.entries.map(\.content), [.text("new"), .text("old")])
        XCTAssertEqual(store.selectedEntry?.content, .text("new"))
        XCTAssertEqual(persistence.savedEntriesSnapshots.count, saveCountBeforeCopy)
        XCTAssertEqual(store.clipboardWriteErrorMessage, ClipboardWriteError.failedToWriteText.localizedDescription)
    }

    func testPerformRepeatCopySelectedEntryCopiesSelectionAndMovesItToTop() {
        let writer = RecordingClipboardWriter()
        let store = makeStore(clipboardWriter: writer, maxEntries: 10)
        store.add(intakeEntry(text: "old"))
        store.add(intakeEntry(text: "new"))
        let old = store.entries[1]
        store.perform(.select(old))

        store.perform(.repeatCopySelected)

        XCTAssertEqual(writer.writtenContents, [.text("old")])
        XCTAssertEqual(store.entries.first?.content, .text("old"))
        XCTAssertEqual(store.selectedEntry?.content, .text("old"))
    }

    func testPerformCopyAndPromoteKeepsFavoriteState() {
        let writer = RecordingClipboardWriter()
        let store = makeStore(clipboardWriter: writer, maxEntries: 10)
        store.add(intakeEntry(text: "favorite"))
        let entry = store.entries[0]

        store.perform(.toggleFavorite(entry))
        store.perform(.copyAndPromote(store.entries[0]))

        XCTAssertEqual(store.entries.first?.content, .text("favorite"))
        XCTAssertEqual(store.entries.first?.isFavorite, true)
    }

    func testPerformSelectDeleteAndClearKeepsFavorites() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "one"))
        store.add(intakeEntry(text: "two"))

        let oldest = store.entries[1]
        store.perform(.select(oldest))
        XCTAssertEqual(store.selectedEntry?.id, oldest.id)

        store.perform(.delete(oldest))
        XCTAssertEqual(store.entries.map(\.content), [.text("two")])
        XCTAssertEqual(store.selectedEntry?.content, .text("two"))

        let favorite = store.entries[0]
        store.perform(.toggleFavorite(favorite))
        store.add(intakeEntry(text: "ordinary"))
        XCTAssertEqual(store.entries.map(\.content), [.text("ordinary"), .text("two")])

        store.perform(.clear)
        XCTAssertEqual(store.entries.map(\.content), [.text("two")])
        XCTAssertEqual(store.entries.first?.isFavorite, true)
        XCTAssertEqual(store.selectedEntry?.content, .text("two"))
    }

    func testSelectionSupportsRangeToggleBulkFavoriteAndBulkDelete() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "one"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "two"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(intakeEntry(text: "three"), timestamp: Date(timeIntervalSince1970: 3))
        let newest = store.entries[0]
        let oldest = store.entries[2]

        store.perform(.selectOnly(newest))
        store.perform(.selectRange(to: oldest))

        XCTAssertEqual(store.selectedCount, 3)
        XCTAssertEqual(store.selectedEntry?.content, .text("one"))

        store.perform(.toggleSelection(store.entries[1]))

        XCTAssertEqual(store.selectedCount, 2)
        XCTAssertFalse(store.isSelected(store.entries[1]))

        store.perform(.favoriteSelection)

        XCTAssertEqual(store.entries.filter(\.isFavorite).map(\.content), [.text("three"), .text("one")])

        store.perform(.deleteSelection)

        XCTAssertEqual(store.entries.map(\.content), [.text("two")])
        XCTAssertEqual(store.selectedEntry?.content, .text("two"))
        XCTAssertEqual(store.selectedCount, 1)
    }

    func testTogglingCurrentSelectionKeepsDetailOnRemainingSelectedEntry() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "one"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "two"), timestamp: Date(timeIntervalSince1970: 2))

        store.perform(.selectOnly(store.entries[0]))
        store.perform(.toggleSelection(store.entries[1]))
        store.perform(.toggleSelection(store.entries[1]))

        XCTAssertEqual(store.selectedCount, 1)
        XCTAssertEqual(store.selectedEntry?.content, .text("two"))
    }

    func testAddSupportsMultipleFileContent() throws {
        let store = makeStore(maxEntries: 10)
        let firstURL = URL(fileURLWithPath: "/tmp/first.txt")
        let secondURL = URL(fileURLWithPath: "/tmp/second.txt")

        store.add(intakeEntry(files: [firstURL, secondURL]))

        XCTAssertEqual(store.entries.map(\.content), [.files([firstURL, secondURL])])
        XCTAssertEqual(store.selectedEntry?.content, .files([firstURL, secondURL]))
    }

    func testAddingOrdinaryEntryWhileFavoriteFilterIsActiveKeepsVisibleSelection() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "favorite"), timestamp: Date(timeIntervalSince1970: 1))
        store.perform(.toggleFavorite(store.entries[0]))
        store.perform(.updateFilter(.favorites))

        store.add(intakeEntry(text: "ordinary"), timestamp: Date(timeIntervalSince1970: 2))

        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("favorite")])
        XCTAssertEqual(store.selectedEntry?.content, .text("favorite"))
    }

    func testRemovingFavoriteStateWhileFavoriteFilterIsActiveSelectsNextVisibleEntry() {
        let store = makeStore(maxEntries: 10)
        store.add(intakeEntry(text: "first"), timestamp: Date(timeIntervalSince1970: 1))
        store.perform(.toggleFavorite(store.entries[0]))
        store.add(intakeEntry(text: "second"), timestamp: Date(timeIntervalSince1970: 2))
        store.perform(.toggleFavorite(store.entries[0]))
        store.perform(.updateFilter(.favorites))

        store.perform(.toggleFavorite(store.filteredEntries[0]))

        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("first")])
        XCTAssertEqual(store.selectedEntry?.content, .text("first"))
    }

    private func intakeEntry(text: String) -> ClipboardIntake.Entry {
        // 固定来源 App：否则来源取自由于真实前台应用（NSWorkspace.frontmostApplication），
        // 排序断言会随测试期间谁在焦点上而随机失败。R-05 之后来源可以在采集时注入。
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
    }

    private func intakeEntry(image: StoredImage) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .image(image), thumbnail: image, sourceUTIs: ["public.png"])
    }

    private func intakeEntry(file url: URL) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .file(url), thumbnail: nil, sourceUTIs: ["public.file-url"])
    }

    private func intakeEntry(file url: URL, thumbnail: StoredImage) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .file(url), thumbnail: thumbnail, sourceUTIs: ["public.file-url"])
    }

    private func intakeEntry(files urls: [URL]) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .files(urls), thumbnail: nil, sourceUTIs: ["public.file-url"])
    }

    private func makeStore(
        clipboardWriter: ClipboardWriting = RecordingClipboardWriter(),
        maxEntries: Int
    ) -> HistoryStore {
        HistoryStore(
            clipboardWriter: clipboardWriter,
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: maxEntries, maxAgeDays: nil),
            maxEntries: maxEntries
        )
    }
}

@MainActor
private final class RecordingClipboardWriter: ClipboardWriting {
    private(set) var writtenContents: [ClipboardEntryContent] = []
    private var nextChangeCount = 1
    var errorToThrow: Error?

    func write(_ content: ClipboardEntryContent) throws -> Int {
        writtenContents.append(content)
        if let errorToThrow {
            throw errorToThrow
        }
        nextChangeCount += 1
        return nextChangeCount
    }
}
