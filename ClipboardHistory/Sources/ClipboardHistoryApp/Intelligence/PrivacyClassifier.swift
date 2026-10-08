import Foundation

/// 面向"界面上要不要显示正文"的轻量判定。复用推荐引擎已有的敏感规则，
/// 避免两处各写一套正则（审计 R-16 / R-43）。
enum PrivacyClassifier {
    static func mayContainSecrets(_ entry: ClipboardEntry) -> Bool {
        let text: String
        switch entry.content {
        case .text(let body):
            text = body
        case .image, .file, .files:
            text = entry.ocrText ?? ""
        }
        guard !text.isEmpty else { return false }
        let end = text.index(
            text.startIndex,
            offsetBy: ClipboardEntryIntelligenceAdapter.sensitivitySampleLimit,
            limitedBy: text.endIndex
        ) ?? text.endIndex
        let sample = String(text[text.startIndex..<end])
        return RuleBasedRecommendationEngine.containsSensitiveContent(
            ClipboardEntrySummary(
                id: entry.id,
                contentKind: "text",
                preview: sample,
                isFavorite: entry.isFavorite,
                copiedAt: entry.timestamp,
                sourceUTIs: entry.sourceUTIs,
                sourceAppBundleID: entry.sourceAppBundleID,
                sensitivitySample: sample
            )
        )
    }
}
