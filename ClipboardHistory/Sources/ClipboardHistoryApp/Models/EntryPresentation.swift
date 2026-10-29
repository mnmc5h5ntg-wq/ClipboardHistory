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
        // R65 / BACKLOG 94：这里以前写的是 `"📄 \(url.lastPathComponent)"`。三件事一起坏：
        // ① 它是 Apple Color Emoji 的一张**彩色图**，而这一行文字旁边（侧栏的行首、详情头的
        //    `photo` / `doc.text`）用的是 SF Symbol —— 同一个"这是文件"在一屏上说两种语言；
        // ② 它在字符串里，于是**参与搜索匹配**：`QuickPickModel.filtered` 拿整条预览做
        //    `localizedCaseInsensitiveContains`，打一个 📄 就能把文件行全筛出来（不是功能，是漏的口子）；
        // ③ 它白吃两个字符的截断预算（预览上限 60 字，文件名因此早两个字被切掉）。
        // 文件行的图标现在由**行首那一列**给（`QuickPickModel.rowSymbolName` + 浮层的 symbol 列），
        // 文案只说"是哪一条"。
        case .file(let url):
            return url.lastPathComponent
        case .files(let urls):
            if let firstURL = urls.first {
                return "\(firstURL.lastPathComponent) 等 \(urls.count) 个文件"
            }
            return "多个文件"
        }
    }

    /// 显示用的字符数上限。`String.count` 是整串 grapheme 遍历（2.4MB 文本实测 5.5ms，
    /// 审计第一轮 R-10 / 第二轮 B-3），而这行文案只需要量级正确：数到上限就停。
    static let sizeCountLimit = 100_000

    /// 数到 `limit` 就放弃并返回 `nil`（表示"超过上限"），让成本有界而不是随内容线性增长。
    static func characterCount(of string: String, limit: Int = sizeCountLimit) -> Int? {
        var count = 0
        for _ in string {
            count += 1
            if count > limit { return nil }
        }
        return count
    }

    static func sizeDescription(for content: ClipboardEntryContent) -> String {
        switch content {
        case .text(let string):
            if let count = characterCount(of: string) {
                return "\(count) 个字符"
            }
            return "超过 \(sizeCountLimit) 个字符"
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

    /// R481：文本条目是不是一条链接（只认 http/https、无空白）。纯函数，行内标记用它。
    static func looksLikeLink(_ text: String) -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard trimmed.hasPrefix("http://") || trimmed.hasPrefix("https://") else { return false }
        return !trimmed.contains(" ") && !trimmed.contains("\n")
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
