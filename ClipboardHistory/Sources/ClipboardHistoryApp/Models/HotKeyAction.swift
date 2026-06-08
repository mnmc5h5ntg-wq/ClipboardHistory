import Foundation

enum HotKeyAction: CaseIterable {
    case showMainWindow
    case repeatCopy

    var title: String {
        switch self {
        case .showMainWindow:
            return "呼出主窗口"
        case .repeatCopy:
            return "再次复制"
        }
    }

    var description: String {
        switch self {
        case .showMainWindow:
            return "关闭或隐藏主窗口后，可使用此快捷键重新打开。"
        case .repeatCopy:
            return "把当前选中的历史记录再次复制到剪贴板。"
        }
    }

    var defaultShortcut: HotKeyShortcut {
        switch self {
        case .showMainWindow:
            return .defaultShortcut
        case .repeatCopy:
            return .defaultRepeatCopyShortcut
        }
    }

    var preferenceKey: String {
        switch self {
        case .showMainWindow:
            return "showMainWindowHotKeyShortcut"
        case .repeatCopy:
            return "repeatCopyHotKeyShortcut"
        }
    }

    var hotKeyIdentifier: UInt32 {
        switch self {
        case .showMainWindow:
            return 1
        case .repeatCopy:
            return 2
        }
    }

    var probeHotKeyIdentifier: UInt32 {
        hotKeyIdentifier + 1_000
    }

    var notificationName: Notification.Name {
        switch self {
        case .showMainWindow:
            return .showMainWindowHotKeyPressed
        case .repeatCopy:
            return .repeatCopyHotKeyPressed
        }
    }

    init?(hotKeyIdentifier: UInt32) {
        switch hotKeyIdentifier {
        case Self.showMainWindow.hotKeyIdentifier:
            self = .showMainWindow
        case Self.repeatCopy.hotKeyIdentifier:
            self = .repeatCopy
        default:
            return nil
        }
    }
}
