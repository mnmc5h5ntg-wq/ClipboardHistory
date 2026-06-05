import AppKit
import SwiftUI

func dbg(_ msg: String) {
    if let data = (msg + "\n").data(using: .utf8) {
        if let fh = FileHandle(forWritingAtPath: "/tmp/clipboard_debug.txt") {
            fh.seekToEndOfFile(); fh.write(data); fh.synchronizeFile()
        }
    }
}
func initLog() { try? "".write(toFile: "/tmp/clipboard_debug.txt", atomically: true, encoding: .utf8) }

struct StoredImage: Equatable, Hashable {
    let nsImage: NSImage
    init(_ image: NSImage) { self.nsImage = image }
    static func == (lhs: StoredImage, rhs: StoredImage) -> Bool { lhs.nsImage === rhs.nsImage }
    func hash(into hasher: inout Hasher) { hasher.combine(ObjectIdentifier(nsImage)) }
}

final class ClipboardManager: ObservableObject, @unchecked Sendable {

    enum EntryContent: Equatable, Hashable {
        case text(String)
        case image(StoredImage)
        case file(URL)

        var preview: String {
            switch self {
            case .text(let s):
                let t = s.replacingOccurrences(of: "\n", with: " ↵ ")
                return String(t.prefix(60)) + (t.count > 60 ? "…" : "")
            case .image(let img):
                return "图片 \(Int(img.nsImage.size.width))×\(Int(img.nsImage.size.height))"
            case .file(let url):
                return "📄 \(url.lastPathComponent)"
            }
        }

        var sizeDescription: String {
            switch self {
            case .text(let s): return "\(s.count) 个字符"
            case .image(let img): return "\(Int(img.nsImage.size.width)) × \(Int(img.nsImage.size.height)) 像素"
            case .file(let url): return "文件: \(url.path)"
            }
        }

        var sourceURL: URL? {
            if case .file(let url) = self { return url }
            return nil
        }
    }

    struct Entry: Identifiable, Equatable, Hashable {
        let id = UUID()
        let content: EntryContent
        let timestamp: Date
        let thumbnail: StoredImage?
        let sourceURL: URL?
        let sourceUTIs: [String]
        var shortPreview: String { content.preview }
    }

    @Published var entries: [Entry] = []
    @Published var selectedEntry: Entry?
    @Published private(set) var searchText = ""
    var filteredEntries: [Entry] {
        guard !searchText.isEmpty else { return entries }
        return entries.filter {
            switch $0.content {
            case .text(let s):
                return s.localizedCaseInsensitiveContains(searchText)
            case .image:
                return "图片".localizedCaseInsensitiveContains(searchText)
            case .file(let url):
                return url.lastPathComponent.localizedCaseInsensitiveContains(searchText)
            }
        }
    }

    private var lastChangeCount = NSPasteboard.general.changeCount
    private var timer: Timer?
    private let maxEntries = 100

    func startMonitoring() {
        initLog()
        dbg("=== START ===")
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.checkPasteboard() }
        }
    }
    func stopMonitoring() { timer?.invalidate(); timer = nil }

    private func checkPasteboard() {
        let pb = NSPasteboard.general
        guard pb.changeCount != lastChangeCount else { return }
        lastChangeCount = pb.changeCount
        if let (content, thumbnail) = Self.readEntry(from: pb) {
            addEntry(content, thumbnail: thumbnail); return
        }
    }

    private func addEntry(_ content: EntryContent, thumbnail: StoredImage?) {
        if let f = entries.first, f.content == content { return }
        let sourceUTIs = (NSPasteboard.general.types ?? []).map { $0.rawValue }
        let e = Entry(
            content: content,
            timestamp: Date(),
            thumbnail: thumbnail,
            sourceURL: content.sourceURL,
            sourceUTIs: sourceUTIs
        )
        switch content {
        case .image(let si):
            let img = si.nsImage
            dbg("[STORE] oid=\(ObjectIdentifier(img)) type=\(type(of: img)) size=\(img.size) valid=\(img.isValid)")
            dbg("[STORE] reps=\(img.representations.count)")
            for (i, r) in img.representations.enumerated() {
                dbg("[STORE] rep[\(i)]: \(type(of: r)) px=\(r.pixelsWide)x\(r.pixelsHigh) size=\(r.size)")
            }
        case .file(let url):
            dbg("[STORE] file: \(url.path)")
            if let thumb = thumbnail {
                dbg("[STORE] thumb oid=\(ObjectIdentifier(thumb.nsImage)) size=\(thumb.nsImage.size)")
            }
        default: break
        }
        dbg("[STORE] sourceUTIs: \(sourceUTIs)")
        entries.insert(e, at: 0)
        if entries.count > maxEntries { entries = Array(entries.prefix(maxEntries)) }
        selectedEntry = entries.first
    }

    private static func readText(from pb: NSPasteboard) -> EntryContent? {
        guard let t = pb.string(forType: .string), !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        else { return nil }
        return .text(t)
    }

    /// 统一入口：file-url → png → tiff → text
    private static func readEntry(from pb: NSPasteboard) -> (EntryContent, StoredImage?)? {
        let rawTypes = (pb.types ?? []).map { $0.rawValue }
        dbg("[READ] types: \(rawTypes)")

        // --- Priority 1: public.file-url ---
        if let url = readFileURL(from: pb) {
            dbg("[READ] fileURL: \(url.path)")
            var thumb: StoredImage? = nil
            if let tiff = pb.data(forType: .tiff),
               let img = NSImage(data: tiff) {
                dbg("[READ] thumb from TIFF: \(img.size)")
                thumb = StoredImage(img)
            } else if let icnsData = pb.data(forType: NSPasteboard.PasteboardType(rawValue: "com.apple.icns")),
                      let img = NSImage(data: icnsData) {
                dbg("[READ] thumb from icns: \(img.size)")
                thumb = StoredImage(img)
            }
            dbg("[READ] => file: \(url.lastPathComponent)")
            return (.file(url), thumb)
        }

        // --- Priority 2: public.png (real pixel data) ---
        if let pngData = pb.data(forType: .png),
           let image = NSImage(data: pngData) {
            dbg("[READ] PNG: \(pngData.count) bytes, size=\(image.size)")
            return (.image(StoredImage(image)), StoredImage(image))
        }

        // --- Priority 3: public.tiff (real pixel data, no file-url present) ---
        if let tiffData = pb.data(forType: .tiff),
           let image = NSImage(data: tiffData) {
            dbg("[READ] TIFF: \(tiffData.count) bytes, size=\(image.size)")
            return (.image(StoredImage(image)), StoredImage(image))
        }

        // --- Priority 4: text ---
        if let t = pb.string(forType: .string),
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            dbg("[READ] => text: \(t.prefix(40))")
            return (.text(t), nil)
        }

        return nil
    }

    /// 从剪贴板读取文件 URL（优先用 NSURL 对象，回退到字符串）
    private static func readFileURL(from pb: NSPasteboard) -> URL? {
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

    func copyToClipboard(_ entry: Entry) {
        let pb = NSPasteboard.general; pb.clearContents()
        switch entry.content {
        case .text(let t): pb.setString(t, forType: .string)
        case .image(let img): pb.writeObjects([img.nsImage])
        case .file(let url): pb.writeObjects([url as NSURL])
        }
        lastChangeCount = pb.changeCount
    }

    func copyToClipboardAndBringToTop(_ entry: Entry) {
        copyToClipboard(entry)
        entries.removeAll { $0.id == entry.id }
        entries.insert(Entry(content: entry.content, timestamp: Date(),
                             thumbnail: entry.thumbnail, sourceURL: entry.sourceURL,
                             sourceUTIs: entry.sourceUTIs), at: 0)
        selectedEntry = entries.first
    }

    func delete(_ entry: Entry) {
        entries.removeAll { $0.id == entry.id }
        if selectedEntry?.id == entry.id { selectedEntry = entries.first }
    }
    func clearAll() { entries.removeAll(); selectedEntry = nil }
    func updateSearch(_ text: String) { searchText = text }
}
