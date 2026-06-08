import AppKit

enum AppCommand: CaseIterable, Equatable {
    case showMainWindow
    case showSettings
    case refreshHistory
    case clearHistory
    case quit

    var title: String {
        switch self {
        case .showMainWindow:
            return "显示主窗口"
        case .showSettings:
            return "设置…"
        case .refreshHistory:
            return "刷新历史"
        case .clearHistory:
            return "清空未收藏…"
        case .quit:
            return "退出时间剪史"
        }
    }

    var keyEquivalent: String {
        switch self {
        case .showSettings:
            return ","
        case .quit:
            return "q"
        case .showMainWindow, .refreshHistory, .clearHistory:
            return ""
        }
    }

    var keyModifiers: NSEvent.ModifierFlags {
        keyEquivalent.isEmpty ? [] : .command
    }
}

enum AppCommandCatalog {
    static let menuBarCommands: [AppCommand] = [
        .showMainWindow,
        .showSettings,
        .refreshHistory,
        .clearHistory,
        .quit
    ]
}
