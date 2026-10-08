import AppKit
import CryptoKit

struct StoredImage: Equatable, Hashable, @unchecked Sendable {
    let nsImage: NSImage
    private let fingerprint: String

    init(_ image: NSImage) {
        self.nsImage = image
        self.fingerprint = Self.fingerprint(for: image)
    }

    init?(pngData: Data) {
        guard let image = NSImage(data: pngData) else { return nil }
        self.nsImage = image
        self.fingerprint = Self.fingerprint(for: image)
    }

    func pngData() -> Data? {
        Self.pngData(from: nsImage)
    }

    static func == (lhs: StoredImage, rhs: StoredImage) -> Bool {
        lhs.fingerprint == rhs.fingerprint
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(fingerprint)
    }

    private static func fingerprint(for image: NSImage) -> String {
        if let pixelFingerprint = pixelFingerprint(for: image) {
            return pixelFingerprint
        }

        guard let data = pngData(from: image) else {
            return "object:\(ObjectIdentifier(image))"
        }
        return SHA256.hash(data: data)
            .map { String(format: "%02x", $0) }
            .joined()
    }

    private static func pngData(from image: NSImage) -> Data? {
        guard let tiffData = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData) else {
            return nil
        }
        return bitmap.representation(using: NSBitmapImageRep.FileType.png, properties: [:])
    }

    private static func pixelFingerprint(for image: NSImage) -> String? {
        var proposedRect = NSRect(origin: .zero, size: image.size)
        guard let cgImage = image.cgImage(forProposedRect: &proposedRect, context: nil, hints: nil) else {
            return nil
        }

        let width = cgImage.width
        let height = cgImage.height
        guard width > 0, height > 0 else { return nil }

        var pixels = Data(count: width * height * 4)
        let rendered = pixels.withUnsafeMutableBytes { buffer -> Bool in
            guard let baseAddress = buffer.baseAddress,
                  let context = CGContext(
                    data: baseAddress,
                    width: width,
                    height: height,
                    bitsPerComponent: 8,
                    bytesPerRow: width * 4,
                    space: CGColorSpaceCreateDeviceRGB(),
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
                        | CGBitmapInfo.byteOrder32Big.rawValue
                  ) else {
                return false
            }

            context.clear(CGRect(x: 0, y: 0, width: width, height: height))
            context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }

        guard rendered else { return nil }

        var fingerprintData = "\(width)x\(height):".data(using: .utf8) ?? Data()
        fingerprintData.append(pixels)
        return SHA256.hash(data: fingerprintData)
            .map { String(format: "%02x", $0) }
            .joined()
    }
}
