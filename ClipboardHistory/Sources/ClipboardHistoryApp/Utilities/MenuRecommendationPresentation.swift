import Foundation

/// R506：macOS 13+ 的状态菜单是 SwiftUI `MenuBarExtra`，菜单项标签会被拍平成
/// 单个文本 —— 推荐行原来用 HStack（标题 + 右侧理由），系统只留下第一个 Text，
/// 「为什么推荐」整段消失。这里把理由并进同一个 Text（弱一档），保住信息。
enum MenuRecommendationPresentation {
    static func reasonSuffix(_ reason: String) -> String {
        let trimmed = reason.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "" : "  " + trimmed
    }
}
