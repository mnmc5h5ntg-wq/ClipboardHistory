import AppKit
import CryptoKit

/// 惰性缓存盒子：让 StoredImage 保持值语义，同时把昂贵计算做一次。
final class _FingerprintCache: @unchecked Sendable {
    private let lock = NSLock()
    private var value: String?

    func get_or_set(_ make: () -> String) -> String {
        lock.lock()
        defer { lock.unlock() }
        if let value { return value }
        let made = make()
        value = made
        return made
    }
}

/// 图片编码字节的惰性缓存（class 盒子，值语义仍然保持）。
final class _EncodedPNGCache: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Data?

    func get_or_set(_ make: () -> Data?) -> Data? {
        lock.lock()
        defer { lock.unlock() }
        if let value { return value }
        let made = make()
        value = made
        return made
    }
}

struct StoredImage: Equatable, Hashable, @unchecked Sendable {
    let nsImage: NSImage
    /// 剪贴板/磁盘里本来就带 PNG 字节时直接复用，不再二次编码。
    private let sourcePNGData: Data?
    private let encodedCache = _EncodedPNGCache()
    /// 指纹按需计算：启动载入 12 张 1600x1200 时，仅"解码 + 采样哈希"就要 400ms+，
    /// 而绝大多数条目在这一生里根本不会被拿去比较。
    private let fingerprintCache = _FingerprintCache()

    init(_ image: NSImage, pngData: Data? = nil) {
        self.nsImage = image
        self.sourcePNGData = pngData
    }

    init?(pngData: Data) {
        guard let image = NSImage(data: pngData) else { return nil }
        self.nsImage = image
        self.sourcePNGData = pngData
    }

    /// 指纹 = 64x64 像素采样哈希，**与编码方式无关**。
    /// 这一点是行为要求而不是风格：「再次复制」会把图片重新过一遍剪贴板，
    /// 我们写出去的是 NSImage，剪贴板给回来的却是 TIFF —— 只有按像素比，
    /// 同一张图才不会变成两条（`testAddPromotesImageRoundTrippedThroughPasteboard...` 守着）。
    ///
    /// 但取样的**方式**可以是廉价的：以前先 `NSImage.cgImage(forProposedRect:)`
    /// 整幅解码再缩到 64x64，3000x2000 冷启动实测 217ms，而它发生在主线程的去重比较里。
    /// 现在让 ImageIO 直接解出 64px 缩略图（同图实测 58ms），并在字节完全相同时
    /// 直接判定相同（0.2ms 量级），把最常见的那一类比较从解码路径上摘掉。
    private var fingerprint: String {
        fingerprintCache.get_or_set { Self.pixelFingerprint(image: nsImage, pngData: pngData()) }
    }

    func pngData() -> Data? {
        if let sourcePNGData { return sourcePNGData }
        return encodedCache.get_or_set {
            Self.pngData(from: nsImage)
        }
    }

    static func == (lhs: StoredImage, rhs: StoredImage) -> Bool {
        // 短路只在"必然等价"时才用：字节相同 ⇒ 像素必然相同。
        // 反过来"尺寸不同 ⇒ 不同图"看着也成立，但点尺寸受 DPI 影响，
        // 同一张图的 PNG 与 TIFF 可能给出不同点尺寸，所以不做那条短路。
        if let a = lhs.sourcePNGData, let b = rhs.sourcePNGData, a == b { return true }
        return lhs.fingerprint == rhs.fingerprint
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(fingerprint)
    }

    private static func hex<D: Sequence<UInt8>>(_ digest: D) -> String {
        digest.map { String(format: "%02x", $0) }.joined()
    }

    private static func pngData(from image: NSImage) -> Data? {
        guard let tiffData = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData) else {
            return nil
        }
        return bitmap.representation(using: NSBitmapImageRep.FileType.png, properties: [:])
    }

    /// 采样边长。指纹键里带上原始像素宽高，所以两张"缩样相同但原图不同"的图不会误判。
    private static let sampleSide = 64

    /// 首选路径：从 PNG 字节直接解出 64px 一帧。
    /// 只有在字节都拿不到（位图坏掉）时才退回 NSImage 整幅解码那条老路。
    private static func pixelFingerprint(image: NSImage, pngData data: Data?) -> String {
        if let data, let sample = sampledFingerprint(fromPNG: data) {
            return sample
        }
        if let sample = sampledFingerprint(for: image) {
            return sample
        }
        guard let encoded = data ?? pngData(from: image) else {
            return "object:\(ObjectIdentifier(image))"
        }
        return "full:" + hex(SHA256.hash(data: encoded))
    }

    /// ImageIO 路线：宽高从文件头读（不 inflate），像素只解 64px 那一帧。
    static func sampledFingerprint(fromPNG data: Data) -> String? {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil) else { return nil }
        let side = sampleSide
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: side,
        ]
        guard let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            return nil
        }
        guard let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let pixelWidth = properties[kCGImagePropertyPixelWidth] as? Int,
              let pixelHeight = properties[kCGImagePropertyPixelHeight] as? Int,
              pixelWidth > 0, pixelHeight > 0 else {
            return nil
        }
        return sampleKey(pixelWidth: pixelWidth, pixelHeight: pixelHeight, of: thumbnail)
    }

    private static func sampledFingerprint(for image: NSImage) -> String? {
        var proposedRect = NSRect(origin: .zero, size: image.size)
        guard let cgImage = image.cgImage(forProposedRect: &proposedRect, context: nil, hints: nil) else {
            return nil
        }
        guard cgImage.width > 0, cgImage.height > 0 else { return nil }
        return sampleKey(pixelWidth: cgImage.width, pixelHeight: cgImage.height, of: cgImage)
    }

    /// 两条来源共用这一段：缩到 64x64 RGBA 后连同原始宽高一起哈希，
    /// 保证"同一张图"无论从 PNG 字节还是 NSImage 进来都得到同一个键。
    private static func sampleKey(pixelWidth: Int, pixelHeight: Int, of cgImage: CGImage) -> String? {
        let side = sampleSide
        var pixels = Data(count: side * side * 4)
        let rendered = pixels.withUnsafeMutableBytes { buffer -> Bool in
            guard let baseAddress = buffer.baseAddress,
                  let context = CGContext(
                    data: baseAddress,
                    width: side,
                    height: side,
                    bitsPerComponent: 8,
                    bytesPerRow: side * 4,
                    space: CGColorSpaceCreateDeviceRGB(),
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
                        | CGBitmapInfo.byteOrder32Big.rawValue
                  ) else {
                return false
            }
            context.interpolationQuality = .high
            context.clear(CGRect(x: 0, y: 0, width: side, height: side))
            context.draw(cgImage, in: CGRect(x: 0, y: 0, width: side, height: side))
            return true
        }
        guard rendered else { return nil }

        var fingerprintData = "s\(side):\(pixelWidth)x\(pixelHeight):".data(using: .utf8) ?? Data()
        fingerprintData.append(pixels)
        return "sample:" + hex(SHA256.hash(data: fingerprintData))
    }
}
