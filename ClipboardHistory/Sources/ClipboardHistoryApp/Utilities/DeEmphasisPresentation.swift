import AppKit

/// 弱化正文（已完成任务项、删除线）的**颜色**：仍要比正文弱，但必须过 14pt 正文的 4.5:1。
///
/// 为什么不用 `secondaryLabelColor`：`MarkdownPresentation` 里引用块的注释记过 ——
/// secondary 在亮档实测 **3.95:1**，低于 14pt 正文的 4.5:1；R450/R453 的弱化色沿用了它，
/// R454 把这条欠账补上（同一族：装饰不能把内容画糊）。
/// 动态色在 provider 里直接返回黑/白 + alpha：这里不能用 `labelColor.withAlphaComponent`
/// 在 provider 外解析（R30 那一族），provider 拿到 appearance 后给具体成分。
enum DeEmphasisPresentation {
    static var textColor: NSColor {
        NSColor(name: "deEmphasisText") { appearance in
            let dark = appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
            return dark
                ? NSColor.white.withAlphaComponent(0.62)
                : NSColor.black.withAlphaComponent(0.58)
        }
    }
}
