import AppKit

/// QuickPick 面板底部的**键盘操作提示**（R449）。
///
/// 缺陷形状：`↑`/`↓` 选择、`↵` 粘贴、`Esc` 关闭这三组键全靠用户猜 ——
/// 面板底部一直是空白（旧帧最后一行以下没有任何墨）。这一行由 AppKit 约束
/// 钉在表格下方，表格让出它的高度；提示不进表格、不参与搜索匹配。
enum QuickPickKeyboardHint {
    static let text = "↑↓ 选择 · ↵ 粘贴 · Esc 关闭"
    static let identifier = "quickPickKeyboardHint"
    static let height: CGFloat = 16
    static let bottomInset: CGFloat = 6
    static let topSpacing: CGFloat = 4
    static let horizontalInset: CGFloat = 12

    /// 与 `QuickPickController` 里其他元信息同一档字号（11pt）。
    static var font: NSFont { .systemFont(ofSize: VisualFont.meta) }
    /// 提示是元信息：比候选行弱一档，暗档用动态色。
    /// R565：从前是 `.tertiaryLabelColor` —— 帧上现读字芯 light (140,140,140)/底 255 ⇒ **3.36:1**、
    /// dark (127,127,127)/底 30 ⇒ **4.16:1**，两档都跌破 4.5:1，而这一句是浮层里唯一的功能性说明
    /// （R449 开它就是为了让用户不用猜键）。改成与全仓其余次要文字同一档的 `.secondaryLabelColor`
    /// （主列表时间行、行内标记、详情 meta 都是这一档）⇒ 仍然比候选行弱一档，设计意图一字未改。
    static var color: NSColor { .secondaryLabelColor }
}
