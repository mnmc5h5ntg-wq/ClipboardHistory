import XCTest
@testable import ClipboardHistoryApp

@MainActor
private final class FakeDestructiveConfirming: DestructiveConfirming {
    var answer: Bool
    private(set) var requestedTitles: [String] = []

    init(answer: Bool) {
        self.answer = answer
    }

    func confirm(title: String, message: String, confirmTitle: String, cancelTitle: String) -> Bool {
        requestedTitles.append(title)
        return answer
    }
}

/// 审计 X-01：菜单栏"清空未收藏"过去直接删除，带弹窗的确认函数没有任何调用者。
/// 现在 `.clearHistory` 必须经过确认；确认被拒时不得改动历史，也不得触发保存。
@MainActor
final class HistoryClearConfirmationTests: XCTestCase {
    private func entry(_ text: String, favorite: Bool) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date().addingTimeInterval(-Double(text.count)),
            thumbnail: nil,
            sourceURL: nil,
            isFavorite: favorite,
            sourceUTIs: []
        )
    }

    private func makeShell(answer: Bool) -> (ApplicationShell, HistoryStore, RecordingHistoryPersistence, FakeDestructiveConfirming) {
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            entry("keepme", favorite: true),
            entry("dropme", favorite: false),
        ])
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        let confirmation = FakeDestructiveConfirming(answer: answer)
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
            contextPreferences: ContextPreferenceSettings(),
            confirmation: confirmation
        )
        shell.configure(historyStore: store)
        // configure() 会安排 0.4s 后的真实剪贴板轮询；测试里立刻停掉，
        // 保证断言期间没有任何后台读取/写入参与。
        store.stopMonitoring()
        return (shell, store, persistence, confirmation)
    }

    func testClearHistoryCommandAsksForConfirmationAndDoesNotDeleteOnCancel() {
        let (shell, store, persistence, confirmation) = makeShell(answer: false)
        let snapshotsBefore = persistence.savedEntriesSnapshots.count

        shell.perform(.clearHistory)

        XCTAssertEqual(confirmation.requestedTitles, ["清空未收藏记录"], "命令必须走确认流程")
        XCTAssertEqual(store.entries.count, 2, "取消后一条都不能少")
        XCTAssertEqual(
            persistence.savedEntriesSnapshots.count,
            snapshotsBefore,
            "取消后不得把删空的列表写回磁盘"
        )
    }

    func testClearHistoryCommandDeletesOnlyAfterConfirmation() {
        let (shell, store, _, confirmation) = makeShell(answer: true)

        shell.perform(.clearHistory)

        XCTAssertEqual(confirmation.requestedTitles.count, 1)
        XCTAssertEqual(store.entries.map(\.content), [.text("keepme")], "只清未收藏")
        XCTAssertTrue(store.entries.allSatisfy(\.isFavorite))
    }

    func testDirectClearActionStillAvailableForAlreadyConfirmedPaths() {
        // 设置页走 SwiftUI alert，确认由视图层负责，store.perform(.clear) 保持无条件执行。
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            entry("keepme", favorite: true),
            entry("dropme", favorite: false),
        ])
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        store.perform(.clear)
        XCTAssertEqual(store.entries.map(\.content), [.text("keepme")])
    }
}
