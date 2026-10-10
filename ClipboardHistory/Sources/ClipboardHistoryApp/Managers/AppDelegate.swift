import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    static let sharedHistoryStore = HistoryStore()

    let historyStore: HistoryStore

    /// 默认仍走全局共享 store（产品路径一字不变）。这个注入接缝是给测试与离屏捕获用的：
    /// 传一个用 `RecordingHistoryPersistence` 造的 store，就能构造 AppDelegate 而**不碰**
    /// `~/Library/Application Support/时间剪史/`。审计第二轮 04 §4.2 N-1 说明为什么必须有它：
    /// 菜单栏面板以前拍不到帧，因为构造 AppDelegate 会读用户真实存档，而 `HOME` 重定向
    /// 实测**不改变** `applicationSupportDirectory`，隔离只能靠注入。
    init(historyStore: HistoryStore? = nil) {
        self.historyStore = historyStore ?? AppDelegate.sharedHistoryStore
        super.init()
    }

    /// 必须显式写出来，不能指望继承 —— 这是 v1.4.8 候选包启动即闪退的原因（D-019 的副作用）。
    ///
    /// Swift 侧写 `AppDelegate()` 会解析到上面那个带默认参数的 `init(historyStore:)`，
    /// 看起来"有 init()"；但 SwiftUI 的 `@NSApplicationDelegateAdaptor(AppDelegate.self)` 存的是
    /// **元类型**，它通过 ObjC 发 `-init`。NSObject 子类一旦自己声明 designated initializer 而没有
    /// `override init()`，编译器就给 `-init` 留一个 trap 桩，于是产品一打开就：
    /// `Fatal error: Use of unimplemented initializer 'init()' for class AppDelegate`。
    /// 守卫在 `AppDelegateStoreInjectionTests`（运行时走元类型那条 + 源码扫描兜底）。
    override convenience init() {
        self.init(historyStore: nil)
    }
    private let showMainWindowHotKeySettings = HotKeySettings(action: .showMainWindow)
    private let repeatCopyHotKeySettings = HotKeySettings(action: .repeatCopy)
    private let quickPickHotKeySettings = HotKeySettings(action: .quickPick)
    private let loginItemSettings = LoginItemSettings()
    let contextPreferences = ContextPreferenceSettings()
    private lazy var shell = ApplicationShell(
        showMainWindowHotKeySettings: showMainWindowHotKeySettings,
        repeatCopyHotKeySettings: repeatCopyHotKeySettings,
        quickPickHotKeySettings: quickPickHotKeySettings,
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
        // 两份进程各自整库写 history.json，后写的会整片盖掉先写的记录（见 InstanceGuard）。
        // 这里静默退出而不是弹窗：正常双击第二个图标时 macOS 本来就是把已有实例带到前台，
        // 只有 `open -n`（make run 用的就是它）才会真的开第二份。
        if let otherPID = InstanceGuard.conflictingPID() {
            LifecycleDebugLogger.log("检测到同 bundle 的另一实例 pid=\(otherPID)：本次启动取消，避免互相覆盖存档")
            NSApp.terminate(nil)
            return
        }
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
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleQuickPickHotKeyPressed(_:)),
            name: .quickPickHotKeyPressed,
            object: nil
        )
        showMainWindowHotKeySettings.start()
        repeatCopyHotKeySettings.start()
        // 快速选择的 ⌃⌥⇧V 也在这里注册：它和另外两个走同一个 Carbon 路径，
        // 注册失败（被别的 App 占了）时 `HotKeySettings` 会自己给出可见的提示文案。
        quickPickHotKeySettings.start()
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
        quickPickHotKeySettings.stop()
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

        historyStore.perform(.recordRecommendationAccepted(entry.id))
        shell.copyAndPasteEntry(entry)
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

    @objc private func handleQuickPickHotKeyPressed(_ notification: Notification) {
        LifecycleDebugLogger.log("handleQuickPickHotKeyPressed called")
        shell.toggleQuickPick()
    }

    @objc private func handleRepeatCopyHotKeyPressed(_ notification: Notification) {
        LifecycleDebugLogger.log("handleRepeatCopyHotKeyPressed called")
        shell.repeatCopySelectedEntry()
    }

}
