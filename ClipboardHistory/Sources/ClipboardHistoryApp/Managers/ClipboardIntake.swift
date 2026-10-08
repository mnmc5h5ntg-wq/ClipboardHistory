import AppKit

struct ClipboardIntake {
    struct Entry {
        let content: ClipboardEntryContent
        let thumbnail: StoredImage?
        let sourceUTIs: [String]
        /// 来源 App 在读取剪贴板那一刻就定下来（而不是构造历史条目时），
        /// 这样"重复复制被提升"时也不会丢 attribution（审计 P-01）。
        let sourceAppBundleID: String?
        let sourceAppName: String?

        init(
            content: ClipboardEntryContent,
            thumbnail: StoredImage?,
            sourceUTIs: [String],
            sourceAppBundleID: String? = nil,
            sourceAppName: String? = nil
        ) {
            self.content = content
            self.thumbnail = thumbnail
            self.sourceUTIs = sourceUTIs
            self.sourceAppBundleID = sourceAppBundleID
            self.sourceAppName = sourceAppName
        }

        func makeHistoryEntry(timestamp: Date = Date()) -> ClipboardEntry {
            ClipboardEntry(
                content: content,
                timestamp: timestamp,
                thumbnail: thumbnail,
                sourceURL: content.sourceURL,
                sourceUTIs: sourceUTIs,
                sourceAppBundleID: resolvedSourceAppBundleID,
                sourceAppName: resolvedSourceAppName
            )
        }

        private var resolvedSourceAppBundleID: String? {
            sourceAppBundleID ?? NSWorkspace.shared.frontmostApplication?.bundleIdentifier
        }

        private var resolvedSourceAppName: String? {
            sourceAppName ?? NSWorkspace.shared.frontmostApplication?.localizedName
        }

        func makeHistoryEntry(unlessDuplicateOf latestEntry: ClipboardEntry?, timestamp: Date = Date()) -> ClipboardEntry? {
            guard latestEntry?.content != content else { return nil }
            return makeHistoryEntry(timestamp: timestamp)
        }
    }

    /// 注入的 pasteboard 必须真的用于后续读取。旧写法只在 `init` 里用它取一次
    /// `changeCount`，各读取方法的 `from:` 参数默认 `.general`，于是"注入了替身、
    /// 读的却是真实系统剪贴板"——测试会静默测到用户真实内容（本轮实测踩到）。
    private let pasteboard: NSPasteboard
    private var lastChangeCount: Int

    init(pasteboard: NSPasteboard = .general) {
        self.pasteboard = pasteboard
        self.lastChangeCount = pasteboard.changeCount
    }

    mutating func refresh(from override: NSPasteboard? = nil) -> Entry? {
        let pasteboard = override ?? self.pasteboard
        lastChangeCount = pasteboard.changeCount
        return readEntry(from: pasteboard)
    }

    mutating func markCurrentChangeCount(from override: NSPasteboard? = nil) {
        markChangeCount((override ?? self.pasteboard).changeCount)
    }

    mutating func markChangeCount(_ changeCount: Int) {
        lastChangeCount = changeCount
    }

    mutating func readChangedEntry(from override: NSPasteboard? = nil) -> Entry? {
        let pasteboard = override ?? self.pasteboard
        guard pasteboard.changeCount != lastChangeCount else { return nil }
        lastChangeCount = pasteboard.changeCount
        return readEntry(from: pasteboard)
    }

    /// 统一入口：file-url(s) → png → tiff → text
    private func readEntry(from pasteboard: NSPasteboard) -> Entry? {
        if let urls = readFileURLs(from: pasteboard), !urls.isEmpty {
            var thumb: StoredImage?
            if let tiff = pasteboard.data(forType: .tiff),
               let img = NSImage(data: tiff) {
                thumb = StoredImage(img)
            } else if let icnsData = pasteboard.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                      let img = NSImage(data: icnsData) {
                thumb = StoredImage(img)
            }
            let content: ClipboardEntryContent = urls.count == 1 ? .file(urls[0]) : .files(urls)
            return makeEntry(content: content, thumbnail: thumb, pasteboard: pasteboard)
        }

        if let pngData = pasteboard.data(forType: .png),
           let image = NSImage(data: pngData) {
            let stored = StoredImage(image)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let tiffData = pasteboard.data(forType: .tiff),
           let image = NSImage(data: tiffData) {
            let stored = StoredImage(image)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let t = pasteboard.string(forType: .string),
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return makeEntry(content: .text(t), thumbnail: nil, pasteboard: pasteboard)
        }

        return nil
    }

    private func makeEntry(
        content: ClipboardEntryContent,
        thumbnail: StoredImage?,
        pasteboard: NSPasteboard
    ) -> Entry {
        let app = NSWorkspace.shared.frontmostApplication
        return Entry(
            content: content,
            thumbnail: thumbnail,
            sourceUTIs: (pasteboard.types ?? []).map { $0.rawValue },
            sourceAppBundleID: app?.bundleIdentifier,
            sourceAppName: app?.localizedName
        )
    }

    private func readFileURLs(from pb: NSPasteboard) -> [URL]? {
        // 必须限定"仅文件 URL"：不带该选项时，浏览器复制的链接（public.url）
        // 也会被读成 URL 并被当成文件条目，之后回写永远失败（审计 P-15）。
        if let urls = pb.readObjects(
            forClasses: [NSURL.self],
            options: [.urlReadingFileURLsOnly: true]
        ) as? [URL], !urls.isEmpty {
            return urls
        }
        if let urlString = pb.string(forType: .fileURL),
           let url = URL(string: urlString) {
            return [url]
        }
        return nil
    }
}
