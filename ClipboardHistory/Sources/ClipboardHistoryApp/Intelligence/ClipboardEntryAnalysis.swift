import Foundation

/// 只含字符串的分析快照：可以安全地交给后台线程。
///
/// 取代旧写法——过去把整个 `[ClipboardEntry]`（其 `.image` 分支带着 `NSImage`）
/// 送进 `Task.detached`，靠 `@unchecked Sendable` 才编得过（审计 R-19：
/// "已修复"其实只是被静音）。
struct ClipboardEntryRawSnapshot: Sendable, Hashable {
    enum Kind: Sendable, Hashable {
        case text(String)
        case image(pixelDescription: String)
        case file(path: String)
        case files(paths: [String])
    }

    let id: UUID
    let kind: Kind
    let timestamp: Date
    let isFavorite: Bool
    let sourceUTIs: [String]
    let sourceAppBundleID: String?
    let sourceAppName: String?
    let ocrText: String?
}

extension ClipboardEntry {
    /// 在主线程构建（只有这里需要碰 `NSImage` 拿尺寸），之后所有正则分析都在后台。
    var analysisSnapshot: ClipboardEntryRawSnapshot {
        let kind: ClipboardEntryRawSnapshot.Kind
        switch content {
        case .text(let text):
            kind = .text(text)
        case .image(let image):
            let size = image.nsImage.size
            kind = .image(pixelDescription: "\(Int(size.width))×\(Int(size.height))")
        case .file(let url):
            kind = .file(path: url.path)
        case .files(let urls):
            kind = .files(paths: urls.map(\.path))
        }
        return ClipboardEntryRawSnapshot(
            id: id,
            kind: kind,
            timestamp: timestamp,
            isFavorite: isFavorite,
            sourceUTIs: sourceUTIs,
            sourceAppBundleID: sourceAppBundleID,
            sourceAppName: sourceAppName,
            ocrText: ocrText
        )
    }
}
