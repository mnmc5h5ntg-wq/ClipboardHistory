import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class ApplicationShellTests: XCTestCase {
    func testCopyHistoryEntryByIDReResolvesCurrentEntryBeforeCopying() {
        let writer = TestClipboardWriter()
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        store.add(
            ClipboardIntake.Entry(
                content: .text("current"),
                thumbnail: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            ),
            timestamp: Date(timeIntervalSince1970: 1)
        )
        let currentEntry = store.entries[0]

        let staleEntry = makeClipboardEntry(
            id: currentEntry.id,
            content: .text("stale"),
            timestamp: Date(timeIntervalSince1970: 0)
        )
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings()
        )

        shell.configure(historyStore: store)
        shell.copyHistoryEntry(staleEntry)

        XCTAssertEqual(writer.writtenContents, [.text("current")])
    }

    func testCopyHistoryEntryByIDIgnoresMissingEntries() {
        let writer = TestClipboardWriter()
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil),
            maxEntries: 10
        )
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings()
        )

        shell.configure(historyStore: store)
        shell.copyHistoryEntry(id: UUID())

        XCTAssertTrue(writer.writtenContents.isEmpty)
    }
}
