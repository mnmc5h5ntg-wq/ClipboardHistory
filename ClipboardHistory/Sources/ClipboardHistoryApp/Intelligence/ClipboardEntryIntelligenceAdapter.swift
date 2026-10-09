import Foundation

struct ClipboardEntryIntelligenceAdapter {
    // MARK: - 以字符串快照为输入的分析（可跨线程）

    func summary(for snapshot: ClipboardEntryRawSnapshot) -> ClipboardEntrySummary {
        ClipboardEntrySummary(
            id: snapshot.id,
            contentKind: contentKind(for: snapshot.kind),
            preview: preview(for: snapshot),
            isFavorite: snapshot.isFavorite,
            copiedAt: snapshot.timestamp,
            sourceUTIs: snapshot.sourceUTIs,
            sourceAppBundleID: snapshot.sourceAppBundleID,
            sensitivitySample: sensitivitySample(for: snapshot),
            sourceDirectoryPath: sourceDirectoryPath(for: snapshot.kind)
        )
    }

    func summaries(for snapshots: [ClipboardEntryRawSnapshot]) -> [ClipboardEntrySummary] {
        snapshots.map(summary(for:))
    }

    func intelligence(for snapshot: ClipboardEntryRawSnapshot, analyzedAt: Date? = nil) -> EntryIntelligence {
        let tags = tags(for: snapshot)
        return EntryIntelligence(
            entryID: snapshot.id,
            summary: intelligenceSummary(for: snapshot, tags: tags),
            tags: tags,
            detectedLanguage: nil,
            sensitivity: sensitivity(for: snapshot, tags: tags),
            embeddingStatus: embeddingStatus(for: snapshot.kind),
            lastAnalyzedAt: analyzedAt,
            source: .ruleBased
        )
    }

    private func text(of kind: ClipboardEntryRawSnapshot.Kind) -> String? {
        if case .text(let text) = kind { return text }
        return nil
    }

    private func preview(for snapshot: ClipboardEntryRawSnapshot) -> String {
        switch snapshot.kind {
        case .text(let string):
            return String(string.replacingOccurrences(of: "\n", with: " ↵ ").prefix(160))
        case .image(let description):
            return "图片 \(description)"
        case .file(let path):
            return URL(fileURLWithPath: path).lastPathComponent
        case .files(let paths):
            return paths.prefix(3).map { URL(fileURLWithPath: $0).lastPathComponent }.joined(separator: ", ")
        }
    }

    private func sensitivitySample(for snapshot: ClipboardEntryRawSnapshot) -> String {
        let text = self.text(of: snapshot.kind) ?? snapshot.ocrText ?? ""
        guard !text.isEmpty else { return "" }
        let end = text.index(
            text.startIndex,
            offsetBy: Self.sensitivitySampleLimit,
            limitedBy: text.endIndex
        ) ?? text.endIndex
        return String(text[text.startIndex..<end])
    }

    private func sourceDirectoryPath(for kind: ClipboardEntryRawSnapshot.Kind) -> String? {
        let path: String?
        switch kind {
        case .file(let single):
            path = single
        case .files(let many):
            path = many.first
        default:
            path = nil
        }
        guard let directory = path.map({ URL(fileURLWithPath: $0).deletingLastPathComponent().path }),
              !directory.isEmpty else { return nil }
        return directory
    }

    private func contentKind(for kind: ClipboardEntryRawSnapshot.Kind) -> String {
        switch kind {
        case .text(let text):
            if Self.urlDetector.matches(text) { return "url" }
            if Self.emailDetector.matches(text) { return "email" }
            if Self.shellCommandDetector.matches(text) { return "shell-command" }
            if Self.codeDetector.matches(text) { return "code" }
            return "text"
        case .image:
            return "image"
        case .file(let path):
            return fileKind(for: URL(fileURLWithPath: path))
        case .files:
            return "files"
        }
    }

    private func tags(for snapshot: ClipboardEntryRawSnapshot) -> [EntryIntelligenceTag] {
        var tags = Set<EntryIntelligenceTag>()
        switch snapshot.kind {
        case .text(let text):
            tags.insert(.plainText)
            if Self.urlDetector.matches(text) { tags.insert(.url) }
            if Self.emailDetector.matches(text) { tags.insert(.email) }
            if Self.phoneDetector.matches(text) { tags.insert(.phoneNumber) }
            if Self.shellCommandDetector.matches(text) { tags.insert(.shellCommand) }
            if Self.codeDetector.matches(text) { tags.insert(.code) }
            if Self.filePathDetector.matches(text) { tags.insert(.filePath) }
            if Self.passwordDetector.matches(text) { tags.insert(.passwordCandidate) }
            if Self.verificationCodeDetector.matches(text) { tags.insert(.verificationCode) }
            if Self.apiKeyDetector.matches(text) { tags.insert(.apiKeyCandidate) }
        case .image:
            tags.insert(.image)
        case .file(let path):
            tags.formUnion(fileTags(for: URL(fileURLWithPath: path)))
        case .files(let paths):
            paths.map { URL(fileURLWithPath: $0) }.forEach { tags.formUnion(fileTags(for: $0)) }
        }
        return tags.sorted { $0.rawValue < $1.rawValue }
    }

    private func intelligenceSummary(for snapshot: ClipboardEntryRawSnapshot, tags: [EntryIntelligenceTag]) -> String? {
        switch snapshot.kind {
        case .text(let text):
            let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { return nil }
            return String(trimmed.replacingOccurrences(of: "\n", with: " ").prefix(80))
        case .image:
            return "图片内容"
        case .file(let path):
            return "文件：\(URL(fileURLWithPath: path).lastPathComponent)"
        case .files(let paths):
            return "\(paths.count) 个文件"
        }
    }

    private func sensitivity(for snapshot: ClipboardEntryRawSnapshot, tags: [EntryIntelligenceTag]) -> AIPrivacySensitivity {
        if tags.contains(.apiKeyCandidate) || tags.contains(.passwordCandidate) {
            return .secret
        }
        if tags.contains(.verificationCode) {
            return .sensitive
        }
        switch snapshot.kind {
        case .text(let text):
            return text.count > 240 ? .personal : .publicLike
        case .image:
            return .sensitive
        case .file, .files:
            return .personal
        }
    }

    private func embeddingStatus(for kind: ClipboardEntryRawSnapshot.Kind) -> EmbeddingStatus {
        switch kind {
        case .text:
            return .notRequested
        case .image:
            return .unavailable(reason: "图片内容暂不生成文本向量。")
        case .file, .files:
            return .notRequested
        }
    }

    // MARK: - 兼容入口（以 ClipboardEntry 为输入，内部转成字符串快照）

    /// 敏感判定样本上限：8KB。够覆盖真实密钥/令牌出现的位置，又把每次分析的代价封在有界范围内。
    static let sensitivitySampleLimit = 8_192

    func summary(for entry: ClipboardEntry) -> ClipboardEntrySummary {
        summary(for: entry.analysisSnapshot)
    }

    func summaries(for entries: [ClipboardEntry]) -> [ClipboardEntrySummary] {
        entries.map { summary(for: $0.analysisSnapshot) }
    }

    func intelligence(for entry: ClipboardEntry, analyzedAt: Date? = nil) -> EntryIntelligence {
        intelligence(for: entry.analysisSnapshot, analyzedAt: analyzedAt)
    }

    /// 存档可能被手改、或从半截恢复里出现"同 id 两条"（`HistoryStore.collapsingDuplicates` 只按**内容**合并，
    /// 同 id 不同内容会原样留下）。`Dictionary(uniqueKeysWithValues:)` 对重复键是 `fatalError`，
    /// 而这条路径每次预测刷新（菜单打开 / 新复制 / 前台切换）都会走 ⇒ 一次刷新就能把进程 trap 掉。
    /// 所以这里**保留首条**，既不崩也不会为重复项重复算一遍 intelligence。
    func intelligenceByEntryID(for entries: [ClipboardEntry], analyzedAt: Date? = nil) -> [UUID: EntryIntelligence] {
        entries.reduce(into: [UUID: EntryIntelligence]()) { result, entry in
            guard result[entry.id] == nil else { return }
            result[entry.id] = intelligence(for: entry.analysisSnapshot, analyzedAt: analyzedAt)
        }
    }

    func intelligenceByEntryID(for snapshots: [ClipboardEntryRawSnapshot], analyzedAt: Date? = nil) -> [UUID: EntryIntelligence] {
        snapshots.reduce(into: [UUID: EntryIntelligence]()) { result, snapshot in
            guard result[snapshot.id] == nil else { return }
            result[snapshot.id] = intelligence(for: snapshot, analyzedAt: analyzedAt)
        }
    }

    private func contentKind(for content: ClipboardEntryContent) -> String {
        switch content {
        case .text(let text):
            if Self.urlDetector.matches(text) { return "url" }
            if Self.emailDetector.matches(text) { return "email" }
            if Self.shellCommandDetector.matches(text) { return "shell-command" }
            if Self.codeDetector.matches(text) { return "code" }
            return "text"
        case .image:
            return "image"
        case .file(let url):
            return fileKind(for: url)
        case .files:
            return "files"
        }
    }











    private func fileKind(for url: URL) -> String {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext) { return "image-file" }
        if FileTypeSupport.videoExtensions.contains(ext) { return "video-file" }
        return "file"
    }

    private func fileTags(for url: URL) -> Set<EntryIntelligenceTag> {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext) { return [.image] }
        if FileTypeSupport.videoExtensions.contains(ext) { return [.video] }
        if FileTypeSupport.documentExtensions.contains(ext) || Self.documentExtensions.contains(ext) { return [.document] }
        if Self.archiveExtensions.contains(ext) { return [.archive] }
        return [.filePath]
    }
}

private extension ClipboardEntryIntelligenceAdapter {
    static let documentExtensions: Set<String> = [
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "pages", "numbers", "key", "txt", "md", "rtf"
    ]

    static let archiveExtensions: Set<String> = ["zip", "rar", "7z", "tar", "gz", "dmg"]

    static let urlDetector = TextPatternDetector(pattern: #"https?://|www\."#)
    static let emailDetector = TextPatternDetector(pattern: #"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"#, options: [.caseInsensitive])
    static let phoneDetector = TextPatternDetector(pattern: #"(?<!\d)(?:\+?\d[\d\s-]{6,}\d)(?!\d)"#)
    static let shellCommandDetector = TextPatternDetector(pattern: #"^\s*(cd|ls|git|swift|make|npm|pnpm|python3?|curl|brew|xcodebuild)\b"#, options: [.anchorsMatchLines])
    static let codeDetector = TextPatternDetector(pattern: #"\b(import|func|struct|class|enum|let|var|return|if|else|for|while)\b|[{};]"#)
    static let filePathDetector = TextPatternDetector(pattern: #"(/Users/|~/|\./|\.\./)[^\n]+"#)
    static let passwordDetector = TextPatternDetector(pattern: #"(?i)\b(password|passwd|pwd|密码)\b\s*[:=]"#)
    /// 旧规则 `\d{6}` 会把房间号、订单片段一律标成验证码（⇒ sensitivity=.sensitive ⇒ 被降权）。
    static let verificationCodeDetector = TextPatternDetector(
        pattern: #"(?i)(?:验证码|校验码|动态码|短信码|verification code|otp code)\D{0,8}\d{4,8}\b"#
    )
    static let apiKeyDetector = TextPatternDetector(pattern: #"\b(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"#)
}

private struct TextPatternDetector {
    private let regex: NSRegularExpression?

    init(pattern: String, options: NSRegularExpression.Options = []) {
        regex = try? NSRegularExpression(pattern: pattern, options: options)
    }

    func matches(_ text: String) -> Bool {
        guard let regex else { return false }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        return regex.firstMatch(in: text, range: range) != nil
    }
}
