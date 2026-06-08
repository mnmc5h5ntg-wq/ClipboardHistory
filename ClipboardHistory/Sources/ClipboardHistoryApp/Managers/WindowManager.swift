import AppKit

@MainActor
enum WindowManager {
    static let mainWindowIdentifier = NSUserInterfaceItemIdentifier("AppWindow")

    static func showMainWindow(menuBarController: MenuBarController? = nil) {
        LifecycleDebugLogger.log("WindowManager.showMainWindow called")
        LifecycleDebugLogger.logAppState("before showMainWindow", menuBarController: menuBarController)
        NSApplication.shared.unhide(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)

        if let window = mainWindow {
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            window.makeKeyAndOrderFront(nil)
            window.orderFrontRegardless()
            LifecycleDebugLogger.logAppState("after showMainWindow existing window", menuBarController: menuBarController)
            return
        }

        LifecycleDebugLogger.log("WindowManager.showMainWindow no app content window found")
        LifecycleDebugLogger.logAppState("after showMainWindow fallback", menuBarController: menuBarController)
    }

    static func restoreMainWindowIfNeeded(reason: String, menuBarController: MenuBarController? = nil) {
        LifecycleDebugLogger.log("restoreMainWindowIfNeeded reason='\(reason)'")
        let hasVisibleAppWindow = isVisibleAppContentWindowPresent
        LifecycleDebugLogger.log("restoreMainWindowIfNeeded hasVisibleAppWindow=\(hasVisibleAppWindow)")
        if !hasVisibleAppWindow {
            showMainWindow(menuBarController: menuBarController)
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
