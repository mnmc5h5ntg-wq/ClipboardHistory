import Foundation

struct ClipboardEntry: Identifiable, Equatable, Hashable, @unchecked Sendable {
    let id: UUID
    let content: ClipboardEntryContent
    let timestamp: Date
    let thumbnail: StoredImage?
    let sourceURL: URL?
    let isFavorite: Bool
    let sourceUTIs: [String]
    let sourceAppBundleID: String?
    let sourceAppName: String?
    let ocrText: String?

    init(
        id: UUID = UUID(),
        content: ClipboardEntryContent,
        timestamp: Date,
        thumbnail: StoredImage?,
        sourceURL: URL?,
        isFavorite: Bool = false,
        sourceUTIs: [String],
        sourceAppBundleID: String? = nil,
        sourceAppName: String? = nil,
        ocrText: String? = nil
    ) {
        self.id = id
        self.content = content
        self.timestamp = timestamp
        self.thumbnail = thumbnail
        self.sourceURL = sourceURL
        self.isFavorite = isFavorite
        self.sourceUTIs = sourceUTIs
        self.sourceAppBundleID = sourceAppBundleID
        self.sourceAppName = sourceAppName
        self.ocrText = ocrText
    }

    var shortPreview: String {
        content.preview
    }

    func updating(
        timestamp: Date? = nil,
        isFavorite: Bool? = nil,
        ocrText: String?? = nil,
        thumbnail: StoredImage?? = nil
    ) -> ClipboardEntry {
        ClipboardEntry(
            id: id,
            content: content,
            timestamp: timestamp ?? self.timestamp,
            thumbnail: thumbnail ?? self.thumbnail,
            sourceURL: sourceURL,
            isFavorite: isFavorite ?? self.isFavorite,
            sourceUTIs: sourceUTIs,
            sourceAppBundleID: sourceAppBundleID,
            sourceAppName: sourceAppName,
            ocrText: ocrText ?? self.ocrText
        )
    }
}
