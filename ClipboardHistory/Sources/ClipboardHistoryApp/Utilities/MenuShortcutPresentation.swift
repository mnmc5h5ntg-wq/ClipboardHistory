import Foundation

/// 菜单项上的全局快捷键提示。
///
/// 这些组合走 Carbon 全局热键，不是菜单的本地 key equivalent（`AppCommand.keyEquivalent`
/// 只给设置/退出挂 ⌘ 组合）。所以提示只写进标题的文字，**不**给菜单再挂一条本地快捷键 ——
/// 否则同一个组合会同时触发全局热键与菜单项，变成两条行为路径。
enum MenuShortcutPresentation {
    static func title(_ base: String, hint: String?) -> String {
        guard let hint = normalized(hint) else { return base }
        return "\(base)  \(hint)"
    }

    static func hint(for command: AppCommand,
                     showMainWindow: HotKeyShortcut?,
                     quickPick: HotKeyShortcut?) -> String? {
        switch command {
        case .showMainWindow:
            return showMainWindow?.displayString
        case .showQuickPick:
            return quickPick?.displayString
        default:
            return nil
        }
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
