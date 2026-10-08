import Foundation

struct RuleBasedRecommendationEngine {
    var now: Date
    var weights: RecommendationWeights

    init(now: Date = Date(), weights: RecommendationWeights = .default) {
        self.now = now
        self.weights = weights
    }

    func recommend(
        entries: [ClipboardEntrySummary],
        intelligenceByEntryID: [UUID: EntryIntelligence] = [:],
        feedback: [RecommendationFeedback] = [],
        request: RecommendationRequest
    ) -> RecommendationResult {
        let effectiveEntries = request.enablePrivacyFilter
            ? entries.filter { !Self.containsSensitiveContent($0) }
            : entries
        let filtered = effectiveEntries
        // 同分候选需要一个确定的次级排序键：Swift 的 sorted(by:) 文档明确不保证稳定，
        // 只靠"输入顺序"会让同一份历史在不同次运行里给出不同推荐（本轮实测复现）。
        let copiedAtByEntryID = Dictionary(filtered.map { ($0.id, $0.copiedAt) }, uniquingKeysWith: { first, _ in first })
        let candidates = filtered
            .map { entry in
                candidate(
                    for: entry,
                    intelligence: intelligenceByEntryID[entry.id],
                    feedback: feedback,
                    request: request
                )
            }
            .sorted { lhs, rhs in
                if lhs.score.value != rhs.score.value {
                    return lhs.score.value > rhs.score.value
                }
                if lhs.reason != rhs.reason {
                    return lhs.reason < rhs.reason
                }
                let lhsCopiedAt = copiedAtByEntryID[lhs.entryID] ?? .distantPast
                let rhsCopiedAt = copiedAtByEntryID[rhs.entryID] ?? .distantPast
                if lhsCopiedAt != rhsCopiedAt {
                    return lhsCopiedAt > rhsCopiedAt
                }
                return lhs.entryID.uuidString < rhs.entryID.uuidString
            }
            .prefix(max(request.limit, 0))

        return RecommendationResult(
            generatedAt: now,
            candidates: Array(candidates),
            usedAI: false,
            explanation: "使用本地规则排序，未调用 AI 模型。"
        )
    }

    private func candidate(
        for entry: ClipboardEntrySummary,
        intelligence: EntryIntelligence?,
        feedback: [RecommendationFeedback],
        request: RecommendationRequest
    ) -> RecommendationCandidate {
        var features: [RecommendationFeature: Double] = [:]
        features[.recency] = recencyScore(for: entry) * weights.recency
        features[.favorite] = (entry.isFavorite ? 0.18 : 0) * weights.favorite
        features[.appAffinity] = appAffinityScore(for: entry, context: request.context) * weights.appAffinity
        features[.contentTypeAffinity] = contentTypeScore(for: entry, context: request.context) * weights.contentTypeAffinity
        features[.finderDirectoryAffinity] = finderDirectoryScore(for: entry, context: request.context) * weights.finderDirectoryAffinity
        features[.finderSelectionAffinity] = finderSelectionScore(for: entry, context: request.context) * weights.finderSelectionAffinity
        features[.reuseFrequency] = reuseScore(for: entry, feedback: feedback) * weights.reuseFrequency
        features[.negativeFeedback] = negativeFeedbackScore(for: entry, feedback: feedback) * weights.negativeFeedback
        features[.semanticSimilarity] = behavioralRhythmScore(for: entry, context: request.context) * weights.semanticSimilarity
        let hybrid = hybridFrequencyRecencyScore(for: entry, feedback: feedback)
        features[.recency] = max(features[.recency] ?? 0, hybrid)

        if intelligence?.tags.contains(.passwordCandidate) == true
            || intelligence?.tags.contains(.apiKeyCandidate) == true {
            features[.negativeFeedback, default: 0] -= 0.35
        }

        // 必须按固定顺序累加：`features` 是 Dictionary，Dictionary 的迭代顺序按进程随机
        // 播种，`reduce(0, +)` 的浮点求和因此会有 1 ULP 级别的抖动 —— 实测让 5 条同分候选
        // 在两次启动之间排出不同次序（0.23999999999999999 vs 0.24000000000000002）。
        let value = Self.summedScore(from: features).clamped(to: 0...1)
        return RecommendationCandidate(
            entryID: entry.id,
            score: RecommendationScore(value: value, features: features),
            reason: reason(for: entry, score: value, features: features)
        )
    }

    private func recencyScore(for entry: ClipboardEntrySummary) -> Double {
        let age = max(0, now.timeIntervalSince(entry.copiedAt))
        switch age {
        case 0..<60:
            return 0.42
        case 60..<300:
            return 0.34
        case 300..<1_800:
            return 0.24
        case 1_800..<7_200:
            return 0.14
        default:
            return 0.06
        }
    }

    /// 频率×新鲜度混合排序：采纳次数 / 年龄^重力因子
    private func hybridFrequencyRecencyScore(
        for entry: ClipboardEntrySummary,
        feedback: [RecommendationFeedback]
    ) -> Double {
        let adoptions = feedback.filter {
            $0.entryID == entry.id &&
            ($0.kind == .accepted || $0.kind == .copiedManually)
        }.count
        guard adoptions > 0 else { return 0 }
        let ageHours = max(0.1, now.timeIntervalSince(entry.copiedAt) / 3600.0)
        let gravity: Double = 1.5
        return min(Double(adoptions) / pow(ageHours, gravity), 0.35)
    }

    /// 隐私过滤器：排除密码、API 密钥、信用卡号等敏感内容
    /// 检测敏感内容（GitHub Token / API Key / 信用卡 / 私钥 / JWT / 数据库连接串等）。
    /// 注意：当前基于 `entry.preview`（前 160 字符），超长文本中的敏感内容可能漏检。
    /// 完整改进方向：在 `HistoryStore.add()` 存储前对完整文本调用此检测。
    static func containsSensitiveContent(_ entry: ClipboardEntrySummary) -> Bool {
        let text = entry.preview
        // GitHub token: ghp_...
        if text.range(of: "ghp_[A-Za-z0-9]{36,}", options: .regularExpression) != nil { return true }
        // OpenAI/API key: sk-...
        if text.range(of: "sk-[A-Za-z0-9]{32,}", options: .regularExpression) != nil { return true }
        // Slack tokens: xoxb- / xoxp- / xoxa-
        if text.range(of: "xox[abpos]-[0-9]+-[0-9]+-[A-Za-z0-9]+", options: .regularExpression) != nil { return true }
        // JWT: eyJ...
        if text.range(of: "eyJ[A-Za-z0-9_-]+\\.eyJ[A-Za-z0-9_-]+", options: .regularExpression) != nil { return true }
        // PEM 私钥 header
        if text.contains("-----BEGIN RSA PRIVATE KEY-----") || text.contains("-----BEGIN EC PRIVATE KEY-----") || text.contains("-----BEGIN PRIVATE KEY-----") { return true }
        // 数据库连接字符串
        if text.range(of: "(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@", options: .regularExpression) != nil { return true }
        // Authorization header
        if text.range(of: "(?i)authorization:\\s*(bearer|basic)\\s+", options: .regularExpression) != nil { return true }
        // 信用卡号 Luhn 候选：13-19 位数字连写
        if let match = text.range(of: "\\b[0-9]{13,19}\\b", options: .regularExpression) {
            let digits = String(text[match]).filter { $0.isNumber }
            if Self.luhnCheck(digits) { return true }
        }
        // AWS 等常见密钥前缀
        let secretPrefixes = ["AKIA", "ABIA", "ACCA", "AGPA", "AIDA", "AIPA", "AKID", "ANPA", "APKA", "AROA", "ASIA"]
        for prefix in secretPrefixes {
            if text.contains(prefix) && text.count >= 20 { return true }
        }
        // 纯 hex 超长串（可能是私钥）
        if text.range(of: "\\b[0-9a-fA-F]{64,}\\b", options: .regularExpression) != nil {
            return true
        }
        return false
    }

    private static func luhnCheck(_ digits: String) -> Bool {
        guard digits.count >= 13, digits.allSatisfy({ $0.isNumber }) else { return false }
        var sum = 0
        let reversed = digits.reversed().compactMap { Int(String($0)) }
        for (i, digit) in reversed.enumerated() {
            if i % 2 == 1 {
                let doubled = digit * 2
                sum += doubled > 9 ? doubled - 9 : doubled
            } else {
                sum += digit
            }
        }
        return sum % 10 == 0
    }

    private func contentTypeScore(for entry: ClipboardEntrySummary, context: ContextSnapshot) -> Double {
        let kind = entry.contentKind.lowercased()
        let currentApp = context.frontmostApplication?.bundleIdentifier?.lowercased() ?? ""
        let isURL = kind.contains("url") || entry.preview.lowercased().hasPrefix("http")
        let isFile = kind.contains("file") || kind.contains("image")
        let isCode = kind.contains("shell") || kind.contains("code")

        var score = 0.0

        // Phase 1: 当前 App 亲和分 — 始终计算，切换 App 时分数会变化
        if currentApp.contains("safari") || currentApp.contains("chrome") {
            if isURL { score += 0.12 }
            else if isFile { score += 0.02 }
            else { score += 0.06 }
        } else if currentApp.contains("finder") {
            if isFile { score += 0.12 }
            else if isURL { score += 0.02 }
            else { score += 0.04 }
        } else if currentApp.contains("xcode") || currentApp.contains("terminal") {
            if isCode { score += 0.10 }
            else { score += 0.04 }
        } else if currentApp.contains("wechat") || currentApp.contains("telegram") {
            if isFile { score += 0.06 }
            else { score += 0.08 }
        } else {
            // 无法确定当前 App，按内容类型给基础分
            if isURL { score += 0.06 }
            else if isFile { score += 0.04 }
            else if isCode { score += 0.04 }
            else { score += 0.04 }
        }

        // Phase 2: 来源 App 加分 — 条目在天然适用该类型的 App 中被复制
        if let sourceAppID = entry.sourceAppBundleID?.lowercased() {
            if sourceAppID.contains("finder"), kind.contains("file") { score += 0.04 }
            if sourceAppID.contains("xcode"), kind.contains("text") { score += 0.04 }
            if sourceAppID.contains("safari") || sourceAppID.contains("chrome") || sourceAppID.contains("arc") {
                if isURL { score += 0.04 }
                if kind.contains("text") { score += 0.02 }
            }
            if sourceAppID.contains("wechat") || sourceAppID.contains("telegram") || sourceAppID.contains("messages") {
                if kind.contains("image") || kind.contains("file") { score += 0.02 }
                if kind.contains("text") { score += 0.04 }
            }
        }

        return min(score, 0.18)
    }

    private func appAffinityScore(for entry: ClipboardEntrySummary, context: ContextSnapshot) -> Double {
        let currentApp = context.frontmostApplication?.bundleIdentifier?.lowercased() ?? ""
        let source = entry.sourceAppBundleID?.lowercased() ?? ""
        guard !currentApp.isEmpty else { return 0 }

        // 当前 App 等于来源 App → 高亲和
        if !source.isEmpty, currentApp == source {
            return 0.10
        }
        // 当前 App 与来源 App 同类 → 中等亲和
        let browserIDs = ["safari", "chrome", "arc", "firefox", "edge"]
        let chatIDs = ["wechat", "telegram", "messages"]
        let devIDs = ["xcode", "terminal", "code", "idea"]
        if browserIDs.contains(where: { currentApp.contains($0) }) && browserIDs.contains(where: { source.contains($0) }) {
            return 0.06
        }
        if chatIDs.contains(where: { currentApp.contains($0) }) && chatIDs.contains(where: { source.contains($0) }) {
            return 0.06
        }
        if devIDs.contains(where: { currentApp.contains($0) }) && devIDs.contains(where: { source.contains($0) }) {
            return 0.06
        }
        return 0
    }

    private func finderDirectoryScore(for entry: ClipboardEntrySummary, context: ContextSnapshot) -> Double {
        guard let dir = context.finderDirectory?.path else { return 0 }
        let preview = entry.preview.lowercased()
        // 条目来自同目录 → 高匹配
        if preview.contains(dir.lowercased()) {
            return 1.0
        }
        // 条目是文件类型且 Finder 在前台 → 轻微加分
        let kind = entry.contentKind.lowercased()
        if kind.contains("file") || kind.contains("files") {
            return 0.3
        }
        return 0
    }

    private func finderSelectionScore(for entry: ClipboardEntrySummary, context: ContextSnapshot) -> Double {
        guard let sel = context.finderSelection, !sel.fileExtensions.isEmpty else { return 0 }
        let preview = entry.preview.lowercased()
        for ext in sel.fileExtensions {
            if preview.hasSuffix(".\(ext)") {
                return 1.0
            }
        }
        // 同类型文件在 Finder 被选中 → 中等加分
        let kind = entry.contentKind.lowercased()
        if kind.contains("file") || kind.contains("files") {
            return 0.2
        }
        return 0
    }

    private func behavioralRhythmScore(for entry: ClipboardEntrySummary, context: ContextSnapshot) -> Double {
        let events = context.recentEvents
        guard events.count >= 2 else { return 0 }

        let copiedIDs = events
            .filter { $0.kind == .copy }
            .compactMap(\.entryID)

        if copiedIDs.contains(entry.id) {
            return 0.04
        }

        let switchBurst = events.suffix(4)
        let copyCountInBurst = switchBurst.filter { $0.kind == .copy }.count
        let appSwitchCountInBurst = switchBurst.filter { $0.kind == .switchToApp }.count

        if copyCountInBurst >= 2 && appSwitchCountInBurst >= 2 {
            return 0.04
        }

        if copyCountInBurst >= 3 && entry.contentKind.lowercased().contains("text") {
            return 0.02
        }

        return 0
    }

    private func reuseScore(for entry: ClipboardEntrySummary, feedback: [RecommendationFeedback]) -> Double {
        let acceptedCount = feedback.filter { item in
            item.entryID == entry.id && (item.kind == .accepted || item.kind == .copiedManually)
        }.count
        return min(Double(acceptedCount) * 0.08, 0.24)
    }

    private func negativeFeedbackScore(for entry: ClipboardEntrySummary, feedback: [RecommendationFeedback]) -> Double {
        // 考虑反馈时间衰减：最近 24h 内的拒绝权重更高
        let cutoff = now.addingTimeInterval(-86400)
        let negativeCount = feedback.filter { item in
            item.entryID == entry.id &&
            (item.kind == .dismissed || item.kind == .reverted || item.kind == .ignored)
        }.count
        let recentCount = feedback.filter { item in
            item.entryID == entry.id &&
            item.createdAt >= cutoff &&
            (item.kind == .dismissed || item.kind == .reverted || item.kind == .ignored)
        }.count
        let base = Double(negativeCount) * 0.08
        let recent = Double(recentCount) * 0.10
        return -min(base + recent, 0.50)
    }

    private func reason(
        for entry: ClipboardEntrySummary,
        score: Double,
        features: [RecommendationFeature: Double]
    ) -> String {
        if entry.isFavorite {
            return "收藏内容且与当前排序规则匹配。"
        }
        if (features[.recency] ?? 0) >= 0.34 {
            return "这是最近复制的内容。"
        }
        if (features[.reuseFrequency] ?? 0) > 0 {
            return "你之前多次再次复制过这条内容。"
        }
        if score <= 0.1 {
            return "低置信度候选，仅作为历史备选。"
        }
        return "根据本地历史特征推荐。"
    }
}

extension RuleBasedRecommendationEngine {
    /// 按 `RecommendationFeature.allCases` 的固定顺序求和。
    /// 不要改成 `features.values.reduce(0, +)`：Dictionary 的迭代顺序按进程随机播种，
    /// 浮点加法不满足结合律，同一份历史会在不同启动里排出不同推荐次序（本轮实测复现）。
    nonisolated static func summedScore(from features: [RecommendationFeature: Double]) -> Double {
        RecommendationFeature.allCases.reduce(0.0) { total, feature in
            total + (features[feature] ?? 0)
        }
    }
}

private extension Comparable {
    func clamped(to limits: ClosedRange<Self>) -> Self {
        min(max(self, limits.lowerBound), limits.upperBound)
    }
}
