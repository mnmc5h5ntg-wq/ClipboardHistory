import AppKit
import CryptoKit

/// 惰性缓存盒子：让 StoredImage 保持值语义，同时把昂贵计算做一次。
final class _FingerprintCache: @unchecked Sendable {
    private let lock = NSLock()
    private var value: String?

    func get_or_set(_ input: NSImage, _ make: (NSImage) -> String) -> String {
        lock.lock()
        defer { lock.unlock() }
        if let value { return value }
        let made = make(input)
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

    private var fingerprint: String {
        fingerprintCache.get_or_set(nsImage) { Self.fingerprint(for: $0) }
    }

    func pngData() -> Data? {
        if let sourcePNGData { return sourcePNGData }
        return encodedCache.get_or_set {
            Self.pngData(from: nsImage)
        }
    }

    static func == (lhs: StoredImage, rhs: StoredImage) -> Bool {
        lhs.fingerprint == rhs.fingerprint
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(fingerprint)
    }

    private static func fingerprint(for image: NSImage) -> String {
        if let sample = sampledFingerprint(for: image) {
            return sample
        }

        guard let data = pngData(from: image) else {
            return "object:\(ObjectIdentifier(image))"
        }
        return "full:" + hex(SHA256.hash(data: data))
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

    /// 旧实现按原始像素整幅绘制后再 SHA256（1200x900 实测 7.4ms/张，启动载入 8 张
    /// 2000x1500 共 605.8ms，全在主线程）。现在固定缩到 64x64 再哈希：
    /// 仍然能区分"同尺寸但内容不同"的截图，成本与图片原始尺寸解耦。
    private static let sampleSide = 64

    private static func sampledFingerprint(for image: NSImage) -> String? {
        var proposedRect = NSRect(origin: .zero, size: image.size)
        guard let cgImage = image.cgImage(forProposedRect: &proposedRect, context: nil, hints: nil) else {
            return nil
        }
        let pixelWidth = cgImage.width
        let pixelHeight = cgImage.height
        guard pixelWidth > 0, pixelHeight > 0 else { return nil }

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
