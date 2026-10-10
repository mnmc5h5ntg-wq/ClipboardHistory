import Foundation

/// 预测特征里的两块**纯计算**，从 `HistoryStore` 搬出来（第三轮审计 C-5：
/// Store 只留编排与状态，可判定的计算放这里，才谈得上"只减不加"）。
/// 搬动本身不改行为：函数体逐字保留，只是可见性从 `private static` 变成 `static`。
enum RecommendationFeatureSupport {
    static func predictionContextSummary(
        app: RunningApplicationContext?,
        eventCount: Int,
        feedbackCount: Int
    ) -> String {
        var parts: [String] = []
        if let name = app?.localizedName {
            parts.append("来源: \(name)")
        }
        if eventCount > 0 {
            parts.append("轨迹: \(eventCount) 事件")
        }
        if feedbackCount > 0 {
            parts.append("反馈: \(feedbackCount) 条")
        }
        return parts.isEmpty ? "无额外上下文" : parts.joined(separator: " · ")
    }

    static func reuseCounts(byEntryID feedback: [RecommendationFeedback]) -> [UUID: Int] {
        var counts: [UUID: Int] = [:]
        for item in feedback where item.kind == .accepted || item.kind == .copiedManually {
            counts[item.entryID, default: 0] += 1
        }
        return counts
    }
}
