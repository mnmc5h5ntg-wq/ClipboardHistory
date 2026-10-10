import Foundation

enum HotKeyAction: CaseIterable {
    case showMainWindow
    case repeatCopy
    case quickPick

    var title: String {
        switch self {
        case .showMainWindow:
            return "呼出主窗口"
        case .repeatCopy:
            return "再次复制"
        case .quickPick:
            return "快速选择并粘贴"
        }
    }

    var description: String {
        switch self {
        case .showMainWindow:
            return "关闭或隐藏主窗口后，可使用此快捷键重新打开。"
        case .repeatCopy:
            return "把当前选中的历史记录再次复制到剪贴板。"
        case .quickPick:
            // 审计 §5 F-3 建议 ⌘⇧V。刻意**没有**照抄：⌘⇧V 在 Chrome / VS Code / Slack 里
            // 是"粘贴并匹配样式"，一个全局快捷键把它抢走，等于让所有用户的那个功能失灵。
            // 这里跟本产品既有约定同族（⌃⌥V / ⌃⌥C），改成 ⌃⌥⇧V；想用 ⌘⇧V 的人可以在下面自己录。
            return "在任意应用里呼出浮层，打字筛选后回车直接粘回原应用。默认 ⌃⌥⇧V —— "
                + "刻意不是 ⌘⇧V（那是浏览器和编辑器里的“粘贴并匹配样式”，全局抢走会让它们失灵）。"
        }
    }

    var defaultShortcut: HotKeyShortcut {
        switch self {
        case .showMainWindow:
            return .defaultShortcut
        case .repeatCopy:
            return .defaultRepeatCopyShortcut
        case .quickPick:
            return .defaultQuickPickShortcut
        }
    }

    var preferenceKey: String {
        switch self {
        case .showMainWindow:
            return "showMainWindowHotKeyShortcut"
        case .repeatCopy:
            return "repeatCopyHotKeyShortcut"
        case .quickPick:
            return "quickPickHotKeyShortcut"
        }
    }

    var hotKeyIdentifier: UInt32 {
        switch self {
        case .showMainWindow:
            return 1
        case .repeatCopy:
            return 2
        case .quickPick:
            return 3
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
        case .quickPick:
            return .quickPickHotKeyPressed
        }
    }

    init?(hotKeyIdentifier: UInt32) {
        switch hotKeyIdentifier {
        case Self.showMainWindow.hotKeyIdentifier:
            self = .showMainWindow
        case Self.repeatCopy.hotKeyIdentifier:
            self = .repeatCopy
        case Self.quickPick.hotKeyIdentifier:
            self = .quickPick
        default:
            return nil
        }
    }
}
