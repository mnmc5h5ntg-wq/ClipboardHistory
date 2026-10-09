import AppKit
import UniformTypeIdentifiers
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 1.5 / 账本 R2-05 的另一半：整个应用以前不接受任何拖入
/// （`onDrop`/`dropDestination` 全仓零命中）。这里钉住"拖进来变成什么"，
/// 而 provider 解码那段胶水需要真实鼠标拖放，验收等级见账本（未验证）。
@MainActor
final class DroppedFileImportTests: XCTestCase {
    private func fileURL(_ name: String) -> URL {
        URL(fileURLWithPath: "/tmp/\(name)-\(UUID().uuidString).txt")
    }

    func testSingleFileDropsAsOneFileEntry() throws {
        let url = fileURL("单个")
        let planned = try XCTUnwrap(DroppedFileImport.plan(for: [url]))
        XCTAssertEqual(planned.content, .file(url))
        XCTAssertEqual(planned.ignoredCount, 0)
    }

    func testSeveralFilesDropAsOneMultiFileEntry() throws {
        let a = fileURL("甲"), b = fileURL("乙"), c = fileURL("丙")
        let planned = try XCTUnwrap(DroppedFileImport.plan(for: [a, b, c]))
        XCTAssertEqual(planned.content, .files([a, b, c]),
                       "一次拖进来应当是**一条**多文件记录，而不是三条")
        XCTAssertEqual(planned.ignoredCount, 0)
    }

    func testWebURLsAreNotAcceptedAsDroppedFiles() {
        let web = URL(string: "https://example.com/page")!
        XCTAssertNil(DroppedFileImport.plan(for: [web]),
                     "非文件 URL 拖进来不该被当成文件入库（P-15 同族的混淆）")
        XCTAssertNil(DroppedFileImport.plan(for: []))
    }

    func testMixedDropKeepsTheFilesAndCountsWhatItIgnored() throws {
        let file = fileURL("混")
        let web = URL(string: "https://example.com/x")!
        let planned = try XCTUnwrap(DroppedFileImport.plan(for: [web, file]))
        XCTAssertEqual(planned.content, .file(file))
        XCTAssertEqual(planned.ignoredCount, 1, "被丢掉的项要能被数出来，否则用户不知道为什么只进来一条")
    }

    func testDropHintNamesWhatWillBeRecorded() throws {
        let file = fileURL("提示")
        XCTAssertTrue(try XCTUnwrap(DroppedFileImport.dropHint(for: [file])).contains("提示"))
        XCTAssertEqual(try XCTUnwrap(DroppedFileImport.dropHint(for: [fileURL("一"), fileURL("二")])),
                       "加入历史：2 个文件")
        XCTAssertNil(DroppedFileImport.dropHint(for: []))
    }

    func testAcceptedTypesAreFileURLsOnly() {
        XCTAssertEqual(DroppedFileImport.acceptedTypeIdentifiers, [UTType.fileURL.identifier])
    }

    // MARK: - 走 store 的真实路径

    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    func testStoreRecordsDroppedFilesAndPersistsThem() throws {
        let store = makeStore()
        let a = fileURL("拖入甲"), b = fileURL("拖入乙")
        let added = store.addDroppedFiles(urls: [a, b], timestamp: Date(timeIntervalSince1970: 500))
        XCTAssertEqual(added, 1, "一次拖入 = 一条记录")
        XCTAssertEqual(store.entries.count, 1)
        XCTAssertEqual(store.entries.first?.content, .files([a, b]))
        XCTAssertEqual(store.entries.first?.sourceUTIs, ["public.file-url"])

        // 存盘再载入仍然是一条多文件记录（不是只有内存里有）。
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("拖入文件-\(UUID().uuidString)", isDirectory: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save(store.entries)
        persistence.flushPendingSaves()
        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.map(\.content), [.files([a, b])])
    }

    func testStoreIgnoresDropsWithNoUsableFile() {
        let store = makeStore()
        let web = URL(string: "https://example.com/y")!
        XCTAssertEqual(store.addDroppedFiles(urls: [web]), 0)
        XCTAssertEqual(store.addDroppedFiles(urls: []), 0)
        XCTAssertTrue(store.entries.isEmpty, "没有可用文件时不能留下空记录")
    }
}
