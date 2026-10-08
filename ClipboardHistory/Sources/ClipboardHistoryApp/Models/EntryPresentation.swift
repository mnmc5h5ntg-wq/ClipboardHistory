import AppKit
import Foundation

enum EntryPresentation {
    struct FileNameParts {
        let baseName: String
        let fileExtension: String
        let fallbackName: String

        var displayBaseName: String {
            baseName.isEmpty ? fallbackName : baseName
        }
    }

    static func preview(for content: ClipboardEntryContent) -> String {
        switch content {
        case .text(let string):
            // 旧实现对整个正文做 replacingOccurrences，再为判断长度走一遍 grapheme 计数：
            // 2.4MB 文本单条 45.8ms，而侧栏每帧每条都要调它。
            // 只需前 61 个字符就能决定"60 字 + 是否加省略号"。
            let headEnd = string.index(string.startIndex, offsetBy: 61, limitedBy: string.endIndex) ?? string.endIndex
            let head = string[string.startIndex..<headEnd]
            let collapsed = head.replacingOccurrences(of: "\n", with: " ↵ ")
            return String(collapsed.prefix(60)) + (headEnd < string.endIndex ? "…" : "")
        case .image(let image):
            return "图片 \(Int(image.nsImage.size.width))×\(Int(image.nsImage.size.height))"
        case .file(let url):
            return "📄 \(url.lastPathComponent)"
        case .files(let urls):
            if let firstURL = urls.first {
                return "📄 \(firstURL.lastPathComponent) 等 \(urls.count) 个文件"
            }
            return "📄 多个文件"
        }
    }

    static func sizeDescription(for content: ClipboardEntryContent) -> String {
        switch content {
        case .text(let string):
            return "\(string.count) 个字符"
        case .image(let image):
            return "\(Int(image.nsImage.size.width)) × \(Int(image.nsImage.size.height)) 像素"
        case .file(let url):
            return "文件: \(url.lastPathComponent)"
        case .files(let urls):
            return "\(urls.count) 个文件"
        }
    }

    /// 菜单栏/`MenuBarExtra` 用的标题：普通内容给短摘要（否则无法分辨要粘哪一条），
    /// 但被规则判为疑似密钥/密码/验证码的内容只显示类型与时间，不显示正文（审计 R-43）。
    static func menuLabel(for entry: ClipboardEntry) -> String {
        if PrivacyClassifier.mayContainSecrets(entry) {
            let kind: String
            switch entry.content {
            case .text: kind = "文本"
            case .image: kind = "图片"
            case .file: kind = "文件"
            case .files: kind = "多个文件"
            }
            return "疑似敏感内容（\(kind)）· \(relativeTime(entry.timestamp))"
        }
        return menuTitle(for: entry, maxLength: 24)
    }

    static func relativeTime(_ date: Date, now: Date = Date()) -> String {
        let seconds = max(0, Int(now.timeIntervalSince(date)))
        switch seconds {
        case 0..<60: return "刚刚"
        case 60..<3_600: return "\(seconds / 60) 分钟前"
        case 3_600..<86_400: return "\(seconds / 3_600) 小时前"
        default: return "\(seconds / 86_400) 天前"
        }
    }

    static func menuTitle(for entry: ClipboardEntry, maxLength: Int = 42) -> String {
        let title: String
        switch entry.content {
        case .text(let string):
            title = string
                .replacingOccurrences(of: "\n", with: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
        case .image:
            title = preview(for: entry.content)
        case .file(let url):
            title = url.lastPathComponent
        case .files(let urls):
            title = urls.first.map { "\($0.lastPathComponent) 等 \(urls.count) 个文件" } ?? "多个文件"
        }

        guard title.count > maxLength else { return title }
        return String(title.prefix(maxLength - 1)) + "…"
    }

    static func fileNameParts(for url: URL) -> FileNameParts {
        let fileName = url.lastPathComponent
        let fileExtension = url.pathExtension
        let baseName: String
        if fileExtension.isEmpty {
            baseName = fileName
        } else {
            baseName = String(fileName.dropLast(fileExtension.count + 1))
        }
        return FileNameParts(
            baseName: baseName,
            fileExtension: fileExtension,
            fallbackName: fileName
        )
    }
}
