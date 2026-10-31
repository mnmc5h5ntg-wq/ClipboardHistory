import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R523：折叠/展开主窗口的**静态骨架**。宽度、最小宽、持久化、用户 resize 记忆、屏幕 clamp
/// 都从产品入口（`delegate.perform(.toggleMainWindowCollapse)` / 主窗口创建）现读；
/// 纯函数策略同一套真值表直接判。过渡动画与胶片证人留给 R524。
@MainActor
final class MainWindowCollapseTests: XCTestCase {
    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!

    private func setUpProduct(_ name: String = UUID().uuidString) {
        defaults = UserDefaults(suiteName: "r523-collapse-\(name)")!
        defaults.removePersistentDomain(forName: "r523-collapse-\(name)")
        controller = MainWindowCollapseController(defaults: defaults)
        store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        delegate = AppDelegate(historyStore: store, collapseController: controller)
        NSApplication.shared.setActivationPolicy(.regular)
    }

    private func tearDownProduct() {
        retireAllMainWindows()
        WindowManager.uninstallMainWindowFactoryForTesting()
        delegate = nil
        store = nil
        controller = nil
        defaults = nil
    }

    private var mainWindows: [NSWindow] {
        NSApplication.shared.windows.filter { WindowManager.isAppContentWindow($0) }
    }

    private func retireAllMainWindows() {
        for window in mainWindows {
            window.delegate = nil
            window.identifier = NSUserInterfaceItemIdentifier("RetiredAppWindowForTesting")
            window.orderOut(nil)
        }
        WindowManager.forgetMainWindowForTesting()
        settle()
    }

    private func settle(_ seconds: TimeInterval = 0.08) {
        RunLoop.current.run(until: Date().addingTimeInterval(seconds))
    }

    /// R524：折叠是 0.20s 的逐帧过渡；判定"落定"要等控制器真的停表，不能拍脑袋睡一个数。
    private func settleTransition(_ timeout: TimeInterval = 1.0) {
        let deadline = Date().addingTimeInterval(timeout)
        while controller.isTransitioning, Date() < deadline {
            RunLoop.current.run(until: Date().addingTimeInterval(0.01))
        }
        XCTAssertFalse(controller.isTransitioning, "过渡在 \(timeout)s 内没有收尾 ⇒ 留下半折状态")
        settle(0.03)
    }

    private func makeVisibleWindow() -> NSWindow? {
        WindowManager.showMainWindow()
        settle(0.12)
        let windows = mainWindows
        XCTAssertEqual(windows.count, 1, "没有建出唯一主窗口")
        return windows.first
    }

    private func setWidth(_ width: CGFloat, of window: NSWindow) {
        var frame = window.frame
        frame.size.width = width
        window.setFrame(frame, display: false)
        settle()
    }

    func testCollapseUsesItsOwnWidthAndExpandRestoresResizedWidth() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeVisibleWindow() else { return }
        setWidth(800, of: window)
        let heightBefore = window.frame.height
        let leftBefore = window.frame.origin.x
        let topBefore = window.frame.maxY

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertTrue(controller.isCollapsed)
        XCTAssertEqual(window.frame.width, MainWindowCollapsePolicy.collapsedWidthDefault, accuracy: 1.0,
                       "折叠宽不是单独定义的 420pt")
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0,
                       "折叠宽不许沿用侧栏的 268pt")
        XCTAssertEqual(window.minSize.width, MainWindowCollapsePolicy.collapsedMinWidth, accuracy: 0.5)
        XCTAssertEqual(window.frame.height, heightBefore, accuracy: 0.5, "折叠改了高度")
        XCTAssertEqual(window.frame.origin.x, leftBefore, accuracy: 1.0, "折叠没有保持左上角（x）")
        XCTAssertEqual(window.frame.maxY, topBefore, accuracy: 1.0, "折叠没有保持左上角（top）")

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertFalse(controller.isCollapsed)
        XCTAssertEqual(window.frame.width, 800, accuracy: 1.0,
                       "再展开没有回到用户最近一次 resize 的 800pt")
        XCTAssertEqual(window.minSize.width, MainWindowCollapsePolicy.expandedMinWidth, accuracy: 0.5)
    }

    func testUserResizeInEachStateIsRememberedForNextToggle() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeVisibleWindow() else { return }
        setWidth(777, of: window)
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0)

        setWidth(450, of: window)
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertEqual(window.frame.width, 777, accuracy: 1.0, "展开宽没记住用户 resize 的 777")

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertEqual(window.frame.width, 450, accuracy: 1.0, "折叠宽没记住用户 resize 的 450")
    }

    func testReduceMotionDurationIsZero() {
        XCTAssertEqual(MainWindowCollapsePolicy.animationDuration(reduceMotion: true), 0,
                       "reduce 下不是 0 时长 ⇒ 会留下动画尾巴")
        XCTAssertGreaterThan(MainWindowCollapsePolicy.animationDuration(reduceMotion: false), 0)
    }

    func testPersistenceRoundTripKeepsStateAndBothWidths() {
        setUpProduct("roundtrip")
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeVisibleWindow() else { return }
        setWidth(812, of: window)
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        setWidth(455, of: window)
        // 宽度是在**切换那一刻**记回正要离开的那一档：先展开（记下 455），再折回来。
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertTrue(controller.isCollapsed)

        let restored = MainWindowCollapseController(defaults: defaults)
        XCTAssertTrue(restored.isCollapsed, "折叠状态没有持久化")
        XCTAssertEqual(restored.expandedWidth, 812, accuracy: 1.0, "展开宽没有持久化")
        XCTAssertEqual(restored.collapsedWidth, 455, accuracy: 1.0, "折叠宽没有持久化")

        restored.setCollapsed(false)
        let fresh = MainWindowCollapseController(defaults: defaults)
        XCTAssertFalse(fresh.isCollapsed, "展开状态没有持久化")
    }

    func testCollapsedWindowClampsToVisibleScreenAndKeepsTopLeft() {
        let visible = CGRect(x: 100, y: 50, width: 380, height: 600)
        let width = MainWindowCollapsePolicy.targetWidth(collapsed: true,
                                                         expandedWidth: 800,
                                                         collapsedWidth: 500,
                                                         visibleWidth: visible.width)
        XCTAssertEqual(width, 380, accuracy: 0.5, "屏幕放不下时没有收窄到可见宽")
        XCTAssertEqual(MainWindowCollapsePolicy.originX(clampingX: 200, width: width, visibleFrame: visible),
                       100, accuracy: 0.5, "收窄后右侧跑出屏幕")
        XCTAssertEqual(MainWindowCollapsePolicy.originY(clampingTop: 1200, height: 560, visibleFrame: visible),
                       90, accuracy: 0.5, "顶部跑出屏幕（没有按 top 夹回）")
    }

    func testDetailIsNotRenderedWhenCollapsed() throws {
        XCTAssertTrue(MainWindowCollapsePolicy.detailVisible(collapsed: false))
        XCTAssertFalse(MainWindowCollapsePolicy.detailVisible(collapsed: true))
        let source = try productSource("Views/ContentView.swift")
        guard let collapsedStart = source.range(of: "private var collapsedLayout: some View {"),
              let collapsedEnd = source.range(of: "/// R524",
                                              range: collapsedStart.upperBound..<source.endIndex) else {
            return XCTFail("ContentView 没有折叠布局这一段")
        }
        let collapsedBlock = String(source[collapsedStart.lowerBound..<collapsedEnd.lowerBound])
        XCTAssertFalse(collapsedBlock.contains("DetailView(historyStore:"),
                       "折叠布局里仍然渲染了 detail")
        XCTAssertTrue(collapsedBlock.contains("HistorySidebarView"),
                      "折叠布局没有列表 ⇒ 折叠后是一块空白")
        XCTAssertTrue(source.contains("if progress < 1 || !isCollapsed"),
                      "落定折叠时展开树必须整棵不挂载（否则 detail 还在）")
    }

    func testDoubleClickTitleAndTheVisibleButtonShareTheSameAction() throws {
        let source = try productSource("Views/HistorySidebarView.swift")
        XCTAssertTrue(source.contains(".onTapGesture(count: 2) { toggleCollapse() }"),
                      "标题双击没有接到折叠 action")
        XCTAssertTrue(source.contains("Button {\n                toggleCollapse()"),
                      "可见的折叠/展开按钮没有接到同一个 action")
        XCTAssertTrue(source.contains(".helpLabel(isCollapsed ? \"展开窗口\" : \"折叠窗口\")"),
                      "可见按钮没有 .helpLabel（发现性不能只靠双击）")
        XCTAssertTrue(source.contains("isCollapsed ? \"chevron.right\" : \"chevron.left\""),
                      "按钮的折叠/展开状态没有可见符号")
    }

    func testCreatedWindowAppliesPersistedCollapsedState() {
        defaults = UserDefaults(suiteName: "r523-collapse-login")!
        defaults.removePersistentDomain(forName: "r523-collapse-login")
        defaults.set(true, forKey: MainWindowCollapseController.collapsedKey)
        defaults.set(430.0, forKey: MainWindowCollapseController.collapsedWidthKey)
        controller = MainWindowCollapseController(defaults: defaults)
        store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        delegate = AppDelegate(historyStore: store, collapseController: controller)
        defer { tearDownProduct() }
        retireAllMainWindows()

        guard let window = makeVisibleWindow() else { return }
        XCTAssertTrue(controller.isCollapsed)
        XCTAssertEqual(window.frame.width, 430, accuracy: 1.0,
                       "登录首启处于折叠态时没有按持久化的折叠宽建窗")
        XCTAssertEqual(window.minSize.width, MainWindowCollapsePolicy.collapsedMinWidth, accuracy: 0.5)
    }

    func testMenuCommandRouteTogglesCollapse() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeVisibleWindow() else { return }
        XCTAssertTrue(AppCommandCatalog.menuBarCommands.contains(.toggleMainWindowCollapse),
                      "菜单里没有「折叠/展开窗口」这一项")
        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertTrue(controller.isCollapsed)
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0)
    }

    private func productSource(_ relative: String) throws -> String {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/\(relative)")
        return try String(contentsOf: url, encoding: .utf8)
    }
}
