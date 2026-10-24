import Foundation

/// "这条记录要不要给「渲染 / 原文」那颗控件" —— 薄胶水层。
///
/// R335 起它**只做转发**，不再自己判任何一件事：判定全部住在 `DetailRenderPolicy`。
/// 为什么这是硬规矩而不是整洁：这一层以前自己判"有没有两种看法"，视图那边又判
/// "点下去画哪一种"，两处就会漂 —— R335 第一版真的漂出了一个小而准的假话：
/// `.html` **文件**条目的提示语写的是"与 Markdown 原文之间切换"，而 `.helpLabel`
/// 同时喂 `.help` 与 `accessibilityLabel` ⇒ VoiceOver 会把那句错话念给用户听。
/// 判据抓不到它（它不在帧上，也不在属性串里），只有"一处回答"能抓住它。
enum MarkdownRenderingAffordance {
    /// 这条记录有没有"渲染 / 原文"之分。
    ///
    /// `exists` 是注入进来的，不是顺手写的：文件那两路要问"文件还在不在"，
    /// 而把 `FileManager` 直接调进来看起来无害，实际会让这条判定在测试里
    /// 依赖真实磁盘（以及让视图层没法测"文件被移走"那一支）。
    /// 判据侧传桩，产品侧传真实存在性检查。
    ///
    /// 签名里**没有载荷**，所以这一份回答的是"没有载荷时"的那一种；
    /// 带载荷的条目（真存档里的富文本）由 `DetailView` 直接问
    /// `DetailRenderPolicy.renderers(for:htmlPayload:)` —— 少问一个输入就会答错一个条目，
    /// 这一层不该假装自己能看见它看不见的东西。
    static func offers(for content: ClipboardEntryContent, exists: (URL) -> Bool) -> Bool {
        !DetailRenderPolicy.renderers(for: content, htmlPayload: nil, exists: exists).isEmpty
    }

    /// 产品侧用的那一份：存在性就问文件系统。
    static func offers(for content: ClipboardEntryContent) -> Bool {
        offers(for: content) { FileManager.default.fileExists(atPath: $0.path) }
    }

    /// 某个具体文件该不该渲染（`DetailFileView` 用）。
    /// 文本条目那一路不需要它 —— 那边的判定已经在 `offers(for:)` 里做完。
    ///
    /// 同样**整句转发**：扩展名能不能渲染，答案只有一处（`DetailRenderPolicy.renderer(forFile:)`）。
    /// R335 起它认 `.html` / `.htm`，不再只认 Markdown —— 以前那一支落在"其它文本文件"，
    /// 等宽显示源码，也就是**没有任何预览**（用户点名的就是这一格）。
    static func renders(url: URL, in mode: MarkdownPreviewMode) -> Bool {
        mode == .rendered && DetailRenderPolicy.renderer(forFile: url) != nil
    }

    // `renders(text:in:)` 在 R335 被删（现读 grep：0 个调用点）。
    // 留着的代价不是"多一行死代码"，是**第二个权威**：它的签名看不见 HTML 载荷，
    // 于是任何用它决定的地方都会把"带载荷的文本条目"答成 Markdown 那一种。
}
