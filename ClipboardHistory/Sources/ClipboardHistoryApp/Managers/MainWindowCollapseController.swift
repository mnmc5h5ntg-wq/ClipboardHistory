import AppKit
import QuartzCore

/// R523：折叠/展开的**唯一状态**。持久化两档宽度与当前状态；切换时先把当前窗口宽
/// 记回"正要离开的那一档"，下一次切回来就尊重用户最近一次 resize。
///
/// R552：**一步切换，不演**（D-552）。旧版（R524 起）是「t=0 翻状态 + 60Hz 定时器逐拍
/// `setFrame(display: true)`」，真机屏上读数（`scripts/real_screen_fold_transition.py`）：
/// - 切换那一拍主线程空窗 60ms（折叠）/106ms（展开）—— DetailView 的建/拆；
/// - 屏上只在 50ms 内换 4 帧（折叠）/ 17ms 内换 2 帧（展开），其余 150ms 屏上不动；
/// - 合起来的观感就是用户报的「点一下先卡住，然后窗口整块跳过去」。
/// 试过快照盖子（材质拍不出来 ⇒ 一块纯黑）与窗口服务合成几何（本机只给 2–3 档中间宽），
/// 两条都在同一台真机上量过、都不成立 ⇒ 按「宁可不演也不卡顿」收成一步。
/// 判据钉的是这几个可数的量：`switches` / `geometryWrites` / `minSizeWrites` / `publishedIntermediates`。
@MainActor
final class MainWindowCollapseController: ObservableObject {
    static let collapsedKey = "mainWindowCollapsed"
    static let expandedWidthKey = "mainWindowExpandedWidth"
    static let collapsedWidthKey = "mainWindowCollapsedWidth"
    /// R532：折叠态一次性提示。确认前每次折叠都显示，确认后永不再显示（跨重启）。
    static let hintAcknowledgedKey = "mainWindowCollapseHintAcknowledged"

    @Published private(set) var isCollapsed: Bool
    /// 0 = 完全展开，1 = 完全折叠。**只有这两个值**：一步切换没有中间进度可发布。
    @Published private(set) var foldProgress: Double
    /// R532：折叠态提示是否显示（折叠且用户未确认过）。
    @Published private(set) var showsCollapseHint: Bool

    /// 以下四格是给判据数的：一次切换应当是「布局 1 次、几何 1 次、minSize 1 次、中间态 0 次」。
    private(set) var switches = 0
    private(set) var geometryWrites = 0
    private(set) var minSizeWrites = 0
    private(set) var publishedIntermediates = 0
    /// 每次写 `foldProgress` 都记一笔，判据此钉住「整段路上只发布过 0 与 1」。
    private var publishedProgressValues: [Double] = []

    private let defaults: UserDefaults
    private let persists: Bool
    private var hintAcknowledged: Bool

    /// 一步切换 ⇒ 永远没有"在飞"的过渡。保留这一格是因为菜单项与真机通道要问"现在能不能再点"。
    var isTransitioning: Bool { false }

    init(defaults: UserDefaults = .standard, persists: Bool = true) {
        self.defaults = defaults
        self.persists = persists
        let collapsed = persists ? defaults.bool(forKey: Self.collapsedKey) : false
        let acknowledged = persists ? defaults.bool(forKey: Self.hintAcknowledgedKey) : false
        self.isCollapsed = collapsed
        self.foldProgress = collapsed ? 1 : 0
        self.hintAcknowledged = acknowledged
        self.showsCollapseHint = collapsed && !acknowledged
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

    /// R532：用户点「知道了」后，折叠提示不再出现（跨重启）。
    func acknowledgeCollapseHint() {
        guard showsCollapseHint else { return }
        showsCollapseHint = false
        hintAcknowledged = true
        if persists { defaults.set(true, forKey: Self.hintAcknowledgedKey) }
    }

    /// 切换状态。`window` 不传时用当前主窗口；窗口不存在（登录首启还没建）也允许改状态，
    /// 之后的创建路径会按持久化状态把几何补上。
    func setCollapsed(_ collapsed: Bool, window: NSWindow? = nil) {
        guard collapsed != isCollapsed else { return }
        let target = window ?? WindowManager.currentMainWindow
        if let target { rememberWidth(of: target) }
        switches += 1
        applyState(collapsed)
        guard let target else { return }
        applyGeometry(to: target)
    }

    private func applyState(_ collapsed: Bool) {
        isCollapsed = collapsed
        setProgress(collapsed ? 1 : 0)
        showsCollapseHint = collapsed && !hintAcknowledged
        if persists { defaults.set(collapsed, forKey: Self.collapsedKey) }
    }

    private func setProgress(_ value: Double) {
        if value != foldProgress, value != 0, value != 1 {
            publishedIntermediates += 1
        }
        publishedProgressValues.append(value)
        foldProgress = value
    }

    /// 判据用：整段历史上发布过的进度档（必须只有 0 与 1 两档）。
    var progressRosterForTesting: [Double] { publishedProgressValues }

    /// 只给判据用：建窗与恢复也会走 `applyGeometry`，所以数"一次点击写了几次"之前要先归零。
    func resetTransitionCountersForTesting() {
        switches = 0
        geometryWrites = 0
        minSizeWrites = 0
        publishedIntermediates = 0
        publishedProgressValues.removeAll()
    }

    private func rememberWidth(of window: NSWindow) {
        let width = window.frame.width
        guard width >= MainWindowCollapsePolicy.minWidth(collapsed: isCollapsed) else { return }
        guard persists else { return }
        defaults.set(Double(width),
                     forKey: isCollapsed ? Self.collapsedWidthKey : Self.expandedWidthKey)
    }

    /// 把当前状态一次性套到窗口上：宽度按策略（记住的宽 → 各自最小宽 → 屏幕宽），
    /// `minSize` 跟着状态走（折叠后不许被 SwiftUI 弹回 600），并保持左上角。
    /// 一次切换 = 一次 `minSize` 写 + 一次 `setFrame`，中间没有任何被逐拍改宽的第三笔。
    func applyGeometry(to window: NSWindow) {
        let visible = (window.screen ?? NSScreen.main)?.visibleFrame
        let width = MainWindowCollapsePolicy.targetWidth(
            collapsed: isCollapsed,
            expandedWidth: expandedWidth,
            collapsedWidth: collapsedWidth,
            visibleWidth: visible?.width
        )
        window.minSize = NSSize(width: MainWindowCollapsePolicy.minWidth(collapsed: isCollapsed),
                                height: MainWindowCollapsePolicy.minHeight)
        minSizeWrites += 1
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
        geometryWrites += 1
    }
}
