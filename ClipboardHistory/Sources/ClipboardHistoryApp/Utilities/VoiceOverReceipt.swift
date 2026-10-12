import AppKit

/// 给读屏用户播报一次状态变化（动效审计 MC-13）。
///
/// 为什么需要这一层：`copyConfirmed` 以前只改 `.help()` / `accessibilityLabel`。
/// 而按钮**保持焦点**时 VoiceOver 不会自动重读标签 —— 于是视觉上有了"已复制"，
/// 读屏里什么都没有。动效替代不了这句话：减弱动态的人未必是听不见的人，
/// 看不见的人则一定拿不到那 1.1 秒的勾。
///
/// 版本边界是**编译器实测**的，不是查资料听来的：本机 SDK 报
/// `'AccessibilityNotification' is only available in macOS 14.0 or newer`
/// （spike：`swiftc -target arm64-apple-macos12.0` → 两条 availability 错误）。
/// 部署下限是 macOS 12 ⇒ 12/13 这一档**没有**播报，只剩标签变化。
/// 这条缺口写进 `AGENT_UI_AUDIT` 的未覆盖项，不当成已修；
/// `announce` 因此返回 Bool —— "没播出去"必须是一个能被断言的事实，而不是一个静默的分支。
enum VoiceOverReceipt {
    /// 播报一次状态变化。不受 reduce-motion 影响：读屏播报不是动效。
    @discardableResult
    static func announce(_ text: String) -> Bool {
        guard !text.isEmpty else { return false }
        if #available(macOS 14.0, *) {
            AccessibilityNotification.Announcement(text).post()
            return true
        }
        return false
    }

    /// 当前系统上这条播报到底发得出去吗。判据用它来要求"能发就必须发"，
    /// 而不是让 12/13 的缺口变成一条永远绿的断言。
    static var isSupported: Bool {
        if #available(macOS 14.0, *) { return true }
        return false
    }
}
