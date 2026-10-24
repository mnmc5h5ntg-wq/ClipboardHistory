import AppKit
import Foundation

/// 详情正文"要不要给渲染入口、给哪一个"的**唯一**决定处（R335）。
///
/// 为什么要单独一处而不是让 `MarkdownRenderingAffordance` 与视图各问各的：
/// 这条判据管的是同一件事的两半 —— "那颗控件该不该出现" 与 "点下去画的是哪一种"。
/// 分成两处判就会漂成"控件在、点了没变化"或"渲染了、却没有退回原文的入口"，
/// 而这两种漂在帧上都长得像正常界面（R14 那一族：两半必须来自同一个源）。
enum DetailRenderPolicy {

    /// 文本条目：载荷优先，其次"这份文本自己声明是 HTML 文档"，最后才是 Markdown 猜测。
    /// 顺序的每一个箭头都是一条会红的判据（`HtmlPreviewTests.testThePrecedenceIsTheWholePoint`）。
    static func decide(text: String, htmlPayload: Data?) -> DetailRenderDecision {
        let payloadBytes = htmlPayload?.count ?? 0
        if HtmlPreviewPolicy.wantsHtmlRendering(text: text, htmlPayloadBytes: payloadBytes) {
            let source = HtmlPreviewPolicy.renderSource(text: text, htmlPayload: htmlPayload)
            // 超预算 ⇒ **整条入口都不给**，而不是"给了但点了没反应"。
            // 这里没有第三种状态是有理由的：一个"渲染态与原文态逐字节相同"的切换控件
            // 就是在承诺一个做不到的动作（同一颗理由见 `MarkdownRenderingAffordance` 里"文件已不在"那一支）。
            if HtmlPreviewPolicy.declinesForSize(source) { return .plain }
            return .rendered(.html, source: source)
        }
        if MarkdownParsingPolicy.offersRendering(forText: text) {
            return .rendered(.markdown, source: text)
        }
        return .plain
    }

    /// 文本文件：扩展名就是作者的意图（Markdown 那一路早就按这条规矩办，HTML 沿用）。
    static func decide(fileContent: String, url: URL) -> DetailRenderDecision {
        if HtmlPreviewPolicy.isHtmlFile(url) {
            if HtmlPreviewPolicy.declinesForSize(fileContent) { return .plain }
            return .rendered(.html, source: fileContent)
        }
        if MarkdownParsingPolicy.isMarkdownFile(url) {
            return .rendered(.markdown, source: fileContent)
        }
        return .plain
    }

    /// 只问"这一条**可能**用哪一种渲染器"，不要字节 —— 头部那颗控件的提示语必须在文件
    /// 被异步读进来**之前**就说对，而 `decide(fileContent:url:)` 要等字节。
    /// 返回集合（不是单个）是因为"多文件"那一路真的会同时装着两种：
    /// 一条复制了 `说明.md` + `页面.html` 的记录，展开的每一行都走同一个切换控件。
    static func renderer(forFile url: URL) -> DetailRenderer? {
        if HtmlPreviewPolicy.isHtmlFile(url) { return .html }
        if MarkdownParsingPolicy.isMarkdownFile(url) { return .markdown }
        return nil
    }

    /// 这条记录**能**渲染成哪几种（空集 = 没有渲染入口）。
    ///
    /// 为什么它是唯一的出处：`MarkdownRenderingAffordance.offers(for:)` 以前自己判一遍
    /// "有没有两种看法"，视图又判一遍"点下去画哪一种"，于是 R335 第一版留下了一个假话 ——
    /// `.html` **文件**条目的提示语写着"与 Markdown 原文之间切换"（`.helpLabel` 会把它
    /// 喂给 VoiceOver 念出来）。两半必须来自同一处，这一族叫**同一件事两处判**。
    ///
    /// `exists` 是注入进来的（沿用 `offers(for:exists:)` 那条理由）：文件不在了就没有
    /// "两种看法"，而把 `FileManager` 直接调进来会让这条判定在判据里依赖真实磁盘。
    static func renderers(for content: ClipboardEntryContent, htmlPayload: Data?,
                          exists: (URL) -> Bool) -> Set<DetailRenderer> {
        switch content {
        case .text(let text):
            // 文本那一路仍然走 `decide`：超预算就不给入口，那是**同一个决定**的一半，
            // 不许在这里另判一次。
            return decide(text: text, htmlPayload: htmlPayload).renderer.map { [$0] } ?? []
        case .image:
            return []
        case .file(let url):
            guard exists(url) else { return [] }
            return renderer(forFile: url).map { [$0] } ?? []
        case .files(let urls):
            var out = Set<DetailRenderer>()
            for url in urls where exists(url) {
                if let kind = renderer(forFile: url) { out.insert(kind) }
            }
            return out
        }
    }

    static func renderers(for content: ClipboardEntryContent, htmlPayload: Data? = nil) -> Set<DetailRenderer> {
        renderers(for: content, htmlPayload: htmlPayload) { FileManager.default.fileExists(atPath: $0.path) }
    }

    /// 那颗切换控件的提示语。**唯一**的措辞出处。
    ///
    /// 三种回答：只有一种渲染器 ⇒ 说那一种的名字；两种都有 ⇒ 说中性那句
    /// （混着 `.md` 与 `.html` 的一条记录里，说任何一种都对另一半撒谎）；没有 ⇒ 退回 Markdown 那句
    /// （调用点此时根本不会摆这颗控件，这里只是不让它拼出半句话）。
    static func controlHelp(for content: ClipboardEntryContent, htmlPayload: Data?,
                            exists: (URL) -> Bool) -> String {
        let kinds = renderers(for: content, htmlPayload: htmlPayload, exists: exists)
        if kinds.count == 1, let only = kinds.first {
            return only.controlHelp(htmlPayload: htmlPayloadHasBytes(htmlPayload))
        }
        return kinds.isEmpty ? MarkdownPreviewMode.controlHelp : mixedControlHelp
    }

    static func controlHelp(for content: ClipboardEntryContent, htmlPayload: Data? = nil) -> String {
        controlHelp(for: content, htmlPayload: htmlPayload) { FileManager.default.fileExists(atPath: $0.path) }
    }

    /// 混排那一句：不点名任何格式，因此不会说错话。
    static let mixedControlHelp = "在渲染结果与原文之间切换"

    /// 载荷"有没有"这一问只有一处答案：非 nil **且**非空。
    /// 空 Data 不是声明（`HtmlPreviewPolicy` 里那条 `testEmptyPayloadIsNotAPayload` 钉的就是它），
    /// 而提示语如果说"渲染走的是这条记录自带的 HTML 表示"，依据必须与判定用的是同一个谓词。
    static func htmlPayloadHasBytes(_ htmlPayload: Data?) -> Bool {
        (htmlPayload?.isEmpty == false)
    }
}

/// 渲染器身份。**只有两种**，而且它们画进同一块视图 ——
/// 所以 `DetailPreviewKind` 不新增 case（它的粒度是"整块子视图换没换"，见那个枚举自己的注释）。
enum DetailRenderer: Equatable, Hashable, Sendable {
    case markdown
    case html

    /// 缓存键的前缀。刻意**不是**空串对 markdown：那样"没有渲染器"与"Markdown 渲染器"
    /// 在键上同形，第一版实现就是这么写的，于是切换渲染器仍然会命中旧键（判据抓到了它）。
    var cacheKeyPrefix: String {
        switch self {
        case .markdown: return "md\u{241F}"
        case .html: return "ht\u{241F}"
        }
    }

    /// 头部那颗控件的提示语。分开写是因为一句"在渲染结果与 Markdown 原文之间切换"
    /// 挂在 HTML 条目上就是**假话** —— 而 `.helpLabel` 同时喂 `.help` 与 `accessibilityLabel`，
    /// 说错的那一句会被 VoiceOver 念给用户听。
    ///
    /// `htmlPayload` 这一半在 R335 第一版是**死的**：`DetailRenderer` 拿不到条目，
    /// 于是 `HtmlPreviewPolicy.controlHelp(hasPayload:)` 那两支里只有一支被走到 ——
    /// "函数有两个分支而调用点只喂一个常量"这种形状，判据看不见、帧也看不见，
    /// 只有把参数从决定里带出来才接得上（刀 M983 钉的就是"调用点退回常量"那种坏法）。
    func controlHelp(htmlPayload: Bool) -> String {
        switch self {
        case .markdown: return MarkdownPreviewMode.controlHelp
        case .html: return HtmlPreviewPolicy.controlHelp(hasPayload: htmlPayload)
        }
    }
}

/// 决定本身。`source` 是**喂给渲染器的那一份字节**（载荷优先时它不是 `entry.content` 里的文本）。
///
/// 这里刻意**没有** `offersRendering` 那一格：R335 第一版它被视图拿去当"有没有两种看法"的答案，
/// 而它对文件条目只能返回一个假字节（`source: ""`）—— 于是那一格既是第二个权威，又是错的形状。
/// 现在"有没有入口"只有一个问法：`DetailRenderPolicy.renderers(for:htmlPayload:)` 空不空。
enum DetailRenderDecision: Equatable, Sendable {
    case plain
    case rendered(DetailRenderer, source: String)

    var renderer: DetailRenderer? {
        if case .rendered(let kind, _) = self { return kind }
        return nil
    }

    /// 渲染态要的**两样东西**：哪一种渲染器 + 喂给它的那一份字节（HTML 已消毒）。
    /// 单独一个函数是为了让"渲染器与源文本各拿各的"这种拆法在调用点写不出来。
    func resolved() -> (DetailRenderer, String)? {
        guard let renderer = renderer, let source = renderedSource() else { return nil }
        return (renderer, source)
    }

    /// 渲染态真正要画的那一份源文本（消毒之后）。`.plain` 时返回 nil。
    func renderedSource() -> String? {
        guard case .rendered(let kind, let source) = self else { return nil }
        switch kind {
        case .markdown: return source
        case .html: return HtmlSanitizer.renderableHTML(source)
        }
    }
}

/// HTML → `NSAttributedString`。
///
/// `@MainActor` 是**照抄系统的前提**，不是保守：`NSAttributedString.DocumentType.html`
/// 底下是 WebKit 的文本装载器，Apple 的文档写明这个初始化应在主线程调用。
/// 代价实测（R335 spike，本机现读）：168,916 字节 → 85.0ms（≈0.503ms/KB），
/// 热身后小文档 2.3–5.7ms，**第一次**调用 225.7ms（WebKit 初始化，一次性的）。
/// 预算与上限的推导写在 `HtmlPreviewRenderBudget.maximumBytes` 旁边，并由
/// `HtmlPreviewTests.testTheByteCeilingIsDerivedFromTheMeasuredSlope` 钉住。
@MainActor
enum HtmlRendering {
    /// 解析失败（空串、坏字节）返回 nil ⇒ 调用方退回原文，不画半张页面。
    static func attributedString(_ sanitizedHTML: String) -> NSAttributedString? {
        guard let raw = parse(sanitizedHTML) else { return nil }
        // 两步各钉一把刀（M978 只抹不设 / M980 基准取错），顺序有意义：
        // 字号那一步要按**字符数**加权找基准，抹墨不改文本 ⇒ 先后都不影响结果，
        // 但"先设墨再换字体"会让第二步重建属性时把墨冲掉，所以这里定死"先字号后墨"。
        return applySurfaceInk(fitToBodySize(raw))
    }

    /// WebKit 的那一次解析，**不动墨** —— 单独露出来是为了让判据能问"抹之前有几处烤死的颜色"。
    /// 没有这一颗尺，`applySurfaceInk` 就是一段"看起来在修什么"的代码：改完之后测什么都是零。
    static func parse(_ html: String) -> NSAttributedString? {
        let data = Data(html.utf8)
        guard !data.isEmpty else { return nil }
        let options: [NSAttributedString.DocumentReadingOptionKey: Any] = [
            .documentType: NSAttributedString.DocumentType.html,
            .characterEncoding: String.Encoding.utf8.rawValue,
        ]
        return try? NSAttributedString(data: data, options: options, documentAttributes: nil)
    }

    /// 把"这张页面自己的墨"换成"我们这块表面的墨"（R335 看图腿量出来的缺陷，不是推测）。
    ///
    /// 量到的东西（`/tmp/r335_shots`，暗档 720×520 那一帧）：正文列里有 **8779 颗近纯黑**
    /// （RGB 0,0,0）落在 luma=30 的表面上 ⇒ 对比 **1.26:1**，而同一卷里 Markdown 正文是 12.27:1。
    /// 结构（24pt 标题、列表、下划线链接）全对，人读不到。这一族有名字：
    /// **离屏烤死颜色 ⇒ 暗档看不见**（R29 / R30 侧栏黑字同一族）。
    ///
    /// 为什么只"抹掉"不够（第一版就是这么写的，帧上一个字节都没变）：
    /// `removeAttribute` 之后那段文字**没有颜色属性**，于是画它的是文本视图自己的默认墨，
    /// 而默认墨在这条离屏通道里解析成什么，不是这份代码能担保的。
    /// 所以这里改成**主动设**：每一段有字的正文都钉上一支跟着外观变的墨，
    /// 与 Markdown 那条同一个权威（`MarkdownPresentation.bodyColor = .labelColor`）。
    ///
    /// 三条取舍，各自写清楚（不是一条"顺手"）：
    /// ① **作者指定的固定色不保留**：页面假设自己印在白纸上，而我们已经不给它纸了
    ///    （`drawsBackground = false`，画在 App 表面上）。纸是假话的时候，纸上选的颜色也是假话。
    /// ② **背景色整片去掉**：留着一块 `background:#f0f0f0` 就是在暗档表面开一个比表面亮的洞。
    /// ③ **链接段不给 `.labelColor`**：它得看起来像链接。给 `.linkColor`（同样跟着外观变），
    ///    下划线由 WebKit 排进来的 `.underlineStyle` 保留。
    static func applySurfaceInk(_ attributed: NSAttributedString) -> NSAttributedString {
        let out = NSMutableAttributedString(attributedString: attributed)
        let full = NSRange(location: 0, length: out.length)
        out.removeAttribute(.backgroundColor, range: full)
        out.removeAttribute(.foregroundColor, range: full)
        // 逐段设，而不是整片设：链接与正文要两支不同的墨，而"整片先设正文再改链接"
        // 那种写法会把 `.link` 段落的颜色留成上一次设的那一支 —— 判据抓不到，帧上看得出来。
        // 枚举的是**输入**、写的是**输出**：在同一份串上边枚举边加属性会让段边界在枚举中途挪动，
        // 于是"哪一段拿到哪支墨"变成实现细节而不是代码写的东西。
        var runs: [(range: NSRange, isLink: Bool)] = []
        attributed.enumerateAttribute(.link, in: full) { linkValue, range, _ in
            runs.append((range, linkValue != nil))
        }
        for run in runs {
            out.addAttribute(.foregroundColor,
                             value: run.isLink ? surfaceLinkInk : surfaceBodyInk,
                             range: run.range)
        }
        return out
    }

    /// 正文墨：**与 Markdown 那条同一个权威**，不许在这里另立一支。
    static var surfaceBodyInk: NSColor { MarkdownPresentation.bodyColor }

    /// 按**字符数**加权出现最多的那一号字 —— 也就是"这份页面的正文档"。
    ///
    /// 为什么不用"最小号"或"第一段的字号"：正文在字符数上压倒性地占多数，而标题只占几个字。
    /// 用最小号会把 `<small>`/脚注读成正文，用第一段则把 `<h1>` 读成正文（现读：这一份的
    /// 第一段是 24pt 的标题）。加权众数是这四个候选里唯一"跟着内容走而不跟着顺序走"的那个。
    static func fontBaseSize(_ attributed: NSAttributedString) -> CGFloat {
        let full = NSRange(location: 0, length: attributed.length)
        var weight: [CGFloat: Int] = [:]
        attributed.enumerateAttribute(.font, in: full) { value, range, _ in
            guard let font = value as? NSFont else { return }
            let text = (attributed.string as NSString).substring(with: range)
            let chars = text.trimmingCharacters(in: .whitespacesAndNewlines).count
            guard chars > 0 else { return }
            weight[font.pointSize, default: 0] += chars
        }
        return weight.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
    }

    /// 把整份页面的字号**等比**搬到产品正文那一档（R335 看图腿 + `HTML_FONTS` 读数）。
    ///
    /// 现读：`NSAttributedString(html:)` 给的是 `族=Times 字号=24pt/12pt`，
    /// 而产品的正文是 `.AppleSystemUIFontMonospaced/14pt`（`DetailTypography.bodyFontSize`）。
    /// 于是同一个"渲染"档里两条通道差两号字 —— 用户点一下切换，正文从 12pt 衬线跳到 14pt 等宽，
    /// 而这两种都"看起来像渲染成功了"。这一族有名字：**同一档两种刻度**。
    ///
    /// 为什么**只搬字号、不搬字族**：字族是这份页面自己的排版意图（作者写了 serif 就用 serif，
    /// 没写就是浏览器的默认衬线），把它换成产品的等宽就不是"渲染这份 HTML"了；
    /// 而字号那一档是**可读性与层级一致性**的问题 —— 正文小两号在 720pt 的面板里就是要眯眼。
    /// 这个取舍登记进 BACKLOG，不写成注释就算没记过。
    ///
    /// 因子是**推出来的**（目标 ÷ 现读基准），不是抄的常数；基准读不到（0）时原样返回，
    /// 因为"猜一个 12"会把这一格变成自证（判据测的是"正文档 == 14"，猜出来的 14 什么都没说）。
    static func fitToBodySize(_ attributed: NSAttributedString) -> NSAttributedString {
        let base = fontBaseSize(attributed)
        let target = DetailTypography.bodyFontSize
        guard base > 0, abs(base - target) > 0.001 else { return attributed }
        let factor = target / base
        let out = NSMutableAttributedString(attributedString: attributed)
        let full = NSRange(location: 0, length: out.length)
        var runs: [(NSRange, NSFont)] = []
        attributed.enumerateAttribute(.font, in: full) { value, range, _ in
            if let font = value as? NSFont { runs.append((range, font)) }
        }
        for (range, font) in runs {
            let scaled = NSFont(descriptor: font.fontDescriptor, size: font.pointSize * factor)
                ?? font
            out.addAttribute(.font, value: scaled, range: range)
        }
        return out
    }

    /// 链接墨。刻意不是 `NSColor.blue`：固定蓝在暗档上是 3.0 上下，而这正是本轮要修的那一类数。
    static var surfaceLinkInk: NSColor { .linkColor }

    // MARK: - 判据用的两颗尺（产品侧导出，判据不许自己另抄一份 RGB 比较）

    /// 一支颜色在亮暗两档**解析成同一个 RGB** ⇒ 它不跟外观走（烤死的）。
    ///
    /// 为什么用"两档解析是否相同"而不是"它是不是 `NSColor(catalog…)` 之类"：
    /// 后者是在猜实现细节，而这条判据要问的只有一件事 —— **换到暗档它还看得见吗**。
    /// 解析失败（拿不到 RGB 分量）也答"是烤死的"：担保不了的外观就当作担保不了。
    static func resolvesIdenticallyInBothAppearances(_ color: NSColor) -> Bool {
        guard let light = components(color, appearanceName: .aqua),
              let dark = components(color, appearanceName: .darkAqua) else { return true }
        return light == dark
    }

    /// 一支颜色在指定外观下的 RGBA 分量（0…255 整数，便于读数与比较）。
    static func components(_ color: NSColor, appearanceName: NSAppearance.Name) -> [Int]? {
        guard let appearance = NSAppearance(named: appearanceName) else { return nil }
        var out: [Int]?
        appearance.performAsCurrentDrawingAppearance {
            if let rgb = color.usingColorSpace(.deviceRGB) {
                out = [rgb.redComponent, rgb.greenComponent, rgb.blueComponent, rgb.alphaComponent]
                    .map { Int(($0 * 255).rounded()) }
            }
        }
        return out
    }
}
