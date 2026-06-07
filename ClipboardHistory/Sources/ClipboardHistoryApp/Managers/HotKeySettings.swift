import Foundation

@MainActor
final class HotKeySettings: ObservableObject {
    @Published private(set) var shortcut: HotKeyShortcut
    @Published private(set) var message: String?

    private let controller = GlobalHotKeyController()

    init(shortcut: HotKeyShortcut = HotKeyPreferences.showMainWindowShortcut) {
        self.shortcut = shortcut
    }

    func start() {
        if !controller.register(shortcut: shortcut) {
            message = unavailableMessage(for: shortcut)
            shortcut = controller.shortcut
        }
    }

    func stop() {
        controller.stop()
    }

    func recordInvalidShortcut() {
        message = "请使用包含 Control、Option 或 Command 的组合快捷键。"
    }

    @discardableResult
    func save(_ newShortcut: HotKeyShortcut) -> Bool {
        guard newShortcut.isValid else {
            recordInvalidShortcut()
            return false
        }

        let previousShortcut = shortcut
        HotKeyPreferences.showMainWindowShortcut = newShortcut
        if controller.updateShortcut(newShortcut) {
            shortcut = newShortcut
            message = nil
            return true
        }

        HotKeyPreferences.showMainWindowShortcut = previousShortcut
        shortcut = previousShortcut
        message = unavailableMessage(for: newShortcut)
        return false
    }

    func reset() {
        HotKeyPreferences.resetShowMainWindowShortcut()
        _ = save(.defaultShortcut)
    }

    private func unavailableMessage(for shortcut: HotKeyShortcut) -> String {
        "“\(shortcut.displayString)” 可能已被系统或其他应用占用。请换一个快捷键。"
    }
}
