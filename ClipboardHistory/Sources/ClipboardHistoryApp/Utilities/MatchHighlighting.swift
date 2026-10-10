import Foundation

/// 搜索命中片段的定位（第三轮审计 §4 U-4）。
///
/// 为什么单独成文件、为什么返回 UTF-16 偏移而不是 `Range<String.Index>`：
/// - **偏移要和存储对齐**。详情页的正文是 `NSTextView`，它按 UTF-16 数下标；
///   `String.Index` 走的是 Character 边界。两者在 emoji（代理对）与组合变音符号上会分叉，
///   分叉的结果不是"高亮偏一点"，而是把颜色加到错误的字符上、甚至切进半个 emoji 里。
///   所以这里从一开始就按 `NSString` 算，调用方拿到就能直接用。
/// - 高亮是纯定位问题，把它从视图里拿出来，"命中了什么、命中几次、会不会重叠"才是可以被断言的；
///   留在视图里就只能靠肉眼和帧。
/// - `AGENTS.md` 的定义完成标准第 2 条：新逻辑先落成纯函数，视图里只留薄胶水。
enum MatchHighlighting {
    /// 一段命中的位置，单位是 UTF-16 码元（与 `NSTextStorage` 一致）。
    struct Span: Equatable, Sendable {
        let location: Int
        let length: Int
    }

    /// 最多标这么多段。一个字符的查询碰上 200KB 正文时会给出几十万个命中，
    /// 全部标上去既没有可读性，也会把主线程的临时属性设置拖长。
    static let maximumSpanCount = 2_000

    /// 命中区间。空查询不标（返回空），**不许**退化成"全文都算命中"。
    ///
    /// 忽略大小写与音调符号：侧栏的过滤用的是 `localizedCaseInsensitiveContains`
    /// （见 `HistoryStore.filteredEntries`），高亮必须和"它为什么被搜出来"同一套语义，
    /// 否则会出现"这条被搜出来了，正文里却一处都没亮"。
    /// 注意这是近似而不是等价 —— `localized` 变体还带区域感知的折叠，
    /// 个别语言环境下过滤命中而高亮落空是可接受的偏差，反过来（亮了但没被搜出来）才要命。
    static func spans(in text: String, query: String, limit: Int = maximumSpanCount) -> [Span] {
        guard !query.isEmpty, !text.isEmpty, limit > 0 else { return [] }
        let haystack = text as NSString
        let needle = query as NSString
        var spans: [Span] = []
        var searchStart = 0
        while searchStart <= haystack.length - needle.length, spans.count < limit {
            let found = haystack.range(of: needle as String,
                                       options: [.caseInsensitive, .diacriticInsensitive],
                                       range: NSRange(location: searchStart,
                                                      length: haystack.length - searchStart))
            guard found.location != NSNotFound else { break }
            // 命中长度来自 NSString，代理对不会被切断（`range(of:)` 只会整个包住它）。
            spans.append(Span(location: found.location, length: found.length))
            // 前进一格命中长度：左起优先、互不重叠（"aaaa" 查 "aa" 得 2 段，不是 3 段）。
            searchStart = found.location + max(found.length, 1)
        }
        return spans
    }

    /// 把正文切成「命中 / 未命中」交替的片段，给需要自己排版的调用方用
    /// （详情正文走的是 `NSTextView` 的临时属性，不需要这个；这个函数存在是为了
    /// 让"切分"这件事在 SwiftUI 文本运行的场合也能复用同一份判定）。
    static func segments(in text: String, query: String) -> [(String, isMatch: Bool)] {
        let spans = spans(in: text, query: query)
        guard !spans.isEmpty else { return [(text, isMatch: false)] }
        let utf16 = text.utf16
        var result: [(String, isMatch: Bool)] = []
        var cursor = 0
        func slice(from start: Int, to end: Int) -> String {
            guard start < end else { return "" }
            // `String.Index(utf16Offset:in:)` 不是可选的（它会把越界值钳在边界内），
            // 所以这里不需要 guard let —— 越界由上面的 start < end 和调用方一起保证。
            let lo = String.Index(utf16Offset: start, in: text)
            let hi = String.Index(utf16Offset: end, in: text)
            return String(text[lo..<hi])
        }
        for span in spans {
            let plain = slice(from: cursor, to: span.location)
            if !plain.isEmpty { result.append((plain, isMatch: false)) }
            let hit = slice(from: span.location, to: span.location + span.length)
            if !hit.isEmpty { result.append((hit, isMatch: true)) }
            cursor = span.location + span.length
        }
        let tail = slice(from: cursor, to: utf16.count)
        if !tail.isEmpty { result.append((tail, isMatch: false)) }
        return result
    }
}
