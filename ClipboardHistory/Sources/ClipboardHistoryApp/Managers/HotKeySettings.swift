import Foundation

@MainActor
final class HotKeySettings: ObservableObject {
    let action: HotKeyAction
    @Published private(set) var shortcut: HotKeyShortcut
    @Published private(set) var message: String?

    private let controller: HotKeyControlling

    init(
        action: HotKeyAction = .showMainWindow,
        shortcut: HotKeyShortcut? = nil,
        controller: HotKeyControlling? = nil
    ) {
        self.action = action
        self.shortcut = shortcut ?? HotKeyPreferences.shortcut(for: action)
        self.controller = controller ?? GlobalHotKeyController(action: action)
    }

    func start() {
        guard !controller.register(shortcut: shortcut) else {
            message = nil
            return
        }

        let unavailableShortcut = shortcut
        if unavailableShortcut != action.defaultShortcut,
           controller.register(shortcut: action.defaultShortcut) {
            HotKeyPreferences.resetShortcut(for: action)
            shortcut = action.defaultShortcut
            message = fallbackToDefaultMessage(unavailableShortcut: unavailableShortcut)
            return
        }

        shortcut = controller.shortcut
        message = disabledMessage(unavailableShortcut)
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
        HotKeyPreferences.setShortcut(newShortcut, for: action)
        switch controller.updateShortcut(newShortcut) {
        case .updated:
            shortcut = newShortcut
            message = nil
            return true
        case .newShortcutUnavailable(let restoredPrevious):
            HotKeyPreferences.setShortcut(previousShortcut, for: action)
            shortcut = previousShortcut
            message = restoredPrevious
                ? unavailableMessage(for: newShortcut)
                : restoreFailedMessage(unavailableShortcut: newShortcut, previousShortcut: previousShortcut)
            return false
        }
    }

    func reset() {
        HotKeyPreferences.resetShortcut(for: action)
        _ = save(action.defaultShortcut)
    }

    private func unavailableMessage(for shortcut: HotKeyShortcut) -> String {
        "“\(shortcut.displayString)” 可能已被系统或其他应用占用。请换一个快捷键。"
    }

    private func fallbackToDefaultMessage(unavailableShortcut: HotKeyShortcut) -> String {
        "“\(unavailableShortcut.displayString)” 可能已被占用，已恢复为默认快捷键“\(action.defaultShortcut.displayString)”。"
    }

    private func restoreFailedMessage(
        unavailableShortcut: HotKeyShortcut,
        previousShortcut: HotKeyShortcut
    ) -> String {
        "“\(unavailableShortcut.displayString)” 可能已被占用，且原快捷键“\(previousShortcut.displayString)”未能恢复。请重新设置。"
    }

    private func disabledMessage(_ unavailableShortcut: HotKeyShortcut) -> String {
        "“\(unavailableShortcut.displayString)” 可能已被系统或其他应用占用，当前快捷键未启用。"
    }
}
