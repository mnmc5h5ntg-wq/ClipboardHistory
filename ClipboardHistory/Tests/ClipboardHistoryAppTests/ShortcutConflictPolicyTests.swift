import XCTest
@testable import ClipboardHistoryApp

final class ShortcutConflictPolicyTests: XCTestCase {
    func testDistinctShortcutsHaveNoConflict() {
        let rows = [
            (name: "呼出主窗口", shortcut: HotKeyShortcut.defaultShortcut),
            (name: "再次复制", shortcut: HotKeyShortcut.defaultRepeatCopyShortcut),
            (name: "快速选择并粘贴", shortcut: HotKeyShortcut.defaultQuickPickShortcut),
        ]
        XCTAssertTrue(ShortcutConflictPolicy.conflicts(rows).isEmpty)
    }

    func testSameShortcutIsReportedOnceInRowOrder() {
        let rows = [
            (name: "呼出主窗口", shortcut: HotKeyShortcut.defaultRepeatCopyShortcut),
            (name: "再次复制", shortcut: HotKeyShortcut.defaultRepeatCopyShortcut),
            (name: "快速选择并粘贴", shortcut: HotKeyShortcut.defaultQuickPickShortcut),
        ]
        let conflicts = ShortcutConflictPolicy.conflicts(rows)
        XCTAssertEqual(conflicts.count, 1)
        XCTAssertEqual(conflicts.first?.firstName, "呼出主窗口")
        XCTAssertEqual(conflicts.first?.secondName, "再次复制")
        XCTAssertEqual(conflicts.first?.shortcut, "⌃⌥C")
    }

    func testThreeWayCollisionReportsEveryPair() {
        let rows = [
            (name: "A", shortcut: HotKeyShortcut.defaultShortcut),
            (name: "B", shortcut: HotKeyShortcut.defaultShortcut),
            (name: "C", shortcut: HotKeyShortcut.defaultShortcut),
        ]
        let conflicts = ShortcutConflictPolicy.conflicts(rows)
        XCTAssertEqual(conflicts.count, 3)
        XCTAssertEqual(conflicts.map(\.firstName), ["A", "A", "B"])
        XCTAssertEqual(conflicts.map(\.secondName), ["B", "C", "C"])
    }

    func testZeroOrOneRowHasNoConflict() {
        XCTAssertTrue(ShortcutConflictPolicy.conflicts([]).isEmpty)
        XCTAssertTrue(ShortcutConflictPolicy.conflicts([
            (name: "只有一个", shortcut: HotKeyShortcut.defaultShortcut),
        ]).isEmpty)
    }
}
