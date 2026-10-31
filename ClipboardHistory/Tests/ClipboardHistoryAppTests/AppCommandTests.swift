import XCTest
@testable import ClipboardHistoryApp

final class AppCommandTests: XCTestCase {
    func testMenuBarCommandCatalogKeepsExpectedOrder() {
        XCTAssertEqual(
            AppCommandCatalog.menuBarCommands,
            [.showMainWindow, .showQuickPick, .showSettings, .clearHistory, .quit]
        )
    }

    func testCommandTitlesStayCentralized() {
        XCTAssertEqual(AppCommand.showMainWindow.title, "显示主窗口")
        XCTAssertEqual(AppCommand.showQuickPick.title, "快速选择…")
        XCTAssertEqual(AppCommand.showSettings.title, "设置")
        XCTAssertEqual(AppCommand.refreshHistory.title, "刷新历史")
        XCTAssertEqual(AppCommand.clearHistory.title, "清空未收藏")
        XCTAssertEqual(AppCommand.quit.title, "退出时间剪史")
    }

    func testOnlyClearHistoryIsDestructive() {
        XCTAssertEqual(AppCommand.allCases.filter(\.isDestructive), [.clearHistory],
                       "只有清空未收藏会删数据；其余命令都不该被染成危险色")
    }

    func testKeyboardShortcutsForAppCommands() {
        XCTAssertEqual(AppCommand.showSettings.keyEquivalent, ",")
        XCTAssertEqual(AppCommand.quit.keyEquivalent, "q")
        XCTAssertEqual(AppCommand.refreshHistory.keyEquivalent, "")
        XCTAssertEqual(AppCommand.showQuickPick.keyEquivalent, "",
                       "快速选择只走全局热键；菜单里再挂本地 key equivalent 会造出第二条路径")
    }
}
