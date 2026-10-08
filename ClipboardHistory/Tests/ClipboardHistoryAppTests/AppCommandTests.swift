import XCTest
@testable import ClipboardHistoryApp

final class AppCommandTests: XCTestCase {
    func testMenuBarCommandCatalogKeepsExpectedOrder() {
        XCTAssertEqual(
            AppCommandCatalog.menuBarCommands,
            [.showMainWindow, .showSettings, .clearHistory, .quit]
        )
    }

    func testCommandTitlesStayCentralized() {
        XCTAssertEqual(AppCommand.showMainWindow.title, "显示主窗口")
        XCTAssertEqual(AppCommand.showSettings.title, "设置")
        XCTAssertEqual(AppCommand.refreshHistory.title, "刷新历史")
        XCTAssertEqual(AppCommand.clearHistory.title, "清空未收藏")
        XCTAssertEqual(AppCommand.quit.title, "退出时间剪史")
    }

    func testKeyboardShortcutsForAppCommands() {
        XCTAssertEqual(AppCommand.showSettings.keyEquivalent, ",")
        XCTAssertEqual(AppCommand.quit.keyEquivalent, "q")
        XCTAssertEqual(AppCommand.refreshHistory.keyEquivalent, "")
    }
}
