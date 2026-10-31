import AppKit
import QuartzCore

/// R523：折叠/展开的**唯一状态**。持久化两档宽度与当前状态；切换时先把当前窗口宽
/// 记回"正要离开的那一档"，下一次切回来就尊重用户最近一次 resize。
///
/// R524：过渡由**控制器自己按 60Hz 驱动**（不是 SwiftUI/NSAnimationContext 隐式动画）：
/// - 每一拍同时更新 `foldProgress`（内容交叉淡 + 中缝阴影）与窗口宽 → 两者同一时钟；
/// - 可中断：再点一次直接以当前进度/当前宽度为起点反向，没有动画队列、不会留半折；
/// - reduce-motion 时 `animationDuration == 0`，状态与几何一步到位。
@MainActor
final class MainWindowCollapseController: ObservableObject {
    static let collapsedKey = "mainWindowCollapsed"
    static let expandedWidthKey = "mainWindowExpandedWidth"
    static let collapsedWidthKey = "mainWindowCollapsedWidth"

    @Published private(set) var isCollapsed: Bool
    /// 0 = 完全展开，1 = 完全折叠。由过渡逐帧推进；两端与 `isCollapsed` 一致。
    @Published private(set) var foldProgress: Double

    private let defaults: UserDefaults
    private let persists: Bool

    private var transitionTimer: DispatchSourceTimer?
    private var transitionStart: CFTimeInterval = 0
    private var transitionDuration: TimeInterval = 0
    private var transitionFromProgress: Double = 0
    private var transitionToProgress: Double = 0
    private var transitionFromWidth: CGFloat = 0
    private var transitionToWidth: CGFloat = 0

    var isTransitioning: Bool { transitionTimer != nil }

    init(defaults: UserDefaults = .standard, persists: Bool = true) {
        self.defaults = defaults
        self.persists = persists
        let collapsed = persists ? defaults.bool(forKey: Self.collapsedKey) : false
        self.isCollapsed = collapsed
        self.foldProgress = collapsed ? 1 : 0
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
        // 已停在同一档才是一次空操作；过渡中再点是**反向**，必须继续。
        if !isTransitioning, collapsed == isCollapsed { return }
        let target = window ?? WindowManager.currentMainWindow
        if !isTransitioning, let target { rememberWidth(of: target) }

        isCollapsed = collapsed
        if persists { defaults.set(collapsed, forKey: Self.collapsedKey) }

        guard let target else {
            stopTransition()
            foldProgress = collapsed ? 1 : 0
            return
        }

        let duration = MainWindowCollapsePolicy.animationDuration(
            reduceMotion: MotionCatalog.motionShouldBeReduced
        )
        guard duration > 0 else {
            // reduce-motion：0 时长直切，不留任何过渡状态。
            stopTransition()
            foldProgress = collapsed ? 1 : 0
            applyGeometry(to: target)
            return
        }
        startTransition(on: target, toCollapsed: collapsed, duration: duration)
    }

    private func rememberWidth(of window: NSWindow) {
        let width = window.frame.width
        guard width >= MainWindowCollapsePolicy.minWidth(collapsed: isCollapsed) else { return }
        guard persists else { return }
        defaults.set(Double(width),
                     forKey: isCollapsed ? Self.collapsedWidthKey : Self.expandedWidthKey)
    }

    // MARK: - 逐帧过渡

    private func startTransition(on window: NSWindow, toCollapsed: Bool, duration: TimeInterval) {
        stopTransition()
        transitionFromProgress = foldProgress
        transitionToProgress = toCollapsed ? 1 : 0
        transitionFromWidth = window.frame.width
        let visible = (window.screen ?? NSScreen.main)?.visibleFrame
        transitionToWidth = MainWindowCollapsePolicy.targetWidth(
            collapsed: toCollapsed,
            expandedWidth: expandedWidth,
            collapsedWidth: collapsedWidth,
            visibleWidth: visible?.width
        )
        transitionDuration = duration
        transitionStart = CACurrentMediaTime()
        // 途中两档最小宽都要能容纳：先把 minSize 放到较小的一档，收尾再落回目标档。
        window.minSize = NSSize(width: MainWindowCollapsePolicy.collapsedMinWidth,
                                height: MainWindowCollapsePolicy.minHeight)
        let timer = DispatchSource.makeTimerSource(queue: .main)
        timer.schedule(deadline: .now(), repeating: 1.0 / 60.0)
        timer.setEventHandler { [weak self] in
            MainActor.assumeIsolated {
                self?.advanceTransition()
            }
        }
        timer.resume()
        transitionTimer = timer
    }

    private func advanceTransition() {
        guard let window = WindowManager.currentMainWindow else {
            stopTransition()
            foldProgress = transitionToProgress
            return
        }
        let linear = min(max((CACurrentMediaTime() - transitionStart) / transitionDuration, 0), 1)
        let eased = MainWindowCollapsePolicy.easedProgress(linear)
        foldProgress = transitionFromProgress
            + (transitionToProgress - transitionFromProgress) * eased
        let width = transitionFromWidth
            + (transitionToWidth - transitionFromWidth) * CGFloat(eased)
        setWindowWidth(width, on: window)
        if linear >= 1 {
            finishTransition(on: window)
        }
    }

    private func finishTransition(on window: NSWindow) {
        stopTransition()
        foldProgress = transitionToProgress
        applyGeometry(to: window)
    }

    private func stopTransition() {
        transitionTimer?.setEventHandler {}
        transitionTimer?.cancel()
        transitionTimer = nil
    }

    private func setWindowWidth(_ width: CGFloat, on window: NSWindow) {
        var frame = window.frame
        let top = frame.maxY
        frame.size.width = width
        if let visible = (window.screen ?? NSScreen.main)?.visibleFrame {
            frame.origin.x = MainWindowCollapsePolicy.originX(clampingX: frame.origin.x,
                                                              width: width,
                                                              visibleFrame: visible)
            frame.origin.y = MainWindowCollapsePolicy.originY(clampingTop: top,
                                                              height: frame.height,
                                                              visibleFrame: visible)
        }
        window.setFrame(frame, display: true)
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
        setWindowWidth(width, on: window)
    }
}
