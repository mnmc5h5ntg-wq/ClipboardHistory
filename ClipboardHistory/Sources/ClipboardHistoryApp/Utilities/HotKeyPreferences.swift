import Foundation

enum HotKeyPreferences {
    private static let shortcutKey = "showMainWindowHotKeyShortcut"

    static var showMainWindowShortcut: HotKeyShortcut {
        get {
            guard let data = UserDefaults.standard.data(forKey: shortcutKey),
                  let shortcut = try? JSONDecoder().decode(HotKeyShortcut.self, from: data),
                  shortcut.isValid else {
                return .defaultShortcut
            }
            return shortcut
        }
        set {
            guard let data = try? JSONEncoder().encode(newValue) else { return }
            UserDefaults.standard.set(data, forKey: shortcutKey)
        }
    }

    static func resetShowMainWindowShortcut() {
        UserDefaults.standard.removeObject(forKey: shortcutKey)
    }
}
