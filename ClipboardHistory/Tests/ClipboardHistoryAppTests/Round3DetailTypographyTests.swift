import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 §4 U-4（详情排版：行长 / meta / 命中高亮）的判据。
///
/// 分成两层，按 `AGENTS.md` 的定义完成标准：
/// - 纯函数层：命中定位与列宽推导（这两个是最容易被"顺手调一下"改坏又看不出来的）；
/// - 组件层：真的建一个 `ChineseSelectableNSTextView`，让高亮走过它唯一的生产入口 `updateBody`，
///   然后从 `NSLayoutManager` 把临时属性读回来 —— 这样"高亮打上了 / 清干净了 / 文本没被改"
///   三件事是量出来的，不是看帧看出来的。帧只用来复核对齐与底色对比度。
@MainActor
final class Round3DetailTypographyTests: XCTestCase {

    // MARK: - 命中定位（UTF-16 偏移）

    private func spans(_ text: String, _ query: String) -> [MatchHighlighting.Span] {
        MatchHighlighting.spans(in: text, query: query)
    }

    func testSpansLocateEveryOccurrenceLeftmostFirst() {
        XCTAssertEqual(spans("abc def abc", "abc"),
                       [.init(location: 0, length: 3), .init(location: 8, length: 3)])
    }

    func testEmptyQueryMatchesNothing() {
        XCTAssertTrue(spans("随便什么正文", "").isEmpty,
                      "空查询退化成全文命中，等于整段正文一片黄")
        XCTAssertTrue(spans("", "abc").isEmpty)
    }

    func testQueryLongerThanTextMatchesNothing() {
        XCTAssertTrue(spans("ab", "abcdef").isEmpty)
    }

    func testSpansIgnoreCaseAndDiacritics() {
        // 侧栏过滤走 `localizedCaseInsensitiveContains`，高亮必须同一套语义，
        // 否则会出现"这条被搜出来了、正文里一处都不亮"。
                // 偏移是数出来的：`Mixed Case ` 占 11 个码元（5+1+4+1），TEXT 从 11 起。
        // （这里连错过一次写成 12 —— 手数字符数不可靠，所以每个用例都把期望写成一个显式区间。）
        XCTAssertEqual(spans("Mixed Case TEXT", "text"), [.init(location: 11, length: 4)])
        XCTAssertEqual(spans("café au lait", "CAFE"), [.init(location: 0, length: 4)])
    }

    func testSpansDoNotOverlapAndAdvancePastEachHit() {
        // "aaaa" 查 "aa"：左起优先，得两段而不是三段（重叠的两段会把颜色加回同一个字符上）。
        XCTAssertEqual(spans("aaaa", "aa"), [.init(location: 0, length: 2), .init(location: 2, length: 2)])
    }

    func testSpansUseUTF16OffsetsForSurrogatePairs() {
        // 这条是这个函数存在的理由。emoji 在 UTF-16 里是代理对（2 个码元），
        // 用 Character 边界算偏移就会和 NSTextStorage 的下标分叉 ——
        // 分叉的后果不是偏一点，而是颜色落在错的字符上、甚至切进半个 emoji。
        let text = "🍎x🍎"
        XCTAssertEqual(spans(text, "x"), [.init(location: 2, length: 1)])
        let emoji = spans(text, "🍎")
        XCTAssertEqual(emoji.count, 2)
        XCTAssertEqual(emoji.first, .init(location: 0, length: 2))
                // 第二个 🍎 在 3..5，不是 4..6：每个 emoji 占 2 个码元，中间的 x 占 1 个。
        XCTAssertEqual(emoji.last, .init(location: 3, length: 2))
        // 偏移必须能直接喂给 layoutManager 而不越界
        let storage = text as NSString
        for span in emoji {
            XCTAssertLessThanOrEqual(NSMaxRange(NSRange(location: span.location, length: span.length)),
                                     storage.length)
        }
    }

    func testSpansAreCappedSoAOneCharacterQueryCannotFreezeTheMainThread() {
        let long = String(repeating: "a", count: 20_000)
        let result = spans(long, "a")
        XCTAssertEqual(result.count, MatchHighlighting.maximumSpanCount,
                       "上限没起作用：2 万个命中会被逐个加上临时属性")
        XCTAssertTrue(result.allSatisfy { $0.length == 1 })
    }

    func testSegmentsSplitTextIntoHitAndPlainRuns() {
        let pieces = MatchHighlighting.segments(in: "找 我 找", query: "找")
        XCTAssertEqual(pieces.map { $0.0 } , ["找", " 我 ", "找"])
        XCTAssertEqual(pieces.map { $0.isMatch }, [true, false, true])
        // 空查询不许返回空数组，要返回"整段都不是命中"
        // 带标签的元组数组不能直接进 `XCTAssertEqual`（元组不合 Equatable），逐字段比。
        let whole = MatchHighlighting.segments(in: "abc", query: "")
        XCTAssertEqual(whole.count, 1)
        XCTAssertEqual(whole.first?.0, "abc")
        XCTAssertEqual(whole.first?.1, false)
    }

    // MARK: - 可读列宽

    func testColumnWidthIsDerivedFromTheFontNotCopiedAsAPixelConstant() {
        let advance = DetailTypography.advance(of: DetailTypography.bodyFont)
        XCTAssertGreaterThan(advance, 0, "推进量测不出来 —— 列宽会退化成 gutter*2")
        let width = DetailTypography.columnWidth(glyphAdvance: advance)
        XCTAssertEqual(width, DetailTypography.containerGutter * 2 + advance * CGFloat(DetailTypography.maximumCharactersPerLine))
        // 审计给的参照是"720pt 时 640pt 左右"；这里必须落在同一个量级，
        // 而不是我随手挑的另一个数。
        XCTAssertGreaterThan(width, 480)
        XCTAssertLessThan(width, 700)
    }

    func testColumnWidthNeverExceedsTheContainer() {
        XCTAssertEqual(DetailTypography.columnWidth(containerWidth: 300, glyphAdvance: 9), 300,
                       "窄窗口里列宽反过来把窗口撑宽了")
        XCTAssertLessThan(DetailTypography.columnWidth(containerWidth: 1_000, glyphAdvance: 9), 1_000)
    }

    func testLargerFontProducesAWiderColumnAtTheSameCharacterLimit() {
        // 行长上限是"68 个字符"，所以字号变大列宽必须跟着变大 ——
        // 这条断言存在的意义就是防止有人把列宽写成死常数。
        let small = DetailTypography.columnWidth(
            glyphAdvance: DetailTypography.advance(of: .monospacedSystemFont(ofSize: 11, weight: .regular)))
        let large = DetailTypography.columnWidth(
            glyphAdvance: DetailTypography.advance(of: .monospacedSystemFont(ofSize: 17, weight: .regular)))
        XCTAssertGreaterThan(large, small)
    }

    func testMetaTextIsOneLineAndCarriesTheSourceApp() {
        let withApp = DetailTypography.metaText(copiedAt: "10-10 14:32", size: "1.2 KB", sourceAppName: "Safari")
        XCTAssertFalse(withApp.contains("\n"), "meta 必须是单行")
        XCTAssertTrue(withApp.contains("10-10 14:32 复制"))
        XCTAssertTrue(withApp.contains("1.2 KB"))
        XCTAssertTrue(withApp.contains("来自 Safari"), "来源 App 要能在详情里看到（B-2 已经持久化了它）")
        let withoutApp = DetailTypography.metaText(copiedAt: "10-10 14:32", size: "1.2 KB", sourceAppName: nil)
        XCTAssertFalse(withoutApp.contains("来自"), "读不到来源时不许写「来自 (unknown)」这种话")
        let emptyApp = DetailTypography.metaText(copiedAt: "t", size: "s", sourceAppName: "")
        XCTAssertFalse(emptyApp.hasSuffix("·"), "空来源不该留下一个孤零零的分隔符：\(emptyApp)")
    }

    // MARK: - 组件层：高亮真的打上了、能清掉、不改文本

    private func makeTextView() -> ChineseSelectableNSTextView {
        ChineseSelectableNSTextView()
    }

    private func backgroundAttribute(_ view: ChineseSelectableNSTextView, at index: Int) -> Any? {
        guard let layoutManager = view.layoutManager else { return nil }
        return layoutManager.temporaryAttributes(atCharacterIndex: index,
                                                 effectiveRange: nil)[.backgroundColor]
    }

    func testHighlightMarksHitsAndLeavesPlainCharactersUnmarked() {
        let view = makeTextView()
        let marked = view.updateBody(text: "剪贴板 clipboard 历史", font: DetailTypography.bodyFont, highlightQuery: "CLIP")
        XCTAssertEqual(marked, 1, "「clipboard」里那一个命中没标出来（查询用大写，判的是大小写不敏感）")
        XCTAssertNotNil(backgroundAttribute(view, at: 4), "'clipboard' 的 c 没有底色")
        XCTAssertNotNil(backgroundAttribute(view, at: 7), "命中段中间的字没底色：一段里只涂了首字")
        XCTAssertNil(backgroundAttribute(view, at: 0), "非命中字符也被涂色了")
        XCTAssertNil(backgroundAttribute(view, at: 9), "命中段结束之后还留着底色（长度算错了）")
    }

    func testHighlightDoesNotAlterTheTextItself() {
        let view = makeTextView()
        let text = "第一行\n第二行 clipboard"
        _ = view.updateBody(text: text, font: DetailTypography.bodyFont, highlightQuery: "第二")
        XCTAssertEqual(view.string, text,
                       "命中高亮改动了字符串本体 —— 用户复制到的就不再是原文")
        XCTAssertFalse(view.isRichText, "为了高亮把只读区改成富文本，等于换掉了它的复制语义")
    }

    func testHighlightIsClearedWhenTheQueryChanges() {
        let view = makeTextView()
        _ = view.updateBody(text: "aaa bbb", font: DetailTypography.bodyFont, highlightQuery: "aaa")
        XCTAssertNotNil(backgroundAttribute(view, at: 0))
        _ = view.updateBody(text: "aaa bbb", font: DetailTypography.bodyFont, highlightQuery: "bbb")
        XCTAssertNil(backgroundAttribute(view, at: 0),
                     "换查询词时旧的命中没清：黄块会停在不含搜索词的位置上")
        XCTAssertNotNil(backgroundAttribute(view, at: 4))
        _ = view.updateBody(text: "aaa bbb", font: DetailTypography.bodyFont, highlightQuery: "")
        XCTAssertNil(backgroundAttribute(view, at: 4), "查询清空后仍有残留底色")
    }

    func testHighlightSurvivesAnEntrySwitch() {
        // 切换选中条目时文本会被整体换掉。`string` 一赋值旧临时属性就跟着字形消失，
        // 所以顺序（先设文本再打高亮）是判据，不是风格问题。
        let view = makeTextView()
        _ = view.updateBody(text: "第一条 clip", font: DetailTypography.bodyFont, highlightQuery: "clip")
        XCTAssertNotNil(backgroundAttribute(view, at: 4))
        _ = view.updateBody(text: "第二条 clip clip", font: DetailTypography.bodyFont, highlightQuery: "clip")
        XCTAssertEqual(view.string, "第二条 clip clip")
        XCTAssertNotNil(backgroundAttribute(view, at: 4))
        XCTAssertNotNil(backgroundAttribute(view, at: 9), "第二个命中没打上")
        XCTAssertNil(backgroundAttribute(view, at: 0))
    }

    // MARK: - 接线守卫（判使用处，不判名字）

    func testDetailViewIsWiredToTheMeasureAndTheHighlight() throws {
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("highlightQuery: historyStore.searchText"),
                      "详情正文没把当前搜索词交给高亮")
        XCTAssertTrue(detail.contains("maxWidth: DetailTypography.columnWidth()"),
                      "正文列宽没有限制（U-4 的行长问题仍在）")
        XCTAssertFalse(detail.contains("VStack(alignment: .center"),
                       "meta 又变回两行居中了")
        XCTAssertTrue(detail.contains("lineLimit(1)"), "meta 允许换行了")

        let textView = codeOnly(try productSource(named: "Views/ChineseTextContextMenu.swift"))
        XCTAssertTrue(textView.contains("textContainer?.widthTracksTextView = true"),
                      "文本容器还在跟着无限宽走，横向滚动条去掉后长行会被裁掉")
        XCTAssertFalse(textView.contains("hasHorizontalScroller = true"),
                      "横向滚动条又回来了：行长不受限的老问题会跟着回来")
        XCTAssertTrue(textView.contains("removeTemporaryAttribute"),
                      "换条目/换查询时不清旧命中 —— 黄块会停在错的地方")
        XCTAssertTrue(textView.contains("isHorizontallyResizable = false"),
                      "文本视图仍可横向撑宽，列宽限制形同虚设")
    }

    func testGutterConstantIsTheSameOnBothSidesOfTheAlignment() throws {
        // meta 与正文同左缘靠的是"同一个列宽 + 同一个 gutter"。
        // 两处各写一个 20 的话，改一处就悄悄不对齐了，而帧上要肉眼才看得出。
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("DetailTypography.containerGutter"),
                      "meta 的左内缩没引用同一个常数")
        let textView = codeOnly(try productSource(named: "Views/ChineseTextContextMenu.swift"))
        XCTAssertTrue(textView.contains("NSSize(width: DetailTypography.containerGutter"),
                      "正文容器的内缩没引用同一个常数")
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
        // 刻意不 `throw XCTSkip`：守卫找不到被守卫的文件时应当**红**，而不是安静跳过 ——
        // 一个会跳过的守卫和一个通过的守卫在报表里长得一样，文件改名之后它只会永远跳过。
        throw NSError(domain: "Round3DetailTypographyTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
