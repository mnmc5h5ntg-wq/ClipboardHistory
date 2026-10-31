// R428：菜单项显示全局快捷键提示（显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V），并把快速选择挂进菜单。
// 12 的 NSMenu 用真实 NSMenuItem 标题作证；13+ 的 MenuBarExtra 是系统菜单，像素通道具名 NOT-RUN。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class MenuShortcutPresentationTests: XCTestCase {

    func testHintsComeFromTheConfiguredGlobalShortcuts() {
        XCTAssertEqual(MenuShortcutPresentation.hint(
            for: .showMainWindow,
            showMainWindow: .defaultShortcut,
            quickPick: .defaultQuickPickShortcut), "⌃⌥V")
        XCTAssertEqual(MenuShortcutPresentation.hint(
            for: .showQuickPick,
            showMainWindow: .defaultShortcut,
            quickPick: .defaultQuickPickShortcut), "⌃⌥⇧V")
        XCTAssertNil(MenuShortcutPresentation.hint(
            for: .showSettings,
            showMainWindow: .defaultShortcut,
            quickPick: .defaultQuickPickShortcut),
            "设置已有 ⌘, 本地键；不要再写一条文字提示")
        XCTAssertNil(MenuShortcutPresentation.hint(
            for: .quit,
            showMainWindow: .defaultShortcut,
            quickPick: .defaultQuickPickShortcut))
    }

    func testTitleAppendsANonBlankHintOnly() {
        XCTAssertEqual(MenuShortcutPresentation.title("显示主窗口", hint: "⌃⌥V"),
                       "显示主窗口  ⌃⌥V")
        XCTAssertEqual(MenuShortcutPresentation.title("显示主窗口", hint: nil), "显示主窗口")
        XCTAssertEqual(MenuShortcutPresentation.title("显示主窗口", hint: "  \n"), "显示主窗口")
        XCTAssertEqual(MenuShortcutPresentation.title("显示主窗口", hint: " ⌃⌥V "),
                       "显示主窗口  ⌃⌥V")
    }

    func testTheRealMenuCarriesTheHintsAndTheQuickPickCommand() {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        let controller = MenuBarController()
        controller.configure(
            commandHandler: { _ in },
            historyStore: store,
            menuShortcutHints: {
                [.showMainWindow: HotKeyShortcut.defaultShortcut.displayString,
                 .showQuickPick: HotKeyShortcut.defaultQuickPickShortcut.displayString]
            }
        )
        let menu = NSMenu()
        controller.populate(menu)
        let titles = menu.items.map(\.title)
        XCTAssertTrue(titles.contains("显示主窗口  ⌃⌥V"), "菜单里没有带提示的显示主窗口：\(titles)")
        XCTAssertTrue(titles.contains("快速选择…  ⌃⌥⇧V"), "菜单里没有带提示的快速选择：\(titles)")
        XCTAssertTrue(titles.contains("设置"), "设置仍是原生 ⌘, 键，标题不应带文字提示")
        XCTAssertTrue(titles.contains("退出时间剪史"), "退出项缺失")
    }

    func testMenuHintsFollowACustomShortcutAtPopulateTime() {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        var mainShortcut = HotKeyShortcut.defaultShortcut
        let quickShortcut = HotKeyShortcut.defaultQuickPickShortcut
        let controller = MenuBarController()
        controller.configure(
            commandHandler: { _ in },
            historyStore: store,
            menuShortcutHints: {
                [.showMainWindow: mainShortcut.displayString,
                 .showQuickPick: quickShortcut.displayString]
            }
        )
        let menu = NSMenu()
        controller.populate(menu)
        XCTAssertTrue(menu.items.map(\.title).contains("显示主窗口  ⌃⌥V"))

        mainShortcut = HotKeyShortcut.defaultRepeatCopyShortcut
        let updated = NSMenu()
        controller.populate(updated)
        let titles = updated.items.map(\.title)
        XCTAssertTrue(titles.contains("显示主窗口  ⌃⌥C"),
                      "改键后菜单没有跟着走（提示是快照而不是按需读）：\(titles)")
        XCTAssertFalse(titles.contains("显示主窗口  ⌃⌥V"),
                       "旧快捷键还挂在菜单上")
    }

    func testBothSurfacesUseThePresenterAndTheQuickPickCommand() throws {
        let app = codeOnly(try productSource(named: "App.swift"))
        XCTAssertTrue(app.contains("appDelegate.menuShortcutHint(for: command)"),
                      "13+ 的 MenuBarExtra 没有从 appDelegate 取提示")
        XCTAssertTrue(app.contains("MenuShortcutPresentation.title("),
                      "13+ 的菜单项没有走标题呈现器")

        let controller = codeOnly(try productSource(named: "Managers/MenuBarController.swift"))
        XCTAssertTrue(controller.contains("MenuShortcutPresentation.title(command.title,"),
                      "12 的 NSMenu 没有走标题呈现器")
        XCTAssertTrue(controller.contains("menuShortcutHints()[command]"),
                      "12 的菜单没有使用传入的提示")

        let shell = codeOnly(try productSource(named: "Managers/ApplicationShell.swift"))
        XCTAssertTrue(shell.contains("menuShortcutHints: {"),
                      "Shell 没有把全局快捷键提示交给 MenuBarController")
        XCTAssertTrue(shell.contains("showMainWindowHotKeySettings.shortcut.displayString"),
                      "提示没有读当前（可改）的呼出快捷键")
        XCTAssertTrue(shell.contains("quickPickHotKeySettings.shortcut.displayString"),
                      "提示没有读当前（可改）的快速选择快捷键")

        XCTAssertTrue(AppCommandCatalog.menuBarCommands.contains(.showQuickPick),
                      "快速选择没有进菜单命令区")
    }

    /// R505：状态菜单（macOS 13+ 的 SwiftUI MenuBarExtra）里，两条标准快捷键
    /// （⌘, / ⌘Q）之前一个字都不画 —— Button 不挂 `.keyboardShortcut` 时菜单没有右对齐那一列。
    /// 全局热键（⌃⌥V / ⌃⌥⇧V）仍走标题里的行内提示：给它们挂本地键等于造第二条触发路径。
    func testStandardShortcutsAreVisibleInTheSwiftUIMenu() throws {
        XCTAssertEqual(MenuCommandShortcutPresentation.keyEquivalent(for: .showSettings), ",")
        XCTAssertEqual(MenuCommandShortcutPresentation.keyEquivalent(for: .quit), "q")
        for command in [AppCommand.showMainWindow, .showQuickPick, .refreshHistory,
                        .clearHistory, .dismissAllRecommendations] {
            XCTAssertNil(MenuCommandShortcutPresentation.keyEquivalent(for: command),
                         "\(command) 是全局热键或没有快捷键 ⇒ 不许挂本地等价物：会造出第二条触发路径")
        }
        let app = codeOnly(try productSource(named: "App.swift"))
        XCTAssertTrue(app.contains(".modifier(MenuCommandShortcutModifier(command: command))"),
                      "命令区没有把标准快捷键修饰器挂上去 ⇒ 菜单里仍然看不到 ⌘, / ⌘Q")
        XCTAssertTrue(app.contains(".modifier(MenuCommandShortcutModifier(command: .quit))"),
                      "退出项没有把标准快捷键修饰器挂上去")
    }

    /// R516：破坏性命令「清空未收藏」在两条状态菜单路径上都带**文本**警告记号。
    /// `.menu` 会把 Label 的图标拍平（实测三角消失）；文本字符能留下，且不依赖文字颜色。
    func testDestructiveCommandCarriesATextWarningPrefixInBothMenuPaths() throws {
        XCTAssertEqual(MenuDestructivePresentation.warningPrefix, "\u{26A0}\u{FE0E} ")
        XCTAssertEqual(MenuDestructivePresentation.title("清空未收藏"),
                       "\u{26A0}\u{FE0E} 清空未收藏")
        let app = codeOnly(try productSource(named: "App.swift"))
        XCTAssertTrue(app.contains("Text(MenuDestructivePresentation.title(title))"),
                      "13+ 的菜单没有给破坏性命令加文本警告记号")
        XCTAssertFalse(app.contains(".foregroundColor(.red)"),
                       "红字方案已撤：系统灰底上只有 1.08:1")
        let controller = codeOnly(try productSource(named: "Managers/MenuBarController.swift"))
        XCTAssertTrue(controller.contains("MenuDestructivePresentation.title(base)"),
                      "12 的 NSMenu 没有给破坏性命令加文本警告记号")
        XCTAssertFalse(controller.contains("NSColor.systemRed"),
                       "红字方案已撤：12 的 NSMenu 也不许再用系统红文字")
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
        throw NSError(domain: "MenuShortcutPresentationTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
