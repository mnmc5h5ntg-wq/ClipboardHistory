import AppKit
import ImageIO

/// 采集图片时的像素上限（审计第二轮 B-4 / 账本 R2-08）。
///
/// 以前没有上限：剪贴板里的原分辨率图片整张入库，一张 4K 截图就是数十 MB 的 PNG，
/// 而库上限是 500 条 ⇒ 磁盘占用可以长到十几 GB，且每次保存都要过一遍这些字节。
///
/// **4096 的依据**（不是随手取的）：
/// - 4K 截图 3840×2160 的最长边 3840 ≤ 4096 ⇒ **逐字节不动**，最常见的"截个图"场景零损失；
/// - 界面最宽的详情列约 1100pt（`content-wide-1100x800` 夹具），retina 2× 也只需要 2200px；
/// - OCR 走的是 1200px 的降采样（`HistoryStore.decodeImageForOCR`），去重指纹只用 64px。
/// 也就是说 4096 已经远高于本产品任何一处显示/分析所需，只有 5K/6K 截图与相机原图会被缩。
enum ImageIntakePolicy {
    static let maxPixelDimension = 4096

    struct Plan: Equatable {
        /// 是否需要降采样。**只降不升**：小于上限的图一律原样保留。
        let shouldDownsample: Bool
        let longestEdge: Int
    }

    static func plan(pixelWidth: Int, pixelHeight: Int, limit: Int = maxPixelDimension) -> Plan {
        let longest = max(pixelWidth, pixelHeight)
        return Plan(shouldDownsample: longest > limit, longestEdge: longest)
    }

    /// 从编码数据读像素宽高（只读文件头，不 inflate 整幅图）。
    static func pixelDimensions(of data: Data) -> (width: Int, height: Int)? {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil),
              let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let width = properties[kCGImagePropertyPixelWidth] as? Int,
              let height = properties[kCGImagePropertyPixelHeight] as? Int,
              width > 0, height > 0 else {
            return nil
        }
        return (width, height)
    }
}

extension StoredImage {
    /// 超过上限就降采样，否则**原样返回**（连传入的 PNG 字节也一并保留，不重新编码）。
    ///
    /// 任何一步失败都退回原图：宁可这一次多占磁盘，也不能因为缩放失败把用户复制的图片丢掉。
    static func downsamplingIfNeeded(
        _ image: NSImage,
        pngData: Data? = nil,
        limit: Int = ImageIntakePolicy.maxPixelDimension
    ) -> StoredImage {
        let untouched = StoredImage(image, pngData: pngData)
        guard let sourceData = pngData ?? image.tiffRepresentation,
              let source = CGImageSourceCreateWithData(sourceData as CFData, nil),
              let dimensions = ImageIntakePolicy.pixelDimensions(of: sourceData) else {
            return untouched
        }
        let plan = ImageIntakePolicy.plan(
            pixelWidth: dimensions.width,
            pixelHeight: dimensions.height,
            limit: limit
        )
        guard plan.shouldDownsample else { return untouched }

        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: limit,
            kCGImageSourceShouldCacheImmediately: true
        ]
        guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            return untouched
        }
        // 注意：不再把**原来的** pngData 传下去 —— 那份字节对应的是大尺寸的图，
        // 留着会让去重与落盘写出与内存不一致的内容。
        let downsampled = NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
        // 但要把**新尺寸**的 PNG 字节一起交下去（第三轮审计 D-6）：只给 NSImage 时
        // `pngData()` 要走 `encodedCache` 现算，而第一次算恰好落在两个最不该慢的时刻 ——
        // 保存快照（`@MainActor`）与用户按住鼠标拖出的那一瞬间（`EntryDrag.payload`）。
        // 4096px 的 PNG 编码是几十毫秒级；在这里（采集的后台路径）算一次，两处都受益。
        let png = NSBitmapImageRep(cgImage: cgImage).representation(using: .png, properties: [:])
        if let png {
            return StoredImage(downsampled, pngData: png)
        }
        return StoredImage(downsampled)
    }
}
