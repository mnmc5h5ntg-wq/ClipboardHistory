import Foundation

/// 主列表行的时间行：`时间 · 来自 <来源 App>`。
///
/// 为什么要有这一层（R444）：剪贴板历史里"这条是从哪个 App 来的"是核心信息之一，
/// 但主列表以前只显示时间 —— 来源只在详情头部（R425 的图标 + 文案）才看得到。
/// 行里加来源之后，**时间在前、来源在后**：行宽不够时先截断来源，时间不丢
/// （时间回答"新旧"，来源回答"从哪来"，前者是扫读的第一层）。
///
/// 来源可以为 nil（存档里没有来源字段）：此时只显示时间，不编一个"未知"。
enum HistoryRowSourceLine {
    static func text(time: String, sourceAppName: String?) -> String {
        guard let name = normalized(sourceAppName) else { return time }
        return "\(time) · 来自 \(name)"
    }

    private static func normalized(_ text: String?) -> String? {
        guard let text else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
