import XCTest
@testable import ClipboardHistoryApp

/// R43 / BACKLOG 62 / D-102：「导出反馈数据」那条回执 —— 只说一次，而且说的是人话。
///
/// 修前两件事同时不合格：
/// ① 三个分支都写 `exportMessage`（行内）**并且**置 `showExportAlert`（模态）⇒ 同一句话被说两遍，
///    其中一遍还会打断用户；
/// ② 失败那支是 `"导出失败：\(error.localizedDescription)"`，而 `ExportError` 不是 `LocalizedError`
///    ⇒ 界面写的是 "The operation couldn't be completed. (…)" —— R41 的 U-67 在另一个出口上复现。
///
/// 本文件不覆盖管线：①②的措辞由纯函数 `FeedbackExportReceipt` 决定，这里判的是那张真值表；
/// **管线级**判据是同文件里 `testExportFeedbackActionSpeaksThroughTheMapperOnce`
/// （读产品源码里那个真动作，确认它走映射器、不再置模态、不把原文写进界面）。
/// 像素侧的对应物是 `receipt-line` 那张组件帧 —— 它现在画的就是本文件钉的这句失败回执。
@MainActor
final class SettingsFailureReceiptTests: XCTestCase {
    // MARK: - 真值表

    func testFeedbackExportReceiptTruthTable() {
        // ① 成功：说文件名，不庆祝。
        XCTAssertEqual(FeedbackExportReceipt.success(fileName: "feedback_export_20261014-120000.jsonl"),
                       "已导出：feedback_export_20261014-120000.jsonl")

        // ② 没数据：这不是错误，措辞也不许带"失败"两个字。
        let noData = FeedbackExportReceipt.failure(RecommendationFeedbackStore.ExportError.noData)
        XCTAssertEqual(noData, FeedbackExportReceipt.noData)
        XCTAssertFalse(noData.contains("失败"), "空数据被说成失败 ⇒ 用户会以为自己的数据坏了：\(noData)")

        // ③ 写盘失败：一句下一步，且**不**把 payload 搬进界面。
        let writing = FeedbackExportReceipt.failure(
            RecommendationFeedbackStore.ExportError.writingFailed(
                "Error Domain=NSCocoaErrorDomain Code=640 \"The file exists.\""))
        XCTAssertTrue(writing.contains("没能写进磁盘"), writing)
        XCTAssertTrue(writing.contains("再试一次"), "必须给下一步：\(writing)")
        XCTAssertFalse(writing.contains("NSCocoaErrorDomain"),
                       "payload 是诊断材料，归日志；进界面就是 BACKLOG 62 的原样复现：" + writing)

        // ④ 未分类错误：也说"文件没有生成"，因为三个抛出点都在写出文件之前或之中。
        let unknown = FeedbackExportReceipt.failure(
            NSError(domain: NSCocoaErrorDomain, code: 260,
                    userInfo: [NSLocalizedDescriptionKey: "The operation couldn’t be completed."]))
        XCTAssertTrue(unknown.contains("文件没有生成"), unknown)
        XCTAssertFalse(unknown.contains("The operation"), "系统原文不许进界面：" + unknown)

        // ⑤ 每一格都必须**非空**且不含英文错误域 —— 这条兜底防的是"以后有人加一个分支忘了写文案"。
        for message in [FeedbackExportReceipt.noData, writing, unknown,
                        FeedbackExportReceipt.success(fileName: "x")] {
            XCTAssertFalse(message.isEmpty)
            XCTAssertFalse(message.contains("ErrorDomain"), "界面文案里不许出现错误域：" + message)
            XCTAssertFalse(message.contains("error -"), "界面文案里不许出现 OSStatus 原文：" + message)
        }
        CaptureReadings.emit("FEEDBACK_EXPORT_RECEIPT_TRUTH_TABLE 5 格：noData≠失败 / 两种失败都给下一步 / 无系统原文")
    }

    // MARK: - 管线级：那个真动作

    /// 读**产品源码里的那个动作**（不是复刻）：它必须走映射器、必须只说一次。
    ///
    /// 为什么不做成"调用 `SettingsView` 的私有方法"：`exportFeedbackData` 是 `private`，
    /// 而且里面是 `NSSavePanel` + Finder —— 那两样在测试进程里碰不得（会抢用户前台）。
    /// 所以这条判的是**接线**：动作体里出现了映射器的两个出口、没出现 `localizedDescription`、
    /// 全文件不再有第二条通道（`showExportAlert` / 那条 `.alert`）。
    /// 它挡得住的坏法：有人把措辞改回直出原文、或者又把模态加回来。
    func testExportFeedbackActionSpeaksThroughTheMapperOnce() throws {
        let source = try productSource(named: "Views/SettingsView.swift")
        let code = Self.stripCommentLines(source)
        let action = try XCTUnwrap(
            Self.functionBody("private func exportFeedbackData()", in: code),
            "找不到 `exportFeedbackData` ⇒ 这条判据没有对象（改名了就要一起改判据）")

        XCTAssertTrue(action.contains("FeedbackExportReceipt.success"),
                      "成功那条不再走映射器 ⇒ 真值表钉的话与界面说的话会分家")
        XCTAssertTrue(action.contains("FeedbackExportReceipt.failure"),
                      "失败那条不再走映射器 ⇒ BACKLOG 62 直接复发")
        XCTAssertFalse(action.contains("localizedDescription"),
                       "动作里又出现 `localizedDescription` ⇒ 系统原文会直接进横幅（U-67 那一族）")
        XCTAssertTrue(action.contains("LifecycleDebugLogger.log"),
                      "原文不进界面不等于丢掉：它必须落到日志，否则下次红字报错无从诊断")

        XCTAssertFalse(code.contains("showExportAlert"),
                       "第二条通道被加回来了：同一个导出结果既走行内回执又弹模态（BACKLOG 62）")
        XCTAssertFalse(code.contains(".alert(\"导出反馈数据\""),
                       "同上 —— 那条 `.alert` 就是模态那一半")
        CaptureReadings.emit("EXPORT_FEEDBACK_CHANNEL 一条通道：行内 ReceiptLine；原文进日志")
    }

    /// 「暂无数据」这一支从 `catch noData` 变成 `catch let error` 之后，
    /// 措辞仍必须由映射器决定（而不是在动作里手写一句）。这一条钉的是那个**归一**。
    func testEmptyDataStillGoesThroughTheMapperRatherThanASpecialCase() throws {
        let code = Self.stripCommentLines(try productSource(named: "Views/SettingsView.swift"))
        let action = try XCTUnwrap(Self.functionBody("private func exportFeedbackData()", in: code))
        XCTAssertFalse(action.contains("\"暂无反馈数据可导出\""),
                       "动作里手抄了一句文案 ⇒ 真值表与界面会分家（这一句现在归映射器）")
        XCTAssertEqual(FeedbackExportReceipt.noData, "暂无反馈数据可导出")
    }

    // MARK: - 存档导出 / 导入那两条（BACKLOG 62 的第二、第三个出口）

    /// 同一族措辞，另外两个出口：`SettingsWindowController` 的两个注入闭包。
    func testArchiveTransferReceiptTruthTable() throws {
        let export = ArchiveTransferReceipt.exportFailed(
            NSError(domain: NSCocoaErrorDomain, code: 640,
                    userInfo: [NSLocalizedDescriptionKey: "The file “x.json” couldn’t be saved."]))
        XCTAssertTrue(export.contains("导出失败"), export)
        XCTAssertTrue(export.contains("历史记录本身没有任何变化"),
                      "这句是查过的：`data.write` 失败时 `entries` 一个字节都没动：" + export)
        XCTAssertTrue(export.contains("再试一次"), "必须给下一步：" + export)

        let importText = ArchiveTransferReceipt.importFailed(
            NSError(domain: NSCocoaErrorDomain, code: 260, userInfo: nil))
        XCTAssertTrue(importText.contains("导入失败"), importText)
        XCTAssertTrue(importText.contains("记录没有任何变化"), importText)

        // ④ 这一格钉的是**那句"没有变化"的前提**：两条路上错误都发生在改动历史之前。
        //    以后有人把导出改成"就地逐条写"或把导入改成流式合并，这句话就会变成假话 ——
        //    那时该红的是这条，而不是让界面继续说一件不再成立的事。
        let store = try productSource(named: "Managers/HistoryStore.swift")
        let importBody = try XCTUnwrap(Self.functionBody("func importArchiveJSON", in: store),
                                       "找不到 `importArchiveJSON` ⇒ 这条前提判据没有对象")
        let importCall = try XCTUnwrap(importBody.range(of: "ArchiveTransfer.import(data)"),
                                       "导入的抛出点变了 ⇒ 请重读它是否仍在 `entries` 被改之前，再决定这句要不要留")
        let assignment = try XCTUnwrap(importBody.range(of: "entries = "),
                                       "找不到 `entries = ` 那一步 ⇒ 前提判据要跟着改写，不许静默跳过")
        XCTAssertTrue(importCall.lowerBound < assignment.lowerBound,
                      "`entries` 的赋值现在排在解码之前 ⇒ “记录没有任何变化”是假话，改文案并改这条判据")

        for message in [export, importText] {
            XCTAssertFalse(message.contains("ErrorDomain"), "系统原文不许进界面：" + message)
            XCTAssertFalse(message.contains("couldn"), "英文原文不许进界面：" + message)
        }
        CaptureReadings.emit("ARCHIVE_TRANSFER_RECEIPT 两格：都含下一步、都不含原文，且钉住“改动之前抛完”这个前提")
    }

    /// 那两个闭包必须走映射器，而且不许再把 `localizedDescription` 拼进界面。
    func testArchiveActionsSpeakThroughTheMapperAndLogTheRawError() throws {
        let source = try productSource(named: "Managers/SettingsWindowController.swift")
        let code = Self.stripCommentLines(source)
        XCTAssertTrue(code.contains("ArchiveTransferReceipt.exportFailed"),
                      "导出存档那条回执不再走映射器 ⇒ 真值表与界面会分家")
        XCTAssertTrue(code.contains("ArchiveTransferReceipt.importFailed"),
                      "导入存档那条回执不再走映射器")
        XCTAssertFalse(code.contains("失败：\\(error.localizedDescription)"),
                       "又有人把系统原文拼进界面了（BACKLOG 62 的原样）")
        let logs = code.components(separatedBy: "LifecycleDebugLogger.log").count - 1
        XCTAssertEqual(logs, 2, "原文不进界面不等于丢掉：两个 catch 各该有一条日志（实际读到 \(logs) 条）")
        CaptureReadings.emit("ARCHIVE_ACTION_CHANNEL 措辞走映射器、原文走日志（2 个 catch）")
    }

    // MARK: - 夹具不许替产品写文案（R24 那条规矩的又一次落地）

    /// `receipt-line` 那张帧以前画的是 **`"已导出 94 条记录到 ~/Desktop/时间剪史-导出.json"`** ——
    /// 全仓 grep 不到这句产品话。也就是说这张帧一直在给一个不存在的文案做保：
    /// 产品把回执改短、改长、改措辞，它都不会红。
    /// ⇒ 这条判据钉的是"帧里的回执文案必须来自生产者"，两个方向都会红：
    ///   有人把手写文案加回来 ⇒ 红；这一族以后新增一个 `ReceiptLine` 夹具而忘了接生产者 ⇒ 也红。
    func testHarnessNeverHandWritesReceiptCopy() throws {
        let harness = try harnessSource()
        let offenders = Self.handWrittenReceiptArguments(in: harness)
        XCTAssertTrue(offenders.isEmpty,
                      "这些 ReceiptLine 夹具的文案是手写的字面量（产品不会这么说，帧却在替它做保）：\n"
                          + offenders.joined(separator: "\n")
                          + "\n⇒ 换成生产者函数（`FeedbackExportReceipt` / `ArchiveTransferReceipt` / "
                          + "`CopyThenPaste.decide`），让措辞一改帧就红")
        CaptureReadings.emit("RECEIPT_FIXTURE_COPY 手写文案 0 处")
    }

    /// 上面那把尺自己的真值表：抓得住手写，也不把合法写法误报。
    func testHandWrittenReceiptScanIsATruthTable() {
        XCTAssertEqual(Self.handWrittenReceiptArguments(in: #"ReceiptLine(text: "已导出 94 条", dismiss: {})"#),
                       [#"ReceiptLine(text: "已导出 94 条", dismiss: {})"#])
        XCTAssertTrue(Self.handWrittenReceiptArguments(
            in: #"ReceiptLine(text: FeedbackExportReceipt.noData) {}"#).isEmpty,
            "生产者写法被误报 ⇒ 守卫会逼人把它删掉")
        XCTAssertTrue(Self.handWrittenReceiptArguments(
            in: "ReceiptLine(text: message) { self.exportMessage = nil }").isEmpty,
            "变量（产品自己算出来的那句）不是手写文案")
        // 注释里的那句引用**不许**算违规 —— 否则这条判据第一次跑就会红在自己的说明上。
        XCTAssertTrue(Self.handWrittenReceiptArguments(
            in: "// 原来是 `\"已导出 94 条记录到 …\"`，全仓 grep 不到").isEmpty,
            "注释被当成了产品文案")
    }

    // MARK: - 扫描器

    /// 只认字面量开头的参数（`ReceiptLine(text: "`）。注释行先摘掉 ——
    /// 这条判据扫的是**测试源码**，而它的说明里必然要引用那句坏文案（自匹配那一族）。
    static func handWrittenReceiptArguments(in source: String) -> [String] {
        source.components(separatedBy: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.hasPrefix("//") && $0.contains("ReceiptLine(text: \"") }
    }

    /// 夹具文件与本文件在同一个目录下 —— 这条判据读的是**别的文件**，
    /// 所以不需要"扫自身源码要先把守卫自己摘掉"那一步。
    private func harnessSource() throws -> String {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().appendingPathComponent("UICaptureHarness.swift")
        guard let text = try? String(contentsOf: url, encoding: .utf8) else {
            throw NSError(domain: "SettingsFailureReceiptTests", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "读不到 UICaptureHarness.swift：守卫找不到对象时必须红"])
        }
        return text
    }


    /// 从一段源码里抠出某个函数的大括号体（配平，不靠行数猜）。
    static func functionBody(_ declaration: String, in source: String) -> String? {
        guard let start = source.range(of: declaration) else { return nil }
        var index = start.upperBound
        var depth = 0
        var seenBrace = false
        var body = ""
        while index < source.endIndex {
            let character = source[index]
            if character == "{" {
                depth += 1
                seenBrace = true
            } else if character == "}" {
                depth -= 1
                if seenBrace && depth == 0 {
                    body.append(character)
                    return body
                }
            }
            if seenBrace { body.append(character) }
            index = source.index(after: index)
        }
        return nil
    }

    static func stripCommentLines(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory + "/" + name)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "SettingsFailureReceiptTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 \(relative)：守卫找不到被守卫的东西时必须红"])
    }
}
