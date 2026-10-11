import Foundation

/// "这条记录要不要给「渲染 / 原文」那颗控件" —— 薄胶水层。
///
/// 判定本身在 `MarkdownParsingPolicy`（纯函数），这里只做一件事：
/// 把它翻译成"界面上有没有这个入口"。单独成文件是为了让**视图里一个 if 都不带业务**，
/// 也让这条判定有一处可以被源码锚点测试钉住的地方（`AGENTS.md` 定义完成标准第 1 条）。
enum MarkdownRenderingAffordance {
    static func offers(for content: ClipboardEntryContent) -> Bool {
        switch content {
        case .text(let text):
            return MarkdownParsingPolicy.offersRendering(forText: text)
        case .image:
            // 图片没有"原文"可言。OCR 文字是另一件事（F-4），不要混进这个入口。
            return false
        case .file(let url):
            return MarkdownParsingPolicy.isMarkdownFile(url)
        case .files(let urls):
            // 多文件里只要有一个 Markdown，头部那颗控件就有意义：
            // 展开的每一条都走同一个 `DetailFileView`，切换会同时作用在它们身上。
            return urls.contains { MarkdownParsingPolicy.isMarkdownFile($0) }
        }
    }

    /// 某个具体文件在该不该渲染（`DetailFileView` 用）。
    /// 文本条目那一路不需要它 —— 那边的判定已经在 `offers(for:)` 里做完。
    static func renders(url: URL, in mode: MarkdownPreviewMode) -> Bool {
        mode == .rendered && MarkdownParsingPolicy.isMarkdownFile(url)
    }

    /// 文本条目在给定模式下要不要走渲染。
    static func renders(text: String, in mode: MarkdownPreviewMode) -> Bool {
        mode == .rendered && MarkdownParsingPolicy.offersRendering(forText: text)
    }
}
