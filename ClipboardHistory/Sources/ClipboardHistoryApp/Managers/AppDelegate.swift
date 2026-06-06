import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private weak var manager: ClipboardManager?
    private let menuBarController = MenuBarController()
    private var isConfigured = false
    private var didDeferInitialActivationRestore = false

    func configure(manager: ClipboardManager) {
        LifecycleDebugLogger.log("AppDelegate.configure called isConfigured=\(isConfigured)")
        self.manager = manager
        menuBarController.configure(manager: manager)
        LifecycleDebugLogger.logAppState("after AppDelegate.configure", menuBarController: menuBarController)

        guard !isConfigured else { return }
        isConfigured = true
        manager.startMonitoring(after: 0.4)
        LifecycleDebugLogger.log("ClipboardManager.startMonitoring scheduled from AppDelegate.configure")
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        LifecycleDebugLogger.reset()
        LifecycleDebugLogger.log("applicationDidFinishLaunching called")
        NSApp.setActivationPolicy(.regular)
        installReopenAppleEventHandler()
        LifecycleDebugLogger.logAppState("after applicationDidFinishLaunching", menuBarController: menuBarController)
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationDidBecomeActive called")
        LifecycleDebugLogger.logAppState("after applicationDidBecomeActive", menuBarController: menuBarController)
        if didDeferInitialActivationRestore {
            menuBarController.restoreMainWindowIfNeeded(reason: "applicationDidBecomeActive")
        } else {
            didDeferInitialActivationRestore = true
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 300_000_000)
                self.menuBarController.restoreMainWindowIfNeeded(reason: "initial applicationDidBecomeActive deferred")
            }
        }
        LifecycleDebugLogger.logAppState("after applicationDidBecomeActive restore check", menuBarController: menuBarController)
    }

    func applicationDidResignActive(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationDidResignActive called")
        LifecycleDebugLogger.logAppState("after applicationDidResignActive", menuBarController: menuBarController)
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        LifecycleDebugLogger.log("applicationShouldHandleReopen called hasVisibleWindows=\(flag)")
        LifecycleDebugLogger.logAppState("before applicationShouldHandleReopen show", menuBarController: menuBarController)
        menuBarController.showMainWindow()
        LifecycleDebugLogger.logAppState("after applicationShouldHandleReopen show", menuBarController: menuBarController)
        return true
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        LifecycleDebugLogger.log("applicationShouldTerminateAfterLastWindowClosed called -> false")
        LifecycleDebugLogger.logAppState("after applicationShouldTerminateAfterLastWindowClosed", menuBarController: menuBarController)
        return false
    }

    func applicationWillTerminate(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationWillTerminate called")
        LifecycleDebugLogger.logAppState("before applicationWillTerminate", menuBarController: menuBarController)
        NSAppleEventManager.shared().removeEventHandler(
            forEventClass: AEEventClass(kCoreEventClass),
            andEventID: AEEventID(kAEReopenApplication)
        )
        manager?.stopMonitoring()
        LifecycleDebugLogger.close()
    }

    func showMainWindow() {
        menuBarController.showMainWindow()
    }

    func refreshHistory() {
        menuBarController.refreshHistory()
    }

    func confirmAndClearHistory() {
        menuBarController.confirmAndClearHistory()
    }

    func quit() {
        menuBarController.quit()
    }

    private func installReopenAppleEventHandler() {
        LifecycleDebugLogger.log("installReopenAppleEventHandler called")
        NSAppleEventManager.shared().setEventHandler(
            self,
            andSelector: #selector(handleReopenApplicationEvent(_:withReplyEvent:)),
            forEventClass: AEEventClass(kCoreEventClass),
            andEventID: AEEventID(kAEReopenApplication)
        )
    }

    @objc private func handleReopenApplicationEvent(
        _ event: NSAppleEventDescriptor,
        withReplyEvent replyEvent: NSAppleEventDescriptor
    ) {
        LifecycleDebugLogger.log("handleReopenApplicationEvent called")
        LifecycleDebugLogger.logAppState("before handleReopenApplicationEvent show", menuBarController: menuBarController)
        menuBarController.showMainWindow()
        LifecycleDebugLogger.logAppState("after handleReopenApplicationEvent show", menuBarController: menuBarController)
    }
}
