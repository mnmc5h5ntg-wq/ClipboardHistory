import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R567：折叠/展开重做的**第①段**（`docs/FOLD_DUO_SPEC_2026-11-03.md` §3）—— 几何与读数重锚，不动画。
///
/// 这一段只判四件事，全部从**产品入口**进入（`WindowManager.showMainWindow()` 建真窗口 +
/// `delegate.perform(.toggleMainWindowCollapse)` 走产品自己的 action）：
/// ① 默认内容尺寸 848×600；② 折叠 = 高度不变、宽度对折 ⇒ 424×600；
/// ③ 两栏各占内容宽的一半（D5 的 50/50 —— 折痕必须正好落在中缝上）；
/// ④ 锁比例用 `contentAspectRatio`（拖边角等比、不弹回），并且**随状态翻过去**；
/// 外加中缝拖拽被禁 —— 锁法是 `canCollapse == false` 且每列 `minimumThickness == maximumThickness`
/// （这份 SDK 的 `NSSplitViewItem.h` 里没有 `isDraggable`，可拖的开关就是这两个约束）；
/// 两栏锁等宽之后，分隔条能拖出的只有不对称。
///
/// ⚠ 这一节**不判**任何过渡、模糊、透明、阴影（那是第②③段的靶；§4 那三条假设一条都没当成已成立）。
@MainActor
final class FoldGeometryReanchorTests: XCTestCase {
    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!
    private var savedDetailContentTopInset: CGFloat?

    private func setUpProduct(_ name: String = UUID().uuidString) {
        savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        defaults = UserDefaults(suiteName: "r567-fold-geometry-\(name)")!
        defaults.removePersistentDomain(forName: "r567-fold-geometry-\(name)")
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

    /// 等 SwiftUI 把分栏器建出来。**找不到 = 判据红**（探针失效不等于那格绿，R488 那条规矩）。
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

    /// 两栏的**实际布局宽度**（pt，从 `arrangedSubviews` 读，不读产品常量）。
    private func columnWidths(of split: NSSplitViewController) -> [CGFloat] {
        split.splitView.arrangedSubviews.map { $0.frame.width }
    }

    // MARK: - ① + ② 默认尺寸与「高度不变、宽度对折」

    func testExpandedWidthIs848AndFoldHalvesItWithoutTouchingHeight() throws {
        setUpProduct()
        defer { tearDownProduct() }
        guard let window = makeWindow() else { return }

        let layout = window.contentLayoutRect.size
        let frameHeight = window.frame.height
        CaptureReadings.emit("FOLD_GEOMETRY_REANCHOR 状态=展开 layout=\(Int(layout.width))x\(Int(layout.height))"
            + " frame高=\(String(format: "%.1f", frameHeight))"
            + " 三种口径 layout/contentRect/contentView=\(Int(layout.width))"
            + "/\(NSStringFromSize(window.contentRect(forFrameRect: window.frame).size))"
            + "/\(window.contentView.map { NSStringFromSize($0.frame.size) } ?? "无")")
        XCTAssertEqual(layout.width, 848, accuracy: 0.5,
                       "默认内容宽不是规格 D5 的 848（现读 \(layout.width)）")

        delegate.perform(.toggleMainWindowCollapse)
        settle(0.2)
        let folded = window.contentLayoutRect.size
        CaptureReadings.emit("FOLD_GEOMETRY_REANCHOR 状态=折叠 layout=\(Int(folded.width))x\(Int(folded.height))"
            + " frame高=\(String(format: "%.1f", window.frame.height)) 高差=\(window.frame.height - frameHeight)")
        XCTAssertEqual(folded.width, 424, accuracy: 0.5,
                       "折叠宽不是展开宽的一半（\(folded.width) vs \(layout.width)）")
        XCTAssertEqual(folded.width * 2, layout.width, accuracy: 1.0,
                       "折叠宽 × 2 不等于展开宽 ⇒ 折痕落不到中缝")
        XCTAssertEqual(window.frame.height, frameHeight, accuracy: 0.5,
                       "D5 说折叠只动宽度：整窗高变了就不是对折")

        delegate.perform(.toggleMainWindowCollapse)
        settle(0.2)
        XCTAssertEqual(window.contentLayoutRect.width, 848, accuracy: 0.5,
                       "展开没回到 848 ⇒ 对折不可逆")
    }

    // MARK: - ③ 两栏各半（50/50）

    func testTheTwoColumnsEachTakeHalfTheContentWidth() throws {
        setUpProduct()
        defer { tearDownProduct() }
        guard let window = makeWindow() else { return }
        guard let split = splitController(of: window) else {
            XCTFail("真窗口里找不到 NSSplitViewController 或它没有列项 ⇒ 这一格没有内容，不是没红")
            return
        }
        let views = split.splitView.arrangedSubviews
        let thickness = split.splitView.dividerThickness
        guard views.count >= 2 else {
            XCTFail("分栏器只有 \(views.count) 个 arrangedSubviews ⇒ 读不到两栏")
            return
        }
        let sidebar = views[0].frame.width
        let content = split.splitView.bounds.width
        // 详情列的 frame 在 SwiftUI 里铺满分栏器（实测 `{{0,0},{848,632}}`），所以它自己的宽**不是**证人；
        // 可判的是那条恒等式：内容宽 − 侧栏 − 分隔条 = 详情实际占到的那一段。
        let detail = content - sidebar - thickness
        CaptureReadings.emit("FOLD_GEOMETRY_COLUMNS 侧栏=\(String(format: "%.2f", sidebar))"
            + " 详情(算)=\(String(format: "%.2f", detail))"
            + " 分隔条=\(String(format: "%.2f", thickness))"
            + " 分栏宽=\(String(format: "%.2f", content))"
            + " 缝中心=\(String(format: "%.2f", sidebar + thickness / 2))")
        XCTAssertEqual(sidebar, 423.5, accuracy: 0.5,
                       "侧栏不是 (848 − 1)/2 ⇒ 两栏对不上半页（现读 \(sidebar)）")
        XCTAssertEqual(detail, sidebar, accuracy: 0.01,
                       "两栏不等宽（侧栏 \(sidebar) vs 详情 \(detail)）⇒ 50/50 不成立，折痕会落在中缝之外")
        XCTAssertEqual(sidebar + thickness / 2, content / 2, accuracy: 0.01,
                       "分隔条的中心不在内容宽的正中 ⇒ 对折时右半页盖不到左半页")

        // 行为证人：真的去"拖"一次中缝。AppKit 文档说 `setPosition` 的行为等同于用户拖
        // （会走 delegate 的约束），所以拖得动就是没锁住。
        split.splitView.setPosition(300, ofDividerAt: 0)
        settle(0.15)
        CaptureReadings.emit("FOLD_GEOMETRY_DRAG_PROBE 拖到300之后 侧栏=\(String(format: "%.2f", views[0].frame.width))")
        XCTAssertEqual(views[0].frame.width, sidebar, accuracy: 0.01,
                       "中缝还能被拖（拖到 300 之后侧栏变成 \(views[0].frame.width)）⇒ D7 的「禁中缝拖拽」没落地")
    }

    // MARK: - ④ 锁比例随状态翻过去

    func testAspectRatioIsLockedAndFlipsWithTheFold() throws {
        setUpProduct()
        defer { tearDownProduct() }
        guard #available(macOS 13.0, *) else {
            throw XCTSkip("ASPECT_LOCK_NOT_RUN=macos<13 —— `contentAspectRatio` 是 macOS 13 才有的 API；"
                + "这一格在 12 上不许读成「锁住了」，也不许读成「产品坏了」")
        }
        guard let window = makeWindow() else { return }
        let ratio = window.contentAspectRatio.width / max(window.contentAspectRatio.height, 0.001)
        CaptureReadings.emit("FOLD_GEOMETRY_ASPECT 状态=展开 ratio=\(String(format: "%.6f", ratio))"
            + " 规格期望=1.413333(=848/600)"
            + " 可拖=\(window.styleMask.contains(.resizable))")
        XCTAssertEqual(ratio, 848.0 / 600.0, accuracy: 0.002,
                       "展开态没把比例锁成 848/600 ⇒ 拖边角不等比，或压根没锁")

        delegate.perform(.toggleMainWindowCollapse)
        settle(0.2)
        let flipped = window.contentAspectRatio.width / max(window.contentAspectRatio.height, 0.001)
        CaptureReadings.emit("FOLD_GEOMETRY_ASPECT 状态=折叠 ratio=\(String(format: "%.6f", flipped))"
            + " 规格期望=0.706667(=424/600)")
        XCTAssertEqual(flipped, 424.0 / 600.0, accuracy: 0.002,
                       "折叠后比例没翻过去 ⇒ 窗口还按展开态那个横 √2 锁着，纵向对折就锁死在错的形状上")
    }

    // MARK: - ⑤ 中缝不许拖

    /// SDK 里 `NSSplitViewItem` **没有** `isDraggable` 这个属性（本仓 `xcrun --show-sdk-path` 那份
    /// `NSSplitViewItem.h` 现读：可拖的开关是 `minimumThickness` / `maximumThickness` / `canCollapse`
    /// 这三个约束，外加 `NSSplitView` 那份 delegate 里的 constrain 方法）。所以"禁中缝拖拽"在这里
    /// 只能判**机制本身**：两栏都被锁成一个不能变的厚度，且侧栏不可折叠 ⇒ 分隔条没有可去的位置。
    func testTheSeamBetweenTheTwoColumnsCannotBeDragged() throws {
        setUpProduct()
        defer { tearDownProduct() }
        guard let window = makeWindow() else { return }
        guard let split = splitController(of: window) else {
            XCTFail("找不到分栏器 ⇒ 这一格没有内容")
            return
        }
        let lines = split.splitViewItems.map { item in
            String(format: "canCollapse=%d min=%.1f max=%.1f",
                   item.canCollapse ? 1 : 0, item.minimumThickness, item.maximumThickness)
        }
        CaptureReadings.emit("FOLD_GEOMETRY_ITEMS 列数=\(split.splitViewItems.count) 每列=[\(lines.joined(separator: " ; "))]")
        XCTAssertEqual(split.splitViewItems.count, 2,
                       "两栏之外还多出 \(split.splitViewItems.count - 2) 列 ⇒ 50/50 无从判起")
        for (index, item) in split.splitViewItems.enumerated() {
            XCTAssertFalse(item.canCollapse,
                           "第 \(index) 列仍可被拖没（canCollapse）⇒ 中缝还能把一栏拖消失")
        }
    }
}
