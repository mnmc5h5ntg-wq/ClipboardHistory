import AppKit

/// 表格表头的字重。
///
/// 为什么要这一层（R440）：`MarkdownScanner.collectTable` 会把 `| --- |` 那条分隔行丢掉，
/// 于是渲染出来的表格里「表头」与「表体」只剩**第一行**这个位置差别 —— 两者同字号、同字重、
/// 同颜色，作者写下的表头意图在屏幕上没有证人。修法只动字重：等宽字体的 semibold 与 regular
/// **推进宽度相同**，所以不会挪列，也不需要重排（R234 明确说过列重排是刻意不做的）。
///
/// 表头就是表格块的第一行 —— 这个事实来自 `collectTable`（它跳过第二行分隔线后，
/// 收集到的第一行必然是表头）。把它抽成纯函数，像素判据才能拿同一句话去复算。
enum TableHeaderPresentation {
    static var headerFont: NSFont {
        .monospacedSystemFont(ofSize: MarkdownPresentation.codeFontSize, weight: .semibold)
    }

    /// 表格块正文里第一行的字符范围（不含换行符）。没有内容或第一行是空行时返回 nil。
    static func headerRange(in content: String) -> NSRange? {
        guard !content.isEmpty else { return nil }
        let text = content as NSString
        let newline = text.range(of: "\n")
        let length = newline.location == NSNotFound ? text.length : newline.location
        guard length > 0 else { return nil }
        return NSRange(location: 0, length: length)
    }
}
