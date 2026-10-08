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

    @Published private(set) var entries: [Entry] = [] {
        didSet { invalidateFilteredCache() }
    }
    @Published private(set) var selectedEntry: Entry?
    @Published private(set) var selectedEntryIDs: Set<Entry.ID> = []
    @Published private(set) var searchText = "" {
        didSet { invalidateFilteredCache() }
    }
    @Published private(set) var filter: Filter = .all {
        didSet { invalidateFilteredCache() }
    }
    @Published private(set) var clipboardWriteErrorMessage: String?
    /// 存档损坏时的恢复提示（备份回退 / 原件保全）。UI 层可据此显示一次性提示。
    @Published private(set) var historyRecoveryNotice: String?
    /// 自动粘贴失败时要让用户看见原因，而不是"点了没反应"（审计 R-13）。
    @Published private(set) var pasteFailureNotice: String?

    /// 过滤结果缓存。`filteredEntries` 在一次界面求值里会被多处读取
    /// （列表、计数文案、空态标题、选中态协调），旧写法每次都全表重扫：
    /// 实测 500 条 ×1KB + 搜索词 = 13.8ms/次，一帧 3–5 次。
    private var cachedFilteredEntries: [Entry] = []
    private var filteredCacheIsValid = false

    private func invalidateFilteredCache() {
        filteredCacheIsValid = false
    }

    var filteredEntries: [Entry] {
        if filteredCacheIsValid { return cachedFilteredEntries }
        let computed = computeFilteredEntries()
        cachedFilteredEntries = computed
        filteredCacheIsValid = true
        return computed
    }

    private func computeFilteredEntries() -> [Entry] {
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
        // "显露偏好窗口"在结果真正显示出来的那一刻开启（见 applyPredictionResult），
        // 这里只负责：新一代开始计算时不要提前开窗。

        // 代际号：只有最新一代的结果允许回写界面。旧实现不取消也不比对代际，
        // 连续复制时后台任务完成顺序不确定 ⇒ 陈旧结果会盖掉新结果（审计 R-11）。
        predictionGeneration += 1
        let generation = predictionGeneration

        let capturedAt = Date()
        // 只把字符串快照交给后台：带 NSImage 的条目不再跨 actor 边界（审计 R-19）。
        let capturedSnapshots = entries.map(\.analysisSnapshot)
        let capturedSelectedID = selectedEntry?.id
        let capturedWeights = weightsStore.weights
        let capturedFeedback = feedbackStore.recent()
        let capturedEnablePrivacyFilter = contextPreferences.canFilterSensitiveContent
        let capturedEffectiveApp = effectiveFrontmostApp()

        var collector = contextCollector
        collector.preferences = contextPreferences
        let capturedRecentEvents = collector.currentContext(
            recentEntries: [],
            selectedEntryID: nil,
            capturedAt: capturedAt,
            skipAppleScript: true
        ).recentEvents

        var presenterContext = ContextSnapshot.minimal(recentEntries: [], capturedAt: capturedAt)
        presenterContext.frontmostApplication = capturedEffectiveApp
        presenterContext.recentEvents = capturedRecentEvents

        let capturedContextSummary = Self.predictionContextSummary(
            app: capturedEffectiveApp,
            eventCount: capturedRecentEvents.count,
            feedbackCount: capturedFeedback.count
        )
        let capturedCurrentAppName = capturedEffectiveApp?.localizedName
        let capturedReuseCounts = Self.reuseCounts(byEntryID: capturedFeedback)

        Task.detached(priority: .userInitiated) { [weak self] in
            let result = LocalRecommendationService(
                engine: RuleBasedRecommendationEngine(now: capturedAt, weights: capturedWeights)
            ).recommend(
                snapshots: capturedSnapshots,
                selectedEntryID: capturedSelectedID,
                feedback: capturedFeedback,
                frontmostApplication: capturedEffectiveApp,
                limit: 3,
                capturedAt: capturedAt,
                enablePrivacyFilter: capturedEnablePrivacyFilter
            )
            await MainActor.run { [weak self] in
                guard let self, self.predictionGeneration == generation else { return }
                self.applyPredictionResult(
                    result,
                    contextSummary: capturedContextSummary,
                    currentAppName: capturedCurrentAppName,
                    reuseCounts: capturedReuseCounts,
                    presenterContext: presenterContext
                )
            }
        }
    }

    private func applyPredictionResult(
        _ result: RecommendationResult,
        contextSummary: String,
        currentAppName: String?,
        reuseCounts: [UUID: Int],
        presenterContext: ContextSnapshot
    ) {
        var reasons: [UUID: String] = [:]
        var suggestionEntries: [Entry] = []
        for candidate in result.candidates {
            guard let entry = entries.first(where: { $0.id == candidate.entryID }) else { continue }
            reasons[candidate.entryID] = RecommendationPresenter.reason(
                for: candidate,
                entry: entry,
                context: presenterContext,
                currentAppName: currentAppName,
                reuseCount: reuseCounts[candidate.entryID] ?? 0
            )
            suggestionEntries.append(entry)
        }
        predictionReasonByEntryID = reasons
        predictionContextSummary = contextSummary
        predictionSuggestionEntries = suggestionEntries
        armRevealedPreferenceWindow(shownEntryIDs: suggestionEntries.prefix(3).map(\.id))
    }

    /// 推荐可见后的 30s 窗口：期间手动复制了不在这批推荐里的内容，
    /// 记为 copiedManually（隐式采纳信号）。不开窗 ⇒ 每次复制都会被当成"采纳"，
    /// 排序被自我强化（本轮实测：无条件开窗时反馈数从 2 变 3）。
    private func armRevealedPreferenceWindow(shownEntryIDs: [UUID]) {
        revealedPreferenceWindowTimer?.invalidate()
        guard !shownEntryIDs.isEmpty else {
            lastPredictionEntryIDs = []
            return
        }
        lastPredictionEntryIDs = Set(shownEntryIDs)
        revealedPreferenceWindowTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.revealedPreferenceWindowTimer = nil
                self?.lastPredictionEntryIDs = []
            }
        }
    }

    /// 真实前台 App：优先用应用切换监听记录的 bundleID，回退到最近一条记录的来源。
    private func effectiveFrontmostApp() -> RunningApplicationContext? {
        if let bundleID = lastFrontmostBundleID,
           let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == bundleID }) {
            return RunningApplicationContext(
                localizedName: app.localizedName,
                bundleIdentifier: bundleID,
                processIdentifier: app.processIdentifier
            )
        }
        return entries.first.flatMap { entry in
            entry.sourceAppBundleID.map {
                RunningApplicationContext(
                    localizedName: entry.sourceAppName,
                    bundleIdentifier: $0,
                    processIdentifier: nil
                )
            }
        }
    }

    private static func predictionContextSummary(
        app: RunningApplicationContext?,
        eventCount: Int,
        feedbackCount: Int
    ) -> String {
        var parts: [String] = []
        if let name = app?.localizedName {
            parts.append("来源: \(name)")
        }
        if eventCount > 0 {
            parts.append("轨迹: \(eventCount) 事件")
        }
        if feedbackCount > 0 {
            parts.append("反馈: \(feedbackCount) 条")
        }
        return parts.isEmpty ? "无额外上下文" : parts.joined(separator: " · ")
    }

    private static func reuseCounts(byEntryID feedback: [RecommendationFeedback]) -> [UUID: Int] {
        var counts: [UUID: Int] = [:]
        for item in feedback where item.kind == .accepted || item.kind == .copiedManually {
            counts[item.entryID, default: 0] += 1
        }
        return counts
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
    private var predictionGeneration = 0

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
        cachedFilteredEntries = computeFilteredEntries()
        filteredCacheIsValid = true
        historyRecoveryNotice = loadedRecoveryNotice
        if let loadedRecoveryNotice {
            LifecycleDebugLogger.log("[历史存档恢复] \(loadedRecoveryNotice)")
        }
    }

    /// UI 消费掉恢复提示后调用，避免同一条提示反复出现。
    func dismissHistoryRecoveryNotice() {
        historyRecoveryNotice = nil
    }

    /// 记录一次自动粘贴失败。只接受调用方已经脱敏过的原因文案（见 `SystemEventsPasteKey`）。
    func reportPasteFailure(_ reason: String) {
        pasteFailureNotice = reason
    }

    func dismissPasteFailure() {
        pasteFailureNotice = nil
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

        // 显露偏好：如果推荐窗口打开期间用户手动复制了别的
        if revealedPreferenceWindowTimer != nil, !lastPredictionEntryIDs.contains(entry.id) {
            let context = contextCollector.currentContext(
                recentEntries: ClipboardEntryIntelligenceAdapter().summaries(for: entries),
                selectedEntryID: selectedEntry?.id,
                capturedAt: Date()
            )
            feedbackStore.recordCopiedManually(entryID: entry.id, context: context)
        }
        // 每次新复制都重算一次推荐：菜单栏可能随时被打开，而"每 2 秒轮询"在
        // 无事发生时也在做全库分析（审计 R-11/R-21）。按复制事件驱动，
        // 频率由用户动作决定，代价有界。
        refreshPredictions()
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

        return true
    }

    /// OCR 的像素解码不再发生在主线程（审计 R-23）。
    ///
    /// 主线程只负责拿到"字节或 URL"——存档里的条目本来就带 PNG 字节，这一步是零成本；
    /// 解码与识别都在一条串行后台队列上完成，所以启动时扫描 N 张图不会再
    /// 连续 N 次卡主线程，也不会并发抢满 CPU 核。
    /// 解码上限 1200px：认字不需要原始分辨率，整幅解一张 4000×3000 只是浪费。
    private func scheduleOCRIfNeeded(for entry: Entry) {
        let entryID = entry.id
        let source: OCRImageSource

        switch entry.content {
        case .image(let stored):
            guard let data = stored.pngData() else {
                Self.ocrLog("FAIL no image bytes for \(entryID.uuidString.prefix(8))...")
                return
            }
            Self.ocrLog("OCR queued for .image entry \(entryID.uuidString.prefix(8))..., bytes=\(data.count)")
            source = .data(data)
        case .file(let url):
            guard Self.supportedImageExtensions.contains(url.pathExtension.lowercased()) else {
                Self.ocrLog("skip file OCR - \(url.lastPathComponent) not an image extension")
                return
            }
            Self.ocrLog("OCR queued for .file entry \(entryID.uuidString.prefix(8))..., name=\(url.lastPathComponent)")
            source = .url(url)
        default:
            Self.ocrLog("skip OCR - not image or image-file entry")
            return
        }

        Self.ocrQueue.async {
            guard let cg = Self.decodeImageForOCR(source) else {
                Self.ocrLog("FAIL decode for \(entryID.uuidString.prefix(8))...")
                return
            }
            guard let text = SystemContextCollector.recognizeText(in: cg) else {
                Self.ocrLog("OCR returned nil text for \(entryID.uuidString.prefix(8))...")
                return
            }
            // 只记长度，不记内容：截图 OCR 出来的文字完全可能就是密码或令牌。
            Self.ocrLog("OCR done for \(entryID.uuidString.prefix(8))...: chars=\(text.count) \(cg.width)x\(cg.height)")
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

    /// 给 OCR 用的图片来源：只有字节或 URL 是 Sendable 的，NSImage 不进后台（D-010）。
    enum OCRImageSource: Sendable {
        case data(Data)
        case url(URL)
    }

    /// 串行队列：启动时扫描整库图片也不会并发抢满核心，且主线程完全不参与解码。
    nonisolated private static let ocrQueue = DispatchQueue(label: "com.clipboardhistory.ocr", qos: .utility)

    /// 用 ImageIO 直接解出"够认字"的一帧，顺带处理 EXIF 方向。
    /// 比 `NSImage(contentsOf:)` + `cgImage(forProposedRect:)` 少一次整幅位图落地。
    /// internal 而非 private：这条函数是"像素解码发生在哪儿"这件事唯一可测的接缝。
    nonisolated static func decodeImageForOCR(_ source: OCRImageSource, maxPixel: Int = 1_200) -> CGImage? {
        let imageSource: CGImageSource?
        switch source {
        case .data(let data):
            imageSource = CGImageSourceCreateWithData(data as CFData, nil)
        case .url(let url):
            imageSource = CGImageSourceCreateWithURL(url as CFURL, nil)
        }
        guard let imageSource else { return nil }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixel,
        ]
        return CGImageSourceCreateThumbnailAtIndex(imageSource, 0, options as CFDictionary)
    }

        private nonisolated static func ocrLog(_ message: String) {
        // 统一走调试开关（CLIPBOARD_HISTORY_DEBUG=1）。
        // 旧实现无条件写 /tmp/ocr_debug.log，会把图片文件名与 OCR 文本前缀抄送到全局可写目录。
        LifecycleDebugLogger.logFromBackground("[OCR] \(Date()) \(message)")
    }

        private var appSwitchObserver: NSObjectProtocol?
    private var lastFrontmostBundleID: String?

    /// 用 `NSWorkspace.didActivateApplicationNotification` 取代 1 秒轮询：
    /// 事件精确（不会漏掉 1s 内的来回切换），空闲时完全不产生 wake-up（审计 R-21）。
    private func startAppSwitchMonitor() {
        stopAppSwitchMonitor()
        appSwitchObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
            Task { @MainActor [weak self] in
                self?.handleApplicationActivated(app)
            }
        }
    }

    private func stopAppSwitchMonitor() {
        if let appSwitchObserver {
            NSWorkspace.shared.notificationCenter.removeObserver(appSwitchObserver)
            self.appSwitchObserver = nil
        }
    }

    private func handleApplicationActivated(_ app: NSRunningApplication?) {
        guard let bundleID = app?.bundleIdentifier,
              bundleID != Bundle.main.bundleIdentifier else { return }
        if bundleID != lastFrontmostBundleID {
            lastFrontmostBundleID = bundleID
            _ = contextCollector.recordAppSwitch()
            // 前台 App 变了，"猜你要粘贴"的依据就变了
            refreshPredictions()
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
