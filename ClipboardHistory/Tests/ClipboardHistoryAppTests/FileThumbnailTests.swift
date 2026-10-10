import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 图片文件条目的行内缩略图（用户报的缺陷：详情区能看到图，左侧列表只有一个通用文档符号）。
///
/// 判据分三层：① 该不该补（真值表，含"已经有缩略图就别再动"）；
/// ② 补出来的是什么（真从磁盘解一张，尺寸有界、非图片解不出）；
/// ③ 写回是否只有一条路（条目已消失/已有缩略图时不许覆盖，且必须落盘）。
/// 全部用临时目录，绝不碰 `~/Library/Application Support/时间剪史/`（D-002）。
@MainActor
final class FileThumbnailTests: XCTestCase {

    private func makeStore(entriesToLoad: [ClipboardEntry] = []) -> (HistoryStore, RecordingHistoryPersistence) {
        let recorder = RecordingHistoryPersistence(entriesToLoad: entriesToLoad)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: recorder,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        return (store, recorder)
    }

    private func fileEntry(url: URL, thumbnail: StoredImage? = nil) -> ClipboardEntry {
        ClipboardEntry(content: .file(url), timestamp: Date(timeIntervalSince1970: 1),
                       thumbnail: thumbnail, sourceURL: url, sourceUTIs: ["public.file-url"])
    }

    /// 临时目录 + 注册清理。刻意不用 `setUpWithError` 存字段：那个钩子在 Swift 6 的
    /// `@MainActor` 测试类里是非隔离的，直接写属性会破 0 告警闸门。
    private func makeTempDirectory() throws -> URL {
        let dir = FileManager.default.temporaryDirectory
            .appendingPathComponent("file-thumbnail-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: dir) }
        return dir
    }

    /// 写一个真实的 PNG 到临时目录，返回它的 URL。
    private func writePNG(in directory: URL, named name: String, width: Int, height: Int) throws -> URL {
        let url = directory.appendingPathComponent(name)
        guard let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
        ) else { throw XCTSkip("造不出位图") }
        for y in 0..<height {
            for x in 0..<width {
                rep.setColor(NSColor(red: CGFloat(x) / CGFloat(max(width, 1)),
                                     green: CGFloat(y) / CGFloat(max(height, 1)),
                                     blue: 0.5, alpha: 1), atX: x, y: y)
            }
        }
        let png = try XCTUnwrap(rep.representation(using: .png, properties: [:]))
        try png.write(to: url)
        return url
    }

    // MARK: - ① 该不该补

    func testShouldAttachOnlyForImageFilesWithoutAThumbnail() throws {
        let png = URL(fileURLWithPath: "/tmp/例子.png")
        XCTAssertTrue(FileThumbnailPolicy.shouldAttachThumbnail(for: fileEntry(url: png)),
                      "图片文件没有缩略图正是缺陷的形状，必须判 true")
        XCTAssertFalse(FileThumbnailPolicy.shouldAttachThumbnail(
            for: fileEntry(url: png, thumbnail: try makeStoredImage())),
            "已经有缩略图就别再去磁盘上解一张：白跑一趟，还会覆盖剪贴板带来的那一份")
        XCTAssertFalse(FileThumbnailPolicy.shouldAttachThumbnail(
            for: fileEntry(url: URL(fileURLWithPath: "/tmp/说明.md"))),
            "非图片扩展名不该去解")
        XCTAssertFalse(FileThumbnailPolicy.shouldAttachThumbnail(
            for: ClipboardEntry(content: .files([png, URL(fileURLWithPath: "/tmp/b.png")]),
                               timestamp: Date(), thumbnail: nil, sourceURL: nil,
                               sourceUTIs: ["public.file-url"])),
            "多文件条目没有单一目标文件可解")
        XCTAssertFalse(FileThumbnailPolicy.shouldAttachThumbnail(
            for: ClipboardEntry(content: .text("hi"), timestamp: Date(), thumbnail: nil,
                               sourceURL: nil, sourceUTIs: ["public.utf8-plain-text"])))
        XCTAssertFalse(FileThumbnailPolicy.shouldAttachThumbnail(
            for: fileEntry(url: URL(string: "https://example.com/a.png")!)),
            "网页地址不是本机文件，不许去读盘")
    }

    // MARK: - ② 补出来的是什么

    func testThumbnailIsDecodedFromDiskAndSizeBounded() throws {
        let dir = try makeTempDirectory()
        let url = try writePNG(in: dir, named: "大图.png", width: 1200, height: 900)
        let thumb = try XCTUnwrap(FileThumbnailPolicy.thumbnail(for: url),
                                  "真实 PNG 解不出缩略图，行里就还是那个文档符号")
        let image = try XCTUnwrap(thumb.nsImage)
        let longest = Int(max(image.size.width, image.size.height))
        print("THUMB \(Int(image.size.width))x\(Int(image.size.height)) bytes=\(thumb.pngData()?.count ?? -1)")
        XCTAssertLessThanOrEqual(longest, FileThumbnailPolicy.maxPixel,
                                 "缩略图尺寸失控：行首只有 32pt，落盘全尺寸图等于复制用户文件")
        XCTAssertGreaterThan(longest, 0)
        XCTAssertNotNil(thumb.pngData(), "缩略图必须自带 PNG 字节（同 D-6 的理由：别把首次编码留给主线程）")
    }

    func testThumbnailReturnsNilForUnreadableOrNonImage() throws {
        let dir = try makeTempDirectory()
        XCTAssertNil(FileThumbnailPolicy.thumbnail(for: dir.appendingPathComponent("不存在.png")),
                     "文件不存在必须安静地返回 nil，不能抛、不能打日志刷屏")
        let text = dir.appendingPathComponent("说明.txt")
        try "只是一段文本".data(using: .utf8)!.write(to: text)
        XCTAssertNil(FileThumbnailPolicy.thumbnail(for: text), "非图片文件解不出缩略图")
    }

    // MARK: - ③ 写回

    func testApplyThumbnailWritesOnceAndPersists() throws {
        let dir = try makeTempDirectory()
        let url = try writePNG(in: dir, named: "写回.png", width: 600, height: 400)
        let entry = fileEntry(url: url)
        // 用"存档里已有这条"进 store：`perform(.refresh)` 是**轮询剪贴板**（会读真实粘贴板），
        // 不是重新载入，拿它当夹具会凭空多出一条条目来。
        let (store, recorder) = makeStore(entriesToLoad: [entry])
        XCTAssertEqual(store.entries.map(\.id), [entry.id], "夹具没按预期载入那一条")
        let savesBefore = recorder.savedEntriesSnapshots.count

        let thumb = try XCTUnwrap(FileThumbnailPolicy.thumbnail(for: url))
        XCTAssertTrue(store.applyThumbnail(entryID: entry.id, thumbnail: thumb))
        XCTAssertNotNil(store.entries.first?.thumbnail, "写回后条目里还是 nil")
        XCTAssertGreaterThan(recorder.savedEntriesSnapshots.count, savesBefore,
                             "改了条目不落盘 = 重启又变回没有预览")

        XCTAssertFalse(store.applyThumbnail(entryID: entry.id, thumbnail: thumb),
                       "第二次不许覆盖：后台任务可能和别的写回撞上")
        XCTAssertFalse(store.applyThumbnail(entryID: UUID(), thumbnail: thumb),
                       "条目已经不在了还写 = 给不存在的条目补数据")
    }

    /// 端到端：`add` 一条图片文件后，缩略图应当在后台补上。
    /// 这条测的是**接线** —— 只测真值表的话，"判据对但没人调用"照样能全绿。
    func testAddAttachesThumbnailAsynchronously() throws {
        let dir = try makeTempDirectory()
        let url = try writePNG(in: dir, named: "端到端.png", width: 800, height: 600)
        let (store, _) = makeStore()
        store.add(ClipboardIntake.Entry(
            content: .file(url), thumbnail: nil, sourceUTIs: ["public.file-url"]
        ), timestamp: Date(timeIntervalSince1970: 7), isUserInitiated: true)

        let deadline = Date().addingTimeInterval(3)
        while store.entries.first?.thumbnail == nil && Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertNotNil(store.entries.first?.thumbnail,
                        "3 秒内没补上缩略图：后台任务没排、或写回没回主线程")
    }

    /// 启动回填必须存在并被调用（老历史里那些没有预览的条目靠它）。
    func testStartupBackfillIsWired() throws {
        let shell = codeOnly(try productSource(named: "Managers/ApplicationShell.swift"))
        XCTAssertTrue(shell.contains("attachMissingFileThumbnails()"),
                      "启动时不回填，老条目的行内预览会永远空着")
        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        XCTAssertTrue(store.contains("attachFileThumbnailIfNeeded(for: entry)"),
                      "新复制的图片文件条目没接上补图")
    }

    /// 行首视觉列必须"有缩略图就用图"。补上了缩略图但行里仍然画符号，用户看到的还是原缺陷。
    func testRowLeadingVisualPrefersTheThumbnail() throws {
        let rows = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        let afterFile = try XCTUnwrap(
            rows.components(separatedBy: "case .file:").dropFirst().first,
            "行首视觉列里没有 .file 分支"
        )
        let fileBranch = afterFile.components(separatedBy: "case .files:").first ?? afterFile
        XCTAssertTrue(fileBranch.contains("entry.thumbnail"),
                      ".file 分支没有优先用缩略图：补了图也看不见")
        XCTAssertTrue(fileBranch.contains("ThumbnailImage"),
                      ".file 分支不再画缩略图，退回符号了")
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
