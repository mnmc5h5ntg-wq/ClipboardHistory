import Foundation

/// 注入 ⌘V 之前对"目标应用还在不在前台"的复核（审计第二轮 B-6 / 03-04 / 账本 R2-12）。
///
/// 从复制到注入之间有约 250ms，这段时间里用户可能切走窗口，目标应用也可能自己退出。
/// 照常注入就会把内容粘进**别的**应用 —— 既是正确性问题也是隐私问题，而"粘错地方"比"不粘"更糟。
///
/// 纯函数，方便把每种组合都钉住；读系统状态的活儿留在 `ApplicationShell` 里。
enum PasteTargetCheck {
    enum Outcome: Equatable {
        /// 目标仍是当初那个应用，可以注入。
        case proceed
        /// 前台已经换成别的应用：取消注入。
        case targetChanged
        /// 目标进程已经退出：取消注入。
        case targetGone
    }

    /// - Parameters:
    ///   - expectedBundleID: 发起粘贴时那个前台应用的 bundle id。
    ///     `nil` = 当初就没识别出目标（例如它不是常规 App），此时**无从复核**，沿用旧行为放行，
    ///     而不是新增一条"识别不出就不粘"的拦截 —— 那会把可用的功能变坏。
    ///   - actualBundleID: 注入前一刻的前台应用。
    ///   - expectedTerminated: 目标进程是否已退出。
    static func evaluate(
        expectedBundleID: String?,
        actualBundleID: String?,
        expectedTerminated: Bool
    ) -> Outcome {
        guard let expectedBundleID else { return .proceed }
        // 退出优先于"bundle id 相同"：应用崩溃后被重新拉起时，前台那个同 id 的进程
        // 已经不是原来那个窗口/焦点上下文了，照样注入会粘到不确定的位置。宁可取消。
        if expectedTerminated { return .targetGone }
        return actualBundleID == expectedBundleID ? .proceed : .targetChanged
    }
}
