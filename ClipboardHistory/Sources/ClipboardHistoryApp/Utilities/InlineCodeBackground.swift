import AppKit

/// 行内代码底色的**内边距**（R455）。
///
/// 缺陷形状：`.backgroundColor` 只按字形 advance 涂 —— 实测底色带 94.5pt、字宽 92.0pt，
/// 左右各只有 ~1pt，行内码和相邻正文挤在一起。
/// 改成背景层自绘：只向**空白侧**各让 3pt（前一个是空格/行首、后一个是空格/行尾）——
/// 紧贴标点时不让，否则底色会盖到后随的“。”上。上下各 1pt，圆角 2pt。
enum InlineCodeBackground {
    static let horizontalPadding: CGFloat = 4
    static let verticalPadding: CGFloat = 1
    static let cornerRadius: CGFloat = 2
    static var color: NSColor { MarkdownPresentation.codeBackground }

    /// 只在空白侧加 padding：`previousIsWhitespace` / `nextIsWhitespaceOrEnd` 由调用方
    /// 从文本存储的前后字符判定（行首/行尾算空白）。
    static func horizontalPaddings(previousIsWhitespace: Bool,
                                   nextIsWhitespaceOrEnd: Bool) -> (left: CGFloat, right: CGFloat) {
        (previousIsWhitespace ? horizontalPadding : 0,
         nextIsWhitespaceOrEnd ? horizontalPadding : 0)
    }

    static func rect(lineRect: CGRect, startX: CGFloat, endX: CGFloat,
                     leftPadding: CGFloat, rightPadding: CGFloat,
                     containerOrigin: CGPoint) -> CGRect {
        CGRect(x: containerOrigin.x + startX - leftPadding,
               y: containerOrigin.y + lineRect.minY - verticalPadding,
               width: max(0, endX - startX) + leftPadding + rightPadding,
               height: lineRect.height + verticalPadding * 2)
    }
}
