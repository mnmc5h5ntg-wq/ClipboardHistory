import AppKit

@MainActor
final class ApplicationShell {
    private weak var manager: ClipboardManager?
    private let menuBarController = MenuBarController()
    private let mainMenuController = MainMenuController()
    private let settingsWindowController: SettingsWindowController
    private var isConfigured = false
    private var didDeferInitialActivationRestore = false

    init(hotKeySettings: HotKeySettings) {
        self.settingsWindowController = SettingsWindowController(hotKeySettings: hotKeySettings)
    }

    func configure(manager: ClipboardManager) {
        LifecycleDebugLogger.log("ApplicationShell.configure called isConfigured=\(isConfigured)")
        self.manager = manager
        menuBarController.configure(manager: manager)
        LifecycleDebugLogger.logAppState("after ApplicationShell.configure", menuBarController: menuBarController)

        guard !isConfigured else { return }
        isConfigured = true
        manager.startMonitoring(after: 0.4)
        LifecycleDebugLogger.log("ClipboardManager.startMonitoring scheduled from ApplicationShell.configure")
    }

    func applicationDidFinishLaunching(appDelegate: AppDelegate) {
        mainMenuController.configure(appDelegate: appDelegate)
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidFinishLaunching", menuBarController: menuBarController)
    }

    func applicationDidBecomeActive() {
        mainMenuController.installMainMenuRepeatedly()
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidBecomeActive", menuBarController: menuBarController)
        if didDeferInitialActivationRestore {
            menuBarController.restoreMainWindowIfNeeded(reason: "applicationDidBecomeActive")
        } else {
            didDeferInitialActivationRestore = true
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 300_000_000)
                self.menuBarController.restoreMainWindowIfNeeded(reason: "initial applicationDidBecomeActive deferred")
            }
        }
        LifecycleDebugLogger.logAppState("after ApplicationShell restore check", menuBarController: menuBarController)
    }

    func applicationDidResignActive() {
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidResignActive", menuBarController: menuBarController)
    }

    func handleReopen() {
        LifecycleDebugLogger.logAppState("before ApplicationShell.handleReopen", menuBarController: menuBarController)
        menuBarController.showMainWindow()
        LifecycleDebugLogger.logAppState("after ApplicationShell.handleReopen", menuBarController: menuBarController)
    }

    func shouldTerminateAfterLastWindowClosed() -> Bool {
        LifecycleDebugLogger.logAppState("after ApplicationShell.shouldTerminateAfterLastWindowClosed", menuBarController: menuBarController)
        return false
    }

    func applicationWillTerminate() {
        LifecycleDebugLogger.logAppState("before ApplicationShell.applicationWillTerminate", menuBarController: menuBarController)
        manager?.stopMonitoring()
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

    func showSettings() {
        settingsWindowController.show()
    }

    func quit() {
        menuBarController.quit()
    }
}
