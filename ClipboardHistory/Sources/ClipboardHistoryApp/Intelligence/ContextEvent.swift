import Foundation

enum ContextEventKind: String, Codable, CaseIterable, Hashable {
    case copy
    case switchToApp
    case switchToDesktop
    case idle
}

struct ContextEvent: Identifiable, Codable, Equatable, Hashable {
    var id: UUID
    var kind: ContextEventKind
    var timestamp: Date
    var frontmostApplication: RunningApplicationContext?
    var entryID: UUID?

    init(
        id: UUID = UUID(),
        kind: ContextEventKind,
        timestamp: Date = Date(),
        frontmostApplication: RunningApplicationContext? = nil,
        entryID: UUID? = nil
    ) {
        self.id = id
        self.kind = kind
        self.timestamp = timestamp
        self.frontmostApplication = frontmostApplication
        self.entryID = entryID
    }
}

extension Array where Element == ContextEvent {
    func inRecentWindow(after anchor: Date, within interval: TimeInterval = 600) -> [ContextEvent] {
        let start = Swift.max(anchor.addingTimeInterval(-interval), Date(timeIntervalSince1970: 0))
        return filter { $0.timestamp >= start && $0.timestamp <= anchor }
    }

    var switchPattern: String {
        let kinds = map(\.kind).map { kind in
            switch kind {
            case .copy: return "C"
            case .switchToApp: return "A"
            case .switchToDesktop: return "D"
            case .idle: return "."
            }
        }
        return kinds.joined()
    }
}
