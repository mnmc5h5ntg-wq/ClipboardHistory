import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R552：折叠/展开**一步切换**的证人（D-552「宁可不演也不卡顿」）。
///
/// 这一族以前的证人是离屏胶片（按 `foldProgress` 渲染中间态）与进程内逐拍的窗口宽序列 ——
/// 用户实测反馈说真机上是「点一下先卡住，然后窗口整块跳过去」，而这两把尺都看不见那件事：
/// 离屏通道压根没有窗口服务，进程内序列读的是模型值（一步写入之后模型就是终值，中间档只活在
/// 合成画面里）。所以本轮先把量尺换成真实窗口的屏上采样（`scripts/real_screen_fold_transition.py`
/// + `RealScreenFoldTransitionTests`），量完再决定留不留动画。
///
/// 屏上读数（同一台 MacBook Air，60fps 录像）：
/// - 旧版：主线程空窗 60ms（折叠）/106ms（展开）；屏上只在 50ms 内换 4 帧、17ms 内换 2 帧；
///   右缘一次跳 277pt（折叠）/322pt（展开）。
/// - 快照盖子：侧栏材质在 `cacheDisplay` 里是纯黑 ⇒ 撤。
/// - 几何交给窗口服务：屏上右缘只给 3 档（750→535→302）、展开 2 档 ⇒ 没有中间帧可演，撤。
///
/// 于是这一族判据钉的是"可数的形状"：一次切换 = 布局 1 次、几何 1 次、`minSize` 1 次、
/// 中间进度 0 次；时长恒为 0（这一格由 `testFoldAnimationDurationIsPinnedToZero` 钉住，
/// 把它改回 0.20 的提交会当场红）。
@MainActor
final class MainWindowFoldMotionTests: XCTestCase {
    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!
    private var savedReduceOverride: Bool?
    private var savedAnimationsEnabled: Bool?
    /// R526：真实窗口会经 `WindowConfigurator` 改写全局 `WindowChromeMetrics.shared`；
    /// 不还原会让同一进程后面渲染的详情帧换掉顶部 inset（runner 的 Swift 全量里真的发生了）。
    private var savedDetailContentTopInset: CGFloat?

    private func setUpProduct(_ name: String = UUID().uuidString) {
        savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        defaults = UserDefaults(suiteName: "r552-fold-\(name)")!
        defaults.removePersistentDomain(forName: "r552-fold-\(name)")
        savedReduceOverride = MotionCatalog.overrideReduceMotion
        savedAnimationsEnabled = MotionCatalog.animationsEnabled
        MotionCatalog.overrideReduceMotion = false
        MotionCatalog.animationsEnabled = true
        controller = MainWindowCollapseController(defaults: defaults)
        store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        for index in 0..<4 {
            store.add(
                ClipboardIntake.Entry(
                    content: .text("折叠一步切换取证条目 \(index) abcdefghijklmnop"),
                    thumbnail: nil,
                    sourceUTIs: ["public.utf8-plain-text"]
                ),
                timestamp: Date(timeIntervalSince1970: TimeInterval(1_800_000_000 + index * 60))
            )
        }
        delegate = AppDelegate(historyStore: store, collapseController: controller)
        NSApplication.shared.setActivationPolicy(.regular)
    }

    private func tearDownProduct() {
        if let savedReduceOverride { MotionCatalog.overrideReduceMotion = savedReduceOverride }
        else { MotionCatalog.overrideReduceMotion = nil }
        if let savedAnimationsEnabled { MotionCatalog.animationsEnabled = savedAnimationsEnabled }
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

    private func makeWindow(width: CGFloat = 750) -> NSWindow? {
        WindowManager.showMainWindow(creatingIfNeeded: true)
        settle(0.12)
        guard let window = mainWindows.first else {
            XCTFail("没有建出主窗口")
            return nil
        }
        var frame = window.frame
        frame.size.width = width
        window.setFrame(frame, display: false)
        settle()
        return window
    }

    /// 折叠：`perform` 返回的那一拍就必须已经是终态 —— 状态、进度、模型宽、最小宽四样一起到位。
    func testCollapseIsOneStepWithNoIntermediateState() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }

        controller.resetTransitionCountersForTesting()
        delegate.perform(.toggleMainWindowCollapse)
        settle(0.05)

        XCTAssertFalse(controller.isTransitioning, "一步切换不该有『还在过渡』这个状态")
        XCTAssertTrue(controller.isCollapsed, "状态没跟着这一步走")
        XCTAssertEqual(controller.foldProgress, 1, accuracy: 0.001)
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0, "模型宽没有一步到折叠档")
        XCTAssertEqual(window.minSize.width, 360, accuracy: 0.5, "最小宽没有一步落到折叠档")
        XCTAssertEqual(controller.switches, 1, "一次点击切了不止一次布局")
        XCTAssertEqual(controller.geometryWrites, 1, "一次点击写了一次以上几何（旧版是每拍一次）")
        XCTAssertEqual(controller.minSizeWrites, 1, "一次点击写了一次以上 minSize")
        XCTAssertEqual(controller.publishedIntermediates, 0, "发布了中间进度 ⇒ 整棵树会被逐拍重排")
        CaptureReadings.emit("FOLD_ONE_STEP collapse 切换=\(controller.switches)"
              + " 几何=\(controller.geometryWrites) minSize=\(controller.minSizeWrites)"
              + " 中间态=\(controller.publishedIntermediates)"
              + " 宽=\(Int(window.frame.width)) 最小=\(Int(window.minSize.width))")
    }

    /// 展开：同样一步到位，回到展开档的宽与最小宽。
    func testExpandIsOneStepBackToExpandedGeometry() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }
        delegate.perform(.toggleMainWindowCollapse)
        settle(0.05)
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0)

        controller.resetTransitionCountersForTesting()
        delegate.perform(.toggleMainWindowCollapse)
        settle(0.05)

        XCTAssertFalse(controller.isCollapsed)
        XCTAssertFalse(controller.isTransitioning)
        XCTAssertEqual(window.frame.width, 750, accuracy: 1.0, "展开没有一步回到 750")
        XCTAssertEqual(window.minSize.width, 600, accuracy: 0.5, "展开档最小宽没落下")
        XCTAssertEqual(controller.switches, 1, "一次点击切了不止一次布局")
        XCTAssertEqual(controller.geometryWrites, 1, "一次点击写了一次以上几何")
        XCTAssertEqual(controller.minSizeWrites, 1, "一次点击写了一次以上 minSize")
        XCTAssertEqual(controller.publishedIntermediates, 0)
        CaptureReadings.emit("FOLD_ONE_STEP expand 切换=\(controller.switches)"
              + " 几何=\(controller.geometryWrites) minSize=\(controller.minSizeWrites)"
              + " 宽=\(Int(window.frame.width)) 最小=\(Int(window.minSize.width))")
    }

    /// 进度这一辈子只许出现 0 与 1 两档（旧版每拍发布一次，等于每拍重排整棵树）。
    func testFoldProgressOnlyEverTakesTheTwoEndpoints() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }
        for _ in 0..<4 {
            delegate.perform(.toggleMainWindowCollapse)
            settle(0.05)
        }
        let roster = Set(controller.progressRosterForTesting.map { $0.rounded() })
        XCTAssertEqual(roster, [0, 1], "发布过中间进度：\(controller.progressRosterForTesting)")
        XCTAssertEqual(controller.publishedIntermediates, 0)
        XCTAssertEqual(window.frame.width, 750, accuracy: 1.0, "四次往返没回到展开档")
        CaptureReadings.emit("FOLD_PROGRESS_ROSTER 档数=\(roster.count) 值=\(roster.sorted())"
              + " 切换=\(controller.switches) 中间态=\(controller.publishedIntermediates)")
    }

    /// 同档重复调用必须是空操作：不写几何、不写 minSize、不切布局。
    func testSettingTheSameStateAgainWritesNothing() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }
        controller.resetTransitionCountersForTesting()
        controller.setCollapsed(true, window: window)
        XCTAssertEqual(controller.switches, 1)
        controller.resetTransitionCountersForTesting()
        controller.setCollapsed(true, window: window)
        XCTAssertEqual(controller.switches, 0, "同档重复调用又切了一次布局")
        XCTAssertEqual(controller.geometryWrites, 0, "同档重复调用还会写几何")
        XCTAssertEqual(controller.minSizeWrites, 0)
        CaptureReadings.emit("FOLD_NO_OP 重复调用 切换=\(controller.switches) 几何=\(controller.geometryWrites)")
    }

    /// D-552 的那颗钉子：时长恒为 0。把它改回 `.windowFold` 的 0.20 会让这条红。
    func testFoldAnimationDurationIsPinnedToZero() {
        XCTAssertEqual(MainWindowCollapsePolicy.animationDuration(reduceMotion: false), 0, accuracy: 0.001,
                       "折叠又有了时长 ⇒ 一步切换的决定（D-552）被推翻，但屏上中间帧那两格还没解决")
        XCTAssertEqual(MainWindowCollapsePolicy.animationDuration(reduceMotion: true), 0, accuracy: 0.001)
    }

    /// reduce-motion 与普通路径必须**完全同形**：时长两边都是 0，走的也是同一条一步切换。
    /// （显式把窗口传进去：SwiftPM 并行跑用例，`WindowManager.currentMainWindow` 是全局弱引用，
    /// 靠它兜底会读到别的用例那扇窗。）
    func testReduceMotionPathIsTheSameOneStep() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        MotionCatalog.overrideReduceMotion = true
        guard let window = makeWindow(width: 750) else { return }
        XCTAssertEqual(MainWindowCollapsePolicy.animationDuration(reduceMotion: true),
                       MainWindowCollapsePolicy.animationDuration(reduceMotion: false),
                       "reduce 与普通路径拿到了不同的时长")

        controller.resetTransitionCountersForTesting()
        controller.setCollapsed(true, window: window)
        settle(0.05)
        XCTAssertFalse(controller.isTransitioning)
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0)
        XCTAssertEqual(controller.foldProgress, 1, accuracy: 0.001)
        XCTAssertEqual(window.minSize.width, 360, accuracy: 0.5)
        XCTAssertEqual(controller.switches, 1)
        XCTAssertEqual(controller.geometryWrites, 1)
        CaptureReadings.emit("FOLD_REDUCE instant width=\(Int(window.frame.width))"
              + " 切换=\(controller.switches) 几何=\(controller.geometryWrites)")
    }

    /// 政策真值表：两档宽/最小宽、菜单标题、detail 可见性 —— 这些与"演不演"无关，继续钉住。
    func testCollapsePolicyGeometryTruthTable() {
        XCTAssertEqual(MainWindowCollapsePolicy.collapsedWidthDefault, 420, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.expandedWidthDefault, 750, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.minWidth(collapsed: true), 360, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.minWidth(collapsed: false), 600, accuracy: 0.001)
        XCTAssertFalse(MainWindowCollapsePolicy.detailVisible(collapsed: true))
        XCTAssertEqual(MainWindowCollapsePolicy.menuTitle(collapsed: true), "展开窗口")
        XCTAssertEqual(MainWindowCollapsePolicy.menuTitle(collapsed: false), "折叠窗口")
        XCTAssertEqual(MainWindowCollapsePolicy.targetWidth(collapsed: true,
                                                            expandedWidth: 750,
                                                            collapsedWidth: 420,
                                                            visibleWidth: 1000), 420, accuracy: 0.001)
        // 屏幕比目标档还窄时屏幕优先（窗口不许跑出屏）
        XCTAssertEqual(MainWindowCollapsePolicy.targetWidth(collapsed: false,
                                                            expandedWidth: 750,
                                                            collapsedWidth: 420,
                                                            visibleWidth: 700), 700, accuracy: 0.001)
    }
}
