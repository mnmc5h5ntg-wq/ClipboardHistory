import Foundation

enum ClipboardEntryContent: Equatable, Hashable {
    case text(String)
    case image(StoredImage)
    case file(URL)

    var preview: String {
        switch self {
        case .text(let string):
            let text = string.replacingOccurrences(of: "\n", with: " ↵ ")
            return String(text.prefix(60)) + (text.count > 60 ? "…" : "")
        case .image(let image):
            return "图片 \(Int(image.nsImage.size.width))×\(Int(image.nsImage.size.height))"
        case .file(let url):
            return "📄 \(url.lastPathComponent)"
        }
    }

    var sizeDescription: String {
        switch self {
        case .text(let string):
            return "\(string.count) 个字符"
        case .image(let image):
            return "\(Int(image.nsImage.size.width)) × \(Int(image.nsImage.size.height)) 像素"
        case .file(let url):
            return "文件: \(url.path)"
        }
    }

    var sourceURL: URL? {
        if case .file(let url) = self { return url }
        return nil
    }
}
