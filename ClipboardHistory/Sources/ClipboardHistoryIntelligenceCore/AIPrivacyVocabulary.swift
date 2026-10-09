import Foundation

/// 推荐/情报层共用的**隐私词汇表**。
///
/// 为什么单独成 target（账本 R2-15 / 决策 D-020）：审计第二轮说"AI 脚手架零产品调用、应移出产品路径"，
/// 这句话对 `AIProviderModels` / `AIPrivacyPolicy.decide` 成立，但**对这两个枚举不成立** ——
/// 产品代码一直在用它们（`RecommendationModels.swift:34`、`ContextSnapshot.swift`、
/// `EntryIntelligence.swift`、`ClipboardEntryIntelligenceAdapter.swift:138`），
/// 第一次尝试整体搬走时构建直接报 `cannot find type 'AIPrivacySensitivity' in scope`。
/// 所以拆成：真正在用的词汇表留在这里（产品 target 依赖本模块），没接线的草案挪去
/// `ClipboardHistoryDesignDrafts`，不再进入交付的二进制。
public enum AIPrivacyScope: String, Codable, CaseIterable, Hashable, Sendable {
    case localOnly
    case metadataOnly
    case redactedContent
    case fullContentWithConsent

    public var allowsNetworkRequest: Bool {
        switch self {
        case .localOnly:
            return false
        case .metadataOnly, .redactedContent, .fullContentWithConsent:
            return true
        }
    }
}

public enum AIPrivacySensitivity: String, Codable, CaseIterable, Hashable, Comparable, Sendable {
    case publicLike
    case personal
    case sensitive
    case secret

    public static func < (lhs: AIPrivacySensitivity, rhs: AIPrivacySensitivity) -> Bool {
        lhs.rank < rhs.rank
    }

    private var rank: Int {
        switch self {
        case .publicLike: return 0
        case .personal: return 1
        case .sensitive: return 2
        case .secret: return 3
        }
    }
}
