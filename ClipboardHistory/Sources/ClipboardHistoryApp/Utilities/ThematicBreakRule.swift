import AppKit

/// Markdown **主题分隔线**（`---` / `***` / `___`）的绘制几何。
///
/// 为什么要有这一层（R447）：`MarkdownPresentation` 早先把主题分隔线渲染成 24 个
/// `─` 字符 —— 帧上是一条比正文窄、比行高厚的"假线"（长度由字数决定），
/// 复制渲染结果时还会把这 24 个字符带进剪贴板。主题分隔线是**装饰**，不是内容：
/// 它不该进文本存储，也不该由字数决定长短。
/// 现在属性串里只留一个占位空格（保住这一行的高度），线由正文视图画：
/// 通栏、1pt、动态 `secondaryLabelColor`，长度跟着列宽而不是字数。
enum ThematicBreakRule {
    /// 线的厚度（pt）。1pt 在 1x/2x 都是最细的可绘制线。
    static let thickness: CGFloat = 1
    /// 动态色：线是结构分隔，不是文案；暗档不许被烤成黑的。
    static var color: NSColor { .secondaryLabelColor }

    /// 属性串里这一块的占位文本：一个空格，保住行高；复制出来看不见。
    static let placeholder = " "

    /// 线的矩形：横跨整个正文列，纵向落在块那一行的中间。
    static func rect(containerOriginX: CGFloat, containerWidth: CGFloat,
                     lineTop: CGFloat, lineHeight: CGFloat) -> CGRect {
        let y = lineTop + max(0, (lineHeight - thickness) / 2)
        return CGRect(x: containerOriginX, y: y,
                      width: max(0, containerWidth), height: thickness)
    }
}
