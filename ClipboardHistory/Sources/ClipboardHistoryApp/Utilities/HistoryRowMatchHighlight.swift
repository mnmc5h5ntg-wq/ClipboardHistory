import AppKit
import SwiftUI

/// 主列表行的搜索命中高亮（R456）。
///
/// 为什么要有这一层：侧栏过滤从 R445 起会匹配正文与来源 App 名，但行里此前**一个字都不标** ——
/// 只命中来源的行（`sidebar-search-source`）整行没有任何线索；正文命中落在两行截断之外时也一样。
/// 高亮只标**可见文字里真的出现过的**片段：时间不是搜索字段，所以来源行里只标 App 名、
/// 不标时间（否则会出现"亮了却没参与匹配"的假线索）。
///
/// 语义与过滤同源：复用 `MatchHighlighting.segments`（大小写/变音符号不敏感），
/// 这样"为什么被搜出来"与"哪里亮了"不会各说一套。
enum HistoryRowMatchHighlight {
    static func highlighted(_ text: String, query: String) -> AttributedString {
        var result = AttributedString()
        for piece in MatchHighlighting.segments(in: text, query: query) {
            var run = AttributedString(piece.0)
            if piece.isMatch {
                run.backgroundColor = Color(nsColor: DetailTypography.highlightColor)
            }
            result.append(run)
        }
        return result
    }

    static func sourceLine(time: String, sourceAppName: String?, query: String) -> AttributedString {
        guard let name = normalized(sourceAppName) else { return AttributedString(time) }
        var result = AttributedString("\(time) · 来自 ")
        result.append(highlighted(name, query: query))
        return result
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
