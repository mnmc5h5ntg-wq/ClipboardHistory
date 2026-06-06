import Foundation

struct ClipboardEntry: Identifiable, Equatable, Hashable {
    let id = UUID()
    let content: ClipboardEntryContent
    let timestamp: Date
    let thumbnail: StoredImage?
    let sourceURL: URL?
    let sourceUTIs: [String]

    var shortPreview: String {
        content.preview
    }
}
