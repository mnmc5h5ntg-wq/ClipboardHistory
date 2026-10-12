import AppKit

@MainActor
enum WindowManager {
    static let mainWindowIdentifier = NSUserInterfaceItemIdentifier("AppWindow")
    /// 由 `WindowConfigurator` 在窗口挂载时注册；只从 MainActor 访问，
    /// 因此不需要 nonisolated(unsafe)（那是把数据竞争静音掉的写法）。
    private(set) static weak var _mainWindow: NSWindow?

    static func registerMainWindow(_ window: NSWindow) {
        _mainWindow = window
        window.identifier = mainWindowIdentifier
    }

    static func showMainWindow(
        menuBarController: MenuBarController? = nil
    ) {
        LifecycleDebugLogger.log("WindowManager.showMainWindow called")
        LifecycleDebugLogger.logAppState("before showMainWindow", menuBarController: menuBarController)
        LifecycleDebugLogger.log("[SHOW-WIN] showMainWindow called. _mainWindow=\(_mainWindow != nil) NSApp.windows.count=\(NSApp.windows.count)")
        for (i, w) in NSApp.windows.enumerated() {
            LifecycleDebugLogger.log("[SHOW-WIN] window[\(i)] title='\(w.title)' visible=\(w.isVisible) miniaturized=\(w.isMiniaturized) id=\(w.identifier?.rawValue ?? "nil") class=\(String(describing: type(of: w)))")
        }
        
        NSApplication.shared.unhide(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)

        LifecycleDebugLogger.log("[SHOW-WIN] after unhide+activate _mainWindow=\(_mainWindow != nil)")

        // 优先使用直接引用
        if let window = _mainWindow {
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

        LifecycleDebugLogger.log("WindowManager.showMainWindow no existing SwiftUI main window found")
        LifecycleDebugLogger.logAppState("after showMainWindow no existing window", menuBarController: menuBarController)
    }

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
}
