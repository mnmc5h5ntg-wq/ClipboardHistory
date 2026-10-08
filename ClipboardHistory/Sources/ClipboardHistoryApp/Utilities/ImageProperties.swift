import AppKit
import ImageIO
import CoreGraphics

enum ImageProperties {
    /// 只读图片头部元信息拿像素尺寸，不_decode_整张图。
    /// 考虑 EXIF 方向：>=5 表示图像需要旋转 90°，显示宽高要互换。
    nonisolated static func pixelSize(of url: URL) -> NSSize? {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any]
        else { return nil }
        guard let width = (properties[kCGImagePropertyPixelWidth] as? NSNumber)?.doubleValue,
              let height = (properties[kCGImagePropertyPixelHeight] as? NSNumber)?.doubleValue,
              width > 0, height > 0
        else { return nil }

        let orientation = (properties[kCGImagePropertyOrientation] as? NSNumber)?.uint32Value ?? 1
        let rotates: Bool
        switch orientation {
        case 5, 6, 7, 8:
            rotates = true
        default:
            rotates = false
        }
        return rotates ? NSSize(width: height, height: width) : NSSize(width: width, height: height)
    }
}
