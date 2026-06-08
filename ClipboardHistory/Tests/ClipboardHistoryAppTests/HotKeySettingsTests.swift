import Carbon
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class HotKeySettingsTests: XCTestCase {
    override func tearDown() async throws {
        await MainActor.run {
            HotKeyPreferences.resetShowMainWindowShortcut()
            HotKeyPreferences.resetRepeatCopyShortcut()
        }
        try await super.tearDown()
    }

    func testSaveSuccessUpdatesShortcutAndClearsMessage() {
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
