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
        case selectOnly(Entry)
        case toggleSelection(Entry)
        case selectRange(to: Entry)
        case dragSelectRange(anchorID: Entry.ID, target: Entry)
        case copy(Entry)
        case copyAndPromote(Entry)
        case repeatCopySelected
        case toggleFavorite(Entry)
        case delete(Entry)
        case deleteSelection
        case favoriteSelection
        case unfavoriteSelection
        case togglePredictionSuggestions
        case recordRecommendationAccepted(UUID)
        case dismissAllRecommendations
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
    @Published private(set) var selectedEntryIDs: Set<Entry.ID> = []
    @Published private(set) var searchText = ""
    @Published private(set) var filter: Filter = .all
    @Published private(set) var clipboardWriteErrorMessage: String?
    /// 存档损坏时的恢复提示（备份回退 / 原件保全）。UI 层可据此显示一次性提示。
    @Published private(set) var historyRecoveryNotice: String?
    @Published private(set) var showsPredictionSuggestions = false

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
                if "图片".localizedCaseInsensitiveContains(searchText) { return true }
                if let ocr = entry.ocrText, ocr.localizedCaseInsensitiveContains(searchText) { return true }
                return false
            case .file(let url):
                if url.lastPathComponent.localizedCaseInsensitiveContains(searchText) { return true }
                if let ocr = entry.ocrText, ocr.localizedCaseInsensitiveContains(searchText) { return true }
                return false
            case .files(let urls):
                return urls.contains { $0.lastPathComponent.localizedCaseInsensitiveContains(searchText) }
            }
        }
    }

    var favoriteCount: Int {
        entries.filter(\.isFavorite).count
    }

    var ordinaryCount: Int {
        entries.filter { !$0.isFavorite }.count
    }

    var selectedCount: Int {
        selectedEntryIDs.count
    }

    var hasSelection: Bool {
        !selectedEntryIDs.isEmpty
    }

    @Published private(set) var predictionContextSummary: String = ""

    @Published private(set) var predictionSuggestionEntries: [Entry] = []
    @Published private(set) var predictionReasonByEntryID: [UUID: String] = [:]

    func refreshPredictions() {
        // 显露偏好：启动 30s 监听窗口
        lastPredictionEntryIDs = Set(predictionSuggestionEntries.prefix(3).map(\.id))
        if lastPredictionEntryIDs.isEmpty { lastPredictionEntryIDs = [] }
        revealedPreferenceWindowTimer?.invalidate()
        revealedPreferenceWindowTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.revealedPreferenceWindowTimer = nil
            }
        }
        let capturedAt = Date()
        var collector = contextCollector
        let prefs = contextPreferences
        collector.preferences = prefs

        // 真实前台 App：优先用 monitor 实时记录的 lastFrontmostBundleID
        var effectiveApp: RunningApplicationContext?
        if let bid = lastFrontmostBundleID,
           let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == bid }) {
            effectiveApp = RunningApplicationContext(
                localizedName: app.localizedName,
                bundleIdentifier: bid,
                processIdentifier: app.processIdentifier
            )
        }
        if effectiveApp == nil {
            effectiveApp = entries.first.flatMap { e in
                e.sourceAppBundleID.map { RunningApplicationContext(localizedName: e.sourceAppName, bundleIdentifier: $0, processIdentifier: nil) }
            }
        }
        let currentAppName = effectiveApp?.localizedName
        let capturedEntries = entries
        let capturedSelectedID = selectedEntry?.id
        let capturedWeights = weightsStore.weights
        let capturedFeedback = feedbackStore.recent()
        let capturedEffectiveApp = effectiveApp
        let capturedPermissionState = prefs.permissionState
        let capturedEnablePrivacyFilter = prefs.canFilterSensitiveContent
        let capturedRecentEvents = collector.currentContext(recentEntries: [], selectedEntryID: nil, capturedAt: capturedAt, skipAppleScript: true).recentEvents

        Task.detached(priority: .userInitiated) { [weak self] in
            let summaries = ClipboardEntryIntelligenceAdapter().summaries(for: capturedEntries)
            var context = ContextSnapshot.minimal(recentEntries: summaries, selectedEntryID: capturedSelectedID, capturedAt: capturedAt)
            context.frontmostApplication = capturedEffectiveApp
            context.permissionState = capturedPermissionState
            context.recentEvents = capturedRecentEvents

            let result = LocalRecommendationService(
                engine: RuleBasedRecommendationEngine(now: capturedAt, weights: capturedWeights)
            ).recommend(
                entries: capturedEntries,
                selectedEntryID: capturedSelectedID,
                feedback: capturedFeedback,
                frontmostApplication: capturedEffectiveApp,
                limit: 3,
                capturedAt: capturedAt,
                enablePrivacyFilter: capturedEnablePrivacyFilter
            )
            let candidateIDs = result.candidates.map { $0.entryID }
            let entryMap = Dictionary(uniqueKeysWithValues: capturedEntries.map { ($0.id, $0) })
            var reasons: [UUID: String] = [:]
            for c in result.candidates {
                guard let entry = entryMap[c.entryID] else { continue }

                let kindLabel: String = {
                    switch entry.content {
                    case .text(let t):
                        if t.hasPrefix("http") { return "链接" }
                        if t.count < 200 && t.contains("\n") { return "文本片段" }
                        return "文本"
                    case .image: return "图片"
                    case .file: return "文件"
                    case .files: return "多文件"
                    }
                }()

                let f = c.score.features
                var tags: [String] = []

                if let current = currentAppName, let src = entry.sourceAppName, current == src {
                    // same app, no label
                } else if let current = currentAppName {
                    tags.append("当前在\(current)")
                }
                if let app = entry.sourceAppName, !tags.contains(where: { $0.hasPrefix("当前在") }) {
                    tags.append(app)
                }
                if (f[.recency] ?? 0) >= 0.34 { tags.append("刚刚复制") }
                if (f[.reuseFrequency] ?? 0) > 0 { tags.append("复用\(Int((f[.reuseFrequency] ?? 0)/0.08))次") }

                if (f[.contentTypeAffinity] ?? 0) > 0 {
                    let currentBID = context.frontmostApplication?.bundleIdentifier?.lowercased() ?? ""
                    if currentBID.contains("safari") || currentBID.contains("chrome") {
                        tags.append("偏好链接")
                    } else if currentBID.contains("finder") {
                        tags.append("偏好文件")
                    } else if currentBID.contains("xcode") || currentBID.contains("terminal") {
                        tags.append("偏好命令/代码")
                    } else if currentBID.contains("wechat") || currentBID.contains("telegram") {
                        tags.append("偏好文本/图片")
                    } else {
                        tags.append("内容匹配")
                    }
                }

                if (f[.appAffinity] ?? 0) > 0 {
                    if let src = entry.sourceAppName, let cur = currentAppName, src == cur {
                        tags.append("回到\(src)")
                    } else if let src = entry.sourceAppName, let cur = currentAppName {
                        tags.append("\(src)→\(cur)")
                    } else {
                        tags.append("App匹配")
                    }
                }

                if (f[.semanticSimilarity] ?? 0) > 0 {
                    let events = context.recentEvents
                    let copyBurst = events.suffix(4).filter { $0.kind == .copy }.count
                    let switches = events.suffix(4).filter { $0.kind == .switchToApp }.count
                    if copyBurst >= 3 && switches >= 1 {
                        tags.append("跨应用连续复制")
                    } else if copyBurst >= 3 {
                        tags.append("短时间内多次复制")
                    } else if switches >= 2 {
                        tags.append("频繁切换应用中")
                    } else {
                        tags.append("你刚复制过同类内容")
                    }
                }

                if (f[.finderDirectoryAffinity] ?? 0) > 0.5 {
                    if let dir = context.finderDirectory?.path {
                        let name = URL(fileURLWithPath: dir).lastPathComponent
                        tags.append("来自「\(name)」")
                    } else {
                        tags.append("同目录文件")
                    }
                }

                if (f[.finderSelectionAffinity] ?? 0) > 0.5 {
                    if let exts = context.finderSelection?.fileExtensions, !exts.isEmpty {
                        let extList = exts.prefix(2).joined(separator: "、")
                        if exts.count > 2 {
                            tags.append("选中 .\(extList) 等文件")
                        } else {
                            tags.append("选中 .\(extList)")
                        }
                    } else {
                        tags.append("同类文件被选中")
                    }
                }

                if (f[.negativeFeedback] ?? 0) < 0 { tags.append("已降权") }

                var parts: [String] = ["\(kindLabel)"]
                if !tags.isEmpty { parts.append(tags.joined(separator: " · ")) }
                parts.append("\(Int(c.score.value * 100))%")

                reasons[c.entryID] = parts.joined(separator: " · ")
            }

            var parts: [String] = []
            if let app = capturedEffectiveApp?.localizedName {
                parts.append("来源: \(app)")
            }
            let eventCount = context.recentEvents.count
            if eventCount > 0 {
                parts.append("轨迹: \(eventCount) 事件")
            }
            let fbCount = capturedFeedback.count
            if fbCount > 0 {
                parts.append("反馈: \(fbCount) 条")
            }
            let ctxSummary = parts.isEmpty ? "无额外上下文" : parts.joined(separator: " · ")

            let suggestionEntries = candidateIDs.compactMap { candidateID in
                capturedEntries.first { $0.id == candidateID }
            }

            await MainActor.run { [weak self] in
                self?.predictionReasonByEntryID = reasons
                self?.predictionContextSummary = ctxSummary
                self?.predictionSuggestionEntries = suggestionEntries
            }
        }
    }

    private var timer: Timer?
    private var delayedStartTask: Task<Void, Never>?
    private var intake: ClipboardIntake
    private let clipboardWriter: ClipboardWriting
    private let persistence: HistoryPersisting
    private let retentionPolicy: HistoryRetentionPolicy

    var contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings()
    var feedbackStore = RecommendationFeedbackStore()
    private var revealedPreferenceWindowTimer: Timer?
    private var lastPredictionEntryIDs: Set<UUID> = []

    var weightsStore = RecommendationWeightsStore()
    private var contextCollector = SystemContextCollector()

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
        let loadedRecoveryNotice = persistence.recoveryNotice
        let persistedEntries = Self.collapsingDuplicates(in: self.retentionPolicy.retaining(loadedEntries))
        self.entries = persistedEntries
        self.selectedEntry = persistedEntries.first
        self.selectedEntryIDs = persistedEntries.first.map { [$0.id] } ?? []
        if persistedEntries != loadedEntries {
            persist()
        }
        historyRecoveryNotice = loadedRecoveryNotice
        if let loadedRecoveryNotice {
            LifecycleDebugLogger.log("[历史存档恢复] \(loadedRecoveryNotice)")
        }
    }

    /// UI 消费掉恢复提示后调用，避免同一条提示反复出现。
    func dismissHistoryRecoveryNotice() {
        historyRecoveryNotice = nil
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

        startAppSwitchMonitor()
    }

    func stopMonitoring() {
        delayedStartTask?.cancel()
        delayedStartTask = nil
        timer?.invalidate()
        timer = nil
        stopAppSwitchMonitor()
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
            selectOnly(entry)
        case .selectOnly(let entry):
            selectOnly(entry)
        case .toggleSelection(let entry):
            toggleSelection(entry)
        case .selectRange(to: let entry):
            selectRange(to: entry)
        case .dragSelectRange(anchorID: let anchorID, target: let entry):
            selectRange(from: anchorID, to: entry)
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
        case .deleteSelection:
            deleteSelection()
        case .favoriteSelection:
            setFavoriteForSelection(true)
        case .unfavoriteSelection:
            setFavoriteForSelection(false)
        case .togglePredictionSuggestions:
            showsPredictionSuggestions.toggle()
            if showsPredictionSuggestions {
                refreshPredictions()
            } else {
                predictionSuggestionEntries = []
                predictionContextSummary = ""
            }
        case .recordRecommendationAccepted(let entryID):
            let context = contextCollector.currentContext(
                recentEntries: ClipboardEntryIntelligenceAdapter().summaries(for: entries),
                selectedEntryID: selectedEntry?.id,
                capturedAt: Date(),
                skipAppleScript: true
            )
            feedbackStore.recordAccepted(entryID: entryID, context: context)
            revealedPreferenceWindowTimer?.invalidate()
            revealedPreferenceWindowTimer = nil
        case .dismissAllRecommendations:
            let context = contextCollector.currentContext(
                recentEntries: ClipboardEntryIntelligenceAdapter().summaries(for: entries),
                selectedEntryID: selectedEntry?.id,
                capturedAt: Date(),
                skipAppleScript: true
            )
            for entry in predictionSuggestionEntries.prefix(3) {
                feedbackStore.recordDismissed(entryID: entry.id, context: context)
            }
            revealedPreferenceWindowTimer?.invalidate()
            revealedPreferenceWindowTimer = nil
            refreshPredictions()
        case .clear:
            clearAll()
        }
    }

    func isSelected(_ entry: Entry) -> Bool {
        selectedEntryIDs.contains(entry.id)
    }

    private func selectOnly(_ entry: Entry) {
        if entries.contains(where: { $0.id == entry.id }) {
            selectedEntry = entry
            selectedEntryIDs = [entry.id]
        }
    }

    private func toggleSelection(_ entry: Entry) {
        guard entries.contains(where: { $0.id == entry.id }) else { return }
        if selectedEntryIDs.contains(entry.id) {
            selectedEntryIDs.remove(entry.id)
            reconcileSelection()
        } else {
            selectedEntryIDs.insert(entry.id)
            selectedEntry = entry
        }
    }

    private func selectRange(to entry: Entry) {
        selectRange(from: selectedEntry?.id ?? selectedEntryIDs.first, to: entry)
    }

    private func selectRange(from anchorID: Entry.ID?, to entry: Entry) {
        let visibleEntries = filteredEntries
        guard let targetIndex = visibleEntries.firstIndex(where: { $0.id == entry.id }) else { return }
        let anchorID = anchorID ?? entry.id
        guard let anchorIndex = visibleEntries.firstIndex(where: { $0.id == anchorID }) else {
            selectOnly(entry)
            return
        }
        let bounds = min(anchorIndex, targetIndex)...max(anchorIndex, targetIndex)
        selectedEntryIDs = Set(visibleEntries[bounds].map(\.id))
        selectedEntry = entry
    }

    func add(_ intakeEntry: ClipboardIntake.Entry, timestamp: Date = Date()) {
        if promoteExistingEntryIfNeeded(for: intakeEntry, timestamp: timestamp) {
            return
        }

        guard let entry = intakeEntry.makeHistoryEntry(unlessDuplicateOf: entries.first, timestamp: timestamp) else {            return
        }

        entries.insert(entry, at: 0)
        entries = retentionPolicy.retaining(entries)
        reconcileSelection(preferredEntryID: entry.id)
        persist()
        scheduleOCRIfNeeded(for: entry)
        _ = contextCollector.recordCopy(entryID: entry.id)
        // 序列模式追踪
        
        // 显露偏好：如果推荐窗口打开期间用户手动复制了别的
        if revealedPreferenceWindowTimer != nil, !lastPredictionEntryIDs.contains(entry.id) {
            let context = contextCollector.currentContext(
                recentEntries: ClipboardEntryIntelligenceAdapter().summaries(for: entries),
                selectedEntryID: selectedEntry?.id,
                capturedAt: Date()
            )
            feedbackStore.recordCopiedManually(entryID: entry.id, context: context)
        }
        if showsPredictionSuggestions {
            refreshPredictions()
        }
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
        scheduleOCRIfNeeded(for: updatedEntry)
        // 序列模式追踪

        return true
    }

    private func scheduleOCRIfNeeded(for entry: Entry) {
        let entryID = entry.id
        let cgImage: CGImage?

        switch entry.content {
        case .image(let stored):
            Self.ocrLog("OCR triggered for .image entry \(entryID.uuidString.prefix(8))..., imageSize=\(stored.nsImage.size)")
            cgImage = stored.nsImage.cgImage(forProposedRect: nil, context: nil, hints: nil)
                ?? stored.nsImage.tiffRepresentation.flatMap({ NSBitmapImageRep(data: $0)?.cgImage })
        case .file(let url):
            guard Self.supportedImageExtensions.contains(url.pathExtension.lowercased()) else {
                Self.ocrLog("skip file OCR - \(url.lastPathComponent) not an image extension")
                return
            }
            Self.ocrLog("OCR triggered for .file entry \(entryID.uuidString.prefix(8))..., url=\(url.lastPathComponent)")
            guard let img = NSImage(contentsOf: url) else {
                Self.ocrLog("FAIL could not load NSImage from \(url.lastPathComponent)")
                return
            }
            cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil)
                ?? img.tiffRepresentation.flatMap({ NSBitmapImageRep(data: $0)?.cgImage })
        default:
            Self.ocrLog("skip OCR - not image or image-file entry")
            return
        }

        guard let cg = cgImage else {
            Self.ocrLog("FAIL cgImage extraction for \(entryID.uuidString.prefix(8))...")
            return
        }
        Self.ocrLog("cgImage extracted OK: \(cg.width)x\(cg.height)")

        DispatchQueue.global(qos: .utility).async {
            guard let text = SystemContextCollector.recognizeText(in: cg) else {
                Self.ocrLog("OCR returned nil text for \(entryID.uuidString.prefix(8))...")
                return
            }
            let wordCount = text.split(separator: " ").count
            Self.ocrLog("OCR done for \(entryID.uuidString.prefix(8))...: \(text.prefix(80))... (\(wordCount) tokens)")
            DispatchQueue.main.async { [weak self] in
                guard let self else { return }
                guard let idx = self.entries.firstIndex(where: { $0.id == entryID }) else {
                    Self.ocrLog("WARN entry \(entryID.uuidString.prefix(8))... no longer in entries array")
                    return
                }
                self.entries[idx] = self.entries[idx].updating(ocrText: text)
                self.persist()
                Self.ocrLog("persisted ocrText for \(entryID.uuidString.prefix(8))...")
            }
        }
    }

    private func refreshHistory() {
        if let intakeEntry = intake.refresh() {            add(intakeEntry)
        }
    }

    func scheduleOCRForExistingImages() {
        let needingOCR = entries.filter { entry in
            if entry.ocrText != nil { return false }
            switch entry.content {
            case .image: return true
            case .file(let url): return Self.supportedImageExtensions.contains(url.pathExtension.lowercased())
            default: return false
            }
        }
        Self.ocrLog("scheduleOCRForExistingImages: \(needingOCR.count) images need OCR out of \(entries.count) total")
        for entry in needingOCR {
            scheduleOCRIfNeeded(for: entry)
        }
    }

    private static let supportedImageExtensions: Set<String> = [
        "png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "heic", "heif", "webp", "ico", "svg"
    ]

        private nonisolated static func ocrLog(_ message: String) {
        // 统一走调试开关（CLIPBOARD_HISTORY_DEBUG=1）。
        // 旧实现无条件写 /tmp/ocr_debug.log，会把图片文件名与 OCR 文本前缀抄送到全局可写目录。
        LifecycleDebugLogger.logFromBackground("[OCR] \(Date()) \(message)")
    }

        private var appSwitchTimer: Timer?
    private var lastFrontmostBundleID: String?

    private func startAppSwitchMonitor() {
        stopAppSwitchMonitor()
        appSwitchTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.checkAppSwitch()
            }
        }
    }

    private func stopAppSwitchMonitor() {
        appSwitchTimer?.invalidate()
        appSwitchTimer = nil
    }

    private func checkAppSwitch() {
        guard let app = NSWorkspace.shared.frontmostApplication,
              let bundleID = app.bundleIdentifier,
              bundleID != Bundle.main.bundleIdentifier else { return }
        if bundleID != lastFrontmostBundleID {
            lastFrontmostBundleID = bundleID
            _ = contextCollector.recordAppSwitch()
        }
    }

    private func checkPasteboard() {
        if let intakeEntry = intake.readChangedEntry() {            add(intakeEntry)
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
        feedbackStore.removeEntries(withID: entry.id)
        reconcileSelection()
        persist()
    }

    private func deleteSelection() {
        guard !selectedEntryIDs.isEmpty else { return }
        let removedIDs = selectedEntryIDs
        entries.removeAll { removedIDs.contains($0.id) }
        feedbackStore.removeEntries(withIDs: removedIDs)
        reconcileSelection()
        persist()
    }

    private func setFavoriteForSelection(_ isFavorite: Bool) {
        guard !selectedEntryIDs.isEmpty else { return }
        var didChange = false
        entries = entries.map { entry in
            guard selectedEntryIDs.contains(entry.id),
                  entry.isFavorite != isFavorite else {
                return entry
            }
            didChange = true
            return entry.updating(isFavorite: isFavorite)
        }
        guard didChange else { return }
        entries = retentionPolicy.retaining(entries)
        reconcileSelection()
        persist()
    }

    private func clearAll() {
        let removedIDs = Set(entries.filter { !$0.isFavorite }.map(\.id))
        entries.removeAll { !$0.isFavorite }
        feedbackStore.removeEntries(withIDs: removedIDs)
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
        let visibleIDs = Set(visibleEntries.map(\.id))
        selectedEntryIDs = selectedEntryIDs.intersection(visibleIDs)
        if let preferredEntryID,
           let preferredEntry = visibleEntries.first(where: { $0.id == preferredEntryID }) {
            selectedEntry = preferredEntry
            selectedEntryIDs = [preferredEntryID]
            return
        }

        if !selectedEntryIDs.isEmpty,
           let selectedVisibleEntry = visibleEntries.first(where: { selectedEntryIDs.contains($0.id) }) {
            selectedEntry = selectedVisibleEntry
            return
        }

        if let selectedEntry,
           let currentEntry = visibleEntries.first(where: { $0.id == selectedEntry.id }) {
            self.selectedEntry = currentEntry
            if selectedEntryIDs.isEmpty {
                selectedEntryIDs = [currentEntry.id]
            }
            return
        }

        selectedEntry = visibleEntries.first
        selectedEntryIDs = selectedEntry.map { [$0.id] } ?? []
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
        case .files, .file, .text:
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
            sourceUTIs: intakeEntry.sourceUTIs.isEmpty ? duplicateEntry.sourceUTIs : intakeEntry.sourceUTIs,
            sourceAppBundleID: intakeEntry.sourceAppBundleID ?? duplicateEntry.sourceAppBundleID,
            sourceAppName: intakeEntry.sourceAppName ?? duplicateEntry.sourceAppName,
            ocrText: duplicateEntry.ocrText
        )
    }
}
