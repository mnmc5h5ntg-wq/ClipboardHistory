import AppKit
import Combine

final class ClipboardManager: ObservableObject, @unchecked Sendable {
    typealias Entry = ClipboardEntry
    typealias EntryContent = ClipboardEntryContent

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
    private var delayedStartTask: Task<Void, Never>?
    private let maxEntries = 100

    func startMonitoring(after delay: TimeInterval = 0) {
        stopMonitoring()
        if delay > 0 {
            delayedStartTask = Task { @MainActor [weak self] in
                try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                guard !Task.isCancelled else { return }
                self?.startMonitoring()
                self?.checkPasteboard()
            }
            return
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.checkPasteboard() }
        }
    }
    func stopMonitoring() {
        delayedStartTask?.cancel()
        delayedStartTask = nil
        timer?.invalidate()
        timer = nil
    }

    func refreshHistory() {
        let pb = NSPasteboard.general
        lastChangeCount = pb.changeCount
        if let (content, thumbnail) = Self.readEntry(from: pb) {
            addEntry(content, thumbnail: thumbnail)
        }
    }

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
        entries.insert(e, at: 0)
        if entries.count > maxEntries { entries = Array(entries.prefix(maxEntries)) }
        selectedEntry = entries.first
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
