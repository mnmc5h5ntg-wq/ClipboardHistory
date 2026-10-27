import AppKit

/// 代码块的**左侧外边距行号**。
///
/// 为什么要这一层（R441）：代码块是剪贴板里最常见的一类内容（命令、片段、配置），
/// 而详情区是一整段只读正文 —— 贴一段 30 行的脚本进来，读者数不清第几行，
/// 也没法和同事说"第 12 行那个括号"。
///
/// 行号**不进正文、也不挤正文**：正文照旧从容器原点（20pt）起排，
/// 行号画在容器左侧那 20pt 外边距里、右对齐到原点左 3pt。
/// 这样不挪正文、不动代码块的灰底（属性串那一层原样保留），只多出一条槽。
/// 行号也不进文本存储：复制/搜索都拿不到这些数字。
///
/// 99 行以内用 11pt；三位数（≥100 行）收成 9pt —— 20pt 的外边距放不下
/// 3 个 11pt 等宽数字（20.4pt），而 9pt 的 3 位是 ~16.8pt。
/// 四位数（≥1000 行）会再超一点：剪贴板条目的长度上限先到，记在 BACKLOG 里不假装解决。
enum CodeBlockLineNumbers {
    static let fontSize: CGFloat = 11
    static let compactFontSize: CGFloat = 9
    static let compactThreshold: Int = 100
    /// 数字右沿到正文容器原点的距离（即行号右沿 = 正文左沿 - 3pt）。
    static let marginInset: CGFloat = 3

    static func font(forLineCount count: Int) -> NSFont {
        .monospacedSystemFont(ofSize: count >= compactThreshold ? compactFontSize : fontSize,
                              weight: .regular)
    }

    /// 动态色：槽里的数字是元信息，不能比代码更抢眼，也不许在暗档被烤成黑的。
    static var color: NSColor { .secondaryLabelColor }

    static func lineCount(in content: String) -> Int {
        guard !content.isEmpty else { return 0 }
        return content.components(separatedBy: "\n").count
    }

    static func digitCount(forLineCount count: Int) -> Int {
        String(max(count, 1)).count
    }

    /// 第 `line` 个行号的绘制原点：右对齐到 `containerOriginX - marginInset`。
    static func numberOrigin(containerOriginX: CGFloat, line: Int, font: NSFont,
                             lineTop: CGFloat, lineHeight: CGFloat, numberHeight: CGFloat) -> CGPoint {
        let text = "\(line)" as NSString
        let width = text.size(withAttributes: [.font: font]).width
        return CGPoint(x: containerOriginX - marginInset - width,
                       y: lineTop + max(0, (lineHeight - numberHeight) / 2))
    }
}
