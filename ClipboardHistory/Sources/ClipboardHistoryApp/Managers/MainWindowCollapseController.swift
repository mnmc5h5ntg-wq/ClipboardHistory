import AppKit

/// R523：折叠/展开的**唯一状态**。持久化两档宽度与当前状态；切换时先把当前窗口宽
/// 记回"正要离开的那一档"，下一次切回来就尊重用户最近一次 resize。
@MainActor
final class MainWindowCollapseController: ObservableObject {
    static let collapsedKey = "mainWindowCollapsed"
    static let expandedWidthKey = "mainWindowExpandedWidth"
    static let collapsedWidthKey = "mainWindowCollapsedWidth"

    @Published private(set) var isCollapsed: Bool

    private let defaults: UserDefaults
    private let persists: Bool

    init(defaults: UserDefaults = .standard, persists: Bool = true) {
        self.defaults = defaults
        self.persists = persists
        self.isCollapsed = persists ? defaults.bool(forKey: Self.collapsedKey) : false
    }

    var expandedWidth: CGFloat {
        width(forKey: Self.expandedWidthKey, fallback: MainWindowCollapsePolicy.expandedWidthDefault)
    }

    var collapsedWidth: CGFloat {
        width(forKey: Self.collapsedWidthKey, fallback: MainWindowCollapsePolicy.collapsedWidthDefault)
    }

    private func width(forKey key: String, fallback: CGFloat) -> CGFloat {
        guard persists, defaults.object(forKey: key) != nil else { return fallback }
        let value = CGFloat(defaults.double(forKey: key))
        return value > 0 ? value : fallback
    }

    func toggle() {
        setCollapsed(!isCollapsed)
    }

    /// 切换状态。`window` 不传时用当前主窗口；窗口不存在（登录首启还没建）也允许改状态，
    /// 之后的创建路径会按持久化状态把几何补上。
    func setCollapsed(_ collapsed: Bool, window: NSWindow? = nil) {
        guard collapsed != isCollapsed else { return }
        let target = window ?? WindowManager.currentMainWindow
        if let target { rememberWidth(of: target) }
        isCollapsed = collapsed
        if persists { defaults.set(collapsed, forKey: Self.collapsedKey) }
        if let target { applyGeometry(to: target) }
    }

    private func rememberWidth(of window: NSWindow) {
        let width = window.frame.width
        guard width >= MainWindowCollapsePolicy.minWidth(collapsed: isCollapsed) else { return }
        guard persists else { return }
        defaults.set(Double(width),
                     forKey: isCollapsed ? Self.collapsedWidthKey : Self.expandedWidthKey)
    }

    /// 把当前状态套到窗口上：宽度按策略（记住的宽 → 各自最小宽 → 屏幕宽），
    /// `minSize` 跟着状态走（折叠后不许被 SwiftUI 弹回 600），并保持左上角。
    func applyGeometry(to window: NSWindow) {
        let visible = (window.screen ?? NSScreen.main)?.visibleFrame
        let width = MainWindowCollapsePolicy.targetWidth(
            collapsed: isCollapsed,
            expandedWidth: expandedWidth,
            collapsedWidth: collapsedWidth,
            visibleWidth: visible?.width
        )
        let minWidth = MainWindowCollapsePolicy.minWidth(collapsed: isCollapsed)
        window.minSize = NSSize(width: minWidth, height: MainWindowCollapsePolicy.minHeight)
        var frame = window.frame
        let top = frame.maxY
        frame.size.width = width
        if let visible {
            frame.origin.x = MainWindowCollapsePolicy.originX(clampingX: frame.origin.x,
                                                              width: width,
                                                              visibleFrame: visible)
            frame.origin.y = MainWindowCollapsePolicy.originY(clampingTop: top,
                                                              height: frame.height,
                                                              visibleFrame: visible)
        }
        window.setFrame(frame, display: true)
    }
}
