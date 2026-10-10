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

    /// OCR 关心的"这条里有没有可识别的图"：图片本身，或扩展名像图片的文件。
    /// 判据放这儿是为了让 `OCRPolicy.shouldSchedule` 真的被调用，而不是摆着好看。
    static let ocrCapableFileExtensions: Set<String> = [
        "png", "jpg", "jpeg", "heic", "tif", "tiff", "gif", "bmp",
    ]

    var isOCRTarget: Bool {
        switch self {
        case .image:
            return true
        case .file(let url):
            return ClipboardEntryContent.ocrCapableFileExtensions.contains(url.pathExtension.lowercased())
        case .files:
            return false
        case .text:
            return false
        }
    }

    var sourceURL: URL? {
        if case .file(let url) = self { return url }
        if case .files(let urls) = self { return urls.first }
        return nil
    }
}
