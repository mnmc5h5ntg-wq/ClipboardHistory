import AppKit

@MainActor
enum WindowManager {
    static let mainWindowIdentifier = NSUserInterfaceItemIdentifier("AppWindow")
    /// 由 `WindowConfigurator` 在窗口挂载时注册；只从 MainActor 访问，
    /// 因此不需要 nonisolated(unsafe)（那是把数据竞争静音掉的写法）。
    private(set) static weak var _mainWindow: NSWindow?
    /// 无窗口时创建唯一主窗口的工厂。由 `AppDelegate` 在 init 里安装（它知道 store），
    /// WindowManager 自己不认识 SwiftUI 视图层；未安装时保持"只 present、不创建"的旧行为。
    private(set) static var mainWindowFactory: (@MainActor () -> NSWindow)?

    static func installMainWindowFactory(_ factory: @escaping @MainActor () -> NSWindow) {
        mainWindowFactory = factory
    }

    static func uninstallMainWindowFactoryForTesting() {
        mainWindowFactory = nil
    }

    static func forgetMainWindowForTesting() {
        _mainWindow = nil
    }

    static func registerMainWindow(_ window: NSWindow) {
        _mainWindow = window
        window.identifier = mainWindowIdentifier
    }

    /// `creatingIfNeeded` 是两种语义的分界：
    /// - `true`（Dock reopen / 菜单「显示主窗口」/ ⌘S / 热键 / 登录首启恢复）：没有窗口就**创建**。
    /// - `false`（启动后 200ms 的 best-effort）：只 present 已存在的窗口，绝不创建。
    /// 去掉这个分界会把「启动时不打开主窗口」那个设置悄悄作废。
    static func showMainWindow(
        creatingIfNeeded: Bool = true,
        menuBarController: MenuBarController? = nil
    ) {
        LifecycleDebugLogger.log("WindowManager.showMainWindow called creatingIfNeeded=\(creatingIfNeeded)")
        LifecycleDebugLogger.logAppState("before showMainWindow", menuBarController: menuBarController)
        LifecycleDebugLogger.log("[SHOW-WIN] showMainWindow called. _mainWindow=\(_mainWindow != nil) NSApp.windows.count=\(NSApp.windows.count)")
        for (i, w) in NSApp.windows.enumerated() {
            LifecycleDebugLogger.log("[SHOW-WIN] window[\(i)] title='\(w.title)' visible=\(w.isVisible) miniaturized=\(w.isMiniaturized) id=\(w.identifier?.rawValue ?? "nil") class=\(String(describing: type(of: w)))")
        }
        
        NSApplication.shared.unhide(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)

        LifecycleDebugLogger.log("[SHOW-WIN] after unhide+activate _mainWindow=\(_mainWindow != nil)")

        // 优先使用直接引用。弱引用还活着不等于窗口还能用：被 AppKit 关掉的窗口会离开
        // `NSApp.windows`，但别处的强引用可能让它继续存活（测试里销毁窗口时就是这个形状）。
        // 只认"仍在 AppKit 窗口表里"的那一份 —— 用户的关窗走 delegate（orderOut，仍在表里），
        // 所以这条检查不会把"隐藏"误判成"没有"。
        if let window = _mainWindow, isAttachedToApplication(window) {
            LifecycleDebugLogger.log("[SHOW-WIN] found via weak ref. isMiniaturized=\(window.isMiniaturized) isVisible=\(window.isVisible)")
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            present(window)
            LifecycleDebugLogger.logAppState("after showMainWindow via weak ref", menuBarController: menuBarController)
            return
        }

        // 回退：在窗口列表中搜索
        if let window = mainWindow {
            LifecycleDebugLogger.log("[SHOW-WIN] found via identifier search. isMiniaturized=\(window.isMiniaturized) isVisible=\(window.isVisible)")
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            present(window)
            LifecycleDebugLogger.logAppState("after showMainWindow via identifier search", menuBarController: menuBarController)
            return
        }

        // R522：登录项启动时 WindowGroup 可能一个窗口都没建。这里必须先查"有没有"，
        // 没有就创建**唯一一个** —— 否则 Dock 点击 / 菜单 / ⌘S 全部无声无息。
        if creatingIfNeeded, let created = createMainWindow() {
            present(created)
            LifecycleDebugLogger.logAppState("after showMainWindow created main window", menuBarController: menuBarController)
            return
        }

        LifecycleDebugLogger.log("WindowManager.showMainWindow no existing SwiftUI main window found")
        LifecycleDebugLogger.logAppState("after showMainWindow no existing window", menuBarController: menuBarController)
    }

    /// 创建唯一主窗口。**唯一性由 `showMainWindow` 那两段 existing 检查保证**（同一把闸门），
    /// 这个函数自己不再查一次 —— 重复的门会让"删掉一段仍不重复"的刀失去对象。
    @discardableResult
    static func createMainWindow() -> NSWindow? {
        guard let factory = mainWindowFactory else {
            LifecycleDebugLogger.log("[SHOW-WIN] no main window factory installed")
            return nil
        }
        let window = factory()
        registerMainWindow(window)
        LifecycleDebugLogger.log("[SHOW-WIN] created main window id=\(window.identifier?.rawValue ?? "nil")")
        return window
    }

    static var hasVisibleMainWindow: Bool { isVisibleAppContentWindowPresent }

    static var currentMainWindow: NSWindow? { _mainWindow ?? mainWindow }

    /// 把窗口带到前台。**没有淡入**（动效审计 M10 被撤，理由在报告 §12.1 更正 #7 与红线 8）：
    /// 主窗口和 QuickPick 一样是热键 / 菜单栏唤起的日常入口，那一类路径上同类全部瞬时出现；
    /// 而这个仓库有过一整类"窗口其实存在但看不见"的缺陷（`[SHOW-WIN]` 那些日志就是为它加的），
    /// 把"是否出现"交给一个可被打断、可能有代际竞态的动画，是拿可靠性换质感。
    /// 动效仍然有，但只在内容与尺寸那一侧：行内状态、详情换类型、提示条进出。
    /// 出现方式交给系统 —— 它知道 Stage Manager 与全屏空间要什么。
    private static func present(_ window: NSWindow) {
        window.makeKeyAndOrderFront(nil)
        window.orderFrontRegardless()
    }

    static func restoreMainWindowIfNeeded(
        reason: String,
        menuBarController: MenuBarController? = nil
    ) {
        LifecycleDebugLogger.log("restoreMainWindowIfNeeded reason='\(reason)'")
        let hasVisibleAppWindow = isVisibleAppContentWindowPresent
        LifecycleDebugLogger.log("restoreMainWindowIfNeeded hasVisibleAppWindow=\(hasVisibleAppWindow)")
        if !hasVisibleAppWindow {
            showMainWindow(
                menuBarController: menuBarController
            )
        }
    }

    private static var mainWindow: NSWindow? {
        NSApplication.shared.windows.first { window in
            isAppContentWindow(window)
        }
    }

    private static var isVisibleAppContentWindowPresent: Bool {
        NSApplication.shared.windows.contains { window in
            isAppContentWindow(window) && window.isVisible
        }
    }

    static func isAppContentWindow(_ window: NSWindow) -> Bool {
        let className = String(describing: type(of: window))
        return !(window is NSPanel)
            && !className.contains("NSStatusBarWindow")
            && window.identifier == mainWindowIdentifier
    }

    private static func isAttachedToApplication(_ window: NSWindow) -> Bool {
        NSApplication.shared.windows.contains { $0 === window }
    }
}
