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

/// 破坏性确认弹窗的按钮排布（纯值，便于单测）。
///
/// HIG：默认按钮必须是**最安全的动作**，Escape 必须取消。旧实现把"清空"放在第一位，
/// 于是 Return 直接触发破坏性动作（审计第二轮 1.7 / R2-06）。
enum DestructiveAlertLayout {
    struct Button: Equatable {
        let title: String
        let isDestructive: Bool
        /// 只有取消按钮拿 Return；破坏性按钮不设快捷键，必须显式点击。
        let keyEquivalent: String
    }

    static func buttons(confirmTitle: String, cancelTitle: String) -> [Button] {
        [
            Button(title: cancelTitle, isDestructive: false, keyEquivalent: "\r"),
            Button(title: confirmTitle, isDestructive: true, keyEquivalent: "")
        ]
    }

    /// `runModal()` 的返回值 → 用户是否确认。按钮顺序换过之后这里必须跟着换，
    /// 所以单独抽出来钉住：判错方向会把"取消"当成"清空历史"，比原缺陷更糟。
    static func isConfirmed(_ response: NSApplication.ModalResponse) -> Bool {
        response == .alertSecondButtonReturn
    }
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
        for button in DestructiveAlertLayout.buttons(confirmTitle: confirmTitle, cancelTitle: cancelTitle) {
            let added = alert.addButton(withTitle: button.title)
            added.keyEquivalent = button.keyEquivalent
            // 标成破坏性动作：系统会给它警示样式，并且不会把它当默认按钮。
            added.hasDestructiveAction = button.isDestructive
        }
        return DestructiveAlertLayout.isConfirmed(alert.runModal())
    }
}
