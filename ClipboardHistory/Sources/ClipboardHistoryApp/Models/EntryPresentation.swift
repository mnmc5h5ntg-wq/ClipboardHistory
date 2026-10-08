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
            let text = string.replacingOccurrences(of: "\n", with: " ↵ ")
            return String(text.prefix(60)) + (text.count > 60 ? "…" : "")
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
