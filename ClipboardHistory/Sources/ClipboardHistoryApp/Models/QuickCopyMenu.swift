import Foundation

struct QuickCopyMenuSection: Identifiable, Equatable {
    let title: String
    let entries: [ClipboardEntry]

    var id: String { title }
}

enum QuickCopyMenu {
    static let defaultLimit = 5

    static func sections(
        entries: [ClipboardEntry],
        limit: Int = defaultLimit
    ) -> [QuickCopyMenuSection] {
        [
            QuickCopyMenuSection(
                title: "最近复制",
                entries: Array(entries.prefix(limit))
            ),
            QuickCopyMenuSection(
                title: "收藏",
                entries: Array(entries.filter(\.isFavorite).prefix(limit))
            )
        ]
        .filter { !$0.entries.isEmpty }
    }
}
