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

    /// R526：真实窗口会经 `WindowConfigurator` 改写全局 `WindowChromeMetrics.shared`；
    /// 不还原会让同一进程后面渲染的详情帧换掉顶部 inset（runner 的 Swift 全量里真的发生了）。
    private var savedDetailContentTopInset: CGFloat?

    private func setUpProduct(_ name: String = UUID().uuidString) {
        savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
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
        if let savedDetailContentTopInset {
            WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedDetailContentTopInset)
        }
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

    /// R525：折叠/展开要有**应用菜单 + 键盘**入口（之前只有状态菜单与界面）。
    /// 两个入口都走同一个 `perform(.toggleMainWindowCollapse)`，不是第二条触发路径。
    func testCollapseHasAnAppMenuEntryAndKeyboardShortcut() throws {
        XCTAssertEqual(AppCommand.toggleMainWindowCollapse.keyEquivalent, "\\")
        XCTAssertEqual(AppCommand.toggleMainWindowCollapse.keyModifiers, .command)
        XCTAssertEqual(MenuCommandShortcutPresentation.keyEquivalent(for: .toggleMainWindowCollapse), "\\")
        let commands = try productSource("Managers/ClipboardHistoryCommands.swift")
        XCTAssertTrue(commands.contains("appDelegate.perform(.toggleMainWindowCollapse)"),
                      "Window 菜单没有折叠/展开项")
        XCTAssertTrue(commands.contains(".keyboardShortcut(\"\\\\\", modifiers: .command)"),
                      "折叠/展开没有挂 ⌘\\")
    }

    /// R529：Window 菜单项标题随折叠态切换（旧值：两态都写静态「折叠/展开窗口」）。
    /// 同一 perform dispatch，标题只是呈现；折叠/展开各跑一次。
    func testWindowMenuTitleReflectsCollapseState() throws {
        XCTAssertEqual(MainWindowCollapsePolicy.menuTitle(collapsed: false), "折叠窗口")
        XCTAssertEqual(MainWindowCollapsePolicy.menuTitle(collapsed: true), "展开窗口")
        let commands = try productSource("Managers/ClipboardHistoryCommands.swift")
        XCTAssertTrue(commands.contains("MainWindowCollapsePolicy.menuTitle(collapsed: collapse.isCollapsed)"),
                      "Window 菜单项标题没有跟折叠状态走")
        XCTAssertTrue(commands.contains("appDelegate.perform(.toggleMainWindowCollapse)"),
                      "Window 菜单项没有走同一个折叠 dispatch")
        XCTAssertTrue(commands.contains("Toggle(isOn: Binding("),
                      "Window 菜单项不是可勾选的 Toggle ⇒ 看不出当前折叠态")
        XCTAssertTrue(commands.contains("get: { collapse.isCollapsed }"),
                      "Toggle 的勾选没有读当前折叠态")
        XCTAssertFalse(commands.contains("Button(AppCommand.toggleMainWindowCollapse.title)"),
                       "Window 菜单项又退回静态标题")
    }

    /// R530：折叠/展开不许把列表选区弄丢。选区住在 store（`selectedEntryIDs`），
    /// 折叠只换布局；这里从产品入口切两态并现读 store。
    func testSelectionSurvivesCollapseAndExpand() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard makeVisibleWindow() != nil else { return }
        store.add(
            ClipboardIntake.Entry(content: .text("选区保持夹具"), thumbnail: nil,
                                  sourceUTIs: ["public.utf8-plain-text"]),
            timestamp: Date(timeIntervalSince1970: 1_800_000_000)
        )
        guard let entry = store.entries.first else { return XCTFail("夹具没有条目") }
        store.perform(.selectOnly(entry))
        XCTAssertEqual(store.selectedEntryIDs, [entry.id])

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertEqual(store.selectedEntryIDs, [entry.id], "折叠把选区丢了")

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        XCTAssertEqual(store.selectedEntryIDs, [entry.id], "再展开把选区丢了")
    }

    /// R531：折叠后焦点不许留在已被移除的详情 text view 上。
    /// 旧值先现读：详情可聚焦 → 折叠 → 读 `window.firstResponder`；若它仍指向那棵已卸下的视图，
    /// 键盘输入会落进看不见的控件。负向证人（旧值已正确）时也保留这一条，防止以后回归。
    func testCollapseDoesNotLeaveFocusInRemovedDetail() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard makeVisibleWindow() != nil else { return }
        store.add(
            ClipboardIntake.Entry(content: .text("焦点夹具：折叠后这段正文不该再接收键盘输入。"),
                                  thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"]),
            timestamp: Date(timeIntervalSince1970: 1_800_000_100)
        )
        guard let entry = store.entries.first else { return XCTFail("夹具没有条目") }
        store.perform(.selectOnly(entry))
        settle(0.4)
        guard let window = mainWindows.first else { return XCTFail("没有主窗口") }
        guard let textView = firstDetailTextView(in: window.contentView) else {
            return XCTFail("详情里没有可聚焦的 text view ⇒ 焦点判据无从取证")
        }
        XCTAssertTrue(window.makeFirstResponder(textView), "详情 text view 拿不到焦点")
        XCTAssertTrue(window.firstResponder === textView, "焦点没有落在详情 text view 上")

        delegate.perform(.toggleMainWindowCollapse)
        settleTransition()
        let responder = window.firstResponder
        XCTAssertFalse(responder === textView, "折叠后焦点仍留在已移除的详情 text view 上")
        if let view = responder as? NSView {
            XCTAssertTrue(view.isDescendant(of: window.contentView!),
                          "折叠后焦点落在一个已脱离窗口的视图上：\(type(of: view))")
        }
    }

    private func firstDetailTextView(in view: NSView?) -> ChineseSelectableNSTextView? {
        guard let view else { return nil }
        if let text = view as? ChineseSelectableNSTextView { return text }
        for sub in view.subviews {
            if let found = firstDetailTextView(in: sub) { return found }
        }
        return nil
    }

    /// R532：折叠提示只在「折叠且未确认」时出现；确认后跨重启不再出现。
    /// 旧值：折叠窗只有箭头与工具提示，没有一行可见说明（帧 `main-collapsed` 无提示行）。
    func testCollapseHintShowsUntilAcknowledgedAndPersists() {
        let suite = "r532-collapse-hint-\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        controller = MainWindowCollapseController(defaults: defaults)
        XCTAssertFalse(controller.showsCollapseHint, "展开态不该有折叠提示")
        controller.setCollapsed(true)
        XCTAssertTrue(controller.showsCollapseHint, "第一次折叠没有提示")
        controller.acknowledgeCollapseHint()
        XCTAssertFalse(controller.showsCollapseHint, "确认后提示没有消失")
        XCTAssertTrue(defaults.bool(forKey: MainWindowCollapseController.hintAcknowledgedKey),
                      "确认没有持久化")
        controller.setCollapsed(false)
        controller.setCollapsed(true)
        XCTAssertFalse(controller.showsCollapseHint, "确认后再次折叠不该再提示")
        let restored = MainWindowCollapseController(defaults: defaults)
        XCTAssertFalse(restored.showsCollapseHint, "重启后已确认的提示又出现")
        defaults.removePersistentDomain(forName: suite)
    }

    /// R532：登录首启就是折叠态时，未确认仍有提示；确认过则不出现。
    func testCollapsedLaunchShowsHintOnlyWhenNotAcknowledged() {
        let suite = "r532-collapse-launch-\(UUID().uuidString)"
        let local = UserDefaults(suiteName: suite)!
        local.removePersistentDomain(forName: suite)
        local.set(true, forKey: MainWindowCollapseController.collapsedKey)
        let fresh = MainWindowCollapseController(defaults: local)
        XCTAssertTrue(fresh.showsCollapseHint, "折叠首启没有提示")
        fresh.acknowledgeCollapseHint()
        local.set(true, forKey: MainWindowCollapseController.collapsedKey)
        let restored = MainWindowCollapseController(defaults: local)
        XCTAssertFalse(restored.showsCollapseHint, "已确认的提示在重启后又出现")
        local.removePersistentDomain(forName: suite)
    }

    /// R532：提示从控制器 → 主窗口根视图 → ContentView → 侧栏的接线与文案。
    func testCollapseHintIsWiredFromControllerToSidebar() throws {
        XCTAssertEqual(CollapseHintPresentation.text, "窗口已折叠 · 点箭头或按 ⌘\\ 展开")
        XCTAssertEqual(CollapseHintPresentation.dismissTitle, "知道了")
        let app = try productSource("App.swift")
        XCTAssertTrue(app.contains("showsCollapseHint: collapse.showsCollapseHint"),
                      "主窗口根视图没有把提示状态传给 ContentView")
        XCTAssertTrue(app.contains("acknowledgeCollapseHint: { collapse.acknowledgeCollapseHint() }"),
                      "主窗口根视图没有把确认动作接到控制器")
        let content = try productSource("Views/ContentView.swift")
        XCTAssertTrue(content.contains("var showsCollapseHint: Bool = false"))
        XCTAssertTrue(content.contains("showsCollapseHint: showsCollapseHint"),
                      "ContentView 没有把提示状态传给侧栏")
        XCTAssertTrue(content.contains("acknowledgeCollapseHint: acknowledgeCollapseHint"),
                      "ContentView 没有把确认动作传给侧栏")
        let sidebar = try productSource("Views/HistorySidebarView.swift")
        XCTAssertTrue(sidebar.contains("if isCollapsed, showsCollapseHint {"),
                      "侧栏没有在折叠且未确认时渲染提示")
        XCTAssertTrue(sidebar.contains("Text(CollapseHintPresentation.text)"),
                      "侧栏没有用统一文案")
        XCTAssertTrue(sidebar.contains("acknowledgeCollapseHint()"),
                      "提示的「知道了」没有接确认动作")
    }

    /// R533：折叠提示的「知道了」必须是独立无障碍元素。
    /// 旧值：提示行用了 `.accessibilityElement(children: .combine)`，把可点按钮并进一段文字；
    /// 离屏窗口不建 AX 树（已知盲区），所以这里用产品源码段钉住「不许合并」这条契约。
    func testCollapseHintKeepsDismissButtonActionableForVoiceOver() throws {
        let sidebar = try productSource("Views/HistorySidebarView.swift")
        guard let start = sidebar.range(of: "private var collapseHintLine: some View {"),
              let end = sidebar.range(of: "private var headerRow: some View {",
                                      range: start.upperBound..<sidebar.endIndex) else {
            return XCTFail("折叠提示的源码段找不到 ⇒ 这条判据无从取证")
        }
        let hint = String(sidebar[start.lowerBound..<end.lowerBound])
        XCTAssertFalse(hint.contains(".accessibilityElement(children: .combine)"),
                       "折叠提示把可点的「知道了」合并进一个元素 ⇒ VoiceOver 拿不到按钮动作")
        XCTAssertTrue(hint.contains("Button(CollapseHintPresentation.dismissTitle)"),
                      "「知道了」不是独立按钮")
        XCTAssertTrue(hint.contains(".helpLabel(CollapseHintPresentation.dismissHelp)"),
                      "「知道了」没有读屏/悬停说明")
        XCTAssertTrue(hint.contains(".accessibilityHidden(true)"),
                      "装饰性的信息图标没有从读屏树里隐藏")
    }

    private func productSource(_ relative: String) throws -> String {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/\(relative)")
        return try String(contentsOf: url, encoding: .utf8)
    }
}
