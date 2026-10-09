import AppKit
import Foundation
import UniformTypeIdentifiers

/// 把拖进来的文件变成一条历史（审计第二轮 1.5 / 账本 R2-05 的另一半：
/// "窗口也不接受拖入文件来入库"）。
///
/// 规划是纯函数，视图侧只负责在 `.onDrop` 里调用它并把结果交给 `HistoryStore.add`。
/// 刻意**不**在这里判断"要不要显示提示"之类的事，保持可测。
enum DroppedFileImport {
    struct Planned: Equatable {
        let content: ClipboardEntryContent
        /// 被丢进来但不是文件 URL 的项（例如从浏览器拖一段富文本进来时带的 URL）。
        let ignoredCount: Int
    }

    /// 只接受**文件 URL**：非文件 URL（Web 链接之类）走的是"复制"路径而不是拖放，
    /// 这里收下就会与 P-15 那类"把链接当文件"的混淆同源。
    static func plan(for urls: [URL]) -> Planned? {
        let files = urls.filter(\.isFileURL)
        let ignored = urls.count - files.count
        guard !files.isEmpty else { return nil }
        if files.count == 1 {
            return Planned(content: .file(files[0]), ignoredCount: ignored)
        }
        return Planned(content: .files(files), ignoredCount: ignored)
    }

    /// 拖放落点用的类型标识（macOS 12 上 `UTType.fileURL` 可用；不用 13+ 的 `Transferable`）。
    static var acceptedTypeIdentifiers: [String] {
        [UTType.fileURL.identifier]
    }

    /// 拖放反馈文字（放在窗口里时给用户一个明确落点）。
    static func dropHint(for urls: [URL]) -> String? {
        guard let planned = plan(for: urls) else { return nil }
        switch planned.content {
        case .file(let url): return "加入历史：\(url.lastPathComponent)"
        case .files(let urls): return "加入历史：\(urls.count) 个文件"
        default: return nil
        }
    }
}
