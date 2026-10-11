// 不覆盖管线：本文件只钉 Markdown **解析**的纯函数真值表（源码 → 值模型）。
// 真实渲染（值模型 → NSAttributedString → 详情区的只读文本视图）、以及"选中一个 .md 文件
// 到底看到了渲染结果"这条产品路径，在 `Round4MarkdownTests`（含 MediaLoader → FilePreview
// → 视图的入口用例）与 `UICaptureHarness` 的 `detail-markdown` 帧里。
// （`AGENTS.md` 定义完成标准第 1 条：只测纯函数的文件要自己写明边界。）
import Foundation
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class MarkdownParsingTests: XCTestCase {

    // MARK: - 夹具辅助

    private func blocks(_ source: String) -> [MarkdownBlock] {
        MarkdownParser.parse(source).blocks
    }

    private func visible(_ source: String) -> String {
        MarkdownParser.parse(source).visibleText
    }

    private func runs(_ source: String) -> [MarkdownInline] {
        blocks(source).first?.runs ?? []
    }

    /// 连续字母或数字算一个"词"，其余字符是分隔。用于不变量比对。
    private func words(of text: String) -> [String] {
        var result: [String] = []
        var current = ""
        for character in text {
            if String(character).rangeOfCharacter(from: .alphanumerics) != nil {
                current.append(character)
            } else if !current.isEmpty {
                result.append(current)
                current = ""
            }
        }
        if !current.isEmpty { result.append(current) }
        return result
    }

    /// 核心不变量：**源文件里的每一个词都必须按顺序出现在渲染结果里**。
    /// 渲染器最坏的错不是难看，是把用户的字弄丢 —— 这条比任何样式断言都重要，
    /// 所以它单独存在，并且对一批"故意恶心"的输入跑。
    private func assertNothingIsLost(_ source: String, _ rendered: String,
                                     _ context: String,
                                     file: StaticString = #filePath, line: UInt = #line) {
        var haystack = Substring(rendered)
        for word in words(of: source) {
            guard let found = haystack.range(of: word) else {
                XCTFail("\(context)：源文本里的「\(word)」在渲染结果里找不到了。渲染结果：\(rendered)",
                        file: file, line: line)
                return
            }
            haystack = haystack[found.upperBound...]
        }
    }

    // MARK: - 判定：什么算 Markdown

    func testOnlyMarkdownExtensionsAreRecognisedAsDocuments() {
        XCTAssertTrue(MarkdownParsingPolicy.isMarkdownFile(URL(fileURLWithPath: "/tmp/说明.md")))
        XCTAssertTrue(MarkdownParsingPolicy.isMarkdownFile(URL(fileURLWithPath: "/tmp/README.MarkDown")))
        // mdx 是 JSX（语法完全不同），当文档渲染会把代码排成散文。
        XCTAssertFalse(MarkdownParsingPolicy.isMarkdownFile(URL(fileURLWithPath: "/tmp/note.mdx")))
        XCTAssertFalse(MarkdownParsingPolicy.isMarkdownFile(URL(fileURLWithPath: "/tmp/note.txt")))
        XCTAssertFalse(MarkdownParsingPolicy.isMarkdownFile(URL(fileURLWithPath: "/tmp/noextension")))
    }

    func testSingleSyntaxSignalIsNotEnoughToOfferRendering() {
        // Python/Shell 的 `# 注释` 在 Markdown 里就是标题。只有一类信号时不给渲染入口 ——
        // 这是"误判代价不对称"的直接后果：把代码排成大标题比不给按钮糟得多。
        let commentsOnly = "# 读取配置\n# 这里没有别的语法\n"
        XCTAssertEqual(MarkdownParsingPolicy.signals(in: commentsOnly), [.heading])
        XCTAssertFalse(MarkdownParsingPolicy.offersRendering(forText: commentsOnly))

        let bullets = "- 一条\n- 两条\n"
        XCTAssertEqual(MarkdownParsingPolicy.signals(in: bullets), [.unorderedList])
        XCTAssertFalse(MarkdownParsingPolicy.offersRendering(forText: bullets))
    }

    func testTwoDifferentSignalsOfferRendering() {
        let readmeish = "# 标题\n\n- 项目\n- 另一项\n"
        XCTAssertTrue(MarkdownParsingPolicy.signals(in: readmeish).isSuperset(of: [.heading, .unorderedList]))
        XCTAssertTrue(MarkdownParsingPolicy.offersRendering(forText: readmeish))
        XCTAssertTrue(MarkdownParsingPolicy.offersRendering(forText: "看 `代码` 和 [链接](https://example.com)"))
        XCTAssertFalse(MarkdownParsingPolicy.offersRendering(forText: "今天天气不错，就是普通一句话。"))
        XCTAssertFalse(MarkdownParsingPolicy.offersRendering(forText: ""))
    }

    func testASingleStrayBacktickIsNotACodeSpanSignal() {
        // 孤立反引号在日志与命令行里到处都是。把它算成"行内码"这一类，
        // 就会和 `# 注释` 那类凑够两类，把一段普通文本排成带标题的文档。
        let stray = "# 读取配置\n把 ` 这个字符当成占位符\n"
        XCTAssertEqual(MarkdownParsingPolicy.signals(in: stray), [.heading])
        XCTAssertFalse(MarkdownParsingPolicy.offersRendering(forText: stray))
        // 成对才算（与解析器要求闭栏是同一条定义）。
        XCTAssertTrue(MarkdownParsingPolicy.signals(in: "`占位符`").isSuperset(of: [.codeSpan]))
    }

    func testControlTitleSaysWhatItWillBecomeNotWhatItIs() {
        XCTAssertEqual(MarkdownPreviewMode.controlTitle(for: .rendered), "原文")
        XCTAssertEqual(MarkdownPreviewMode.controlTitle(for: .source), "渲染")
    }

    func testTogglingRoundTripsAndTitleFollows() {
        // 标题与动作必须配套：如果 `toggled()` 写反了，标题说"看原文"、实际却切到另一个方向，
        // 用户只会觉得这按钮坏了。这条是那颗**按不动的**控件唯一的自动化防线
        // （在屏探针里它的 AX 树是空的，见 UIInteractionProbeTests 的说明）。
        XCTAssertEqual(MarkdownPreviewMode.rendered.toggled(), .source)
        XCTAssertEqual(MarkdownPreviewMode.source.toggled(), .rendered)
        XCTAssertEqual(MarkdownPreviewMode.rendered.toggled().toggled(), .rendered)
        XCTAssertEqual(MarkdownPreviewMode.controlTitle(for: MarkdownPreviewMode.rendered.toggled()), "渲染",
                       "翻转后标题没跟着翻：按钮会说谎")
    }

    // MARK: - 块级：标题

    func testATXHeadingKeepsLevelAndDropsOnlyTheMarker() {
        XCTAssertEqual(blocks("# 标题").first?.kind, .heading(level: 1))
        XCTAssertEqual(runs("# 标题"), [MarkdownInline(text: "标题")])
        XCTAssertEqual(blocks("###### 六级").first?.kind, .heading(level: 6))
        XCTAssertEqual(visible("###### 六级"), "六级")
    }

    func testSeventhHashIsNotAHeadingAndKeepsItsText() {
        // 超过 6 级 CommonMark 就不认了，整行退回段落 —— 关键是 `#######` 里的文字不许没。
        XCTAssertEqual(blocks("####### 七级不是标题").first?.kind, .paragraph)
        XCTAssertEqual(visible("####### 七级不是标题"), "####### 七级不是标题")
    }

    func testHashWithoutSpaceIsNotAHeading() {
        XCTAssertEqual(blocks("#没有空格").first?.kind, .paragraph)
        XCTAssertEqual(visible("#没有空格"), "#没有空格")
    }

    func testClosingHashesAreStrippedButCodeSharpIsNot() {
        XCTAssertEqual(runs("## 标题 ##"), [MarkdownInline(text: "标题")])
        XCTAssertEqual(runs("# C#").first?.text ?? "", "C#")
    }

    func testSetextUnderlinePromotesThePendingParagraph() {
        XCTAssertEqual(blocks("一级\n===").first?.kind, .heading(level: 1))
        XCTAssertEqual(blocks("二级\n---").first?.kind, .heading(level: 2))
        XCTAssertEqual(visible("二级\n---"), "二级")
    }

    func testLoneDashAfterParagraphIsNotAHeading() {
        // 与 CommonMark 的一处**有意偏差**：单个 `-` 跟在段落后面，中文笔记里通常是
        // 手写的分隔，而不是"这个段落是二级标题"。偏差的代价是漏认一个 setext 标题，
        // 收益是不把整段字升级成大标题 —— 后者更容易被用户当成 bug。
        let parsed = blocks("段落内容\n-")
        XCTAssertEqual(parsed.count, 1)
        XCTAssertEqual(parsed.first?.kind, .paragraph)
        XCTAssertEqual(visible("段落内容\n-"), "段落内容\n-")
    }

    // MARK: - 块级：代码

    func testFencedCodeKeepsContentAndLanguageAndDropsFence() {
        let parsed = blocks("```swift\nlet x = 1\n```")
        XCTAssertEqual(parsed.first?.kind, .codeBlock(language: "swift"))
        XCTAssertEqual(parsed.first?.runs.first?.text, "let x = 1")
    }

    func testFencedCodeKeepsRelativeIndentation() {
        // 逐行 trim 会把代码的层次抹平，而"看起来还是那段代码"是代码块唯一的价值。
        XCTAssertEqual(blocks("```\n  两格\n    四格\n```").first?.runs.first?.text, "  两格\n    四格")
    }

    func testUnclosedFenceRunsToEndInsteadOfVanishing() {
        let parsed = blocks("```python\nprint(1)\n还没闭栏")
        XCTAssertEqual(parsed.count, 1)
        XCTAssertEqual(parsed.first?.kind, .codeBlock(language: "python"))
        assertNothingIsLost("print(1)\n还没闭栏", visible("```python\nprint(1)\n还没闭栏"), "未闭栏的围栏")
    }

    func testTildeFenceWorksToo() {
        XCTAssertEqual(blocks("~~~\nplain\n~~~").first?.runs.first?.text, "plain")
    }

    func testIndentedCodeBlock() {
        let parsed = blocks("    四格缩进就是代码")
        XCTAssertEqual(parsed.first?.kind, .codeBlock(language: nil))
        XCTAssertEqual(parsed.first?.runs.first?.text, "四格缩进就是代码")
    }

    func testIndentedLineAfterParagraphIsAContinuationNotCode() {
        // CommonMark 同：缩进代码不能打断段落。
        let parsed = blocks("普通段落\n    缩进的续行")
        XCTAssertEqual(parsed.count, 1)
        XCTAssertEqual(parsed.first?.kind, .paragraph)
    }

    // MARK: - 块级：引用

    func testQuoteDropsTheMarkerButKeepsTheText() {
        let parsed = blocks("> 引言内容")
        XCTAssertEqual(parsed.first?.kind, .paragraph)
        XCTAssertEqual(parsed.first?.quoteDepth, 1)
        XCTAssertEqual(parsed.first?.runs, [MarkdownInline(text: "引言内容")])
    }

    func testHeadingInsideQuoteStaysAHeading() {
        // 早先按"引用是一种块类型"建模时，这条会退化成普通段落 ——
        // 引用里的标题仍然是标题，结构是 Markdown 的全部意义。
        let parsed = blocks("> ## 标题在引用里")
        XCTAssertEqual(parsed.first?.kind, .heading(level: 2))
        XCTAssertEqual(parsed.first?.quoteDepth, 1)
    }

    func testNestedQuotesAccumulateDepthAndStayLiteralBeyondTheCap() {
        XCTAssertEqual(blocks(">> 两层").first?.quoteDepth, 2)
        let deep = String(repeating: ">", count: MarkdownParsingPolicy.maximumQuoteDepth + 2) + " 太深了"
        let parsed = blocks(deep)
        XCTAssertTrue(parsed.allSatisfy { $0.quoteDepth <= MarkdownParsingPolicy.maximumQuoteDepth })
        assertNothingIsLost("太深了", visible(deep), "超深引用")
    }

    // MARK: - 块级：列表

    func testUnorderedItemsBecomeOneBlockEach() {
        let parsed = blocks("- 一\n- 二")
        XCTAssertEqual(parsed.count, 2)
        XCTAssertEqual(parsed.map(\.kind), [.unorderedItem(depth: 0, task: nil), .unorderedItem(depth: 0, task: nil)])
        XCTAssertEqual(parsed.map { $0.runs.first?.text }, ["一", "二"])
    }

    func testTwoSpaceIndentIsOneNestingLevel() {
        XCTAssertEqual(blocks("- 父\n  - 子").map(\.kind),
                       [.unorderedItem(depth: 0, task: nil), .unorderedItem(depth: 1, task: nil)])
    }

    func testStarLinesThatAreEmphasisAreNotListItems() {
        // `*斜体*` 起行的行没有"标记 + 空格"，不该被拆成列表。
        XCTAssertEqual(blocks("*斜体不是列表*").first?.kind, .paragraph)
    }

    func testOrderedItemNumberIsVisibleContent() {
        // 顺序是信息。`3. 第三步` 排成"第三步"会让读者以为步骤少了两步。
        let parsed = blocks("3. 第三步")
        XCTAssertEqual(parsed.first?.kind, .orderedItem(depth: 0, number: 3))
        XCTAssertEqual(visible("3. 第三步"), "3. 第三步")
    }

    func testOrderedMarkerNeedsSpaceAndContent() {
        XCTAssertEqual(blocks("2.Eleven 不是列表").first?.kind, .paragraph)
        XCTAssertEqual(blocks("1.").first?.kind, .paragraph, "只有标记没有正文：不画空编号")
        XCTAssertEqual(visible("1."), "1.")
    }

    func testEmptyListItemStaysLiteral() {
        // "- " 后面什么都没有：画一个悬空圆点没有信息量，原样显示更诚实。
        XCTAssertEqual(blocks("-").first?.kind, .paragraph)
        XCTAssertEqual(visible("-"), "-")
    }

    func testTaskItemsBecomeStatesAndTheLetterXIsConsumed() {
        XCTAssertEqual(blocks("- [x] 买牛奶").first?.kind, .unorderedItem(depth: 0, task: .checked))
        XCTAssertEqual(blocks("- [ ] 没做完").first?.kind, .unorderedItem(depth: 0, task: .unchecked))
        XCTAssertEqual(blocks("- [x] 买牛奶").first?.runs, [MarkdownInline(text: "买牛奶")])
        // `[x]` 里的 x 变成勾选符号，这是"不丢词"不变量的**显式例外**之一，
        // 所以下面的宽不变量用例要先把任务标记剥掉再比。
    }

    func testMultiLineListItemIsKeptTogether() {
        let parsed = blocks("- 第一行\n  续行还在这一项里\n- 下一项")
        XCTAssertEqual(parsed.count, 2)
        XCTAssertEqual(parsed.first?.runs.first?.text, "第一行\n续行还在这一项里")
    }

    // MARK: - 块级：分隔线、表格、段落

    func testThematicBreakVariants() {
        for source in ["---", "***", "___", "- - -"] {
            XCTAssertEqual(blocks(source).first?.kind, .thematicBreak, source)
        }
    }

    func testTableBecomesOneVerbatimBlockAndTheRuleRowDisappears() {
        let parsed = blocks("| 名称 | 数量 |\n| --- | --- |\n| 苹果 | 3 |")
        XCTAssertEqual(parsed.count, 1)
        XCTAssertEqual(parsed.first?.kind, .table)
        let content = parsed.first?.runs.first?.text ?? ""
        XCTAssertTrue(content.contains("名称"))
        XCTAssertTrue(content.contains("苹果"))
        XCTAssertFalse(content.contains("---"), "分隔行本身不进正文")
    }

    func testParagraphKeepsEverySourceNewline() {
        // 与 CommonMark 的另一处**有意偏差**：软换行不折叠成空格。
        // 中文笔记普遍"一句一行"，折叠后挤成一坨更难读；而且折叠会删字符，
        // 而"不丢可见文字"是这层的硬不变量。
        XCTAssertEqual(visible("一行\n二行\n三行"), "一行\n二行\n三行")
    }

    func testBlankLinesSeparateParagraphs() {
        XCTAssertEqual(blocks("甲\n\n乙").count, 2)
    }

    // MARK: - 行内

    func testEmphasisAndStrong() {
        XCTAssertEqual(runs("这是 **粗** 的字"),
                       [MarkdownInline(text: "这是 "),
                        MarkdownInline(marks: .strong, text: "粗"),
                        MarkdownInline(text: " 的字")])
        XCTAssertEqual(runs("这是 *斜* 的字")[1].marks, .emphasis)
        XCTAssertEqual(runs("***既粗又斜***")[0].marks, [.strong, .emphasis])
    }

    func testUnderscoresDoNotItaliciseSnakeCase() {
        // 这条是 `_` 规则存在的唯一理由：粘贴进来的代码里全是下划线标识符。
        XCTAssertEqual(runs("some_var_name"), [MarkdownInline(text: "some_var_name")])
        XCTAssertEqual(runs("_斜体_")[0].marks, .emphasis)
    }

    func testUnbalancedDelimitersStayLiteral() {
        XCTAssertEqual(runs("**没有闭栏"), [MarkdownInline(text: "**没有闭栏")])
        XCTAssertEqual(runs("`没有闭栏"), [MarkdownInline(text: "`没有闭栏")])
        XCTAssertEqual(runs("[没有括号](缺右"), [MarkdownInline(text: "[没有括号](缺右")])
    }

    func testStarAfterSpaceIsNotAnOpener() {
        // flanking：开栏右边是空白就不算强调开栏，`* 星号 *` 是两个星号加普通字。
        // （行首的 `* ` 是另一回事：那是列表标记，见 `testStarLineAtLineStartIsABullet`。）
        XCTAssertEqual(runs("这是 * 星号 * 的字"), [MarkdownInline(text: "这是 * 星号 * 的字")])
    }

    func testStarLineAtLineStartIsABullet() {
        // `* 星号 *` 起行在 CommonMark 里就是项目符号 + 正文"星号 *"，
        // 这是**规格行为**不是误判。钉住它，免得以后有人"顺手修掉"。
        let parsed = blocks("* 星号 *")
        XCTAssertEqual(parsed.first?.kind, .unorderedItem(depth: 0, task: nil))
        XCTAssertEqual(parsed.first?.runs.first?.text, "星号 *")
    }

    func testInlineCodeIsNotFurtherParsed() {
        let parsed = runs("看 `**原样**` 这段")
        XCTAssertEqual(parsed[1].marks, .code)
        XCTAssertEqual(parsed[1].text, "**原样**")
    }

    func testDoubleBacktickCodeSpanCanContainASingleBacktick() {
        let parsed = runs("`` a`b ``")
        XCTAssertEqual(parsed.first?.marks, .code)
        XCTAssertEqual(parsed.first?.text, "a`b")
    }

    func testCodeSpanLosesOneSpaceEachSideOnlyWhenBothPresent() {
        XCTAssertEqual(runs("` x `")[0].text, "x")
        XCTAssertEqual(runs("`x`")[0].text, "x")
        XCTAssertEqual(runs("`   `")[0].text, "   ", "全是空格时不去，否则内容变成空串")
    }

    func testStrikethrough() {
        XCTAssertEqual(runs("~~删掉的~~")[0].marks, .strikethrough)
    }

    func testLinkKeepsLabelAndCarriesDestination() {
        let parsed = runs("参考 [官方文档](https://example.com/doc) 里")
        XCTAssertEqual(parsed[1].marks, .link)
        XCTAssertEqual(parsed[1].text, "官方文档")
        XCTAssertEqual(parsed[1].destination, "https://example.com/doc")
    }

    func testLinkLabelCanHoldEmphasis() {
        let parsed = runs("[**重点**](https://a.example)")
        XCTAssertEqual(parsed.first?.marks, [.link, .strong])
        XCTAssertEqual(parsed.first?.text, "重点")
    }

    func testImageSyntaxStaysLiteral() {
        // 把 alt 文本显示成一个可点链接是**说谎**；原样显示 `![图](x.png)` 至多不好看。
        XCTAssertEqual(visible("![图](x.png)"), "![图](x.png)")
    }

    func testAutolinkNeedsAKnownScheme() {
        XCTAssertEqual(runs("<https://a.example>")[0].marks, .link)
        XCTAssertEqual(runs("<https://a.example>")[0].destination, "https://a.example")
        XCTAssertEqual(runs("<不是链接>"), [MarkdownInline(text: "<不是链接>")])
    }

    func testBackslashEscapeMakesTheNextCharacterLiteral() {
        XCTAssertEqual(runs("\\*不是斜体\\*"), [MarkdownInline(text: "*不是斜体*")])
        XCTAssertEqual(runs("\\# 不是标题").first?.text, "# 不是标题")
    }

    func testNestedEmphasisComposesMarks() {
        let parsed = runs("**粗 _和斜_ 结束**")
        XCTAssertEqual(parsed.map(\.marks), [.strong, [.strong, .emphasis], .strong])
        XCTAssertEqual(parsed.map(\.text), ["粗 ", "和斜", " 结束"])
    }

    func testInlineNestingBeyondTheCapFallsBackToLiteralText() {
        let deep = String(repeating: "**", count: MarkdownParsingPolicy.maximumInlineNestingDepth + 1) + "里"
        assertNothingIsLost("里", visible(deep), "超深嵌套")
    }

    // MARK: - 上限与截断

    func testRenderingStopsAtTheCharacterCapAndSaysSo() {
        let source = String(repeating: "一", count: MarkdownParsingPolicy.maximumRenderedCharacters + 10)
        let document = MarkdownParser.parse(source)
        XCTAssertTrue(document.isTruncated)
        XCTAssertEqual(document.visibleText.count, MarkdownParsingPolicy.maximumRenderedCharacters)
    }

    func testShortDocumentIsNeverMarkedTruncated() {
        XCTAssertFalse(MarkdownParser.parse("# 短").isTruncated)
    }

    // MARK: - 核心不变量：不丢可见文字

    func testAwkwardInputsKeepEveryWordInOrder() {
        // 这些是"故意让解析器难受"的输入：未闭合、错配、纯符号、HTML、CRLF、emoji。
        // 链接地址与 `[x]` 任务标记是**已声明的例外**（前者变成链接属性、后者变成勾选符号），
        // 所以用例本身不含这两种语法；它们的行为在上面的专门用例里钉。
        let corpus = [
            "# 标题 与 **未闭合的粗体\n- 列表项\n\n> 引用 `代码\n>> 更深\n",
            "| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 |\n",
            "```\nfunction f() { return 1 }\n```\n后面还有 正文",
            "2. 第二步\n   续行的内容\n***分隔***\n段落里的 <b>HTML</b> 原样显示",
            "CRLF 行尾\r\n第二行\r\n第三行",
            "🍎 emoji 与 **粗 🍌** 混排\n",
            "####### 七级\n#无空格\nsome_var_name 和 *星号 带空格*\n",
        ]
        for (offset, source) in corpus.enumerated() {
            assertNothingIsLost(source, visible(source), "语料第 \(offset) 条")
        }
    }

    func testTheThreeDeclaredExceptionsToTheNoLossInvariant() {
        // 把例外写进测试，而不是写进"反正没人看"的注释里：
        // 这三处确实会让源文本的字母不再出现在渲染结果里，所以任何改动都必须在
        // 有人读过这条用例的前提下发生。三处的共同点是**被吃掉的都是语法而不是 prose**：
        // 任务标记的 x、链接地址（变成链接属性）、围栏信息串（变成 codeBlock 的 language）。
        XCTAssertTrue(visible("- [x] 买牛奶").contains("买牛奶"))
        XCTAssertFalse(visible("- [x] 买牛奶").contains("x]"))

        XCTAssertTrue(visible("[官方文档](https://example.com)").contains("官方文档"))
        XCTAssertFalse(visible("[官方文档](https://example.com)").contains("https://example.com"))

        // 信息串不进正文，但它**在模型里**：渲染只是没把语言名摊在屏幕上，不是把它丢了。
        XCTAssertTrue(visible("```swift\nlet x = 1\n```").contains("let x = 1"))
        XCTAssertFalse(visible("```swift\nlet x = 1\n```").contains("swift"))
        XCTAssertEqual(blocks("```swift\nlet x = 1\n```").first?.kind, .codeBlock(language: "swift"))
    }

    func testEmptyAndWhitespaceSourcesProduceNothingRatherThanCrashing() {
        for source in ["", "   ", "\n\n\n", "```", "###", ">", "|", "**"] {
            let document = MarkdownParser.parse(source)
            // 只要求不崩、且解析结果要么空、要么只含原样保留的字面量。
            for block in document.blocks {
                XCTAssertTrue(block.runs.allSatisfy { !$0.text.isEmpty }, "\(source) 解析出空 run")
            }
        }
    }

    func testQuotedBlocksKeepTheirOrder() {
        // 连续的 `>` 行在 CommonMark 里是**同一段**（引用内的软换行由我们保留成换行），
        // 所以是两块：引用段 + 正文段。空 run 不允许出现（那是"``` 只有开栏"那次的回归）。
        let parsed = blocks("> 甲\n> 乙\n丙")
        XCTAssertEqual(parsed.map { $0.runs.first?.text }, ["甲\n乙", "丙"])
        XCTAssertEqual(parsed.map(\.quoteDepth), [1, 0])
    }
}
