import AppKit
import AVFoundation

extension ClipboardManager {
    /// 统一入口：file-url → png → tiff → text
    static func readEntry(from pb: NSPasteboard) -> (EntryContent, StoredImage?)? {
        if let url = readFileURL(from: pb) {
            var thumb = thumbnailForFile(at: url)
            if thumb == nil {
                if let tiff = pb.data(forType: .tiff),
                   let img = NSImage(data: tiff) {
                    thumb = StoredImage(img)
                } else if let icnsData = pb.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                          let img = NSImage(data: icnsData) {
                    thumb = StoredImage(img)
                }
            }
            return (.file(url), thumb)
        }

        if let pngData = pb.data(forType: .png),
           let image = NSImage(data: pngData) {
            return (.image(StoredImage(image)), StoredImage(image))
        }

        if let tiffData = pb.data(forType: .tiff),
           let image = NSImage(data: tiffData) {
            return (.image(StoredImage(image)), StoredImage(image))
        }

        if let t = pb.string(forType: .string),
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return (.text(t), nil)
        }

        return nil
    }

    private static func readFileURL(from pb: NSPasteboard) -> URL? {
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

    private static func thumbnailForFile(at url: URL) -> StoredImage? {
        let ext = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(ext), let image = NSImage(contentsOf: url) {
            return StoredImage(scaledImage(image, maxPixelSize: 512))
        }
        if FileTypeSupport.videoExtensions.contains(ext), let image = videoThumbnail(for: url) {
            return StoredImage(scaledImage(image, maxPixelSize: 512))
        }
        return nil
    }

    private static func videoThumbnail(for url: URL) -> NSImage? {
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
                    result.thumbnail = Self.image(from: cgImage)
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

    private static func image(from cgImage: CGImage) -> NSImage {
        NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
    }

    private static func scaledImage(_ image: NSImage, maxPixelSize: CGFloat) -> NSImage {
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
