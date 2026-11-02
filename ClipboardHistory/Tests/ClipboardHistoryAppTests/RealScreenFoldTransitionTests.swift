import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R552：**真实窗口**上的折叠/展开过渡采样 —— 给 python 侧的屏上录像当被试与坐标源。
///
/// 为什么要它（用户实测反馈 + STATE R552 靶 ①）：折叠过渡在真机上是灾难级体验，而这一族
/// 以前的全部证据都来自**离屏胶片** —— 离屏看不见窗口服务的真实合成，于是「15 帧 / 8 个中间宽」
/// 与手上的卡顿可以同时为真。离屏证据判为**不够格**，这一条改成把产品真的那扇窗摆上屏幕，
/// 由外部进程以 60fps 录屏量屏上帧间距；本条只负责三件事：
///   1. 把窗口矩形**由被测物自己印**（不写死坐标 —— R143 那一族：手抄偏移会让尺截到错的那一态）；
///   2. 等外部录像开跑（`go` 文件）之后，按固定节拍做「折叠 → 停 → 展开」；
///   3. 每一拍记 `(t_ms, 窗口宽, foldProgress, isCollapsed, 分栏各列宽)` 到 CSV ——
///      分栏宽度是「detail 还在不在树上」的现场证人，用来把「内容跳变」与「窗口变窄」分开。
///
/// 默认 skip（会把产品窗口摆到屏幕上，不进 CI）；开法见 `scripts/real_screen_fold_transition.py`。
@MainActor
final class RealScreenFoldTransitionTests: XCTestCase {
    private static let rectKey = "R552_RECT_FILE"
    private static let ticksKey = "R552_TICKS_FILE"
    private static let goKey = "R552_GO_FILE"

    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!
    private var savedReduceOverride: Bool?
    private var savedAnimationsEnabled: Bool?
    private var savedDetailContentTopInset: CGFloat?

    private func setUpProduct() {
        savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        defaults = UserDefaults(suiteName: "r552-realscreen-\(UUID().uuidString)")!
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
                    content: .text("折叠真机取证条目 \(index) abcdefghijklmnop"),
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
        for window in NSApplication.shared.windows.filter({ WindowManager.isAppContentWindow($0) }) {
            window.delegate = nil
            window.orderOut(nil)
        }
        WindowManager.forgetMainWindowForTesting()
        WindowManager.uninstallMainWindowFactoryForTesting()
        if let savedDetailContentTopInset {
            WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedDetailContentTopInset)
        }
        delegate = nil
        store = nil
        controller = nil
        defaults = nil
    }

    private func spin(_ seconds: TimeInterval) {
        RunLoop.current.run(until: Date().addingTimeInterval(seconds))
    }

    /// 分栏各列宽：detail 在树上时是「侧栏宽, 详情宽」，折叠后 NavigationSplitView 整个不渲染。
    private static func splitColumnWidths(in window: NSWindow) -> [CGFloat] {
        guard let root = window.contentView, let split = firstSplitView(in: root) else { return [] }
        return split.subviews.map { $0.frame.width }
    }

    private static func firstSplitView(in view: NSView) -> NSSplitView? {
        if let split = view as? NSSplitView { return split }
        for child in view.subviews {
            if let found = firstSplitView(in: child) { return found }
        }
        return nil
    }

    func testRecordRealWindowFoldTransition() throws {
        let env = ProcessInfo.processInfo.environment
        guard env["CLIPBOARD_HISTORY_REALSCREEN_FOLD"] != nil else {
            throw XCTSkip("REALSCREEN_FOLD_NOT_RUN=env（默认 skip：会把产品窗口摆上屏幕）")
        }
        let rectPath = env[Self.rectKey] ?? "/tmp/r552-fold-rect.txt"
        let ticksPath = env[Self.ticksKey] ?? "/tmp/r552-fold-ticks.csv"
        let goPath = env[Self.goKey] ?? "/tmp/r552-fold-go"
        try? FileManager.default.removeItem(atPath: rectPath)
        try? FileManager.default.removeItem(atPath: ticksPath)
        try? FileManager.default.removeItem(atPath: goPath)

        setUpProduct()
        defer { tearDownProduct() }
        guard let screen = NSScreen.main else {
            try? "NO_SCREEN".write(toFile: rectPath, atomically: true, encoding: .utf8)
            return XCTFail("REALSCREEN_FOLD_NOT_RUN=no-screen ⇒ 这一格是没跑，不是通过")
        }
        WindowManager.showMainWindow(creatingIfNeeded: true)
        spin(0.6)
        guard let window = NSApplication.shared.windows.first(where: { WindowManager.isAppContentWindow($0) }) else {
            try? "NO_WINDOW".write(toFile: rectPath, atomically: true, encoding: .utf8)
            return XCTFail("REALSCREEN_FOLD_NOT_RUN=no-window ⇒ 主窗口没摆上屏幕")
        }
        var frame = window.frame
        frame.size.width = MainWindowCollapsePolicy.expandedWidthDefault
        frame.size.height = 492
        frame.origin.x = max(screen.visibleFrame.minX + 20, 120)
        frame.origin.y = screen.visibleFrame.maxY - frame.height - 40
        window.setFrame(frame, display: false)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        spin(0.8)

        // 矩形由被测物自己印：Swift 的左下原点 → 屏幕的左上原点（pt）。
        // 第二行给**屏幕本身的 pt 尺寸** —— 录像的像素尺寸 ÷ 它 = 这台机器的倍率，
        // 写死 2.0 会在外接非 Retina 屏上把尺的坐标整体算错（R495 那一族：探针落点漂到别人身上）。
        let rectLine = "\(Int(window.frame.minX)),\(Int(screen.frame.height - window.frame.maxY)),"
            + "\(Int(window.frame.width)),\(Int(window.frame.height))"
        let screenLine = "screen=\(Int(screen.frame.width))x\(Int(screen.frame.height))"
        try (rectLine + "\n" + screenLine).write(toFile: rectPath, atomically: true, encoding: .utf8)
        CaptureReadings.emit("REALSCREEN_FOLD rect=\(rectLine) \(screenLine) 等待外部录像")

        // 等 python 那边录像真的开跑（go 文件出现），再按固定节拍演两次。
        let goDeadline = Date().addingTimeInterval(30)
        while !FileManager.default.fileExists(atPath: goPath), Date() < goDeadline {
            spin(0.1)
        }
        guard FileManager.default.fileExists(atPath: goPath) else {
            return XCTFail("REALSCREEN_FOLD_NOT_RUN=no-go ⇒ 外部录像没起来，这一格不许算读过")
        }
        spin(0.6)

        var lines = ["t_ms,width,progress,isCollapsed,columns"]
        let start = Date()
        func tick() {
            let t = Int(Date().timeIntervalSince(start) * 1000)
            let cols = Self.splitColumnWidths(in: window).map { String(format: "%.0f", $0) }.joined(separator: "|")
            lines.append(String(format: "%d,%.1f,%.4f,%d,%@",
                                t, window.frame.width, controller.foldProgress,
                                controller.isCollapsed ? 1 : 0, cols.isEmpty ? "-" : cols))
        }
        func run(_ seconds: TimeInterval) {
            let deadline = Date().addingTimeInterval(seconds)
            repeat {
                tick()
                spin(0.006)
            } while Date() < deadline
        }

        run(0.5)
        delegate.perform(.toggleMainWindowCollapse)   // 折叠
        run(1.4)
        delegate.perform(.toggleMainWindowCollapse)   // 展开
        run(1.4)
        try lines.joined(separator: "\n").write(toFile: ticksPath, atomically: true, encoding: .utf8)

        let widths = lines.dropFirst().compactMap { $0.split(separator: ",").dropFirst().first.flatMap { Double($0) } }
        let distinct = Set(widths.map { Int($0.rounded()) }).count
        CaptureReadings.emit("REALSCREEN_FOLD ticks=\(lines.count - 1) 窗口宽档数=\(distinct) "
                             + "收尾折叠=\(controller.isCollapsed) 过渡中=\(controller.isTransitioning)")
        window.orderOut(nil)
    }
}
