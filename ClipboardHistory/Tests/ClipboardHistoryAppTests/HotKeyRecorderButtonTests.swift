import AppKit
import Carbon
import XCTest
@testable import ClipboardHistoryApp

/// 快捷键录制按钮（审计第二轮 13-08：`HotKeyRecorderView` 失焦这条路径没有测试）。
///
/// 这个控件在录制时会**吃掉所有按键**，所以它的"退出录制"比"进入录制"更值得钉：
/// 一旦卡在录制态，用户按什么都没反应，而界面上只有一行小字。
/// 判据一律取可观测的东西（标题、回调、窗口第一响应者），不去读私有状态。
@MainActor
final class HotKeyRecorderButtonTests: XCTestCase {
    /// 用来"接走"焦点的视图。裸 `NSView` 的 `acceptsFirstResponder` 是 false，
    /// 拿它当目标会让 `makeFirstResponder` 直接失败 —— 那样失焦用例红的是夹具而不是产品。
    final class FocusTarget: NSView {
        override var acceptsFirstResponder: Bool { true }
    }
    private func keyEvent(_ keyCode: UInt16, modifiers: NSEvent.ModifierFlags = []) -> NSEvent {
        NSEvent.keyEvent(with: .keyDown,
                         location: .zero,
                         modifierFlags: modifiers.intersection(.deviceIndependentFlagsMask),
                         timestamp: ProcessInfo.processInfo.systemUptime,
                         windowNumber: 0,
                         context: nil,
                         characters: "",
                         charactersIgnoringModifiers: "",
                         isARepeat: false,
                         keyCode: keyCode) ?? NSEvent()
    }

    private func makeWindowWithButton(_ button: HotKeyRecorderButton) -> (NSWindow, NSView) {
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 240, height: 120),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let other = FocusTarget()
        other.setFrameSize(NSSize(width: 100, height: 20))
        button.setFrameSize(NSSize(width: 100, height: 20))
        window.contentView?.addSubview(other)
        window.contentView?.addSubview(button)
        return (window, other)
    }

    private func makeButton(shortcut: HotKeyShortcut = .defaultShortcut) -> HotKeyRecorderButton {
        let button = HotKeyRecorderButton()
        button.shortcut = shortcut
        return button
    }

    func testStartRecordingShowsPrompt() {
        let button = makeButton()
        button.startRecording()
        XCTAssertEqual(button.title, "请输入快捷键", "进入录制态必须把标题换成提示语")
    }

    func testEscapeCancelsWithoutChangingShortcut() {
        let button = makeButton()
        var changed = 0
        button.onShortcutChange = { _ in changed += 1 }
        button.startRecording()
        button.keyDown(with: keyEvent(UInt16(kVK_Escape)))
        XCTAssertEqual(changed, 0, "Esc 不该被当成新快捷键")
        XCTAssertEqual(button.title, HotKeyShortcut.defaultShortcut.displayString,
                       "Esc 之后必须把标题还原成原快捷键")
    }

    func testValidComboIsAcceptedAndReported() {
        let button = makeButton()
        var received: HotKeyShortcut?
        button.onShortcutChange = { received = $0 }
        button.startRecording()
        button.keyDown(with: keyEvent(UInt16(kVK_ANSI_K), modifiers: [.control, .option]))
        XCTAssertEqual(received?.keyCode, UInt32(kVK_ANSI_K), "录到的 keyCode 不对：\(String(describing: received))")
        XCTAssertEqual(received?.modifiers, UInt32(controlKey | optionKey))
        XCTAssertEqual(button.title, received?.displayString, "标题要跟着换成新录到的组合")
    }

    /// 没有主修饰键的组合是非法的：必须回调"无效"，并且**不改动**原快捷键。
    func testPlainKeyIsRejectedAndKeepsOldShortcut() {
        let button = makeButton()
        var changed = 0, invalid = 0
        button.onShortcutChange = { _ in changed += 1 }
        button.onInvalidShortcut = { invalid += 1 }
        button.startRecording()
        button.keyDown(with: keyEvent(UInt16(kVK_ANSI_A)))
        XCTAssertEqual(invalid, 1, "无修饰键的组合要报「快捷键无效」")
        XCTAssertEqual(changed, 0, "非法组合不得覆盖原快捷键")
        XCTAssertEqual(button.shortcut, HotKeyShortcut.defaultShortcut)
        XCTAssertEqual(button.title, HotKeyShortcut.defaultShortcut.displayString, "拒绝之后要退出录制态")
    }

    /// 审计点名的那一条：**录制中途失焦**必须退出录制，否则窗口里其他控件收不到按键。
    func testLosingFocusWhileRecordingEndsRecording() throws {
        let button = makeButton()
        let (window, other) = makeWindowWithButton(button)
        window.makeFirstResponder(button)
        button.startRecording()
        XCTAssertTrue(window.firstResponder === button, "startRecording 应当把第一响应者抢过来")

        window.makeFirstResponder(other)
        XCTAssertEqual(button.title, HotKeyShortcut.defaultShortcut.displayString,
                       "失焦之后标题还停在「请输入快捷键」，说明它仍以为自己在录制")
        XCTAssertFalse(window.firstResponder === button,
                       "失焦后第一响应者仍是录制按钮：用户接下来按的每个键都会被吃掉")
    }

    /// 失焦时若本来就没在录制，不该把标题改掉（避免"看一眼就重置"的错觉）。
    func testLosingFocusWhileIdleKeepsTitle() {
        let button = makeButton()
        let (window, other) = makeWindowWithButton(button)
        window.makeFirstResponder(button)
        window.makeFirstResponder(other)
        XCTAssertEqual(button.title, HotKeyShortcut.defaultShortcut.displayString)
    }
}
