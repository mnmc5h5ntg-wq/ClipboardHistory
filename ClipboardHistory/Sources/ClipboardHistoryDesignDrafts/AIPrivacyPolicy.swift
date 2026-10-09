import Foundation
import ClipboardHistoryIntelligenceCore

struct AIPrivacyDecision: Codable, Equatable, Hashable {
    enum Action: String, Codable, Hashable {
        case allow
        case redact
        case block
    }

    var action: Action
    var reason: String
    var effectiveScope: AIPrivacyScope
}

enum AIPrivacyPolicy {
    static func decide(
        requestedScope: AIPrivacyScope,
        sensitivity: AIPrivacySensitivity,
        providerRunsLocally: Bool
    ) -> AIPrivacyDecision {
        if providerRunsLocally {
            return AIPrivacyDecision(
                action: .allow,
                reason: "本地模型处理，不离开设备。",
                effectiveScope: .localOnly
            )
        }

        switch (requestedScope, sensitivity) {
        case (.localOnly, _):
            return AIPrivacyDecision(
                action: .block,
                reason: "当前隐私策略仅允许本地处理。",
                effectiveScope: .localOnly
            )
        case (_, .secret):
            return AIPrivacyDecision(
                action: .block,
                reason: "内容疑似包含密码、令牌或密钥，禁止发送到云端。",
                effectiveScope: .localOnly
            )
        case (.metadataOnly, .sensitive), (.metadataOnly, .personal), (.metadataOnly, .publicLike):
            return AIPrivacyDecision(
                action: .redact,
                reason: "仅发送类型、长度、来源等元数据。",
                effectiveScope: .metadataOnly
            )
        case (.redactedContent, .sensitive):
            return AIPrivacyDecision(
                action: .redact,
                reason: "敏感内容将脱敏后发送。",
                effectiveScope: .redactedContent
            )
        case (.redactedContent, .personal), (.redactedContent, .publicLike):
            return AIPrivacyDecision(
                action: .allow,
                reason: "允许发送经隐私策略检查的内容。",
                effectiveScope: .redactedContent
            )
        case (.fullContentWithConsent, .sensitive), (.fullContentWithConsent, .personal), (.fullContentWithConsent, .publicLike):
            return AIPrivacyDecision(
                action: .allow,
                reason: "用户已允许向云端发送完整内容。",
                effectiveScope: .fullContentWithConsent
            )
        }
    }
}
