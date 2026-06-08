import AppKit
import Foundation

struct FilePreview {
    enum Content {
        case image(NSImage)
        case text(String)
        case video
        case quickLook
        case fallback
    }

    let url: URL
    let thumbnail: StoredImage?
    let content: Content
    let videoAspectRatio: CGFloat?

    init(
        url: URL,
        thumbnail: StoredImage?,
        content: Content,
        videoAspectRatio: CGFloat? = nil
    ) {
        self.url = url
        self.thumbnail = thumbnail
        self.content = content
        self.videoAspectRatio = videoAspectRatio
    }
}
