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

    /// BACKLOG 224（R205）：D-4 修了"接住了但什么都没发生"，漏了另一半 ——
    /// provider **声称**是文件、`loadItem` 却一个 URL 都没解出来时，`urls` 是空数组，
    /// store 看到的是"什么都没拖进来"，于是连 D-4 那条回执也不发 ⇒ 用户视角仍然是"我拖了，什么都没发生"。
    /// 三条正反对照一起写：① attempted=2 而解出 0 ⇒ 必须说话，且说的是 2 不是 0；
    /// ② 不传 attemptedCount（旧调用方）⇒ 行为与改前一致，不许凭空造回执；③ 真解出来一个 ⇒ 成功不该被横幅打断。
    func testDroppedProvidersThatDecodeToNothingStillSpeakUp() {
        let store = makeStore()
        XCTAssertEqual(store.addDroppedFiles(urls: [], attemptedCount: 2), 0)
        let notice = store.droppedFilesNotice
        XCTAssertNotNil(notice, "声称是文件却一个都没解出来 ⇒ 必须就地说话（D-4 的另一半）")
        XCTAssertEqual(notice?.contains("2 项"), true, "回执要说 attempted 的个数而不是解出来的 0：\(notice ?? "nil")")
        XCTAssertTrue(store.entries.isEmpty, "说话不等于入库：仍然不能留下空记录")

        let quiet = makeStore()
        XCTAssertEqual(quiet.addDroppedFiles(urls: []), 0)
        XCTAssertNil(quiet.droppedFilesNotice, "没传 attemptedCount 的旧调用方照旧不说话（这条不许被放宽成默认回执）")

        let ok = makeStore()
        let file = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("dropped-\(UUID().uuidString).txt")
        FileManager.default.createFile(atPath: file.path, contents: Data("x".utf8))
        addTeardownBlock { try? FileManager.default.removeItem(at: file) }
        XCTAssertEqual(ok.addDroppedFiles(urls: [file], attemptedCount: 1), 1)
        XCTAssertNil(ok.droppedFilesNotice, "成功那一格不该被横幅打断")
    }

    /// BACKLOG 230（R206）：**调用点守卫**。
    ///
    /// 为什么单独要有这一条：上面那三条对照都从 store 入口进，它们证明的是"store 有说话的能力"。
    /// 把视图里那一处传参摘掉，store 看到的是空数组、`attemptedCount` 是 nil ⇒ 三对照全绿，
    /// 而产品重新变回"我拖了，什么都没发生"。判据有牙但咬不到接线 —— 这是 R43/R44 那一族"零调用点的死尺"。
    /// 扫之前剥行注释：整文件 contains 会命中引用它自己的那些注释（R74/R75 记过同一族）。
    func testSidebarWiresTheAttemptedCountAtTheCallSite() throws {
        let view = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
        let raw = try String(contentsOf: view, encoding: .utf8)
        let code = raw.split(separator: "\n", omittingEmptySubsequences: false).map { line -> String in
            guard let cut = line.range(of: "//") else { return String(line) }
            return String(line[..<cut.lowerBound])
        }.joined(separator: "\n")
        let wired = "addDroppedFiles(urls: urls, attemptedCount: wanted.count)"
        let bare = "addDroppedFiles(urls: urls)"
        let wiredHits = code.components(separatedBy: wired).count - 1
        let bareHits = code.components(separatedBy: bare).count - 1
        XCTAssertEqual(wiredHits, 1, "侧栏只有一处拖入调用点，且必须把「声称有几个」传进 store ⇒ 传参就是这条回执唯一的接线")
        XCTAssertEqual(bareHits, 0, "调用点退回不传 attemptedCount：store 会看到空数组而重新静默，而 store 那三条对照全都会绿")
    }
}
