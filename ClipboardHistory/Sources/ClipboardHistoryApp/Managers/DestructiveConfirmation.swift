import AppKit

/// 危险操作确认。抽成协议是为了让"从菜单清空历史"这类破坏性动作可被单测覆盖
/// （审计发现该路径曾经绕过确认直接删除）。
@MainActor
protocol DestructiveConfirming {
    func confirm(
        title: String,
        message: String,
        confirmTitle: String,
        cancelTitle: String
    ) -> Bool
}

@MainActor
struct SystemDestructiveConfirming: DestructiveConfirming {
    func confirm(
        title: String,
        message: String,
        confirmTitle: String,
        cancelTitle: String
    ) -> Bool {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: confirmTitle)
        alert.addButton(withTitle: cancelTitle)
        return alert.runModal() == .alertFirstButtonReturn
    }
}
