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

/// R487/R488：渲染态表格去源码竖线，并按列最大实宽用制表位对齐。
///
/// `collectTable` 把原始行（含 `|`）直接交给正文字体，于是"渲染"出来的表格
/// 仍是一段带竖线的源码。R487 先去掉语法字符；R488 发现只把竖线换空格时，
/// 列起点仍跟着作者源码里的空格走，长单元格会把第二列推歪 —— 于是改成
/// `\t` 分列 + 绝对制表位（表头 semibold、表体 regular 各用自己的字体量宽）。
/// R234 的"列重排刻意不做"仍然成立：这是对齐到列最大实宽，不是重排内容。
enum MarkdownTablePresentation {
    /// 单行去竖线（不做列对齐）：给只需要"没有源码语法"的调用与判据用。
    static func renderedRow(_ row: String) -> String {
        cells(in: row).joined(separator: "  ")
    }

    /// R488：列之间只用 `\t` 分隔；列起点由 `MarkdownPresentation` 给表格块设的
    /// `tabStops` 绝对对齐。表头 semibold 与表体 regular 的 CJK 实宽不同，
    /// 用空格补宽会在表头/表体之间残留一两格的漂移，制表位不吃这个差。
    static func renderedContent(_ rows: [String]) -> String {
        rows.map { cells(in: $0).joined(separator: "\t") }.joined(separator: "\n")
    }

    /// 每列之间留 12pt；返回第二列起每个制表位的绝对位置。
    static func columnStops(in content: String) -> [NSTextTab] {
        // 这里拿到的是**已渲染**的 tab 行（没有竖线），按 tab 切列。
        let parsed = content.components(separatedBy: "\n")
            .map { $0.components(separatedBy: "\t") }
        guard let columnCount = parsed.map(\.count).max(), columnCount > 1 else { return [] }
        let fonts = parsed.indices.map { $0 == 0 ? TableHeaderPresentation.headerFont : MarkdownPresentation.codeFont }
        var widths = [CGFloat](repeating: 0, count: columnCount)
        for (rowIndex, row) in parsed.enumerated() {
            for (column, cell) in row.enumerated() {
                widths[column] = max(widths[column], width(of: cell, font: fonts[rowIndex]))
            }
        }
        var stops: [NSTextTab] = []
        var position: CGFloat = 0
        for column in 0..<(columnCount - 1) {
            position += widths[column] + 12
            stops.append(NSTextTab(textAlignment: .left, location: position))
        }
        return stops
    }

    /// 渲染后表格的总宽（最长一行的最后一列右沿），给宽表文档宽度用。
    static func measuredWidth(in content: String) -> CGFloat {
        let parsed = content.components(separatedBy: "\n")
            .map { $0.components(separatedBy: "\t") }
        guard let columnCount = parsed.map(\.count).max(), columnCount > 0 else { return 0 }
        let fonts = parsed.indices.map { $0 == 0 ? TableHeaderPresentation.headerFont : MarkdownPresentation.codeFont }
        let stops = columnStops(in: content)
        var widest: CGFloat = 0
        for (rowIndex, row) in parsed.enumerated() {
            let lastStart = stops.last?.location ?? 0
            let lastCell = row.last ?? ""
            widest = max(widest, lastStart + width(of: lastCell, font: fonts[rowIndex]))
        }
        return widest
    }

    private static func width(of text: String, font: NSFont) -> CGFloat {
        (text as NSString).size(withAttributes: [.font: font]).width
    }

    private static func cells(in row: String) -> [String] {
        var parts = row.components(separatedBy: "|")
            .map { $0.trimmingCharacters(in: .whitespaces) }
        while parts.first?.isEmpty == true { parts.removeFirst() }
        while parts.last?.isEmpty == true { parts.removeLast() }
        return parts
    }
}
