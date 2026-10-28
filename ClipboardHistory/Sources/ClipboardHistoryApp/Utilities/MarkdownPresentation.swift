import AppKit
import Foundation

/// Markdown 值模型 → `NSAttributedString`（详情区右半边那一栏的排版决定都在这）。
///
/// 这一层刻意只做"给哪段字加什么属性"，所有**数字**与**分叉**都写成可以单独断言的纯函数：
/// 字号、缩进、项目符号、中文强调到底用斜体还是字重 —— 留在视图里就只能靠肉眼看帧，
/// 而帧看不出"中文斜体其实是合成倾斜"这种只在特定字形上才暴露的问题。
enum MarkdownPresentation {
    // MARK: - 字号与字体

    /// Markdown 正文用**比例字体**（系统 SF），而普通文本条目的正文仍是等宽
    /// （`DetailTypography.bodyFont`：那通常是代码、命令、URL，要数着看）。
    /// 列宽两者共用同一个 `DetailTypography.columnWidth()`：14pt 下这个宽度
    /// 大约排得下 68 个拉丁字母或 40 个汉字，两个都在可读区间内，
    /// 于是"切换渲染/原文时正文列不动"这件事是几何上的必然，不是巧合。
    static let bodyFontSize: CGFloat = 14
    static let codeFontSize: CGFloat = 13

    static var bodyFont: NSFont { .systemFont(ofSize: bodyFontSize) }
    static var codeFont: NSFont { .monospacedSystemFont(ofSize: codeFontSize, weight: .regular) }

    /// 标题字阶。比值不是随手调的：一级到三级要"一眼分得出"，四到六级已经接近正文，
    /// 再拉开就会把详情区搞成海报。
    static func headingFontSize(level: Int) -> CGFloat {
        switch max(1, min(level, MarkdownParsingPolicy.maximumHeadingLevel)) {
        case 1: return 20
        case 2: return 17
        case 3: return 15.5
        case 4: return 14
        case 5: return 13
        default: return 12
        }
    }

    /// 六到一级的标题都至少不比正文小 —— 六级标题靠"粗 + 次要色"和正文分开，
    /// 而不是靠一个看不见的小字号。
    static func headingFont(level: Int) -> NSFont {
        let size = headingFontSize(level: level)
        let weight: NSFont.Weight = level <= 2 ? .bold : .semibold
        return .systemFont(ofSize: size, weight: weight)
    }

    // MARK: - 颜色

    static var headingColor: NSColor { .labelColor }
    /// 引用里的正文用**正文字色**，不做颜色弱化。
    ///
    /// 试过两版弱化，都被实测否掉：
    /// ① `secondaryLabelColor`：亮色帧上 3.95:1 —— 引用是正文级散文，14pt 要 4.5:1，
    ///    为了"看起来像引用"把内容画糊是本末倒置；
    /// ② `labelColor.withAlphaComponent(0.8)`：暗色下**整行消失**。探针
    ///    （`testSemanticColorsAreNotBakedByWithAlphaComponent`）给出的解析值是
    ///    `a=0.80 r=0 g=0 b=0` —— `withAlphaComponent` 会把动态色在调用那一刻按当前外观
    ///    烤成固定 RGB，暗色下拿到的是 aqua 的黑。黑字压在深色底上就是看不见。
    /// 所以引用的层级只靠**缩进**表达：它是真线索，而且在两种外观下都不会失效。
    static var quoteColor: NSColor { .labelColor }
    static var bodyColor: NSColor { .labelColor }
    static var linkColor: NSColor { .linkColor }
    /// 装饰性标记（项目符号）。带语义的标记（编号、任务框）走 `markerColor(for:)` 的另一档。
    ///
    /// `secondaryLabelColor` 在亮色帧上是 3.95:1，但项目符号是**装饰**不是内容
    /// （WCAG 1.4.3 管的是文字与有意义的 UI 部件），而它必须还是动态色 —— 见上面那条探针。
    static var markerColor: NSColor { .secondaryLabelColor }
    /// 承载语义的标记：`3.` 是顺序、`☑` 是完成态 —— 它们是内容，不是装饰，
    /// 所以用正文字色，不能比正文更难读。
    static var meaningfulMarkerColor: NSColor { .labelColor }

    /// 纯函数：这个块的标记带不带语义。做成函数是因为这一档判断会随块类型变（任务项 vs 普通项），
    /// 留在颜色常量里就只能靠"看起来差不多"。
    static func markerColor(for block: MarkdownBlock) -> NSColor {
        switch block.kind {
        case .orderedItem: return meaningfulMarkerColor
        case .unorderedItem(_, let task) where task != nil: return meaningfulMarkerColor
        default: return markerColor
        }
    }

    /// 行内码与代码块的底色。刻意不是"框"：属性串画不出圆角框，
    /// 一个浅底色色带是 NSTextView 里唯一诚实的表达（对比度实量记在 `AGENT_UI_AUDIT.md`）。
    static var codeBackground: NSColor { NSColor.quaternaryLabelColor }

    static func foregroundColor(for block: MarkdownBlock) -> NSColor {
        if case .heading = block.kind { return headingColor }
        if case .codeBlock = block.kind { return bodyColor }
        return block.quoteDepth > 0 ? quoteColor : bodyColor
    }

    // MARK: - 缩进

    static let listMarkerAdvance: CGFloat = 16
    static let quoteIndent: CGFloat = 18
    static let maximumListDepth: Int = MarkdownParsingPolicy.maximumListDepth

    /// 引用深度作为**属性**跟着整块走，正文视图按它画左侧导引线（`MarkdownQuoteRule`）。
    /// 不复用段落缩进反推：缩进是 `CGFloat` 的排版结果，列表续行也占着它，
    /// 从字形几何反推"这是引用"会把列表续行认成引用（两类缩进本来就不是一件事）。
    static let quoteDepthAttribute = NSAttributedString.Key("ClipboardHistory.markdownQuoteDepth")

    /// 代码块的行数（只打在块正文上，不含块后的分隔空行）：正文视图按它在左侧槽里画行号。
    static let codeBlockLineCountAttribute = NSAttributedString.Key("ClipboardHistory.markdownCodeLineCount")

    /// 代码块的归一化语言标签（已由 `CodeLanguageTag.label(for:)` 转成短标签）。
    /// 没有语言、或语言不给标签，就不打这个属性 —— 视图层不会自己再猜。
    static let codeLanguageAttribute = NSAttributedString.Key("ClipboardHistory.markdownCodeLanguage")

    static func blockText(_ block: MarkdownBlock) -> String {
        block.runs.map(\.text).joined()
    }

    /// 段落首行缩进：引用层数 × 引用缩进 + 列表深度 × 项目符宽度。
    static func firstLineHeadIndent(for block: MarkdownBlock) -> CGFloat {
        CGFloat(block.quoteDepth) * quoteIndent
            + listDepth(of: block.kind) * listMarkerAdvance
    }

    /// 悬挂缩进的第二行起点：列表项要让续行对齐到正文而不是对齐到圆点下面。
    static func headIndent(for block: MarkdownBlock) -> CGFloat {
        guard isListItem(block.kind) else { return firstLineHeadIndent(for: block) }
        return firstLineHeadIndent(for: block) + listMarkerAdvance
    }

    static func listDepth(of kind: MarkdownBlock.Kind) -> CGFloat {
        switch kind {
        case .unorderedItem(let depth, _), .orderedItem(let depth, _):
            return CGFloat(min(max(depth, 0), maximumListDepth))
        default:
            return 0
        }
    }

    static func isListItem(_ kind: MarkdownBlock.Kind) -> Bool {
        switch kind {
        case .unorderedItem, .orderedItem: return true
        default: return false
        }
    }

    /// 项目符号。深度轮换 `• ◦ ▪`，和 GitHub 的三级嵌套一致；再深就重复最后一个。
    static func bulletGlyph(depth: Int) -> String {
        switch min(max(depth, 0), 2) {
        case 0: return "•"
        case 1: return "◦"
        default: return "▪"
        }
    }

    static func taskGlyph(_ state: MarkdownBlock.TaskState?) -> String? {
        guard let state else { return nil }
        return state == .checked ? "☑" : "☐"
    }

    /// 分隔线用一根横线字符画。属性串里没有"画一条线"这种原语，
    /// 而插入一个 `NSTextAttachment` 会让只读区的复制结果带上附件、
    /// 并给 VoiceOver 多一个没有语义的元素。字符线是唯一"看起来是线、复制出来是空"的选择。
    static let thematicBreakText = String(repeating: "─", count: 24)

    // MARK: - 中文强调：斜体还是字重

    enum EmphasisStyle: Equatable {
        /// 有真斜体的文字（拉丁）走斜体，语义与上游一致。
        case italic
        /// 没有真斜体的文字（中日韩）走**加一档字重**。
        case heavierWeight
    }

    /// 中文的"斜体"在系统里没有真字形，AppKit 会给一个**合成倾斜**（把正体剪切错切）。
    /// 中文排版惯例里强调是加重或加框，合成斜体既糊字又不合习惯；
    /// 所以这里按内容分叉：拉丁用斜体，CJK 用字重。
    /// 这个分叉必须是纯函数，否则"为什么这句是斜的"就只能靠猜。
    static func emphasisStyle(for text: String) -> EmphasisStyle {
        containsCJK(text) ? .heavierWeight : .italic
    }

    static func containsCJK(_ text: String) -> Bool {
        for scalar in text.unicodeScalars {
            let value = scalar.value
            if value >= 0x2E80 && value <= 0x2FFF { return true }      // 部首、CJK 标点
            if value >= 0x3000 && value <= 0x30FF { return true }      // CJK 标点、假名
            if value >= 0x3400 && value <= 0x4DBF { return true }      // 扩展 A
            if value >= 0x4E00 && value <= 0x9FFF { return true }      // 基本汉字
            if value >= 0xAC00 && value <= 0xD7AF { return true }      // 谚文
            if value >= 0xF900 && value <= 0xFAFF { return true }      // 兼容汉字
            if value >= 0xFF00 && value <= 0xFFEF { return true }      // 全角
        }
        return false
    }

    // MARK: - 字形计划（纯函数，可断言）

    /// 一个 run 最终要什么字形，全部在这里算完。
    ///
    /// 之所以要一个中间计划而不是直接造 `NSFont`：`NSFont` 的相等性在测试里几乎没法读
    /// （两个同字号同字体的对象比较会带着眼罩过），而 `FontPlan` 是值类型，
    /// "中文强调不许用合成斜体""行内码要跟着标题的字号"这类决定都能被精确断言。
    struct FontPlan: Equatable, Sendable {
        var size: CGFloat
        var weight: NSFont.Weight
        var isItalic: Bool
        var isMonospaced: Bool
    }

    static func size(for block: MarkdownBlock) -> CGFloat {
        switch block.kind {
        case .heading(let level): return headingFontSize(level: level)
        case .codeBlock, .table: return codeFontSize
        default: return bodyFontSize
        }
    }

    static func blockWeight(for block: MarkdownBlock) -> NSFont.Weight {
        if case .heading(let level) = block.kind { return level <= 2 ? .bold : .semibold }
        return .regular
    }

    /// 表格与代码块是"逐字保留"的宽内容，整块等宽、不再吃行内语法。
    static func isWideContent(_ kind: MarkdownBlock.Kind) -> Bool {
        switch kind {
        case .codeBlock, .table: return true
        default: return false
        }
    }

    static func fontPlan(for run: MarkdownInline, in block: MarkdownBlock) -> FontPlan {
        let blockIsWide = isWideContent(block.kind)
        let monospaced = blockIsWide || run.marks.contains(.code)
        // 行内码在标题里要**保住标题的字号**，否则 `# 用 `code` 起名` 会突然掉一号。
        let size = size(for: block)
        guard !blockIsWide else {
            return FontPlan(size: size, weight: blockWeight(for: block), isItalic: false, isMonospaced: true)
        }
        var weight = blockWeight(for: block)
        var italic = false
        if run.marks.contains(.strong) {
            // 标题本身已经是 bold/semibold，`**` 在里面加不出更粗的档，保持档不变。
            weight = weight.rawValue >= NSFont.Weight.bold.rawValue ? weight : .bold
        }
        if run.marks.contains(.emphasis), !run.marks.contains(.strong) {
            switch emphasisStyle(for: run.text) {
            case .italic:
                italic = true
            case .heavierWeight:
                // 中文已经有粗体档就不再动（六级标题本身就是 semibold，再档会跳成 bold）。
                if weight.rawValue < NSFont.Weight.medium.rawValue { weight = .medium }
            }
        }
        return FontPlan(size: size, weight: weight, isItalic: italic, isMonospaced: monospaced)
    }

    static func font(for plan: FontPlan) -> NSFont {
        let base: NSFont = plan.isMonospaced
            ? .monospacedSystemFont(ofSize: plan.size, weight: plan.weight)
            : .systemFont(ofSize: plan.size, weight: plan.weight)
        guard plan.isItalic else { return base }
        let descriptor = base.fontDescriptor.withSymbolicTraits(.italic)
        return NSFont(descriptor: descriptor, size: plan.size) ?? base
    }

    static func font(for run: MarkdownInline, in block: MarkdownBlock) -> NSFont {
        font(for: fontPlan(for: run, in: block))
    }

    /// 把 run 的样式算成具体属性。
    static func attributes(for run: MarkdownInline, in block: MarkdownBlock) -> [NSAttributedString.Key: Any] {
        var attributes: [NSAttributedString.Key: Any] = [:]
        // **颜色与可点必须同现同缺**：链接色只在真的能点时给。
        // 否则屏幕上会出现"蓝色、下划线、点了没反应"的字 —— 那是假 affordance，
        // 比不给链接更坏。名单与理由在下面的 `linkURL(for:)`。
        let clickable = run.marks.contains(.link) ? linkURL(for: run.destination ?? "") : nil
        attributes[.foregroundColor] = clickable == nil ? foregroundColor(for: block) : linkColor
        attributes[.font] = font(for: run, in: block)

        if run.marks.contains(.strikethrough) {
            attributes[.strikethroughStyle] = NSUnderlineStyle.single.rawValue
        }
        if run.marks.contains(.code) {
            attributes[.backgroundColor] = codeBackground
        }
        if let clickable {
            attributes[.link] = clickable
        }
        return attributes
    }

    /// 链接目标必须是**看起来能用**的 URL，否则宁可不加 `.link` 属性。
    ///
    /// 为什么这条要单独存在：`URL(string:)` 对 `](javascript:alert(1)` 这类字符串照样返回非 nil，
    /// 而 NSTextView 会把它变成可点的东西。预览一个来路不明的剪贴板文件时，
    /// "只有 http/https/mailto 能点"是这条边界的唯一防线（与 `EntryDrag` 里
    /// "Web URL 不给拖成文件"是同一族决定）。
    static func linkURL(for destination: String) -> URL? {
        guard let url = URL(string: destination), let scheme = url.scheme?.lowercased() else { return nil }
        guard ["http", "https", "mailto"].contains(scheme) else { return nil }
        return url
    }

    // MARK: - 构建

    /// 整个模型 → 一个属性串。
    ///
    /// 段落属性用 `NSParagraphStyle` 打在**整块范围**（含块内每一个换行）上，
    /// 这样引用/列表里的软换行和自动折行都跟着同一套缩进走。
    static func attributedString(for document: MarkdownDocument) -> NSAttributedString {
        let result = NSMutableAttributedString()
        for (offset, block) in document.blocks.enumerated() {
            let start = result.length
            append(block, to: result)
            guard result.length > start else { continue }
            let blockContentLength = result.length - start
            let separator = separator(after: block, before: document.blocks.indices.contains(offset + 1)
                ? document.blocks[offset + 1] : nil)
            result.replaceCharacters(in: NSRange(location: result.length, length: 0), with: separator)
            // 段落属性覆盖到分隔符，块内所有行（含空行）才不会漏掉缩进与行距。
            let range = NSRange(location: start, length: result.length - start)
            result.addAttribute(.paragraphStyle, value: paragraphStyle(for: block), range: range)
            // R440：表头（表格块第一行）用等宽 semibold 与表体分开。属性串这一层只换字体，
            // 推进宽度不变，所以列不会挪；范围只到第一行，表体保持 regular。
            if case .table = block.kind {
                let content = (result.string as NSString).substring(with: NSRange(location: start,
                                                                                 length: blockContentLength))
                if let header = TableHeaderPresentation.headerRange(in: content) {
                    result.addAttribute(.font, value: TableHeaderPresentation.headerFont,
                                        range: NSRange(location: start, length: header.length))
                }
            }
            // R441：代码块的行数只打在块正文上（不含分隔空行），正文视图按它在左槽里画行号。
            // R446：语言标签同样只打在这段正文上；没有语言或语言不给标签时**不打**，
            // 视图层按属性有没有值决定画不画，不二次推断围栏。
            if case .codeBlock(let language) = block.kind {
                let content = (result.string as NSString).substring(with: NSRange(location: start,
                                                                                 length: blockContentLength))
                let lineCount = CodeBlockLineNumbers.lineCount(in: content)
                if lineCount > 0 {
                    result.addAttribute(codeBlockLineCountAttribute, value: lineCount,
                                        range: NSRange(location: start, length: blockContentLength))
                }
                if let tag = CodeLanguageTag.label(for: language) {
                    result.addAttribute(codeLanguageAttribute, value: tag,
                                        range: NSRange(location: start, length: blockContentLength))
                }
            }
            // 导引线属性与段落缩进覆盖同一个范围（含块后的分隔空行）：
            // 相邻两个同级引用块因此天然连成一条线，空白行不会把线切断。
            if block.quoteDepth > 0 {
                result.addAttribute(quoteDepthAttribute, value: block.quoteDepth, range: range)
            }
            // R441：宽底不再由属性串背。`.backgroundColor` 是按字形段画的，代码块的最后一行
            // 没有换行符时底色只到最后一个字（帧上是锯齿灰带）；改由正文视图按行片段画**通栏**，
            // 见 `ChineseSelectableNSTextView.drawCodeBlockBackgrounds`。谓词
            // `appliesWideContentBackground` 仍是"这一块要不要宽底"的唯一策略。
        }
        if document.isTruncated {
            let start = result.length
            result.append(NSAttributedString(string: MarkdownParsingPolicy.truncationNote,
                                             attributes: [.font: bodyFont,
                                                          .foregroundColor: NSColor.secondaryLabelColor]))
            result.addAttribute(.paragraphStyle, value: paragraphStyle(for: MarkdownBlock(kind: .paragraph, runs: [])),
                                range: NSRange(location: start, length: result.length - start))
        }
        return result
    }

    // MARK: - 块的节奏（块间距与分隔）

    /// 两个相邻块之间插什么。
    ///
    /// 第一版用 `paragraphSpacing` 撑块间距，帧上是错的：TextKit 把段落间距算进**上一行的行片段矩形**，
    /// 于是宽内容块的那条灰底会连间距一起涂出来，代码块和紧挨着的表格粘成一块灰斑。
    /// 改成"块之间真的空一行"之后，空行是一个独立段落，灰底天然停在内容末尾 ——
    /// 而且这本来就是 Markdown 源文件的写法（作者自己就在块之间敲空行）。
    /// 列表项之间不空行：它们是同一组，空行会把一个列表排成一堆散句。
    static func separator(after current: MarkdownBlock, before next: MarkdownBlock?) -> String {
        guard let next else { return "\n" }
        if isListItem(current.kind), isListItem(next.kind) { return "\n" }
        return "\n\n"
    }

    /// 块**前**的额外留白。空行已经给了基础间距，这里只加"标题需要更多空气"那一档。
    static func paragraphSpacingBefore(for block: MarkdownBlock) -> CGFloat {
        switch block.kind {
        case .heading(let level): return level <= 2 ? 10 : 6
        case .codeBlock, .table: return 4
        case .thematicBreak: return 6
        default: return 0
        }
    }

    static func lineSpacing(for block: MarkdownBlock) -> CGFloat {
        // 标题行内不要额外撑：字阶本身已经把层级表达完了。
        if case .heading = block.kind { return 1 }
        return 2
    }

    static func paragraphStyle(for block: MarkdownBlock) -> NSParagraphStyle {
        let style = NSMutableParagraphStyle()
        style.firstLineHeadIndent = firstLineHeadIndent(for: block)
        style.headIndent = headIndent(for: block)
        style.lineSpacing = lineSpacing(for: block)
        style.paragraphSpacingBefore = paragraphSpacingBefore(for: block)
        // 正文左对齐：详情区是读东西的地方，不是排海报的地方。
        style.alignment = .left
        return style
    }

    private static func append(_ block: MarkdownBlock, to result: NSMutableAttributedString) {
        switch block.kind {
        case .thematicBreak:
            result.append(NSAttributedString(string: thematicBreakText,
                                             attributes: [.font: bodyFont, .foregroundColor: markerColor]))
        case .unorderedItem(let depth, let task):
            let glyph = taskGlyph(task) ?? bulletGlyph(depth: depth)
            appendMarker(glyph + "\t", to: result, block: block)
            appendRuns(block.runs, to: result, block: block)
        case .orderedItem(_, let number):
            // 编号是内容：`3. 第三步` 只排成"第三步"等于把顺序弄丢了。
            appendMarker("\(number).\t", to: result, block: block)
            appendRuns(block.runs, to: result, block: block)
        case .table, .codeBlock:
            // 代码块与表格已经在解析层逐字保留，这里只换字体；
            // 表格的列对齐靠等宽字体保住，重排会让它看起来像被人改过。
            appendRuns(block.runs, to: result, block: block)
        case .heading, .paragraph:
            appendRuns(block.runs, to: result, block: block)
        }
    }

    private static func appendMarker(_ text: String, to result: NSMutableAttributedString,
                                     block: MarkdownBlock) {
        result.append(NSAttributedString(string: text,
                                         attributes: [.font: markerFont(for: block),
                                                      .foregroundColor: markerColor(for: block)]))
    }

    /// 项目符/编号的字号跟所属块一致（标题里的编号不该突然缩小）。
    private static func markerFont(for block: MarkdownBlock) -> NSFont {
        font(for: FontPlan(size: size(for: block), weight: blockWeight(for: block),
                           isItalic: false, isMonospaced: false))
    }

    private static func appendRuns(_ runs: [MarkdownInline], to result: NSMutableAttributedString,
                                   block: MarkdownBlock) {
        for run in runs {
            result.append(NSAttributedString(string: run.text, attributes: attributes(for: run, in: block)))
        }
    }

    /// 宽内容整块铺一层底色。
    ///
    /// 第一版没铺，帧上的结果是"代码块看起来就是一行普通字"—— 等宽字体不足以把它和上下文分开，
    /// 而它恰恰是最需要"这块是原样、那块是正文"的地方。属性串画不出圆角框，
    /// 一条通栏色带是 NSTextView 里唯一诚实的表达。
    static func appliesWideContentBackground(to block: MarkdownBlock) -> Bool {
        // 代码块吃灰底，**表格不吃**。R234 看图时量到的病：渲染模式里表格与代码块在画面上
        // 完全同形（同 13pt 等宽、同 `quaternaryLabel` 灰底、同 4pt 段前距），而那块灰底在 macOS
        // 上一律读成"这是源码"——于是"渲染"这一档把一张数据表说成了代码，比 原文 更误导。
        // 表格的分组靠等宽对齐与竖线本身；列重排仍然是刻意不做的那一件（见账 D 里那条）。
        if case .table = block.kind { return false }
        return isWideContent(block.kind)
    }
}
