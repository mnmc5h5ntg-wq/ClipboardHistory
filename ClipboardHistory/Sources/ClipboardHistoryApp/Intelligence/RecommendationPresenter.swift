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

        // App 亲和标签先算出来：它可能已经把来源 App 的名字说了一遍（"回到Safari"），
        // 下面决定是否还要补一个裸 App 名时要用到这个事实。
        // 顺序保持不变 —— 这里只是**提前计算**，追加仍在原来的位置。
        var appAffinityTag: String?
        if (features[.appAffinity] ?? 0) > 0 {
            let source = entry.sourceAppName
            switch (source, currentAppName) {
            case let (source?, current?) where source == current:
                appAffinityTag = "回到\(source)"
            case let (source?, current?):
                appAffinityTag = "\(source)→\(current)"
            default:
                appAffinityTag = "App匹配"
            }
        }

        if let current = currentAppName, let source = entry.sourceAppName, current == source {
            // 就在原应用里，不必重复说明
        } else if let current = currentAppName {
            tags.append("当前在\(current)")
        }
        // 裸来源 App 名只在"没有任何标签点过来源 App"时才补：
        // "当前在X"（跨应用时来源会由 "Safari→X" 说）与 "回到Safari" 都算点过。
        // 以前只挡了前者，于是"就在原应用里 + 有 App 亲和"这一最常见组合会写成
        // "Safari · 回到Safari"（菜单栏面板第一次拍出真像素时看到的问题）。
        let sourceAlreadyNamed: Bool = {
            if tags.contains(where: { $0.hasPrefix("当前在") }) { return true }
            guard let tag = appAffinityTag, let source = entry.sourceAppName else { return false }
            return tag.contains(source)
        }()
        if let source = entry.sourceAppName, !sourceAlreadyNamed {
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
        if let appAffinityTag {
            tags.append(appAffinityTag)
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
