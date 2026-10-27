import Foundation

/// Dock 角标的读数：没有未读剪辑时不挂角标，超过两位数写成「99+」。
/// 角标本体由 WindowServer 画，进程里没有可截图的视图（见 `DockBadgeController`）。
enum DockBadgePolicy {
    static let maxDisplayedCount = 99

    static func label(unseenCount: Int) -> String? {
        guard unseenCount > 0 else { return nil }
        guard unseenCount <= maxDisplayedCount else { return "\(maxDisplayedCount)+" }
        return "\(unseenCount)"
    }
}

/// 只有 App 不在前台时新到的剪辑才算「未读」：前台时列表当场可见，
/// 再往 Dock 上挂数字只是噪音。回到前台即清零。
struct DockBadgeTracker {
    private(set) var entryCount: Int
    private(set) var unseenCount = 0
    private(set) var isActive: Bool

    init(entryCount: Int, isActive: Bool) {
        self.entryCount = entryCount
        self.isActive = isActive
    }

    var badgeLabel: String? {
        DockBadgePolicy.label(unseenCount: unseenCount)
    }

    mutating func noteEntryCount(_ count: Int) {
        let delta = count - entryCount
        if !isActive && delta > 0 {
            unseenCount += delta
        }
        entryCount = count
        if unseenCount > count {
            unseenCount = max(0, count)
        }
    }

    mutating func noteActivation(_ active: Bool) {
        isActive = active
        if active {
            unseenCount = 0
        }
    }
}
