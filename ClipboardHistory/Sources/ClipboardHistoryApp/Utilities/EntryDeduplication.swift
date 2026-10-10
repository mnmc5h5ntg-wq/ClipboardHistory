import Foundation

/// 相邻重复记录的判定与合并（第三轮审计 C-5：从 `HistoryStore` 里搬出来的纯逻辑）。
///
/// 这块判据以前散在 Store 的私有静态方法里，只有靠"整个 store 跑一遍"才能间接观察到；
/// 搬出来之后它可以被逐条真值表钉住，Store 也真的变小了 —— 这正是"只减不加"那条守卫
/// 想要的形状：**不是把守卫调松，是把逻辑搬对地方**。
enum EntryDeduplication {
    /// 与原 `HistoryStore.Entry` 同一个类型；搬出来后要用真实类型名，
    /// 保留别名是为了让函数体逐字不变（少一处可能改错的地方）。
    typealias Entry = ClipboardEntry

    static func collapsingDuplicates(in entries: [Entry]) -> [Entry] {
        entries.reduce(into: []) { collapsedEntries, entry in
            guard let existingIndex = collapsedEntries.firstIndex(where: { isDuplicate($0, of: entry) }) else {
                collapsedEntries.append(entry)
                return
            }

            collapsedEntries[existingIndex] = collapsedEntries[existingIndex]
                .updating(isFavorite: collapsedEntries[existingIndex].isFavorite || entry.isFavorite)
        }
    }

    static func isDuplicate(_ entry: Entry, of intakeEntry: ClipboardIntake.Entry) -> Bool {
        hasSameDuplicateIdentity(
            content: entry.content,
            thumbnail: entry.thumbnail,
            as: intakeEntry.content,
            thumbnail: intakeEntry.thumbnail
        )
    }

    static func isDuplicate(_ lhs: Entry, of rhs: Entry) -> Bool {
        hasSameDuplicateIdentity(
            content: lhs.content,
            thumbnail: lhs.thumbnail,
            as: rhs.content,
            thumbnail: rhs.thumbnail
        )
    }

    static func hasSameDuplicateIdentity(
        content lhsContent: ClipboardEntryContent,
        thumbnail lhsThumbnail: StoredImage?,
        as rhsContent: ClipboardEntryContent,
        thumbnail rhsThumbnail: StoredImage?
    ) -> Bool {
        if lhsContent == rhsContent {
            return true
        }

        guard let lhsImage = duplicateImageIdentity(for: lhsContent, thumbnail: lhsThumbnail),
              let rhsImage = duplicateImageIdentity(for: rhsContent, thumbnail: rhsThumbnail) else {
            return false
        }
        return lhsImage == rhsImage
    }

    static func duplicateImageIdentity(
        for content: ClipboardEntryContent,
        thumbnail: StoredImage?
    ) -> StoredImage? {
        switch content {
        case .image(let image):
            return image
        case .file(let url) where FileTypeSupport.imageExtensions.contains(url.pathExtension.lowercased()):
            return thumbnail
        case .files, .file, .text:
            return nil
        }
    }

    static func mergedEntry(
        from duplicateEntry: Entry,
        replacingWith intakeEntry: ClipboardIntake.Entry,
        timestamp: Date,
        isFavorite: Bool
    ) -> Entry {
        Entry(
            id: duplicateEntry.id,
            content: intakeEntry.content,
            timestamp: timestamp,
            thumbnail: intakeEntry.thumbnail ?? duplicateEntry.thumbnail,
            sourceURL: intakeEntry.content.sourceURL,
            isFavorite: isFavorite,
            sourceUTIs: intakeEntry.sourceUTIs.isEmpty ? duplicateEntry.sourceUTIs : intakeEntry.sourceUTIs,
            sourceAppBundleID: intakeEntry.sourceAppBundleID ?? duplicateEntry.sourceAppBundleID,
            sourceAppName: intakeEntry.sourceAppName ?? duplicateEntry.sourceAppName,
            ocrText: duplicateEntry.ocrText
        )
    }
}
