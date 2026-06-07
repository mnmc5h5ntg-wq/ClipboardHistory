import Foundation

enum ClipboardEntryContent: Equatable, Hashable {
    case text(String)
    case image(StoredImage)
    case file(URL)

    var preview: String {
        EntryPresentation.preview(for: self)
    }

    var sizeDescription: String {
        EntryPresentation.sizeDescription(for: self)
    }

    var sourceURL: URL? {
        if case .file(let url) = self { return url }
        return nil
    }
}
