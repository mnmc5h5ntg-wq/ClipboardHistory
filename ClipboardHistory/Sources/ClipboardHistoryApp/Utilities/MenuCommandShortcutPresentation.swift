import SwiftUI

/// R505：macOS 13+ 的状态菜单是 SwiftUI `MenuBarExtra`，两条标准快捷键（⌘, / ⌘Q）
/// 之前既没有挂 `.keyboardShortcut`、也没有写进标题 ⇒ 菜单里一个字都不画。
/// 这里只补**标准键**的显示与菜单内触发；全局热键（⌃⌥⇧V 等）仍走标题里的行内提示，
/// 不给它们挂本地快捷键 —— 同一个组合会有 Carbon 与菜单两条触发路径。
enum MenuCommandShortcutPresentation {
    static func keyEquivalent(for command: AppCommand) -> String? {
        switch command {
        case .showSettings:
            return ","
        case .quit:
            return "q"
        case .toggleMainWindowCollapse:
            return "\\"
        case .showMainWindow, .showQuickPick, .refreshHistory,
             .clearHistory, .dismissAllRecommendations:
            return nil
        }
    }
}

@available(macOS 13, *)
struct MenuCommandShortcutModifier: ViewModifier {
    let command: AppCommand

    @ViewBuilder
    func body(content: Content) -> some View {
        if let key = MenuCommandShortcutPresentation.keyEquivalent(for: command),
           let scalar = key.unicodeScalars.first {
            content.keyboardShortcut(KeyEquivalent(Character(scalar)), modifiers: .command)
        } else {
            content
        }
    }
}
