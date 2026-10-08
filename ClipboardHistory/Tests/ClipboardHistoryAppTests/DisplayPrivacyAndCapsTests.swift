import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R-22 / R-41 / R-42 / R-43 的回归守卫。
@MainActor
final class DisplayPrivacyAndCapsTests: XCTestCase {
    private func textEntry(_ text: String, age: TimeInterval = 0) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date().addingTimeInterval(-age),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: []
        )
    }

    // MARK: R-43 菜单栏脱敏标签

    func testMenuLabelShowsShortPreviewForOrdinaryText() {
        let entry = textEntry(String(repeating: "甲", count: 100))
        let label = EntryPresentation.menuLabel(for: entry)
        XCTAssertTrue(label.hasPrefix("甲甲甲"), label)
        XCTAssertEqual(label.count, 24, "23 字 + 省略号：够认出是哪条，不够旁人读完")
    }

    func testMenuLabelHidesSecretLookingContent() {
        let entry = textEntry("ghp_" + String(repeating: "A", count: 36) + " 我的 github 令牌")
        let label = EntryPresentation.menuLabel(for: entry)
        XCTAssertTrue(label.contains("疑似敏感内容"), label)
        XCTAssertFalse(label.contains("ghp_"), "令牌本身不得出现在菜单栏：\(label)")
        XCTAssertTrue(label.contains("刚刚"), label)
    }

    func testMenuLabelMasksSecretFoundOnlyInImageOCRText() {
        let image = try! makeStoredImage(size: NSSize(width: 4, height: 4))
        let entry = ClipboardEntry(
            content: .image(image),
            timestamp: Date(),
            thumbnail: image,
            sourceURL: nil,
            sourceUTIs: [],
            ocrText: "-----BEGIN PRIVATE KEY----- 以及后续内容"
        )
        let label = EntryPresentation.menuLabel(for: entry)
        XCTAssertTrue(label.contains("疑似敏感内容"), label)
        XCTAssertTrue(label.contains("图片"), label)
    }

    func testRelativeTimeBuckets() {
        let now = Date(timeIntervalSince1970: 1_700_000_000)
        XCTAssertEqual(EntryPresentation.relativeTime(now.addingTimeInterval(-10), now: now), "刚刚")
        XCTAssertEqual(EntryPresentation.relativeTime(now.addingTimeInterval(-120), now: now), "2 分钟前")
        XCTAssertEqual(EntryPresentation.relativeTime(now.addingTimeInterval(-7_200), now: now), "2 小时前")
        XCTAssertEqual(EntryPresentation.relativeTime(now.addingTimeInterval(-172_800), now: now), "2 天前")
    }

    func testParentDirectoryLabelHidesAbsolutePrefix() throws {
        let url = URL(fileURLWithPath: "/Users/someone/Documents/项目/a.swift")
        XCTAssertEqual(url.parentDirectoryLabel, "…/项目")
        XCTAssertEqual(URL(fileURLWithPath: "/").parentDirectoryLabel, "…")
    }

    // MARK: R-22 体积上限

    func testOversizedTextIsTruncatedWithMarker() {
        let huge = String(repeating: "x", count: ClipboardIntake.maxTextCharacters + 5_000)
        let bounded = ClipboardIntake.bounded(huge)
        XCTAssertLessThan(bounded.count, huge.count)
        XCTAssertTrue(bounded.contains("已截断保存"))

        XCTAssertEqual(ClipboardIntake.bounded("正常长度"), "正常长度")
    }

    func testPreviewReadIsCapped() throws {
        let directory = try makeTemporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let file = directory.appendingPathComponent("big.txt")
        let payload = String(repeating: "0123456789\n", count: 60_000)   // ~660KB
        try payload.write(to: file, atomically: true, encoding: .utf8)

        let payloadResult = try XCTUnwrap(MediaLoader.filePreviewPayloadSync(url: file))
        guard case .text(let text) = payloadResult else { return XCTFail("应走文本预览分支") }
        XCTAssertLessThan(text.utf8.count, MediaLoader.maxPreviewTextBytes + 2_000)
        XCTAssertTrue(text.contains("预览仅读取前"), "必须说明看到的是截断预览")
    }

    // MARK: R-41 视频预览计划

    func testVideoPreviewPlanFallsBackToInformationUnavailable() throws {
        let missing = URL(fileURLWithPath: "/tmp/definitely-not-a-real-video-\(UUID().uuidString).mov")
        let preview = FilePreview(url: missing, thumbnail: nil, content: .video, videoAspectRatio: nil)
        XCTAssertEqual(VideoPreviewPlan.resolve(preview: preview), .informationUnavailable)

        let withRatio = FilePreview(url: missing, thumbnail: nil, content: .video, videoAspectRatio: 1.777)
        XCTAssertEqual(VideoPreviewPlan.resolve(preview: withRatio), .player(aspectRatio: 1.777))

        let nonsense = FilePreview(url: missing, thumbnail: nil, content: .video, videoAspectRatio: .nan)
        XCTAssertEqual(VideoPreviewPlan.resolve(preview: nonsense), .informationUnavailable)
    }

    // MARK: R-42 只读元信息拿尺寸

    func testImagePropertiesReadsSizeWithoutDecoding() throws {
        let directory = try makeTemporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let image = NSImage(size: NSSize(width: 1234, height: 777))
        image.lockFocus()
        NSColor.systemGreen.setFill()
        NSRect(origin: .zero, size: image.size).fill()
        image.unlockFocus()
        let tiff = try XCTUnwrap(image.tiffRepresentation)
        let bitmap = try XCTUnwrap(NSBitmapImageRep(data: tiff))
        let png = try XCTUnwrap(bitmap.representation(using: .png, properties: [:]))
        let file = directory.appendingPathComponent("shot.png")
        try png.write(to: file)

        let size = try XCTUnwrap(ImageProperties.pixelSize(of: file))
        // Retina 下 lockFocus 生成的位图是 2x，断言 against 真实像素而非点尺寸
        XCTAssertEqual(Int(size.width), bitmap.pixelsWide)
        XCTAssertEqual(Int(size.height), bitmap.pixelsHigh)
        XCTAssertGreaterThan(size.width, 0)
    }
}
