import AppKit
import Foundation

struct HistoryRetentionPolicy: Equatable {
    static let `default` = HistoryRetentionPolicy(maxEntries: 500, maxAgeDays: 30)

    let maxEntries: Int
    let maxAgeDays: Int?

    func retaining(_ entries: [ClipboardEntry], now: Date = Date()) -> [ClipboardEntry] {
        let cutoff = maxAgeDays.map {
            now.addingTimeInterval(-Double($0) * 24 * 60 * 60)
        }
        let retainedFavorites = entries.filter(\.isFavorite)
        let retainedOrdinary = entries
            .filter { !$0.isFavorite }
            .filter { entry in
                guard let cutoff else { return true }
                return entry.timestamp >= cutoff
            }
            .sorted { $0.timestamp > $1.timestamp }
            .prefix(maxEntries)
        return (retainedFavorites + Array(retainedOrdinary)).sorted { $0.timestamp > $1.timestamp }
    }
}

@MainActor
protocol HistoryPersisting {
    func load() -> [ClipboardEntry]
    func save(_ entries: [ClipboardEntry]) throws
    func flushPendingSaves()
    /// 上一次载入时是否走了"存档损坏 → 保全原件/从备份恢复"路径。
    var recoveryNotice: String? { get }
}

extension HistoryPersisting {
    func flushPendingSaves() {}
    var recoveryNotice: String? { nil }
}

@MainActor
final class FileHistoryPersistence: HistoryPersisting {
    /// 存档格式版本。以前这个字段只写不读（审计 R-20）：装了更新的版本再退回本版本时，
    /// 新格式的字段会被当成不认识的东西丢掉，而下一次保存就把 v2 覆盖成 v1 —— 静默数据损失。
    static let currentSchemaVersion = 1

    private struct StoredHistory: Codable, Sendable {
        let version: Int
        let entries: [StoredEntry]
    }

    private struct StoredEntry: Codable, Sendable {
        enum ContentKind: String, Codable, Sendable {
            case text
            case image
            case file
        }

        let id: UUID
        let timestamp: Date
        let contentKind: ContentKind
        let text: String?
        let urlString: String?
        let urlStrings: [String]?
        let imageFileName: String?
        let thumbnailFileName: String?
        let isFavorite: Bool?
        let sourceUTIs: [String]
        /// 来源 App（审计第二轮 B-2 / 账本 R2-07）：以前只在内存里，重启后归因全丢，
        /// 于是 `appAffinity` 对"载入的历史"恒为 0 —— 推荐权重里有一项永远算不出来。
        /// 两个字段都是 Optional，旧存档缺键时解出 nil，**不需要**升 schema 版本；
        /// 旧版本程序读到多出来的键也会忽略（Codable 默认行为），所以双向兼容。
        let sourceAppBundleID: String?
        let sourceAppName: String?
        let ocrText: String?
        /// 「固定」位（第三轮审计 §5 F-5）。可选字段、缺键读为 false ⇒ 按 D-016 的
        /// "只加可选字段不升版"策略，`currentSchemaVersion` 保持 1；旧版读到这个键会忽略它。
        let isPinned: Bool?
        /// 富文本两份表示（§5 F-2）。都是 Optional：缺键 ⇒ nil ⇒ 老存档原样读回，
        /// 按 D-016 的"只加可选字段不升版"，`currentSchemaVersion` 保持 1。
        /// 它们会让 `history.json` 变大（上限见 `RichTextPolicy.maximumTotalBytes`），
        /// 所以采集侧默认关；导出时和图片一样被跳过。
        let richTextRTF: Data?
        let richTextHTML: Data?

        /// 读回来时两份都没有就当作没有富文本，而不是造一个空壳。
        var richText: RichTextPayload? {
            let payload = RichTextPayload(rtf: richTextRTF, html: richTextHTML)
            return payload.isEmpty ? nil : payload
        }

        var fileURLs: [URL] {
            if let urlStrings, !urlStrings.isEmpty {
                return urlStrings.compactMap(URL.init(string:))
            }
            if let urlString, let url = URL(string: urlString) {
                return [url]
            }
            return []
        }
    }

    private struct PendingImageWrite: Sendable {
        let fileName: String
        let data: Data
    }

    private struct SaveSnapshot: Sendable {
        let storedHistory: StoredHistory
        let imageWrites: [PendingImageWrite]
        let usedImageFileNames: Set<String>
    }

    private let rootDirectory: URL
    private let fileManager: FileManager
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    private let saveQueue: DispatchQueue
    private var pendingSave: DispatchWorkItem?
    private var loadedRecoveryNotice: String?
    /// 本次运行内必须保护的图片文件名（来自损坏原件与备份的尽力提取）。
    private var protectedImageFileNames: Set<String> = []

    /// 存档来自更高版本时置位：本程序只读打开，不再写盘。
    private(set) var isArchiveFromNewerVersion = false

    var recoveryNotice: String? { loadedRecoveryNotice }
    var backupHistoryURL: URL { FileHistoryPersistence.backupURL(for: historyURL) }

    init(
        rootDirectory: URL = FileHistoryPersistence.defaultRootDirectory(),
        fileManager: FileManager = .default,
        saveQueue: DispatchQueue? = nil
    ) {
        self.rootDirectory = rootDirectory
        self.fileManager = fileManager
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()
        self.saveQueue = saveQueue ?? DispatchQueue(
            label: "ClipboardHistory.FileHistoryPersistence.save",
            qos: .utility
        )
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func load() -> [ClipboardEntry] {
        flushPendingSaves()
        loadedRecoveryNotice = nil
        protectedImageFileNames = []
        // 只读标志也必须跟着每次载入复位：否则同一实例先载入一份"更新版本写的存档"、
        // 再载入一份当前版本存档时，save() 仍被上一次的标志错误地禁用（审计 N-3）。
        isArchiveFromNewerVersion = false

        guard let storedHistory = decodeStoredHistory(at: historyURL) else {
            // 文件不存在 = 首次运行（或用户手工清空），正常空态。
            if !fileManager.fileExists(atPath: historyURL.path) {
                guard let backup = decodeStoredHistory(at: backupHistoryURL) else { return [] }
                loadedRecoveryNotice = "主存档不存在，已从备份恢复 \(backup.entries.count) 条记录。"
                protectedImageFileNames.formUnion(Self.imageFileNames(from: backup))
                return entries(from: backup)
            }
            // 存在但解析不了（崩溃/断电留下的半截 JSON）。
            // 关键：先保全原件副本，再尝试滚动备份；两种手段都失败时也要保护旧图片文件，
            // 否则"下一次复制"就会把整个历史库连图片一起删掉（审计 P-06 复现过的缺陷）。
            let preserved = Self.preserveCorruptFile(at: historyURL)
            protectedImageFileNames.formUnion(Self.looseImageFileNames(inFileAt: historyURL))
            if let backup = decodeStoredHistory(at: backupHistoryURL) {
                protectedImageFileNames.formUnion(Self.imageFileNames(from: backup))
                loadedRecoveryNotice = "存档无法解析，已从备份恢复 \(backup.entries.count) 条记录；"
                    + "损坏原件保全在 \(preserved?.lastPathComponent ?? "未知位置")。"
                return entries(from: backup)
            }
            loadedRecoveryNotice = "存档无法解析，原件保全在 "
                + "\(preserved?.lastPathComponent ?? "未知位置")；本次以空历史启动，旧图片文件不会被删除。"
            return []
        }

        return entries(from: accept(storedHistory))
    }

    /// 版本闸门：高于本程序支持的版本 ⇒ 只读打开并说明原因；否则走显式迁移。
    private func accept(_ storedHistory: StoredHistory) -> StoredHistory {
        if storedHistory.version > Self.currentSchemaVersion {
            isArchiveFromNewerVersion = true
            loadedRecoveryNotice = "这份历史存档由更新的版本写入（v\(storedHistory.version) > v\(Self.currentSchemaVersion)），"
                + "本版本只读打开，不会覆盖它。请升级回原来的版本继续使用该存档。"
            LifecycleDebugLogger.log("存档版本 v\(storedHistory.version) 高于本程序 v\(Self.currentSchemaVersion)：进入只读")
            return storedHistory
        }
        return Self.migrate(storedHistory)
    }

    /// 唯一的迁移入口。以后改格式必须在这里加一级显式升级，
    /// 让"忘了写迁移"成为一件会在代码评审里被看见的事，而不是静默行为差异。
    ///
    /// 版本策略（D-016 的决定，第三轮审计 D-5 把它写成边界而不只是注释）：
    /// ① **只加可选字段不升版** —— 升版会让旧版程序把存档判成只读（见上面 `进入只读` 那条分支），
    ///    用户"升级后又能用"的承诺会被打断；
    /// ② 一旦**改语义或删字段**就必须升 v2 并在这里加一级显式升级 ——
    ///    可选字段的 additive 规则救不了"同一个键含义变了"。
    /// ① 的可信度由 `Round3AuditFixTests.testArchiveWrittenByNewerCodeStillOpensForOlderCode` 钉住
    /// （新→旧→新 的往返），不要只靠这段话。
    nonisolated private static func migrate(_ history: StoredHistory) -> StoredHistory {
        switch history.version {
        case 1:
            return history
        default:
            // 比当前更低的版本：目前没有需要升格的旧格式；字段都是可选的，原样载入不会崩。
            return history
        }
    }

    private func decodeStoredHistory(at url: URL) -> StoredHistory? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? decoder.decode(StoredHistory.self, from: data)
    }

    private func entries(from storedHistory: StoredHistory) -> [ClipboardEntry] {
        return storedHistory.entries.compactMap { storedEntry in
            switch storedEntry.contentKind {
            case .text:
                guard let text = storedEntry.text else { return nil }
                return entry(from: storedEntry, content: .text(text), thumbnail: nil)
            case .image:
                guard let imageFileName = storedEntry.imageFileName,
                      let image = loadImage(named: imageFileName) else {
                    return nil
                }
                return entry(from: storedEntry, content: .image(image), thumbnail: image)
            case .file:
                let urls = storedEntry.fileURLs
                guard !urls.isEmpty else {
                    return nil
                }
                let content: ClipboardEntryContent = urls.count == 1 ? .file(urls[0]) : .files(urls)
                let thumbnail = storedEntry.thumbnailFileName.flatMap { loadImage(named: $0) }
                return entry(from: storedEntry, content: content, thumbnail: thumbnail)
            }
        }
    }

    func save(_ entries: [ClipboardEntry]) throws {
        guard !isArchiveFromNewerVersion else {
            // 覆盖一份更高版本的存档 = 把它的新字段抹掉。宁可这次复制不落盘，也不能毁数据。
            LifecycleDebugLogger.log("存档来自更高版本：跳过写入")
            return
        }
        let snapshot = try saveSnapshot(from: entries)
        // 去抖：连续保存时，让还没开始执行的那一次被后一次取代 —— 快照是**整库**的，
        // 后一次包含前一次的全部内容，所以丢弃前一次不会丢数据。
        // 刻意**不**用定时器延时落盘：那会在"复制完立刻退出 App"时丢掉最后一条。
        pendingSave?.cancel()
        let workItem = Self.makeSaveWorkItem(
            snapshot: snapshot,
            rootDirectory: rootDirectory,
            protectedImageFileNames: protectedImageFileNames
        )
        pendingSave = workItem
        saveQueue.async(execute: workItem)
    }

    func flushPendingSaves() {
        pendingSave?.wait()
        pendingSave = nil
    }

    /// 存档根目录。
    ///
    /// `CLIPBOARD_HISTORY_DATA_DIR` 是给**运行时冒烟测试**用的隔离开关（第三轮审计 C-4）：
    /// 它让 CI 可以真的把打包后的 app 启起来看一眼，而不碰用户 `~/Library/Application Support/时间剪史/`
    /// 里那份真存档（D-002 的边界）。名字里带 DATA 而不是 HOME，就是为了不冒充别的语义。
    /// 只有显式设置且非空才生效，没设置时行为与改动前逐字节相同。
    static let dataDirectoryEnvironmentKey = "CLIPBOARD_HISTORY_DATA_DIR"

    static func defaultRootDirectory() -> URL {
        if let override = ProcessInfo.processInfo.environment[dataDirectoryEnvironmentKey],
           !override.isEmpty {
            return URL(fileURLWithPath: (override as NSString).expandingTildeInPath, isDirectory: true)
        }
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support")
        return base.appendingPathComponent("时间剪史", isDirectory: true)
    }

    private var historyURL: URL {
        rootDirectory.appendingPathComponent("history.json")
    }

    private var imagesDirectory: URL {
        rootDirectory.appendingPathComponent("images", isDirectory: true)
    }

    private func entry(
        from storedEntry: StoredEntry,
        content: ClipboardEntryContent,
        thumbnail: StoredImage?
    ) -> ClipboardEntry {
        ClipboardEntry(
            id: storedEntry.id,
            content: content,
            timestamp: storedEntry.timestamp,
            thumbnail: thumbnail,
            sourceURL: content.sourceURL,
            isFavorite: storedEntry.isFavorite ?? false,
            sourceUTIs: storedEntry.sourceUTIs,
            sourceAppBundleID: storedEntry.sourceAppBundleID,
            sourceAppName: storedEntry.sourceAppName,
            ocrText: storedEntry.ocrText,
            isPinned: storedEntry.isPinned ?? false,
            richText: storedEntry.richText
        )
    }

    private func saveSnapshot(from entries: [ClipboardEntry]) throws -> SaveSnapshot {
        var imageWrites: [PendingImageWrite] = []
        let storedEntries = try entries.map { try storedEntry(from: $0, imageWrites: &imageWrites) }
        return SaveSnapshot(
            storedHistory: StoredHistory(version: 1, entries: storedEntries),
            imageWrites: imageWrites,
            usedImageFileNames: Set(storedEntries.flatMap { [$0.imageFileName, $0.thumbnailFileName].compactMap(\.self) })
        )
    }

    private func storedEntry(
        from entry: ClipboardEntry,
        imageWrites: inout [PendingImageWrite]
    ) throws -> StoredEntry {
        switch entry.content {
        case .text(let text):
            return StoredEntry(
                id: entry.id,
                timestamp: entry.timestamp,
                contentKind: .text,
                text: text,
                urlString: nil,
                urlStrings: nil,
                imageFileName: nil,
                thumbnailFileName: nil,
                isFavorite: entry.isFavorite,
                sourceUTIs: entry.sourceUTIs,
                sourceAppBundleID: entry.sourceAppBundleID,
                sourceAppName: entry.sourceAppName,
                ocrText: entry.ocrText,
                isPinned: entry.isPinned,
                richTextRTF: entry.richText?.rtf,
                richTextHTML: entry.richText?.html
            )
        case .image(let image):
            let imageFileName = "\(entry.id.uuidString)-image.png"
            try append(image, named: imageFileName, to: &imageWrites)
            return StoredEntry(
                id: entry.id,
                timestamp: entry.timestamp,
                contentKind: .image,
                text: nil,
                urlString: nil,
                urlStrings: nil,
                imageFileName: imageFileName,
                thumbnailFileName: nil,
                isFavorite: entry.isFavorite,
                sourceUTIs: entry.sourceUTIs,
                sourceAppBundleID: entry.sourceAppBundleID,
                sourceAppName: entry.sourceAppName,
                ocrText: entry.ocrText,
                isPinned: entry.isPinned,
                richTextRTF: entry.richText?.rtf,
                richTextHTML: entry.richText?.html
            )
        case .file(let url):
            let thumbnailFileName: String?
            if let thumbnail = entry.thumbnail {
                let fileName = "\(entry.id.uuidString)-thumbnail.png"
                try append(thumbnail, named: fileName, to: &imageWrites)
                thumbnailFileName = fileName
            } else {
                thumbnailFileName = nil
            }
            return StoredEntry(
                id: entry.id,
                timestamp: entry.timestamp,
                contentKind: .file,
                text: nil,
                urlString: url.absoluteString,
                urlStrings: [url.absoluteString],
                imageFileName: nil,
                thumbnailFileName: thumbnailFileName,
                isFavorite: entry.isFavorite,
                sourceUTIs: entry.sourceUTIs,
                sourceAppBundleID: entry.sourceAppBundleID,
                sourceAppName: entry.sourceAppName,
                ocrText: entry.ocrText,
                isPinned: entry.isPinned,
                richTextRTF: entry.richText?.rtf,
                richTextHTML: entry.richText?.html
            )
        case .files(let urls):
            let thumbnailFileName: String?
            if let thumbnail = entry.thumbnail {
                let fileName = "\(entry.id.uuidString)-thumbnail.png"
                try append(thumbnail, named: fileName, to: &imageWrites)
                thumbnailFileName = fileName
            } else {
                thumbnailFileName = nil
            }
            return StoredEntry(
                id: entry.id,
                timestamp: entry.timestamp,
                contentKind: .file,
                text: nil,
                urlString: urls.first?.absoluteString,
                urlStrings: urls.map(\.absoluteString),
                imageFileName: nil,
                thumbnailFileName: thumbnailFileName,
                isFavorite: entry.isFavorite,
                sourceUTIs: entry.sourceUTIs,
                sourceAppBundleID: entry.sourceAppBundleID,
                sourceAppName: entry.sourceAppName,
                ocrText: entry.ocrText,
                isPinned: entry.isPinned,
                richTextRTF: entry.richText?.rtf,
                richTextHTML: entry.richText?.html
            )
        }
    }

    private func append(
        _ image: StoredImage,
        named fileName: String,
        to imageWrites: inout [PendingImageWrite]
    ) throws {
        guard let data = image.pngData() else {
            throw CocoaError(.fileWriteUnknown)
        }
        imageWrites.append(PendingImageWrite(fileName: fileName, data: data))
    }

    private func loadImage(named fileName: String) -> StoredImage? {
        let url = imagesDirectory.appendingPathComponent(fileName)
        guard let data = try? Data(contentsOf: url) else { return nil }
        return StoredImage(pngData: data)
    }

    /// 磁盘上那份图片是否已经就是"我们这次要写的字节"。
    ///
    /// 判据是**存在 + 字节长度相同**。文件名由条目 UUID 派生，所以只有"同一条目的图片换了内容"
    /// 才可能需要重写，而两张不同的图 PNG 压出来长度恰好相同的概率可以忽略；真出现
    /// "同名同长度不同内容"只有手改存档一条路，而那种情况下 `load()` 本来就以磁盘为准。
    /// 换来的是稳态保存不再把整库图片重写一遍（审计第二轮 B-1 / R2-04：磁盘 IO 与图片数线性，
    /// 500 条带图的库每次复制都要重写几百个文件）。
    /// 外部把文件删掉时这里返回 false ⇒ 自动补写，不会留下"存档指着不存在的图片"。
    nonisolated private static func isAlreadyOnDisk(
        _ url: URL,
        data: Data,
        fileManager: FileManager
    ) -> Bool {
        guard let attributes = try? fileManager.attributesOfItem(atPath: url.path),
              let size = attributes[.size] as? NSNumber else {
            return false
        }
        return size.int64Value == Int64(data.count)
    }

    nonisolated private static func makeSaveWorkItem(
        snapshot: SaveSnapshot,
        rootDirectory: URL,
        protectedImageFileNames: Set<String>
    ) -> DispatchWorkItem {
        DispatchWorkItem {
            do {
                try write(snapshot, rootDirectory: rootDirectory, protectedImageFileNames: protectedImageFileNames)
            } catch {
                let message = String(describing: error)
                Task { @MainActor in
                    LifecycleDebugLogger.log("FileHistoryPersistence background save failed error=\(message)")
                }
            }
        }
    }

    nonisolated private static func write(
        _ snapshot: SaveSnapshot,
        rootDirectory: URL,
        protectedImageFileNames: Set<String>
    ) throws {
        let fileManager = FileManager.default
        let historyURL = rootDirectory.appendingPathComponent("history.json")
        let imagesDirectory = rootDirectory.appendingPathComponent("images", isDirectory: true)

        try ensurePrivateDirectory(rootDirectory, fileManager: fileManager)
        try ensurePrivateDirectory(imagesDirectory, fileManager: fileManager)
        for imageWrite in snapshot.imageWrites {
            let imageURL = imagesDirectory.appendingPathComponent(imageWrite.fileName)
            if isAlreadyOnDisk(imageURL, data: imageWrite.data, fileManager: fileManager) {
                continue
            }
            try imageWrite.data.write(to: imageURL, options: .atomic)
            try setPrivateFilePermissions(imageURL, fileManager: fileManager)
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(snapshot.storedHistory)
        let backupURL = Self.backupURL(for: historyURL)

        try data.write(to: historyURL, options: .atomic)
        try setPrivateFilePermissions(historyURL, fileManager: fileManager)
        // 滚动备份：永远是一份完整且成功写盘过的快照，损坏时可回退。
        try data.write(to: backupURL, options: .atomic)
        try setPrivateFilePermissions(backupURL, fileManager: fileManager)

        // 保护集只来自"本次运行遇到过损坏存档"时尽力提取出的文件名（见 load()）。
        // 正常路径保持既有语义：被删除条目的图片应当在下一次保存时清理掉
        // （testSaveRemovesUnusedImageFiles 锁住这一行为）。
        try removeUnusedImages(
            keeping: snapshot.usedImageFileNames.union(protectedImageFileNames),
            imagesDirectory: imagesDirectory,
            fileManager: fileManager
        )
    }

    /// 存档的滚动备份位置：`history.json.bak`。
    nonisolated static func backupURL(for historyURL: URL) -> URL {
        URL(fileURLWithPath: historyURL.path + ".bak")
    }

    /// 把无法解析的原件保全成 `history.corrupt-<时间戳>.json`，绝不删除原件。
    nonisolated private static func preserveCorruptFile(at url: URL) -> URL? {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        let candidate = url.deletingPathExtension()
            .appendingPathExtension("corrupt-\(formatter.string(from: Date())).json")
        guard !FileManager.default.fileExists(atPath: candidate.path) else { return nil }
        do {
            try FileManager.default.copyItem(at: url, to: candidate)
            try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: candidate.path)
            return candidate
        } catch {
            return nil
        }
    }

    nonisolated private static func imageFileNames(from storedHistory: StoredHistory) -> Set<String> {
        Set(storedHistory.entries.flatMap { [$0.imageFileName, $0.thumbnailFileName].compactMap(\ .self) })
    }

    /// 尽力从（可能半截的）JSON 文本里提取图片文件名，用于在损坏事件中保住对应文件。
    nonisolated private static func looseImageFileNames(inFileAt url: URL) -> Set<String> {
        guard let text = try? String(contentsOf: url, encoding: .utf8) else { return [] }
        return looseImageFileNames(in: text)
    }

    nonisolated private static func looseImageFileNames(in text: String) -> Set<String> {
        let pattern = "[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}-(?:image|thumbnail)\\.png"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        var names: Set<String> = []
        for match in regex.matches(in: text, range: range) {
            if let swiftRange = Range(match.range, in: text) {
                names.insert(String(text[swiftRange]))
            }
        }
        return names
    }

    nonisolated private static func ensurePrivateDirectory(
        _ url: URL,
        fileManager: FileManager
    ) throws {
        try fileManager.createDirectory(at: url, withIntermediateDirectories: true)
        try fileManager.setAttributes(
            [.posixPermissions: 0o700],
            ofItemAtPath: url.path
        )
    }

    nonisolated private static func setPrivateFilePermissions(
        _ url: URL,
        fileManager: FileManager
    ) throws {
        try fileManager.setAttributes(
            [.posixPermissions: 0o600],
            ofItemAtPath: url.path
        )
    }

    nonisolated private static func removeUnusedImages(
        keeping usedFileNames: Set<String>,
        imagesDirectory: URL,
        fileManager: FileManager
    ) throws {
        guard let imageFiles = try? fileManager.contentsOfDirectory(
            at: imagesDirectory,
            includingPropertiesForKeys: nil
        ) else { return }

        for file in imageFiles where !usedFileNames.contains(file.lastPathComponent) {
            try? fileManager.removeItem(at: file)
        }
    }
}
