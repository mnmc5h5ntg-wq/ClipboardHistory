import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class RecordingHistoryPersistence: HistoryPersisting {
    var entriesToLoad: [ClipboardEntry]
    private(set) var loadCallCount = 0
    private(set) var savedEntriesSnapshots: [[ClipboardEntry]] = []
    var saveError: Error?

    init(entriesToLoad: [ClipboardEntry] = []) {
        self.entriesToLoad = entriesToLoad
    }

    func load() -> [ClipboardEntry] {
        loadCallCount += 1
        return entriesToLoad
    }

    func save(_ entries: [ClipboardEntry]) throws {
        if let saveError {
            throw saveError
        }
        savedEntriesSnapshots.append(entries)
        entriesToLoad = entries
    }
}

@MainActor
final class TestClipboardWriter: ClipboardWriting {
    private(set) var writtenContents: [ClipboardEntryContent] = []
    private var nextChangeCount = 1
    var errorToThrow: Error?

    func write(_ content: ClipboardEntryContent) throws -> Int {
        writtenContents.append(content)
        if let errorToThrow {
            throw errorToThrow
        }
        nextChangeCount += 1
        return nextChangeCount
    }
}

func makeClipboardEntry(
    id: UUID = UUID(),
    content: ClipboardEntryContent,
    timestamp: Date = Date(timeIntervalSince1970: 1_000),
    thumbnail: StoredImage? = nil,
    isFavorite: Bool = false,
    sourceUTIs: [String] = []
) -> ClipboardEntry {
    ClipboardEntry(
        id: id,
        content: content,
        timestamp: timestamp,
        thumbnail: thumbnail,
        sourceURL: content.sourceURL,
        isFavorite: isFavorite,
        sourceUTIs: sourceUTIs
    )
}

func makeStoredImage(color: NSColor = .red, size: NSSize = NSSize(width: 2, height: 2)) throws -> StoredImage {
    let image = NSImage(size: size)
    image.lockFocus()
    color.setFill()
    NSRect(origin: .zero, size: size).fill()
    image.unlockFocus()

    guard let data = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: data),
          let png = bitmap.representation(using: .png, properties: [:]),
          let storedImage = StoredImage(pngData: png) else {
        throw NSError(domain: "ClipboardHistoryAppTests", code: 1)
    }

    return storedImage
}

func makeTemporaryDirectory(
    named name: String = UUID().uuidString,
    file: StaticString = #filePath,
    line: UInt = #line
) throws -> URL {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(name, isDirectory: true)
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    return directory
}

/// 多个测试共用的登录项替身（原为 LoginItemSettingsTests 私有）。
@MainActor
final class FakeLoginItemManager: LoginItemManaging {
    let isSupported: Bool
    private(set) var requestedStates: [Bool] = []
    var error: Error?
    var isEnabled: Bool

    init(isSupported: Bool, isEnabled: Bool) {
        self.isSupported = isSupported
        self.isEnabled = isEnabled
    }

    func setEnabled(_ enabled: Bool) throws {
        requestedStates.append(enabled)
        if let error {
            throw error
        }
        isEnabled = enabled
    }
}
