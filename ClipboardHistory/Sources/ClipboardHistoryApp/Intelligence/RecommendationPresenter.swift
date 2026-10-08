import Foundation

/// 把"为什么推荐这条"渲染成面向用户的一行中文。
///
/// 从 `HistoryStore.refreshPredictions()` 里搬出来（那 95 行原本和并发编排、
/// 结果回写混在同一个 `@MainActor` 方法里，既不可测也没人测）。
/// 纯函数：同样输入必然同样输出，因此可以逐标签写断言。
enum RecommendationPresenter {
    static func kindLabel(for entry: ClipboardEntry) -> String {
        switch entry.content {
        case .text(let text):
            if text.hasPrefix("http") { return "链接" }
            if text.count < 200 && text.contains("\n") { return "文本片段" }
            return "文本"
        case .image:
            return "图片"
        case .file:
            return "文件"
        case .files:
            return "多文件"
        }
    }

    /// - Parameter reuseCount: 该条目被采纳/再次复制的**次数**。
    ///   不要从 `features[.reuseFrequency]` 反推：那个值已经乘过用户可调的权重，
    ///   旧写法 `Int(f / 0.08)` 在用户拖动"复用频率"滑杆后显示的次数就是错的（审计 R-17）。
    static func reason(
        for candidate: RecommendationCandidate,
        entry: ClipboardEntry,
        context: ContextSnapshot,
        currentAppName: String?,
        reuseCount: Int
    ) -> String {
        let features = candidate.score.features
        var tags: [String] = []

        if let current = currentAppName, let source = entry.sourceAppName, current == source {
            // 就在原应用里，不必重复说明
        } else if let current = currentAppName {
            tags.append("当前在\(current)")
        }
        if let source = entry.sourceAppName,
           !tags.contains(where: { $0.hasPrefix("当前在") }) {
            tags.append(source)
        }
        if (features[.recency] ?? 0) >= 0.34 {
            tags.append("刚刚复制")
        }
        if reuseCount > 0 {
            tags.append("复用\(reuseCount)次")
        }
        if (features[.contentTypeAffinity] ?? 0) > 0 {
            tags.append(contentTypeTag(bundleID: context.frontmostApplication?.bundleIdentifier))
        }
        if (features[.appAffinity] ?? 0) > 0 {
            let source = entry.sourceAppName
            switch (source, currentAppName) {
            case let (source?, current?) where source == current:
                tags.append("回到\(source)")
            case let (source?, current?):
                tags.append("\(source)→\(current)")
            default:
                tags.append("App匹配")
            }
        }
        if (features[.semanticSimilarity] ?? 0) > 0 {
            tags.append(behavioralTag(events: context.recentEvents))
        }
        if (features[.finderDirectoryAffinity] ?? 0) > 0.5 {
            if let directory = context.finderDirectory?.path {
                tags.append("来自「\(URL(fileURLWithPath: directory).lastPathComponent)」")
            } else {
                tags.append("同目录文件")
            }
        }
        if (features[.finderSelectionAffinity] ?? 0) > 0.5 {
            tags.append(finderSelectionTag(extensions: context.finderSelection?.fileExtensions ?? []))
        }
        if (features[.negativeFeedback] ?? 0) < 0 {
            tags.append("已降权")
        }

        var parts: [String] = [kindLabel(for: entry)]
        if !tags.isEmpty { parts.append(tags.joined(separator: " · ")) }
        parts.append("\(Int(candidate.score.value * 100))%")
        return parts.joined(separator: " · ")
    }

    private static func contentTypeTag(bundleID: String?) -> String {
        let app = bundleID?.lowercased() ?? ""
        if app.contains("safari") || app.contains("chrome") { return "偏好链接" }
        if app.contains("finder") { return "偏好文件" }
        if app.contains("xcode") || app.contains("terminal") { return "偏好命令/代码" }
        if app.contains("wechat") || app.contains("telegram") { return "偏好文本/图片" }
        return "内容匹配"
    }

    private static func behavioralTag(events: [ContextEvent]) -> String {
        let recent = events.suffix(4)
        let copies = recent.filter { $0.kind == .copy }.count
        let switches = recent.filter { $0.kind == .switchToApp }.count
        if copies >= 3 && switches >= 1 { return "跨应用连续复制" }
        if copies >= 3 { return "短时间内多次复制" }
        if switches >= 2 { return "频繁切换应用中" }
        return "你刚复制过同类内容"
    }

    private static func finderSelectionTag(extensions: [String]) -> String {
        guard !extensions.isEmpty else { return "同类文件被选中" }
        let list = extensions.prefix(2).joined(separator: "、")
        return extensions.count > 2 ? "选中 .\(list) 等文件" : "选中 .\(list)"
    }
}
