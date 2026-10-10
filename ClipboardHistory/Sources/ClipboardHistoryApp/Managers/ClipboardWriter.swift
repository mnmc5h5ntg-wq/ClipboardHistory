import AppKit

@MainActor
protocol ClipboardWriting {
    @discardableResult
    func write(_ content: ClipboardEntryContent) throws -> Int

    /// 带富文本的写回（§5 F-2）。默认实现**丢掉富文本**，所以夹具用的
    /// `TestClipboardWriter` 不必逐个改 —— 代价是"RTF 真的进了剪贴板"这条判据
    /// 必须用 `SystemClipboardWriter` + 命名剪贴板来测：拿夹具测会恒绿。
    @discardableResult
    func write(_ content: ClipboardEntryContent, richText: RichTextPayload?) throws -> Int
}

extension ClipboardWriting {
    @discardableResult
    func write(_ content: ClipboardEntryContent, richText: RichTextPayload?) throws -> Int {
        try write(content)
    }
}

enum ClipboardWriteError: LocalizedError, Equatable {
    case failedToWriteText
    case failedToWriteImage
    case failedToWriteFileURL
    case fileDoesNotExist

    var errorDescription: String? {
        switch self {
        case .failedToWriteText:
            return "无法写入文本到剪贴板。"
        case .failedToWriteImage:
            return "无法写入图片到剪贴板。"
        case .failedToWriteFileURL:
            return "无法写入文件到剪贴板。"
        case .fileDoesNotExist:
            return "文件已移动或删除，无法写入剪贴板。"
        }
    }
}

@MainActor
struct SystemClipboardWriter: ClipboardWriting {
    private let pasteboard: NSPasteboard

    init(pasteboard: NSPasteboard = .general) {
        self.pasteboard = pasteboard
    }

    @discardableResult
    func write(_ content: ClipboardEntryContent) throws -> Int {
        try write(content, richText: nil)
    }

    @discardableResult
    func write(_ content: ClipboardEntryContent, richText: RichTextPayload?) throws -> Int {
        let fileURLs: [URL]
        switch content {
        case .file(let url):
            fileURLs = [url]
        case .files(let urls):
            fileURLs = urls
        case .text, .image:
            fileURLs = []
        }

        if fileURLs.contains(where: { !FileManager.default.fileExists(atPath: $0.path) }) {
            throw ClipboardWriteError.fileDoesNotExist
        }

        pasteboard.clearContents()
        if case .text(let text) = content, let richText, !richText.isEmpty {
            // 一条 `NSPasteboardItem`，按 RTF → HTML → 纯文本 的顺序登记：
            // 富文本应用向前找它认的那一份，只认纯文本的目标拿到的仍是干净文本。
            let item = NSPasteboardItem()
            RichTextPolicy.write(text, payload: richText, to: item)
            guard pasteboard.writeObjects([item]) else {
                throw ClipboardWriteError.failedToWriteText
            }
            return pasteboard.changeCount
        }
        let didWrite: Bool
        switch content {
        case .text(let text):
            didWrite = pasteboard.setString(text, forType: .string)
        case .image(let image):
            didWrite = pasteboard.writeObjects([image.nsImage])
        case .file(let url):
            didWrite = pasteboard.writeObjects([url as NSURL])
        case .files(let urls):
            didWrite = pasteboard.writeObjects(urls.map { $0 as NSURL })
        }

        guard didWrite else {
            switch content {
            case .text:
                throw ClipboardWriteError.failedToWriteText
            case .image:
                throw ClipboardWriteError.failedToWriteImage
            case .file, .files:
                throw ClipboardWriteError.failedToWriteFileURL
            }
        }
        return pasteboard.changeCount
    }
}
