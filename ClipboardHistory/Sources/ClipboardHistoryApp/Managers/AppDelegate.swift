import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let hotKeySettings = HotKeySettings()
    private lazy var shell = ApplicationShell(hotKeySettings: hotKeySettings)

    func configure(manager: ClipboardManager) {
        shell.configure(manager: manager)
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        LifecycleDebugLogger.reset()
        LifecycleDebugLogger.log("applicationDidFinishLaunching called")
        NSApp.setActivationPolicy(.regular)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleShowMainWindowHotKeyPressed(_:)),
            name: .showMainWindowHotKeyPressed,
            object: nil
        )
        hotKeySettings.start()
        installReopenAppleEventHandler()
        shell.applicationDidFinishLaunching(appDelegate: self)
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationDidBecomeActive called")
        shell.applicationDidBecomeActive()
    }

    func applicationDidResignActive(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationDidResignActive called")
        shell.applicationDidResignActive()
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        LifecycleDebugLogger.log("applicationShouldHandleReopen called hasVisibleWindows=\(flag)")
        shell.handleReopen()
        return true
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        LifecycleDebugLogger.log("applicationShouldTerminateAfterLastWindowClosed called -> false")
        return shell.shouldTerminateAfterLastWindowClosed()
    }

    func applicationWillTerminate(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationWillTerminate called")
        shell.applicationWillTerminate()
        NSAppleEventManager.shared().removeEventHandler(
            forEventClass: AEEventClass(kCoreEventClass),
            andEventID: AEEventID(kAEReopenApplication)
        )
        NotificationCenter.default.removeObserver(
            self,
            name: .showMainWindowHotKeyPressed,
            object: nil
        )
        hotKeySettings.stop()
        LifecycleDebugLogger.close()
    }

    func showMainWindow() {
        shell.showMainWindow()
    }

    func refreshHistory() {
        shell.refreshHistory()
    }

    func confirmAndClearHistory() {
        shell.confirmAndClearHistory()
    }

    func showSettings() {
        shell.showSettings()
    }

    @objc func showSettingsFromMenu() {
        showSettings()
    }

    @objc func showAboutPanel() {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.2.1"
        let githubURL = "https://github.com/mnmc5h5ntg-wq/ClipboardHistory"
        NSApplication.shared.orderFrontStandardAboutPanel(options: [
            .applicationName: "时间剪史",
            .applicationVersion: version,
            .credits: NSAttributedString(
                string: """
                作者：王子懿
                License：MIT
                GitHub：\(githubURL)

                一个 macOS 原生风格的剪贴板历史管理工具，支持文本、图片和常见文件预览。
                """
            )
        ])
    }

    @objc func openGitHubRepository() {
        guard let url = URL(string: "https://github.com/mnmc5h5ntg-wq/ClipboardHistory") else { return }
        NSWorkspace.shared.open(url)
    }

    func quit() {
        shell.quit()
    }

    @objc func quitFromMenu() {
        quit()
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
        shell.handleReopen()
    }

    @objc private func handleShowMainWindowHotKeyPressed(_ notification: Notification) {
        LifecycleDebugLogger.log("handleShowMainWindowHotKeyPressed called")
        shell.showMainWindow()
    }

}
