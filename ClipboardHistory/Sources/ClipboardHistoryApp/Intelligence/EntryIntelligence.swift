import Foundation

struct EntryIntelligence: Identifiable, Codable, Equatable, Hashable {
    var id: UUID { entryID }
    var entryID: UUID
    var summary: String?
    var tags: [EntryIntelligenceTag]
    var detectedLanguage: String?
    var sensitivity: AIPrivacySensitivity
    var embeddingStatus: EmbeddingStatus
    var lastAnalyzedAt: Date?
    var source: IntelligenceSource

    init(
        entryID: UUID,
        summary: String? = nil,
        tags: [EntryIntelligenceTag] = [],
        detectedLanguage: String? = nil,
        sensitivity: AIPrivacySensitivity = .personal,
        embeddingStatus: EmbeddingStatus = .notRequested,
        lastAnalyzedAt: Date? = nil,
        source: IntelligenceSource = .ruleBased
    ) {
        self.entryID = entryID
        self.summary = summary
        self.tags = tags
        self.detectedLanguage = detectedLanguage
        self.sensitivity = sensitivity
        self.embeddingStatus = embeddingStatus
        self.lastAnalyzedAt = lastAnalyzedAt
        self.source = source
    }
}

enum EntryIntelligenceTag: String, Codable, CaseIterable, Hashable {
    case plainText
    case url
    case email
    case phoneNumber
    case code
    case shellCommand
    case filePath
    case image
    case video
    case document
    case archive
    case passwordCandidate
    case verificationCode
    case apiKeyCandidate
}

enum EmbeddingStatus: Codable, Equatable, Hashable {
    case notRequested
    case pending
    case available(model: String, updatedAt: Date)
    case unavailable(reason: String)
}

enum IntelligenceSource: String, Codable, Hashable {
    case ruleBased
    case localModel
    case cloudModel
    case imported
}
