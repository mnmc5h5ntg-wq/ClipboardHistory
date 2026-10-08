import Foundation

/// 推荐引擎各项因子的权重系数，用户可在设置中客制化。
/// 默认值 1.0 表示使用引擎原始分数；0.0 禁用该因子；2.0 表示双倍权重。
struct RecommendationWeights: Codable, Equatable {
    var recency: Double = 1.0
    var favorite: Double = 1.0
    var appAffinity: Double = 1.0
    var contentTypeAffinity: Double = 1.0
    var finderDirectoryAffinity: Double = 1.0
    var finderSelectionAffinity: Double = 1.0
    var semanticSimilarity: Double = 1.0
    var reuseFrequency: Double = 1.0
    var negativeFeedback: Double = 1.0

    static let `default` = RecommendationWeights()

    subscript(factor: Factor) -> Double {
        get {
            switch factor {
            case .recency: return recency
            case .favorite: return favorite
            case .appAffinity: return appAffinity
            case .contentTypeAffinity: return contentTypeAffinity
            case .finderDirectoryAffinity: return finderDirectoryAffinity
            case .finderSelectionAffinity: return finderSelectionAffinity
            case .semanticSimilarity: return semanticSimilarity
            case .reuseFrequency: return reuseFrequency
            case .negativeFeedback: return negativeFeedback
            }
        }
        set {
            switch factor {
            case .recency: recency = newValue
            case .favorite: favorite = newValue
            case .appAffinity: appAffinity = newValue
            case .contentTypeAffinity: contentTypeAffinity = newValue
            case .finderDirectoryAffinity: finderDirectoryAffinity = newValue
            case .finderSelectionAffinity: finderSelectionAffinity = newValue
            case .semanticSimilarity: semanticSimilarity = newValue
            case .reuseFrequency: reuseFrequency = newValue
            case .negativeFeedback: negativeFeedback = newValue
            }
        }
    }

    enum Factor: String, CaseIterable, Codable {
        case recency
        case favorite
        case appAffinity
        case contentTypeAffinity
        case finderDirectoryAffinity
        case finderSelectionAffinity
        case semanticSimilarity
        case reuseFrequency
        case negativeFeedback

        var label: String {
            switch self {
            case .recency: return "近因"
            case .favorite: return "收藏"
            case .appAffinity: return "App 亲和"
            case .contentTypeAffinity: return "内容类型亲和"
            case .finderDirectoryAffinity: return "Finder 目录"
            case .finderSelectionAffinity: return "Finder 选中文件"
            case .semanticSimilarity: return "行为节奏"
            case .reuseFrequency: return "复用频率"
            case .negativeFeedback: return "负反馈降权"
            }
        }

        var description: String {
            switch self {
            case .recency: return "最近复制的内容权重更高"
            case .favorite: return "收藏内容获得额外加分"
            case .appAffinity: return "当前前台 App 与内容的匹配度"
            case .contentTypeAffinity: return "内容类型（文本/图片/文件/链接）匹配"
            case .finderDirectoryAffinity: return "Finder 当前目录与来源目录的匹配度"
            case .finderSelectionAffinity: return "Finder 选中文件类型与内容的匹配度"
            case .semanticSimilarity: return "短时间内频繁复制/切换时的模式匹配"
            case .reuseFrequency: return "反复复制同一条内容的历史积累"
            case .negativeFeedback: return "被忽略/撤回的内容自动降权幅度"
            }
        }
    }
}

/// 持有可持久化的推荐权重，发布变化通知
@MainActor
final class RecommendationWeightsStore: ObservableObject {
    @Published var weights: RecommendationWeights {
        didSet {
            guard weights != oldValue else { return }
            persist()
        }
    }

    init() {
        weights = Self.load()
    }

    func restoreDefaults() {
        weights = .default
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(weights) else { return }
        UserDefaults.standard.set(data, forKey: Key.store)
    }

    private static func load() -> RecommendationWeights {
        guard let data = UserDefaults.standard.data(forKey: Key.store),
              let weights = try? JSONDecoder().decode(RecommendationWeights.self, from: data) else {
            return .default
        }
        return weights
    }

    private enum Key {
        static let store = "RecommendationWeights.store"
    }
}
