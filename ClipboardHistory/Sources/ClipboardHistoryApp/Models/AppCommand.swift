import AppKit

enum AppCommand: CaseIterable, Equatable {
    case showMainWindow
    case showQuickPick
    case showSettings
    case refreshHistory
    case clearHistory
    case dismissAllRecommendations
    case quit

    var title: String {
        switch self {
        case .showMainWindow:
            return "显示主窗口"
        case .showQuickPick:
            return "快速选择…"
        case .showSettings:
            return "设置"
        case .refreshHistory:
            return "刷新历史"
        case .clearHistory:
            return "清空未收藏"
        case .quit:
            return "退出时间剪史"
        case .dismissAllRecommendations:
            return "都不是我想要的"
        }
    }

    var keyEquivalent: String {
        switch self {
        case .showSettings:
            return ","
        case .quit:
            return "q"
        // 快速选择在菜单里没有本地键等价物：它的全局快捷键走 Carbon 注册（⌃⌥⇧V），
        // 在这里再挂一个 ⌘ 组合会凭空造出第二条按键路径，两条路迟早行为不一致。
        case .showMainWindow, .showQuickPick, .refreshHistory, .clearHistory, .dismissAllRecommendations:
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
        .clearHistory,
        .quit
    ]
}
