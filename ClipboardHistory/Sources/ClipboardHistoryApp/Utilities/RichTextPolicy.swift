import AppKit

/// 富文本载荷（第三轮审计 §5 F-2）。
///
/// 问题：`ClipboardIntake` 以前只读 `.string`，写回只 `setString` ⇒
/// 从 Word / Pages / 邮件里复制的一段带加粗和链接的文字，进了历史就只剩裸文本，
/// 再粘贴回去格式全丢 —— 这是剪贴板管理器最常被抱怨的一点。
struct RichTextPayload: Equatable, Hashable, Sendable, Codable {
    /// RTF（`public.rtf`）。Word / Pages / 邮件正文都认这个。
    var rtf: Data?
    /// HTML（`public.html`）。网页编辑器、Slack 类应用更认这个。
    var html: Data?

    var isEmpty: Bool { (rtf?.isEmpty ?? true) && (html?.isEmpty ?? true) }
}

/// 富文本的采集/写回策略。默认**关闭**：开一次等于把每条文本记录存 2–3 份表示，
/// 存档体积翻倍，而 RTF 里还常带着来源元数据（Word 的修订、邮件的信头），
/// 所以这个开关必须由用户点头，不能由产品替他决定。
enum RichTextPolicy {
    static let rtfType = NSPasteboard.PasteboardType.rtf
    static let htmlType = NSPasteboard.PasteboardType.html

    /// 开关键。`SettingsView` 的 Toggle 与这里必须用同一个键。
    static let enabledKey = "preserveRichTextFormat"

    /// 单份表示的字节上限。沿用文本 512K 字符那套思路，但按**字节**算：
    /// RTF/HTML 是字节流，一个 200 页的 Word 文档复制出来能到几十 MB，
    /// 而它进了 `history.json` 就是每条记录都要重写一遍的巨大负载。
    static let maximumBytesPerRepresentation = 256 * 1024

    /// 一条记录里富文本的总上限（两份表示加起来）。
    static let maximumTotalBytes = 384 * 1024

    static func isEnabled(defaults: UserDefaults = .standard) -> Bool {
        // 默认关：显式读"有没有这个键"而不是 `bool(forKey:)`，
        // 因为后者在缺键时返回 false，恰好也"对"，于是将来想改默认值时这里不会有任何提示。
        if defaults.object(forKey: enabledKey) == nil { return false }
        return defaults.bool(forKey: enabledKey)
    }

    static func setEnabled(_ enabled: Bool, defaults: UserDefaults = .standard) {
        defaults.set(enabled, forKey: enabledKey)
    }

    /// 收不收这一段。超限的表示**整份丢掉**而不是截断：
    /// 截断的 RTF/HTML 是坏结构，粘出去会出乱码甚至让目标应用报错，
    /// 而"没有富文本、只有纯文本"永远是可接受的下限。
    static func accepts(bytes count: Int, runningTotal: Int) -> Bool {
        count > 0 && count <= maximumBytesPerRepresentation && runningTotal + count <= maximumTotalBytes
    }

    /// 从剪贴板取富文本表示。开关关、没有表示、或全部超限时返回 nil。
    static func capture(enabled: Bool = true,
                        dataFor: (NSPasteboard.PasteboardType) -> Data?) -> RichTextPayload? {
        guard enabled else { return nil }
        var payload = RichTextPayload(rtf: nil, html: nil)
        var total = 0
        // 顺序有意：RTF 是被支持得最广的那一份，先给它预算；
        // 两个都塞得下才都留，只塞得下一个时留下的是更准的那一个。
        if let rtf = dataFor(rtfType), accepts(bytes: rtf.count, runningTotal: 0) {
            payload.rtf = rtf
            total += rtf.count
        }
        if let html = dataFor(htmlType), accepts(bytes: html.count, runningTotal: total) {
            payload.html = html
        }
        return payload.isEmpty ? nil : payload
    }

    /// 从剪贴板抓（生产入口）。
    static func capture(from pasteboard: NSPasteboard, defaults: UserDefaults = .standard) -> RichTextPayload? {
        capture(enabled: isEnabled(defaults: defaults)) { pasteboard.data(forType: $0) }
    }

    /// 写回时的类型登记顺序。**纯文本永远写**，而且排在富文本之后：
    /// 只认 `public.utf8-plain-text` 的目标（终端、纯文本框）拿到的仍是干净文本，
    /// 而 Word/Pages 会向前找它认的那一份。反过来（字符串放最前）会让富文本被跳过。
    static func write(_ text: String, payload: RichTextPayload?, to item: NSPasteboardItem) {
        if let rtf = payload?.rtf, !rtf.isEmpty {
            item.setData(rtf, forType: rtfType)
        }
        if let html = payload?.html, !html.isEmpty {
            item.setData(html, forType: htmlType)
        }
        item.setString(text, forType: .string)
    }
}
