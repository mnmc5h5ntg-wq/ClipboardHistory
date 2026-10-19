import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 第四轮新增功能「右侧预览渲染 Markdown」的判据。
///
/// 按 `AGENTS.md` 的定义完成标准分三层，**缺一层就不算做完**：
/// 1. 纯函数真值表（`MarkdownParsingTests` 一份，这里一份呈现层的）；
/// 2. **产品入口**：临时目录里写一个真的 `.md` 文件，走 `MediaLoader` → `FilePreview`
///    → 真的建一个 `ChineseSelectableNSTextView`，从视图自己的 `attributedString` 把属性读回来；
/// 3. 接线锚点：判"视图确实把 Markdown 交给了渲染器"，而不是判"渲染器存在"。
///    第二轮 N-1 的教训就是纯函数全绿而产品照崩（D-034 / D-038）。
///
/// 数据安全：只用 `FileManager.temporaryDirectory` 下的私有子目录 + `RecordingHistoryPersistence`
/// + `TestClipboardWriter`，从不碰 `~/Library/Application Support/时间剪史/`（D-002）。
@MainActor
final class Round4MarkdownTests: XCTestCase {

    private let sample = """
    # 发布说明

    这一段里有一个 **粗体**、一个 *emphasis*，还有行内 `code`。

    - [x] 已经完成
    - [ ] 还没有
    3. 第三步的内容

    > 引用里的话
    > 第二行

    ```swift
    let x = 1
    ```

    | 名称 | 数量 |
    | --- | --- |
    | 苹果 | 3 |

    参考 [官方文档](https://example.com/doc) 与 <https://bare.example>。
    """

    private var temporaryDirectory: URL = FileManager.default.temporaryDirectory
        .appendingPathComponent("markdown-preview-tests", isDirectory: true)

    // MARK: - ② 产品入口：真实文件 → 真实预览管线 → 真实文本视图

    func testMarkdownFileGoesThroughTheRealPreviewPipelineIntoAStyledTextView() async throws {
        let url = try writeTemporaryFile(named: "README.md", contents: sample)

        // 产品入口一：详情区用的就是这条加载路径。
        let previewState = await MediaLoader.loadFilePreview(url: url, thumbnail: nil)
        guard case .success(let preview) = previewState, case .text(let loaded) = preview.content else {
            XCTFail("Markdown 文件没有走通文本预览路径：\(previewState)")
            return
        }
        XCTAssertEqual(loaded, sample, "读回来的正文与磁盘上的不一致")

        // 产品入口二：视图决定渲不渲。
        XCTAssertTrue(MarkdownRenderingAffordance.renders(url: url, in: .rendered))
        XCTAssertFalse(MarkdownRenderingAffordance.renders(url: url, in: .source),
                       "「原文」态必须还给用户那一份原始字节")

        // 产品入口三：真的建一个只读正文视图，让它走生产方法。
        let view = ChineseSelectableNSTextView()
        let marked = view.updateMarkdown(source: loaded, highlightQuery: "")
        XCTAssertEqual(marked, 0, "没给搜索词却标了命中")

        let storage = try XCTUnwrap(view.textStorage, "只读正文没有文本存储")
        XCTAssertTrue(storage.string.contains("发布说明"))
        XCTAssertTrue(storage.string.contains("第三步的内容"), "有序项正文丢了")
        XCTAssertTrue(storage.string.contains("3."), "有序项的编号丢了：顺序是内容")
        XCTAssertFalse(storage.string.contains("# 发布说明"), "标题的 `#` 还在，等于没渲染")
        XCTAssertFalse(storage.string.contains("```"), "围栏标记漏在渲染结果里")
        XCTAssertFalse(storage.string.contains("let x = 1\n```"))

        // 字号：一级标题确实比正文大（这一条是"渲染"这件事的最低标准）。
        let headingAttributes = try XCTUnwrap(attributes(in: storage, containing: "发布说明"))
        let headingFont = try XCTUnwrap(headingAttributes[.font] as? NSFont)
        let bodyAttributes = try XCTUnwrap(attributes(in: storage, containing: "还有行内"))
        let bodyFont = try XCTUnwrap(bodyAttributes[.font] as? NSFont)
        XCTAssertGreaterThan(headingFont.pointSize, bodyFont.pointSize,
                             "标题字号没超过正文，那这不是渲染只是去掉了 #")
        XCTAssertEqual(bodyFont.pointSize, MarkdownPresentation.bodyFontSize)

        // 中文强调不许是合成斜体；拉丁强调必须是斜体。
        XCTAssertFalse(try isItalic(storage, containing: "粗体"),
                       "中文 **粗体** 被排成倾斜 —— 系统没有真中文斜体，那是错切出来的假字形")
        XCTAssertTrue(try isItalic(storage, containing: "emphasis"),
                      "拉丁 *斜体* 没有斜体，等于这个语法白解析了")

        // 行内码要等宽 + 有底色。
        let codeAttributes = try XCTUnwrap(attributes(in: storage, containing: "code"))
        XCTAssertNotNil(codeAttributes[.backgroundColor], "行内码没有底色，和正文分不开")
        let codeFont = try XCTUnwrap(codeAttributes[.font] as? NSFont)
        XCTAssertEqual(codeFont.familyName, MarkdownPresentation.codeFont.familyName,
                       "行内码不是等宽字体：\(codeFont)")

        // 代码块整块等宽。
        let blockAttributes = try XCTUnwrap(attributes(in: storage, containing: "let x = 1"))
        XCTAssertEqual((try XCTUnwrap(blockAttributes[.font] as? NSFont)).familyName,
                       MarkdownPresentation.codeFont.familyName)

        // 链接：标签可点，地址不外泄成文字。
        let linkAttributes = try XCTUnwrap(attributes(in: storage, containing: "官方文档"))
        let link = try XCTUnwrap(linkAttributes[.link] as? URL)
        XCTAssertEqual(link.absoluteString, "https://example.com/doc")
        XCTAssertFalse(storage.string.contains("https://example.com/doc)"),
                       "链接地址被当正文摊在屏幕上")

        // 只读区仍然是"复制出来是纯文本"，而且仍然是中文菜单那一份。
        XCTAssertFalse(view.isRichText, "富文本正文把只读区变成了可粘贴富文本的编辑区")
        XCTAssertTrue(view.isSelectable)
        XCTAssertEqual(view.menu?.title, "")
        let titles = (view.menu?.items ?? []).map(\.title)
        XCTAssertEqual(titles, ["复制", "", "全选", "查找…"], "渲染态丢了收口过的中文右键菜单：\(titles)")
    }

    func testHighlightStillWorksOnRenderedMarkdownAndNeverMutatesTheText() throws {
        let view = ChineseSelectableNSTextView()
        _ = view.updateMarkdown(source: sample, highlightQuery: "")
        let beforeRender = try XCTUnwrap(view.textStorage)

        let marked = view.updateMarkdown(source: sample, highlightQuery: "发布")
        XCTAssertEqual(marked, 1, "渲染后的正文里搜索命中没打上")
        XCTAssertEqual(view.string, beforeRender.string,
                       "高亮改了文本内容 —— 命中必须走临时属性，不是改串")

        let layoutManager = try XCTUnwrap(view.layoutManager)
        // 命中位置**从渲染结果里查**，不手数下标：渲染把 `#` 吃掉了，
        // "发布"在原文里的下标和在渲染结果里的下标不一样（这一类数错下标的错本轮犯过两次）。
        let hit = (view.string as NSString).range(of: "发布")
        XCTAssertNotEqual(hit.location, NSNotFound, "夹具前提：渲染结果里得有这么个词")
        let background = layoutManager.temporaryAttribute(.backgroundColor,
                                                         atCharacterIndex: hit.location,
                                                         effectiveRange: nil) as? NSColor
        XCTAssertNotNil(background, "命中字符上没有临时底色")
        XCTAssertNil(beforeRender.attribute(.backgroundColor, at: hit.location, effectiveRange: nil),
                     "底色被写进了文本存储而不是临时属性")

        // 换搜索词要清掉旧命中（U-4 那条规矩在新路径上同样成立）。
        _ = view.updateMarkdown(source: sample, highlightQuery: "不存在的词")
        XCTAssertNil(layoutManager.temporaryAttribute(.backgroundColor,
                                                      atCharacterIndex: hit.location,
                                                      effectiveRange: nil),
                     "旧命中留在原来的位置上，会把用户指到不含搜索词的地方")
    }

    func testSameSourceDoesNotRebuildTheBodySoTypingInTheSearchFieldStaysCheap() throws {
        let view = ChineseSelectableNSTextView()
        _ = view.updateMarkdown(source: sample, highlightQuery: "")
        // 留住一次选中区：重建正文会把选中区清空，所以它正好是"有没有重新赋值"的探针。
        view.setSelectedRange(NSRange(location: 3, length: 5))
        _ = view.updateMarkdown(source: sample, highlightQuery: "发布")
        XCTAssertEqual(view.selectedRange, NSRange(location: 3, length: 5),
                       "同一份源码又被重建了一次：搜索框每敲一个字都会重排整篇")

        _ = view.updateMarkdown(source: "# 换了内容", highlightQuery: "")
        XCTAssertTrue(view.string.contains("换了内容"))
        XCTAssertNotEqual(view.selectedRange, NSRange(location: 3, length: 5),
                          "源码变了却没重建")
    }

    func testRenderingAMarkdownEntryNeverRewritesWhatTheStoreHolds() throws {
        // "渲染只改看法、不改数据"必须是可证的：走 store 的真实写回路径。
        let writer = TestClipboardWriter()
        let store = HistoryStore(clipboardWriter: writer,
                                 persistence: RecordingHistoryPersistence(),
                                 retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
        let source = "# 标题\n\n- 项目"
        store.add(ClipboardIntake.Entry(content: .text(source), thumbnail: nil, sourceUTIs: []),
                  timestamp: Date(timeIntervalSince1970: 1))
        let entry = try XCTUnwrap(store.entries.first)

        let view = ChineseSelectableNSTextView()
        _ = view.updateMarkdown(source: source, highlightQuery: "")
        XCTAssertFalse(view.string.contains("# 标题"), "夹具前提：确实渲染过了")

        store.perform(.copyAndPromote(entry))
        let writtenContents = writer.writtenContents
        guard case .text(let written)? = writtenContents.last else {
            XCTFail("复制管线写出的不是文本：\(writtenContents)")
            return
        }
        XCTAssertEqual(written, source,
                       "复制出去的是渲染后的文字 —— 存档与剪贴板都必须还是用户原来那份")
    }

    // MARK: - ②′ 视图树里的活路径（锚点挡不住"把分支改成恒假"，这一层可以）

    /// 把任意视图铺进一个离屏窗口，返回窗口（要活着，否则视图跟着析构）与树里的正文视图。
    /// 手法与 `UICaptureHarness` 同一套：裸 `NSHostingView` 没有 window 时
    /// `maxWidth: .infinity` 会退化，量到的几何就不是真的。
    private func mount<V: View>(_ view: V, size: NSSize = NSSize(width: 720, height: 520))
        -> (window: NSWindow, host: NSHostingView<V>) {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(origin: .zero, size: size),
                              styleMask: [.titled, .closable, .resizable],
                              backing: .buffered, defer: false)
        window.appearance = NSAppearance(named: .aqua)
        let host = NSHostingView(rootView: view)
        host.frame = NSRect(origin: .zero, size: size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.setContentSize(size)
        window.layoutIfNeeded()
        host.layoutSubtreeIfNeeded()
        return (window, host)
    }

    /// 走树要**现走**，不能一次拍平：文件预览在 `.loading` 那一态里根本没有正文视图，
    /// 挂载时取一次快照就会永远等不到它（第一次跑这条用例就是这么红的）。
    private func bodies(in host: NSView) -> [ChineseSelectableNSTextView] {
        var found: [ChineseSelectableNSTextView] = []
        var queue: [NSView] = [host]
        while let current = queue.popLast() {
            if let body = current as? ChineseSelectableNSTextView { found.append(body) }
            queue.append(contentsOf: current.subviews)
        }
        return found
    }

    private func waitUntil(_ description: String, timeout: TimeInterval = 5.0,
                           condition: @MainActor () -> Bool) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立")
    }

    private func runs(_ text: String) -> [MarkdownInline] {
        MarkdownInlineParser.runs(in: text)
    }

    private func markdownTextStore() -> HistoryStore {
        let store = HistoryStore(clipboardWriter: TestClipboardWriter(),
                                 persistence: RecordingHistoryPersistence(),
                                 retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text(UICaptureTests.markdownFixtureBody),
                                        thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        store.perform(.selectOnly(store.entries[0]))
        return store
    }

    /// 这条是**功能本身**的判据：详情视图真的把 Markdown 交给了渲染器，
    /// 而且「原文」那一路确实还回到原始字节。源码锚点只能证明"字还在那儿"，
    /// 把 `if renders(...)` 改成 `if false && renders(...)` 时锚点全绿、产品照旧不渲染
    /// —— 本轮变异对照实测到的就是这个缺口。
    func testDetailViewRendersMarkdownInTheMountedViewTree() throws {
        let rendered = mount(DetailView(historyStore: markdownTextStore(),
                                        initialMarkdownMode: .rendered))
        let renderedBodies = bodies(in: rendered.host)
        XCTAssertEqual(renderedBodies.count, 1, "详情树里应该只有一块正文视图")
        let body = try XCTUnwrap(renderedBodies.first)
        XCTAssertFalse(body.string.contains("# 发布时间剪史"),
                       "渲染分支没生效：正文里仍是 Markdown 原文")
        XCTAssertFalse(body.string.contains("```"))
        XCTAssertTrue(body.string.contains("发布时间剪史 1.4.9"), "渲染把标题正文弄丢了")
        XCTAssertTrue(body.string.contains("第三步的内容不能被吃掉"))

        let headingRange = (body.string as NSString).range(of: "发布时间剪史")
        XCTAssertNotEqual(headingRange.location, NSNotFound)
        let headingFont = try XCTUnwrap(body.attributedString()
            .attribute(.font, at: headingRange.location, effectiveRange: nil) as? NSFont)
        XCTAssertEqual(headingFont.pointSize, MarkdownPresentation.headingFontSize(level: 1),
                       "标题在真实视图树里没有拿到标题字号（渲染只发生在纯函数层）")

        // 同一份数据、同一个入口，切到「原文」必须看见标记。
        let source = mount(DetailView(historyStore: markdownTextStore(),
                                      initialMarkdownMode: .source))
        let sourceBody = try XCTUnwrap(bodies(in: source.host).first)
        XCTAssertTrue(sourceBody.string.contains("## 安装"),
                      "「原文」态没有把原始 Markdown 还给用户")
        XCTAssertNotEqual(body.string, sourceBody.string,
                          "两种模式画出同一个字符串 ⇒ 那颗控件背后什么都没有切换")
    }

    /// 文件那一路（磁盘上的真 `.md` → `DetailFileView` → 视图）在离屏窗口里量不到：
    /// `DetailFileView` 靠 SwiftUI 的 `.task(id:)` 异步加载，而 `.task` 在"从未 ordered front
    /// 的窗口"里不会启动 —— 实测树里永远停在 `NSProgressIndicator`（第一次跑这条用例就是这么红的）。
    /// 所以这一路的**活路径**判据搬到了在屏探针
    /// `UIInteractionProbeTests.testMarkdownFilePreviewRendersInARealWindow`
    /// （CI 会跑，`CLIPBOARD_HISTORY_UI_INTERACTION=1`），这里只留能确定性判的部分：
    /// 加载路径本身（上面那条 `testMarkdownFileGoesThroughTheRealPreviewPipelineIntoAStyledTextView`）
    /// 与"视图确实按判定分叉"（下面两条源码锚点）。
    func testTheOffscreenFilePreviewLimitationIsRecordedNotPaperedOver() throws {
        let url = try writeTemporaryFile(named: "说明.md", contents: sample)
        XCTAssertTrue(MarkdownRenderingAffordance.renders(url: url, in: .rendered))
        XCTAssertFalse(MarkdownRenderingAffordance.renders(url: url, in: .source))
        // 多文件里夹一个 .md：头部那颗控件必须出现（否则展开后没法退回原文）。
        let mixed: ClipboardEntryContent = .files([URL(fileURLWithPath: "/tmp/图.png"), url])
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: mixed))
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .file(URL(fileURLWithPath: "/tmp/合同.pdf"))))
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .image(try makeStoredImage())))
    }

    func testTheToggleIsNotPromisedForAMarkdownFileThatIsGone() throws {
        let here = try writeTemporaryFile(named: "在那.md", contents: sample)
        let gone = URL(fileURLWithPath: "/tmp/absent-\(UUID().uuidString).md")
        // 夹具前提：那个"不在了"的路径真的不在（否则这条测的是别的东西）。
        XCTAssertFalse(FileManager.default.fileExists(atPath: gone.path))

        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .file(gone), exists: { _ in false }),
                       "文件都不在了还承诺有两种看法")
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: .file(here), exists: { _ in true }))
        // 产品侧那一份走真实文件系统：把文件删掉，入口要跟着消失。
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: .file(here)))
        try FileManager.default.removeItem(at: here)
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .file(here)),
                       "文件被移走之后头部还挂着那颗控件")

        // 多文件：只要有一个还在的 .md 就给；全都不在了就不给。
        let another = try writeTemporaryFile(named: "另一个.md", contents: sample)
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: .files([gone, another]),
                                                         exists: { $0 == gone ? false : true }))
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .files([gone, another]), exists: { _ in false }))
    }

    func testAutolinkOnlyAcceptsWebAndMailSchemesInTheParser() {
        // 与 `linkURL(for:)` 的白名单逐个对齐；`file:` 不在名单里：
        // 一个只读预览不该把本地路径变成可点的东西。
        XCTAssertEqual(runs("<https://a.example>")[0].marks, .link)
        XCTAssertEqual(runs("<mailto:a@b.example>")[0].marks, .link)
        XCTAssertEqual(runs("<file:///tmp/x>"), [MarkdownInline(text: "<file:///tmp/x>")])
        XCTAssertEqual(runs("<javascript:alert(1)>").first?.marks, MarkdownInline.Mark.plain)
    }

    func testLinkColourAndClickabilityAlwaysAgree() {
        // 蓝到下划线却点不动，是最容易做出来、也最难被"看帧"发现的一种说谎。
        let paragraph = MarkdownBlock(kind: .paragraph, runs: [])
        let clickable = MarkdownInline(marks: .link, text: "文档", destination: "https://a.example")
        let inert = MarkdownInline(marks: .link, text: "本地", destination: "file:///tmp/x")
        let clickAttrs = MarkdownPresentation.attributes(for: clickable, in: paragraph)
        let inertAttrs = MarkdownPresentation.attributes(for: inert, in: paragraph)
        XCTAssertNotNil(clickAttrs[.link])
        XCTAssertEqual(clickAttrs[.foregroundColor] as? NSColor, MarkdownPresentation.linkColor)
        XCTAssertNil(inertAttrs[.link])
        XCTAssertNotEqual(inertAttrs[.foregroundColor] as? NSColor, MarkdownPresentation.linkColor,
                          "点不动的目标仍然被涂成链接色：假 affordance")
    }

    // MARK: - ① 呈现层真值表

    func testHeadingTypeScaleIsMonotonicAndNeverSmallerThanBody() {
        var previous = CGFloat.greatestFiniteMagnitude
        for level in 1...MarkdownParsingPolicy.maximumHeadingLevel {
            let size = MarkdownPresentation.headingFontSize(level: level)
            XCTAssertLessThanOrEqual(size, previous, "第 \(level) 级标题比上一级还大")
            XCTAssertGreaterThanOrEqual(size, MarkdownPresentation.bodyFontSize - 2,
                                        "第 \(level) 级标题小到和正文分不开")
            previous = size
        }
        // 变异对照用：整条字阶被"顺手改成常数"时这里必须红。
        XCTAssertGreaterThan(MarkdownPresentation.headingFontSize(level: 1),
                             MarkdownPresentation.headingFontSize(level: 3))
        XCTAssertEqual(MarkdownPresentation.headingFontSize(level: 99),
                       MarkdownPresentation.headingFontSize(level: 6), "越界的层级没被夹住")
        XCTAssertEqual(MarkdownPresentation.headingFontSize(level: 0),
                       MarkdownPresentation.headingFontSize(level: 1))
    }

    func testChineseEmphasisUsesWeightAndLatinUsesItalic() {
        XCTAssertEqual(MarkdownPresentation.emphasisStyle(for: "重点"), .heavierWeight)
        XCTAssertEqual(MarkdownPresentation.emphasisStyle(for: "emphasis"), .italic)
        // 混排按 CJK 走：合成斜体在汉字上是"糊字"，拉丁那几个字母跟着直立代价小得多。
        XCTAssertEqual(MarkdownPresentation.emphasisStyle(for: "重点 emphasis"), .heavierWeight)
        XCTAssertTrue(MarkdownPresentation.containsCJK("全角ＡＢＣ"))
        XCTAssertTrue(MarkdownPresentation.containsCJK("日本語"))
        XCTAssertTrue(MarkdownPresentation.containsCJK("한국어"))
        XCTAssertFalse(MarkdownPresentation.containsCJK("plain ascii 123"))

        let cjk = MarkdownPresentation.fontPlan(for: MarkdownInline(marks: .emphasis, text: "重点"),
                                                in: MarkdownBlock(kind: .paragraph, runs: []))
        XCTAssertFalse(cjk.isItalic)
        XCTAssertEqual(cjk.weight, .medium)

        let latin = MarkdownPresentation.fontPlan(for: MarkdownInline(marks: .emphasis, text: "emphasis"),
                                                 in: MarkdownBlock(kind: .paragraph, runs: []))
        XCTAssertTrue(latin.isItalic)
        XCTAssertEqual(latin.weight, .regular, "拉丁斜体不该同时把字重也抬上去")
    }

    func testStrongInsideHeadingDoesNotClimbTheWeightScaleForever() {
        let plan = MarkdownPresentation.fontPlan(for: MarkdownInline(marks: .strong, text: "粗"),
                                                 in: MarkdownBlock(kind: .paragraph, runs: []))
        XCTAssertEqual(plan.weight, .bold)
        let inHeading = MarkdownPresentation.fontPlan(
            for: MarkdownInline(marks: .strong, text: "粗"),
            in: MarkdownBlock(kind: .heading(level: 1), runs: [])
        )
        XCTAssertEqual(inHeading.weight, .bold, "一级标题本来就是 bold，`**` 不该再加一档")
    }

    func testInlineCodeKeepsItsBlocksSizeButTurnsMonospaced() {
        let inHeading = MarkdownPresentation.fontPlan(
            for: MarkdownInline(marks: .code, text: "x"),
            in: MarkdownBlock(kind: .heading(level: 2), runs: [])
        )
        XCTAssertEqual(inHeading.size, MarkdownPresentation.headingFontSize(level: 2),
                       "标题里的行内码突然掉到正文字号，行高会跳一下")
        XCTAssertTrue(inHeading.isMonospaced)
    }

    func testWideContentBlocksAreAlwaysMonospacedAndNeverItalicised() {
        for kind: MarkdownBlock.Kind in [.codeBlock(language: "swift"), .table] {
            let block = MarkdownBlock(kind: kind, runs: [MarkdownInline(text: "a | b")])
            let plan = MarkdownPresentation.fontPlan(for: MarkdownInline(marks: [.emphasis], text: "a | b"),
                                                    in: block)
            XCTAssertTrue(plan.isMonospaced, "\(kind) 没走等宽")
            XCTAssertFalse(plan.isItalic, "\(kind) 里的下划线被当成强调排斜了")
        }
    }

    func testTableIsNotDressedAsCodeButKeepsItsOwnGrouping() {
        // R234 看图量到的病：表格与代码块在画面上同形（同字号、同灰底、同段距），而那块灰底
        // 在 macOS 上一律读成"这是源码"。这一格钉的是**两张不同的脸**：代码块吃灰底、表格不吃，
        // 但表格仍然等宽（列对齐靠它）—— 摘掉底色不许顺手把等宽一起弄丢。
        let code = MarkdownBlock(kind: .codeBlock(language: nil), runs: [MarkdownInline(text: "let x = 1")])
        let table = MarkdownBlock(kind: .table, runs: [MarkdownInline(text: "| 名称 | 数量 |")])
        XCTAssertTrue(MarkdownPresentation.appliesWideContentBackground(to: code),
                      "代码块的灰底是它唯一的块边界，撤掉就没有边界了")
        XCTAssertFalse(MarkdownPresentation.appliesWideContentBackground(to: table),
                       "表格又吃灰底 ⇒ 和代码块同形，渲染模式把数据表说成源码")
        // 谓词说了不算：读**真产物**上那一行的 `.backgroundColor`。
        let doc = MarkdownDocument(blocks: [code, table], isTruncated: false)
        let out = MarkdownPresentation.attributedString(for: doc)
        var sawCodeBackground = false
        var sawTableWithoutBackground = false
        out.enumerateAttribute(.backgroundColor, in: NSRange(location: 0, length: out.length)) { value, range, _ in
            let text = (out.string as NSString).substring(with: range)
            if text.contains("let x = 1") {
                XCTAssertEqual(value as? NSColor, MarkdownPresentation.codeBackground,
                               "代码块那一行没拿到灰底 ⇒ 这条断言没在判它说的事")
                sawCodeBackground = true
            }
            if text.contains("| 名称 | 数量 |") {
                XCTAssertNil(value, "表格那一行仍被涂了底色 ⇒ 和代码块同形")
                sawTableWithoutBackground = true
            }
        }
        XCTAssertTrue(sawCodeBackground && sawTableWithoutBackground,
                      "两行都没在产物里露面 ⇒ 这一格是空判（枚举没覆盖到被测文本）")
        XCTAssertTrue(MarkdownPresentation.fontPlan(for: MarkdownInline(text: "| 名称 | 数量 |"), in: table)
                        .isMonospaced,
                      "撤底色的代价如果是丢等宽，表格的竖线会散开 ⇒ 更糟")
    }

    func testListAndQuoteIndentsStackAndAreClamped() {
        let nested = MarkdownBlock(kind: .unorderedItem(depth: 2, task: nil), runs: [], quoteDepth: 1)
        let flat = MarkdownBlock(kind: .paragraph, runs: [])
        XCTAssertGreaterThan(MarkdownPresentation.firstLineHeadIndent(for: nested),
                             MarkdownPresentation.firstLineHeadIndent(for: flat))
        // 悬挂缩进：续行要对齐正文，不是对齐圆点下面。
        let item = MarkdownBlock(kind: .unorderedItem(depth: 0, task: nil), runs: [])
        XCTAssertGreaterThan(MarkdownPresentation.headIndent(for: item),
                             MarkdownPresentation.firstLineHeadIndent(for: item))
        let paragraph = MarkdownBlock(kind: .paragraph, runs: [])
        XCTAssertEqual(MarkdownPresentation.headIndent(for: paragraph),
                       MarkdownPresentation.firstLineHeadIndent(for: paragraph))

        let absurd = MarkdownBlock(kind: .unorderedItem(depth: 999, task: nil), runs: [])
        XCTAssertEqual(MarkdownPresentation.listDepth(of: absurd.kind),
                       CGFloat(MarkdownPresentation.maximumListDepth), "深度没夹住，缩进会推出容器")
    }

    func testMarkersAndGlyphsAreStable() {
        XCTAssertEqual(MarkdownPresentation.bulletGlyph(depth: 0), "•")
        XCTAssertEqual(MarkdownPresentation.bulletGlyph(depth: 1), "◦")
        XCTAssertEqual(MarkdownPresentation.bulletGlyph(depth: 2), "▪")
        XCTAssertEqual(MarkdownPresentation.bulletGlyph(depth: 99), "▪", "超深没重复最后一档")
        XCTAssertEqual(MarkdownPresentation.taskGlyph(.checked), "☑")
        XCTAssertEqual(MarkdownPresentation.taskGlyph(.unchecked), "☐")
        XCTAssertNil(MarkdownPresentation.taskGlyph(nil))
    }

    func testOnlyWebAndMailLinksBecomeClickable() {
        for destination in ["https://example.com", "http://a", "mailto:x@y.z"] {
            XCTAssertNotNil(MarkdownPresentation.linkURL(for: destination), destination)
        }
        // 只读预览不该把来路不明的剪贴板内容变成启动器。
        for destination in ["javascript:alert(1)", "file:///etc/passwd", "telnet://x", "data:text/html,x", ""] {
            XCTAssertNil(MarkdownPresentation.linkURL(for: destination), destination)
        }
    }

    func testEveryLinkedRunActuallyCarriesAClickableDestination() throws {
        // 解析层与呈现层的协议名单必须逐个对齐，否则屏幕上会出现"蓝色但点不动"的假链接。
        let source = "[网页](https://a.example) [邮件](mailto:x@y.z) [本地](file:///tmp/x) [脚本](javascript:alert(1)) <https://bare.example>"
        let document = MarkdownParser.parse(source)
        let linked = document.blocks.flatMap(\.runs).filter { $0.marks.contains(.link) }
        XCTAssertFalse(linked.isEmpty, "夹具前提：这条语料里得有链接")
        let paragraph = MarkdownBlock(kind: .paragraph, runs: [])
        for run in linked {
            let resolved = MarkdownPresentation.attributes(for: run, in: paragraph)
            if let destination = run.destination,
               MarkdownPresentation.linkURL(for: destination) != nil {
                XCTAssertNotNil(resolved[.link], "带 .link 样式的 run 没有可点目标：\(destination)")
            } else {
                XCTAssertNil(resolved[.link], "\(run.destination ?? "nil") 不该变成可点链接")
            }
        }
    }

    func testEmptyDocumentRendersNothingRatherThanAStandaloneNewline() {
        let rendered = MarkdownPresentation.attributedString(for: MarkdownDocument())
        XCTAssertEqual(rendered.length, 0)
        XCTAssertEqual(MarkdownPresentation.attributedString(for: MarkdownParser.parse("")).length, 0)
    }

    func testTruncationNoteAppearsOnlyWhenTruncated() {
        let full = MarkdownPresentation.attributedString(for: MarkdownParser.parse("# 短"))
        XCTAssertFalse(full.string.contains(MarkdownParsingPolicy.truncationNote))
        let long = String(repeating: "字", count: MarkdownParsingPolicy.maximumRenderedCharacters + 1)
        let cut = MarkdownPresentation.attributedString(for: MarkdownParser.parse(long))
        XCTAssertTrue(cut.string.contains(MarkdownParsingPolicy.truncationNote),
                      "截断了却不告诉用户，那就是「悄悄少了一段」")
    }

    func testQuoteLevelIsCarriedByIndentNotByAFadedTextColor() {
        // 引用正文用正文字色。这一度被改成"弱化"，两次都被实测否掉：
        // `secondaryLabelColor` 亮色帧 3.95:1（引用是散文，14pt 要 4.5:1），
        // `labelColor.withAlphaComponent(0.8)` 暗色下被烤成黑色 → 整行看不见。
        // 所以层级只靠缩进表达；这条断言守的是"别再用手烤的浅色"。
        let quoted = MarkdownBlock(kind: .paragraph, runs: [MarkdownInline(text: "引用")], quoteDepth: 1)
        let plain = MarkdownBlock(kind: .paragraph, runs: [MarkdownInline(text: "正文")])
        XCTAssertEqual(MarkdownPresentation.foregroundColor(for: quoted),
                       MarkdownPresentation.foregroundColor(for: plain))
        XCTAssertGreaterThan(MarkdownPresentation.firstLineHeadIndent(for: quoted),
                             MarkdownPresentation.firstLineHeadIndent(for: plain),
                             "引用既不缩进也不弱化，那就等于没有引用这一级")
        let heading = MarkdownBlock(kind: .heading(level: 2), runs: [MarkdownInline(text: "标题")], quoteDepth: 1)
        XCTAssertEqual(MarkdownPresentation.foregroundColor(for: heading), MarkdownPresentation.headingColor)
    }

    func testMarkersThatCarryMeaningAreNotFaded() {
        // `3.` 是顺序、`☑` 是完成态 —— 它们是内容，必须和正文同色；
        // 项目符号是装饰，可以弱一档。
        let ordered = MarkdownBlock(kind: .orderedItem(depth: 0, number: 3), runs: [])
        let task = MarkdownBlock(kind: .unorderedItem(depth: 0, task: .checked), runs: [])
        let bullet = MarkdownBlock(kind: .unorderedItem(depth: 0, task: nil), runs: [])
        XCTAssertEqual(MarkdownPresentation.markerColor(for: ordered), MarkdownPresentation.meaningfulMarkerColor)
        XCTAssertEqual(MarkdownPresentation.markerColor(for: task), MarkdownPresentation.meaningfulMarkerColor)
        XCTAssertEqual(MarkdownPresentation.markerColor(for: bullet), MarkdownPresentation.markerColor)
        XCTAssertNotEqual(MarkdownPresentation.markerColor(for: ordered),
                          MarkdownPresentation.markerColor(for: bullet), "两档标记一个颜色，等于这条分档没写")
    }

    // MARK: - 动态色守卫（这一族缺陷的根因探针）

    private func resolve(_ color: NSColor, under name: NSAppearance.Name) -> (r: CGFloat, g: CGFloat, b: CGFloat, a: CGFloat) {
        let appearance = NSAppearance(named: name)!
        var resolved = (CGFloat(-1), CGFloat(-1), CGFloat(-1), CGFloat(-1))
        appearance.performAsCurrentDrawingAppearance {
            let srgb = color.usingColorSpace(.sRGB) ?? color
            resolved = (srgb.redComponent, srgb.greenComponent, srgb.blueComponent, srgb.alphaComponent)
        }
        return resolved
    }

    /// 在**指定外观下**求值一个颜色，模拟"静态常量在哪一刻被烤色"。
    ///
    /// 这一层不是洁癖：上一版直接写 `resolve(.labelColor.withAlphaComponent(0.8), under: .darkAqua)`，
    /// 单独跑是绿的，**全量跑却红了** —— 因为 `withAlphaComponent` 按"调用那一刻的当前外观"烤色，
    /// 而当前外观会被同进程里前一个测试留下状态影响。
    /// 依赖环境状态的判据不是判据，所以烤色时机必须和解析外观一样显式固定。
    private func baked(_ make: () -> NSColor, at name: NSAppearance.Name) -> NSColor {
        let appearance = NSAppearance(named: name)!
        var result = NSColor.black
        appearance.performAsCurrentDrawingAppearance { result = make() }
        return result
    }

    func testSemanticColorsAreNotBakedByWithAlphaComponent() {
        // 这条是**根因探针**：先证明"在亮色下 withAlphaComponent、到暗色里解析"会得到黑色，
        // 再证明我们用的颜色没有这个毛病。没有前半段，后半段只是断言一个巧合。
        let bakedInLight = baked({ NSColor.labelColor.withAlphaComponent(0.8) }, at: .aqua)
        let dark = resolve(bakedInLight, under: .darkAqua)
        XCTAssertEqual(dark.a, 0.8, accuracy: 0.01, "alpha 没留住，前提变了")
        XCTAssertEqual(dark.r, 0, accuracy: 0.01,
                       "前提变了：withAlphaComponent 不再按创建时外观烤色，这条守卫要改写")
        XCTAssertEqual(dark.g, 0, accuracy: 0.01)
        XCTAssertEqual(dark.b, 0, accuracy: 0.01)
        // 阳性对照：同一句代码在暗色下创建就得到白的 —— 决定结果的是**创建时机**而不是解析时机。
        let bakedInDark = baked({ NSColor.labelColor.withAlphaComponent(0.8) }, at: .darkAqua)
        XCTAssertGreaterThan(resolve(bakedInDark, under: .darkAqua).r, 0.9)
        // 而真正的动态色在暗色下始终是白的。
        XCTAssertGreaterThan(resolve(.labelColor, under: .darkAqua).r, 0.9)

        // 我们用的每一档文字色都必须是动态的：暗色下不能比背景还暗。
        for (label, color) in [("正文", MarkdownPresentation.bodyColor),
                               ("引用", MarkdownPresentation.quoteColor),
                               ("标题", MarkdownPresentation.headingColor),
                               ("标记", MarkdownPresentation.markerColor),
                               ("链接", MarkdownPresentation.linkColor)] {
            let inDark = resolve(color, under: .darkAqua)
            XCTAssertGreaterThan(inDark.r + inDark.g + inDark.b, 1.2,
                                 "\(label) 在暗色下解析成近黑：\(inDark) —— 深色底上会看不见")
        }
    }

    func testSearchHighlightColourFollowsTheAppearanceInsteadOfBeingBaked() {
        let light = resolve(DetailTypography.highlightColor, under: .aqua)
        let dark = resolve(DetailTypography.highlightColor, under: .darkAqua)
        XCTAssertEqual(light.a, 0.32, accuracy: 0.001)
        XCTAssertEqual(dark.a, 0.32, accuracy: 0.001)
        // 黄 = 红高、绿高、蓝低。两种外观都得是黄的，而不是被烤成 aqua 那一份后压在深底上。
        for (label, color) in [("亮", light), ("暗", dark)] {
            XCTAssertGreaterThan(color.r, 0.8, "\(label) 色下命中底不是红的：\(color)")
            XCTAssertGreaterThan(color.g, 0.6, "\(label) 色下命中底不是绿的：\(color)")
            XCTAssertLessThan(color.b, 0.35, "\(label) 色下命中底太偏蓝，不像系统黄：\(color)")
        }
        // 阳性对照：把同一份颜色换成"在亮色下烤好"的写法，暗色下必须解析成**不同**的值，
        // 否则这条用例其实什么都没测。
        let bakedDark = resolve(baked({ NSColor.systemYellow.withAlphaComponent(0.32) }, at: .aqua),
                                under: .darkAqua)
        let differs = abs(bakedDark.g - dark.g) > 0.01 || abs(bakedDark.b - dark.b) > 0.01
        XCTAssertTrue(differs, "烤色与动态色在暗色下解析成同一个值 ⇒ 这条守卫没有判别力")
        print("COLOR_PROBE dynamic_dark=(\(dark.r),\(dark.g),\(dark.b)) baked_dark=(\(bakedDark.r),\(bakedDark.g),\(bakedDark.b))")
    }

    func testMarkdownPresentationDoesNotBakeDynamicColours() throws {
        // 会红的规矩，而不是靠人记得：这一族的缺陷都长同一个样子 ——
        // `某个语义色.withAlphaComponent(...)` 被写成静态常量。
        let presentation = codeOnly(try productSource(named: "Utilities/MarkdownPresentation.swift"))
        XCTAssertFalse(presentation.contains("withAlphaComponent"),
                       "呈现层出现了 `withAlphaComponent`：语义色会被烤成固定 RGB，暗色下会看不见")
        let typography = try productSource(named: "Utilities/DetailTypography.swift")
        XCTAssertTrue(typography.contains("NSColor(name: nil)"),
                      "命中底色不再是按外观解析的动态色（U-4 的黄色在暗色下会被烤成 aqua 那一份）")
    }

    // MARK: - ③ 接线锚点：判"确实路由到渲染器"

    func testDetailViewRoutesMarkdownToTheRendererAndBack() throws {
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("MarkdownRenderingAffordance.renders(text: text, in: markdownMode)"),
                      "文本条目没有走判定层，等于开关形同虚设")
        XCTAssertTrue(detail.contains("ChineseSelectableAttributedTextView(source: text,"),
                      "渲染分支根本没建富文本视图 —— 判定对了、视图没换，缺陷还在")
        XCTAssertTrue(detail.contains("ChineseSelectableTextView("),
                      "「原文」那条路被删了：渲染器一旦出错用户没有退路")
        // R211 之后这颗调用变成两行（多了 `freezeLoadingForCapture:`），整行字面量匹配不到 ⇒
        // 这条守卫在 runner 上红过一轮（run 39258514435，`Executed 886 tests / 1 failure`）。
        // 改成「折行也算数」的形状匹配，并额外钉住新参数接的是**属性**而不是死值
        // （写死 true 会让产品永远停在骨架，而那正是这张帧需要的、产品不该有的状态）。
        let fileCall = detail.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }
            .joined(separator: " ")
        XCTAssertTrue(fileCall.contains("DetailFileView(url: url, thumbnail: entry.thumbnail, markdownMode: markdownMode, freezeLoadingForCapture: freezeLoadingForCapture)"),
                      "文件预览没接到当前模式，或没把冻结开关原样传下去")
        XCTAssertTrue(fileCall.contains("markdownMode: markdownMode"),
                      "「原文 / 渲染」那颗开关没接到文件预览上")
        XCTAssertTrue(detail.contains("MultiFileDetailView(urls: urls, markdownMode: markdownMode)"),
                      "多文件里展开的 Markdown 不受开关控制")
        XCTAssertTrue(detail.contains("MarkdownModeButton(title: MarkdownPreviewMode.controlTitle(for: markdownMode))"),
                      "头部那颗控件没接上标题")
        XCTAssertTrue(detail.contains("markdownMode = markdownMode.toggled()"),
                      "控件的动作没走 toggled()：标题与翻转方向会各说各话")
        XCTAssertTrue(detail.contains("helpLabel(MarkdownPreviewMode.controlHelp)"),
                      "控件只有视觉没有无障碍标签（R-54 那一族的规矩）")
        // R32：同 Round3 那条 —— 渲染分支走的是 `.detailReadableColumn()`，
        // 上限在那一处定义里。这里判"渲染分支自己有没有接上"，用调用点计数而不是字符串存在性。
        let renderedWired = detail.components(separatedBy: ".detailReadableColumn()").count - 1
        XCTAssertGreaterThanOrEqual(renderedWired, 2,
                      "详情区只接了 \(renderedWired) 处可读列 ⇒ 渲染分支或原文分支有一个不限宽了"
                      + "（U-4 的行长问题会跟着回来，而且两种看法的左轴会不一样）")
    }

    func testFilePreviewRoutesMarkdownFilesToTheRenderer() throws {
        let views = codeOnly(try productSource(named: "Views/DetailPreviewViews.swift"))
        XCTAssertTrue(views.contains("MarkdownRenderingAffordance.renders(url: url, in: markdownMode)"),
                      "Markdown 文件没走判定层")
        XCTAssertTrue(views.contains("ChineseSelectableAttributedTextView(source: content)"),
                      "文件预览的渲染分支没建富文本视图")
        XCTAssertTrue(views.contains("ChineseSelectableTextView(text: content, font: .monospacedSystemFont"),
                      "非 Markdown 文本文件的等宽预览被顺手改掉了")
    }

    func testBothReadOnlyBodiesShareOneAssembly() throws {
        let textView = codeOnly(try productSource(named: "Views/ChineseTextContextMenu.swift"))
        XCTAssertTrue(textView.contains("func updateMarkdown(source: String, highlightQuery: String) -> Int"),
                      "富文本正文没有唯一写入口")
        XCTAssertTrue(textView.contains("if source != appliedMarkdownSource, let textStorage"),
                      "没有「源码变了才重建」这个条件 —— 搜索框每敲一个字都会重排整篇")
        XCTAssertTrue(textView.contains("readOnlyBodyScrollView(font: nil)"),
                      "富文本正文没共用装配，列宽/内缩/右键菜单会和纯文本那条路分叉")
        XCTAssertTrue(textView.contains("textView.updateMarkdown(source: source, highlightQuery: highlightQuery)"),
                      "updateNSView 没接到渲染入口")
        XCTAssertTrue(textView.contains("appliedMarkdownSource = nil"),
                      "纯文本入口没作废渲染缓存：同一实例先渲染过 Markdown 会留着属性串")
        // 装配只允许有一份。这个数字是**单调量**：将来有人复制粘贴第二套配置，这里立刻红。
        XCTAssertEqual(textView.components(separatedBy: "widthTracksTextView = true").count - 1, 1,
                      "只读正文的容器配置出现了第二份，两处会慢慢分叉")
        XCTAssertEqual(textView.components(separatedBy: "hasHorizontalScroller = false").count - 1, 1,
                      "滚动条配置出现了第二份")
    }

    // MARK: - 复杂度上限（这条是"敢把渲染放主线程"的前提）

    func testAdversarialUnclosedMarkupDoesNotQuadraticallyBlowUp() throws {
        // 未闭合的 `*` 每个都要向前找闭栏。没有 `maximumInlineMarkupDistance` 时
        // 这一段是 O(n²)：40000 个字符 = 十几亿次比较，主线程直接冻住。
        // `*a ` 而不是 `* a `：开栏右邻必须是**非空白**才算开栏，
        // 用 `* a` 的话每个星号都在第一道判定上被驳回，扫都不扫，这条用例就没有判别力。
        let adversarial = String(repeating: "*a ", count: 13_400)
        XCTAssertGreaterThan(adversarial.count, 40_000, "夹具前提：要跑到 40000 的上限")
        let start = Date()
        let document = MarkdownParser.parse(adversarial)
        let rendered = MarkdownPresentation.attributedString(for: document)
        let elapsed = Date().timeIntervalSince(start)
        print("MARKDOWN_PERF adversarial_40k_ms=\(Int(elapsed * 1000)) runs=\(document.blocks.first?.runs.count ?? 0)")
        XCTAssertLessThan(elapsed, 2.0, "解析+构建 40000 个未闭合标记超过 2 秒：主线程会被冻住")
        XCTAssertTrue(rendered.string.contains("a"))

        let dense = String(repeating: "字", count: MarkdownParsingPolicy.maximumRenderedCharacters)
        let denseStart = Date()
        let denseRendered = MarkdownPresentation.attributedString(for: MarkdownParser.parse(dense))
        let denseElapsed = Date().timeIntervalSince(denseStart)
        print("MARKDOWN_PERF dense_40k_ms=\(Int(denseElapsed * 1000)) length=\(denseRendered.length)")
        XCTAssertLessThan(denseElapsed, 2.0)

        let richStart = Date()
        _ = MarkdownPresentation.attributedString(for: MarkdownParser.parse(sample))
        print("MARKDOWN_PERF real_sample_ms=\(Int(Date().timeIntervalSince(richStart) * 1000))")
    }

    // MARK: - 夹具

    private func writeTemporaryFile(named name: String, contents: String) throws -> URL {
        let directory = temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        addTeardownBlock {
            try? FileManager.default.removeItem(at: directory)
        }
        let url = directory.appendingPathComponent(name)
        try contents.data(using: .utf8)!.write(to: url)
        return url
    }

    private func attributes(in storage: NSAttributedString, containing needle: String)
        -> [NSAttributedString.Key: Any]? {
        let range = (storage.string as NSString).range(of: needle)
        guard range.location != NSNotFound else { return nil }
        return storage.attributes(at: range.location, effectiveRange: nil)
    }

    private func isItalic(_ storage: NSAttributedString, containing needle: String) throws -> Bool {
        let attributes = try XCTUnwrap(self.attributes(in: storage, containing: needle),
                                       "渲染结果里找不到「\(needle)」")
        let font = try XCTUnwrap(attributes[.font] as? NSFont)
        return font.fontDescriptor.symbolicTraits.contains(.italic)
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "Round4MarkdownTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
