import Foundation

/// 详情预览的 **HTML 通道**（R335 / 用户点名："让右侧预览窗口支持 html 预览"）。
///
/// 这一档只做判定与消毒，**不碰视图**：渲染走既有的那条属性串正文
/// （`ChineseSelectableAttributedTextView`），于是 `DetailPreviewKind` 不需要新 case ——
/// 它的粒度定义是"有没有整块子视图被插入/移除"，而 HTML 与 Markdown 用的是同一块视图。
/// 给它加一个 case 就是加一条永远不会执行的承诺（同一文件里那段注释立的规矩）。
///
/// ## 为什么"消毒"是这条通道的前提，而不是锦上添花
///
/// 本产品**至今没有任何出网通道**：那道逐文件扫网络 API 字面量的守卫（`LocalOnlyGuardTests`）
/// 在产品 target 上现读零命中（R335）—— 顺带一提，它连注释里的字面量都扫，所以这一句里
/// 不能出现那些 API 的名字：一次有用的红，记在 U-1126。
/// 而剪贴板里的 HTML 是**别人写的**：`<img src="https://tracker/pixel.gif?id=…">` 这种一行
/// 就把"用户正在看哪条剪贴板历史"发出去了 —— 那等于把用户的存档内容交给第三个服务器，
/// 比泄露一条文本严重得多（它连"看了什么"都说了）。
///
/// R335 的 spike（`/tmp/html_spike/`，本机现读）量到 `NSAttributedString(html:)` 在这台机器上
/// **确实一个请求都没发**（本地计数服务器 `HITS=0`，含 `<img>` / `<link rel=stylesheet>` /
/// 内联 `background-image:url()` / `<script>fetch()`，并等了 3 秒）。
/// 但那只是**一台机器的一个系统版本**的读数，不能当契约：
/// ① 判据不许抄别的机器的数（D-227 那一族）；② 系统哪天开始预取，这条通道就静默地变成出网通道。
/// 所以这里把"没有可加载的东西"做成**结构性质**（消毒 + 一条会红的残留检查），
/// spike 那两条只作为"为什么选这条通道"的出处记在账里。
enum HtmlPreviewPolicy {

    /// 渲染 HTML 的字节上限。**单独一个 enum**，因为它是跨文件的不变式：
    /// 判据 `HtmlPreviewPolicyTests.testTheByteCeilingIsDerivedFromTheMeasuredSlope`
    /// 拿它同时对比 `MotionCatalog.maximumDuration`（预算）与当场量出来的斜率。
    static var maximumRenderBytes: Int { HtmlPreviewRenderBudget.maximumBytes }

    /// 文档级标记：只有这两种形状才把**纯文本条目**当成 HTML。
    ///
    /// 为什么不做"看到 `<div>` 就算"：用户真的会复制 HTML **源码**，而源码里满是小写标签；
    /// 把源码渲染成页面，等于把他要抄的东西藏起来。`<!doctype html` / `<html` 是
    /// "这是一份文档"的强声明，复制源码时通常也带着它 —— 那一类误判由「原文」那颗控件兜住
    /// （入口存在本身就说明"两种看法都有"，切换是一击的事）。
    static func looksLikeHtmlDocument(_ text: String) -> Bool {
        let head = text.prefix(400).lowercased()
        return head.contains("<!doctype html") || head.contains("<html")
    }

    /// 文件那一路：`.html` / `.htm`（大小写都认）。
    static func isHtmlFile(_ url: URL) -> Bool {
        ["html", "htm"].contains(url.pathExtension.lowercased())
    }

    /// 该不该给这条记录一个 **HTML 渲染器**。
    ///
    /// 优先级是这条判据的全部内容，所以它写成函数而不是散在视图里的 if：
    /// ① 条目带着 `public.html` 载荷 ⇒ HTML 赢。载荷是**来源 App 自己声明**"这段内容的富格式是 HTML"，
    ///    而 Markdown 那一路是对纯文本投影的**猜测**；猜测不许盖过声明。
    /// ② 没有载荷时，纯文本长得像一份 HTML 文档 ⇒ HTML。
    /// ③ 其余情况不在这里回答（Markdown 自己那格回答），这里只说"不"。
    static func wantsHtmlRendering(text: String, htmlPayloadBytes: Int) -> Bool {
        if htmlPayloadBytes > 0 { return true }
        return looksLikeHtmlDocument(text)
    }

    /// 渲染器实际该画哪一份字节：有载荷用载荷（那才是富格式的本体），否则用文本本身。
    static func renderSource(text: String, htmlPayload: Data?) -> String {
        guard let htmlPayload = htmlPayload, !htmlPayload.isEmpty,
              let decoded = String(data: htmlPayload, encoding: .utf8), !decoded.isEmpty
        else { return text }
        return decoded
    }

    /// 超预算就不渲染（并且要说清为什么 —— 静默退回原文会让人以为"这 HTML 渲染出来就这样"）。
    static func declinesForSize(_ source: String) -> Bool {
        source.utf8.count > maximumRenderBytes
    }

    /// 给头部那颗控件的标题：与 Markdown 同一条规矩 —— 说"点下去会变成什么"。
    static func controlHelp(hasPayload: Bool) -> String {
        hasPayload
            ? "在渲染结果与 HTML 原文之间切换（渲染走的是这条记录自带的 HTML 表示）"
            : "在渲染结果与 HTML 原文之间切换"
    }
}

/// HTML 消毒：**剥掉一切会自己动起来的东西**，留下结构。
///
/// 三条边界，都是量出来的而不是感觉：
/// ① **会加载的**（`src` / `srcset` / `poster` / `background` / `<img>` / `<link>` / `<iframe>` /
///   `<object>` / `<embed>` / `<video>` / `<audio>` / `<source>` / `<base>` / `<meta http-equiv=refresh>`）
///   —— 全部去掉，因为它们能在用户没点任何东西的时候发请求；
/// ② **会执行的**（`<script>`、`on*=` 事件属性、`javascript:` 伪协议、内联 `expression()`）—— 全部去掉；
/// ③ **只是长得不像正文的**（`<style>` 整块、注释 `<!-- -->`）—— 去掉，否则样式表文本会以正文出现
///   （spike 现读：`NSAttributedString(html:)` 自己就不把 `<style>` 画成正文，这一条是防御性的，
///   写在账里而不是当成已验证的缺陷）。
///
/// **留下** `<a href>`：点链接是用户点头的动作，不是产品替他出网；而且 URL 本来就以文字显示在页面上。
/// 内联 `style` 里的 `url(...)` 整条声明去掉，其余声明保留（邮件正文大量依赖内联颜色/字号，
/// 一刀切掉 `style` 会把"渲染"退化成"去标签"）。
enum HtmlSanitizer {

    /// 成对标签：连**内容**一起删（脚本体与样式体不是给用户读的）。
    /// `title` / `head` 在 R335 第一版里漏了：`<title>` 的文字会以正文形式出现在最上面，
    /// 读起来像"页面里多了一个重复标题"——那是排版坏了，不是渲染成功。
    private static let dropElementWithContent = [
        "script", "style", "noscript", "template", "title", "head",
    ]

    /// 整块删但不删内容（容器里的文字还是正文，例如表单里的说明文字）。
    private static let dropTagKeepContent = [
        "iframe", "object", "embed", "frame", "frameset", "canvas", "svg", "math",
        "video", "audio", "source", "track", "map", "area", "portal",
    ]

    /// 自闭合/无内容的标签：整块删。
    private static let dropVoidTag = ["img", "link", "base", "meta", "input", "button"]

    /// 会触发加载或执行的属性名。
    private static let dangerousAttributes = [
        "src", "srcset", "imagesrcset", "poster", "background", "action", "formaction",
        "data", "code", "codebase", "usemap", "dynsrc", "lowsrc", "ping",
    ]

    private static func regex(_ pattern: String, _ options: NSRegularExpression.Options = [.caseInsensitive]) -> NSRegularExpression? {
        try? NSRegularExpression(pattern: pattern, options: options)
    }

    private static let pairedDrop = dropElementWithContent.map { tag in
        (tag: tag, re: regex("<\(tag)\\b[^>]*>.*?</\(tag)\\s*>", [.caseInsensitive, .dotMatchesLineSeparators]))
    }
    private static let blockDrop = dropTagKeepContent.map { tag in
        (tag: tag, re: regex("<\(tag)\\b[^>]*/?>", [.caseInsensitive, .dotMatchesLineSeparators]))
    }
    private static let voidDrop = dropVoidTag.map { tag in
        (tag: tag, re: regex("<\(tag)\\b[^>]*/?>", [.caseInsensitive, .dotMatchesLineSeparators]))
    }
    private static let comments = regex("<!--.*?-->", [.dotMatchesLineSeparators])
    private static let eventAttrs = regex("\\s+on[a-z]+\\s*=\\s*(\"[^\"]*\"|'[^']*'|[^\\s>]+)")
    private static let dangerousAttrs = dangerousAttributes.map { name in
        (name: name, re: regex("\\s+\(name)\\s*=\\s*(\"[^\"]*\"|'[^']*'|[^\\s>]+)"))
    }
    /// `data-*` 全删：它们是给 JS 用的（懒加载占位、埋点参数），渲染器用不到，
    /// 而 `data-src="https://…"` 正是"名字看着无害、值里带 URL"的那一类
    /// —— R335 第一版就是被它打红的（属性名单没写它）。
    private static let dataAttrs = regex(
        "\\s+data-[a-z0-9_.-]+\\s*=\\s*(\"[^\"]*\"|'[^']*'|[^\\s>]+)", [.caseInsensitive])
    /// **兜底那一条**：除 `href` 之外，任何属性的值里只要出现 `://` / `data:` / `url(` 就整条删掉。
    /// 为什么靠"问值"而不是把属性名列全：名字是填不完的（`srcset`、`poster`、`xlink:href`、
    /// `data-original`、各家框架自定义…），而"这个值里有没有一个 URL"是一个**能问完**的问题。
    /// 它与 `residualFetchableReferences` 用同一条判据 —— 名单会漏，问题不会。
    private static let urlValuedAttrs = regex(
        "\\s+(?!href=|HREF=)[a-zA-Z_:][-a-zA-Z0-9_:.]*\\s*=\\s*"
        + "(\"[^\"]*(?://|data:|url\\()[^\"]*\"|'[^']*(?://|data:|url\\()[^']*')",
        [.caseInsensitive])
    private static let styleAttrs = regex("\\s+style\\s*=\\s*(\"([^\"]*)\"|'([^']*)')", [.caseInsensitive])
    /// `<img>` 本体与它的 `alt`（R336 / BACKLOG 401）。
    private static let imgTag = regex("<img\\b[^>]*/?>", [.caseInsensitive, .dotMatchesLineSeparators])
    private static let altAttr = regex("\\balt\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)')",
                                       [.caseInsensitive, .dotMatchesLineSeparators])
    private static let urlDeclaration = regex("[^;]*url\\s*\\([^)]*\\)[^;]*;?", [.caseInsensitive])
    private static let jsHref = regex("\\s+href\\s*=\\s*(\"|')\\s*javascript:[^\"']*\\1", [.caseInsensitive])
    private static let nsResidue = regex("(xmlns(:[a-z0-9._-]+)?|xlink:href|kml:href)\\s*=\\s*(\"[^\"]*\"|'[^']*')", [.caseInsensitive])

    /// 主入口。幂等（`sanitize(sanitize(x)) == sanitize(x)`，判据里钉着）：
    /// 每一支删除都只针对"可加载/可执行"这一类构造，不会把上一次留下的东西变成新的目标。
    static func sanitize(_ html: String) -> String {
        var s = html
        func replace(_ re: NSRegularExpression?, with template: String = "") {
            guard let re = re else { return }
            s = re.stringByReplacingMatches(in: s, range: NSRange(location: 0, length: s.utf16.count),
                                            withTemplate: template)
        }
        // 注释先走：`<!-- <script>…</script> -->` 里的东西不该被后面的规则"救活"，
        // 反过来也不该让脚本规则去匹配注释里的假标签（两支规则谁先跑都会改变另一支的输入）。
        replace(comments)
        for (_, re) in pairedDrop { replace(re) }
        for (_, re) in blockDrop { replace(re) }
        // ①′ `<img>` 先换成它的 alt 文本，再让 voidDrop 把标签本体删掉（R336 / BACKLOG 401）。
        //     为什么不能直接删：一张以图为主的页面复制下来，渲染态会是一块**空白**，
        //     而屏幕上没有任何一句话解释"这里原本有东西"——那是把消毒的代价静默转嫁给用户。
        //     `alt` 正是 HTML 自己为这件事准备的字段（图加载不了时该显示什么），
        //     用它不是发明，是照抄规范。
        s = imagesReplacedWithAlt(s)
        for (_, re) in voidDrop { replace(re) }
        replace(jsHref)
        replace(eventAttrs)
        replace(nsResidue)
        for (_, re) in dangerousAttrs { replace(re) }
        // 内联 style：只去掉带 url() 的那一条声明，其余留着（颜色/字号是"渲染"的本体）。
        if let styleAttrs = styleAttrs {
            var out = ""
            var last = 0
            let ns = s as NSString
            for m in styleAttrs.matches(in: s, range: NSRange(location: 0, length: ns.length)) {
                out += ns.substring(with: NSRange(location: last, length: m.range.location - last))
                let quoteRange = m.range(at: 2).location != NSNotFound ? m.range(at: 2) : m.range(at: 3)
                let value = quoteRange.location != NSNotFound ? ns.substring(with: quoteRange) : ""
                let kept = urlDeclaration?.stringByReplacingMatches(in: value,
                                                                    range: NSRange(location: 0, length: value.utf16.count),
                                                                    withTemplate: "") ?? value
                // 引号统一成双引号，值里的双引号直接删掉：保留原引号形状要在两个捕获组之间再跳一次，
                // 而"引号是哪种"对渲染没有任何影响 —— 复杂度和收益不对等，写在这里而不是不写。
                out += "style=\"" + kept.replacingOccurrences(of: "\"", with: "") + "\""
                last = m.range.location + m.range.length
            }
            out += ns.substring(from: last)
            s = out
        }
        // 兜底两条排在 style 外科手术**之后**：先保住 `color:#0a0`，再把任何仍然带 URL 的属性
        // （包括改不干净的 style）整条删掉。反过来排会把整条 style 一起带走 ——
        // 判据 `testInlineStyleKeepsColorsButLosesUrls` 抓的就是这个顺序（R335 现读：先排错时颜色没了）。
        replace(urlValuedAttrs)
        replace(dataAttrs)
        return s
    }

    /// 消毒之后**还剩什么可加载/可执行的东西**。判据要的是空表；
    /// 它同时也是那条"这台机器判不了"的替代物：不依赖任何一次网络观测，纯结构。
    static func residualFetchableReferences(_ html: String) -> [String] {
        let patterns = [
            "<script", "<style", "<img", "<link", "<iframe", "<object", "<embed", "<video", "<audio",
            "<source", "<meta", "<base", "src\\s*=", "srcset\\s*=", "poster\\s*=", "background\\s*=",
            "formaction\\s*=", "javascript:", "url\\s*\\(",
        ]
        var hits: [String] = []
        for p in patterns {
            guard let re = regex(p) else { continue }
            if re.firstMatch(in: html, range: NSRange(location: 0, length: html.utf16.count)) != nil {
                hits.append(p)
            }
        }
        // 事件属性单独一条：`on\w+=` 的形状与上面的字面量不同族，分开数才不会互相顶掉。
        if let re = regex("\\son[a-z]+\\s*="),
           re.firstMatch(in: html, range: NSRange(location: 0, length: html.utf16.count)) != nil {
            hits.append("on*=…")
        }
        return hits
    }

    /// 把每个 `<img …>` 换成它的 `alt` 文本；**没有 alt 或 alt 是空的就整块删掉**。
    ///
    /// 三条规则，各自有出处，不是"顺手"：
    /// ① 有 alt ⇒ 留那句文字。图被消毒撤掉之后，alt 是这张页面里**本来就准备给人读**的那一份
    ///    （HTML 规范里 `alt` 就是"图加载不了时显示什么"），撤掉它等于把作者的说明也一起撤了。
    /// ② `alt=""` 或没有 alt ⇒ 整块删，**不发明占位文字**。空 alt 在规范里是作者明确声明
    ///    "这是装饰图"；而 1×1 的埋点像素通常根本没有 alt —— 给这两种写出"〔图片〕"
    ///    等于替追踪像素在屏幕上占一个位置，那是另一种泄漏（它告诉用户"这里有一张图"，
    ///    而那张图本来就是用来数他的）。
    /// ③ alt 值里的 `<` 与 `>` 一律删掉：属性值会变成**正文**，不剥尖括号就是
    ///    `alt="<script>alert(1)</script>"` 这种"从属性里爬回文档"的通道。
    ///    （这一条与"注释里藏的 script 不许被救活"同一族：顺序会改变另一支规则的输入。）
    /// ④ **独占一行**的图 ⇒ alt 自成一段（包成 `<p>`）；**句中**的图 ⇒ 就地换成文字。
    ///    这一条是 R336 自己踩出来的：只做 ①〜③ 时，说明文字是裸的行内文本，
    ///    `NSAttributedString(html:)` 把它并进上一个块的行节奏 —— 真帧现读它与下一段之间
    ///    是 20.0pt（= 列表自己的行内距），而两个 `<p>` 之间是 32.0pt；
    ///    屏幕上"图的说明"和下一段挤成同一段，读起来像列表漏了一颗项目符号。
    ///    仓库外的 spike 同一条量到 17.0 对 29.0，并且**包 `<div>` 没有这个效果**（与不包同数）
    ///    ⇒ 选 `<p>` 不是"随便挑一个块级标签"，是量出来的。
    static func imagesReplacedWithAlt(_ html: String) -> String {
        guard let tag = imgTag else { return html }
        let ns = html as NSString
        var out = ""
        var last = 0
        for m in tag.matches(in: html, range: NSRange(location: 0, length: ns.length)) {
            out += ns.substring(with: NSRange(location: last, length: m.range.location - last))
            last = m.range.location + m.range.length
            let whole = ns.substring(with: m.range)
            guard let alt = altAttr else { continue }
            let inner = alt.firstMatch(in: whole, range: NSRange(location: 0, length: (whole as NSString).length))
            guard let hit = inner else { continue }
            // 两个捕获组（双引号 / 单引号）只有一支会命中，取非空那一支。
            let group = hit.range(at: 1).location != NSNotFound ? hit.range(at: 1) : hit.range(at: 2)
            guard group.location != NSNotFound else { continue }
            let raw = (whole as NSString).substring(with: group)
            let cleaned = raw.unicodeScalars.filter { $0 != "<" && $0 != ">" }
                .reduce(into: "") { $0.append(Character($1) == "\n" ? " " : Character($1)) }
                .trimmingCharacters(in: .whitespacesAndNewlines)
            guard !cleaned.isEmpty else { continue }   // 装饰图 / 埋点像素：整块删
            out += isStandaloneBlock(ns, at: m.range) ? "<p>" + cleaned + "</p>" : cleaned
        }
        out += ns.substring(from: last)
        return out
    }

    /// 这张图是不是**独占一行**：它前面（到上一个 `>` 为止）与后面（到下一个 `<` 为止）都只剩空白。
    ///
    /// 两个方向都要问：只问一边会把句中的图判成独占 ——
    /// `<p>见图 <img alt="图一"> 说明</p>` 里那张图后面紧跟标签边界，"后面是空白"这一半成立，
    /// 而前面是"见图"两个字。判成独占就会把一句话劈成三段。
    private static func isStandaloneBlock(_ ns: NSString, at range: NSRange) -> Bool {
        let before = ns.substring(with: NSRange(location: 0, length: range.location))
        let tailStart = range.location + range.length
        let after = ns.substring(with: NSRange(location: tailStart, length: ns.length - tailStart))
        let headSlice: Substring
        if let gt = before.range(of: ">", options: .backwards) {
            headSlice = before[gt.upperBound...]
        } else {
            headSlice = Substring(before)   // 整串之前没有标签：这段文字本来就在文档最前面
        }
        guard headSlice.allSatisfy(\.isWhitespace) else { return false }
        let tailSlice: Substring
        if let lt = after.firstIndex(of: "<") {
            tailSlice = after[..<lt]
        } else {
            tailSlice = Substring(after)
        }
        return tailSlice.allSatisfy(\.isWhitespace)
    }

    /// 渲染前的最后一道闸：**只**喂消毒过的串。
    /// 单独一个函数是为了让"忘了消毒"这件事在判据里是一根可以下的刀（M974）。
    static func renderableHTML(_ raw: String) -> String {
        sanitize(raw)
    }
}

/// HTML 渲染的字节上限（R335）。
///
/// 为什么必须有一条：存档侧的字节上限管不住**文本**那一路 ——
/// `RichTextPolicy.maximumBytesPerRepresentation`（256KB）只管载荷，而一条纯文本条目
/// 可以是几百 KB 的 HTML 源码。详情区是 `@MainActor` 画的，`NSAttributedString(html:)`
/// 又在主线程解析（Apple 的文档要求），于是没有上限就等于让用户按一下方向键换来一次半秒卡顿。
///
/// 这条线不是拍的：R335 spike 本机现读 `168,916 字节 → 85.0ms`（≈0.503ms/KB），
/// 仓库自己那条预算是 `MotionCatalog.maximumDuration = 0.25s`。
/// 判据在**每次运行时**重量斜率并断言"上限换算的毫秒 ≤ 预算"，
/// 所以将来谁把上限抬到量不出来的地方，红的是那一格而不是用户的体验。
enum HtmlPreviewRenderBudget {
    static let maximumBytes = 128 * 1024
}
