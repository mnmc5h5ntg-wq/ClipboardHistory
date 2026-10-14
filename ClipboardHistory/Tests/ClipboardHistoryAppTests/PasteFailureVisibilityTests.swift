import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R-13：自动粘贴这条链路上，"失败"过去没有任何出口 —— `Process.launch()` 之后
/// 没人看退出码，用户看到的就是"点了菜单没反应"。
/// 这里锁住三件事：失败会浮到界面并可被消除、成功不留提示、报错文案可执行。
@MainActor
final class PasteFailureVisibilityTests: XCTestCase {
    @MainActor
    private final class FakePasteKey: PasteKeyExecuting {
        var outcome: String?
        private(set) var calls = 0

        init(outcome: String? = nil) {
            self.outcome = outcome
        }

        func synthesizePaste() async -> String? {
            calls += 1
            return outcome
        }
    }

    private func makeShell(pasteKey: PasteKeyExecuting) -> (ApplicationShell, HistoryStore) {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(),
            pasteKey: pasteKey
        )
        shell.configure(historyStore: store)
        return (shell, store)
    }

    func testFailedKeystrokeBecomesVisibleNoticeUntilDismissed() {
        let key = FakePasteKey(outcome: "系统未授权本 App 控制「System Events」。")
        let (shell, store) = makeShell(pasteKey: key)
        XCTAssertNil(store.pasteFailureNotice)

        shell.sendPasteKeystroke()
        let deadline = Date().addingTimeInterval(5)
        while Date() < deadline, store.pasteFailureNotice == nil {
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTAssertEqual(store.pasteFailureNotice, "系统未授权本 App 控制「System Events」。")
        XCTAssertEqual(key.calls, 1)

        store.dismissPasteFailure()
        XCTAssertNil(store.pasteFailureNotice)
    }

    func testSuccessfulKeystrokeLeavesNoNotice() {
        let (shell, store) = makeShell(pasteKey: FakePasteKey(outcome: nil))
        shell.sendPasteKeystroke()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        XCTAssertNil(store.pasteFailureNotice)
    }

    // MARK: - 报错文案

    func testErrAEEventNotPermittedMapsToAutomationGuidance() {
        let stderr = "osascript:5:16: execution error: 未获得授权将Apple事件发送给System Events。 (-1743)"
        let reason = SystemEventsPasteKey.reason(fromStderr: stderr)
        XCTAssertTrue(reason.contains("自动化"), "应指向「自动化」授权页：\(reason)")
        XCTAssertTrue(reason.contains("手动粘贴"), "应给出可用的替代路径：\(reason)")
    }

    func testEnglishUnauthorizedStderrAlsoMaps() {
        let reason = SystemEventsPasteKey.reason(
            fromStderr: "\"System Events\" got error: Not authorized to send Apple events to System Events. (-1743)"
        )
        XCTAssertTrue(reason.contains("自动化"), reason)
    }

    func testUnknownFailureKeepsFirstStderrLineAndTruncates() {
        let longLine = String(repeating: "x", count: 600)
        let reason = SystemEventsPasteKey.reason(fromStderr: "boom\n\(longLine)")
        XCTAssertTrue(reason.hasPrefix("自动粘贴未完成：boom"), reason)
        XCTAssertLessThan(reason.count, 260, "错误文案必须截断，实际 \(reason.count) 字")
    }

    func testEmptyStderrStillProducesSentence() {
        let reason = SystemEventsPasteKey.reason(fromStderr: "   \n  ")
        XCTAssertFalse(reason.isEmpty)
        XCTAssertTrue(reason.contains("手动粘贴"), reason)
    }

    /// 脚本必须是固定文案。一旦有人把条目内容拼进 AppleScript，报错原文就可能
    /// 带着剪贴板内容进界面和日志 —— 这条守卫比"检查文案里没有秘密"更根本。
    func testPasteScriptIsFixedTextWithoutEntryContent() {
        XCTAssertEqual(
            SystemEventsPasteKey.pasteScript,
            "tell application \"System Events\" to keystroke \"v\" using command down"
        )
    }

    // MARK: - R40：复制这一步失败时，**不许**继续粘贴（U-66 / D-099）

    /// 真值表（R41 扩成三格）。方向也要钉：
    /// 只断言"失败 ⇒ 取消"的话，把 `guard let` 写成反向实现也能两格全过（成功被挡掉、失败被放行）。
    /// 所以成功那一格断言的是"放行"，而不是"不报错"。
    func testCopyThenPasteTruthTable() {
        XCTAssertEqual(CopyThenPaste.decide(failure: nil), .pasteNow,
                       "复制成功（失败事实被清成 nil）必须放行 —— 挡住它就是把手动的功能改坏")
        let cleared = CopyThenPaste.decide(
            failure: ClipboardWriteFailure(message: "文本没能写进系统剪贴板。", clearedPasteboard: true))
        guard case .cancel(let clearedReason) = cleared else {
            return XCTFail("清空之后失败必须取消注入，实际 \(String(describing: cleared))")
        }
        XCTAssertTrue(clearedReason.contains("文本没能写进系统剪贴板"), clearedReason)
        XCTAssertTrue(clearedReason.contains("已经被清掉"),
                      "清空发生在写入失败**之前** ⇒ 那句必须承认旧内容没了：" + clearedReason)
        XCTAssertFalse(clearedReason.contains("仍是原来的内容"),
                       "同一句里不许既说「被清掉」又说「仍是原来的内容」：" + clearedReason)

        let untouched = CopyThenPaste.decide(
            failure: ClipboardWriteFailure(message: "文件已被移动或删除。", clearedPasteboard: false))
        guard case .cancel(let untouchedReason) = untouched else {
            return XCTFail("清空之前失败同样要取消注入，实际 \(String(describing: untouched))")
        }
        XCTAssertTrue(untouchedReason.contains("仍是原来的内容，没有被替换"),
                      "没动过剪贴板时这句才是真话：" + untouchedReason)
        XCTAssertFalse(untouchedReason.contains("已经被清掉"), untouchedReason)
    }

    /// R41：回执**不许说假话**，也不许把系统英文原文搬进界面（U-67 / D-100）。
    ///
    /// 来历：R40 那句"剪贴板里仍是原来的内容，没有被替换"是我照着"失败了所以什么都没发生"写的，
    /// 而 `SystemClipboardWriter.write` 的真实顺序是「校验 → `clearContents()` → 写入」——
    /// 三种"写入失败"全部发生在**清空之后**，那时用户原来的内容已经没了。
    /// 一条只用来报告失败的回执，反过来成了第二个缺陷。
    func testClipboardWriteFailureClassificationTruthTable() {
        // ① 清空之前抛的那一种：只有它配说"仍是原来的内容"。
        let missing = ClipboardWriteFailure.classify(ClipboardWriteError.fileDoesNotExist)
        XCTAssertFalse(missing.clearedPasteboard, "fileDoesNotExist 抛在 clearContents 之前")
        XCTAssertTrue(missing.message.contains("文件已被移动或删除"), missing.message)
        // ② 清空之后抛的那三种：必须承认旧内容没了。
        for error in [ClipboardWriteError.failedToWriteText, .failedToWriteImage, .failedToWriteFileURL] {
            let fact = ClipboardWriteFailure.classify(error)
            XCTAssertTrue(fact.clearedPasteboard, "\(error) 发生在 clearContents 之后")
            XCTAssertTrue(fact.message.contains("剪贴板"), fact.message)
        }
        // ③ 未分类错误：**保守**当作已清空，且**不许**把系统原文带进界面。
        let unknown = ClipboardWriteFailure.classify(
            NSError(domain: NSOSStatusErrorDomain, code: -100,
                    userInfo: [NSLocalizedDescriptionKey: "The operation couldn\u{2019}t be completed."]))
        XCTAssertTrue(unknown.clearedPasteboard, "猜错方向的代价不对称：说错「还在」会让人去粘空内容")
        XCTAssertFalse(unknown.message.contains("The operation"),
                       "系统英文原文不许进界面（它进日志）：" + unknown.message)
        XCTAssertFalse(unknown.message.isEmpty)
        print("CLIPBOARD_FAILURE_TRUTH_TABLE 四型 + 未分类：cleared=false 只有 fileDoesNotExist 一种")
    }

    /// **管线级**（产品入口 = `ApplicationShell.copyAndPasteEntry`，也就是浮层回车 / 菜单栏点一条）：
    /// 写剪贴板失败时，一条 ⌘V 都不许注入，而且界面要说话。
    ///
    /// 修前这一臂是**真的会粘出错东西**：第一步的结果没人看，第二步照样切前台、照样按键 ——
    /// 目标应用收到的是用户剪贴板里**原来**那条无关内容，而界面一句话都没有
    /// （`clipboardWriteErrorMessage` 全仓唯一的显示消费者是详情区那颗按钮）。
    func testCopyFailureCancelsTheAutoPasteAndSaysSo() throws {
        let writer = TestClipboardWriter()
        writer.errorToThrow = NSError(domain: "PasteFailureVisibilityTests", code: 7,
                                      userInfo: [NSLocalizedDescriptionKey: "剪贴板被占用"])
        let key = FakePasteKey(outcome: nil)
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        store.add(ClipboardIntake.Entry(content: .text("要复制的那条"),
                                        thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"]))
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(),
            pasteKey: key
        )
        shell.configure(historyStore: store)
        guard let entry = store.entries.first else {
            return XCTFail("夹具没把条目放进 store ⇒ 这条判据没有对象")
        }

        shell.copyAndPasteEntry(entry)
        // 跨过 `copyAndPasteEntry` 里那两段延迟（0.1 + 0.15 秒）：
        // 只 sleep 一点点会得到"没按键"的假绿 —— 那可能只是还没轮到它按。
        RunLoop.main.run(until: Date().addingTimeInterval(0.8))

        XCTAssertEqual(key.calls, 0,
                       "复制失败之后仍然注入了 ⌘V ⇒ 目标应用粘出来的是用户剪贴板里原来的内容")
        let notice = try XCTUnwrap(store.pasteFailureNotice,
                                   "复制失败必须浮到界面（走的是仓库里已有那条横幅通道）")
        XCTAssertTrue(notice.contains("复制到剪贴板失败"), notice)
        XCTAssertFalse(notice.contains("要复制的那条"), "回执不许把条目原文带回界面（隐私）")
        // R41：这一臂的错误是未分类的 NSError ⇒ 保守当作"已经清空过"，
        // 于是那句"仍是原来的内容"必须**不**出现（它在这一臂里是假话）。
        XCTAssertFalse(notice.contains("仍是原来的内容"),
                       "未分类错误下不许承诺旧内容还在：" + notice)
        XCTAssertTrue(notice.contains("已经被清掉"),
                      "保守说法要明确告诉用户要重新复制：" + notice)
        XCTAssertFalse(notice.contains("剪贴板被占用"),
                       "测试夹具里那句人造文本不该再出现在界面上：" + notice)
    }

    /// 另一臂：**闸门不许把正常路径挡掉**。
    /// 这一臂刻意不断言"⌘V 真的注入了" —— 那一步取决于测试进程此刻是不是前台，
    /// 本机与 CI 都可能被 `PasteTargetCheck` 判成 targetChanged（那是另一条已有用例钉着的判据）。
    /// 所以这里问的是**可分的部分**：走的绝不是"复制失败"那一支。
    func testCopySuccessIsNotBlockedByTheNewGate() throws {
        let key = FakePasteKey(outcome: nil)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        store.add(ClipboardIntake.Entry(content: .text("正常的一条"),
                                        thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"]))
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(),
            pasteKey: key
        )
        shell.configure(historyStore: store)
        guard let entry = store.entries.first else {
            return XCTFail("夹具没把条目放进 store ⇒ 这条判据没有对象")
        }

        shell.copyAndPasteEntry(entry)
        RunLoop.main.run(until: Date().addingTimeInterval(0.8))

        // 第一版这里只断言"没被报成复制失败" —— 变异 M186（把闸门方向反过来）证明那条断言太弱：
        // 反了的实现会在成功那一支直接 `return`，于是既没按键也没提示，
        // "没有复制失败的提示"照样成立 ⇒ 正常路径整个被挡掉却全绿。
        // 现在问的是"有没有走到下一步"：要么真注入了，要么被**目标复核**取消（那句必带"目标应用"）。
        let reachedThePasteStage = key.calls > 0
            || (store.pasteFailureNotice?.contains("目标应用") ?? false)
        XCTAssertTrue(reachedThePasteStage,
                      "复制成功却没走到注入、也没走到目标复核那句取消 ⇒ 正常路径被闸门误挡"
                      + "（calls=\(key.calls) notice=\(store.pasteFailureNotice ?? "nil")）")
        XCTAssertFalse(store.pasteFailureNotice?.contains("复制到剪贴板失败") ?? false,
                       "复制成功却被新闸门报成「复制失败」 ⇒ 正常路径被挡掉了")
    }

    /// 接线守卫（**辅助**，不是主判据）：上面那条管线用例已经能红在"仍然按了键"上，
    /// 这一条只是把"决策表被真的接在链路上"钉住，防止有人把 `decide` 换成调用点里的临时 if。
    func testCopyAndPastePathConsultsTheGate() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Managers/ApplicationShell.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 ApplicationShell.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)
        XCTAssertTrue(source.contains("CopyThenPaste.decide(failure:"),
                      "复制 → 粘贴这条链路没有咨询决策表")
        // 咨询必须在注入之前（顺序反了等于不咨询）。
        let gateIndex = source.range(of: "CopyThenPaste.decide(failure:")?.lowerBound
        let injectIndex = source.range(of: "self?.sendPasteKeystrokeAfterVerifyingTarget")?.lowerBound
        if let gateIndex, let injectIndex {
            XCTAssertLessThan(gateIndex, injectIndex, "注入出现在闸门之前，顺序反了")
        } else {
            XCTFail("找不到闸门或注入的调用点，无法判断顺序")
        }
    }
}
