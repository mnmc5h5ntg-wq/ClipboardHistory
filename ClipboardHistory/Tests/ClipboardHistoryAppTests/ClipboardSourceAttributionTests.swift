import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R-04：从浏览器复制的链接不得被当成"文件"条目。
/// 对应审计探针 P-15：旧实现用 `readObjects(forClasses:[NSURL.self], options:nil)`，
/// `public.url` 里的 http(s) 也命中，且文件判定优先于文本，于是回写必然失败
/// （`fileExists(atPath: url.path)` 对 `https://host/page` 取 `/page`）。
final class ClipboardIntakeURLKindTests: XCTestCase {
    private func pasteboardWithBrowserLikeLink(_ string: String) throws -> NSPasteboard {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.link.\(UUID().uuidString)"))
        pasteboard.clearContents()
        let item = NSPasteboardItem()
        item.setString(string, forType: .string)
        item.setString(string, forType: NSPasteboard.PasteboardType(rawValue: "public.url"))
        let wrote = pasteboard.writeObjects([item])
        XCTAssertTrue(wrote, "测试夹具应能写入命名 pasteboard")
        return pasteboard
    }

    func testLinkIsRecordedAsTextNotFile() throws {
        let link = "https://example.com/page?a=1&b=2"
        var intake = ClipboardIntake(pasteboard: try pasteboardWithBrowserLikeLink(link))
        intake.markChangeCount(-1)
        let entry = try XCTUnwrap(intake.readChangedEntry())
        // 不把 entry.content 打进断言消息：注入失效时它是用户真实剪贴板内容。
        XCTAssertTrue(entry.content == .text(link), "链接应作为文本记录，而不是 .file（类型：\(kind(of: entry.content))）")
    }

    func testWebURLOnlyPasteboardIsNotMistakenForFileEntry() throws {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.weburl.\(UUID().uuidString)"))
        pasteboard.clearContents()
        let url = try XCTUnwrap(URL(string: "https://example.com/only-url"))
        XCTAssertTrue(pasteboard.writeObjects([url as NSURL]))

        var intake = ClipboardIntake(pasteboard: pasteboard)
        intake.markChangeCount(-1)
        // 以前这里是 `guard … else { return }`（注释写着"不记也算通过"）：断言永远不可能失败，
        // intake 回归成任何形状都是绿的（审计 N-4）。现在把**两侧**都钉住：
        // ① 只含非文件 NSURL 的剪贴板按当前设计不产生条目 —— `readFileURLs` 限定
        //    `.urlReadingFileURLsOnly`（审计 P-15 的修法），而这类剪贴板没有字符串可读；
        // ② 万一它开始产生条目，也绝不允许是"非文件的 .file 条目"（P-15 的原始缺陷）。
        // 若哪天决定"把 public.url 记成文本条目"，①会红，那时连同本文件的姊妹用例一起改。
        let recorded = intake.readChangedEntry()
        XCTAssertNil(recorded, "只含 Web URL 的剪贴板当前不应产生条目；这条红了说明 intake 行为变了")
        if let entry = recorded, case .file(let fileURL) = entry.content, !fileURL.isFileURL {
            XCTFail("Web URL 被当成文件条目：\(fileURL.absoluteString)")
        }
        if let entry = recorded {
            XCTAssertTrue(entry.content != .file(url), "不应记成该 Web URL 的文件条目")
        }
    }

    func testRealFileURLStillBecomesFileEntry() throws {
        let file = URL(fileURLWithPath: FileManager.default.temporaryDirectory.path)
            .appendingPathComponent("存在的文件-\(UUID().uuidString).txt")
        try "内容".write(to: file, atomically: true, encoding: .utf8)
        defer { try? FileManager.default.removeItem(at: file) }

        let pasteboard = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.file.\(UUID().uuidString)"))
        pasteboard.clearContents()
        XCTAssertTrue(pasteboard.writeObjects([file as NSURL]))

        var intake = ClipboardIntake(pasteboard: pasteboard)
        intake.markChangeCount(-1)
        let entry = try XCTUnwrap(intake.readChangedEntry())
        let recordedPath: String
        switch entry.content {
        case .file(let url): recordedPath = url.path
        default: return XCTFail("Finder 复制的文件应记为 .file，实际类型：\(kind(of: entry.content))")
        }
        XCTAssertEqual(recordedPath, file.path, "Finder 复制的文件仍应记为文件条目")
    }

    /// 端到端：链接类条目回写剪贴板不得报"文件已移动或删除"。
    func testLinkEntryWritesBackWithoutFileError() async throws {
        let link = "https://example.com/roundtrip?x=1"
        let pasteboard = try pasteboardWithBrowserLikeLink(link)
        var intake = ClipboardIntake(pasteboard: pasteboard)
        intake.markChangeCount(-1)
        let entry = try XCTUnwrap(intake.readChangedEntry())

        let content = entry.content
        let changeCount = try await MainActor.run {
            let writer = SystemClipboardWriter(pasteboard: NSPasteboard(
                name: NSPasteboard.Name("clipboardhistory.tests.write.\(UUID().uuidString)")
            ))
            return try writer.write(content)
        }
        XCTAssertGreaterThan(changeCount, 0)
    }
}

/// 注入的 pasteboard 必须真的被读取路径使用（旧写法各方法默认 `.general`，
/// 会静默读到用户真实剪贴板内容）。
final class ClipboardIntakeInjectionTests: XCTestCase {
    func testInjectedPasteboardIsTheOneActuallyRead() throws {
        let marker = "注入专用-\(UUID().uuidString)"
        let pasteboard = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.inject.\(UUID().uuidString)"))
        pasteboard.clearContents()
        pasteboard.setString(marker, forType: .string)

        var intake = ClipboardIntake(pasteboard: pasteboard)
        let entry = try XCTUnwrap(intake.refresh(), "refresh() 必须读注入的 pasteboard，而不是 .general")
        XCTAssertTrue(entry.content == .text(marker), "refresh() 没有读注入的 pasteboard（类型：\(kind(of: entry.content))）")

        intake.markChangeCount(-1)
        let changed = try XCTUnwrap(intake.readChangedEntry())
        XCTAssertTrue(changed.content == .text(marker), "readChangedEntry() 没有读注入的 pasteboard")
    }

    func testExplicitOverrideStillWins() throws {
        let injected = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.injected.\(UUID().uuidString)"))
        injected.clearContents()
        injected.setString("injected", forType: .string)
        let override = NSPasteboard(name: NSPasteboard.Name("clipboardhistory.tests.override.\(UUID().uuidString)"))
        override.clearContents()
        override.setString("override", forType: .string)

        var intake = ClipboardIntake(pasteboard: injected)
        XCTAssertTrue(intake.refresh(from: override)?.content == .text("override"), "显式 from: 覆盖必须优先")
    }
}

/// 只返回内容类型名，避免把可能来自真实剪贴板的正文写进测试日志。
private func kind(of content: ClipboardEntryContent) -> String {
    switch content {
    case .text: return "text"
    case .image: return "image"
    case .file: return "file"
    case .files: return "files"
    }
}

/// R-05：重复复制把条目提升到顶部时，不得丢掉来源 App 归因。
/// 对应审计探针 P-01：`HistoryStore.entry(from:replacingWith:)` 重建条目时
/// 没带 `sourceAppBundleID`/`sourceAppName`，于是 appAffinity 因子与
/// "回到 X"标签对任何被复制过两次以上的内容永久失效。
@MainActor
final class SourceAttributionTests: XCTestCase {
    private func intake(text: String, bundleID: String? = nil, appName: String? = nil) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: bundleID,
            sourceAppName: appName
        )
    }

    private func loadedEntry(text: String, bundleID: String, appName: String) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date().addingTimeInterval(-3600),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: [],
            sourceAppBundleID: bundleID,
            sourceAppName: appName
        )
    }

    private func makeStore(entriesToLoad: [ClipboardEntry]) -> HistoryStore {
        HistoryStore(
            intake: ClipboardIntake(pasteboard: .general),
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(entriesToLoad: entriesToLoad),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    func testPromotionFallsBackToPreviousSourceWhenIntakeCarriesNone() {
        let store = makeStore(entriesToLoad: [
            loadedEntry(text: "hello", bundleID: "com.apple.Safari", appName: "Safari"),
        ])
        store.add(intake(text: "hello"), timestamp: Date())

        let promoted = store.entries.first
        XCTAssertEqual(promoted?.content, .text("hello"))
        XCTAssertEqual(promoted?.sourceAppBundleID, "com.apple.Safari", "P-01 修复：提升不得丢来源")
        XCTAssertEqual(promoted?.sourceAppName, "Safari")
    }

    func testPromotionPrefersTheNewCopySourceApp() {
        let store = makeStore(entriesToLoad: [
            loadedEntry(text: "shared", bundleID: "com.apple.Safari", appName: "Safari"),
        ])
        store.add(intake(
            text: "shared",
            bundleID: "com.tencent.xinWeChat",
            appName: "WeChat"
        ), timestamp: Date())

        XCTAssertEqual(store.entries.first?.sourceAppBundleID, "com.tencent.xinWeChat", "新一次的来源应覆盖旧来源")
        XCTAssertEqual(store.entries.first?.sourceAppName, "WeChat")
    }

    func testFreshEntryKeepsRecordedSourceWithoutTouchingWorkspace() {
        let entry = intake(text: "abc", bundleID: "com.apple.Terminal", appName: "Terminal")
            .makeHistoryEntry(timestamp: Date(timeIntervalSince1970: 1_000))
        XCTAssertEqual(entry.sourceAppBundleID, "com.apple.Terminal")
        XCTAssertEqual(entry.sourceAppName, "Terminal")
    }
}
