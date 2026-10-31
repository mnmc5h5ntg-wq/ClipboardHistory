import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R522：登录项启动时 WindowGroup 可能一个窗口都不建 —— 旧版 `showMainWindow` 只会 present，
/// 于是 Dock 点击 / 菜单「显示主窗口」/ ⌘S 全部无声无息。这一卷从**产品入口**（AppDelegate 的
/// reopen / perform / applicationDidBecomeActive、ApplicationShell 的 handleReopen / 启动 best-effort）
/// 断言「没有窗口就创建唯一一个」「已有窗口不重复创建」。
@MainActor
final class MainWindowCreationTests: XCTestCase {
    private var store: HistoryStore!
    private var delegate: AppDelegate!

    private func installProductFactory() {
        store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        // AppDelegate.init 会装上产品工厂（与登录首启同一条路），不是测试另造一个。
        delegate = AppDelegate(historyStore: store)
        NSApplication.shared.setActivationPolicy(.regular)
    }

    private func tearDownProductState() {
        retireAllMainWindows()
        WindowManager.uninstallMainWindowFactoryForTesting()
        delegate = nil
        store = nil
    }

    private var mainWindows: [NSWindow] {
        NSApplication.shared.windows.filter { WindowManager.isAppContentWindow($0) }
    }

    /// 模拟「登录首启时一个 AppWindow 都没有」。不能对 ARC 下的窗口用
    /// `isReleasedWhenClosed=true` 真销毁（会过释放、信号 11）；改成把测试造的窗口
    /// 改名 + orderOut + 清掉弱引用 —— 对产品查找来说等价于不存在，且不影响窗口自身的生命周期。
    private func retireAllMainWindows() {
        for window in mainWindows {
            window.delegate = nil
            window.identifier = NSUserInterfaceItemIdentifier("RetiredAppWindowForTesting")
            window.orderOut(nil)
        }
        WindowManager.forgetMainWindowForTesting()
        settle()
    }

    private func settle(_ seconds: TimeInterval = 0.05) {
        RunLoop.current.run(until: Date().addingTimeInterval(seconds))
    }

    private func onlyMainWindow(_ message: String) -> NSWindow? {
        let windows = mainWindows
        XCTAssertEqual(windows.count, 1, message)
        return windows.first
    }

    func testReopenCreatesExactlyOneVisibleMainWindowWhenNoneExists() {
        installProductFactory()
        defer { tearDownProductState() }
        XCTAssertEqual(mainWindows.count, 0, "测试起点必须没有 AppWindow（登录首启的形状）")

        _ = delegate.applicationShouldHandleReopen(NSApplication.shared, hasVisibleWindows: false)
        settle()
        guard let first = onlyMainWindow("Dock reopen 在无窗口时没有创建主窗口 ⇒ 用户只能退出重开") else {
            return
        }
        XCTAssertTrue(first.isVisible, "创建出来的主窗口不可见")
        XCTAssertEqual(first.identifier, WindowManager.mainWindowIdentifier)
        XCTAssertEqual(first.title, "时间剪史")

        _ = delegate.applicationShouldHandleReopen(NSApplication.shared, hasVisibleWindows: false)
        settle()
        XCTAssertEqual(mainWindows.count, 1, "第二次 reopen 又建了一个主窗口")
        XCTAssertTrue(mainWindows.first === first, "第二次 reopen 换成了另一个窗口对象")
    }

    func testMenuCommandCreatesTheSameSingleWindow() {
        installProductFactory()
        defer { tearDownProductState() }
        retireAllMainWindows()
        XCTAssertEqual(mainWindows.count, 0)

        delegate.perform(.showMainWindow)
        settle()
        guard let first = onlyMainWindow("菜单「显示主窗口」在无窗口时没有创建") else { return }
        XCTAssertTrue(first.isVisible)

        delegate.perform(.showMainWindow)
        settle()
        XCTAssertEqual(mainWindows.count, 1)
        XCTAssertTrue(mainWindows.first === first)
    }

    /// 产品的关窗是**隐藏**（`windowShouldClose` → orderOut + 返回 false）：关掉再 reopen
    /// 必须把同一扇窗口亮出来，且始终只有一个。窗口**不存在**时的创建由上面两条从零起点的用例判。
    func testClosingTheOnlyWindowThenReopeningShowsItAgain() {
        installProductFactory()
        defer { tearDownProductState() }
        retireAllMainWindows()

        WindowManager.showMainWindow()
        settle()
        guard let window = onlyMainWindow("起点没有建出唯一主窗口") else { return }
        XCTAssertTrue(window.isVisible)

        window.close()
        settle()
        XCTAssertEqual(mainWindows.count, 1, "产品关窗把窗口销毁了 ⇒ 再打开只能重建（旧行为是隐藏）")
        XCTAssertFalse(window.isVisible, "close() 之后窗口仍然可见 ⇒ 关窗没有生效")

        _ = delegate.applicationShouldHandleReopen(NSApplication.shared, hasVisibleWindows: false)
        settle()
        XCTAssertEqual(mainWindows.count, 1, "reopen 之后主窗口不是唯一一个")
        XCTAssertTrue(mainWindows.first === window, "reopen 换成了另一个窗口（关窗=隐藏那条契约断了）")
        XCTAssertTrue(window.isVisible, "reopen 没有把隐藏的窗口亮出来")
    }

    /// 登录首启：第一次 `applicationDidBecomeActive` 就必须把窗口建出来（默认设置开）。
    func testFirstActivationCreatesTheWindowEvenWithNoSceneWindow() {
        installProductFactory()
        defer { tearDownProductState() }
        let previous = UserDefaults.standard.object(forKey: "hideMainWindowOnLaunch")
        UserDefaults.standard.removeObject(forKey: "hideMainWindowOnLaunch")
        defer {
            if let previous { UserDefaults.standard.set(previous, forKey: "hideMainWindowOnLaunch") }
            else { UserDefaults.standard.removeObject(forKey: "hideMainWindowOnLaunch") }
        }
        retireAllMainWindows()

        delegate.applicationDidBecomeActive(
            Notification(name: NSApplication.didBecomeActiveNotification)
        )
        // 300ms 的延迟恢复 Task 也在这段窗口里跑完，避免它落到下一条用例里。
        settle(0.8)
        XCTAssertEqual(mainWindows.count, 1, "首次激活没有补出主窗口 ⇒ 登录首启白屏")
        XCTAssertTrue(mainWindows[0].isVisible)
    }

    /// 「启动时不打开主窗口」不许被首次激活那条路作废。
    func testFirstActivationDoesNotCreateWhenLaunchWindowSettingIsOff() {
        installProductFactory()
        defer { tearDownProductState() }
        let previous = UserDefaults.standard.object(forKey: "hideMainWindowOnLaunch")
        UserDefaults.standard.set(true, forKey: "hideMainWindowOnLaunch")
        defer {
            if let previous { UserDefaults.standard.set(previous, forKey: "hideMainWindowOnLaunch") }
            else { UserDefaults.standard.removeObject(forKey: "hideMainWindowOnLaunch") }
        }
        retireAllMainWindows()

        delegate.applicationDidBecomeActive(
            Notification(name: NSApplication.didBecomeActiveNotification)
        )
        settle()
        XCTAssertEqual(mainWindows.count, 0,
                       "设置关着启动窗口时，首次激活偷偷建了窗口 ⇒ 设置被作废")
    }

    /// 启动后 200ms 的 best-effort 只许 present，不许创建。
    func testStartupBestEffortDoesNotCreateAWindow() {
        installProductFactory()
        defer { tearDownProductState() }
        retireAllMainWindows()

        delegate.showExistingMainWindowIfAvailable()
        settle()
        XCTAssertEqual(mainWindows.count, 0,
                       "启动 best-effort 创建了窗口 ⇒ 「启动时不打开主窗口」被绕开")
    }

    /// 延迟恢复那条路（ApplicationShell 内 300ms）也要能创建；再保险一次。
    func testDeferredInitialRestoreCreatesTheWindow() {
        store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        let collapse = MainWindowCollapseController(persists: false)
        WindowManager.installMainWindowFactory {
            AppDelegate.makeMainWindow(historyStore: self.store, collapse: collapse)
        }
        defer { tearDownProductState() }
        let previous = UserDefaults.standard.object(forKey: "hideMainWindowOnLaunch")
        UserDefaults.standard.removeObject(forKey: "hideMainWindowOnLaunch")
        defer {
            if let previous { UserDefaults.standard.set(previous, forKey: "hideMainWindowOnLaunch") }
            else { UserDefaults.standard.removeObject(forKey: "hideMainWindowOnLaunch") }
        }
        let settings = HotKeySettings(action: .showMainWindow)
        let shell = ApplicationShell(
            showMainWindowHotKeySettings: settings,
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings()
        )
        shell.configure(historyStore: store)
        retireAllMainWindows()

        shell.applicationDidBecomeActive()
        settle(0.8)
        XCTAssertEqual(mainWindows.count, 1,
                       "300ms 延迟恢复没有补出窗口（旧版只试一次就永远不再试）")
        XCTAssertTrue(mainWindows[0].isVisible)
    }

    /// 菜单、热键、Dock reopen 必须汇到同一创建入口 —— 行为侧由上面几条判，这里钉接线。
    func testMenuHotKeyAndReopenAllReachTheSameCreatingEntry() throws {
        let app = try productSource("App.swift")
        let delegateSource = try productSource("Managers/AppDelegate.swift")
        let shellSource = try productSource("Managers/ApplicationShell.swift")
        XCTAssertTrue(app.contains("appDelegate.perform(command)"),
                      "MenuBarExtra 菜单没有走 AppDelegate.perform ⇒ 菜单不是产品入口")
        XCTAssertTrue(delegateSource.contains("name: .showMainWindowHotKeyPressed")
                      && delegateSource.contains("handleShowMainWindowHotKeyPressed")
                      && delegateSource.contains("shell.showMainWindow()"),
                      "热键通知没有汇到 shell.showMainWindow")
        XCTAssertTrue(delegateSource.contains("shell.handleReopen()"),
                      "Dock reopen 没有汇到 shell.handleReopen")
        XCTAssertTrue(shellSource.contains("func handleReopen()")
                      && shellSource.contains("WindowManager.showMainWindow(creatingIfNeeded: creatingIfNeeded"),
                      "handleReopen 与 showMainWindow 没有共用同一个创建入口")
    }

    private func productSource(_ relative: String) throws -> String {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/\(relative)")
        return try String(contentsOf: url, encoding: .utf8)
    }
}
