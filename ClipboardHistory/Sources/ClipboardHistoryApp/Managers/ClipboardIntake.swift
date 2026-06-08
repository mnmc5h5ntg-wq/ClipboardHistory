import AppKit

struct ClipboardIntake {
    struct Entry {
        let content: ClipboardEntryContent
        let thumbnail: StoredImage?
        let sourceUTIs: [String]

        func makeHistoryEntry(timestamp: Date = Date()) -> ClipboardEntry {
            ClipboardEntry(
                content: content,
                timestamp: timestamp,
                thumbnail: thumbnail,
                sourceURL: content.sourceURL,
                sourceUTIs: sourceUTIs
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

    /// 统一入口：file-url → png → tiff → text
    private func readEntry(from pasteboard: NSPasteboard) -> Entry? {
        if let url = readFileURL(from: pasteboard) {
            var thumb: StoredImage?
            if let tiff = pasteboard.data(forType: .tiff),
               let img = NSImage(data: tiff) {
                thumb = StoredImage(img)
            } else if let icnsData = pasteboard.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                      let img = NSImage(data: icnsData) {
                thumb = StoredImage(img)
            }
            return makeEntry(content: .file(url), thumbnail: thumb, pasteboard: pasteboard)
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

    private func readFileURL(from pb: NSPasteboard) -> URL? {
        if let urls = pb.readObjects(forClasses: [NSURL.self], options: nil) as? [URL],
           let url = urls.first {
            return url
        }
        if let urlString = pb.string(forType: .fileURL),
           let url = URL(string: urlString) {
            return url
        }
        return nil
    }
}
