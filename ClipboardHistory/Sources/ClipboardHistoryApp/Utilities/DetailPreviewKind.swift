import Foundation

/// 详情预览的**类型身份**：只有它变了，才有一整块子视图被插入/移除。
///
/// 换页动效挂在它上面（`DetailView` 的 `.animation(value:)`），因为这是两件事：
/// 「同一类内容换了字」用户要读的是新内容，不需要被解释；
/// 「整块界面被换掉」（文本 → 图片）才需要一次软交接。
/// 挂在 `entry.id` 上会把两件事混成一件 —— 那样每次方向键翻记录都演一遍。
///
/// 纯值、可断言：`MotionCatalogTests` 直接问"这两条记录之间换没换类型"。
///
/// 粒度必须和 `DetailView.preview(for:)` 的分支**一一对应**：它是"视图类型身份"，
/// 不是"内容语义"。所以 `.file` 不再按 md/非 md 细分 —— 那两种走的是同一个视图，
/// 根本没有子视图被插入/移除，细分出来的是一个永远不会执行的承诺。
enum DetailPreviewKind: Hashable {
    case renderedText
    case rawText
    case image
    case file
    case files

    init(entry: ClipboardEntry, markdownMode: MarkdownPreviewMode) {
        switch entry.content {
        case .text(let text):
            // 渲染态与原文态是**两个不同的视图**（属性串 vs 纯文本），
            // 点那颗切换控件时整块会换掉 —— 所以它们是两种类型，不是同一种。
            self = MarkdownRenderingAffordance.renders(text: text, in: markdownMode) ? .renderedText : .rawText
        case .image:
            self = .image
        case .file:
            self = .file
        case .files:
            self = .files
        }
    }
}
