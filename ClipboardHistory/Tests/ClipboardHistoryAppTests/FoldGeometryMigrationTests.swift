import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R592（用户实测反馈 1 + 3）：升级用户的**旧记忆压住新默认值** ⇒ 一次性几何迁移。
///
/// 用户机现读（2026-11-06 16:12，`defaults export com.clipboardhistory.app`）：
/// ```
/// mainWindowExpandedWidth = 750        mainWindowCollapsedWidth = 420      ← R567 之前的两档默认
/// "NSWindow Frame …MainWindowContent…-1-AppWindow-1" = "585 368 750 492 0 0 1470 923 "
/// "NSSplitView Subview Frames …-AppWindow-1, SidebarNavigationSplitView"
///     = ["0 0 423.5 492 NO NO", "423.5 0 326.5 492 NO NO"]                ← 两栏实测不等宽
/// ```
/// 三样叠在一起才是"等分没生效"：记忆宽 750 被 `width(forKey:fallback:)` 原样端上来、
/// 恢复的窗口高 492 让宽高比变成 1.52（不是 √2）、分栏帧把详情列钉成 326.5。
/// 所以迁移必须同时抬**两档宽度**、改写**恢复的窗口宽高**（顶边不动）、删掉**分栏子视图帧**，
/// 并打版本键。少做任意一样，用户签字的那两条验收（两栏等宽、比例≈√2）都过不了。
///
/// 判据进入的方式（AGENTS.md 第 1 条）：①②③走 `MainWindowCollapseController(defaults:)` 与
/// `WindowManager.showMainWindow()` 真窗口 + `delegate.perform(.toggleMainWindowCollapse)`；
/// 纯真值表那一格只判 `plan`，它在下面第二条里被产品入口那格逐字复用同样的输入。
@MainActor
final class FoldGeometryMigrationTests: XCTestCase {
    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!
    private var savedDetailContentTopInset: CGFloat?

    /// `seed` 必须排在 controller 建出来**之前** —— 迁移就在 init 里跑，晚seed 就是另一跑了。
    private func setUpProduct(_ name: String = UUID().uuidString, seed: ((UserDefaults) -> Void)? = nil) {
        savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        defaults = UserDefaults(suiteName: "r592-fold-migration-\(name)")!
        defaults.removePersistentDomain(forName: "r592-fold-migration-\(name)")
        seed?(defaults)
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

    private func makeWindow() -> NSWindow? {
        WindowManager.showMainWindow()
        settle(0.12)
        let windows = mainWindows
        XCTAssertEqual(windows.count, 1, "没有建出唯一主窗口")
        return windows.first
    }

    private func splitController(of window: NSWindow) -> NSSplitViewController? {
        let deadline = Date().addingTimeInterval(2.0)
        while Date() < deadline {
            if let split = WindowConfigurator.Coordinator.splitViewController(in: window),
               !split.splitViewItems.isEmpty {
                return split
            }
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        return nil
    }

    /// 用户机上那两条键的**逐字**拼写（16:12 现读，键名是 SwiftUI 的类型拼写；改类型会换键名，
    /// 所以迁移按"含 `ClipboardHistoryApp.` 且含 `-AppWindow-`"认，不按整串抄）。
    private let userWindowFrameKey =
        "NSWindow Frame SwiftUI.WindowGroup<SwiftUI.ModifiedContent<ClipboardHistoryApp.MainWindowContent, "
        + "SwiftUI._AppearanceActionModifier>>-1-AppWindow-1"
    private let userSplitFrameKey =
        "NSSplitView Subview Frames SwiftUI.WindowGroup<SwiftUI.ModifiedContent<ClipboardHistoryApp.MainWindowContent, "
        + "SwiftUI._AppearanceActionModifier>>-1-AppWindow-1, SidebarNavigationSplitView"

    private func seedLegacyUserStore(_ d: UserDefaults) {
        d.set(750.0, forKey: MainWindowCollapseController.expandedWidthKey)
        d.set(420.0, forKey: MainWindowCollapseController.collapsedWidthKey)
        d.set(false, forKey: MainWindowCollapseController.collapsedKey)
        d.set("585 368 750 492 0 0 1470 923 ", forKey: userWindowFrameKey)
        d.set(["0.000000, 0.000000, 423.500000, 492.000000, NO, NO",
               "423.500000, 0.000000, 326.500000, 492.000000, NO, NO"], forKey: userSplitFrameKey)
    }

    // MARK: - ① 真值表：四档具名出口，谁都不许被读成"没红"

    func testPlanTruthTableNamesAllFourExits() {
        let legacy = MainWindowGeometryMigration.plan(
            storedExpanded: MainWindowGeometryMigration.legacyExpandedWidth,
            storedCollapsed: MainWindowGeometryMigration.legacyCollapsedWidth,
            storedVersion: nil)
        XCTAssertEqual(legacy.reason, "legacy-default-pair")
        XCTAssertEqual(legacy.expandedWidth, MainWindowCollapsePolicy.expandedWidthDefault)
        XCTAssertEqual(legacy.collapsedWidth, MainWindowCollapsePolicy.collapsedWidthDefault)
        XCTAssertTrue(legacy.rewritesRestoredFrames, "旧默认对必须连恢复的窗口帧一起抬，否则高还是 492")
        XCTAssertTrue(legacy.stampsVersion)

        // 只抬了一半（旧版本只写了展开档）⇒ 不能算旧默认对，一律不动。
        let half = MainWindowGeometryMigration.plan(storedExpanded: 750, storedCollapsed: nil, storedVersion: nil)
        XCTAssertEqual(half.reason, "not-legacy-pair")
        XCTAssertNil(half.expandedWidth, "记忆值不是旧默认对还去抬 ⇒ 会把用户自己调过的宽度抹掉")
        XCTAssertFalse(half.rewritesRestoredFrames)

        let fresh = MainWindowGeometryMigration.plan(storedExpanded: nil, storedCollapsed: nil, storedVersion: nil)
        XCTAssertEqual(fresh.reason, "no-legacy-memory")
        XCTAssertTrue(fresh.stampsVersion, "新装也要打版本键，否则以后每一轮 init 都重跑一遍判据")
        XCTAssertNil(fresh.expandedWidth)

        let done = MainWindowGeometryMigration.plan(storedExpanded: 750, storedCollapsed: 420, storedVersion: 1)
        XCTAssertEqual(done.reason, "already-migrated")
        XCTAssertNil(done.expandedWidth, "已经迁过还抬 ⇒ 「只抬一次」没了")
        XCTAssertFalse(done.stampsVersion)
    }

    // MARK: - ② 产品入口：记忆值 + 恢复帧，一次跑完就到位

    func testLegacyMemoryIsRaisedOnceThroughTheControllerEntry() {
        setUpProduct(seed: seedLegacyUserStore)
        defer { tearDownProduct() }
        XCTAssertEqual(controller.geometryMigration?.reason, "legacy-default-pair",
                       "产品入口没跑到迁移 ⇒ 这一格红了才对（现读 \(String(describing: controller.geometryMigration?.reason))）")
        XCTAssertEqual(defaults.double(forKey: MainWindowCollapseController.expandedWidthKey), 848, accuracy: 0.001,
                       "旧记忆 750 没被抬到规格档 848")
        XCTAssertEqual(defaults.double(forKey: MainWindowCollapseController.collapsedWidthKey), 424, accuracy: 0.001,
                       "旧折叠记忆 420 没被抬到 424（= 848 的一半）")
        XCTAssertEqual(defaults.integer(forKey: MainWindowGeometryMigration.versionKey),
                       MainWindowGeometryMigration.currentVersion)
        // 折叠状态本身不是几何，迁移不许顺手改它。
        XCTAssertFalse(defaults.bool(forKey: MainWindowCollapseController.collapsedKey))

        // 恢复的窗口帧：宽高换成规格档，**顶边逐字不动**（用户的摆放位置是他调过的东西）。
        let frame = defaults.string(forKey: userWindowFrameKey) ?? ""
        let parts = frame.split(separator: " ").compactMap(Double.init)
        XCTAssertEqual(parts.count, 8, "改写后的窗口帧读不出八个数：\(frame)")
        XCTAssertEqual(parts[2], 848, accuracy: 0.01, "恢复帧的宽没抬 ⇒ 启动后 AppKit 会把 750 盖回来")
        XCTAssertEqual(parts[3], 600, accuracy: 0.01, "恢复帧的高没抬 ⇒ 宽高比还是 1.52，不是 √2")
        XCTAssertEqual(parts[1] + parts[3], 368 + 492, accuracy: 0.01,
                       "顶边动了 ⇒ 迁移抹掉了用户放的位置（现读 \(frame)）")
        XCTAssertEqual(parts[0], 585, accuracy: 0.01, "左边距该逐字保留")
        XCTAssertEqual(Array(parts[4...]), [0, 0, 1470, 923], "屏幕那一段是 AppKit 写的，迁移不该改它")
        XCTAssertNil(defaults.array(forKey: userSplitFrameKey),
                     "分栏子视图帧还留着 ⇒ 详情列会被恢复成 326.5，两栏不等宽")

        CaptureReadings.emit("FOLD_GEOMETRY_MIGRATION reason=\(controller.geometryMigration?.reason ?? "nil")"
            + " 展开档=\(defaults.double(forKey: MainWindowCollapseController.expandedWidthKey))"
            + " 折叠档=\(defaults.double(forKey: MainWindowCollapseController.collapsedWidthKey))"
            + " 版本键=\(defaults.integer(forKey: MainWindowGeometryMigration.versionKey))"
            + " 恢复帧=\(frame) 分栏帧残留=\(defaults.object(forKey: userSplitFrameKey) == nil ? 0 : 1)")
    }

    func testVersionKeyIsWhyTheSecondLaunchLeavesTheUsersOwnWidthAlone() {
        setUpProduct(seed: seedLegacyUserStore)
        defer { tearDownProduct() }
        // 迁移之后用户自己把窗口拖回 750/420（旧默认那对数值）。第二段记忆必须原样留着：
        // 钉的就是"只抬一次"，而它的证人只有版本键。
        defaults.set(750.0, forKey: MainWindowCollapseController.expandedWidthKey)
        defaults.set(420.0, forKey: MainWindowCollapseController.collapsedWidthKey)
        let second = MainWindowCollapseController(defaults: defaults)
        XCTAssertEqual(second.geometryMigration?.reason, "already-migrated")
        XCTAssertEqual(defaults.double(forKey: MainWindowCollapseController.expandedWidthKey), 750, accuracy: 0.001,
                       "第二跑又把 750 抬成 848 ⇒ 「只抬一次」被版本键以外的东西替代了，用户的调整被抹掉")
        // 摘掉版本键这一格的正对照：没有键 ⇒ 同一段记忆会被反复抬。
        defaults.removeObject(forKey: MainWindowGeometryMigration.versionKey)
        let third = MainWindowCollapseController(defaults: defaults)
        XCTAssertEqual(third.geometryMigration?.reason, "legacy-default-pair",
                       "删掉版本键后迁移不再认旧默认对 ⇒ 这一格说明版本键才是那条闸门")
    }

    func testAUserWhoActuallyResizedIsLeftAlone() {
        setUpProduct { d in
            d.set(1000.0, forKey: MainWindowCollapseController.expandedWidthKey)
            d.set(500.0, forKey: MainWindowCollapseController.collapsedWidthKey)
            d.set("100 100 1000 700 0 0 1470 923 ", forKey: self.userWindowFrameKey)
        }
        defer { tearDownProduct() }
        XCTAssertEqual(controller.geometryMigration?.reason, "not-legacy-pair")
        XCTAssertEqual(defaults.double(forKey: MainWindowCollapseController.expandedWidthKey), 1000, accuracy: 0.001,
                       "手动调过 1000 的用户被迁移改了宽度 ⇒ 迁移越界")
        XCTAssertEqual(defaults.string(forKey: userWindowFrameKey), "100 100 1000 700 0 0 1470 923 ",
                       "不是旧默认对还去改写恢复帧 ⇒ 抹掉了用户自己的窗口尺寸")
    }

    // MARK: - ③ 验收（用户签字口径）：升级后从产品入口读两栏等宽 + 比例≈√2

    func testUpgradedUserGetsEqualColumnsAndRootTwoRatio() throws {
        setUpProduct(seed: seedLegacyUserStore)
        defer { tearDownProduct() }
        guard let window = makeWindow() else { return }
        let layout = window.contentLayoutRect.size
        let content = window.contentRect(forFrameRect: window.frame).size
        let view = window.contentView?.frame.size ?? .zero
        let frameSize = window.frame.size
        CaptureReadings.emit(String(format: "FOLD_UPGRADE_CALIBERS layout=%.1fx%.1f contentRect=%.1fx%.1f"
                                    + " contentView=%.1fx%.1f frame=%.1fx%.1f",
                                    layout.width, layout.height, content.width, content.height,
                                    view.width, view.height, frameSize.width, frameSize.height))
        let ratio = Double(content.width / max(content.height, 1))
        CaptureReadings.emit(String(format: "FOLD_UPGRADE_ACCEPT 内容=%.1fx%.1f 宽高比=%.4f √2=%.4f 差=%.4f",
                                    content.width, content.height, ratio, 2.0.squareRoot(),
                                    abs(ratio - 2.0.squareRoot())))
        XCTAssertEqual(content.width, 848, accuracy: 0.5,
                       "升级后内容宽不是规格档 848（现读 \(content.width)）⇒ 旧记忆没抬起来")
        XCTAssertLessThan(abs(ratio - 2.0.squareRoot()), 0.02,
                          "宽高比 \(ratio) 离 √2 超过 0.02 ⇒ 用户签的那条「比例≈√2」不成立")

        guard let split = splitController(of: window) else {
            XCTFail("真窗口里找不到 NSSplitViewController ⇒ 这一格没有内容，不是没红")
            return
        }
        let views = split.splitView.arrangedSubviews
        guard views.count >= 2 else {
            XCTFail("分栏器只有 \(views.count) 个 arrangedSubviews ⇒ 读不到两栏")
            return
        }
        typealias Caliber = FoldGeometryReanchorTests.ColumnGridCaliber
        let sidebar = Double(views[0].frame.width)
        let thickness = Double(split.splitView.dividerThickness)
        let splitWidth = Double(split.splitView.bounds.width)
        let detail = splitWidth - sidebar - thickness
        let scale = Double(window.backingScaleFactor)
        // 等宽这把尺**复用第①段那一支**（`FoldGeometryReanchorTests.ColumnGridCaliber`）：
        // 界值按倍率派生，两处各写一份就会漂成两个口径（R587 那条"词表两份写法"的同族）。
        // 全部转成 Double 再进尺 —— 那一支的量纲是 Double，混着 CGFloat 传会撞上报"歧义的 /"的坑。
        let outcome = Caliber.verdict(scale: scale, sidebar: sidebar, detail: detail,
                                      seamCenter: sidebar + thickness / 2,
                                      contentCenter: splitWidth / 2)
        CaptureReadings.emit(String(format: "FOLD_UPGRADE_COLUMNS 侧栏=%.2f 详情=%.2f 分栏宽=%.2f 倍率=%.1fx 判=%@",
                                    sidebar, detail, splitWidth, scale,
                                    outcome == Caliber.Outcome.ok ? "等宽" : "不等宽"))
        if outcome != Caliber.Outcome.ok {
            XCTFail("升级用户两栏不等宽（侧栏 \(sidebar) vs 详情 \(detail)，判据=\(outcome)）"
                + " ⇒ 第①段对老用户等于没发生过")
        }
    }

    // MARK: - ⑤ 用户机上那一半：恢复通路给的高度也要抬（只抬那一趟）

    /// 2026-11-06 18:24 换装之后在用户机上现读：宽度那半成了（`mainWindowExpandedWidth = 848`、
    /// 两栏 423.5 / 424.5），但窗口仍是 `311 241 848 492` ⇒ 比例 1.72，用户签的那条「≈√2」不过。
    /// 成因不是键没改写（改写那一步有证人，见本节②），而是 AppKit 的恢复通路除了 defaults 键
    /// 之外还看 saved state，高度只从后者回来。所以产品要在**迁移那一趟**把高度也抬到规格档。
    func testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio() {
        setUpProduct(seed: seedLegacyUserStore)
        defer { tearDownProduct() }
        // 一扇"恢复出来的旧窗口"：750×492，顶边 860（= 368 + 492）。
        let window = NSWindow(contentRect: NSRect(x: 585, y: 368, width: 750, height: 492),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        let oldTop = window.frame.maxY
        controller.applyGeometry(to: window)
        let size = window.contentRect(forFrameRect: window.frame).size
        let ratio = Double(size.width / max(size.height, 1))
        CaptureReadings.emit(String(format: "FOLD_RATIO_INVARIANT 第一趟 内容=%.1fx%.1f 比=%.4f 顶边差=%.1f 抬高度次数=%d",
                                    size.width, size.height, ratio, abs(window.frame.maxY - oldTop),
                                    controller.heightLifts))
        XCTAssertEqual(size.width, 848, accuracy: 0.5, "旧记忆 750 没被抬到 848")
        XCTAssertEqual(size.height, 600, accuracy: 1.0,
                       "高度没抬到 √2 那档 ⇒ 恢复的 492 还在，比例 1.72（用户签的那条不成立）")
        XCTAssertLessThan(abs(ratio - 2.0.squareRoot()), 0.02, "抬完之后宽高比必须≈√2")
        XCTAssertEqual(window.frame.maxY, oldTop, accuracy: 0.5,
                       "抬高度把顶边挪走了 ⇒ 用户放的位置被抹掉")
        XCTAssertEqual(controller.heightLifts, 1, "这一趟应该只抬一次（现读 \(controller.heightLifts)）")

        // 用户自己等比拖出来的那一档：产品记的宽度跟着变成 900（`rememberWidth` 在切换时写），
        // 于是 applyGeometry 面对的是 900×637 —— 已在 √2 上 ⇒ 不许再抬高度。
        defaults.set(900.0, forKey: MainWindowCollapseController.expandedWidthKey)
        window.setFrame(NSRect(x: window.frame.minX, y: window.frame.maxY - 637,
                               width: 900, height: 637), display: false)
        controller.applyGeometry(to: window)
        let second = window.contentRect(forFrameRect: window.frame).size
        CaptureReadings.emit(String(format: "FOLD_RATIO_INVARIANT 第二趟 内容=%.1fx%.1f 抬高度次数=%d",
                                    second.width, second.height, controller.heightLifts))
        XCTAssertEqual(second.width, 900, accuracy: 0.5, "第二趟的宽度该是用户记下来的 900")
        XCTAssertEqual(second.height, 637, accuracy: 0.5,
                       "用户等比拖出来的尺寸被抬回 600 ⇒ 不变量写错了（现读 \(second.height)）")
        XCTAssertEqual(controller.heightLifts, 1,
                       "第二趟又抬了一次（现读 \(controller.heightLifts)）⇒ 已在 √2 上也动，抹掉用户自己的尺寸")
    }

    func testTheRatioInvariantIsNotTiedToTheMigrationPair() {
        setUpProduct()                       // 没有旧记忆（用户从杪没截 over）
        defer { tearDownProduct() }
        XCTAssertEqual(controller.geometryMigration?.reason, "no-legacy-memory")
        let window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 1000, height: 700),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                              backing: .buffered, defer: false)
        controller.applyGeometry(to: window)
        let size = window.contentRect(forFrameRect: window.frame).size
        CaptureReadings.emit(String(format: "FOLD_RATIO_INVARIANT 无旧记忆 内容=%.1fx%.1f 抬高度次数=%d",
                                    size.width, size.height, controller.heightLifts))
        XCTAssertEqual(size.height, 848.0 / 2.0.squareRoot(), accuracy: 1.0,
                       "不在 √2 上就抬 —— 这一条是不变量，不靠迁移那个条件（否则用户机上已经打过的那一次之后就永远修不好）")
    }

    func testHeightLiftTruthTable() {
        // 展开态：848 → 599.6（规格档 600 在容差内）；所以 848×600 不该再抬。
        XCTAssertNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 848, height: 600),
                     "848×600 已经在 √2 上，再抬一次就是每轮都动用户的窗口")
        XCTAssertNotNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 848, height: 492))
        XCTAssertEqual(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 848, height: 492) ?? 0,
                       848.0 / 2.0.squareRoot(), accuracy: 0.01)
        // 折叠态：高度不变，所以 424 宽对应的仍是 600（方向相反）。
        XCTAssertNil(MainWindowCollapsePolicy.heightLift(collapsed: true, width: 424, height: 600),
                     "折叠态 424×600 是一个竖 √2，抬它就是把 D5 改提了")
        XCTAssertNotNil(MainWindowCollapsePolicy.heightLift(collapsed: true, width: 424, height: 492))
        // 容差：用户等比拖出来的 900×637 必须判成"已在楣上"。
        XCTAssertNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 900, height: 637),
                     "900×637 离 √2 只有 0.0009，抬它就是抹掉用户自己的尺寸")
        XCTAssertNotNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 848, height: 618),
                        "偏 3% 还不抬 ⇒ 容差被放宽了")
        // 没有对象的两种：零宽 / 零高 ⇒ 不抬也不猜。
        XCTAssertNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 0, height: 600))
        XCTAssertNil(MainWindowCollapsePolicy.heightLift(collapsed: false, width: 848, height: 0))
    }

    // MARK: - ④ 恢复帧的字符串手术：读不出来就不许猜

    func testRestoredFrameStringRefusesMalformedValuesAndKeepsTheTopEdge() {
        XCTAssertEqual(MainWindowGeometryMigration.restoredFrameString("585 368 750 492 0 0 1470 923 ",
                                                                        width: 848, height: 600),
                       "585 260 848 600 0 0 1470 923 ",
                       "顶边 860 必须原样留着 ⇒ y 该回算成 860−600=260")
        XCTAssertNil(MainWindowGeometryMigration.restoredFrameString("585 368 750", width: 848, height: 600),
                     "只有三个数就当没这条键；猜一个 origin 出去会把用户的窗口挪到别处")
        XCTAssertNil(MainWindowGeometryMigration.restoredFrameString("", width: 848, height: 600))
        // 正对照：负 origin（窗口在副屏）也要按同样那条恒等式走。
        XCTAssertEqual(MainWindowGeometryMigration.restoredFrameString("-100 -200 750 492 0 0 1470 923 ",
                                                                       width: 848, height: 600),
                       "-100 -308 848 600 0 0 1470 923 ",
                       "顶边 292 不动 ⇒ y 从 −200 变成 292−600=−308；把负号丢掉就是另一台机器上的窗口位置")
    }

    func testTheMigrationOnlyRecognisesItsOwnMainWindowKeys() {
        XCTAssertTrue(MainWindowGeometryMigration.isMainWindowFrameKey(userWindowFrameKey))
        XCTAssertTrue(MainWindowGeometryMigration.isMainWindowSplitKey(userSplitFrameKey))
        // 系统面板与别的 App 的键一个都不许进这个集合（迁移不许拿用户的默认域当靶子扫）。
        XCTAssertFalse(MainWindowGeometryMigration.isMainWindowFrameKey("NSWindow Frame NSColorPanel"))
        XCTAssertFalse(MainWindowGeometryMigration.isMainWindowFrameKey("NSWindow Frame com_apple_SwiftUI_Settings_window"))
        XCTAssertFalse(MainWindowGeometryMigration.isMainWindowSplitKey(
            "NSSplitView Subview Frames SomeOtherApp.Something-1-AppWindow-1, SidebarNavigationSplitView"))
        XCTAssertFalse(MainWindowGeometryMigration.isMainWindowFrameKey("mainWindowExpandedWidth"))
    }
}
