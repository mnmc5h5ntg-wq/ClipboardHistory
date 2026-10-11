import Foundation

/// Markdown 的**判定与解析**层：源码 → 值模型，全程纯函数、不碰 AppKit。
///
/// 分成"值模型 + 呈现"两层的原因不是整洁，是两件具体的事：
/// 1. **解析要能离主线程跑**。详情区每次换选都会重算正文，把一个几百 KB 的 README
///    的解析留在主线程就是掉帧。而 `NSAttributedString` 不是 `Sendable`，
///    一旦"解析出什么"直接做成属性串就必须绑在主线程。所以这里产出 `Sendable` 的值模型，
///    `MarkdownPresentation` 才在主线程把它变成属性串。
/// 2. **解析要能被真值表钉住**（`AGENTS.md` 定义完成标准第 2 条：新逻辑先落纯函数）。
///    "这行是不是标题""`**` 包到哪结束"留在视图里就只能靠眼睛验收。
///
/// 支持的是**一个明确的子集**，不是 CommonMark 认证实现。刻意不支持的（上游会渲染、
/// 这里原样显示成文字）：引用式链接 `[a][ref]`、图片、脚注、HTML 块、裸 URL 自动链接、
/// 松散/紧凑列表语义、表格列重排。这些一律走"原样保留"而不是"吞掉" ——
/// 渲染器最坏的错不是画得不好看，而是**把用户的内容弄丢了**。
enum MarkdownParsingPolicy {
    /// 按扩展名判定"这就是 Markdown 文档"。刻意只有这两个：
    /// `mdown`/`mdtxt`/`textbundle` 在真实文件里几乎遇不到，而把别名扩到 `mdx`
    /// （JSX，语法完全不同）就会把代码当文档渲染。
    static let fileExtensions: Set<String> = ["md", "markdown"]

    /// 要渲染的字符上限。`MediaLoader` 已经只读前 256KB 文本，这里再收一刀的原因是
    /// 属性串的构建成本按 run 数走，而日志类文件的"行"可以有几万条。
    /// 超出的部分不静默丢弃：尾部追加 `truncationNote`，而原文模式永远给完整的那份。
    static let maximumRenderedCharacters = 40_000

    static let truncationNote = "……（后面的内容没有渲染，切到「原文」看全文）"

    /// 块级嵌套上限（引用里再套引用）。超过就不再把 `>` 当标记，整行按字面量显示。
    static let maximumQuoteDepth = 6
    /// 行内嵌套上限（`**粗 _加斜体_ **`）。超过保留标记字符本身。
    static let maximumInlineNestingDepth = 4
    /// 列表缩进层级上限，防御畸形输入把悬挂缩进推出容器宽度。
    static let maximumListDepth = 6
    /// 标题层级。第 7 个 `#` 开始就不算标题了（CommonMark 同），整行按字面量留着。
    static let maximumHeadingLevel = 6

    /// 一个行内标记**最远**在哪里允许出现闭栏（字符数）。
    ///
    /// 这不是"排版口味"而是**复杂度上限**：找闭栏是前向扫描，每遇到一个未闭合的
    /// `*` / `` ` `` / `[` 都要扫到行尾。没有上界时，`* a * a * a …` 这种输入会让
    /// 整段解析退化成 O(n²) —— 40000 个字符就是几十亿次比较，主线程直接冻住。
    /// 加上界之后最坏情况是 O(n × 上界)，而且语义上也说得通：
    /// 强调、行内码、链接都不会跨过几百个字符（真正的长链接交给 `<…>` 自动链接）。
    /// 超出上界就当字面量，内容一个字不少。
    static let maximumInlineMarkupDistance = 240

    static func isMarkdownFile(_ url: URL) -> Bool {
        fileExtensions.contains(url.pathExtension.lowercased())
    }

    /// 一段文本里出现的 Markdown 语法信号。
    ///
    /// 为什么要这个而不是"看起来像不像"：文本条目（从 README 里复制的一段、
    /// 从聊天工具里粘的一段）没有扩展名可依，判定只能靠内容。而**误判的代价不对称** ——
    /// 把 Python 源码的 `# 注释` 当标题渲染，比"没给渲染入口"糟得多。
    /// 所以这里只列信号、不做决定，决定在 `offersRendering`。
    enum Signal: String, CaseIterable, Sendable {
        case heading
        case fencedCode
        case unorderedList
        case orderedList
        case blockquote
        case thematicBreak
        case link
        case codeSpan
        case emphasis
        case tableRule
    }

    static func signals(in text: String) -> Set<Signal> {
        guard !text.isEmpty else { return [] }
        var found: Set<Signal> = []
        let lines = text.components(separatedBy: .newlines)
        for line in lines {
            let body = MarkdownScanner.body(of: line)
            if body.isEmpty { continue }
            if MarkdownScanner.isATXHeading(body) { found.insert(.heading) }
            if MarkdownScanner.isFence(body) { found.insert(.fencedCode) }
            if MarkdownScanner.isBlockquote(body) { found.insert(.blockquote) }
            if MarkdownScanner.isThematicBreak(body) { found.insert(.thematicBreak) }
            if MarkdownScanner.unorderedMarker(of: body) != nil { found.insert(.unorderedList) }
            if MarkdownScanner.orderedMarker(of: body) != nil { found.insert(.orderedList) }
            if MarkdownScanner.isTableRule(body) { found.insert(.tableRule) }
            if MarkdownScanner.containsLinkSyntax(body) { found.insert(.link) }
            if MarkdownScanner.containsCodeSpan(body) { found.insert(.codeSpan) }
            if MarkdownScanner.containsEmphasisSyntax(body) { found.insert(.emphasis) }
        }
        return found
    }

    /// 至少这么多个**不同类型**的信号才给渲染入口。
    /// 取 2 的理由：单个信号在纯文本里太常见（`- ` 开头的行、一处反引号、
    /// 一条 `---` 分隔线都可能出现在日志、代码、配置里）；两类不同语法同时出现，
    /// 才说明"作者真的在写 Markdown"。
    static let minimumSignalsToOfferRendering = 2

    /// 文本条目是否值得给「渲染 / 原文」这个开关，并且值不值得默认就渲染。
    ///
    /// 默认给渲染结果，三个理由撑得住：
    /// ① 判定要求**两类不同语法同时出现**，误判面已经收得很窄；
    /// ② 渲染只改**看法**：`copyAndPromote` 写回剪贴板的仍是用户原来那几个字节，
    ///    存档、搜索、行预览、去重全都不经过这一层（`Round4MarkdownTests` 里钉着这条）；
    /// ③ 那颗「原文」控件就在正文上方同一行，一步退回去。
    /// 真正没有退路的做法是"渲染错了也没法看原文"，所以那条控件是这套功能的前提，不是装饰。
    static func offersRendering(forText text: String) -> Bool {
        signals(in: text).count >= minimumSignalsToOfferRendering
    }
}

/// 预览里 Markdown 的两种显示形态。
/// 它是**视图态**不是数据：不写盘、不进存档、不参与搜索与去重，
/// 换一条记录带着它走没问题，但绝不改 `HistoryStore` 里的任何一个字。
enum MarkdownPreviewMode: Equatable, Sendable {
    case rendered
    case source

    /// 头部那颗控件的标题：控件说的是"点下去会变成什么"，不是"现在是什么"。
    static func controlTitle(for mode: MarkdownPreviewMode) -> String {
        mode == .rendered ? "原文" : "渲染"
    }

    static let controlHelp = "在渲染结果与 Markdown 原文之间切换"

    /// 按一下之后的状态。单独成函数是因为这颗控件的**点击不可自动化**
    /// （在屏探针里 AX 树是空的、几何无法归因，见 `UIInteractionProbeTests` 那段注释），
    /// 于是"翻转方向没写反"这件事只能靠纯函数钉住。
    func toggled() -> MarkdownPreviewMode {
        self == .rendered ? .source : .rendered
    }
}

/// 行内样式标记。用 `OptionSet` 而不是枚举：`**重点 _加斜体_**` 是**叠加**，
/// 一个 run 同时是粗体和斜体是常态，用枚举就得为每种组合造一个 case。
struct MarkdownInline: Equatable, Sendable {
    struct Mark: OptionSet, Equatable, Sendable {
        let rawValue: Int

        static let plain: Mark = []
        static let emphasis = Mark(rawValue: 1 << 0)
        static let strong = Mark(rawValue: 1 << 1)
        static let code = Mark(rawValue: 1 << 2)
        static let strikethrough = Mark(rawValue: 1 << 3)
        static let link = Mark(rawValue: 1 << 4)
    }

    var marks: Mark = .plain
    var text: String
    /// 只有 `.link` 有值：链接目标。刻意不并进 `text` ——
    /// 渲染链接时 GitHub 不显示地址，我们跟随这个语义；
    /// 代价是"丢了可见文字"这条不变量要在测试里显式承认这个例外，而不是藏进断言。
    var destination: String?

    init(marks: Mark = .plain, text: String, destination: String? = nil) {
        self.marks = marks
        self.text = text
        self.destination = destination
    }
}

/// 块级结构。
struct MarkdownBlock: Equatable, Sendable {
    enum Kind: Equatable, Sendable {
        case heading(level: Int)
        case paragraph
        case codeBlock(language: String?)
        case unorderedItem(depth: Int, task: TaskState?)
        case orderedItem(depth: Int, number: Int)
        case thematicBreak
        /// 管道表格：**原样等宽**呈现，不重排列宽。
        /// 理由是重排成网格需要列宽测量与横向布局，在一个只读属性串里做不到干净；
        /// 退而求其次"用等宽字体把作者自己敲的对齐保住"是诚实的，
        /// 用正文字体把每列压成随机宽度才是骗人。
        case table
    }

    enum TaskState: Equatable, Sendable {
        case unchecked
        case checked
    }

    var kind: Kind
    var runs: [MarkdownInline]
    /// 引用层数（0 表示不在引用里）。
    ///
    /// 刻意做成**属性**而不是 `.quote(depth:)` 这种块类型：引用里的标题仍然是标题。
    /// 早先按块类型建模时，`> ## 标题` 会退化成普通段落文字 —— 那是"渲染把结构弄没了"，
    /// 而结构正是 Markdown 的全部意义。
    var quoteDepth: Int = 0

    init(kind: Kind, runs: [MarkdownInline], quoteDepth: Int = 0) {
        self.kind = kind
        self.runs = runs
        self.quoteDepth = quoteDepth
    }

    /// 逐字保留的块（代码块、表格）用它建 run。
    ///
    /// 空内容必须产出**空数组**而不是一个 `text: ""` 的 run：后者在呈现层是一个零宽的属性段，
    /// 在帧上什么都看不见、在代码里却会骗过"每块都有正文"这类断言。
    /// （这条是被测试抓出来的，不是想出来的。）
    static func literalRuns(_ text: String) -> [MarkdownInline] {
        text.isEmpty ? [] : [MarkdownInline(text: text)]
    }
}

struct MarkdownDocument: Equatable, Sendable {
    var blocks: [MarkdownBlock] = []
    var isTruncated = false

    /// 渲染结果里的全部可见文字（"内容没被弄丢"那条不变量用它来比对）。
    ///
    /// 有序列表的**编号是内容不是装饰**，所以它跟着进这里：
    /// `3. 第三步` 渲染成"第三步"是不可接受的 —— 读者会以为顺序被改了。
    /// 项目符号（`•`）与勾选符号相反，它们是装饰，由呈现层加，不在这里计。
    var visibleText: String {
        blocks.map { block in
            switch block.kind {
            case .thematicBreak:
                return ""
            case .orderedItem(_, let number):
                return "\(number). " + block.runs.map(\.text).joined()
            default:
                return block.runs.map(\.text).joined()
            }
        }.joined(separator: "\n")
    }

    var isEmpty: Bool {
        blocks.allSatisfy { block in
            if case .thematicBreak = block.kind { return true }
            return block.runs.isEmpty || block.runs.allSatisfy { $0.text.isEmpty }
        }
    }
}

/// 源码 → 值模型。
enum MarkdownParser {
    static func parse(_ source: String) -> MarkdownDocument {
        var document = MarkdownDocument()
        var text = source
        if text.count > MarkdownParsingPolicy.maximumRenderedCharacters {
            text = String(text.prefix(MarkdownParsingPolicy.maximumRenderedCharacters))
            document.isTruncated = true
        }
        document.blocks = blocks(in: text, depth: 0)
        return document
    }

    /// 一层块扫描。引用块靠递归调用自己来嵌套（`depth` 递增、有上限）。
    private static func blocks(in text: String, depth: Int) -> [MarkdownBlock] {
        let lines = text.components(separatedBy: .newlines)
        var result: [MarkdownBlock] = []
        var paragraph: [String] = []
        var index = 0

        // 段落里**逐行保留换行**。CommonMark 会把软换行折叠成空格，这里刻意不折叠：
        // ① 中文笔记普遍"一句一行"，折叠后一大段挤在一起，比原文更难读；
        // ② 折叠会删掉源文件的字符，而"不丢可见文字"是这层的硬不变量。
        // 代价（英文硬换行的段落看起来参差）记在 AGENT_DECISIONS.md。
        func flushParagraph() {
            guard !paragraph.isEmpty else { return }
            let joined = paragraph.joined(separator: "\n")
            paragraph.removeAll()
            result.append(MarkdownBlock(kind: .paragraph,
                                        runs: MarkdownInlineParser.runs(in: joined),
                                        quoteDepth: depth))
        }

        /// setext 下划线（`标题` 下面一行 `===` / `---`）把已攒的段落升级成标题。
        /// CommonMark 就是这个优先级：段落紧接 `---` 是二级标题而不是分隔线。
        /// 不实现的后果是"标题变成一条横线加一行普通字"—— 那是降级，不是差异。
        func flushParagraphAsHeading(level: Int) {
            let joined = paragraph.joined(separator: " ")
            paragraph.removeAll()
            result.append(MarkdownBlock(kind: .heading(level: level),
                                        runs: MarkdownInlineParser.runs(in: joined),
                                        quoteDepth: depth))
        }

        while index < lines.count {
            let line = lines[index]
            let body = MarkdownScanner.body(of: line)

            if body.isEmpty {
                flushParagraph()
                index += 1
                continue
            }

            // setext 先于分隔线判定（见上面的注释）。
            if !paragraph.isEmpty, MarkdownScanner.isSetextUnderline(body) {
                flushParagraphAsHeading(level: MarkdownScanner.setextLevel(of: body))
                index += 1
                continue
            }

            if MarkdownScanner.isFence(body) {
                flushParagraph()
                let (block, nextIndex) = codeBlock(lines: lines, openingIndex: index,
                                                   marker: MarkdownScanner.fenceCharacter(of: body),
                                                   quoteDepth: depth)
                result.append(block)
                index = nextIndex
                continue
            }

            if MarkdownScanner.isThematicBreak(body) {
                flushParagraph()
                result.append(MarkdownBlock(kind: .thematicBreak, runs: [], quoteDepth: depth))
                index += 1
                continue
            }

            if MarkdownScanner.isBlockquote(body) {
                flushParagraph()
                let (collected, nextIndex) = MarkdownScanner.collectConsecutive(
                    lines: lines, from: index,
                    where: { MarkdownScanner.isBlockquote(MarkdownScanner.body(of: $0)) }
                )
                if depth >= MarkdownParsingPolicy.maximumQuoteDepth {
                    // 嵌套太深：不再剥标记，整段按字面量留着，用户至少看得到原文。
                    result.append(MarkdownBlock(kind: .paragraph,
                                                runs: MarkdownInlineParser.runs(in: collected.joined(separator: "\n")),
                                                quoteDepth: depth))
                } else {
                    let inner = collected.map { MarkdownScanner.blockquoteContent(of: $0) }
                    result.append(contentsOf: blocks(in: inner.joined(separator: "\n"), depth: depth + 1))
                }
                index = nextIndex
                continue
            }

            if MarkdownScanner.isATXHeading(body) {
                flushParagraph()
                let level = min(MarkdownScanner.headingLevel(of: body) ?? 1,
                                MarkdownParsingPolicy.maximumHeadingLevel)
                result.append(MarkdownBlock(kind: .heading(level: level),
                                            runs: MarkdownInlineParser.runs(in: MarkdownScanner.headingText(of: body)),
                                            quoteDepth: depth))
                index += 1
                continue
            }

            if index + 1 < lines.count,
               MarkdownScanner.containsPipe(body),
               MarkdownScanner.isTableRule(MarkdownScanner.body(of: lines[index + 1])) {
                flushParagraph()
                let (block, nextIndex) = MarkdownScanner.collectTable(lines: lines, from: index)
                result.append(MarkdownBlock(kind: block.kind, runs: block.runs, quoteDepth: depth))
                index = nextIndex
                continue
            }

            if let marker = MarkdownScanner.listMarker(of: body, indent: MarkdownScanner.indent(of: line)) {
                flushParagraph()
                let (block, nextIndex) = listItem(lines: lines, from: index, marker: marker,
                                                  quoteDepth: depth)
                result.append(block)
                index = nextIndex
                continue
            }

            // 缩进代码不能打断段落（CommonMark 同）：段落后面缩进的行是续行，不是代码。
            if paragraph.isEmpty, MarkdownScanner.isIndentedCode(line) {
                let (collected, nextIndex) = MarkdownScanner.collectConsecutive(
                    lines: lines, from: index,
                    where: { MarkdownScanner.isIndentedCode($0) }
                )
                let content = collected.map { MarkdownScanner.dedentIndented($0) }.joined(separator: "\n")
                result.append(MarkdownBlock(kind: .codeBlock(language: nil),
                                            runs: MarkdownBlock.literalRuns(content),
                                            quoteDepth: depth))
                index = nextIndex
                continue
            }

            paragraph.append(body)
            index += 1
        }
        flushParagraph()
        return result
    }

    /// 围栏代码块：从 `openingIndex` 那行吃到同字符、长度不小于开栏的闭栏。
    /// 没有闭栏就吃到结尾（CommonMark 同样如此，README 被截断时这是常见形态）。
    private static func codeBlock(lines: [String], openingIndex: Int, marker: Character,
                                  quoteDepth: Int) -> (MarkdownBlock, nextIndex: Int) {
        let openingBody = MarkdownScanner.body(of: lines[openingIndex])
        let language = MarkdownScanner.fenceLanguage(of: openingBody)
        let openingLength = MarkdownScanner.fenceLength(of: openingBody) ?? 3
        // 内容按开栏的缩进相对去缩，而不是逐行 trim：代码的层次感就在那些空格里。
        let baseIndent = MarkdownScanner.indent(of: lines[openingIndex])
        var index = openingIndex + 1
        var content: [String] = []
        while index < lines.count {
            let body = MarkdownScanner.body(of: lines[index])
            if MarkdownScanner.isFenceClose(body, marker: marker, minLength: openingLength) {
                index += 1
                break
            }
            content.append(MarkdownScanner.dedent(lines[index], by: baseIndent))
            index += 1
        }
        let text = content.joined(separator: "\n")
        return (MarkdownBlock(kind: .codeBlock(language: language),
                              runs: MarkdownBlock.literalRuns(text),
                              quoteDepth: quoteDepth), index)
    }

    /// 列表项：一行一项，后面**缩进更深且不另起语法**的行并进来
    /// （多行 item 是真文档里的常态，拆成独立段落会把悬挂缩进丢掉）。
    private static func listItem(lines: [String], from index: Int,
                                 marker: MarkdownScanner.ListMarker,
                                 quoteDepth: Int) -> (MarkdownBlock, nextIndex: Int) {
        var content = marker.content
        var next = index + 1
        while next < lines.count {
            let line = lines[next]
            let body = MarkdownScanner.body(of: line)
            if body.isEmpty { break }
            if MarkdownScanner.indent(of: line) <= marker.indent { break }
            // 续行不能自己就是块起始语法，否则那是下一项或一个新块。
            if MarkdownScanner.isATXHeading(body) || MarkdownScanner.isFence(body)
                || MarkdownScanner.isBlockquote(body) || MarkdownScanner.isThematicBreak(body)
                || MarkdownScanner.listMarker(of: body, indent: MarkdownScanner.indent(of: line)) != nil { break }
            content += "\n" + body
            next += 1
        }
        let runs = MarkdownInlineParser.runs(in: content)
        let depth = min(marker.indent / 2, MarkdownParsingPolicy.maximumListDepth)
        let kind: MarkdownBlock.Kind
        if let number = marker.number {
            kind = .orderedItem(depth: depth, number: number)
        } else {
            kind = .unorderedItem(depth: depth, task: marker.task)
        }
        return (MarkdownBlock(kind: kind, runs: runs, quoteDepth: quoteDepth), next)
    }
}

/// 行内解析：`**粗**`、`*斜*`、`` `码` ``、`~~删~~`、`[标签](地址)`、`<https://…>`、`\` 转义。
///
/// 规矩只有一条：**分不出来就当字面量**。未闭合的 `**`、多余的 `~`、`[没有括号`
/// 全部原样留下，宁可多显示两个星号，也不许把用户的字吃掉。
enum MarkdownInlineParser {
    static func runs(in text: String) -> [MarkdownInline] {
        runs(in: text, depth: 0)
    }

    private static func runs(in text: String, depth: Int) -> [MarkdownInline] {
        guard !text.isEmpty else { return [] }
        if depth >= MarkdownParsingPolicy.maximumInlineNestingDepth {
            return [MarkdownInline(text: text)]
        }
        let characters = Array(text)
        var result: [MarkdownInline] = []
        var literal = ""
        var index = 0

        func flushLiteral() {
            guard !literal.isEmpty else { return }
            result.append(MarkdownInline(text: literal))
            literal = ""
        }

        /// 把内层 run 套上外层样式。行内码例外：CommonMark 规定码串内部不再解析语法，
        /// 所以 `` `**x**` `` 显示的就是 `**x**`。
        func wrap(_ inner: [MarkdownInline], _ mark: MarkdownInline.Mark,
                  destination: String? = nil) -> [MarkdownInline] {
            inner.map { run in
                guard !run.marks.contains(.code) else { return run }
                var wrapped = run
                wrapped.marks.insert(mark)
                if let destination { wrapped.destination = destination }
                return wrapped
            }
        }

        while index < characters.count {
            let character = characters[index]

            // 反斜杠转义：`\*` 是星号不是强调。
            if character == "\\", index + 1 < characters.count {
                let next = characters[index + 1]
                if next.isSymbol || next.isPunctuation || next == " " {
                    literal.append(next)
                    index += 2
                    continue
                }
                literal.append(character)
                index += 1
                continue
            }

            if character == "`" {
                let runLength = MarkdownScanner.repeatedRunLength(characters, from: index, character: "`")
                if let closed = MarkdownScanner.findClosingBacktick(in: characters, from: index, length: runLength) {
                    let inner = String(characters[(index + runLength)..<(closed - runLength)])
                    flushLiteral()
                    result.append(MarkdownInline(marks: .code,
                                                 text: MarkdownScanner.trimOneSpaceEachSide(inner)))
                    index = closed
                    continue
                }
                literal.append(character)
                index += 1
                continue
            }

            if character == "~",
               MarkdownScanner.repeatedRunLength(characters, from: index, character: "~") == 2,
               let closed = MarkdownScanner.findDuplicate(in: characters, from: index, character: "~") {
                let inner = String(characters[(index + 2)..<(closed - 2)])
                if !inner.isEmpty {
                    flushLiteral()
                    result.append(contentsOf: wrap(runs(in: inner, depth: depth + 1), .strikethrough))
                    index = closed
                    continue
                }
            }

            if character == "*" || character == "_" {
                let runLength = MarkdownScanner.repeatedRunLength(characters, from: index, character: character)
                if let match = MarkdownScanner.findEmphasisClose(in: characters, from: index,
                                                                character: character, runLength: runLength) {
                    let inner = String(characters[(index + runLength)..<(match.contentEnd)])
                    if !inner.isEmpty {
                        flushLiteral()
                        var wrapped = runs(in: inner, depth: depth + 1)
                        if match.isStrong { wrapped = wrap(wrapped, .strong) }
                        if match.carriesEmphasis { wrapped = wrap(wrapped, .emphasis) }
                        result.append(contentsOf: wrapped)
                        index = match.afterClose
                        continue
                    }
                }
                literal.append(String(characters[index..<index + runLength]))
                index += runLength
                continue
            }

            if character == "[", let link = MarkdownScanner.linkAt(characters, from: index) {
                flushLiteral()
                result.append(contentsOf: wrap(runs(in: link.label, depth: depth + 1), .link,
                                               destination: link.destination))
                index = link.afterDestination
                continue
            }

            if character == "<", let autolink = MarkdownScanner.autolinkAt(characters, from: index) {
                flushLiteral()
                result.append(MarkdownInline(marks: .link, text: autolink.url, destination: autolink.url))
                index = autolink.afterClose
                continue
            }

            literal.append(character)
            index += 1
        }
        flushLiteral()
        return result
    }
}
