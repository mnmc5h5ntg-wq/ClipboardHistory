import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R555 / BACKLOG 632：**「在用户看到那一行之前，不许去受保护目录拿字节」**的计数器证人。
///
/// 这条判据为什么不写成日志正则：弹窗的根因是采集/预览路径主动读桌面文件，而「日志里没打印」
/// 与「没发生」是两件事（账本 R470/R536 同一族坏法）。所以全部断言读
/// `ProtectedFileAccessLedger` 数出来的**次数**；而「0 次」这句话要先由
/// `testPreviewReadIsSeenByTheLedger` 证明这把尺**读得到非 0** 才算数。
///
/// 管线级（AGENTS.md C-1）：第 1 格从**产品入口** `ClipboardIntake.refresh(from:)` 进去，
/// 不是直接调 `MediaLoader`。
/// 数据安全：一律命名私有 `NSPasteboard`，从不碰 `NSPasteboard.general`；夹具文件一律写在
/// `FileManager.default.temporaryDirectory` 下自己的临时目录 —— **不拿用户真实桌面/文档路径做样本**，
/// 读数里也不许出现路径（第 4 格专门把这条钉成函数）。
@MainActor
final class ProtectedFileAccessTests: XCTestCase {

    private func makePasteboard() -> NSPasteboard {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        return pasteboard
    }

    /// 临时目录里的夹具：返回**这个测试自己创建**的文本文件 URL。
    private func makeTextFixture(named name: String, content: String) throws -> URL {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent("r555-protected-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: directory) }
        let url = directory.appendingPathComponent(name)
        try content.data(using: .utf8)!.write(to: url, options: .atomic)
        return url
    }

    /// 三行短文本：样本一次读完（`data.count < textSampleLimit`）⇒ 估高度不需要再问大小。
    private func smallContent() -> String { "第一行\n第二行\n第三行\n" }

    /// 纯 ASCII 的大文件（≥ `textSampleLimit`）：非 ASCII 在 32KB 处截断会切开多字节字符，
    /// 那时 `String(data:encoding:.utf8)` 返回 nil，这一格就没有对象了 —— 这不是我要判的那件事。
    private func truncatedContent() -> String {
        (0..<5_000).map { "line \($0) padded ascii text\n" }.joined()
    }

    private func attach(_ text: String, named name: String) {
        let reading = XCTAttachment(string: text)
        reading.name = name
        reading.lifetime = .keepAlways
        add(reading)
    }

    // MARK: - 1 采集路径：记 URL，不读文件

    /// 从产品入口复制一个文件 URL ⇒ 条目记下来了，而**那个文件一次都没被打开**。
    func testIntakeRecordsAFileURLWithoutReadingTheFile() throws {
        let url = try makeTextFixture(named: "desktop-note.txt", content: smallContent())

        let pasteboard = makePasteboard()
        pasteboard.writeObjects([url as NSURL])
        var intake = ClipboardIntake(pasteboard: pasteboard)
        let entry = try XCTUnwrap(intake.refresh(from: pasteboard), "采集管线没有产出条目")

        guard case .file(let recorded) = entry.content else {
            XCTFail("条目不是文件内容：\(String(describing: entry.content))")
            return
        }
        XCTAssertEqual(recorded, url, "采集记下的 URL 与被复制的那一个不一致")
        let reads = ProtectedFileAccessLedger.count(for: url)
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_INTAKE", for: url),
               named: "PROTECTED_READS_AT_INTAKE")
        XCTAssertEqual(reads, 0,
            "复制这一步就对受保护目录发生了 \(reads) 次访问 ⇒ 采集路径主动读文件（632 的原形、TCC 弹窗的来源）")
    }

    // MARK: - 2 正/负两臂：先证明尺读得到非 0

    func testPreviewReadIsSeenByTheLedger() throws {
        let url = try makeTextFixture(named: "sample.txt", content: smallContent())

        XCTAssertEqual(ProtectedFileAccessLedger.count(for: url), 0,
                       "还没预览就读到非 0 ⇒ 夹具 URL 被别的判据共用（每格该有自己的临时目录）")
        XCTAssertNotNil(MediaLoader.filePreviewPayloadSync(url: url),
                        "文本预览没读到内容 ⇒ 这一格没有对象")
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_PREVIEW", for: url),
               named: "PROTECTED_READS_AT_PREVIEW")
        let sampled = ProtectedFileAccessLedger.count(.previewTextSample, for: url)
        XCTAssertEqual(sampled, 1,
            "预览确实读了文本，计数器却记 \(sampled) 次 ⇒ 尺读不到自己的对象，上一条的 0 是假绿")
    }

    // MARK: - 3 本轮产品改动：小文件估高度不再多问一次路径

    /// 样本没读满上限 ⇒ 整份文件都已经在手里了，不该再 `attributesOfItem` 探一次；
    /// 读满上限那一档仍必须探（否则这格是被**删掉**的，不是被**省掉**的）。
    func testHeightEstimateSkipsTheSizeStatWhenTheSampleIsWhole() throws {
        let small = try makeTextFixture(named: "short.txt", content: smallContent())
        let big = try makeTextFixture(named: "long.txt", content: truncatedContent())
        XCTAssertGreaterThanOrEqual(try Data(contentsOf: big).count,
                                    MultiFilePreviewLayout.textSampleLimit,
                                    "夹具没超过取样上限 ⇒ 这一格测不到「读满之后要探大小」那一支")

        let smallHeight = MultiFilePreviewLayout.preferredHeight(for: small, availableWidth: 420)
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_LAYOUT_SMALL", for: small)
               + " height=\(String(format: "%.1f", smallHeight))",
               named: "PROTECTED_READS_AT_LAYOUT_SMALL")
        let smallSamples = ProtectedFileAccessLedger.count(.layoutTextSample, for: small)
        let smallStats = ProtectedFileAccessLedger.count(.layoutFileSizeStat, for: small)
        XCTAssertEqual(smallSamples, 1, "估高度应当只开一次文件取样，读到 \(smallSamples) 次")
        XCTAssertEqual(smallStats, 0,
            "样本没读满的小文件还是去 stat 了一次路径 ⇒ 同一份渲染里对受保护目录多问了一趟")

        let bigHeight = MultiFilePreviewLayout.preferredHeight(for: big, availableWidth: 420)
        attach(ProtectedFileAccessLedger.reading("PROTECTED_READS_AT_LAYOUT_TRUNCATED", for: big)
               + " height=\(String(format: "%.1f", bigHeight))",
               named: "PROTECTED_READS_AT_LAYOUT_TRUNCATED")
        let bigStats = ProtectedFileAccessLedger.count(.layoutFileSizeStat, for: big)
        XCTAssertEqual(bigStats, 1,
            "读满上限的样本仍然需要知道总大小；这一格读到 \(bigStats) 次 ⇒ "
            + "省 stat 是把探路整格删了，不是按条件省的")
        XCTAssertGreaterThan(bigHeight, smallHeight,
            "大文件的估高度没有更高（\(String(format: "%.1f", bigHeight)) vs "
            + "\(String(format: "%.1f", smallHeight))）⇒ 覆盖度那一段被改坏了，不是被省掉的")
    }

    // MARK: - 4 隐私红线：读数里不许出现路径

    func testLedgerReadingCarriesNoPath() throws {
        let url = try makeTextFixture(named: "privacy-canary.txt", content: smallContent())
        _ = MediaLoader.filePreviewPayloadSync(url: url)
        let line = ProtectedFileAccessLedger.reading("PROTECTED_READS_PRIVACY", for: url)
        XCTAssertFalse(line.contains("/"), "读数里出现了斜杠 ⇒ 疑似把路径写进了日志：\(line)")
        XCTAssertFalse(line.contains("privacy-canary"), "读数里出现了文件名：\(line)")
        XCTAssertFalse(line.contains(url.path), "读数里出现了路径：\(line)")
    }
}
