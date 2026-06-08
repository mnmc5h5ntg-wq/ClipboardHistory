import AppKit
import Combine

@MainActor
final class HistoryStore: ObservableObject {
    typealias Entry = ClipboardEntry

    enum Action {
        case refresh
        case updateSearch(String)
        case updateFilter(Filter)
        case select(Entry)
        case copy(Entry)
        case copyAndPromote(Entry)
        case repeatCopySelected
        case toggleFavorite(Entry)
        case delete(Entry)
        case clear
    }

    enum Filter: String, CaseIterable, Identifiable {
        case all
        case favorites

        var id: String { rawValue }

        var title: String {
            switch self {
            case .all:
                return "全部"
            case .favorites:
                return "收藏"
            }
        }
    }

    @Published private(set) var entries: [Entry] = []
    @Published private(set) var selectedEntry: Entry?
    @Published private(set) var searchText = ""
    @Published private(set) var filter: Filter = .all
    @Published private(set) var clipboardWriteErrorMessage: String?

    var filteredEntries: [Entry] {
        let entriesForFilter = entries.filter { entry in
            switch filter {
            case .all:
                return true
            case .favorites:
                return entry.isFavorite
            }
        }

        guard !searchText.isEmpty else { return entriesForFilter }
        return entriesForFilter.filter { entry in
            switch entry.content {
            case .text(let string):
                return string.localizedCaseInsensitiveContains(searchText)
            case .image:
                return "图片".localizedCaseInsensitiveContains(searchText)
            case .file(let url):
                return url.lastPathComponent.localizedCaseInsensitiveContains(searchText)
            }
        }
    }

    var favoriteCount: Int {
        entries.filter(\.isFavorite).count
    }

    var ordinaryCount: Int {
        entries.filter { !$0.isFavorite }.count
    }

    private var timer: Timer?
    private var delayedStartTask: Task<Void, Never>?
    private var intake: ClipboardIntake
    private let clipboardWriter: ClipboardWriting
    private let persistence: HistoryPersisting
    private let retentionPolicy: HistoryRetentionPolicy

    init(
        intake: ClipboardIntake = ClipboardIntake(),
        clipboardWriter: ClipboardWriting = SystemClipboardWriter(),
        persistence: HistoryPersisting = FileHistoryPersistence(),
        retentionPolicy: HistoryRetentionPolicy = .default,
        maxEntries: Int? = nil
    ) {
        self.intake = intake
        self.clipboardWriter = clipboardWriter
        self.persistence = persistence
        if let maxEntries {
            self.retentionPolicy = HistoryRetentionPolicy(maxEntries: maxEntries, maxAgeDays: retentionPolicy.maxAgeDays)
        } else {
            self.retentionPolicy = retentionPolicy
        }
        let loadedEntries = persistence.load()
        let persistedEntries = Self.collapsingDuplicates(in: self.retentionPolicy.retaining(loadedEntries))
        self.entries = persistedEntries
        self.selectedEntry = persistedEntries.first
        if persistedEntries != loadedEntries {
            persist()
        }
    }

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
            Task { @MainActor [weak self] in
                self?.checkPasteboard()
            }
        }
    }

    func stopMonitoring() {
        delayedStartTask?.cancel()
        delayedStartTask = nil
        timer?.invalidate()
        timer = nil
    }

    func flushPendingPersistence() {
        persistence.flushPendingSaves()
    }

    func perform(_ action: Action) {
        switch action {
        case .refresh:
            refreshHistory()
        case .updateSearch(let text):
            searchText = text
            reconcileSelection()
        case .updateFilter(let filter):
            self.filter = filter
            reconcileSelection()
        case .select(let entry):
            selectedEntry = entry
        case .copy(let entry):
            copyToClipboard(entry)
        case .copyAndPromote(let entry):
            copyToClipboardAndPromote(entry)
        case .repeatCopySelected:
            repeatCopySelectedEntry()
        case .toggleFavorite(let entry):
            toggleFavorite(entry)
        case .delete(let entry):
            delete(entry)
        case .clear:
            clearAll()
        }
    }

    func add(_ intakeEntry: ClipboardIntake.Entry, timestamp: Date = Date()) {
        if promoteExistingEntryIfNeeded(for: intakeEntry, timestamp: timestamp) {
            return
        }

        guard let entry = intakeEntry.makeHistoryEntry(unlessDuplicateOf: entries.first, timestamp: timestamp) else {
            return
        }

        entries.insert(entry, at: 0)
        entries = retentionPolicy.retaining(entries)
        reconcileSelection(preferredEntryID: entry.id)
        persist()
    }

    private func promoteExistingEntryIfNeeded(for intakeEntry: ClipboardIntake.Entry, timestamp: Date) -> Bool {
        let matchingEntries = entries.filter { Self.isDuplicate($0, of: intakeEntry) }
        guard let duplicateEntry = matchingEntries.first else {
            return false
        }

        let matchingIDs = Set(matchingEntries.map(\.id))
        let isFavorite = matchingEntries.contains { $0.isFavorite }
        entries.removeAll { matchingIDs.contains($0.id) }
        let updatedEntry = Self.entry(
            from: duplicateEntry,
            replacingWith: intakeEntry,
            timestamp: timestamp,
            isFavorite: isFavorite
        )
        entries.insert(updatedEntry, at: 0)
        entries = retentionPolicy.retaining(entries)
        reconcileSelection(preferredEntryID: updatedEntry.id)
        persist()
        return true
    }

    private func refreshHistory() {
        if let intakeEntry = intake.refresh() {
            add(intakeEntry)
        }
    }

    private func checkPasteboard() {
        if let intakeEntry = intake.readChangedEntry() {
            add(intakeEntry)
        }
    }

    private func copyToClipboard(_ entry: Entry) {
        writeToClipboard(entry)
    }

    private func copyToClipboardAndPromote(_ entry: Entry) {
        guard writeToClipboard(entry) else { return }
        let isFavorite = entries.first { $0.id == entry.id }?.isFavorite ?? entry.isFavorite
        entries.removeAll { $0.id == entry.id }
        let updatedEntry = entry.updating(timestamp: Date(), isFavorite: isFavorite)
        entries.insert(updatedEntry, at: 0)
        entries = retentionPolicy.retaining(entries)
        reconcileSelection(preferredEntryID: updatedEntry.id)
        persist()
    }

    private func repeatCopySelectedEntry() {
        guard let selectedEntry else { return }
        copyToClipboardAndPromote(selectedEntry)
    }

    @discardableResult
    private func writeToClipboard(_ entry: Entry) -> Bool {
        do {
            let changeCount = try clipboardWriter.write(entry.content)
            clipboardWriteErrorMessage = nil
            intake.markChangeCount(changeCount)
            return true
        } catch {
            clipboardWriteErrorMessage = error.localizedDescription
            LifecycleDebugLogger.log("HistoryStore clipboard write failed error=\(error)")
            return false
        }
    }

    private func toggleFavorite(_ entry: Entry) {
        guard let index = entries.firstIndex(where: { $0.id == entry.id }) else { return }
        let updatedEntry = entries[index].updating(isFavorite: !entries[index].isFavorite)
        entries[index] = updatedEntry
        entries = retentionPolicy.retaining(entries)
        reconcileSelection(preferredEntryID: updatedEntry.id)
        persist()
    }

    private func delete(_ entry: Entry) {
        entries.removeAll { $0.id == entry.id }
        reconcileSelection()
        persist()
    }

    private func clearAll() {
        entries.removeAll { !$0.isFavorite }
        reconcileSelection()
        persist()
    }

    private func persist() {
        do {
            try persistence.save(entries)
        } catch {
            LifecycleDebugLogger.log("HistoryStore persistence failed error=\(error)")
        }
    }

    private func reconcileSelection(preferredEntryID: Entry.ID? = nil) {
        let visibleEntries = filteredEntries
        if let preferredEntryID,
           let preferredEntry = visibleEntries.first(where: { $0.id == preferredEntryID }) {
            selectedEntry = preferredEntry
            return
        }

        if let selectedEntry,
           let currentEntry = visibleEntries.first(where: { $0.id == selectedEntry.id }) {
            self.selectedEntry = currentEntry
            return
        }

        selectedEntry = visibleEntries.first
    }

    private static func collapsingDuplicates(in entries: [Entry]) -> [Entry] {
        entries.reduce(into: []) { collapsedEntries, entry in
            guard let existingIndex = collapsedEntries.firstIndex(where: { isDuplicate($0, of: entry) }) else {
                collapsedEntries.append(entry)
                return
            }

            collapsedEntries[existingIndex] = collapsedEntries[existingIndex]
                .updating(isFavorite: collapsedEntries[existingIndex].isFavorite || entry.isFavorite)
        }
    }

    private static func isDuplicate(_ entry: Entry, of intakeEntry: ClipboardIntake.Entry) -> Bool {
        hasSameDuplicateIdentity(
            content: entry.content,
            thumbnail: entry.thumbnail,
            as: intakeEntry.content,
            thumbnail: intakeEntry.thumbnail
        )
    }

    private static func isDuplicate(_ lhs: Entry, of rhs: Entry) -> Bool {
        hasSameDuplicateIdentity(
            content: lhs.content,
            thumbnail: lhs.thumbnail,
            as: rhs.content,
            thumbnail: rhs.thumbnail
        )
    }

    private static func hasSameDuplicateIdentity(
        content lhsContent: ClipboardEntryContent,
        thumbnail lhsThumbnail: StoredImage?,
        as rhsContent: ClipboardEntryContent,
        thumbnail rhsThumbnail: StoredImage?
    ) -> Bool {
        if lhsContent == rhsContent {
            return true
        }

        guard let lhsImage = duplicateImageIdentity(for: lhsContent, thumbnail: lhsThumbnail),
              let rhsImage = duplicateImageIdentity(for: rhsContent, thumbnail: rhsThumbnail) else {
            return false
        }
        return lhsImage == rhsImage
    }

    private static func duplicateImageIdentity(
        for content: ClipboardEntryContent,
        thumbnail: StoredImage?
    ) -> StoredImage? {
        switch content {
        case .image(let image):
            return image
        case .file(let url) where FileTypeSupport.imageExtensions.contains(url.pathExtension.lowercased()):
            return thumbnail
        case .file, .text:
            return nil
        }
    }

    private static func entry(
        from duplicateEntry: Entry,
        replacingWith intakeEntry: ClipboardIntake.Entry,
        timestamp: Date,
        isFavorite: Bool
    ) -> Entry {
        Entry(
            id: duplicateEntry.id,
            content: intakeEntry.content,
            timestamp: timestamp,
            thumbnail: intakeEntry.thumbnail ?? duplicateEntry.thumbnail,
            sourceURL: intakeEntry.content.sourceURL,
            isFavorite: isFavorite,
            sourceUTIs: intakeEntry.sourceUTIs.isEmpty ? duplicateEntry.sourceUTIs : intakeEntry.sourceUTIs
        )
    }
}
