import AppKit
import AVFoundation

struct ClipboardIntake {
    struct Entry {
        let content: ClipboardEntryContent
        let thumbnail: StoredImage?
        let sourceUTIs: [String]

        func makeHistoryEntry(timestamp: Date = Date()) -> ClipboardEntry {
            ClipboardEntry(
                content: content,
                timestamp: timestamp,
                thumbnail: thumbnail,
                sourceURL: content.sourceURL,
                sourceUTIs: sourceUTIs
            )
        }

        func makeHistoryEntry(unlessDuplicateOf latestEntry: ClipboardEntry?) -> ClipboardEntry? {
            guard latestEntry?.content != content else { return nil }
            return makeHistoryEntry()
        }
    }

    private var lastChangeCount: Int

    init(pasteboard: NSPasteboard = .general) {
        self.lastChangeCount = pasteboard.changeCount
    }

    mutating func refresh(from pasteboard: NSPasteboard = .general) -> Entry? {
        lastChangeCount = pasteboard.changeCount
        return readEntry(from: pasteboard)
    }

    mutating func markCurrentChangeCount(from pasteboard: NSPasteboard = .general) {
        lastChangeCount = pasteboard.changeCount
    }

    mutating func readChangedEntry(from pasteboard: NSPasteboard = .general) -> Entry? {
        guard pasteboard.changeCount != lastChangeCount else { return nil }
        lastChangeCount = pasteboard.changeCount
        return readEntry(from: pasteboard)
    }

    /// 统一入口：file-url → png → tiff → text
    private func readEntry(from pasteboard: NSPasteboard) -> Entry? {
        if let url = readFileURL(from: pasteboard) {
            var thumb = thumbnailForFile(at: url)
            if thumb == nil {
                if let tiff = pasteboard.data(forType: .tiff),
                   let img = NSImage(data: tiff) {
                    thumb = StoredImage(img)
                } else if let icnsData = pasteboard.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                          let img = NSImage(data: icnsData) {
                    thumb = StoredImage(img)
                }
            }
            return makeEntry(content: .file(url), thumbnail: thumb, pasteboard: pasteboard)
        }

        if let pngData = pasteboard.data(forType: .png),
           let image = NSImage(data: pngData) {
            let stored = StoredImage(image)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let tiffData = pasteboard.data(forType: .tiff),
           let image = NSImage(data: tiffData) {
            let stored = StoredImage(image)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let t = pasteboard.string(forType: .string),
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return makeEntry(content: .text(t), thumbnail: nil, pasteboard: pasteboard)
        }

        return nil
    }

    private func makeEntry(
        content: ClipboardEntryContent,
        thumbnail: StoredImage?,
        pasteboard: NSPasteboard
    ) -> Entry {
        Entry(
            content: content,
            thumbnail: thumbnail,
            sourceUTIs: (pasteboard.types ?? []).map { $0.rawValue }
        )
    }

    private func readFileURL(from pb: NSPasteboard) -> URL? {
        if let urls = pb.readObjects(forClasses: [NSURL.self], options: nil) as? [URL],
           let url = urls.first {
            return url
        }
        if let urlString = pb.string(forType: .fileURL),
           let url = URL(string: urlString) {
            return url
        }
        return nil
    }

    private func thumbnailForFile(at url: URL) -> StoredImage? {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext), let image = NSImage(contentsOf: url) {
            return StoredImage(scaledImage(image, maxPixelSize: 512))
        }
        if FileTypeSupport.videoExtensions.contains(ext), let image = videoThumbnail(for: url) {
            return StoredImage(scaledImage(image, maxPixelSize: 512))
        }
        return nil
    }

    private func videoThumbnail(for url: URL) -> NSImage? {
        let asset = AVURLAsset(url: url)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 512, height: 512)
        let time = CMTime(seconds: 0.1, preferredTimescale: 600)

        if #available(macOS 15, *) {
            let semaphore = DispatchSemaphore(value: 0)
            let lock = NSLock()
            final class ThumbnailResult: @unchecked Sendable {
                var thumbnail: NSImage?
                var error: Error?
            }
            let result = ThumbnailResult()
            generator.generateCGImageAsynchronously(for: time) { cgImage, _, error in
                lock.lock()
                if let cgImage {
                    result.thumbnail = image(from: cgImage)
                } else {
                    result.error = error
                }
                lock.unlock()
                semaphore.signal()
            }
            semaphore.wait()
            lock.lock()
            let thumbnail = result.thumbnail
            lock.unlock()
            if let thumbnail { return thumbnail }
            return nil
        }

        do {
            let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
            return image(from: cgImage)
        } catch {
            return nil
        }
    }

    private func image(from cgImage: CGImage) -> NSImage {
        NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
    }

    private func scaledImage(_ image: NSImage, maxPixelSize: CGFloat) -> NSImage {
        let width = image.size.width
        let height = image.size.height
        guard width > maxPixelSize || height > maxPixelSize else { return image }

        let scale = min(maxPixelSize / width, maxPixelSize / height)
        let targetSize = NSSize(width: width * scale, height: height * scale)
        let scaled = NSImage(size: targetSize)
        scaled.lockFocus()
        image.draw(
            in: NSRect(origin: .zero, size: targetSize),
            from: NSRect(origin: .zero, size: image.size),
            operation: .copy,
            fraction: 1.0
        )
        scaled.unlockFocus()
        return scaled
    }
}
