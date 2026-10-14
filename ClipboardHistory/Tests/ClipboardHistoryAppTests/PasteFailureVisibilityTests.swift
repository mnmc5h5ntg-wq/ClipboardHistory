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

    /// 真值表。两格都得钉，而且**方向**要钉：
    /// 只断言"失败 ⇒ 取消"的话，把 `guard let` 写成 `guard copyErrorMessage != nil` 这种
    /// 反了方向的实现也能两格全过（它把成功挡掉、把失败放行）。
    /// 所以成功那一格断言的是"放行"，而不是"不报错"。
    func testCopyThenPasteTruthTable() {
        XCTAssertEqual(CopyThenPaste.decide(copyErrorMessage: nil), .pasteNow,
                       "复制成功（错误被清成 nil）必须放行 —— 挡住它就是把手动的功能改坏")
        let decision = CopyThenPaste.decide(copyErrorMessage: "剪贴板被占用")
        guard case .cancel(let reason) = decision else {
            return XCTFail("复制失败必须取消注入，实际 \(String(describing: decision))")
        }
        XCTAssertTrue(reason.contains("剪贴板被占用"), "要把原因原样带出来：\(reason)")
        XCTAssertTrue(reason.contains("剪贴板里仍是原来的内容"),
                      "必须说清「没粘」与「剪贴板没被换掉」，否则用户会以为自己丢了一次复制：\(reason)")
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
        XCTAssertTrue(source.contains("CopyThenPaste.decide(copyErrorMessage:"),
                      "复制 → 粘贴这条链路没有咨询决策表")
        // 咨询必须在注入之前（顺序反了等于不咨询）。
        let gateIndex = source.range(of: "CopyThenPaste.decide(copyErrorMessage:")?.lowerBound
        let injectIndex = source.range(of: "self?.sendPasteKeystrokeAfterVerifyingTarget")?.lowerBound
        if let gateIndex, let injectIndex {
            XCTAssertLessThan(gateIndex, injectIndex, "注入出现在闸门之前，顺序反了")
        } else {
            XCTFail("找不到闸门或注入的调用点，无法判断顺序")
        }
    }
}
