import AppKit

/// 详情状态条（时间 · 大小 · 来自 X）左边的来源 App 图标。
///
/// 只在**有来源名**时出现：图标是对那句「来自 X」的视觉锚点，不是一条独立信息。
/// 解析不到应用（被卸载、bundle 缺失）时退回 `app` 符号 —— 不能让一条有来源名的记录
/// 因为查不到图标就少一截状态条。
enum SourceAppBadgePolicy {
    static let fallbackSymbolName = "app"
    /// 与行首类型图标同一档：它和 11pt 的 meta 文字并排，14pt 才同样显眼。
    static let iconSize: CGFloat = VisualGlyph.rowIcon

    static func isVisible(sourceAppName: String?) -> Bool {
        normalized(sourceAppName) != nil
    }

    /// macOS 12 没有 `ViewThatFits`（13+ 由拟合结果决定，不走这条）。
    /// 400pt 是**两头都留够**的那一档：紧凑文案 266pt + 图标 22pt + 「原文」按钮 ~40pt
    /// + 两侧 gutter 40pt + 间距 8pt ≈ 376pt，400 留 24pt 余量；低于它就先不画图标。
    static let minimumDetailWidthForIcon: CGFloat = 400

    static func isVisible(sourceAppName: String?, detailWidth: CGFloat) -> Bool {
        isVisible(sourceAppName: sourceAppName) && detailWidth >= minimumDetailWidthForIcon
    }

    /// 纯解析：bundle ID 归一后交给注入的查找器；空 ID 不查、不猜。
    static func resolvedIcon(bundleID: String?, lookup: (String) -> NSImage?) -> NSImage? {
        guard let id = normalized(bundleID) else { return nil }
        return lookup(id)
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
