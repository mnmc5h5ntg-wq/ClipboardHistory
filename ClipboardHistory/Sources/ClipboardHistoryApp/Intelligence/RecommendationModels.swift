import Foundation

enum RecommendationFeature: String, Codable, CaseIterable, Hashable {
    case recency
    case favorite
    case appAffinity
    case contentTypeAffinity
    case finderDirectoryAffinity
    case finderSelectionAffinity
    case semanticSimilarity
    case searchMatch
    case reuseFrequency
    case negativeFeedback
}

struct RecommendationScore: Codable, Equatable, Hashable {
    var value: Double
    var features: [RecommendationFeature: Double]

    static let zero = RecommendationScore(value: 0, features: [:])
}

struct RecommendationCandidate: Identifiable, Codable, Equatable, Hashable {
    var id: UUID { entryID }
    var entryID: UUID
    var score: RecommendationScore
    var reason: String
}

struct RecommendationRequest: Codable, Equatable, Hashable {
    var context: ContextSnapshot
    var limit: Int
    var allowsAIReRanking: Bool
    var privacyScope: AIPrivacyScope
    var enablePrivacyFilter: Bool = true
}

struct RecommendationResult: Codable, Equatable, Hashable {
    var generatedAt: Date
    var candidates: [RecommendationCandidate]
    var usedAI: Bool
    var explanation: String
}

enum RecommendationFeedbackKind: String, Codable, CaseIterable, Hashable {
    case accepted
    case ignored
    case copiedManually
    case dismissed
    case reverted
}

extension RecommendationFeedback {
    /// 存储用的投影：保留元数据，丢弃所有正文类字段。
    func withoutClipboardContent() -> RecommendationFeedback {
        var copy = self
        copy.context = context.strippedOfClipboardContent()
        return copy
    }
}

struct RecommendationFeedback: Codable, Equatable, Hashable {
    var entryID: UUID
    var kind: RecommendationFeedbackKind
    /// 内存里可以是完整快照（调用方复用同一份 context），但**序列化时只写元数据**。
    var context: ContextSnapshot
    var createdAt: Date

    private enum CodingKeys: String, CodingKey {
        case entryID, kind, context, createdAt
    }

    private enum SlimContextKeys: String, CodingKey {
        case frontmostBundleID, frontmostName, recentEventCount, capturedAt
    }

    init(entryID: UUID, kind: RecommendationFeedbackKind, context: ContextSnapshot, createdAt: Date) {
        self.entryID = entryID
        self.kind = kind
        self.context = context
        self.createdAt = createdAt
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        entryID = try container.decode(UUID.self, forKey: .entryID)
        kind = try container.decode(RecommendationFeedbackKind.self, forKey: .kind)
        createdAt = try container.decode(Date.self, forKey: .createdAt)
        context = try RecommendationFeedback.decodeContext(in: container)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(entryID, forKey: .entryID)
        try container.encode(kind, forKey: .kind)
        try container.encode(createdAt, forKey: .createdAt)
        var contextContainer = container.nestedContainer(
            keyedBy: SlimContextKeys.self,
            forKey: .context
        )
        try contextContainer.encodeIfPresent(context.frontmostApplication?.bundleIdentifier, forKey: .frontmostBundleID)
        try contextContainer.encodeIfPresent(context.frontmostApplication?.localizedName, forKey: .frontmostName)
        try contextContainer.encode(context.recentEvents.count, forKey: .recentEventCount)
        try contextContainer.encode(context.capturedAt, forKey: .capturedAt)
    }

    /// 先按瘦格式解；不认（旧版把整个 ContextSnapshot 写了进去）就按旧格式解，
    /// 解出来立刻去掉正文类字段。
    private static func decodeContext(
        in container: KeyedDecodingContainer<CodingKeys>
    ) throws -> ContextSnapshot {
        if let slim = try? container.nestedContainer(keyedBy: SlimContextKeys.self, forKey: .context),
           slim.contains(.recentEventCount) {
            let bundleID = try? slim.decode(String.self, forKey: .frontmostBundleID)
            let name = try? slim.decode(String.self, forKey: .frontmostName)
            let eventCount = (try? slim.decode(Int.self, forKey: .recentEventCount)) ?? 0
            let capturedAt = (try? slim.decode(Date.self, forKey: .capturedAt)) ?? Date(timeIntervalSince1970: 0)
            let placeholderEvents = (0..<max(eventCount, 0)).map { _ in
                ContextEvent(kind: .idle, timestamp: capturedAt)
            }
            return ContextSnapshot(
                capturedAt: capturedAt,
                frontmostApplication: (bundleID == nil && name == nil) ? nil
                    : RunningApplicationContext(localizedName: name, bundleIdentifier: bundleID, processIdentifier: nil),
                activeWindow: nil,
                browser: nil,
                focusedDocument: nil,
                finderDirectory: nil,
                finderSelection: nil,
                recentEntries: [],
                recentEvents: placeholderEvents,
                selectedEntryID: nil,
                permissionState: .minimal
            )
        }
        let legacy = try container.decode(ContextSnapshot.self, forKey: .context)
        return legacy.strippedOfClipboardContent()
    }
}
