import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class HistoryRetentionPolicyTests: XCTestCase {
    func testRetainingSortsNewestFirstAndCapsEntryCount() {
        let policy = HistoryRetentionPolicy(maxEntries: 2, maxAgeDays: nil)
        let entries = [
            makeClipboardEntry(content: .text("old"), timestamp: Date(timeIntervalSince1970: 1)),
            makeClipboardEntry(content: .text("newest"), timestamp: Date(timeIntervalSince1970: 3)),
            makeClipboardEntry(content: .text("middle"), timestamp: Date(timeIntervalSince1970: 2))
        ]

        let retained = policy.retaining(entries, now: Date(timeIntervalSince1970: 10))

        XCTAssertEqual(retained.map(\.content), [.text("newest"), .text("middle")])
    }

    func testRetainingDropsEntriesOlderThanMaxAge() {
        let policy = HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: 30)
        let now = Date(timeIntervalSince1970: 31 * 24 * 60 * 60)
        let fresh = makeClipboardEntry(content: .text("fresh"), timestamp: now.addingTimeInterval(-29 * 24 * 60 * 60))
        let expired = makeClipboardEntry(content: .text("expired"), timestamp: now.addingTimeInterval(-31 * 24 * 60 * 60))

        let retained = policy.retaining([expired, fresh], now: now)

        XCTAssertEqual(retained.map(\.content), [.text("fresh")])
    }

    func testRetainingKeepsFavoritesOutsideAgeAndCountLimits() {
        let policy = HistoryRetentionPolicy(maxEntries: 1, maxAgeDays: 30)
        let now = Date(timeIntervalSince1970: 60 * 24 * 60 * 60)
        let favorite = makeClipboardEntry(
            content: .text("favorite"),
            timestamp: now.addingTimeInterval(-59 * 24 * 60 * 60),
            isFavorite: true
        )
        let fresh = makeClipboardEntry(
            content: .text("fresh"),
            timestamp: now.addingTimeInterval(-1 * 24 * 60 * 60)
        )
        let extra = makeClipboardEntry(
            content: .text("extra"),
            timestamp: now.addingTimeInterval(-2 * 24 * 60 * 60)
        )

        let retained = policy.retaining([favorite, extra, fresh], now: now)

        XCTAssertEqual(retained.map(\.content), [.text("fresh"), .text("favorite")])
        XCTAssertTrue(retained.first { $0.content == .text("favorite") }?.isFavorite == true)
    }
}

@MainActor
final class FileHistoryPersistenceTests: XCTestCase {
    func testSaveAndLoadTextEntryPreservesMetadata() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let id = UUID()
        let timestamp = Date(timeIntervalSince1970: 1_234)
        let entry = makeClipboardEntry(
            id: id,
            content: .text("persist me"),
            timestamp: timestamp,
            isFavorite: true,
            sourceUTIs: ["public.utf8-plain-text"]
        )

        try persistence.save([entry])
        persistence.flushPendingSaves()
        let loaded = persistence.load()

        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded.first?.id, id)
        XCTAssertEqual(loaded.first?.timestamp, timestamp)
        XCTAssertEqual(loaded.first?.content, .text("persist me"))
        XCTAssertEqual(loaded.first?.isFavorite, true)
        XCTAssertEqual(loaded.first?.sourceUTIs, ["public.utf8-plain-text"])
    }

    func testSaveQueuesDiskWriteUntilFlush() throws {
        let root = try temporaryRoot()
        let saveQueue = DispatchQueue(label: "FileHistoryPersistenceTests.suspendedSaveQueue")
        saveQueue.suspend()
        var queueIsSuspended = true
        defer {
            if queueIsSuspended {
                saveQueue.resume()
            }
        }
        let persistence = FileHistoryPersistence(rootDirectory: root, saveQueue: saveQueue)
        let entry = makeClipboardEntry(content: .text("queued save"))
        let historyURL = root.appendingPathComponent("history.json")

        try persistence.save([entry])

        XCTAssertFalse(FileManager.default.fileExists(atPath: historyURL.path))

        saveQueue.resume()
        queueIsSuspended = false
        persistence.flushPendingSaves()

        XCTAssertTrue(FileManager.default.fileExists(atPath: historyURL.path))
        XCTAssertEqual(persistence.load().map(\.content), [.text("queued save")])
    }

    func testSaveAndLoadImageEntryWritesImageData() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let image = try makeStoredImage()
        let entry = makeClipboardEntry(content: .image(image), sourceUTIs: ["public.png"])

        try persistence.save([entry])
        persistence.flushPendingSaves()
        let loaded = persistence.load()

        guard case .image(let loadedImage) = loaded.first?.content else {
            return XCTFail("Expected image entry")
        }
        XCTAssertNotNil(loadedImage.pngData())
        XCTAssertTrue(
            FileManager.default.fileExists(
                atPath: root
                    .appendingPathComponent("images", isDirectory: true)
                    .appendingPathComponent("\(entry.id.uuidString)-image.png")
                    .path
            )
        )
    }

    func testSaveUsesPrivatePermissionsForHistoryFiles() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let image = try makeStoredImage()
        let entry = makeClipboardEntry(content: .image(image))
        let imagesDirectory = root.appendingPathComponent("images", isDirectory: true)
        let historyURL = root.appendingPathComponent("history.json")
        let imageURL = imagesDirectory.appendingPathComponent("\(entry.id.uuidString)-image.png")

        try persistence.save([entry])
        persistence.flushPendingSaves()

        XCTAssertEqual(try permissions(for: root), 0o700)
        XCTAssertEqual(try permissions(for: imagesDirectory), 0o700)
        XCTAssertEqual(try permissions(for: historyURL), 0o600)
        XCTAssertEqual(try permissions(for: imageURL), 0o600)
    }

    func testSaveAndLoadFileEntryPreservesURLAndThumbnail() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let fileURL = URL(fileURLWithPath: "/tmp/example.mov")
        let thumbnail = try makeStoredImage(color: .blue)
        let entry = makeClipboardEntry(
            content: .file(fileURL),
            thumbnail: thumbnail,
            sourceUTIs: ["public.file-url"]
        )

        try persistence.save([entry])
        persistence.flushPendingSaves()
        let loaded = persistence.load()

        XCTAssertEqual(loaded.first?.content, .file(fileURL))
        XCTAssertNotNil(loaded.first?.thumbnail?.pngData())
        XCTAssertEqual(loaded.first?.sourceUTIs, ["public.file-url"])
    }

    func testSaveAndLoadMultipleFileEntryPreservesAllURLs() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let urls = [
            URL(fileURLWithPath: "/tmp/first.mov"),
            URL(fileURLWithPath: "/tmp/second.mov")
        ]
        let entry = makeClipboardEntry(
            content: .files(urls),
            sourceUTIs: ["public.file-url"]
        )

        try persistence.save([entry])
        persistence.flushPendingSaves()
        let loaded = persistence.load()

        XCTAssertEqual(loaded.first?.content, .files(urls))
        XCTAssertEqual(loaded.first?.sourceUTIs, ["public.file-url"])
    }

    func testLoadDropsImageEntriesWhoseImageFileIsMissing() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let image = try makeStoredImage()
        let entry = makeClipboardEntry(content: .image(image))

        try persistence.save([entry])
        persistence.flushPendingSaves()
        try FileManager.default.removeItem(
            at: root
                .appendingPathComponent("images", isDirectory: true)
                .appendingPathComponent("\(entry.id.uuidString)-image.png")
        )

        XCTAssertTrue(persistence.load().isEmpty)
    }

    func testSaveRemovesUnusedImageFiles() throws {
        let root = try temporaryRoot()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let image = try makeStoredImage()
        let entry = makeClipboardEntry(content: .image(image))
        let imageURL = root
            .appendingPathComponent("images", isDirectory: true)
            .appendingPathComponent("\(entry.id.uuidString)-image.png")

        try persistence.save([entry])
        persistence.flushPendingSaves()
        XCTAssertTrue(FileManager.default.fileExists(atPath: imageURL.path))

        try persistence.save([])
        persistence.flushPendingSaves()

        XCTAssertFalse(FileManager.default.fileExists(atPath: imageURL.path))
    }

    private func temporaryRoot() throws -> URL {
        let root = try makeTemporaryDirectory()
        addTeardownBlock {
            try? FileManager.default.removeItem(at: root)
        }
        return root
    }

    private func permissions(for url: URL) throws -> Int {
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        let permissions = try XCTUnwrap(attributes[.posixPermissions] as? NSNumber)
        return permissions.intValue & 0o777
    }
}

@MainActor
final class HistoryStorePersistenceTests: XCTestCase {
    func testInitLoadsPersistedEntriesOnceAndSelectsNewest() {
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            makeClipboardEntry(content: .text("old"), timestamp: Date(timeIntervalSince1970: 1)),
            makeClipboardEntry(content: .text("new"), timestamp: Date(timeIntervalSince1970: 2))
        ])

        let store = HistoryStore(
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )

        XCTAssertEqual(persistence.loadCallCount, 1)
        XCTAssertEqual(store.entries.map(\.content), [.text("new"), .text("old")])
        XCTAssertEqual(store.selectedEntry?.content, .text("new"))
    }

    func testInitPersistsTrimmedEntriesWhenStoredHistoryExceedsLimit() {
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            makeClipboardEntry(content: .text("one"), timestamp: Date(timeIntervalSince1970: 1)),
            makeClipboardEntry(content: .text("two"), timestamp: Date(timeIntervalSince1970: 2))
        ])

        _ = HistoryStore(
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 1, maxAgeDays: nil)
        )

        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.map(\.content), [.text("two")])
    }

    func testInitCollapsesPersistedDuplicateImageEntriesAndPreservesFavoriteState() throws {
        let image = try makeStoredImage(size: NSSize(width: 4, height: 5))
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            makeClipboardEntry(
                content: .image(image),
                timestamp: Date(timeIntervalSince1970: 3),
                sourceUTIs: ["public.png"]
            ),
            makeClipboardEntry(
                content: .text("between"),
                timestamp: Date(timeIntervalSince1970: 2)
            ),
            makeClipboardEntry(
                content: .image(image),
                timestamp: Date(timeIntervalSince1970: 1),
                isFavorite: true,
                sourceUTIs: ["public.tiff"]
            )
        ])

        let store = HistoryStore(
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.content, .image(image))
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.first?.isFavorite, true)
        XCTAssertEqual(store.entries.map(\.content), [.image(image), .text("between")])
        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.map(\.content), [.image(image), .text("between")])
        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.first?.isFavorite, true)
    }

    func testInitCollapsesPersistedDuplicateFileEntriesAndPreservesFavoriteState() {
        let url = URL(fileURLWithPath: "/tmp/repeat.png")
        let persistence = RecordingHistoryPersistence(entriesToLoad: [
            makeClipboardEntry(
                content: .file(url),
                timestamp: Date(timeIntervalSince1970: 3),
                sourceUTIs: ["public.file-url"]
            ),
            makeClipboardEntry(
                content: .text("between"),
                timestamp: Date(timeIntervalSince1970: 2)
            ),
            makeClipboardEntry(
                content: .file(url),
                timestamp: Date(timeIntervalSince1970: 1),
                isFavorite: true,
                sourceUTIs: ["public.file-url"]
            )
        ])

        let store = HistoryStore(
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )

        XCTAssertEqual(store.entries.count, 2)
        XCTAssertEqual(store.entries.first?.content, .file(url))
        XCTAssertEqual(store.entries.first?.timestamp, Date(timeIntervalSince1970: 3))
        XCTAssertEqual(store.entries.first?.isFavorite, true)
        XCTAssertEqual(store.entries.map(\.content), [.file(url), .text("between")])
        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.map(\.content), [.file(url), .text("between")])
        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.first?.isFavorite, true)
    }

    func testAddDeleteClearAndCopyAndPromotePersistSnapshots() {
        let writer = TestClipboardWriter()
        let persistence = RecordingHistoryPersistence()
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )

        store.add(intakeEntry(text: "one"), timestamp: Date(timeIntervalSince1970: 1))
        store.add(intakeEntry(text: "two"), timestamp: Date(timeIntervalSince1970: 2))
        store.perform(.copyAndPromote(store.entries[1]))
        store.perform(.delete(store.entries[1]))
        store.perform(.toggleFavorite(store.entries[0]))
        store.perform(.clear)

        XCTAssertEqual(persistence.savedEntriesSnapshots.count, 6)
        XCTAssertEqual(persistence.savedEntriesSnapshots[0].map(\.content), [.text("one")])
        XCTAssertEqual(persistence.savedEntriesSnapshots[1].map(\.content), [.text("two"), .text("one")])
        XCTAssertEqual(persistence.savedEntriesSnapshots[2].first?.content, .text("one"))
        XCTAssertEqual(persistence.savedEntriesSnapshots[3].map(\.content), [.text("one")])
        XCTAssertEqual(persistence.savedEntriesSnapshots[4].map(\.content), [.text("one")])
        XCTAssertEqual(persistence.savedEntriesSnapshots[4].first?.isFavorite, true)
        XCTAssertEqual(persistence.savedEntriesSnapshots[5].map(\.content), [.text("one")])
    }

    func testToggleFavoriteUpdatesSelectionFilterAndPersistence() {
        let persistence = RecordingHistoryPersistence()
        let store = HistoryStore(
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        store.add(intakeEntry(text: "ordinary"), timestamp: Date(timeIntervalSince1970: 1))
        let entry = store.entries[0]

        store.perform(.toggleFavorite(entry))
        store.perform(.updateFilter(.favorites))

        XCTAssertEqual(store.favoriteCount, 1)
        XCTAssertEqual(store.filteredEntries.map(\.content), [.text("ordinary")])
        XCTAssertEqual(store.selectedEntry?.content, .text("ordinary"))
        XCTAssertEqual(persistence.savedEntriesSnapshots.last?.first?.isFavorite, true)
    }

    func testSaveFailureDoesNotDiscardInMemoryHistory() {
        let persistence = RecordingHistoryPersistence()
        persistence.saveError = NSError(domain: "HistoryStorePersistenceTests", code: 1)
        let store = HistoryStore(persistence: persistence, maxEntries: 10)

        store.add(intakeEntry(text: "kept in memory"))

        XCTAssertEqual(store.entries.map(\.content), [.text("kept in memory")])
        XCTAssertTrue(persistence.savedEntriesSnapshots.isEmpty)
    }

    private func intakeEntry(text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(text), thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"])
    }
}
