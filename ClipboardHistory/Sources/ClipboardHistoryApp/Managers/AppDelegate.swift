import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    static let sharedHistoryStore = HistoryStore()

    let historyStore = AppDelegate.sharedHistoryStore
    private let showMainWindowHotKeySettings = HotKeySettings(action: .showMainWindow)
    private let repeatCopyHotKeySettings = HotKeySettings(action: .repeatCopy)
    private let loginItemSettings = LoginItemSettings()
    let contextPreferences = ContextPreferenceSettings()
    private lazy var shell = ApplicationShell(
        showMainWindowHotKeySettings: showMainWindowHotKeySettings,
        repeatCopyHotKeySettings: repeatCopyHotKeySettings,
        loginItemSettings: loginItemSettings,
        contextPreferences: contextPreferences
    )

    func configure() {
        historyStore.contextPreferences = contextPreferences
        shell.configure(historyStore: historyStore)
    }

    func applicationWillFinishLaunching(_ notification: Notification) {
        clearSavedApplicationStateIfNeeded()
        shell.applicationWillFinishLaunching(appDelegate: self)
    }

    // MARK: - State Restoration (prevent crash on macOS 12)

    func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        false
    }

    func applicationShouldSaveApplicationState(_ coder: NSCoder) -> Bool {
        false
    }

    func applicationShouldRestoreApplicationState(_ coder: NSCoder) -> Bool {
        false
    }

    private func clearSavedApplicationStateIfNeeded() {
        guard let bundleID = Bundle.main.bundleIdentifier else { return }
        let savedStateURL = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Saved Application State")
            .appendingPathComponent("\(bundleID).savedState")
        try? FileManager.default.removeItem(at: savedStateURL)
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
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleRepeatCopyHotKeyPressed(_:)),
            name: .repeatCopyHotKeyPressed,
            object: nil
        )
        showMainWindowHotKeySettings.start()
        repeatCopyHotKeySettings.start()
        loginItemSettings.refresh()
        installReopenAppleEventHandler()
        configure()
        shell.applicationDidFinishLaunching(appDelegate: self)
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 200_000_000)
            shell.showExistingMainWindowIfAvailable()
        }
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        LifecycleDebugLogger.log("applicationDidBecomeActive called")
        shell.applicationDidBecomeActive()
        // macOS 12: 从隐藏状态恢复时重新显示窗口
        if NSApp.windows.allSatisfy({ $0.isVisible == false || $0.isMiniaturized }) {
            shell.showMainWindow()
        }
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
        NotificationCenter.default.removeObserver(
            self,
            name: .repeatCopyHotKeyPressed,
            object: nil
        )
        showMainWindowHotKeySettings.stop()
        repeatCopyHotKeySettings.stop()
        LifecycleDebugLogger.close()
    }

    func showMainWindow() {
        shell.showMainWindow()
    }

    func refreshHistory() {
        shell.refreshHistory()
    }

    func copyHistoryEntry(id: UUID) {
        shell.copyHistoryEntry(id: id)
    }

    func copyAndPasteHistoryEntry(id: UUID) {
        guard let entry = historyStore.entries.first(where: { $0.id == id }) else {
            return
        }

        // 诊断A: 记录当前 frontmostApp
        if let front = NSWorkspace.shared.frontmostApplication {
        }

        historyStore.perform(.recordRecommendationAccepted(entry.id))
        shell.copyAndPasteEntry(entry)
    }

    func confirmAndClearHistory() {
        shell.confirmAndClearHistory()
    }

    func perform(_ command: AppCommand) {
        shell.perform(command)
    }

    func showSettings() {
        shell.showSettings()
    }

    @objc func showSettingsFromMenu() {
        showSettings()
    }

    @objc func showAboutPanel() {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.2.2beta"
        let githubURL = "https://github.com/mnmc5h5ntg-wq/ClipboardHistory"
        NSApplication.shared.orderFrontStandardAboutPanel(options: [
            .applicationName: "时间剪史",
            .applicationVersion: version,
            .credits: NSAttributedString(
                string: """
                作者：王子懿
                License：WTFPL
                GitHub：\(githubURL)

                一个 macOS 原生风格的剪贴板历史管理工具，支持文本、图片、文件和视频预览。
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

    @objc private func handleRepeatCopyHotKeyPressed(_ notification: Notification) {
        LifecycleDebugLogger.log("handleRepeatCopyHotKeyPressed called")
        shell.repeatCopySelectedEntry()
    }

}
