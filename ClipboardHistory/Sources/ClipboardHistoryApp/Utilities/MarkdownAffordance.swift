import Foundation

/// "这条记录要不要给「渲染 / 原文」那颗控件" —— 薄胶水层。
///
/// 判定本身在 `MarkdownParsingPolicy`（纯函数），这里只做一件事：
/// 把它翻译成"界面上有没有这个入口"。单独成文件是为了让**视图里一个 if 都不带业务**，
/// 也让这条判定有一处可以被源码锚点测试钉住的地方（`AGENTS.md` 定义完成标准第 1 条）。
enum MarkdownRenderingAffordance {
    /// 这条记录有没有"渲染 / 原文"之分。
    ///
    /// `exists` 是注入进来的，不是顺手写的：文件那两路要问"文件还在不在"，
    /// 而把 `FileManager` 直接调进来看起来无害，实际会让这条判定在测试里
    /// 依赖真实磁盘（以及让视图层没法测"文件被移走"那一支）。
    /// 判据侧传桩，产品侧传真实存在性检查。
    static func offers(for content: ClipboardEntryContent, exists: (URL) -> Bool) -> Bool {
        switch content {
        case .text(let text):
            return MarkdownParsingPolicy.offersRendering(forText: text)
        case .image:
            // 图片没有"原文"可言。OCR 文字是另一件事（F-4），不要混进这个入口。
            return false
        case .file(let url):
            // 文件已经不在了就没有"两种看法"：预览给的是"文件已移动或删除"，
            // 这时候摆一颗切了什么都不会变的控件，是在承诺一个做不到的动作。
            return exists(url) && MarkdownParsingPolicy.isMarkdownFile(url)
        case .files(let urls):
            // 多文件里只要有一个还在的 Markdown，头部那颗控件就有意义：
            // 展开的每一条都走同一个 `DetailFileView`，切换会同时作用在它们身上。
            return urls.contains { exists($0) && MarkdownParsingPolicy.isMarkdownFile($0) }
        }
    }

    /// 产品侧用的那一份：存在性就问文件系统。
    static func offers(for content: ClipboardEntryContent) -> Bool {
        offers(for: content) { FileManager.default.fileExists(atPath: $0.path) }
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
