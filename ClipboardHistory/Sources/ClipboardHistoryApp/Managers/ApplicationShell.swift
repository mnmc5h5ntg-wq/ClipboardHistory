import AppKit
import Carbon

@MainActor
final class ApplicationShell {
    private weak var historyStore: HistoryStore?
    private let menuBarController = MenuBarController()
    private let settingsWindowController: SettingsWindowController
    private let confirmation: DestructiveConfirming
    private let pasteKey: PasteKeyExecuting
    private var isConfigured = false
    private var didDeferInitialActivationRestore = false

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        confirmation: DestructiveConfirming = SystemDestructiveConfirming(),
        pasteKey: PasteKeyExecuting = SystemEventsPasteKey()
    ) {
        self.confirmation = confirmation
        self.pasteKey = pasteKey
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
        // 窗口级系统项从源头关掉（issue #13）：允许自动标签页时，AppKit 会往**任何**含标准
        // 编辑动作的菜单里塞「Show All Tabs / Hide Tab Bar / Move Tab to New Window」，
        // 右键菜单也照塞不误，而本产品是单窗口工具，这些项既英文又无关。
        // 必须在建窗之前设 —— 所以放在 willFinishLaunching，而不是某个窗口的配置里。
        NSWindow.allowsAutomaticWindowTabbing = false
        // 编辑态搜索框的右键要在事件派发前截走，否则弹的是共享 field editor 那份系统菜单
        // （issue #13；实测覆盖 `editor.menu` 会被 AppKit 复原，改不动）。
        FieldEditorRightClickInterceptor.install()
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
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { [weak self] in
                self?.sendPasteKeystrokeAfterVerifyingTarget(expected: previousApp)
            }
        }
    }

    /// 注入 ⌘V 之前复核"目标 App 还在不在前台"（审计第二轮 B-6 / 03-04 / 账本 R2-12）。
    ///
    /// `copyAndPasteEntry` 从复制到注入之间有 250ms，这段时间里用户完全可能切走窗口，
    /// 目标 App 也可能自己退出 —— 那时照常注入就会把内容粘进**别的**应用：
    /// 既是正确性问题，也是隐私问题（粘错地方比不粘更糟）。
    /// 取消时要说清"内容还在剪贴板里"，否则用户会以为这次复制丢了。
    func sendPasteKeystrokeAfterVerifyingTarget(expected: NSRunningApplication?) {
        let outcome = PasteTargetCheck.evaluate(
            expectedBundleID: expected?.bundleIdentifier,
            actualBundleID: NSWorkspace.shared.frontmostApplication?.bundleIdentifier,
            expectedTerminated: expected?.isTerminated ?? false
        )
        switch outcome {
        case .proceed:
            sendPasteKeystroke()
        case .targetChanged:
            reportPasteOutcome("目标应用已切换到别处，已取消自动粘贴；内容仍在剪贴板，可手动 ⌘V。")
        case .targetGone:
            reportPasteOutcome("目标应用已退出，已取消自动粘贴；内容仍在剪贴板，可手动 ⌘V。")
        }
    }

    /// 按下 ⌘V 这一步单独拆出来：失败可见性是这条链路唯一需要被测试锁住的行为。
    /// 测试直接调它，既不用等前面两段 activate 延迟，也不会真的往用户界面按键。
    func sendPasteKeystroke() {
        Task { @MainActor [weak self] in
            guard let self else { return }
            self.reportPasteOutcome(await self.pasteKey.synthesizePaste())
        }
    }

    func reportPasteOutcome(_ reason: String?) {
        guard let reason else { return }
        LifecycleDebugLogger.log("自动粘贴失败：\(reason)")
        historyStore?.reportPasteFailure(reason)
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
