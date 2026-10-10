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
        /// 富文本载荷（§5 F-2）。开关关 / 没有表示 / 全部超限时为 nil。
        let richText: RichTextPayload?

        init(
            content: ClipboardEntryContent,
            thumbnail: StoredImage?,
            sourceUTIs: [String],
            sourceAppBundleID: String? = nil,
            sourceAppName: String? = nil,
            richText: RichTextPayload? = nil
        ) {
            self.content = content
            self.thumbnail = thumbnail
            self.sourceUTIs = sourceUTIs
            self.sourceAppBundleID = sourceAppBundleID
            self.sourceAppName = sourceAppName
            self.richText = richText
        }

        func makeHistoryEntry(timestamp: Date = Date()) -> ClipboardEntry {
            ClipboardEntry(
                content: content,
                timestamp: timestamp,
                thumbnail: thumbnail,
                sourceURL: content.sourceURL,
                sourceUTIs: sourceUTIs,
                sourceAppBundleID: resolvedSourceAppBundleID,
                sourceAppName: resolvedSourceAppName,
                richText: richText
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
    /// 采集策略（这一轮加的富文本开关）从哪个 defaults 域读。生产是 `.standard`，
    /// 单测注入独立 suite，于是"设置页打开了开关 → 采集侧真的开始抓 RTF"这一段
    /// 能从产品入口验，而不必往进程的標準域里写东西（与 `HistoryStore.policyDefaults` 同一套办法）。
    var policyDefaults: UserDefaults = .standard

    private let pasteboard: NSPasteboard
    /// 文本正文上限（字符）。超过则截断并留标记：一条超大文本会常驻内存、
    /// 进 JSON 存档，并让每次搜索/渲染都扫它（审计 R-22）。
    static let maxTextCharacters = 512_000

    static func bounded(_ text: String) -> String {
        guard text.count > maxTextCharacters else { return text }
        let end = text.index(text.startIndex, offsetBy: maxTextCharacters)
        return String(text[..<end]) + "\n…（内容过长，已截断保存）"
    }

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
                // 缩略图也会落盘，所以走同一套上限。
                thumb = StoredImage.downsamplingIfNeeded(img)
            } else if let icnsData = pasteboard.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                      let img = NSImage(data: icnsData) {
                thumb = StoredImage.downsamplingIfNeeded(img)
            }
            let content: ClipboardEntryContent = urls.count == 1 ? .file(urls[0]) : .files(urls)
            return makeEntry(content: content, thumbnail: thumb, pasteboard: pasteboard)
        }

        if let pngData = pasteboard.data(forType: .png),
           let image = NSImage(data: pngData) {
            // 超过 4096px 最长边才降采样（审计第二轮 B-4 / 账本 R2-08）；
            // 4K 截图（3840×2160）及以下**逐字节不动**，阈值依据见 ImageIntakePolicy。
            let stored = StoredImage.downsamplingIfNeeded(image, pngData: pngData)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let tiffData = pasteboard.data(forType: .tiff),
           let image = NSImage(data: tiffData) {
            let stored = StoredImage.downsamplingIfNeeded(image)
            return makeEntry(content: .image(stored), thumbnail: stored, pasteboard: pasteboard)
        }

        if let t = pasteboard.string(forType: .string),
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            // 纯文本之外再抓一份 RTF/HTML（§5 F-2）。抓取必须在采集这一刻而不是写回时：
            // 剪贴板的内容只有这一刻还在，等用户从历史里粘贴时，原始表示早就被下一次复制覆盖了。
            let rich = RichTextPolicy.capture(from: pasteboard, defaults: policyDefaults)
            return makeEntry(content: .text(Self.bounded(t)), thumbnail: nil,
                             pasteboard: pasteboard, richText: rich)
        }

        // 只含非文件 NSURL（`public.url`）的剪贴板以前被整条丢弃（审计 N-4 的副产物 / 账本 R2-16，
        // 决策 D-018）：浏览器复制链接通常同时带字符串所以日常无感，但只发布 URL 对象的应用
        // 会让这次复制凭空消失 —— 对剪贴板管理器这是功能缺口。记成文本条目，与"链接带字符串时
        // 记成文本"的既有行为一致；文件路径不会走到这里（上面的 readFileURLs 限定
        // `.urlReadingFileURLsOnly` 且先返回），所以不会复活 P-15 那类"Web URL 被当文件"的缺陷。
        if let urls = pasteboard.readObjects(forClasses: [NSURL.self], options: nil) as? [URL],
           let first = urls.first, !first.isFileURL {
            return makeEntry(content: .text(Self.bounded(first.absoluteString)), thumbnail: nil, pasteboard: pasteboard)
        }

        return nil
    }

    private func makeEntry(
        content: ClipboardEntryContent,
        thumbnail: StoredImage?,
        pasteboard: NSPasteboard,
        richText: RichTextPayload? = nil
    ) -> Entry {
        let app = NSWorkspace.shared.frontmostApplication
        return Entry(
            content: content,
            thumbnail: thumbnail,
            sourceUTIs: (pasteboard.types ?? []).map { $0.rawValue },
            sourceAppBundleID: app?.bundleIdentifier,
            sourceAppName: app?.localizedName,
            richText: richText
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
