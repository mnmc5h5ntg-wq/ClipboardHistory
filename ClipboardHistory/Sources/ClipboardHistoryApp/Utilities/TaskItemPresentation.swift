import AppKit

/// Markdown 任务项的**完成态文字弱化**（R450）。
///
/// 缺陷形状：勾选态只落在 `☑`/`☐` 这两个小字形上，正文和未完成项同色同重 ——
/// 一眼扫一份清单，分不出哪些已经做完。完成项的文字降到次要色，`☑` 标记保留：
/// 完成态还在（复制/读屏都拿得到标记），但视觉上退到后一排。
enum TaskItemPresentation {
    static func dimsText(_ state: MarkdownBlock.TaskState?) -> Bool { state == .checked }

    /// 动态色：完成项文字用次要色；未完成/普通项不动。
    static var completedTextColor: NSColor { .secondaryLabelColor }
}
