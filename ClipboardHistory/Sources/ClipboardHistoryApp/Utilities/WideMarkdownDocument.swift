import AppKit

/// 宽代码/宽表格的文档宽度（R459）。
///
/// U-4 把正文限成 68ch 可读列，超长行折行 —— 那条规则是给**散文**的。
/// 表格与代码不是散文：一行表格在中间折开，列就散了；一行代码折开，缩进就不是缩进。
/// 这里只量代码块与表格块的最宽行，文档比可读列宽时才允许横向滚动；
/// 判断只发生在渲染态，源文/纯文本那条路不动。
enum WideMarkdownDocument {
    /// 返回文本视图应该用的文档宽度（含左右 `gutter`）。没有宽块时原样返回 `columnWidth`。
    static func width(source: String, columnWidth: CGFloat, font: NSFont, gutter: CGFloat) -> CGFloat {
        var widest: CGFloat = 0
        for block in MarkdownParser.parse(source).blocks {
            switch block.kind {
            case .codeBlock:
                for line in MarkdownPresentation.blockText(block).components(separatedBy: "\n") {
                    let measured = (line as NSString).size(withAttributes: [.font: font]).width
                    widest = max(widest, measured)
                }
            case .table:
                // R488：表格行现在用 tab 停靠；总宽必须按最后一列右沿量，不能量源码行。
                widest = max(widest, MarkdownTablePresentation.measuredWidth(
                    in: MarkdownPresentation.blockText(block)))
            default:
                continue
            }
        }
        guard widest > 0 else { return columnWidth }
        return max(columnWidth, min(widest + gutter * 2, 6000))
    }
}
