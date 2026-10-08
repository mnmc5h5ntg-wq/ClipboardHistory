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
}

extension HistoryPersisting {
    func flushPendingSaves() {}
}

@MainActor
final class FileHistoryPersistence: HistoryPersisting {
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
        let ocrText: String?

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
        guard let data = try? Data(contentsOf: historyURL),
              let storedHistory = try? decoder.decode(StoredHistory.self, from: data) else {
            return []
        }

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
        let snapshot = try saveSnapshot(from: entries)
        let workItem = Self.makeSaveWorkItem(snapshot: snapshot, rootDirectory: rootDirectory)
        pendingSave = workItem
        saveQueue.async(execute: workItem)
    }

    func flushPendingSaves() {
        pendingSave?.wait()
        pendingSave = nil
    }

    static func defaultRootDirectory() -> URL {
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
            ocrText: storedEntry.ocrText
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
                ocrText: entry.ocrText
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
                ocrText: entry.ocrText
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
                ocrText: entry.ocrText
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
                ocrText: entry.ocrText
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

    nonisolated private static func makeSaveWorkItem(
        snapshot: SaveSnapshot,
        rootDirectory: URL
    ) -> DispatchWorkItem {
        DispatchWorkItem {
            do {
                try write(snapshot, rootDirectory: rootDirectory)
            } catch {
                let message = String(describing: error)
                Task { @MainActor in
                    LifecycleDebugLogger.log("FileHistoryPersistence background save failed error=\(message)")
                }
            }
        }
    }

    nonisolated private static func write(_ snapshot: SaveSnapshot, rootDirectory: URL) throws {
        let fileManager = FileManager.default
        let historyURL = rootDirectory.appendingPathComponent("history.json")
        let imagesDirectory = rootDirectory.appendingPathComponent("images", isDirectory: true)

        try ensurePrivateDirectory(rootDirectory, fileManager: fileManager)
        try ensurePrivateDirectory(imagesDirectory, fileManager: fileManager)
        for imageWrite in snapshot.imageWrites {
            let imageURL = imagesDirectory.appendingPathComponent(imageWrite.fileName)
            try imageWrite.data.write(to: imageURL, options: .atomic)
            try setPrivateFilePermissions(imageURL, fileManager: fileManager)
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(snapshot.storedHistory)
        try data.write(to: historyURL, options: .atomic)
        try setPrivateFilePermissions(historyURL, fileManager: fileManager)
        try removeUnusedImages(
            keeping: snapshot.usedImageFileNames,
            imagesDirectory: imagesDirectory,
            fileManager: fileManager
        )
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
