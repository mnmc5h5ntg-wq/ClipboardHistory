import Foundation

enum ClipboardEntryContent: Equatable, Hashable {
    case text(String)
    case image(StoredImage)
    case file(URL)
    case files([URL])

    var preview: String {
        EntryPresentation.preview(for: self)
    }

    var sizeDescription: String {
        EntryPresentation.sizeDescription(for: self)
    }

    var sourceURL: URL? {
        if case .file(let url) = self { return url }
        if case .files(let urls) = self { return urls.first }
        return nil
    }
}
