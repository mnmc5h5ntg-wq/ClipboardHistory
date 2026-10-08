import Foundation

struct ClipboardEntryIntelligenceAdapter {
    func summary(for entry: ClipboardEntry) -> ClipboardEntrySummary {
        ClipboardEntrySummary(
            id: entry.id,
            contentKind: contentKind(for: entry.content),
            preview: preview(for: entry),
            isFavorite: entry.isFavorite,
            copiedAt: entry.timestamp,
            sourceUTIs: entry.sourceUTIs,
            sourceAppBundleID: entry.sourceAppBundleID
        )
    }

    func summaries(for entries: [ClipboardEntry]) -> [ClipboardEntrySummary] {
        entries.map(summary(for:))
    }

    func intelligence(for entry: ClipboardEntry, analyzedAt: Date? = nil) -> EntryIntelligence {
        let tags = tags(for: entry)
        return EntryIntelligence(
            entryID: entry.id,
            summary: intelligenceSummary(for: entry, tags: tags),
            tags: tags,
            detectedLanguage: nil,
            sensitivity: sensitivity(for: entry, tags: tags),
            embeddingStatus: embeddingStatus(for: entry),
            lastAnalyzedAt: analyzedAt,
            source: .ruleBased
        )
    }

    func intelligenceByEntryID(for entries: [ClipboardEntry], analyzedAt: Date? = nil) -> [UUID: EntryIntelligence] {
        Dictionary(uniqueKeysWithValues: entries.map { entry in
            (entry.id, intelligence(for: entry, analyzedAt: analyzedAt))
        })
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

    private func preview(for entry: ClipboardEntry) -> String {
        switch entry.content {
        case .text(let string):
            return String(string.replacingOccurrences(of: "\n", with: " ↵ ").prefix(160))
        case .image:
            return entry.shortPreview
        case .file(let url):
            return url.lastPathComponent
        case .files(let urls):
            return urls.map(\.lastPathComponent).prefix(3).joined(separator: ", ")
        }
    }

    private func tags(for entry: ClipboardEntry) -> [EntryIntelligenceTag] {
        var tags = Set<EntryIntelligenceTag>()
        switch entry.content {
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
        case .file(let url):
            tags.formUnion(fileTags(for: url))
        case .files(let urls):
            urls.forEach { tags.formUnion(fileTags(for: $0)) }
        }
        return tags.sorted { $0.rawValue < $1.rawValue }
    }

    private func intelligenceSummary(for entry: ClipboardEntry, tags: [EntryIntelligenceTag]) -> String? {
        switch entry.content {
        case .text(let text):
            let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { return nil }
            return String(trimmed.replacingOccurrences(of: "\n", with: " ").prefix(80))
        case .image:
            return "图片内容"
        case .file(let url):
            return "文件：\(url.lastPathComponent)"
        case .files(let urls):
            return "\(urls.count) 个文件"
        }
    }

    private func sensitivity(for entry: ClipboardEntry, tags: [EntryIntelligenceTag]) -> AIPrivacySensitivity {
        if tags.contains(.apiKeyCandidate) || tags.contains(.passwordCandidate) {
            return .secret
        }
        if tags.contains(.verificationCode) {
            return .sensitive
        }
        switch entry.content {
        case .text(let text):
            return text.count > 240 ? .personal : .publicLike
        case .image:
            return .sensitive
        case .file, .files:
            return .personal
        }
    }

    private func embeddingStatus(for entry: ClipboardEntry) -> EmbeddingStatus {
        switch entry.content {
        case .text:
            return .notRequested
        case .image:
            return .unavailable(reason: "图片内容暂不生成文本向量。")
        case .file, .files:
            return .notRequested
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
    static let verificationCodeDetector = TextPatternDetector(pattern: #"(?<!\d)\d{6}(?!\d)"#)
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
