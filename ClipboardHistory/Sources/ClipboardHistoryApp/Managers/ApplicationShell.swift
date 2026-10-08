import AppKit
import Carbon

@MainActor
final class ApplicationShell {
    private weak var historyStore: HistoryStore?
    private let menuBarController = MenuBarController()
    private let settingsWindowController: SettingsWindowController
    private let confirmation: DestructiveConfirming
    private var isConfigured = false
    private var didDeferInitialActivationRestore = false

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        confirmation: DestructiveConfirming = SystemDestructiveConfirming()
    ) {
        self.confirmation = confirmation
        self.settingsWindowController = SettingsWindowController(
            showMainWindowHotKeySettings: showMainWindowHotKeySettings,
            repeatCopyHotKeySettings: repeatCopyHotKeySettings,
            loginItemSettings: loginItemSettings,
            contextPreferences: contextPreferences
        )
    }

    func configure(historyStore: HistoryStore) {
        LifecycleDebugLogger.log("ApplicationShell.configure called isConfigured=\(isConfigured)")
        self.historyStore = historyStore
        settingsWindowController.configure(historyStore: historyStore, weightsStore: historyStore.weightsStore)
        menuBarController.configure(
            commandHandler: { [weak self] command in
                self?.perform(command)
            },
            historyStore: historyStore,
            pasteHandler: { [weak self] entry in
                self?.copyAndPasteEntry(entry)
            }
        )
        LifecycleDebugLogger.logAppState("after ApplicationShell.configure", menuBarController: menuBarController)

        guard !isConfigured else { return }
        isConfigured = true
        historyStore.startMonitoring(after: 0.4)

        // 启动后延迟扫描已有图片进行 OCR
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak historyStore] in
            historyStore?.scheduleOCRForExistingImages()
        }
        LifecycleDebugLogger.log("HistoryStore.startMonitoring scheduled from ApplicationShell.configure")
    }

    func applicationWillFinishLaunching(appDelegate: AppDelegate) {
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationWillFinishLaunching", menuBarController: menuBarController)
    }

    func applicationDidFinishLaunching(appDelegate: AppDelegate) {
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidFinishLaunching", menuBarController: menuBarController)
    }

    func applicationDidBecomeActive() {
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidBecomeActive", menuBarController: menuBarController)
        if didDeferInitialActivationRestore {
            WindowManager.restoreMainWindowIfNeeded(
                reason: "applicationDidBecomeActive",
                menuBarController: menuBarController
            )
        } else {
            didDeferInitialActivationRestore = true
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 300_000_000)
                WindowManager.restoreMainWindowIfNeeded(
                    reason: "initial applicationDidBecomeActive deferred",
                    menuBarController: self.menuBarController
                )
            }
        }
        LifecycleDebugLogger.logAppState("after ApplicationShell restore check", menuBarController: menuBarController)
    }

    func applicationDidResignActive() {
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidResignActive", menuBarController: menuBarController)
    }

    func handleReopen() {
        LifecycleDebugLogger.logAppState("before ApplicationShell.handleReopen", menuBarController: menuBarController)
        WindowManager.showMainWindow(menuBarController: menuBarController)
        LifecycleDebugLogger.logAppState("after ApplicationShell.handleReopen", menuBarController: menuBarController)
    }

    func shouldTerminateAfterLastWindowClosed() -> Bool {
        LifecycleDebugLogger.logAppState("after ApplicationShell.shouldTerminateAfterLastWindowClosed", menuBarController: menuBarController)
        return false
    }

    func applicationWillTerminate() {
        LifecycleDebugLogger.logAppState("before ApplicationShell.applicationWillTerminate", menuBarController: menuBarController)
        historyStore?.stopMonitoring()
        historyStore?.flushPendingPersistence()
    }

    func showMainWindow() {
        WindowManager.showMainWindow(menuBarController: menuBarController)
    }

    func showExistingMainWindowIfAvailable() {
        WindowManager.showMainWindow(menuBarController: menuBarController)
    }

    func refreshHistory() {
        historyStore?.perform(.refresh)
    }

    func copyHistoryEntry(_ entry: HistoryStore.Entry) {
        copyHistoryEntry(id: entry.id)
    }

    func copyHistoryEntry(id: UUID) {
        guard let entry = historyStore?.entries.first(where: { $0.id == id }) else { return }
        historyStore?.perform(.copyAndPromote(entry))
    }

    func repeatCopySelectedEntry() {
        historyStore?.perform(.repeatCopySelected)
    }

    /// 清空未收藏：必须先确认。菜单栏与命令面板都走这里
    /// （审计 X-01：旧代码里 .clearHistory 直接删除，带弹窗的函数没有任何调用者）。
    func confirmAndClearHistory() {
        let confirmed = confirmation.confirm(
            title: "清空未收藏记录",
            message: "收藏记录会保留，其余历史会被清空。",
            confirmTitle: "清空",
            cancelTitle: "取消"
        )
        guard confirmed else { return }
        historyStore?.perform(.clear)
    }

    func copyAndPasteEntry(_ entry: HistoryStore.Entry) {
        // 1. 复制到剪贴板
        copyHistoryEntry(entry)

        // 2. 用 Process+osascript 执行 ⌘V（CGEvent.postToPid 在 macOS 15 上被阻止）
        let previousApp = NSWorkspace.shared.runningApplications
            .first { $0.isActive && $0.bundleIdentifier != Bundle.main.bundleIdentifier }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            if let app = previousApp {
                app.activate(options: .activateIgnoringOtherApps)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                let task = Process()
                task.launchPath = "/usr/bin/osascript"
                task.arguments = ["-e", "tell application \"System Events\" to keystroke \"v\" using command down"]
                task.launch()
            }
        }
    }
    func perform(_ command: AppCommand) {
        switch command {
        case .showMainWindow:
            showMainWindow()
        case .showSettings:
            showSettings()
        case .refreshHistory:
            refreshHistory()
        case .clearHistory:
            confirmAndClearHistory()
        case .dismissAllRecommendations:
            historyStore?.perform(.dismissAllRecommendations)
        case .quit:
            quit()
        }
    }

    func showSettings() {
        settingsWindowController.show()
    }

    func quit() {
        NSApplication.shared.terminate(nil)
    }
}
