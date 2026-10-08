import AppKit

struct ClipboardIntake {
    struct Entry {
        let content: ClipboardEntryContent
        let thumbnail: StoredImage?
        let sourceUTIs: [String]

        func makeHistoryEntry(timestamp: Date = Date()) -> ClipboardEntry {
            let app = NSWorkspace.shared.frontmostApplication
            return ClipboardEntry(
                content: content,
                timestamp: timestamp,
                thumbnail: thumbnail,
                sourceURL: content.sourceURL,
                sourceUTIs: sourceUTIs,
                sourceAppBundleID: app?.bundleIdentifier,
                sourceAppName: app?.localizedName
            )
        }

        func makeHistoryEntry(unlessDuplicateOf latestEntry: ClipboardEntry?, timestamp: Date = Date()) -> ClipboardEntry? {
            guard latestEntry?.content != content else { return nil }
            return makeHistoryEntry(timestamp: timestamp)
        }
    }

    private var lastChangeCount: Int

    init(pasteboard: NSPasteboard = .general) {
        self.lastChangeCount = pasteboard.changeCount
    }

    mutating func refresh(from pasteboard: NSPasteboard = .general) -> Entry? {
        lastChangeCount = pasteboard.changeCount
        return readEntry(from: pasteboard)
    }

    mutating func markCurrentChangeCount(from pasteboard: NSPasteboard = .general) {
        markChangeCount(pasteboard.changeCount)
    }

    mutating func markChangeCount(_ changeCount: Int) {
        lastChangeCount = changeCount
    }

    mutating func readChangedEntry(from pasteboard: NSPasteboard = .general) -> Entry? {
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
        Entry(
            content: content,
            thumbnail: thumbnail,
            sourceUTIs: (pasteboard.types ?? []).map { $0.rawValue }
        )
    }

    private func readFileURLs(from pb: NSPasteboard) -> [URL]? {
        if let urls = pb.readObjects(forClasses: [NSURL.self], options: nil) as? [URL],
           !urls.isEmpty {
            return urls
        }
        if let urlString = pb.string(forType: .fileURL),
           let url = URL(string: urlString) {
            return [url]
        }
        return nil
    }
}
