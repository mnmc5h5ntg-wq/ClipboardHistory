import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 D-2 / D-3 / D-4 / D-8 的判据。
///
/// 四条都尽量落在"能从产品入口进去"这一层（C-1 那条规矩：修复的验收不要只测内部纯函数），
/// 所以 D-3/D-4 用真 `HistoryStore`，D-2 用真 `RecommendationPresenter.reason(...)`。
@MainActor
final class Round3AuditFixTests: XCTestCase {
    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    private func textEntry(_ string: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(string), thumbnail: nil,
                              sourceUTIs: ["public.utf8-plain-text"],
                              sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari")
    }

    override func tearDown() {
        // 这两个键是真 UserDefaults：不清掉会顺着进程留给后面的用例（"上一个测试改了开关"
        // 是最难查的一类互相污染）。
        UserDefaults.standard.removeObject(forKey: "recordingPaused")
        UserDefaults.standard.removeObject(forKey: "ocrSearchDisabled")
        super.tearDown()
    }

    // MARK: - D-3 暂停记录

    func testRecordingGateTruthTable() {
        XCTAssertTrue(CapturePolicy.accepts(paused: false, isUserInitiated: false))
        XCTAssertFalse(CapturePolicy.accepts(paused: true, isUserInitiated: false),
                       "暂停时后台采集必须不入库")
        XCTAssertTrue(CapturePolicy.accepts(paused: true, isUserInitiated: true),
                       "用户点名要存的（拖入文件）不能被暂停静默丢掉")
        XCTAssertTrue(OCRPolicy.shouldSchedule(isEnabled: true, hasImage: true))
        XCTAssertFalse(OCRPolicy.shouldSchedule(isEnabled: false, hasImage: true))
        XCTAssertFalse(OCRPolicy.shouldSchedule(isEnabled: true, hasImage: false))
    }

    func testPausedStoreDoesNotRecordButStillAcceptsExplicitImport() throws {
        let store = makeStore()
        store.isRecordingPaused = true
        store.add(textEntry("暂停期间复制的"), timestamp: Date(timeIntervalSince1970: 5))
        XCTAssertTrue(store.entries.isEmpty, "暂停了还入库 = 开关是装饰")

        let file = URL(fileURLWithPath: "/tmp/round3-audit-\(UUID().uuidString).txt")
        XCTAssertEqual(store.addDroppedFiles(urls: [file]), 1,
                       "暂停时用户明确拖入的文件应当照常入库")
        XCTAssertEqual(store.entries.count, 1)

        store.isRecordingPaused = false
        store.add(textEntry("恢复之后复制的"), timestamp: Date(timeIntervalSince1970: 6))
        XCTAssertEqual(store.entries.count, 2, "恢复后要能继续记录")
    }

    func testPausedFlagIsPersistedAndDefaultsToRecording() {
        UserDefaults.standard.removeObject(forKey: "recordingPaused")
        let store = makeStore()
        XCTAssertFalse(store.isRecordingPaused, "没写过键时必须照常记录（默认行为不能因为新增开关而改变）")
        store.isRecordingPaused = true
        XCTAssertTrue(makeStore().isRecordingPaused, "开关要跨窗口/重启留在 UserDefaults 里")
    }

    func testOCRDefaultIsOnAndSwitchReadsBack() {
        UserDefaults.standard.removeObject(forKey: "ocrSearchDisabled")
        let store = makeStore()
        XCTAssertTrue(store.isOCRSearchEnabled,
                      "OCR 默认必须是开 —— 键写成取反就是为了不让从没进过设置页的用户被悄悄关掉")
        store.isOCRSearchEnabled = false
        XCTAssertFalse(makeStore().isOCRSearchEnabled)
    }

    /// 接线守卫：两个开关必须真的在采集/OCR 那两条路径上，而且通用页真的有它们。
    func testSwitchesAreWiredIntoProductPathsAndSettingsPane() throws {
        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        XCTAssertTrue(store.contains("CapturePolicy.accepts(sourceAppBundleID:"),
                      "暂停开关没接在入库入口上")
        XCTAssertTrue(store.contains("OCRPolicy.shouldSchedule(isEnabled: isOCRSearchEnabled"),
                      "OCR 开关没接在排任务的地方")
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("recordingPaused"), "通用页没有「暂停记录」")
        XCTAssertTrue(settings.contains("识别截图文字用于搜索"), "通用页没有 OCR 开关")
    }

    // MARK: - D-4 拖入反馈

    func testDroppingOnlyWebURLsReportsNothingArrived() throws {
        let store = makeStore()
        let web = URL(string: "https://example.com/a.png")!
        XCTAssertEqual(store.addDroppedFiles(urls: [web, web]), 0)
        let notice = try XCTUnwrap(store.droppedFilesNotice,
                                   "一项都没进来却是静默的 —— 这就是 D-4 报的那个落点框闪一下就没了")
        XCTAssertTrue(notice.contains("2"), "反馈里要写清被忽略的数量：\(notice)")
        store.dismissDroppedFilesNotice()
        XCTAssertNil(store.droppedFilesNotice)
    }

    func testPartiallyIgnoredDropSaysHowManyWereIgnored() throws {
        let store = makeStore()
        let file = URL(fileURLWithPath: "/tmp/round3-partial.txt")
        let web = URL(string: "https://example.com/x")!
        XCTAssertEqual(store.addDroppedFiles(urls: [file, web]), 1)
        let notice = try XCTUnwrap(store.droppedFilesNotice, "混着拖入时也要说清有 1 项被忽略")
        XCTAssertTrue(notice.contains("1"))
        XCTAssertEqual(store.entries.count, 1)
    }

    func testCleanDropProducesNoNotice() {
        let store = makeStore()
        let file = URL(fileURLWithPath: "/tmp/round3-clean.txt")
        XCTAssertEqual(store.addDroppedFiles(urls: [file]), 1)
        XCTAssertNil(store.droppedFilesNotice, "全成功时不该打扰用户")
    }

    // MARK: - D-2 推荐理由

    /// 表驱动：内容类型标签必须由**条目**决定。审计在帧里读到的原缺陷形状是
    /// 「PDF 文件 + Safari 前台 ⇒ 偏好链接」—— 标签讲的是条目类型，
    /// 而旧实现读的是前台 App 的 bundle id，于是在 Safari 里每条推荐都成了"偏好链接"。
    func testContentTypeTagFollowsTheEntryNotTheFrontmostApp() throws {
        let store = makeStore()
        store.add(ClipboardIntake.Entry(content: .text("https://example.com"), thumbnail: nil,
                                       sourceUTIs: ["public.utf8-plain-text"]))
        store.add(ClipboardIntake.Entry(content: .text("一段普通文本"), thumbnail: nil,
                                       sourceUTIs: ["public.utf8-plain-text"]))
        store.add(ClipboardIntake.Entry(content: .file(URL(fileURLWithPath: "/tmp/合同 终版 v3.pdf")),
                                       thumbnail: nil, sourceUTIs: ["public.file-url"]))
        store.add(ClipboardIntake.Entry(content: .files([URL(fileURLWithPath: "/tmp/a.HEIC"),
                                                         URL(fileURLWithPath: "/tmp/b.HEIC")]),
                                       thumbnail: nil, sourceUTIs: ["public.file-url"]))
        let byContent = Dictionary(uniqueKeysWithValues: store.entries.map { ($0.content, $0) })

        XCTAssertEqual(RecommendationPresenter.contentTypeTag(for: try XCTUnwrap(byContent[.text("https://example.com")])), "常用链接")
        XCTAssertEqual(RecommendationPresenter.contentTypeTag(for: try XCTUnwrap(byContent[.text("一段普通文本")])), "常用文本")
        XCTAssertEqual(RecommendationPresenter.contentTypeTag(for: try XCTUnwrap(byContent[.file(URL(fileURLWithPath: "/tmp/合同 终版 v3.pdf"))])), "常用文件")
        XCTAssertEqual(RecommendationPresenter.contentTypeTag(
            for: try XCTUnwrap(byContent[.files([URL(fileURLWithPath: "/tmp/a.HEIC"), URL(fileURLWithPath: "/tmp/b.HEIC")])])), "常用多文件")
    }

    /// 接线守卫：判据不能只是"多了一个函数"，旧的那条"看前台 App"的路必须断掉。
    func testContentTypeTagNoLongerReadsTheFrontmostApplication() throws {
        let source = codeOnly(try productSource(named: "Intelligence/RecommendationPresenter.swift"))
        XCTAssertFalse(source.contains("contentTypeTag(bundleID:"),
                       "内容类型标签又回去读前台 App 了 —— 那就是 D-2 本体")
        XCTAssertTrue(source.contains("contentTypeTag(for: entry)"),
                      "标签没有从条目自身取类型")
        // 前台 App 仍然要说，但只能说"当前在 X"。
        XCTAssertTrue(source.contains("当前在"), "前台 App 的信息被顺手删掉了")
    }

    // MARK: - D-8 符号风格

    func testSettingsSidebarSymbolsAreAllOutline() throws {
        let source = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        for filled in ["sparkles", "star.fill", "doc.fill", "gearshape.fill", "hand.raised.fill"] {
            XCTAssertFalse(source.contains("\"\(filled)\""),
                           "设置侧栏混进了实心符号 \(filled)：与同列的描线符号重量差一档（审计 D-8）")
        }
    }

    // MARK: - 夹具

    // MARK: - D-5 存档的双向兼容（新→旧→新）

    /// `D-016` 决定"只加可选字段不升 schema 版本"，理由写在 migrate 的注释里。
    /// 但那个决定此前**只有注释**撑着 —— 没有一条用例钉住"旧版程序读到新存档会怎样"。
    /// 这里用真实写入器产出的存档字节，交给一份按**加字段之前**的形状定义的解码器：
    /// 必须能解出来（Codable 默认忽略多余键），且条目数不缩水。
    func testArchiveWrittenByNewerCodeStillOpensForOlderCode() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("round3-downgrade-\(UUID().uuidString)", isDirectory: true)
        // 目录要自己先建出来：`FileHistoryPersistence` 的清理路径会在移除不存在的目录时抛错，
        // 那会被 XCTest 当成用例自己的失败（本轮第一次跑就是这么红的，不是产品问题）。
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let entry = ClipboardEntry(content: .text("来源 App 要能往返"), timestamp: Date(timeIntervalSince1970: 1_000),
                                   thumbnail: nil, sourceURL: nil, isFavorite: false,
                                   sourceUTIs: ["public.utf8-plain-text"],
                                   sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari",
                                   ocrText: nil)
        let writer = FileHistoryPersistence(rootDirectory: root)
        try writer.save([entry])
        // 存盘是异步的（saveQueue），不 flush 就读文件等于读空气。
        writer.flushPendingSaves()

        let data = try Data(contentsOf: root.appendingPathComponent("history.json"))
        // 新字段确实在文件里（否则下面那次"旧版能读"证明不了任何东西）。
        let json = try JSONSerialization.jsonObject(with: data)
        let payload = try XCTUnwrap(json as? [String: Any])
        let entries = try XCTUnwrap(payload["entries"] as? [[String: Any]])
        XCTAssertEqual(entries.count, 1, "阳性对照：存档里就是 1 条")
        XCTAssertEqual(try XCTUnwrap(entries.first?["sourceAppName"] as? String), "Safari",
                       "新字段没写进存档，那旧版能不能读根本无从判断")

        // 加字段之前的形状（不含 sourceAppBundleID / sourceAppName / ocrText）。
        struct LegacyEntry: Codable {
            let id: UUID
            /// 存档里的时间戳是**字符串**（自定义的 ISO 格式，不是 JSON 数字），
            /// 这里按旧版当时的读法声明成 String —— 这条用例要证的是"多余键不会让旧版解不动"，
            /// 不是重新实现一次日期解码。
            let timestamp: String
            let contentKind: String
            let text: String?
            let sourceUTIs: [String]
        }
        struct LegacyFile: Codable {
            let version: Int
            let entries: [LegacyEntry]
        }
        let legacy = try JSONDecoder().decode(LegacyFile.self, from: data)
        XCTAssertEqual(legacy.version, 1, "版本仍是不升版的 v1（D-016）")
        XCTAssertEqual(legacy.entries.count, 1, "旧形状解码丢条目了")
        XCTAssertEqual(legacy.entries[0].text, "来源 App 要能往返")

        // 再回到当前版本读一次：字段按预期在，不产生不可读状态。
        let reopened = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reopened.count, 1)
        XCTAssertEqual(reopened[0].sourceAppName, "Safari")
    }

    // MARK: - D-6 降采样后的图片要自带 PNG 字节

    /// 降采样分支必须把**新尺寸**的 PNG 字节一起交下去：只给 NSImage 时首次编码会落在
    /// 保存快照（`@MainActor`）或用户按住鼠标拖出的那一瞬间。这里能自动判的是"字节有没有带上"，
    /// 以及"带的是新尺寸那份而不是原来那份大图的"。
    func testDownsampleCarriesPngBytesForTheNewSize() throws {
        let source = codeOnly(try productSource(named: "Utilities/ImageIntakePolicy.swift"))
        XCTAssertTrue(source.contains("StoredImage(downsampled, pngData: png)"),
                      "降采样又回到只给 NSImage 了：首次 PNG 编码会掉回主线程（审计 D-6）")
        XCTAssertFalse(source.contains("return StoredImage(\n            NSImage(cgImage:"),
                       "旧的只包 NSImage 那条返回路径还在")
        XCTAssertTrue(source.contains("NSBitmapImageRep(cgImage: cgImage)"),
                      "新字节是在这条后台路径里算出来的吗？没有的话主线程判据不成立")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp/\(relativePath)")
    }
}
