import Foundation

@MainActor
final class RecommendationFeedbackStore {
    private let key = "RecommendationFeedbackStore.entries"

    private(set) var entries: [RecommendationFeedback] = []

    init() {
        guard let data = UserDefaults.standard.data(forKey: key),
              let decoded = try? JSONDecoder().decode([RecommendationFeedback].self, from: data) else {
            return
        }
        entries = decoded
    }

    func recordAccepted(entryID: UUID, context: ContextSnapshot) {
        append(.init(entryID: entryID, kind: .accepted, context: context, createdAt: Date()))
    }

    func recordIgnored(entryID: UUID, context: ContextSnapshot) {
        append(.init(entryID: entryID, kind: .ignored, context: context, createdAt: Date()))
    }

    func recordCopiedManually(entryID: UUID, context: ContextSnapshot) {
        append(.init(entryID: entryID, kind: .copiedManually, context: context, createdAt: Date()))
    }

    func recordDismissed(entryID: UUID, context: ContextSnapshot) {
        append(.init(entryID: entryID, kind: .dismissed, context: context, createdAt: Date()))
    }

    func recordReverted(entryID: UUID, context: ContextSnapshot) {
        append(.init(entryID: entryID, kind: .reverted, context: context, createdAt: Date()))
    }

    func forEntry(_ entryID: UUID) -> [RecommendationFeedback] {
        entries.filter { $0.entryID == entryID }
    }

    func recent(limit: Int = 200) -> [RecommendationFeedback] {
        Array(entries.suffix(limit))
    }

    func reset() {
        entries.removeAll()
        persist()
    }

    func exportToFile() -> URL? {
        let entries = self.entries
        guard !entries.isEmpty else { return nil }
        guard let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?            .appendingPathComponent("ClipboardHistory") else { return nil }
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        let fileURL = dir.appendingPathComponent("feedback_export_\(ISO8601DateFormatter().string(from: Date())).jsonl")
        let lines = entries.map { entry -> String in
            guard let data = try? JSONEncoder().encode(entry),
                  let json = String(data: data, encoding: .utf8) else { return "" }
            return json
        }.filter { !$0.isEmpty }
        let content = lines.joined(separator: "\n")
        try? content.write(to: fileURL, atomically: true, encoding: .utf8)
        // 设置文件仅 owner 可读写
        try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: fileURL.path)
        return fileURL
    }

    private func append(_ feedback: RecommendationFeedback) {
        entries.append(feedback)
        if entries.count > 500 {
            entries.removeFirst(entries.count - 500)
        }
        persist()
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(entries) else { return }
        UserDefaults.standard.set(data, forKey: key)
    }
}
