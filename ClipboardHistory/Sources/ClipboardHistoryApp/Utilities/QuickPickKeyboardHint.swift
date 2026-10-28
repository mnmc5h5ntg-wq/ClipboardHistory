import AppKit

/// QuickPick 面板底部的**键盘操作提示**（R449）。
///
/// 缺陷形状：`↑`/`↓` 选择、`↵` 粘贴、`esc` 关闭这三组键全靠用户猜 ——
/// 面板底部一直是空白（旧帧最后一行以下没有任何墨）。这一行由 AppKit 约束
/// 钉在表格下方，表格让出它的高度；提示不进表格、不参与搜索匹配。
enum QuickPickKeyboardHint {
    static let text = "↑↓ 选择 · ↵ 粘贴 · esc 关闭"
    static let identifier = "quickPickKeyboardHint"
    static let height: CGFloat = 16
    static let bottomInset: CGFloat = 6
    static let topSpacing: CGFloat = 4
    static let horizontalInset: CGFloat = 12

    /// 与 `QuickPickController` 里其他元信息同一档字号（11pt）。
    static var font: NSFont { .systemFont(ofSize: VisualFont.meta) }
    /// 提示是元信息：比候选行弱一档，暗档用动态色。
    static var color: NSColor { .tertiaryLabelColor }
}
