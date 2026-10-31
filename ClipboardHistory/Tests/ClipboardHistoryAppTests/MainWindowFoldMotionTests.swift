import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R524：折叠/展开的过渡证人。两件事分开量：
/// 1. **真实窗口宽**：逐拍读 `window.frame.width`（控制器 60Hz 驱动，可中断、reduce 直切）；
/// 2. **过渡中间帧**：把 `ContentView` 按一组 `foldProgress` 离屏渲染成胶片，
///    证明中间帧既不是展开端点也不是折叠端点（不是"只拍端点两张"）。
@MainActor
final class MainWindowFoldMotionTests: XCTestCase {
    private var defaults: UserDefaults!
    private var store: HistoryStore!
    private var controller: MainWindowCollapseController!
    private var delegate: AppDelegate!
    private var savedReduceOverride: Bool?
    private var savedAnimationsEnabled: Bool?

    private func setUpProduct(_ name: String = UUID().uuidString) {
        defaults = UserDefaults(suiteName: "r524-fold-\(name)")!
        defaults.removePersistentDomain(forName: "r524-fold-\(name)")
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
                    content: .text("折叠胶片条目 \(index) abcdefghijklmnop"),
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
        WindowManager.showMainWindow()
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

    private func sampleTransition(seconds: TimeInterval = 0.7) -> [(width: CGFloat, progress: Double)] {
        var samples: [(width: CGFloat, progress: Double)] = []
        let deadline = Date().addingTimeInterval(seconds)
        while Date() < deadline {
            if let window = WindowManager.currentMainWindow {
                samples.append((window.frame.width, controller.foldProgress))
            }
            RunLoop.current.run(until: Date().addingTimeInterval(0.008))
            if samples.count > 3, !controller.isTransitioning { break }
        }
        return samples
    }

    private func waitForSettled() {
        let deadline = Date().addingTimeInterval(1.2)
        while controller.isTransitioning, Date() < deadline {
            RunLoop.current.run(until: Date().addingTimeInterval(0.01))
        }
        XCTAssertFalse(controller.isTransitioning, "过渡没有收尾 ⇒ 留下半折状态")
        settle(0.03)
    }

    func testCollapseWidthIsMeasuredFrameByFrame() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }

        delegate.perform(.toggleMainWindowCollapse)
        let samples = sampleTransition()
        waitForSettled()

        let widths = samples.map(\.width)
        let progress = samples.map(\.progress)
        let intermediate = widths.filter { $0 > 421 && $0 < 749 }
        let distinct = Set(intermediate.map { Int($0.rounded()) })
        let progressIntermediate = progress.filter { $0 > 0.02 && $0 < 0.98 }
        XCTAssertGreaterThanOrEqual(intermediate.count, 3,
                                    "折叠途中只读到 \(intermediate.count) 帧中间宽 ⇒ 是跳变不是过程：\(widths)")
        XCTAssertGreaterThanOrEqual(distinct.count, 3, "中间宽只有 \(distinct.count) 个不同值：\(widths)")
        for pair in zip(widths, widths.dropFirst()) {
            XCTAssertLessThanOrEqual(pair.1, pair.0 + 1.0,
                                     "折叠宽度不单调：\(pair.0) → \(pair.1)")
        }
        XCTAssertEqual(widths.first ?? 0, 750, accuracy: 1.0, "过渡不是从展开宽开始")
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0, "折叠没有落到 420")
        XCTAssertEqual(window.minSize.width, 360, accuracy: 0.5, "折叠后最小宽没有跟着切")
        XCTAssertGreaterThanOrEqual(progressIntermediate.count, 3,
                                    "foldProgress 中间帧不足：\(progress)")
        XCTAssertEqual(progress.last ?? 0, 1, accuracy: 0.001)
        print("FOLD_WIDTH_FILM collapse frames=\(samples.count)"
              + " intermediate=\(intermediate.count) distinct=\(distinct.count)"
              + " widths=[\(widths.map { String(format: "%.0f", $0) }.joined(separator: ","))]"
              + " progress=[\(progress.map { String(format: "%.2f", $0) }.joined(separator: ","))]"
              + " final=\(Int(window.frame.width)) min=\(Int(window.minSize.width))")
    }

    func testExpandWidthIsMeasuredFrameByFrame() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }
        delegate.perform(.toggleMainWindowCollapse)
        waitForSettled()
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0)

        delegate.perform(.toggleMainWindowCollapse)
        let samples = sampleTransition()
        waitForSettled()
        let widths = samples.map(\.width)
        let intermediate = widths.filter { $0 > 421 && $0 < 749 }
        XCTAssertGreaterThanOrEqual(intermediate.count, 3,
                                    "展开途中只读到 \(intermediate.count) 帧中间宽：\(widths)")
        for pair in zip(widths, widths.dropFirst()) {
            XCTAssertGreaterThanOrEqual(pair.1, pair.0 - 1.0,
                                        "展开宽度不单调：\(pair.0) → \(pair.1)")
        }
        XCTAssertEqual(window.frame.width, 750, accuracy: 1.0, "展开没有回到 750")
        XCTAssertEqual(window.minSize.width, 600, accuracy: 0.5)
        print("FOLD_WIDTH_FILM expand frames=\(samples.count)"
              + " intermediate=\(intermediate.count)"
              + " widths=[\(widths.map { String(format: "%.0f", $0) }.joined(separator: ","))]"
              + " final=\(Int(window.frame.width))")
    }

    func testReduceMotionCutsInstantly() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        MotionCatalog.overrideReduceMotion = true
        guard let window = makeWindow(width: 750) else { return }

        delegate.perform(.toggleMainWindowCollapse)
        settle(0.05)
        XCTAssertFalse(controller.isTransitioning, "reduce 下仍开了过渡计时器")
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0, "reduce 下不是 0 时长直切")
        XCTAssertEqual(controller.foldProgress, 1, accuracy: 0.001)
        XCTAssertEqual(window.minSize.width, 360, accuracy: 0.5)
        print("FOLD_REDUCE instant width=\(Int(window.frame.width)) progress=\(controller.foldProgress)"
              + " transitioning=\(controller.isTransitioning)")
    }

    func testInterruptingMidFoldReversesWithoutHalfState() {
        setUpProduct()
        defer { tearDownProduct() }
        retireAllMainWindows()
        guard let window = makeWindow(width: 750) else { return }

        delegate.perform(.toggleMainWindowCollapse)
        let deadline = Date().addingTimeInterval(0.5)
        while controller.foldProgress < 0.2, Date() < deadline {
            RunLoop.current.run(until: Date().addingTimeInterval(0.005))
        }
        XCTAssertGreaterThanOrEqual(controller.foldProgress, 0.2, "没能在中途截到过渡")
        XCTAssertTrue(controller.isTransitioning)
        delegate.perform(.toggleMainWindowCollapse) // 反向
        let samples = sampleTransition()
        waitForSettled()

        XCTAssertFalse(controller.isCollapsed)
        XCTAssertEqual(window.frame.width, 750, accuracy: 1.0, "反向结束后没有回到展开宽")
        XCTAssertEqual(controller.foldProgress, 0, accuracy: 0.001)
        let widths = samples.map(\.width)
        XCTAssertTrue(widths.allSatisfy { $0 >= 419 && $0 <= 751 },
                      "中途出现过越界宽度（半折留痕）：\(widths)")
        // 再折一次仍能收口
        delegate.perform(.toggleMainWindowCollapse)
        waitForSettled()
        XCTAssertEqual(window.frame.width, 420, accuracy: 1.0, "反向后再折没有落到 420")
        print("FOLD_INTERRUPT widths=[\(widths.map { String(format: "%.0f", $0) }.joined(separator: ","))]"
              + " final=\(Int(window.frame.width))")
    }

    func testFoldProgressDrivesContentOpacityAndHinge() {
        XCTAssertEqual(MainWindowCollapsePolicy.expandedContentOpacity(foldProgress: 0), 1, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.expandedContentOpacity(foldProgress: 0.5), 0.5, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.expandedContentOpacity(foldProgress: 1), 0, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.collapsedContentOpacity(foldProgress: 0), 0, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.collapsedContentOpacity(foldProgress: 1), 1, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.hingeOpacity(foldProgress: 0), 0, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.hingeOpacity(foldProgress: 0.5), 1, accuracy: 0.001)
        XCTAssertEqual(MainWindowCollapsePolicy.hingeOpacity(foldProgress: 1), 0, accuracy: 0.001)
        XCTAssertGreaterThan(MainWindowCollapsePolicy.hingeOpacity(foldProgress: 0.25), 0.5,
                             "中缝阴影在中段不够可见")
    }

    /// 过渡中间帧：按 0/0.25/0.5/0.75/1 渲染真正的 `ContentView` 并落盘。
    /// 判据是"中间帧既不是展开端点、也不是折叠端点"，不是只看两端的差。
    func testFoldFilmstripRendersIntermediateProgressFrames() throws {
        setUpProduct()
        defer { tearDownProduct() }
        let progressValues: [Double] = [0, 0.25, 0.5, 0.75, 1]
        let outDir = URL(fileURLWithPath: ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"]
                         ?? "/tmp/r524_fold_film", isDirectory: true)
        try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

        var reps: [Double: NSBitmapImageRep] = [:]
        for progress in progressValues {
            let view = ContentView(historyStore: store,
                                   isCollapsed: progress >= 1,
                                   foldProgress: progress)
                .frame(width: 750, height: 560)
            let host = NSHostingView(rootView: view)
            host.frame = NSRect(x: 0, y: 0, width: 750, height: 560)
            let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 750, height: 560),
                                  styleMask: .borderless,
                                  backing: .buffered,
                                  defer: false)
            window.contentView = host
            host.layoutSubtreeIfNeeded()
            settle(0.12)
            guard let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) else {
                return XCTFail("progress=\(progress) 读不回帧")
            }
            host.cacheDisplay(in: host.bounds, to: rep)
            reps[progress] = rep
            if let png = rep.representation(using: .png, properties: [:]) {
                try png.write(to: outDir.appendingPathComponent(
                    "fold-progress-\(Int(progress * 100))-750x560.png"))
            }
        }
        guard let expanded = reps[0], let collapsed = reps[1] else { return XCTFail("缺端点帧") }
        func differingPixels(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Int {
            guard let ab = a.bitmapData, let bb = b.bitmapData,
                  a.pixelsWide == b.pixelsWide, a.pixelsHigh == b.pixelsHigh else { return -1 }
            var count = 0
            let total = a.pixelsWide * a.pixelsHigh
            for i in 0..<total {
                let offset = i * 4
                if abs(Int(ab[offset]) - Int(bb[offset])) > 8
                    || abs(Int(ab[offset + 1]) - Int(bb[offset + 1])) > 8
                    || abs(Int(ab[offset + 2]) - Int(bb[offset + 2])) > 8 {
                    count += 1
                }
            }
            return count
        }
        var intermediateDiffs: [String] = []
        for progress in [0.25, 0.5, 0.75] {
            guard let rep = reps[progress] else { return XCTFail("缺 \(progress) 帧") }
            let diffFromExpanded = differingPixels(rep, expanded)
            let diffFromCollapsed = differingPixels(rep, collapsed)
            XCTAssertGreaterThan(diffFromExpanded, 2000,
                                 "p=\(progress) 与展开端点几乎相同 ⇒ 这一帧没有过渡内容")
            XCTAssertGreaterThan(diffFromCollapsed, 2000,
                                 "p=\(progress) 与折叠端点几乎相同 ⇒ 这一帧没有过渡内容")
            intermediateDiffs.append("p\(progress)=\(diffFromExpanded)/\(diffFromCollapsed)")
        }
        print("FOLD_FILM frames=\(progressValues.count) dir=\(outDir.path)"
              + " intermediateDiffs=\(intermediateDiffs.joined(separator: ";"))"
              + " hinge=\(progressValues.map { String(format: "%.2f", MainWindowCollapsePolicy.hingeOpacity(foldProgress: $0)) }.joined(separator: ","))")
    }
}
