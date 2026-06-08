import AppKit
import AVFoundation
import Foundation

enum MediaLoadingState<Value> {
    case loading
    case success(Value)
    case failure(String)
}

extension MediaLoadingState: Sendable where Value: Sendable {}

enum FilePreviewPayload: Sendable {
    case imageData(Data)
    case text(String)
    case video(CGFloat?)
    case quickLook
    case fallback
}

@MainActor
final class MediaLoadHandle {
    private let task: Task<MediaLoadingState<FilePreviewPayload>, Never>
    private let url: URL
    private let thumbnail: StoredImage?

    var value: MediaLoadingState<FilePreview> {
        get async {
            let payloadState = await task.value
            switch payloadState {
            case .loading:
                return .loading
            case .failure(let message):
                return .failure(message)
            case .success(let payload):
                guard let preview = MediaLoader.filePreview(from: payload, url: url, thumbnail: thumbnail) else {
                    return .failure(MediaLoader.failureMessage)
                }
                return .success(preview)
            }
        }
    }

    init(
        task: Task<MediaLoadingState<FilePreviewPayload>, Never>,
        url: URL,
        thumbnail: StoredImage?
    ) {
        self.task = task
        self.url = url
        self.thumbnail = thumbnail
    }

    func cancel() {
        task.cancel()
    }
}

enum MediaLoader {
    typealias FilePreviewResolver = @Sendable (URL) async -> FilePreviewPayload?

    static let cancellationMessage = "预览加载已取消"
    static let failureMessage = "无法加载预览"
    static let missingFileMessage = "文件已移动或删除，无法加载预览"

    @MainActor
    static func loadFilePreview(url: URL, thumbnail: StoredImage?) async -> MediaLoadingState<FilePreview> {
        await loadFilePreviewHandle(url: url, thumbnail: thumbnail).value
    }

    @MainActor
    static func loadFilePreviewHandle(
        url: URL,
        thumbnail: StoredImage?,
        resolver: @escaping FilePreviewResolver = defaultFilePreviewResolver
    ) -> MediaLoadHandle {
        MediaLoadHandle(
            task: Task.detached(priority: .userInitiated) {
                guard !Task.isCancelled else {
                    return .failure(cancellationMessage)
                }

                guard FileManager.default.fileExists(atPath: url.path) else {
                    return .failure(missingFileMessage)
                }

                guard let preview = await resolver(url) else {
                    if Task.isCancelled {
                        return .failure(cancellationMessage)
                    }
                    return .failure(failureMessage)
                }

                guard !Task.isCancelled else {
                    return .failure(cancellationMessage)
                }
                return .success(preview)
            },
            url: url,
            thumbnail: thumbnail
        )
    }

    @MainActor
    static func loadFilePreviewSync(url: URL, thumbnail: StoredImage?) -> FilePreview? {
        guard FileManager.default.fileExists(atPath: url.path) else {
            return nil
        }

        guard let payload = filePreviewPayloadSync(url: url) else {
            return nil
        }

        return filePreview(from: payload, url: url, thumbnail: thumbnail)
    }

    nonisolated static func filePreviewPayloadSync(url: URL) -> FilePreviewPayload? {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext),
           let data = try? Data(contentsOf: url) {
            return .imageData(data)
        }

        if FileTypeSupport.textExtensions.contains(ext),
           let text = try? String(contentsOf: url, encoding: .utf8) {
            return .text(text)
        }

        if FileTypeSupport.videoExtensions.contains(ext) {
            return .video(VideoAspectRatioResolver.aspectRatio(for: url))
        }

        if FileTypeSupport.documentExtensions.contains(ext) {
            return .quickLook
        }

        return .fallback
    }

    @MainActor
    static func filePreview(
        from payload: FilePreviewPayload,
        url: URL,
        thumbnail: StoredImage?
    ) -> FilePreview? {
        switch payload {
        case .imageData(let data):
            guard let image = NSImage(data: data) else { return nil }
            return FilePreview(url: url, thumbnail: thumbnail, content: .image(image))
        case .text(let text):
            return FilePreview(url: url, thumbnail: thumbnail, content: .text(text))
        case .video(let aspectRatio):
            return FilePreview(
                url: url,
                thumbnail: thumbnail,
                content: .video,
                videoAspectRatio: aspectRatio
            )
        case .quickLook:
            return FilePreview(url: url, thumbnail: thumbnail, content: .quickLook)
        case .fallback:
            return FilePreview(url: url, thumbnail: thumbnail, content: .fallback)
        }
    }

    nonisolated private static func defaultFilePreviewResolver(url: URL) async -> FilePreviewPayload? {
        filePreviewPayloadSync(url: url)
    }
}

enum VideoAspectRatioResolver {
    static let fallbackAspectRatio: CGFloat = 16.0 / 9.0

    static func aspectRatio(
        naturalSize: CGSize,
        preferredTransform: CGAffineTransform = .identity
    ) -> CGFloat? {
        let transformedSize = naturalSize.applying(preferredTransform)
        let width = abs(transformedSize.width)
        let height = abs(transformedSize.height)
        guard width > 0, height > 0 else { return nil }
        return width / height
    }

    static func aspectRatio(for url: URL) -> CGFloat? {
        let asset = AVURLAsset(url: url)
        guard let track = asset.tracks(withMediaType: .video).first else {
            return nil
        }
        return aspectRatio(
            naturalSize: track.naturalSize,
            preferredTransform: track.preferredTransform
        )
    }
}
