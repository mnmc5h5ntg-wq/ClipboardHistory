import AppKit
import SwiftUI

extension Notification.Name {
    static let mainWindowDidHide = Notification.Name("ClipboardHistoryMainWindowDidHide")
}

enum WindowChromeLayout {
    static let trafficLightLeading: CGFloat = 21
    static let trafficLightMinimumBottomInset: CGFloat = 6
    static let trafficLightTrailingGap: CGFloat = 8
    static let trafficLightTopInset: CGFloat = 19

    /// 详情头部内容至少要从窗口顶往下留这么多，才不会被三个按钮压住。
    /// 这是**拿不到真实窗口时的兜底值**；正常情况下由 `WindowChromeMetrics`
    /// 用实测的标题栏高度算出来（见 `trafficLightBandBottom`）。
    static let detailContentTopInsetFallback: CGFloat = 35

    static func trafficLightOrigin(titlebarHeight: CGFloat, buttonHeight: CGFloat) -> NSPoint {
        NSPoint(
            x: trafficLightLeading,
            y: max(
                titlebarHeight - buttonHeight - trafficLightTopInset,
                trafficLightMinimumBottomInset
            )
        )
    }

    /// 按钮带在"距窗口顶多少 pt"这个坐标系里的下边缘。
    ///
    /// 为什么要单独把这个量算出来：详情列的内容是 `.ignoresSafeArea(edges: .top)` 铺到窗口顶的，
    /// 于是它的头部那一行和交通灯住在同一条带里 —— 侧栏开着时灯压在侧栏上看不出来，
    /// **一收起侧栏，详情头部就压到按钮上**（用户实测报的这条）。
    /// 带工具栏时容器高 52pt、灯带底边在 33pt；没有工具栏时是 32pt / 26pt。
    /// 所以这个数不能写死在视图里，得由真的摆放按钮的那段代码给出来。
    static func trafficLightBandBottom(titlebarHeight: CGFloat, buttonHeight: CGFloat) -> CGFloat {
        titlebarHeight - trafficLightOrigin(titlebarHeight: titlebarHeight,
                                           buttonHeight: buttonHeight).y
    }

    /// 头部内容要留出的距离：灯带底边 + 一点呼吸，且不小于兜底值。
    static func detailContentTopInset(titlebarHeight: CGFloat, buttonHeight: CGFloat) -> CGFloat {
        max(trafficLightBandBottom(titlebarHeight: titlebarHeight, buttonHeight: buttonHeight) + 2,
            10)
    }
}

/// 把 AppKit 实测到的窗口装饰几何，交给需要躲开它的那一层（详情头部）。
///
/// 为什么不是视图自己算：SwiftUI 拿不到"这个窗口有没有工具栏、标题栏容器多高"，
/// 而按钮正是 AppKit 那侧（`Coordinator.alignTrafficLights`）在每次 resize / 成为 key
/// / 成为 main / 移动时重新摆放的。**谁摆的谁知道底边在哪**，所以由它发布。
@MainActor
final class WindowChromeMetrics: ObservableObject {
    static let shared = WindowChromeMetrics()

    /// 详情头部内容的顶部留白。初值是兜底值：窗口还没被配置过（离屏夹具、首帧）也要安全。
    @Published private(set) var detailContentTopInset: CGFloat = WindowChromeLayout.detailContentTopInsetFallback

    /// 只有真的变了才发布 —— 这个方法在每次 resize 与每次成为 key 时都会被调，
    /// 无脑赋值会让详情区跟着重排。
    func noteTrafficLights(titlebarHeight: CGFloat, buttonHeight: CGFloat) {
        let next = WindowChromeLayout.detailContentTopInset(titlebarHeight: titlebarHeight,
                                                           buttonHeight: buttonHeight)
        if next != detailContentTopInset { detailContentTopInset = next }
    }

    /// 测试专用：还原到进入该用例之前的值。
    /// 不做还原的话，一条量真实窗口的用例会把几何留给后面所有离屏帧夹具 ——
    /// 同一进程里"跑过哪个测试"会悄悄改变帧。
    /// 刻意要求调用方把原值传回来（而不是复位成兜底值）：兜底值和真实窗口的值不一定相等，
    /// 复位成兜底值等于把"首帧状态"和"测过之后的状态"混为一谈。
    func restoreDetailContentTopInsetForTesting(_ value: CGFloat) {
        detailContentTopInset = value
    }
}

/// 透明标题栏 + 禁用原生全屏 + 跨版本窗口尺寸设置
struct WindowConfigurator: NSViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeNSView(context: Context) -> NSView {
        let view = ConfigurationHostView()
        view.configureWindow = { [coordinator = context.coordinator] window in
            LifecycleDebugLogger.log("WindowConfigurator found window")
            window.identifier = WindowManager.mainWindowIdentifier
            WindowManager.registerMainWindow(window)
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = [.managed, .fullScreenNone]
            window.setContentSize(NSSize(width: 750, height: 560))
            window.minSize = NSSize(width: 600, height: 440)
            coordinator.configure(window: window)
            window.delegate = coordinator
            if let zoomButton = window.standardWindowButton(.zoomButton) {
                zoomButton.isEnabled = false
                zoomButton.toolTip = "时间剪史暂不支持全屏显示"
            }
            LifecycleDebugLogger.logAppState("after WindowConfigurator setup")
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}

    private final class ConfigurationHostView: NSView {
        var configureWindow: ((NSWindow) -> Void)?
        private weak var configuredWindow: NSWindow?

        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            configureAttachedWindowIfNeeded()
        }

        override func viewDidMoveToSuperview() {
            super.viewDidMoveToSuperview()
            configureAttachedWindowIfNeeded()
        }

        override func layout() {
            super.layout()
            configureAttachedWindowIfNeeded()
        }

        private func configureAttachedWindowIfNeeded() {
            guard let window, configuredWindow !== window else { return }
            configuredWindow = window
            configureWindow?(window)
        }
    }

    @MainActor
    final class Coordinator: NSObject, NSWindowDelegate {
        private weak var configuredWindow: NSWindow?

        func configure(window: NSWindow) {
            configuredWindow = window
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
            // Aggressive follow-up: SwiftUI may recreate the toggle across several frames
            for delay in [0.0, 0.02, 0.08, 0.2, 0.5, 1.0] {
                DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
                    guard let self, let window = self.configuredWindow else { return }
                    self.removeSidebarToolbarButton(from: window)
                    self.pinSidebarVisible(in: window)
                }
            }
        }

        func windowDidBecomeKey(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
        }

        func windowDidBecomeMain(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
        }

        func windowDidResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
        }

        func windowDidEndLiveResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
        }

        func windowDidMove(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
        }

        func windowShouldClose(_ sender: NSWindow) -> Bool {
            LifecycleDebugLogger.log("windowShouldClose called title='\(sender.title)'")
            LifecycleDebugLogger.logAppState("before windowShouldClose")
            // 最小化到 Dock，macOS 12 上最可靠的窗口保持方案
            sender.orderOut(nil)
            NotificationCenter.default.post(name: .mainWindowDidHide, object: sender)
            LifecycleDebugLogger.logAppState("after windowShouldClose miniaturize")
            return false
        }

        func windowWillClose(_ notification: Notification) {
            // 保留这个回调：`windowShouldClose` 返回 false 时它不该触发，
            // 一旦触发说明窗口被销毁（历史 bug 的表现形式），值得进日志。
            LifecycleDebugLogger.logAppState("windowWillClose")
        }

        private func alignTrafficLights(in window: NSWindow) {
            guard let closeButton = window.standardWindowButton(.closeButton),
                  let minimizeButton = window.standardWindowButton(.miniaturizeButton),
                  let zoomButton = window.standardWindowButton(.zoomButton),
                  let titlebarContainer = closeButton.superview else {
                return
            }

            let buttonOrigin = WindowChromeLayout.trafficLightOrigin(
                titlebarHeight: titlebarContainer.bounds.height,
                buttonHeight: closeButton.frame.height
            )
            // 把"灯带底边在哪"发布给详情头部 —— 它铺到了窗口顶，必须躲开这三个按钮。
            WindowChromeMetrics.shared.noteTrafficLights(
                titlebarHeight: titlebarContainer.bounds.height,
                buttonHeight: closeButton.frame.height
            )
            closeButton.setFrameOrigin(buttonOrigin)
            minimizeButton.setFrameOrigin(
                NSPoint(
                    x: buttonOrigin.x + closeButton.frame.width + WindowChromeLayout.trafficLightTrailingGap,
                    y: buttonOrigin.y
                )
            )
            zoomButton.setFrameOrigin(
                NSPoint(
                    x: buttonOrigin.x + (closeButton.frame.width + WindowChromeLayout.trafficLightTrailingGap) * 2,
                    y: buttonOrigin.y
                )
            )
        }

        private func removeSidebarToolbarButton(from window: NSWindow) {
            guard let toolbar = window.toolbar else { return }
            for index in toolbar.items.indices.reversed() {
                let item = toolbar.items[index]
                if isSidebarToolbarItem(item) {
                    toolbar.removeItem(at: index)
                }
            }
        }

        /// 把侧栏钉成"永远在"（对齐系统设置那类 App）：不允许折叠，
        /// 分隔条最多拖到列的最小宽度就停住；已经是折叠状态的（旧版本留下的窗口存档）当场展开。
        ///
        /// 为什么必须在 AppKit 层做：SwiftUI 那侧能拿掉的只有工具栏按钮和菜单命令
        /// （`toolbar(removing: .sidebarToggle)` 还只在 macOS 14+ 生效），
        /// 而**拖分隔条**这条路根本不经过它们 —— 用户报的"收起侧栏后左上角互相遮挡"
        /// 就是从这条路走出来的。与其给遮挡打补丁再指望用户别那么用，不如让那个状态不可达。
        ///
        /// 为什么要顺手展开：`NavigationSplitView` 会把列的可见性存进窗口/场景存档，
        /// 只在装新版**之前**收起过侧栏的那台机器上，第一帧可能就是收起的。
        /// 只关 `canCollapse` 等于"以后不能再收，但这次还是空的"，对报缺陷的用户来说没修。
        ///
        /// 返回值表示"这次真的找到了分栏器并钉上了"。调用方（含测试）必须能区分
        /// "钉好了"和"根本没找到分栏器"，否则一个找不到东西的实现会永远绿。
        @discardableResult
        func pinSidebarVisible(in window: NSWindow) -> Bool {
            guard let split = Self.splitViewController(in: window) else {
                LifecycleDebugLogger.log("pinSidebarVisible: 没找到 NSSplitViewController，侧栏仍可被拖没")
                return false
            }
            guard let sidebar = Self.sidebarItem(of: split) else {
                LifecycleDebugLogger.log("pinSidebarVisible: 分栏器里没有列项")
                return false
            }
            var changed = false
            if sidebar.canCollapse {
                sidebar.canCollapse = false
                changed = true
            }
            if sidebar.isCollapsed {
                sidebar.isCollapsed = false
                changed = true
            }
            if changed {
                LifecycleDebugLogger.log("pinSidebarVisible: 侧栏已钉为永远显示（分栏器列项数=\(split.splitViewItems.count)）")
            }
            return true
        }

        /// 找到承载 SwiftUI `NavigationSplitView` 的那个 `NSSplitViewController`。两条路线都要走：
        ///
        /// ① 控制器树 BFS：`window.contentViewController` 有值的宿主（AppKit 壳、设置窗口）够用。
        ///    但主窗口上它**是 nil** —— 我们是把 `NSHostingView` 直接摆进 `contentView` 的，
        ///    没有中间控制器。第一版只写了这条，于是 `pinSidebarVisible` 在真窗口上永远返回
        ///    false，只在日志里留一句"没找到"；是那条 A/B 判据（`WindowChromeLayoutTests`）把它抓出来的。
        /// ② 视图树 BFS：SwiftUI 会把 `NSSplitView` 摆在 `contentView` 底下，而
        ///    `NSSplitViewController` 就是那块 split view 的 `delegate`（AppKit 的既有约定），
        ///    所以顺着视图树找 `NSSplitView`、再问它的 delegate，比依赖任何私有类名都稳。
        ///
        /// 层级与深度会随系统版本变（本机 27 与 CI 的 15 上垫的容器数就不一样），
        /// 所以两条都是广度优先，而不是"取第 N 层第 M 个子视图"。
        static func splitViewController(in window: NSWindow) -> NSSplitViewController? {
            if let fromControllerTree = splitController(inControllerTreeOf: window) { return fromControllerTree }
            return window.contentView.flatMap { splitController(inViewTreeOf: $0) }
        }

        private static func splitController(inControllerTreeOf window: NSWindow) -> NSSplitViewController? {
            var queue: [NSViewController] = window.contentViewController.map { [$0] } ?? []
            while let controller = queue.first {
                queue.removeFirst()
                if let split = controller as? NSSplitViewController { return split }
                queue.append(contentsOf: controller.children)
            }
            return nil
        }

        private static func splitController(inViewTreeOf root: NSView) -> NSSplitViewController? {
            var queue: [NSView] = [root]
            while let view = queue.first {
                queue.removeFirst()
                if let split = view as? NSSplitView, let owner = split.delegate as? NSSplitViewController {
                    return owner
                }
                queue.append(contentsOf: view.subviews)
            }
            return nil
        }

        /// 哪一列是侧栏。优先按 `behavior == .sidebar` 认；
        /// 认不出来时退回第一列（SwiftUI 的分栏器里侧栏就是第一列），
        /// 但**不退回"全部列都钉上"** —— 把内容列也钉成不可折叠，
        /// 以后真要加可折叠的检查器列就会莫名其妙失效。
        static func sidebarItem(of split: NSSplitViewController) -> NSSplitViewItem? {
            split.splitViewItems.first { $0.behavior == .sidebar } ?? split.splitViewItems.first
        }

        /// 不是 private：审计第二轮 08-08 / 13-08 指出这条"猜出来再删"的判断没有任何测试。
        /// 它决定要不要从窗口工具栏里摘掉一个按钮，误判的代价是**用户少了一个按钮**，
        /// 所以正反两方向都得有断言钉住（放宽只为测试，行为未变）。
        func isSidebarToolbarItem(_ item: NSToolbarItem) -> Bool {
            if item.action == #selector(NSSplitViewController.toggleSidebar(_:)) {
                return true
            }

            var fields = [
                item.itemIdentifier.rawValue,
                item.label,
                item.paletteLabel,
                item.toolTip ?? ""
            ]
            if let action = item.action {
                fields.append(NSStringFromSelector(action))
            }
            if let view = item.view {
                fields.append(view.accessibilityLabel() ?? "")
                fields.append(accessibilityAndActionText(in: view))
            }
            let normalizedFields = fields.map(\.localizedLowercase)

            return normalizedFields.contains { field in
                field.contains("sidebar")
                    || field.contains("togglesidebar")
                    || field.contains("边栏")
                    || field.contains("侧边栏")
            }
        }

        private func accessibilityAndActionText(in view: NSView) -> String {
            var parts: [String] = [
                view.identifier?.rawValue ?? "",
                view.accessibilityLabel() ?? "",
                view.accessibilityIdentifier()
            ]

            if let control = view as? NSControl {
                parts.append(control.action.map { NSStringFromSelector($0) } ?? "")
                parts.append(control.toolTip ?? "")
            }

            for subview in view.subviews {
                parts.append(accessibilityAndActionText(in: subview))
            }

            return parts.joined(separator: " ")
        }
    }
}
