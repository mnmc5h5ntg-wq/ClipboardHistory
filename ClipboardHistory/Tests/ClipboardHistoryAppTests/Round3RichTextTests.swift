import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 §5 F-2（富文本保真 RTF / HTML）的判据。
///
/// 三条层次都要有，缺一条就会留下假绿：
/// - 纯函数：字节上限与"预算顺序"（超限是**整份丢**而不是截断，截断的 RTF 是坏结构）；
/// - 产品入口：`ClipboardIntake` 真的从剪贴板抓到了表示、`SystemClipboardWriter` 真的写回去了；
/// - 存档：写盘再读回来表示还在，而且**开关关着时不抓**（默认关这件事必须有判据，
///   否则"体积翻倍"就成了产品替用户做的决定）。
///
/// 一律用命名剪贴板与临时目录，不碰用户的真实剪贴板与 `~/Library/Application Support/时间剪史/`。
@MainActor
final class Round3RichTextTests: XCTestCase {
    private let pasteboardName = NSPasteboard.Name("Round3RichText-\(UUID().uuidString)")

    private func makeSuite() -> (UserDefaults, String) {
        let name = "Round3F2-\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: name)!
        return (defaults, name)
    }

    private func cleanUp(_ name: String) {
        UserDefaults.standard.removePersistentDomain(forName: name)
    }

    private func writer(_ pasteboard: NSPasteboard) -> SystemClipboardWriter {
        SystemClipboardWriter(pasteboard: pasteboard)
    }

    // MARK: - 上限与顺序（纯函数）

    func testOversizedRepresentationsAreDroppedWholeNotTruncated() {
        XCTAssertTrue(RichTextPolicy.accepts(bytes: 1_024, runningTotal: 0))
        XCTAssertFalse(RichTextPolicy.accepts(bytes: 0, runningTotal: 0), "空表示不算有富文本")
        XCTAssertFalse(RichTextPolicy.accepts(bytes: RichTextPolicy.maximumBytesPerRepresentation + 1,
                                              runningTotal: 0),
                       "单份超上限还收 = 存档被一个 200 页的 Word 复制撑爆")
        // 单份没超，但加上它就把总额超了 —— 也不行
        XCTAssertFalse(RichTextPolicy.accepts(bytes: RichTextPolicy.maximumTotalBytes, runningTotal: 1))
    }

    func testBudgetGoesToRTFFirst() {
        let rtf = Data(repeating: 0x52, count: 1_000)
        let html = Data(repeating: 0x48, count: 1_000)
        let both = RichTextPolicy.capture { type in
            type == RichTextPolicy.rtfType ? rtf : (type == RichTextPolicy.htmlType ? html : nil)
        }
        XCTAssertEqual(both?.rtf, rtf)
        XCTAssertEqual(both?.html, html)

        // 总额只够一份时，留下的必须是 RTF（被支持得最广的那一份）
        let hugeHTML = Data(repeating: 0x48, count: RichTextPolicy.maximumTotalBytes)
        let onlyRTF = RichTextPolicy.capture { type in
            type == RichTextPolicy.rtfType ? rtf : (type == RichTextPolicy.htmlType ? hugeHTML : nil)
        }
        XCTAssertEqual(onlyRTF?.rtf, rtf, "RTF 被挤掉了：预算顺序不对")
        XCTAssertNil(onlyRTF?.html)

        // 两份都超限 ⇒ 没有富文本，而不是"返回一个空壳"
        let none = RichTextPolicy.capture { _ in Data(repeating: 1, count: RichTextPolicy.maximumBytesPerRepresentation + 1) }
        XCTAssertNil(none)

        // 开关关：什么都不取
        XCTAssertNil(RichTextPolicy.capture(enabled: false) { _ in rtf })
    }

    func testDefaultIsOffAndItIsAnExplicitChoice() {
        let (defaults, name) = makeSuite()
        defer { cleanUp(name) }
        XCTAssertFalse(RichTextPolicy.isEnabled(defaults: defaults),
                       "富文本保真必须默认关：开了等于每条文本记录多存 2 份表示")
        RichTextPolicy.setEnabled(true, defaults: defaults)
        XCTAssertTrue(RichTextPolicy.isEnabled(defaults: defaults))
        RichTextPolicy.setEnabled(false, defaults: defaults)
        XCTAssertFalse(RichTextPolicy.isEnabled(defaults: defaults))
    }

    // MARK: - 采集：走 ClipboardIntake 这个产品入口

    func testIntakeCapturesRichTextOnlyWhenTheSwitchIsOn() throws {
        let (defaults, name) = makeSuite()
        defer { cleanUp(name) }
        let pasteboard = try XCTUnwrap(NSPasteboard(name: pasteboardName))
        defer { pasteboard.clearContents() }

        let rtfData = Data("{\\rtf1\\b 加粗}".utf8)
        func fill() {
            pasteboard.clearContents()
            pasteboard.declareTypes([.string, RichTextPolicy.rtfType, RichTextPolicy.htmlType], owner: nil)
            pasteboard.setString("加粗的文字", forType: .string)
            pasteboard.setData(rtfData, forType: RichTextPolicy.rtfType)
            pasteboard.setData(Data("<b>加粗的文字</b>".utf8), forType: RichTextPolicy.htmlType)
        }

        // 关着：只拿纯文本，且条目里没有富文本载荷
        RichTextPolicy.setEnabled(false, defaults: defaults)
        fill()
        var intake = ClipboardIntake(pasteboard: pasteboard)
        intake.policyDefaults = defaults
        let off = try XCTUnwrap(intake.refresh(from: pasteboard), "开关关着时纯文本仍要照常入库")
        XCTAssertNil(off.richText, "没打开也去抓富文本 = 默认关这个决定没生效")

        // 打开：两份表示都跟着走，并且活到历史条目上
        RichTextPolicy.setEnabled(true, defaults: defaults)
        fill()
        var richIntake = ClipboardIntake(pasteboard: pasteboard)
        richIntake.policyDefaults = defaults
        let on = try XCTUnwrap(richIntake.refresh(from: pasteboard))
        XCTAssertEqual(on.richText?.rtf, rtfData, "RTF 没被抓到")
        XCTAssertEqual(on.richText?.html, Data("<b>加粗的文字</b>".utf8))
        let entry = on.makeHistoryEntry(timestamp: Date(timeIntervalSince1970: 5))
        XCTAssertEqual(entry.richText?.rtf, rtfData, "采集到了却没活到条目对象上")
    }

    // MARK: - 写回：审计点名的那条"RTF 往返后写回 pasteboard 含 rtf 类型"

    func testWriteBackRegistersRTFHTMLThenPlainString() throws {
        let pasteboard = try XCTUnwrap(NSPasteboard(name: pasteboardName))
        defer { pasteboard.clearContents() }
        let rtf = Data("{\\rtf1\\b hi}".utf8)
        let html = Data("<b>hi</b>".utf8)

        _ = try writer(pasteboard).write(.text("hi"), richText: RichTextPayload(rtf: rtf, html: html))

        let types = pasteboard.types ?? []
        XCTAssertTrue(types.contains(RichTextPolicy.rtfType), "剪贴板里没有 public.rtf：\(types)")
        XCTAssertTrue(types.contains(RichTextPolicy.htmlType), "剪贴板里没有 public.html：\(types)")
        XCTAssertEqual(pasteboard.data(forType: RichTextPolicy.rtfType), rtf,
                       "RTF 字节被改写了：粘回 Word 就是坏结构")
        XCTAssertEqual(pasteboard.string(forType: .string), "hi", "纯文本那份必须仍然在")
        // 顺序判据：富文本应用向前找 rtf，只认纯文本的应用还能拿到干净字符串
        XCTAssertLessThan(try XCTUnwrap(types.firstIndex(of: RichTextPolicy.rtfType)),
                          try XCTUnwrap(types.firstIndex(of: .string)),
                          "字符串排在 RTF 前面：富文本应用会先拿到它，格式照样丢")
    }

    func testWritingWithoutRichTextKeepsTheOldPlainPath() throws {
        let pasteboard = try XCTUnwrap(NSPasteboard(name: pasteboardName))
        defer { pasteboard.clearContents() }
        _ = try writer(pasteboard).write(.text("只有文本"), richText: nil)
        XCTAssertEqual(pasteboard.string(forType: .string), "只有文本")
        XCTAssertNil(pasteboard.data(forType: RichTextPolicy.rtfType))
        // 空载荷也不能被当成"有富文本"走 item 那条路
        _ = try writer(pasteboard).write(.text("只有文本"), richText: RichTextPayload(rtf: nil, html: nil))
        XCTAssertEqual(pasteboard.string(forType: .string), "只有文本")
    }

    // MARK: - 存档：写盘读回来表示还在；导出如实说没带走

    func testRichTextSurvivesTheArchiveRoundTrip() throws {
        let root = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("Round3F2-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let rtf = Data("{\\rtf1\\par}".utf8)
        let entry = ClipboardEntry(content: .text("x"), timestamp: Date(timeIntervalSince1970: 9),
                                   thumbnail: nil, sourceURL: nil, sourceUTIs: ["public.utf8-plain-text"],
                                   richText: RichTextPayload(rtf: rtf, html: nil))
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save([entry])
        persistence.flushPendingSaves()

        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.count, 1, "存档读回来是空的：往返判据无从判定")
        XCTAssertEqual(reloaded.first?.richText?.rtf, rtf,
                       "富文本没落盘：重启后从历史粘贴又退回纯文本")
        XCTAssertEqual(reloaded.first?.content, .text("x"))
    }

    func testExportSaysItLeftTheRichTextBehind() throws {
        let withRich = ClipboardEntry(content: .text("加粗"), timestamp: Date(timeIntervalSince1970: 1),
                                      thumbnail: nil, sourceURL: nil, sourceUTIs: [],
                                      richText: RichTextPayload(rtf: Data("rtf".utf8), html: nil))
        let plain = ClipboardEntry(content: .text("普通"), timestamp: Date(timeIntervalSince1970: 2),
                                   thumbnail: nil, sourceURL: nil, sourceUTIs: [])
        let (data, summary) = ArchiveTransfer.export(entries: [withRich, plain])
        XCTAssertEqual(summary.exportedCount, 2)
        XCTAssertEqual(summary.skippedRichTextCount, 1,
                       "没数出带富文本的条数：用户会以为导出的文件里格式还在")
        let text = try XCTUnwrap(String(data: data, encoding: .utf8))
        XCTAssertFalse(text.contains("rtf"), "导出的 JSON 里混进了富文本字节：那份文件是要拷去另一台机器的")
        let warning = ArchiveTransfer.exportWarningText(summary: summary)
        XCTAssertTrue(warning.contains("富文本") && warning.contains("1"),
                      "提示没说明格式没带走：\(warning)")
    }

    // MARK: - 接线守卫（判使用处）

    func testSettingsAndPastePathAreWired() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("保留富文本格式"), "设置页没有这个开关")
        // 键名是**引用** `RichTextPolicy.enabledKey` 而不是抄一遍字符串，
        // 所以这里判的是"有没有引用那个来源"，抄字面量反而要被判为错（两处字面量会漂）。
        XCTAssertTrue(settings.contains("RichTextPolicy.enabledKey"), "开关没写进策略用的那个键")

        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        XCTAssertTrue(store.contains("richText: entry.richText"),
                      "粘贴时没把富文本交给写回 —— 抓到了也白抓")

        let intake = codeOnly(try productSource(named: "Managers/ClipboardIntake.swift"))
        XCTAssertTrue(intake.contains("RichTextPolicy.capture(from: pasteboard, defaults: policyDefaults)"),
                      "采集没走策略（或没走注入的 defaults 域）")

        let drag = codeOnly(try productSource(named: "Utilities/EntryDrag.swift"))
        XCTAssertTrue(drag.contains("case .fileList"), "多文件拖出的载荷类型没了（§4 U-2）")
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
        throw NSError(domain: "Round3RichTextTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
