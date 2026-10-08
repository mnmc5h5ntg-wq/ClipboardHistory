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
}
