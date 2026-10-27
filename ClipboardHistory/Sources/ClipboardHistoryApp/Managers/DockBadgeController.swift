import AppKit
import Combine

@MainActor
final class DockBadgeController {
    private var tracker: DockBadgeTracker
    private let applyBadge: (String?) -> Void
    private var entryCountBridge: AnyCancellable?
    private var hasApplied = false
    private var lastApplied: String?

    /// `isAppActive` / `applyBadge` 的默认值都走真实 `NSApplication`；
    /// 测试注入闭包就能在**不碰**本机 Dock 的前提下读状态机（见 `DockBadgeTests`）。
    init(
        store: HistoryStore,
        isAppActive: @escaping () -> Bool = { NSApplication.shared.isActive },
        applyBadge: @escaping (String?) -> Void = { NSApplication.shared.dockTile.badgeLabel = $0 }
    ) {
        tracker = DockBadgeTracker(entryCount: store.entries.count, isActive: isAppActive())
        self.applyBadge = applyBadge
        entryCountBridge = store.$entries
            .map(\.count)
            .removeDuplicates()
            .sink { [weak self] count in
                self?.noteEntryCount(count)
            }
    }

    func noteEntryCount(_ count: Int) {
        tracker.noteEntryCount(count)
        syncBadge()
    }

    func applicationDidBecomeActive() {
        tracker.noteActivation(true)
        syncBadge()
    }

    func applicationDidResignActive() {
        tracker.noteActivation(false)
        syncBadge()
    }

    private func syncBadge() {
        let label = tracker.badgeLabel
        guard !hasApplied || label != lastApplied else { return }
        hasApplied = true
        lastApplied = label
        applyBadge(label)
    }
}
