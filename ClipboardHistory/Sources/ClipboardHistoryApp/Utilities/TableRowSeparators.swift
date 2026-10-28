import AppKit

/// Markdown 表格**体行之间**的发丝分隔线。
///
/// 为什么要有这一层（R448）：R440 用等宽 semibold 把表头和表体分开之后，
/// 多行表体的行与行之间仍然没有横线 —— 四五行数值并排时，眼睛很容易串行
/// （剪贴板里的价格表、对照表是常态）。表头那一条已经由字重承担，
/// 所以这里**只画体行之间**：单行表体的表（如 `detail-table`）一帧都不变。
///
/// 线画在背景层、只有 1pt；行文本不进属性串、不被复制。宽度取表格文字自身的外接宽度，
/// 不是整个正文列 —— 一张窄表和一张宽表都只在自己的文字下方画线。
enum TableRowSeparators {
    /// 线的厚度（pt）。
    static let thickness: CGFloat = 1
    /// 动态色：比正文弱一档，暗档不许被烤成黑的。
    static var color: NSColor { .tertiaryLabelColor }

    /// 表格块正文的逻辑行数（表头 + 体行；解析层已丢掉 `| --- |` 那一行）。
    static func lineCount(in content: String) -> Int {
        guard !content.isEmpty else { return 0 }
        return content.components(separatedBy: "\n").count
    }

    /// 第 `row` 行（从 1 数，1 = 表头）之后要不要画线：
    /// 只在**两个体行之间**画 —— 表头之后不画、最后一行之后不画。
    static func shouldDraw(afterRow row: Int, totalRows: Int) -> Bool {
        row >= 2 && row < totalRows
    }

    /// 线的矩形：横跨表格文字的外接宽度，纵向贴在该行行片段的下沿。
    static func rect(containerOriginX: CGFloat, width: CGFloat, lineBottom: CGFloat) -> CGRect {
        CGRect(x: containerOriginX, y: lineBottom - thickness,
               width: max(0, width), height: thickness)
    }
}
