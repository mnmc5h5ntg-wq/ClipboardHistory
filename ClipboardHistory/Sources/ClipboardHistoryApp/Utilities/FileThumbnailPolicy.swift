import AppKit
import ImageIO

/// 图片**文件**条目的行内缩略图（用户报的缺陷：详情区能看到图，左侧列表却只有一个通用文档符号）。
///
/// 为什么以前会缺：`.file` 条目的缩略图来自剪贴板里**顺带**给的 TIFF/icns 数据
/// （`ClipboardIntake.readEntry`）。从 Finder 复制文件时系统通常不给那份数据，
/// 于是 `thumbnail == nil`，行首退回 `doc` 符号；而详情区是按 URL 现读文件的，所以两边不一致。
/// 拖拽入库（`HistoryStore.addDroppedFiles`）更是直接写死 `thumbnail: nil`。
///
/// 这里刻意只做"小尺寸缩略图"，不碰详情区的取图路径：
/// ① 缩略图会**落盘**（`thumbnailFileName`），全尺寸等于把用户的图复制一份进历史目录；
/// ② 行首只有 ~32pt，256px 在 retina 上已经够清晰。
enum FileThumbnailPolicy {
    /// 长边上限。行首缩略图约 32pt，retina 2× 是 64px；256 留足余量又能把 PNG 压到几十 KB。
    static let maxPixel: Int = 256

    /// 哪些条目值得去磁盘上取一张缩略图。
    ///
    /// 用的是 `FileTypeSupport.imageExtensions`（**不含 svg**）：ImageIO 解不了 SVG，
    /// 而 OCR 那条路径的集合里有 svg（识别失败只是白跑一趟，不影响正确性）。
    /// 两个集合的差别写在这里，避免以后有人"顺手统一"成一个。
    static func shouldAttachThumbnail(for entry: ClipboardEntry) -> Bool {
        guard entry.thumbnail == nil else { return false }
        guard case .file(let url) = entry.content else { return false }
        return url.isFileURL
            && FileTypeSupport.imageExtensions.contains(url.pathExtension.lowercased())
    }

    /// 从磁盘上的图片文件解一张小缩略图。读不到 / 解不动 / 不是图片 ⇒ nil（行退回符号图标）。
    /// 必须在后台队列调用：这里会有真实的磁盘读与解码。
    static func thumbnail(for url: URL, maxPixel: Int = FileThumbnailPolicy.maxPixel) -> StoredImage? {
        let source = CGImageSourceCreateWithURL(url as CFURL, nil)
            ?? CGImageSourceCreateWithURL(url.standardizedFileURL as CFURL, nil)
        guard let source else { return nil }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixel,
            // 立刻解出来：不缓存的话 `CGImage` 会在后面被访问时再解一次，
            // 而那次可能在主线程上（同 D-010 的"NSImage 不进后台"是同一条约束）。
            kCGImageSourceShouldCacheImmediately: true,
        ]
        guard let cg = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            return nil
        }
        // 只保留一个合理上限内的尺寸：ImageIO 对某些带内嵌预览的文件会给出比请求更大的缩略图。
        let longest = max(cg.width, cg.height)
        guard longest > 0 else { return nil }
        let rep = NSBitmapImageRep(cgImage: cg)
        guard let png = rep.representation(using: .png, properties: [:]) else { return nil }
        return StoredImage(pngData: png)
    }
}
