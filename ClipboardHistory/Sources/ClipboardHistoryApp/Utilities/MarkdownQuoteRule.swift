import AppKit

/// 引用块的导引线：几何与配色都收在这里，正文那一侧只留一次枚举 + 一次填充。
///
/// 为什么要有这条线（R439）：引用此前只靠 `MarkdownPresentation.quoteIndent` 的 18pt 缩进
/// 与正文分层。缩进确实在亮暗两档都成立（`quoteColor` 的注释记了两次配色弱化为什么被否），
/// 但**一段被缩进的文字到底是引用还是列表续行**，只靠左侧 18pt 的空白是答不出来的 ——
/// 列表续行也缩进 16pt。macOS 自己的 Mail / Notes / Pages 在引用左侧都有一条竖线：
/// 它是"这段属于引文"的结构标记，不参与文字配色，所以不会重蹈那两次对比度事故。
///
/// 坐标约定：`textSpan` 是 `NSLayoutManager` 给的**文本容器内坐标**（本 App 的正文视图
/// `textContainerInset.width == DetailTypography.containerGutter`），`containerOriginX`
/// 是同一份 inset。第 `level` 级的线落在容器原点右侧 `leadingOffset + (level-1) * quoteIndent`，
/// 与第 `level` 级引用文字的 `quoteIndent` 缩进并排：最内一级的线到文字左沿恒为
/// `textClearance`（11pt），嵌套一级就在里面再画一条。判据（帧上）读的就是这两件事：
/// 规则带里的最长竖墨段、以及引用文字左沿减去规则带右沿的净距。
enum MarkdownQuoteRule {
    static let width: CGFloat = 2
    static let leadingOffset: CGFloat = 5
    static let cornerRadius: CGFloat = 1

    /// 动态色，不做 `withAlphaComponent`：那一族的坑记在
    /// `MarkdownPresentation.quoteColor` 的注释里（暗档会被烤成 aqua 的黑）。
    static var color: NSColor { .secondaryLabelColor }

    static func ruleX(containerOriginX: CGFloat, level: Int) -> CGFloat {
        containerOriginX + leadingOffset + CGFloat(max(level, 1) - 1) * MarkdownPresentation.quoteIndent
    }

    /// 最内一级的线到引用文字左沿的净距。`quoteIndent - leadingOffset - width` = 11。
    static var textClearance: CGFloat {
        MarkdownPresentation.quoteIndent - leadingOffset - width
    }

    /// 一段引用（可能是多级嵌套）要画的线。`textSpan` 只用来取纵向区间 ——
    /// 横向由级别决定，不跟着每行字形的 bounding box 走（那会把线画在文字里）。
    static func ruleRects(containerOriginX: CGFloat, textSpan: CGRect, quoteDepth: Int) -> [CGRect] {
        guard quoteDepth > 0, textSpan.height > 0 else { return [] }
        return (1...quoteDepth).map { level in
            CGRect(x: ruleX(containerOriginX: containerOriginX, level: level),
                   y: textSpan.minY,
                   width: width,
                   height: textSpan.height)
        }
    }
}
