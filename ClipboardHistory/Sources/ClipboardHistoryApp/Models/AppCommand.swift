import AppKit

enum AppCommand: CaseIterable, Equatable {
    case showMainWindow
    case toggleMainWindowCollapse
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
        case .toggleMainWindowCollapse:
            return "折叠/展开窗口"
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
        // R525：折叠/展开以前只有状态菜单与界面入口，没有应用菜单项也没有键盘键。
        // 补一个应用级 ⌘\：Window 菜单与状态菜单都挂同一个 `perform(.toggleMainWindowCollapse)`，
        // 不是第二条触发路径（同一个 command 的两种呈现）。
        case .toggleMainWindowCollapse:
            return "\\"
        // 快速选择在菜单里没有本地键等价物：它的全局快捷键走 Carbon 注册（⌃⌥⇧V），
        // 在这里再挂一个 ⌘ 组合会凭空造出第二条按键路径，两条路迟早行为不一致。
        case .showMainWindow, .showQuickPick, .refreshHistory,
             .clearHistory, .dismissAllRecommendations:
            return ""
        }
    }

    var keyModifiers: NSEvent.ModifierFlags {
        keyEquivalent.isEmpty ? [] : .command
    }

    /// 菜单里的破坏性命令用系统红：与批量栏垃圾桶、确认弹窗同一套危险语言。
    /// 只有「清空未收藏」会真的删数据；退出、刷新、打开窗口都不是。
    var isDestructive: Bool { self == .clearHistory }
}

enum AppCommandCatalog {
    static let menuBarCommands: [AppCommand] = [
        .showMainWindow,
        .toggleMainWindowCollapse,
        .showQuickPick,
        .showSettings,
        .clearHistory,
        .quit
    ]
}
