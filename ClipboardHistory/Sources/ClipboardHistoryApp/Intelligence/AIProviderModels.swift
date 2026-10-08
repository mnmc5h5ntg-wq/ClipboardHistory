import Foundation

enum AIProviderKind: String, Codable, CaseIterable, Hashable {
    case openAI
    case openAICompatible
    case deepSeek
    case anthropic
    case gemini
    case openRouter
    case ollama
    case appleFoundationModels

    var displayName: String {
        switch self {
        case .openAI: return "OpenAI"
        case .openAICompatible: return "OpenAI Compatible"
        case .deepSeek: return "DeepSeek"
        case .anthropic: return "Anthropic"
        case .gemini: return "Gemini"
        case .openRouter: return "OpenRouter"
        case .ollama: return "Ollama"
        case .appleFoundationModels: return "Apple Foundation Models"
        }
    }

    var isLocalDefault: Bool {
        switch self {
        case .ollama, .appleFoundationModels:
            return true
        case .openAI, .openAICompatible, .deepSeek, .anthropic, .gemini, .openRouter:
            return false
        }
    }
}

struct AIProviderCapabilities: Codable, Equatable, Hashable {
    var supportsTextCompletion: Bool
    var supportsEmbeddings: Bool
    var supportsVision: Bool
    var supportsStreaming: Bool
    var runsLocally: Bool

    static let textOnlyCloud = AIProviderCapabilities(
        supportsTextCompletion: true,
        supportsEmbeddings: false,
        supportsVision: false,
        supportsStreaming: true,
        runsLocally: false
    )

    static let localText = AIProviderCapabilities(
        supportsTextCompletion: true,
        supportsEmbeddings: false,
        supportsVision: false,
        supportsStreaming: true,
        runsLocally: true
    )
}

struct AIProviderConfiguration: Identifiable, Codable, Equatable, Hashable {
    var id: UUID
    var kind: AIProviderKind
    var displayName: String
    var baseURL: URL?
    var chatModel: String
    var embeddingModel: String?
    var capabilities: AIProviderCapabilities
    var customHeaders: [String: String]
    var timeoutSeconds: Double
    var isEnabled: Bool

    init(
        id: UUID = UUID(),
        kind: AIProviderKind,
        displayName: String? = nil,
        baseURL: URL? = nil,
        chatModel: String,
        embeddingModel: String? = nil,
        capabilities: AIProviderCapabilities,
        customHeaders: [String: String] = [:],
        timeoutSeconds: Double = 30,
        isEnabled: Bool = false
    ) {
        self.id = id
        self.kind = kind
        self.displayName = displayName ?? kind.displayName
        self.baseURL = baseURL
        self.chatModel = chatModel
        self.embeddingModel = embeddingModel
        self.capabilities = capabilities
        self.customHeaders = customHeaders
        self.timeoutSeconds = timeoutSeconds
        self.isEnabled = isEnabled
    }
}

enum AITaskKind: String, Codable, Hashable {
    case summarizeClipboardEntry
    case classifyClipboardEntry
    case detectSensitiveContent
    case semanticSearch
    case rerankPasteCandidates
    case explainRecommendation
}

enum AIMessageRole: String, Codable, Hashable {
    case system
    case user
    case assistant
}

struct AIMessage: Codable, Equatable, Hashable {
    var role: AIMessageRole
    var content: String
}

struct AICompletionRequest: Codable, Equatable, Hashable {
    var task: AITaskKind
    var messages: [AIMessage]
    var temperature: Double
    var maxTokens: Int?
    var privacyScope: AIPrivacyScope
}

struct AICompletionResponse: Codable, Equatable, Hashable {
    var text: String
    var usage: AITokenUsage?
    var providerMetadata: [String: String]
}

struct AIEmbeddingRequest: Codable, Equatable, Hashable {
    var input: [String]
    var model: String
    var privacyScope: AIPrivacyScope
}

struct AIEmbeddingResponse: Codable, Equatable, Hashable {
    var vectors: [[Double]]
    var usage: AITokenUsage?
}

struct AITokenUsage: Codable, Equatable, Hashable {
    var inputTokens: Int?
    var outputTokens: Int?
    var totalTokens: Int?
}
