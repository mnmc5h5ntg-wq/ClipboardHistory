import Foundation

struct RunningApplicationContext: Codable, Equatable, Hashable {
    var localizedName: String?
    var bundleIdentifier: String?
    var processIdentifier: Int32?
}

struct WindowContext: Codable, Equatable, Hashable {
    var title: String?
    var sensitivity: AIPrivacySensitivity
}

struct BrowserContext: Codable, Equatable, Hashable {
    var urlString: String?
    var domain: String?
    var title: String?
    var sensitivity: AIPrivacySensitivity
}

struct DocumentContext: Codable, Equatable, Hashable {
    var fileName: String?
    var fileExtension: String?
    var pathIsAvailable: Bool
    var sensitivity: AIPrivacySensitivity
}

struct ClipboardEntrySummary: Identifiable, Codable, Equatable, Hashable {
    var id: UUID
    var contentKind: String
    var preview: String
    var isFavorite: Bool
    var copiedAt: Date
    var sourceUTIs: [String]
    var sourceAppBundleID: String?
}

struct ContextPermissionState: Codable, Equatable, Hashable {
    var canReadFrontmostApplication: Bool
    var canReadWindowTitle: Bool
    var canReadBrowserDomain: Bool
    var canReadFinderDirectory: Bool
    var canReadFinderSelection: Bool

    static let minimal = ContextPermissionState(
        canReadFrontmostApplication: true,
        canReadWindowTitle: false,
        canReadBrowserDomain: false,
        canReadFinderDirectory: false,
        canReadFinderSelection: false,
            )
}

struct ContextSnapshot: Codable, Equatable, Hashable {
    var capturedAt: Date
    var frontmostApplication: RunningApplicationContext?
    var activeWindow: WindowContext?
    var browser: BrowserContext?
    var focusedDocument: DocumentContext?
    var finderDirectory: FinderDirectoryContext?
    var finderSelection: FinderSelectionContext?
    var recentEntries: [ClipboardEntrySummary]
    var recentEvents: [ContextEvent]
    var selectedEntryID: UUID?
    var permissionState: ContextPermissionState

    static func minimal(
        recentEntries: [ClipboardEntrySummary],
        selectedEntryID: UUID? = nil,
        capturedAt: Date = Date()
    ) -> ContextSnapshot {
        ContextSnapshot(
            capturedAt: capturedAt,
            frontmostApplication: nil,
            activeWindow: nil,
            browser: nil,
            focusedDocument: nil,
            recentEntries: recentEntries,
            recentEvents: [],
            selectedEntryID: selectedEntryID,
            permissionState: .minimal
        )
    }
}


struct FinderDirectoryContext: Codable, Equatable, Hashable {
    var path: String
    var sensitivity: AIPrivacySensitivity
}

struct FinderSelectionContext: Codable, Equatable, Hashable {
    var fileExtensions: [String]
    var count: Int
    var sensitivity: AIPrivacySensitivity
}
