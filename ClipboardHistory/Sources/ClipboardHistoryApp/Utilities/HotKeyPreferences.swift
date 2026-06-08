import Foundation

enum HotKeyPreferences {
    static var showMainWindowShortcut: HotKeyShortcut {
        get {
            shortcut(for: .showMainWindow)
        }
        set {
            setShortcut(newValue, for: .showMainWindow)
        }
    }

    static var repeatCopyShortcut: HotKeyShortcut {
        get {
            shortcut(for: .repeatCopy)
        }
        set {
            setShortcut(newValue, for: .repeatCopy)
        }
    }

    static func resetShowMainWindowShortcut() {
        resetShortcut(for: .showMainWindow)
    }

    static func resetRepeatCopyShortcut() {
        resetShortcut(for: .repeatCopy)
    }

    static func shortcut(for action: HotKeyAction) -> HotKeyShortcut {
        guard let data = UserDefaults.standard.data(forKey: action.preferenceKey),
              let shortcut = try? JSONDecoder().decode(HotKeyShortcut.self, from: data),
              shortcut.isValid else {
            return action.defaultShortcut
        }
        return shortcut
    }

    static func setShortcut(_ shortcut: HotKeyShortcut, for action: HotKeyAction) {
        guard let data = try? JSONEncoder().encode(shortcut) else { return }
        UserDefaults.standard.set(data, forKey: action.preferenceKey)
    }

    static func resetShortcut(for action: HotKeyAction) {
        UserDefaults.standard.removeObject(forKey: action.preferenceKey)
    }
}
