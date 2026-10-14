import Foundation

/// 复制 → 自动粘贴这条链路上，**复制这一步的结论**（R40 / U-66）。
///
/// 来历：快速选择浮层回车、菜单栏点一条推荐，走的都是 `ApplicationShell.copyAndPasteEntry`：
/// 先把这条内容写进剪贴板，再把前台切回原目标应用、注入 ⌘V。
/// 修前第一步的**结果没人看** —— `copyHistoryEntry(entry)` 之后直接 `asyncAfter` 切应用、按键。
/// 于是写剪贴板失败时（剪贴板被别的过程锁住、内容编码失败、权限异常）发生的是：
/// 目标应用收到 ⌘V，粘出来的是**用户剪贴板里原来那点东西**。
/// 那比"什么都没发生"糟：用户以为粘的是刚选的那条，实际粘的是上一条无关内容 ——
/// 而且界面一句话都没说（`clipboardWriteErrorMessage` 全仓唯一的显示消费者是详情区那颗按钮）。
///
/// 为什么单独做成枚举 + 纯函数（而不是在调用点写一个 `if`）：
/// ① "nil 就是这次成了"依赖 `HistoryStore.writeToClipboard` 成功时把错误清成 nil 这个**约定**，
///    它必须被一张真值表钉住，否则哪天有人把清理那行删了，这条守卫会静默变成"永远放行"；
/// ② 取消时说什么话是产品行为（要同时说清"没粘"与"剪贴板里还是原内容"），
///    写在纯函数里才断言得到，而不是靠肉眼读调用点。
enum CopyThenPaste {
    enum Decision: Equatable {
        /// 复制成功了，可以继续把前台切回去、注入 ⌘V。
        case pasteNow
        /// 复制没成功：**不许**注入，并且要把这句原样说给用户。
        case cancel(reason: String)
    }

    /// - Parameter copyErrorMessage: 紧跟在复制之后读的 `HistoryStore.clipboardWriteErrorMessage`。
    static func decide(copyErrorMessage: String?) -> Decision {
        guard let copyErrorMessage else { return .pasteNow }
        return .cancel(reason: "复制到剪贴板失败：\(copyErrorMessage)。"
                       + "已取消自动粘贴 —— 剪贴板里仍是原来的内容，没有被替换。")
    }
}
