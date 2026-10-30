import AppKit
import Combine
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class WindowChromeLayoutTests: XCTestCase {
    func testTrafficLightOriginUsesNativeCornerInset() {
        let origin = WindowChromeLayout.trafficLightOrigin(titlebarHeight: 52, buttonHeight: 14)

        XCTAssertEqual(origin.x, 21)
        XCTAssertEqual(origin.y, 19)
    }

    func testTrafficLightOriginDoesNotStickToWindowCornerBeforeTitlebarSettles() {
        let origin = WindowChromeLayout.trafficLightOrigin(titlebarHeight: 20, buttonHeight: 14)

        XCTAssertEqual(origin.x, 21)
        XCTAssertEqual(origin.y, WindowChromeLayout.trafficLightMinimumBottomInset)
    }

    // MARK: - 灯带底边与详情头部的让位

    /// 用户报的缺陷：详情头部那一行和左上角三个按钮叠在一起（侧栏收起时）。
    /// 这里钉的是"让位量确实按实测的灯带底边算"，而不是抄了个看着够大的数。
    func testTrafficLightBandBottomMatchesMeasuredTitlebarHeights() {
        // 带工具栏 52pt（产品真实窗口实测值）与不带工具栏 32pt（探针实测值）。
        XCTAssertEqual(WindowChromeLayout.trafficLightBandBottom(titlebarHeight: 52, buttonHeight: 14), 33)
        XCTAssertEqual(WindowChromeLayout.trafficLightBandBottom(titlebarHeight: 32, buttonHeight: 14), 26)
    }

    func testDetailHeaderClearsTheTrafficLightBandAcrossTitlebarHeights() {
        // 扫描而不是只测两个点：`alignTrafficLights` 里那个 `max(..., 6)` 让底边随容器高变化，
        // 只测一个高度会得到一个"在这台机器上刚好够"的假结论（本仓库同类教训不止一次）。
        for titlebarHeight in stride(from: CGFloat(24), through: 56, by: 2) {
            let band = WindowChromeLayout.trafficLightBandBottom(titlebarHeight: titlebarHeight, buttonHeight: 14)
            let inset = WindowChromeLayout.detailContentTopInset(titlebarHeight: titlebarHeight, buttonHeight: 14)
            XCTAssertGreaterThan(inset, band,
                                 "标题栏 \(titlebarHeight)pt 时头部（\(inset)pt）没躲开灯带底边（\(band)pt）")
        }
    }

    func testFallbackInsetCoversTheRealWindowBeforeItIsMeasured() {
        // 首帧与离屏夹具拿不到窗口，这时用的是兜底值 —— 它必须也已经够。
        XCTAssertGreaterThanOrEqual(
            WindowChromeLayout.detailContentTopInsetFallback,
            WindowChromeLayout.trafficLightBandBottom(titlebarHeight: 52, buttonHeight: 14),
            "兜底值小于真实窗口的灯带底边，第一帧就会压在按钮上"
        )
    }

    func testMetricsPublishesWhatTheWindowActuallyNeedsAndIgnoresRepeatValues() {
        // 用独立实例：这条测的是发布语义，不该顺手改掉产品单例。
        let metric = WindowChromeMetrics()
        let observed = MetricsRecorder(metric: metric)
        defer { observed.stop() }

        metric.noteTrafficLights(titlebarHeight: 52, buttonHeight: 14)
        XCTAssertEqual(metric.detailContentTopInset, 35)
        let emissionsAfterFirst = observed.count
        XCTAssertGreaterThan(emissionsAfterFirst, 0, "第一次设置没发布，视图不会跟着动")

        // 同一个值再报一次不许发布：这个方法在每次 resize / 每次成为 key 时都会被调，
        // 无脑赋值会让详情区跟着重排。
        metric.noteTrafficLights(titlebarHeight: 52, buttonHeight: 14)
        XCTAssertEqual(observed.count, emissionsAfterFirst, "重复值也发布了")

        metric.noteTrafficLights(titlebarHeight: 32, buttonHeight: 14)
        XCTAssertEqual(metric.detailContentTopInset, 28)
        XCTAssertEqual(observed.count, emissionsAfterFirst + 1, "换了值却没发布")

        // 兜底初值本身也要够（首帧与离屏夹具用的就是它）
        XCTAssertEqual(WindowChromeMetrics().detailContentTopInset,
                       WindowChromeLayout.detailContentTopInsetFallback)
    }

    /// 整条链的端到端：真窗口（带工具栏）+ 产品自己的 `WindowConfigurator`
    /// → 发布的让位量必须 ≥ 从那个窗口里**量出来**的灯带底边。
    /// 只测纯函数的话，"摆按钮那段改了、发布那段没跟着改"这种分叉测不到。
    func testConfiguredWindowPublishesAtLeastTheMeasuredBand() throws {
        _ = NSApplication.shared
        // 这条用例会写产品单例，所以进入时记下原值、离开时还原。
        // 为什么写在测试体内而不是 `tearDown`：`tearDown` 是非隔离上下文，
        // 够不到 MainActor 上的单例 —— CI 的 Swift 6.1.2 直接拒绝编译，
        // 本机 6.2 却放行（"本地绿、CI 红"的老一族，这次栽在测试自己的隔离上）。
        let savedInset = WindowChromeMetrics.shared.detailContentTopInset
        defer { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedInset) }

        // 先把单例摆成一个**不可能来自真实窗口**的假值，再建窗口。
        // 顺序反了就测不到接线：上一版把假值摆在窗口配置之后，于是"永远等不到覆盖"，
        // 这条判据在没变异的代码上也是红的 —— 判据要"平时绿、变异红"，两头都得验。
        let sentinel: CGFloat = 16
        WindowChromeMetrics.shared.noteTrafficLights(titlebarHeight: 20, buttonHeight: 14)
        XCTAssertEqual(WindowChromeMetrics.shared.detailContentTopInset, sentinel,
                       "夹具前提：这个假值要能摆进去")

        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 750, height: 560),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        defer { window.orderOut(nil) }
        window.titlebarAppearsTransparent = true
        window.toolbar = NSToolbar(identifier: "chrome-probe")
        let host = NSHostingView(rootView: AnyView(WindowConfigurator().frame(width: 1, height: 1)))
        host.frame = NSRect(x: 0, y: 0, width: 750, height: 560)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)

        guard let contentView = window.contentView else { return XCTFail("窗口没有 contentView") }
        let deadline = Date().addingTimeInterval(3.0)
        while Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            if window.standardWindowButton(.closeButton)?.superview != nil { break }
        }
        let closeButton = try XCTUnwrap(window.standardWindowButton(.closeButton), "窗口没有关闭按钮")
        let titlebar = try XCTUnwrap(closeButton.superview, "按钮不在标题栏容器里")

        // 按钮底边距窗口顶多少：`to: nil` 给的是窗口基坐标（原点在左下），
        // 而 `.fullSizeContentView` 下 contentView 铺满整个窗口，所以 顶距 = 高 − 底边 y。
        let buttonFrameInWindow = titlebar.convert(closeButton.frame, to: nil)
        let bandBottomFromWindowTop = contentView.bounds.height - buttonFrameInWindow.minY
        XCTAssertGreaterThan(bandBottomFromWindowTop, 0, "量不到按钮带，这条判据没有内容")
        print("CHROME 标题栏容器高=\(titlebar.bounds.height) 按钮高=\(closeButton.frame.height) "
            + "灯带底边距窗口顶=\(bandBottomFromWindowTop)pt")

        // 等的不是"按钮出现了"，而是"配置过程真的把几何发布出来了"。
        // 只断言 `published ≥ 实测底边` 是不够的：兜底初值 35 本来就 ≥ 33，
        // 把发布调用整段删掉它照样绿（这一版变异对照就是这么抓到的）。
        XCTAssertLessThan(sentinel, bandBottomFromWindowTop)

        let wireDeadline = Date().addingTimeInterval(3.0)
        while Date() < wireDeadline, WindowChromeMetrics.shared.detailContentTopInset == sentinel {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        let published = WindowChromeMetrics.shared.detailContentTopInset
        XCTAssertNotEqual(published, sentinel,
                          "窗口配置完了却没发布几何 —— 详情头部拿不到真实灯带位置，只能靠兜底值")
        XCTAssertGreaterThanOrEqual(published, bandBottomFromWindowTop,
                                    "发布的让位量 \(published) 小于实测灯带底边 \(bandBottomFromWindowTop)"
                                    + " —— 详情头部会压在交通灯上")
    }

    /// R502：主窗口标题栏的标题策略。真窗口帧里标题栏是空的（应用名在侧栏标题里），
    /// 而 title 字符串仍要保留给 Mission Control/读屏。把「标题不画」写成显式契约：
    /// 一旦系统默认把 title 画出来，它会与详情头部撞在一起（R502 实拍：title 覆盖来源图标上方）。
    func testMainWindowHidesItsTitlebarTitleButKeepsTheName() throws {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 750, height: 560),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        defer { window.orderOut(nil) }
        window.titlebarAppearsTransparent = true
        let host = NSHostingView(rootView: AnyView(WindowConfigurator().frame(width: 1, height: 1)))
        host.frame = NSRect(x: 0, y: 0, width: 750, height: 560)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        let deadline = Date().addingTimeInterval(3.0)
        while Date() < deadline, window.titleVisibility != .hidden {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertEqual(window.titleVisibility, .hidden,
                       "主窗口是自定义标题栏：标题栏里的 title 必须显式隐藏（否则会压到详情头部）")
        XCTAssertEqual(window.title, "时间剪史",
                       "窗口名要保留给 Mission Control/读屏")
        if #available(macOS 11.0, *) {
            XCTAssertEqual(window.titlebarSeparatorStyle, .none,
                           "透明自定义标题栏不再画系统分隔线（真窗口里它是一条孤立亮线）")
        }
    }

    func testDetailViewConsumesThePublishedInset() throws {
        let source = try productSource(named: "Views/DetailView.swift")
        XCTAssertTrue(source.contains(".padding(.top, chrome.detailContentTopInset)"),
                      "详情头部没把让位量接上 —— 灯带一变化它就不跟着动")
        XCTAssertTrue(source.contains("@ObservedObject private var chrome: WindowChromeMetrics"),
                      "没观察窗口的几何变化：首帧之后窗口变了，头部也不会跟着让")
    }

    // MARK: - 侧栏不可收起（系统设置那样永远在）

    /// A/B 两半都要：
    /// ① 不挂 `WindowConfigurator` 的真窗口里，侧栏列项**确实可以折叠**，
    ///    而且我们的查找函数找得到它 —— 这一半同时是"探针没瞎"的证明；
    /// ② 挂上之后必须变成不可折叠。
    /// 只断言 ②，"根本没找到那一列"和"SwiftUI 默认就不让折叠"两种情况都会伪装成通过。
    ///
    /// 刻意用同步 `throws` 而不是 `async throws`：等落地靠的是在主线程上转 `RunLoop`，
    /// 而 `RunLoop.run(until:)` 标了 `noasync` —— 异步签名的用例里转不动 runloop，
    /// 只能 `await Task.sleep` 把主线程让出去，配置回调恰恰在同一个 runloop 上跑。
    func testSidebarIsPinnedVisibleOnlyByTheProductConfigurator() throws {
        // 真实窗口的配置过程会写 `WindowChromeMetrics.shared`，进出都要保住离屏夹具的初值。
        let savedInset = WindowChromeMetrics.shared.detailContentTopInset
        defer { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedInset) }

        let unpinned = try makeContentWindow(configured: false)
        defer { unpinned.orderOut(nil) }
        let plainSidebar = try XCTUnwrap(
            sidebarItem(of: unpinned),
            "找不到承载侧栏的分栏列项 —— 探针失效，这条判据没有内容"
        )
        XCTAssertTrue(plainSidebar.canCollapse,
                      "SwiftUI 默认就不允许折叠？那这个修复和这条判据都是空的，要改写")

        let pinned = try makeContentWindow(configured: true)
        defer { pinned.orderOut(nil) }
        let pinnedSidebar = try XCTUnwrap(sidebarItem(of: pinned), "配置后反而找不到列项了")

        // 钉的动作在配置回调与若干次延迟补做里发生，等它落地而不是假设它同步完成。
        let deadline = Date().addingTimeInterval(2.5)
        while pinnedSidebar.canCollapse, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertFalse(pinnedSidebar.canCollapse,
                       "配置完侧栏仍可折叠：拖分隔条还是能把侧栏拖没，遮挡那条缺陷就还在")
        // 钉的必须是侧栏那一列，而且必须是视图实际在用的那个对象 ——
        // 若 SwiftUI 在配置过程中换过列项，`pinSidebarVisible` 找到的就是另一个壳，
        // 上面那条断言会因为拿到同一个旧对象而假绿。
        XCTAssertEqual(pinnedSidebar.behavior, .sidebar,
                       "钉住的不是 behavior == .sidebar 的那一列（详情列被钉了，侧栏还能拖没）")
        XCTAssertIdentical(pinnedSidebar, try XCTUnwrap(sidebarItem(of: pinned), "配置后列项消失了"),
                           "配置前后不是同一个列项对象：判据测的可能是个已经废弃的壳")
    }

    /// 旧存档那一半：`NavigationSplitView` 会把列的可见性存下来，所以**收起过侧栏的机器
    /// 装上新版后第一帧可能就是折叠的**。只关 `canCollapse` 会得到"以后不能再收，
    /// 但这次还是空的" —— 对报这条缺陷的用户来说等于没修。
    ///
    /// 踩过的坑：第一版是"未配置窗口 → 折叠 → 换根视图成配置过的"，绿了。
    /// 加了一条 `XCTAssertIdentical(旧列项, 现查到的列项)` 才发现**换根视图会把列项重建**，
    /// 于是判据盯的是个已经废弃的壳 —— 它变 false 不代表产品展开了任何东西。
    /// 现在盯的是活对象，触发走的是真事件（窗口缩放 → 产品自己装的 delegate）。
    func testAlreadyCollapsedSidebarIsExpandedByTheProductWindowDelegate() throws {
        let savedInset = WindowChromeMetrics.shared.detailContentTopInset
        defer { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedInset) }
        let window = try makeContentWindow(configured: true)
        defer { window.orderOut(nil) }
        let sidebar = try XCTUnwrap(sidebarItem(of: window), "找不到侧栏列项，探针失效")
        XCTAssertEqual(sidebar.behavior, .sidebar, "找到的不是侧栏那一列")

        // 先等配置器把这一列钉住。
        var deadline = Date().addingTimeInterval(2.5)
        while sidebar.canCollapse, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertFalse(sidebar.canCollapse, "配置器没钉住侧栏，后半条判据无从谈起")

        // 摆"旧存档"：把这一列恢复到 SwiftUI 刚建出来、带着折叠存档时的样子
        // （可折叠 + 已折叠）。不这么做就没法在钉过之后造出"打开时就是收起的"，
        // 因为 `canCollapse == false` 时 AppKit 会直接拒绝折叠。
        sidebar.canCollapse = true
        sidebar.isCollapsed = true
        XCTAssertTrue(sidebar.canCollapse, "夹具前提：这一列得先回到可折叠，否则造不出旧存档")
        XCTAssertTrue(sidebar.isCollapsed, "夹具前提：折叠状态摆不进去，这条判据没有内容")

        // 触发产品自己的路：窗口缩放会走 `windowDidResize` → 再钉一次。
        // delegate 是产品装上去的，不是测试塞的。
        let size = window.contentLayoutRect.size
        window.setContentSize(NSSize(width: size.width + 4, height: size.height))
        deadline = Date().addingTimeInterval(2.5)
        while sidebar.isCollapsed, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertFalse(sidebar.isCollapsed,
                       "带着旧存档打开时侧栏仍是收起的：第一眼看到的还是空列表 + 压在灯上的头部")
        XCTAssertFalse(sidebar.canCollapse, "展开后没重新钉住：再拖一次分隔条还是能拖没")
        XCTAssertIdentical(sidebar, try XCTUnwrap(sidebarItem(of: window), "缩放后列项消失了"),
                           "缩放换了列项对象：判据可能又盯在废弃的壳上")
    }

    func testSidebarItemPrefersTheAppKitSidebarBehaviorColumn() {
        // 认列的规矩本身也要有真值表：优先 `behavior == .sidebar`，
        // 认不出来才退回第一列；而**不许退回"全部列都钉上"**。
        let split = NSSplitViewController()
        let content = NSSplitViewItem(viewController: NSViewController())
        let sidebar = NSSplitViewItem(sidebarWithViewController: NSViewController())
        split.addSplitViewItem(content)     // 故意把内容列放前面
        split.addSplitViewItem(sidebar)

        // 夹具前提：第一列不是侧栏，否则下面两条断言分不出"按 behavior 认"和"按顺序认"。
        XCTAssertNotEqual(split.splitViewItems.first?.behavior, .sidebar)
        XCTAssertEqual(WindowConfigurator.Coordinator.sidebarItem(of: split), sidebar,
                       "没按 behavior 认侧栏，而是按顺序认了第一列")
        XCTAssertEqual(WindowConfigurator.Coordinator.sidebarItem(of: split)?.behavior, .sidebar)

        let onlyOne = NSSplitViewController()
        let plain = NSSplitViewItem(viewController: NSViewController())
        onlyOne.addSplitViewItem(plain)
        XCTAssertNotEqual(plain.behavior, .sidebar)
        XCTAssertEqual(WindowConfigurator.Coordinator.sidebarItem(of: onlyOne), plain,
                       "没有 .sidebar 行为时要退回第一列，否则 SwiftUI 换了 behavior 就悄悄不钉了")

        XCTAssertTrue(NSSplitViewController().splitViewItems.isEmpty)
        XCTAssertNil(WindowConfigurator.Coordinator.sidebarItem(of: NSSplitViewController()),
                     "空分栏器必须返回 nil：兜底成某个列项会让上层误判成钉好了")
    }

    /// 「把那颗按钮删掉」那一半的产品入口判据。
    /// 侧栏现在钉死了，工具栏再留一颗"显示/隐藏侧栏"只会让用户以为还收得掉；
    /// 而摘的时候不许伤到别的项 —— 误判的代价是用户少一个按钮，且没有任何提示。
    ///
    /// 走 `Coordinator.configure(window:)` 而不是直接调那个私有方法：
    /// 用户看到的效果由配置入口决定，只测内部函数就回到"几百条断言全绿、产品照崩"那一族。
    func testConfiguringAWindowRemovesTheSidebarToggleButKeepsOtherToolbarItems() throws {
        _ = NSApplication.shared
        let delegate = RecordingToolbarDelegate()
        let toolbar = NSToolbar(identifier: "chrome-probe-toolbar")
        toolbar.delegate = delegate
        // 逐项插入，而不是 `itemIdentifiers` setter / `setConfigurationFromDictionary:`：
        // 前者要 macOS 15+，后者早就废弃了 —— 测试夹具不该把产品的支持范围往上抬，
        // 也不该靠一条"在当前机器上刚好能用"的写法，判据换机器就哑了。
        toolbar.insertItem(withItemIdentifier: RecordingToolbarDelegate.toggleID, at: 0)
        toolbar.insertItem(withItemIdentifier: RecordingToolbarDelegate.searchID, at: 1)

        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 750, height: 560),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        defer { window.orderOut(nil) }
        // `configure` 里的 `alignTrafficLights` 会写产品单例 `WindowChromeMetrics.shared`。
        // 不还原的话，这条用例就把量到的几何留给了后面所有离屏帧夹具 —— 同一个进程里
        // "跑过哪条测试"会悄悄改变帧（上一轮就是这么栽过一次，判据见隔壁那条 save/defer）。
        let savedInset = WindowChromeMetrics.shared.detailContentTopInset
        defer { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedInset) }
        window.toolbar = toolbar
        window.makeKeyAndOrderFront(nil)
        // 项是显示时才造出来的：不等一下就可能出现"委托写了、items 还是空"的假前提。
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))

        let coordinator = WindowConfigurator().makeCoordinator()
        let classifiedBefore = toolbar.items.filter { coordinator.isSidebarToolbarItem($0) }
        let totalBefore = toolbar.items.count
        // 夹具前提：工具栏里**确实有**一颗会被认成侧栏开关的项，否则"摘掉了"是空的。
        XCTAssertEqual(classifiedBefore.count, 1, "夹具没造出那颗按钮，这条判据没有内容（items=\(toolbar.items)）")
        XCTAssertEqual(totalBefore, 2, "夹具应同时造出一颗普通项，用来证明删除不是清库")

        coordinator.configure(window: window)
        // configure 里那条延迟补做会再摘一次；等到它跑完再判，免得测出"当场摘了、之后又被装回来"
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))

        let ids = toolbar.items.map { $0.itemIdentifier.rawValue }
        XCTAssertTrue(toolbar.items.filter({ coordinator.isSidebarToolbarItem($0) }).isEmpty,
                      "配置后工具栏仍留着侧栏开关：\(ids)")
        XCTAssertTrue(toolbar.items.contains { $0.itemIdentifier == RecordingToolbarDelegate.searchID },
                      "把无关的普通项也删了：\(ids)")
        XCTAssertEqual(toolbar.items.count, totalBefore - classifiedBefore.count,
                       "删多了：\(ids)")
    }

    /// 把"拖不动"这件事变成可复算的数，而不是"关了 canCollapse 应该就拖不动了"的推断。
    /// 量两个量：① `minPossiblePositionOfDivider(at: 0)` —— 分隔条**能去的最左位置**，
    /// 也就是用户能拖到的极限；② 真的把 `setPosition`（拖拽走的正是这个方法）按到 0 与 80，
    /// 读回侧栏那一列的宽度（ObjC 那边叫 `setPosition:ofDividerAtIndex:`，Swift 导入成
    /// `setPosition(_:ofDividerAt:)`）。判据用列自己报的 `minimumThickness`，
    /// 不在测试里再抄一份 250 —— "两处共用同一个常数"推不出"两处对齐"，上一轮刚记过这条。
    func testPinnedSidebarCannotBeDraggedDownToZeroWidth() throws {
        let savedInset = WindowChromeMetrics.shared.detailContentTopInset
        defer { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedInset) }
        let window = try makeContentWindow(configured: true)
        defer { window.orderOut(nil) }
        let sidebar = try XCTUnwrap(sidebarItem(of: window), "找不到侧栏列项，探针失效")
        // 钉错列是这次改动最危险的失败方式（详情列被钉 = 用户看不出任何变化，
        // 而侧栏照样能拖没），所以每条判据都先确认"这是侧栏那一列"。
        XCTAssertEqual(sidebar.behavior, .sidebar, "量的不是侧栏那一列")
        let deadline = Date().addingTimeInterval(2.5)
        while sidebar.canCollapse, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        XCTAssertFalse(sidebar.canCollapse, "没钉住，下面量的就不是产品行为")

        let split = try XCTUnwrap(WindowConfigurator.Coordinator.splitViewController(in: window),
                                  "找不到分栏器")
        let minimum = sidebar.minimumThickness
        XCTAssertGreaterThan(minimum, 0, "列自己没报最小宽度，这条判据没有内容")
        let startWidth = sidebarColumnWidth(of: sidebar)
        XCTAssertGreaterThan(startWidth, 0, "量不到侧栏宽度，这条判据没有内容")
        XCTAssertGreaterThanOrEqual(startWidth, minimum, "起始就已经比列自己承诺的下限还窄")
        // 收尾把分隔条放回原位：AppKit 会把 `NSSplitView Subview Frames` 持久化
        // （用户机上那个键就躺在 `com.clipboardhistory.app` 的 defaults 里），
        // 同一个测试进程里后面再拍离屏帧，侧栏就可能变成 250pt 而不是 280pt。
        // "谁污染谁还原"这条规矩上一轮是为 `WindowChromeMetrics` 记的，这里是同一族。
        defer {
            split.splitView.setPosition(startWidth, ofDividerAt: 0)
            split.splitView.adjustSubviews()
        }

        // ① 最左极限。未钉住时这一列可以折叠，极限就是 0（整条拖没）。
        let leftmost = split.splitView.minPossiblePositionOfDivider(at: 0)
        XCTAssertGreaterThanOrEqual(leftmost, minimum,
                                    "分隔条最左还能到 \(leftmost)pt，而列的下限是 \(minimum)pt：还是能拖没")

        // ② 真的按下去看结果（比"极限位置"更硬：它绕过分栏器自己的约束计算）。
        for target: CGFloat in [0, 80] {
            split.splitView.setPosition(target, ofDividerAt: 0)
            split.splitView.adjustSubviews()
            RunLoop.main.run(until: Date().addingTimeInterval(0.15))
            let width = sidebarColumnWidth(of: sidebar)
            XCTAssertGreaterThanOrEqual(width, minimum,
                                        "把分隔条按到 \(target)pt，侧栏只剩 \(width)pt（下限 \(minimum)pt）")
        }
        print("SIDEBAR_PIN 起始宽度=\(startWidth)pt 列下限=\(minimum)pt 分隔条最左=\(leftmost)pt "
            + "按到 0pt 后=\(sidebarColumnWidth(of: sidebar))pt")

        // A/B 的另一半：同一台机器、同一套夹具，**不挂配置器**时这条判据必须看得见坏状态。
        // 实测本机：未钉住的极限是 -1pt（整条能拖没），钉住之后是 250pt。
        // 少了这一半，"最左 ≥ 列下限"可能量的是一条本来就拖不动的分隔条。
        let unpinned = try makeContentWindow(configured: false)
        defer { unpinned.orderOut(nil) }
        let looseSidebar = try XCTUnwrap(sidebarItem(of: unpinned), "未配置窗口里找不到侧栏列项")
        XCTAssertTrue(looseSidebar.canCollapse, "未配置窗口本该还能折叠，夹具前提破了")
        let looseSplit = try XCTUnwrap(WindowConfigurator.Coordinator.splitViewController(in: unpinned),
                                       "未配置窗口里找不到分栏器")
        let looseLeftmost = looseSplit.splitView.minPossiblePositionOfDivider(at: 0)
        XCTAssertLessThan(looseLeftmost, leftmost,
                          "未钉住的极限(\(looseLeftmost)pt)不比钉住的(\(leftmost)pt)更靠左：这条判据看不见坏状态")
        XCTAssertLessThan(looseLeftmost, looseSidebar.minimumThickness,
                          "未钉住时也到不了列下限以下（最左 \(looseLeftmost)pt / 下限 "
                          + "\(looseSidebar.minimumThickness)pt），量到的东西不对")
        print("SIDEBAR_PIN 未钉住：最左=\(looseLeftmost)pt 列下限=\(looseSidebar.minimumThickness)pt")
    }

    /// 侧栏那一列现在的宽度。问列自己的控制器要视图，**不按 `splitView.subviews` 的下标取**：
    /// 层级打印显示那组子视图是 `[侧栏以外的包装视图(750pt), NSTitlebarBackgroundView,
    /// NSTitlebarBackgroundView, _NSSplitViewShadowView, 侧栏包装视图(280pt)]` ——
    /// 按"第 index 个"去取，index 0 量到的是**内容列**，而它永远 ≥ 250pt，
    /// 这条判据就会绿着通过（第一版就是这么写的，被那张层级打印拦下）。
    private func sidebarColumnWidth(of item: NSSplitViewItem) -> CGFloat {
        item.viewController.view.frame.width
    }

    /// 造一个跑真实 `ContentView` 的窗口（数据侧一律用替身，不碰用户存档）。
    private func makeContentWindow(configured: Bool) throws -> NSWindow {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 750, height: 560),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        window.titlebarAppearsTransparent = true
        let host = NSHostingView(rootView: Self.root(store: Self.makeStore(), configured: configured))
        host.frame = NSRect(x: 0, y: 0, width: 750, height: 560)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        // 等 SwiftUI 真的把分栏器建出来（找不到列项时上面会用 XCTUnwrap 大声失败）
        let deadline = Date().addingTimeInterval(2.0)
        while Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            if let split = WindowConfigurator.Coordinator.splitViewController(in: window),
               !split.splitViewItems.isEmpty { break }
        }
        return window
    }

    private static func makeStore() -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        store.add(ClipboardIntake.Entry(content: .text("侧栏钉住判据用的记录"),
                                        thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        return store
    }

    private static func root(store: HistoryStore, configured: Bool) -> AnyView {
        AnyView(
            Group {
                if configured {
                    ContentView(historyStore: store).background(WindowConfigurator())
                } else {
                    ContentView(historyStore: store)
                }
            }
        )
    }

    private func sidebarItem(of window: NSWindow) -> NSSplitViewItem? {
        guard let split = WindowConfigurator.Coordinator.splitViewController(in: window) else { return nil }
        return WindowConfigurator.Coordinator.sidebarItem(of: split)
    }

    /// 造工具栏内容用的委托：一颗真会被判定成侧栏开关的项，加一颗普通项。
    /// 两颗都是必须的 —— 只造前者的话，"全清"这种坏实现也能通过。
    @MainActor
    private final class RecordingToolbarDelegate: NSObject, NSToolbarDelegate {
        static let toggleID = NSToolbarItem.Identifier("com.apple.SwiftUI.navigationSplitView.toggleSidebar")
        static let searchID = NSToolbarItem.Identifier("probe.search")

        func toolbar(_ toolbar: NSToolbar,
                     itemForItemIdentifier itemIdentifier: NSToolbarItem.Identifier,
                     willBeInsertedIntoToolbar flag: Bool) -> NSToolbarItem? {
            let item = NSToolbarItem(itemIdentifier: itemIdentifier)
            if itemIdentifier == Self.toggleID {
                item.label = "Sidebar"
                item.paletteLabel = "Sidebar"
                item.action = #selector(NSSplitViewController.toggleSidebar(_:))
            } else if itemIdentifier == Self.searchID {
                item.label = "搜索"
                item.paletteLabel = "搜索"
            } else {
                return nil
            }
            return item
        }

        func toolbarDefaultItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
            [Self.toggleID, Self.searchID]
        }

        func toolbarAllowedItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
            [Self.toggleID, Self.searchID]
        }
    }

    @MainActor
    private class MetricsRecorder {
        private var cancellable: AnyCancellable?
        private(set) var count = 0

        init(metric: WindowChromeMetrics) {
            count = 0
            cancellable = metric.$detailContentTopInset.sink { [weak self] _ in
                self?.count += 1
            }
        }

        func stop() { cancellable?.cancel() }
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "WindowChromeLayoutTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
