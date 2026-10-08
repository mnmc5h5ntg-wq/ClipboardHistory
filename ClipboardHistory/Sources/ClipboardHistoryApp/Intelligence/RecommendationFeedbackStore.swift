import Foundation

@MainActor
final class RecommendationFeedbackStore {
    static let storageKey = "RecommendationFeedbackStore.entries"
    static let maxStoredEntries = 500

    private let key: String
    private let defaults: UserDefaults
    private(set) var entries: [RecommendationFeedback] = []
    /// 本次启动是否把旧版"含剪贴板正文预览"的大 blob 收窄过。
    private(set) var didCompactLegacyBlob = false
    /// 收窄前后的字节数（仅诊断用；不记录任何正文）。
    private(set) var legacyBlobByteCount = 0

    init(defaults: UserDefaults = .standard, key: String = RecommendationFeedbackStore.storageKey) {
        self.defaults = defaults
        self.key = key
        loadAndCompactLegacyBlobIfNeeded()
    }

    /// 旧版本把完整 ContextSnapshot（含最多 500 条 ×160 字的剪贴板正文预览）写进
    /// UserDefaults，实测把 plist 撑到 66MB，每次启动都要在主线程解码它。
    /// 这里读一次（解码即自动丢弃正文）并立刻按瘦格式回写。
    private func loadAndCompactLegacyBlobIfNeeded() {
        guard let data = defaults.data(forKey: key) else { return }
        legacyBlobByteCount = data.count
        guard let decoded = try? JSONDecoder().decode([RecommendationFeedback].self, from: data) else {
            entries = []
            return
        }
        entries = decoded
        if let compacted = try? JSONEncoder().encode(entries), compacted.count < data.count {
            didCompactLegacyBlob = true
            defaults.set(compacted, forKey: key)
        }
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

    /// 删除/清空历史记录时同步剪掉对应反馈，
    /// 否则被删条目的正文片段会以反馈名义继续留存。
    func removeEntries(withIDs ids: Set<UUID>) {
        guard !ids.isEmpty else { return }
        let before = entries.count
        entries.removeAll { ids.contains($0.entryID) }
        guard entries.count != before else { return }
        persist()
    }

    func removeEntries(withID id: UUID) {
        removeEntries(withIDs: [id])
    }

    func reset() {
        entries.removeAll()
        persist()
    }

    enum ExportError: Error, Equatable {
        case noData
        case writingFailed(String)
    }

    /// 导出反馈（只含元数据，不含剪贴板正文）。失败必须让调用方看得见 ——
    /// 旧实现用 `try?` 吞掉写盘错误却仍返回 URL，界面于是显示"已导出"。
    func exportToFile() throws -> URL {
        let entries = self.entries
        guard !entries.isEmpty else { throw ExportError.noData }
        let dir = try exportDirectory()
        let fileURL = dir.appendingPathComponent("feedback_export_\(Self.exportStamp(from: Date())).jsonl")
        let encoder = JSONEncoder()
        let lines = try entries.map { entry in
            String(data: try encoder.encode(entry), encoding: .utf8) ?? ""
        }.filter { !$0.isEmpty }
        guard !lines.isEmpty else { throw ExportError.writingFailed("编码结果为空") }
        do {
            try lines.joined(separator: "\n").write(to: fileURL, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: fileURL.path)
        } catch {
            throw ExportError.writingFailed(String(describing: error))
        }
        return fileURL
    }

    private func exportDirectory() throws -> URL {
        guard let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else {
            throw ExportError.writingFailed("找不到 Application Support 目录")
        }
        let dir = base.appendingPathComponent("ClipboardHistory", isDirectory: true)
        try FileManager.default.createDirectory(
            at: dir,
            withIntermediateDirectories: true,
            attributes: [.posixPermissions: 0o700]
        )
        return dir
    }

    private static func exportStamp(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: date)
    }

    private func append(_ feedback: RecommendationFeedback) {
        // 存储前去掉正文类字段：反馈只需要"哪条记录、什么反馈、什么时候"。
        entries.append(feedback.withoutClipboardContent())
        if entries.count > Self.maxStoredEntries {
            entries.removeFirst(entries.count - Self.maxStoredEntries)
        }
        persist()
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(entries) else { return }
        defaults.set(data, forKey: key)
    }
}
