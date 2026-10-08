import Carbon
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class HotKeySettingsTests: XCTestCase {
    /// 这些用例读写的是 UserDefaults 里的真实键位，所以在**每条开头**复位，
    /// 而不是靠 tearDown —— 这样用例顺序无关，也不必覆写 XCTest 的生命周期方法。
    ///
    /// 原来这里覆写的是 `tearDown() async throws` + `try await super.tearDown()`：
    /// 本机 Swift 6.2.1 编得过，GitHub runner 的 Swift/Xcode 组合却报
    /// "sending value of non-Sendable type 'XCTestCase' risks causing data races"，
    /// 整个测试 target 编译失败（CI 首跑就是这么红的）。不依赖生命周期签名才是可移植的。
    private func resetPreferences() {
        HotKeyPreferences.resetShowMainWindowShortcut()
        HotKeyPreferences.resetRepeatCopyShortcut()
    }

    func testSaveSuccessUpdatesShortcutAndClearsMessage() {
        resetPreferences()
        let controller = RecordingHotKeyController()
        let settings = HotKeySettings(controller: controller)
        let shortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_A),
            modifiers: UInt32(cmdKey)
        )

        XCTAssertTrue(settings.save(shortcut))

        XCTAssertEqual(settings.shortcut, shortcut)
        XCTAssertNil(settings.message)
        XCTAssertEqual(controller.registeredShortcuts, [shortcut])
        XCTAssertEqual(HotKeyPreferences.showMainWindowShortcut, shortcut)
    }

    func testRepeatCopyShortcutUsesIndependentPreference() {
        resetPreferences()
        let showMainWindowShortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_A),
            modifiers: UInt32(cmdKey)
        )
        let repeatCopyShortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_B),
            modifiers: UInt32(optionKey)
        )
        HotKeyPreferences.showMainWindowShortcut = showMainWindowShortcut

        let controller = RecordingHotKeyController()
        let settings = HotKeySettings(action: .repeatCopy, controller: controller)

        XCTAssertEqual(settings.shortcut, HotKeyShortcut.defaultRepeatCopyShortcut)
        XCTAssertTrue(settings.save(repeatCopyShortcut))

        XCTAssertEqual(HotKeyPreferences.showMainWindowShortcut, showMainWindowShortcut)
        XCTAssertEqual(HotKeyPreferences.repeatCopyShortcut, repeatCopyShortcut)
        XCTAssertEqual(controller.registeredShortcuts, [repeatCopyShortcut])
    }

    func testSaveFailureRollsBackToPreviousShortcut() {
        resetPreferences()
        let previous = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_B),
            modifiers: UInt32(optionKey)
        )
        let attempted = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_C),
            modifiers: UInt32(cmdKey)
        )
        HotKeyPreferences.showMainWindowShortcut = previous
        let controller = RecordingHotKeyController(updateResults: [.newShortcutUnavailable(restoredPrevious: true)])
        let settings = HotKeySettings(action: .showMainWindow, shortcut: previous, controller: controller)

        XCTAssertFalse(settings.save(attempted))

        XCTAssertEqual(settings.shortcut, previous)
        XCTAssertEqual(HotKeyPreferences.showMainWindowShortcut, previous)
        XCTAssertEqual(controller.registeredShortcuts, [attempted])
        XCTAssertEqual(settings.message, "“⌘C” 可能已被系统或其他应用占用。请换一个快捷键。")
    }

    func testSaveFailureReportsWhenPreviousShortcutCannotBeRestored() {
        resetPreferences()
        let previous = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_B),
            modifiers: UInt32(optionKey)
        )
        let attempted = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_C),
            modifiers: UInt32(cmdKey)
        )
        HotKeyPreferences.showMainWindowShortcut = previous
        let controller = RecordingHotKeyController(updateResults: [.newShortcutUnavailable(restoredPrevious: false)])
        let settings = HotKeySettings(action: .showMainWindow, shortcut: previous, controller: controller)

        XCTAssertFalse(settings.save(attempted))

        XCTAssertEqual(settings.shortcut, previous)
        XCTAssertEqual(HotKeyPreferences.showMainWindowShortcut, previous)
        XCTAssertEqual(controller.registeredShortcuts, [attempted])
        XCTAssertEqual(settings.message, "“⌘C” 可能已被占用，且原快捷键“⌥B”未能恢复。请重新设置。")
    }

    func testStartFallsBackToDefaultShortcutWhenStoredShortcutIsUnavailable() {
        resetPreferences()
        let stored = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_B),
            modifiers: UInt32(optionKey)
        )
        HotKeyPreferences.showMainWindowShortcut = stored
        let controller = RecordingHotKeyController(registerResults: [false, true])
        let settings = HotKeySettings(action: .showMainWindow, shortcut: stored, controller: controller)

        settings.start()

        XCTAssertEqual(settings.shortcut, HotKeyShortcut.defaultShortcut)
        XCTAssertEqual(HotKeyPreferences.showMainWindowShortcut, HotKeyShortcut.defaultShortcut)
        XCTAssertEqual(controller.registeredShortcuts, [stored, HotKeyShortcut.defaultShortcut])
        XCTAssertEqual(settings.message, "“⌥B” 可能已被占用，已恢复为默认快捷键“⌃⌥V”。")
    }

    func testStartReportsDisabledWhenStoredAndDefaultShortcutsAreUnavailable() {
        resetPreferences()
        let stored = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_B),
            modifiers: UInt32(optionKey)
        )
        let controller = RecordingHotKeyController(registerResults: [false, false])
        let settings = HotKeySettings(action: .showMainWindow, shortcut: stored, controller: controller)

        settings.start()

        XCTAssertEqual(settings.shortcut, HotKeyShortcut.defaultShortcut)
        XCTAssertEqual(controller.registeredShortcuts, [stored, HotKeyShortcut.defaultShortcut])
        XCTAssertEqual(settings.message, "“⌥B” 可能已被系统或其他应用占用，当前快捷键未启用。")
    }

    func testInvalidShortcutDoesNotReachController() {
        resetPreferences()
        let controller = RecordingHotKeyController()
        let settings = HotKeySettings(controller: controller)
        let invalid = HotKeyShortcut(
            keyCode: UInt32(kVK_Escape),
            modifiers: UInt32(cmdKey)
        )

        XCTAssertFalse(settings.save(invalid))

        XCTAssertTrue(controller.registeredShortcuts.isEmpty)
        XCTAssertEqual(settings.message, "请使用包含 Control、Option 或 Command 的组合快捷键。")
    }
}

@MainActor
private final class RecordingHotKeyController: HotKeyControlling {
    private var registerResults: [Bool]
    private var updateResults: [HotKeyUpdateResult]
    private(set) var registeredShortcuts: [HotKeyShortcut] = []
    private(set) var didStop = false
    private(set) var shortcut = HotKeyShortcut.defaultShortcut

    init(
        registerResults: [Bool] = [true],
        updateResults: [HotKeyUpdateResult] = [.updated]
    ) {
        self.registerResults = registerResults
        self.updateResults = updateResults
    }

    func updateShortcut(_ newShortcut: HotKeyShortcut) -> HotKeyUpdateResult {
        registeredShortcuts.append(newShortcut)
        let result = updateResults.isEmpty ? .updated : updateResults.removeFirst()
        if result == .updated {
            shortcut = newShortcut
        }
        return result
    }

    func register(shortcut newShortcut: HotKeyShortcut) -> Bool {
        registeredShortcuts.append(newShortcut)
        let result = registerResults.isEmpty ? true : registerResults.removeFirst()
        if result {
            shortcut = newShortcut
        }
        return result
    }

    func stop() {
        didStop = true
    }
}
