import Foundation

struct ClipboardEntry: Identifiable, Equatable, Hashable {
    let id: UUID
    let content: ClipboardEntryContent
    let timestamp: Date
    let thumbnail: StoredImage?
    let sourceURL: URL?
    let isFavorite: Bool
    let sourceUTIs: [String]

    init(
        id: UUID = UUID(),
        content: ClipboardEntryContent,
        timestamp: Date,
        thumbnail: StoredImage?,
        sourceURL: URL?,
        isFavorite: Bool = false,
        sourceUTIs: [String]
    ) {
        self.id = id
        self.content = content
        self.timestamp = timestamp
        self.thumbnail = thumbnail
        self.sourceURL = sourceURL
        self.isFavorite = isFavorite
        self.sourceUTIs = sourceUTIs
    }

    var shortPreview: String {
        content.preview
    }

    func updating(timestamp: Date? = nil, isFavorite: Bool? = nil) -> ClipboardEntry {
        ClipboardEntry(
            id: id,
            content: content,
            timestamp: timestamp ?? self.timestamp,
            thumbnail: thumbnail,
            sourceURL: sourceURL,
            isFavorite: isFavorite ?? self.isFavorite,
            sourceUTIs: sourceUTIs
        )
    }
}
