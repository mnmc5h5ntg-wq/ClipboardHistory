import AppKit

@MainActor
final class ApplicationShell {
    private weak var historyStore: HistoryStore?
    private let menuBarController = MenuBarController()
    private let mainMenuController = MainMenuController()
    private let settingsWindowController: SettingsWindowController
    private var isConfigured = false
    private var didDeferInitialActivationRestore = false

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings
    ) {
        self.settingsWindowController = SettingsWindowController(
            showMainWindowHotKeySettings: showMainWindowHotKeySettings,
            repeatCopyHotKeySettings: repeatCopyHotKeySettings,
            loginItemSettings: loginItemSettings
        )
    }

    func configure(historyStore: HistoryStore) {
        LifecycleDebugLogger.log("ApplicationShell.configure called isConfigured=\(isConfigured)")
        self.historyStore = historyStore
        menuBarController.configure(
            commandHandler: { [weak self] command in
                self?.perform(command)
            },
            entriesProvider: { [weak historyStore] in
                guard let historyStore else { return [] }
                return historyStore.entries
            },
            entryHandler: { [weak self] entry in
                self?.copyHistoryEntry(entry)
            }
        )
        LifecycleDebugLogger.logAppState("after ApplicationShell.configure", menuBarController: menuBarController)

        guard !isConfigured else { return }
        isConfigured = true
        historyStore.startMonitoring(after: 0.4)
        LifecycleDebugLogger.log("HistoryStore.startMonitoring scheduled from ApplicationShell.configure")
    }

    func applicationDidFinishLaunching(appDelegate: AppDelegate) {
        mainMenuController.configure(appDelegate: appDelegate)
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidFinishLaunching", menuBarController: menuBarController)
    }

    func applicationDidBecomeActive() {
        mainMenuController.installMainMenuRepeatedly()
        LifecycleDebugLogger.logAppState("after ApplicationShell.applicationDidBecomeActive", menuBarController: menuBarController)
        if didDeferInitialActivationRestore {
            WindowManager.restoreMainWindowIfNeeded(reason: "applicationDidBecomeActive", menuBarController: menuBarController)
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

    func confirmAndClearHistory() {
        let alert = NSAlert()
        alert.messageText = "清空未收藏记录"
        alert.informativeText = "收藏记录会保留，其余历史会被清空。"
        alert.alertStyle = .warning
        alert.addButton(withTitle: "清空")
        alert.addButton(withTitle: "取消")

        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            historyStore?.perform(.clear)
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
