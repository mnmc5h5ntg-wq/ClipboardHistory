import Carbon
import Carbon.HIToolbox
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
    /// R-32：符号键必须显示成字形本身，而不是退化成「Key 27」。
    func testSymbolKeysHaveReadableNames() {
        let expected: [(UInt32, String)] = [
            (UInt32(kVK_ANSI_Minus), "-"),
            (UInt32(kVK_ANSI_Equal), "="),
            (UInt32(kVK_ANSI_LeftBracket), "["),
            (UInt32(kVK_ANSI_RightBracket), "]"),
            (UInt32(kVK_ANSI_Backslash), "\\"),
            (UInt32(kVK_ANSI_Semicolon), ";"),
            (UInt32(kVK_ANSI_Quote), "'"),
            (UInt32(kVK_ANSI_Comma), ","),
            (UInt32(kVK_ANSI_Period), "."),
            (UInt32(kVK_ANSI_Slash), "/"),
            (UInt32(kVK_ANSI_Grave), "`"),
        ]
        for (code, name) in expected {
            let shortcut = HotKeyShortcut(keyCode: code, modifiers: UInt32(cmdKey))
            XCTAssertEqual(shortcut.displayString, "\u{2318}" + name,
                           "键位 \(code) 应显示成 \u{2318}\(name)，而不是退化成 Key N")
        }
    }
}
