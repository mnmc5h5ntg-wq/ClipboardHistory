import AppKit

/// 详情区的排版约束（第三轮审计 §4 U-4）。
///
/// 单独成文件的原因有两个，都不是"整洁"这种理由：
/// 1. **列宽必须能从字体推出来，而不是抄一个像素数**。审计建议写的是"≤68ch 或 640pt"，
///    这两个数只在当前 14pt 等宽正文下等价；字号一改，640pt 就不再是 68 个字符。
///    所以这里把上限用**字符数**表达，宽度由实际字形的推进算出来，
///    于是"改了字号行长会不会爆"这件事自己跟着变，而不需要有人记得来改常数。
/// 2. 可读行长、meta 文案格式、命中色这三件事都是会被"看着不顺眼就顺手调一下"改动的，
///    放进视图里就只能靠肉眼复核。
enum DetailTypography {
    /// 正文一行的字符上限。排版惯例的可读区间是 45–75ch，取上沿偏中：
    /// 详情正文常常是代码、命令、URL 这类**要数着看**的内容，行太长丢行的代价比小说高。
    static let maximumCharactersPerLine = 68

    /// 正文字号。改这里要同时看 `columnWidth`：行长上限是按这个字号的推进算的。
    static let bodyFontSize: CGFloat = 14
    static let metaFontSize: CGFloat = 11

    /// 文本容器的左右内缩。**必须与 `ChineseSelectableTextView` 的
    /// `textContainerInset.width` 是同一个数** —— 它们不一致的话 meta 行和正文就不同左缘，
    /// 而"两行文字没对齐"这种缺陷在帧上一眼能看见、在代码里看不出来。
    static let containerGutter: CGFloat = 20

    static var bodyFont: NSFont { .monospacedSystemFont(ofSize: bodyFontSize, weight: .regular) }

    /// 一个字形的推进宽度（等宽字体下就是 ch 宽）。
    static func advance(of font: NSFont) -> CGFloat {
        let measured = ("0" as NSString).size(withAttributes: [.font: font]).width
        // 向上取整：68ch 的列如果按 8.4pt 的亚像素推进算，换行点会落在半个字上，
        // 实测会让最后一列偶尔挤进 69 个字符。宁可空一点。
        return measured > 0 ? ceil(measured) : 8
    }

    /// 正文列的最大宽度：左右内缩 + 上限字符宽。
    /// `containerWidth` 传进来时取两者较小值 —— 窄窗口里不能反过来把窗口撑宽。
    static func columnWidth(containerWidth: CGFloat? = nil,
                            font: NSFont = bodyFont,
                            glyphAdvance: CGFloat? = nil,
                            gutter: CGFloat = containerGutter,
                            characters: Int = maximumCharactersPerLine) -> CGFloat {
        // 参数刻意叫 `glyphAdvance` 而不是 `advance`：同名会把静态方法 `advance(of:)` 挡掉，
        // 编译器报的是"cannot call value of non-function type 'CGFloat?'"，一眼看不出是遮蔽。
        let ch = glyphAdvance ?? advance(of: font)
        let measure = gutter * 2 + ch * CGFloat(max(characters, 1))
        guard let containerWidth, containerWidth > 0 else { return measure }
        return min(containerWidth, measure)
    }

    /// 头部那一行 meta。刻意是**一条**、左对齐、比正文弱（U-4 原本的问题：两行居中 meta
    /// 与正文抢注意力，而且居中的元信息读起来要先找它属于谁）。
    static func metaText(copiedAt: String, size: String, sourceAppName: String?) -> String {
        var pieces = ["\(copiedAt) 复制", size]
        if let sourceAppName, !sourceAppName.isEmpty {
            pieces.append("来自 \(sourceAppName)")
        }
        return pieces.joined(separator: "  ·  ")
    }

    /// 搜索命中的底色。
    ///
    /// 刻意不是"选中色"：正文里选一段和"这就是你要找的词"是两件事，用同一个颜色会把
    /// 用户正在选的东西误读成命中。alpha 取 0.32 是为了让 `.labelColor` 的正文
    /// 在亮暗两种底色下都还保住可读性（实际数字在 detail-text-highlight 帧上复量，
    /// 记在 `AGENT_UI_AUDIT.md`，换字号或换底色要重新量）。
    static let highlightColor = NSColor.systemYellow.withAlphaComponent(0.32)
}
