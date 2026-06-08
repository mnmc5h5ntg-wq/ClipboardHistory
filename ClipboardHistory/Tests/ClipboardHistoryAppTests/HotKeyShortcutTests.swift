import Carbon
import XCTest
@testable import ClipboardHistoryApp

final class HotKeyShortcutTests: XCTestCase {
    func testDefaultShortcutIsControlOptionV() {
        let shortcut = HotKeyShortcut.defaultShortcut

        XCTAssertEqual(shortcut.keyCode, UInt32(kVK_ANSI_V))
        XCTAssertEqual(shortcut.modifiers, UInt32(controlKey | optionKey))
        XCTAssertEqual(shortcut.displayString, "⌃⌥V")
        XCTAssertTrue(shortcut.isValid)
    }

    func testDefaultRepeatCopyShortcutIsControlOptionC() {
        let shortcut = HotKeyShortcut.defaultRepeatCopyShortcut

        XCTAssertEqual(shortcut.keyCode, UInt32(kVK_ANSI_C))
        XCTAssertEqual(shortcut.modifiers, UInt32(controlKey | optionKey))
        XCTAssertEqual(shortcut.displayString, "⌃⌥C")
        XCTAssertTrue(shortcut.isValid)
    }

    func testShortcutRequiresPrimaryModifier() {
        let shortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_ANSI_A),
            modifiers: UInt32(shiftKey)
        )

        XCTAssertFalse(shortcut.isValid)
    }

    func testShortcutRejectsReservedKeys() {
        let shortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_Escape),
            modifiers: UInt32(cmdKey)
        )

        XCTAssertFalse(shortcut.isValid)
    }

    func testDisplayStringUsesReadableKeyNames() {
        let shortcut = HotKeyShortcut(
            keyCode: UInt32(kVK_LeftArrow),
            modifiers: UInt32(cmdKey | shiftKey)
        )

        XCTAssertEqual(shortcut.displayString, "⇧⌘←")
    }
}
