import AppKit

@MainActor
protocol ClipboardWriting {
    @discardableResult
    func write(_ content: ClipboardEntryContent) throws -> Int
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
        if case .file(let url) = content,
           !FileManager.default.fileExists(atPath: url.path) {
            throw ClipboardWriteError.fileDoesNotExist
        }

        pasteboard.clearContents()
        let didWrite: Bool
        switch content {
        case .text(let text):
            didWrite = pasteboard.setString(text, forType: .string)
        case .image(let image):
            didWrite = pasteboard.writeObjects([image.nsImage])
        case .file(let url):
            didWrite = pasteboard.writeObjects([url as NSURL])
        }

        guard didWrite else {
            switch content {
            case .text:
                throw ClipboardWriteError.failedToWriteText
            case .image:
                throw ClipboardWriteError.failedToWriteImage
            case .file:
                throw ClipboardWriteError.failedToWriteFileURL
            }
        }
        return pasteboard.changeCount
    }
}
