import AppKit

/// 列表项的**悬挂缩进**：首行正文与续行必须落在同一条竖轴上（R451）。
///
/// 缺陷形状：`headIndent` 是 `firstLineHeadIndent + 16`，但首行正文靠一个 `\t`
/// 走的是**默认制表位**（28pt）—— 首行正文在 28/48pt、续行在 16/36pt，
/// 多行列表项一折行就错开 12pt。修法：给列表块一个**显式制表位**，
/// 位置 = `firstLineHeadIndent + max(16, 标记宽 + 2)`，并让 `headIndent` 用同一个数；
/// 标记本身不挪，正文列跟着标记宽度走（两三位数的编号也不会撞到下一档）。
enum ListHangingIndent {
    /// 标记与正文之间的最小列宽；1 位数字/项目符号都落在这里。
    static let minimumAdvance: CGFloat = 16
    static let markerGap: CGFloat = 2

    /// 正文列相对段落原点的 x。
    static func advance(firstLineIndent: CGFloat, markerWidth: CGFloat) -> CGFloat {
        firstLineIndent + max(minimumAdvance, markerWidth + markerGap)
    }
}
