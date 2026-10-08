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

    /// 只保留排序需要的元数据：前台 App、事件数量、时间。
    /// 反馈记录里存完整快照曾把剪贴板正文的 160 字预览副本写进 UserDefaults
    /// （实测把该 plist 撑到 66MB），因此存储前必须去掉正文类字段。
    func strippedOfClipboardContent() -> ContextSnapshot {
        var copy = self
        copy.recentEntries = []
        copy.activeWindow = copy.activeWindow.map { WindowContext(title: nil, sensitivity: $0.sensitivity) }
        copy.browser = copy.browser.map { BrowserContext(urlString: nil, domain: nil, title: nil, sensitivity: $0.sensitivity) }
        copy.finderDirectory = nil
        copy.finderSelection = nil
        copy.focusedDocument = nil
        copy.selectedEntryID = nil
        copy.recentEvents = copy.recentEvents.map { event in
            ContextEvent(
                id: event.id,
                kind: event.kind,
                timestamp: event.timestamp,
                frontmostApplication: event.frontmostApplication,
                entryID: nil            // 事件里也不留 entry 级关联
            )
        }
        return copy
    }

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
