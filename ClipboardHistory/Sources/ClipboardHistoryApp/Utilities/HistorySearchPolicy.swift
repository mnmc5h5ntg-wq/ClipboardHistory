import Foundation

/// 侧栏搜索的匹配谓词：内容 + **来源 App 名**。
///
/// 为什么有这一层（R445）：R437 起就记着"主列表搜索不匹配 `sourceAppName`"——
/// 而 R444 已经把来源 App 名显示在每行的时间行里（`时间 · 来自 <来源>`）：
/// 看得见、搜不到，是同一块信息的两种口径。把匹配逻辑收成纯函数之后，
/// Store 只留一行调用（`HistoryStore` 只减不加），来源/内容/OCR/文件四条路都能单测。
///
/// 来源匹配**与内容并列**，不是替换：搜 "Safari" 命中来自 Safari 的行，
/// 搜正文仍然命中正文；空的来源/空查询都不编匹配。
enum HistorySearchPolicy {
    static func matches(entry: ClipboardEntry, query: String,
                        ocrIndex: [ClipboardEntry.ID: String]) -> Bool {
        guard !query.isEmpty else { return true }
        if let source = entry.sourceAppName,
           !source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
           source.localizedCaseInsensitiveContains(query) {
            return true
        }
        switch entry.content {
        case .text(let string):
            return string.localizedCaseInsensitiveContains(query)
        case .image:
            if "图片".localizedCaseInsensitiveContains(query) { return true }
            return OCRPolicy.matches(entry: entry, index: ocrIndex, query: query)
        case .file(let url):
            if url.lastPathComponent.localizedCaseInsensitiveContains(query) { return true }
            return OCRPolicy.matches(entry: entry, index: ocrIndex, query: query)
        case .files(let urls):
            return urls.contains { $0.lastPathComponent.localizedCaseInsensitiveContains(query) }
        }
    }
}
