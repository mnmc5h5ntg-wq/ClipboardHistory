import AppKit
import Foundation

struct FilePreview {
    enum Content {
        case image(NSImage)
        case text(String)
        case quickLook
        case fallback
    }

    let url: URL
    let thumbnail: StoredImage?
    let content: Content
}

enum FilePreviewLoader {
    static func load(url: URL, thumbnail: StoredImage?) -> FilePreview {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext),
           let image = NSImage(contentsOf: url) {
            return FilePreview(url: url, thumbnail: thumbnail, content: .image(image))
        }

        if FileTypeSupport.textExtensions.contains(ext),
           let text = try? String(contentsOf: url, encoding: .utf8) {
            return FilePreview(url: url, thumbnail: thumbnail, content: .text(text))
        }

        if FileTypeSupport.documentExtensions.contains(ext) || FileTypeSupport.videoExtensions.contains(ext) {
            return FilePreview(url: url, thumbnail: thumbnail, content: .quickLook)
        }

        return FilePreview(url: url, thumbnail: thumbnail, content: .fallback)
    }
}
