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

struct RecommendationFeedback: Codable, Equatable, Hashable {
    var entryID: UUID
    var kind: RecommendationFeedbackKind
    var context: ContextSnapshot
    var createdAt: Date
}
