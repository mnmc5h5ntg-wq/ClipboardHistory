import AppKit
import ApplicationServices
import QuartzCore
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 在屏交互探针（审计第二轮 `probes/UIInteractionAuditTests.swift` 收进仓库的版本）。
///
/// 为什么进仓库：上一轮这些证据只存在于审计方的 `/tmp` 里，仓库自己无法复跑，
/// 于是"键盘焦点不达标""60fps 达标"这类结论只能靠引用别人的日志。收进来之后，
/// 任何一次 UI 改动都能用同一条命令重新量一遍。
///
/// **默认跳过**：只有在 `CLIPBOARD_HISTORY_UI_INTERACTION=1` 时才真的开窗
/// （`CLIPBOARD_HISTORY_UI_SHOTS` 另可指定帧输出目录）。原因是它会
/// `NSApp.activate` 抢前台、在屏上画窗口，放进 CI 或普通 `swift test` 会干扰用户，
/// 而且帧率数字与机器负载强相关，不适合当远端闸门。
///
/// 数据安全：store 一律用 `RecordingHistoryPersistence` + `TestClipboardWriter`，
/// 从不调 `startMonitoring()`，因此既不读也不写 `~/Library/Application Support/时间剪史/`（D-002）。
@MainActor
final class UIInteractionProbeTests: XCTestCase {
    private static let isEnabled = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_INTERACTION"] == "1"

    private func skipUnlessEnabled() throws {
        try XCTSkipUnless(Self.isEnabled,
                          "在屏交互探针：设 CLIPBOARD_HISTORY_UI_INTERACTION=1 才跑（会抢前台并开窗）")
    }

    private func syntheticStore() -> HistoryStore {
        let entryCount = Int(ProcessInfo.processInfo.environment["UI_AUDIT_ENTRIES"] ?? "60") ?? 60
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 500, maxAgeDays: nil)
        )
        let image = (try? makeStoredImage(color: .systemTeal, size: NSSize(width: 240, height: 140)))
        for index in 0..<entryCount {
            store.add(ClipboardIntake.Entry(
                content: .text("记录 \(index)：用于帧率与键盘取证的一段普通文本，长度适中 abcdefghij"),
                thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"),
                timestamp: Date().addingTimeInterval(-Double(index) * 30))
        }
        if let image {
            store.add(ClipboardIntake.Entry(
                content: .image(image), thumbnail: image, sourceUTIs: ["public.png"],
                sourceAppBundleID: "com.apple.Preview", sourceAppName: "预览"),
                timestamp: Date().addingTimeInterval(-5))
        }
        return store
    }

    private func makeWindow(width: CGFloat, height: CGFloat, origin: CGPoint, store: HistoryStore) -> (NSWindow, NSHostingView<ContentView>) {
        let window = NSWindow(
            contentRect: NSRect(origin: origin, size: NSSize(width: width, height: height)),
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )
        let host = NSHostingView(rootView: ContentView(historyStore: store))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        RunLoop.main.run(until: Date().addingTimeInterval(0.4))
        return (window, host)
    }

    // MARK: - 键盘焦点链

    /// 审计第二轮实测：连按 14 次 `selectNextKeyView`，第一响应者 14 次都是同一个 `NSTextView`
    /// （详情的文本视图），搜索框/筛选/行/浮层按钮一个都进不了焦点环。
    /// 这里把那条观察变成**判据**：焦点链必须能走到详情文本视图以外的控件，
    /// 并且必须走到搜索框（`NSTextField`/其 field editor）。
    func testFocusChainReachesTheSearchFieldAndNotOnlyTheDetailTextView() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        let (window, host) = makeWindow(width: 800, height: 600, origin: CGPoint(x: 240, y: 240), store: store)
        defer { window.orderOut(nil) }

        var chain: [String] = []
        window.makeFirstResponder(host)
        for step in 0..<14 {
            window.selectNextKeyView(nil)
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            let responder = window.firstResponder
            chain.append("\(step):\(responder.map { String(describing: type(of: $0)) } ?? "nil")")
        }
        print("FOCUS-CHAIN " + chain.joined(separator: " | "))

        // 第二条链：**合成真实 Tab 按键**（走 `NSApp.sendEvent`，即用户按键的通道）。
        // `selectNextKeyView` 只走 AppKit 的 key-view 环，而 SwiftUI 的焦点由它自己的引擎管，
        // 两者不一定一致 —— 只量前者有可能量错东西（本轮就出现过：改了焦点相关代码，
        // FOCUS-CHAIN 一个字都没变）。所以判据以真实按键这条链为准，前一条留作对照。
        var keyChain: [String] = []
        for step in 0..<8 {
            sendKey(keyCode: 48, window: window)   // 48 = Tab
            RunLoop.main.run(until: Date().addingTimeInterval(0.06))
            keyChain.append("\(step):\(describe(window.firstResponder))")
        }
        print("TAB-KEY-CHAIN " + keyChain.joined(separator: " | "))

        let keyKinds = Set(keyChain.map { $0.split(separator: ":").last.map(String.init) ?? "" })
        // 判据只钉"真实 Tab 能走到搜索框"这一条：它是可复现、可归因的。
        XCTAssertTrue(
            keyKinds.contains { $0.contains("fieldEditor") || $0.contains("TextField") },
            "真实 Tab 按键到不了搜索框（链：\(keyChain.joined(separator: " | "))）"
        )

        // Tab 走不到列表/按钮**不一定**是产品缺陷：macOS 的键盘访问模式决定 Tab 的范围
        // （AppleKeyboardUIMode = 0/缺省 时 Tab 只在文本框与列表之间走，按钮和 .focusable()
        // 的自绘视图根本不进环；= 3 即「完全键盘访问」才全走）。所以把这个模式一起打出来，
        // 否则"14 次 Tab 全在同一个控件"这种数字无法归因（审计第二轮 1.10 就缺这一栏）。
        let keyboardUIMode = UserDefaults(suiteName: "NSGlobalDomain")?.integer(forKey: "AppleKeyboardUIMode") ?? -1
        print("KEYBOARD-UIMODE \(keyboardUIMode)（0/缺省=Tab 只走文本框与列表，3=完全键盘访问）")
        print("TAB-KEY-KINDS \(keyKinds.sorted())")
        if keyKinds.count <= 1 {
            print("NOTE 真实 Tab 只停在一种控件上。若 KEYBOARD-UIMODE 不是 3，先开"
                + "「系统设置 → 键盘 → 完全键盘访问」再复测，不能据此判产品缺陷；"
                + "列表方向键导航由 SidebarKeyboardNavigationTests 与接线守卫覆盖")
        }

        let kinds = Set(chain.map { $0.split(separator: ":").last.map(String.init) ?? "" })
        if kinds.count <= 1 {
            print("NOTE AppKit key-view 环仍然只有一种第一响应者（\(kinds)）；"
                + "SwiftUI 焦点不走 nextKeyView，这一条只作对照，判据看 TAB-KEY-CHAIN")
        }

        try captureFocusFrames(window: window)
    }

    /// 合成一次真实按键交给 `NSApp.sendEvent`（用户按键走的通道）。
    /// 不用 `CGEventPost`：那需要辅助功能授权，测试进程没有，硬发只会静默无效。
    private func sendKey(keyCode: UInt16, window: NSWindow, flags: NSEvent.ModifierFlags = []) {
        func event(_ type: NSEvent.EventType) -> NSEvent? {
            NSEvent.keyEvent(
                with: type,
                location: .zero,
                modifierFlags: flags,
                timestamp: ProcessInfo.processInfo.systemUptime,
                windowNumber: window.windowNumber,
                context: nil,
                characters: "",
                charactersIgnoringModifiers: "",
                isARepeat: false,
                keyCode: keyCode
            )
        }
        guard let down = event(.keyDown) else { return }
        NSApp.sendEvent(down)
        guard let up = event(.keyUp) else { return }
        NSApp.sendEvent(up)
    }

    /// 第一响应者的可读描述：必须区分"搜索框的 field editor"和"详情那个 NSTextView"，
    /// 否则两者都打印成 `NSTextView`，看不出焦点到底在哪（第一版就是这么被骗的）。
    private func describe(_ responder: NSResponder?) -> String {
        guard let responder else { return "nil" }
        if let textView = responder as? NSTextView {
            return textView.isFieldEditor ? "NSTextView(fieldEditor)" : "NSTextView"
        }
        return String(describing: type(of: responder))
    }

    private func captureFocusFrames(window: NSWindow) throws {        let path = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"] ?? "/tmp/shots-focus"
        let directory = URL(fileURLWithPath: path, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        for dark in [true, false] {
            try capture(window: window,
                        to: directory.appendingPathComponent(dark ? "focus-after-tab-dark.png" : "focus-after-tab-light.png"),
                        dark: dark)
        }
    }

    // MARK: - 帧间隔

    private final class FrameMeter: NSObject {
        var deltas: [Double] = []
        private var last: CFTimeInterval = 0
        private var link: CADisplayLink?

        func start() {
            guard let screen = NSScreen.main else { return }
            let link = screen.displayLink(target: self, selector: #selector(tick(_:)))
            link.add(to: .main, forMode: .common)
            self.link = link
        }

        @objc func tick(_ link: CADisplayLink) {
            if last > 0 { deltas.append(link.timestamp - last) }
            last = link.timestamp
        }

        func stop() {
            link?.invalidate()
            link = nil
        }

        func stats() -> (p50: Double, p95: Double, worst: Double, over16: Int, over33: Int, n: Int) {
            let sorted = deltas.sorted()
            guard !sorted.isEmpty else { return (0, 0, 0, 0, 0, 0) }
            func q(_ fraction: Double) -> Double {
                sorted[min(sorted.count - 1, Int(Double(sorted.count) * fraction))]
            }
            return (q(0.5) * 1000, q(0.95) * 1000, (sorted.last ?? 0) * 1000,
                    sorted.filter { $0 > 0.0167 }.count, sorted.filter { $0 > 0.0334 }.count, sorted.count)
        }
    }

    /// 在真实在屏窗口里驱动状态变化（每 100ms 一次选择/搜索/筛选/多选），量帧间隔。
    /// 审计第二轮的结论是 p95 恒为 16.67ms（60fps 达标），500 条时 worst 56ms。
    /// 上界写得比实测宽（p95 ≤ 20ms、worst ≤ 120ms）：这是本机探针，负载受机器影响，
    /// 宁可留余量也不要变成"环境吵就红"的假闸门。
    func testFrameIntervalsUnderStateChanges() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        let (window, _) = makeWindow(width: 900, height: 640, origin: CGPoint(x: 200, y: 200), store: store)
        defer { window.orderOut(nil) }

        let meter = FrameMeter()
        meter.start()
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        let baseline = meter.stats()

        var phase = 0
        let deadline = Date().addingTimeInterval(3.2)
        var nextStep = Date()
        while Date() < deadline {
            if Date() >= nextStep {
                let count = max(store.entries.count, 1)
                switch phase % 4 {
                case 0: store.perform(.select(store.entries[phase % count]))
                case 1: store.perform(.updateSearch(phase % 2 == 0 ? "记录 3" : ""))
                case 2: store.perform(.updateFilter(phase % 4 == 2 ? .favorites : .all))
                default: store.perform(.toggleSelection(store.entries[phase % count]))
                }
                phase += 1
                nextStep = Date().addingTimeInterval(0.1)
            }
            RunLoop.main.run(until: Date().addingTimeInterval(0.008))
        }
        let loaded = meter.stats()
        meter.stop()

        print("FPS-BASELINE n=\(baseline.n) p50=\(String(format: "%.2f", baseline.p50))ms p95=\(String(format: "%.2f", baseline.p95))ms worst=\(String(format: "%.1f", baseline.worst))ms >16.7ms:\(baseline.over16) >33.4ms:\(baseline.over33)")
        print("FPS-LOADED entries=\(store.entries.count) n=\(loaded.n) p50=\(String(format: "%.2f", loaded.p50))ms p95=\(String(format: "%.2f", loaded.p95))ms worst=\(String(format: "%.1f", loaded.worst))ms >16.7ms:\(loaded.over16) >33.4ms:\(loaded.over33)")

        XCTAssertGreaterThan(loaded.n, 60, "帧样本太少，结论无效")
        XCTAssertLessThanOrEqual(loaded.p95, 20, "p95 帧间隔超过 20ms：60fps 目标未达")
        XCTAssertLessThanOrEqual(loaded.worst, 120, "最差帧超过 120ms：有卡顿级掉帧")
    }

    // MARK: - 无障碍树

    /// 无障碍树遍历。xctest 进程里 `AXUIElementCreateApplication(getpid())` 常常返回 0 个窗口
    /// （审计第二轮实测 `AX-VISITED 0`），那是环境限制而不是产品缺陷 —— 所以这里**跳过而不是失败**，
    /// 并把数字打出来：树建起来了就顺带统计"无名称的可交互元素"。
    func testAccessibilityTreeCoverage() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        let (window, _) = makeWindow(width: 800, height: 600, origin: CGPoint(x: 280, y: 280), store: store)
        defer { window.orderOut(nil) }

        var visited = 0
        var interactive = 0
        var unnamedInteractive: [String] = []
        var roles: [String: Int] = [:]

        func attribute(_ element: AXUIElement, _ name: String) -> String {
            var value: AnyObject?
            guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return "" }
            return (value as? String) ?? ""
        }
        func visit(_ element: AXUIElement, depth: Int) {
            visited += 1
            let role = attribute(element, kAXRoleAttribute as String)
            roles[role, default: 0] += 1
            let interactiveRoles = ["AXButton", "AXTextField", "AXCheckBox", "AXSlider", "AXRow", "AXLink", "AXMenuItem"]
            if interactiveRoles.contains(role) {
                interactive += 1
                let hasName = [kAXTitleAttribute, kAXDescriptionAttribute, kAXHelpAttribute]
                    .contains { !attribute(element, $0 as String).isEmpty }
                if !hasName {
                    unnamedInteractive.append("\(role)#\(visited)")
                }
            }
            if depth < 12 {
                var childrenValue: AnyObject?
                if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &childrenValue) == .success,
                   let children = childrenValue as? [AXUIElement] {
                    for child in children { visit(child, depth: depth + 1) }
                }
            }
        }

        let application = AXUIElementCreateApplication(getpid())
        var windowsValue: AnyObject?
        if AXUIElementCopyAttributeValue(application, kAXWindowsAttribute as CFString, &windowsValue) == .success,
           let windows = windowsValue as? [AXUIElement] {
            for element in windows { visit(element, depth: 0) }
        }
        print("AX-VISITED \(visited) interactive=\(interactive) unnamed=\(unnamedInteractive.count) roles=\(roles.sorted { $0.value > $1.value }.prefix(8))")
        print("AX-UNNAMED \(unnamedInteractive.prefix(20).joined(separator: ","))")

        try XCTSkipIf(visited <= 1,
                      "本进程拿不到无障碍树（AX-VISITED \(visited)）：这是 xctest 的环境限制，不能据此判产品缺陷")
        XCTAssertEqual(unnamedInteractive.count, 0,
                       "有无名称的可交互元素：\(unnamedInteractive.joined(separator: ","))")
    }

    // MARK: - 行内手势（双击复制 / 点星标收藏）

    // MARK: - 行内手势（D-1 之后）

    /// 原来这里有一条 `testRowGesturesFireTheRightActions`：把孤立的一行放进
    /// `NSHostingView`，用合成点击验"单击选中 / 双击复制 / 点星标收藏"。
    /// D-1 的修法③把行里的 `Button` 去掉了（选中态归 `List`），于是这一行里
    /// **没有可命中测试的控件**，合成事件送不进去（实测星标代理还在、点它 favoriteFired 仍为 0）。
    /// 判据不能伪造成"绿"，所以这三件事改成：接线由源码守卫钉（`SidebarListSelectionTests`）、
    /// 结构由表格判据钉（下一条）、真机行为进手工清单第 1 节。

    /// D-1 之后唯一的在屏列表探针：把**整条侧栏**摆上屏，行几何向 `NSTableView` 问。
    /// 它钉得住的是结构（真表格、可多选、行数=可见条目数），
    /// 点/双击/拖选的实际后果在当前合成事件下只能观测（原因见上面那段注释与 D-033）。
    func testRowGesturesWorkInsideTheRealSidebarContainer() throws {
        try skipUnlessEnabled()
        let writer = TestClipboardWriter()
        let store = HistoryStore(
            clipboardWriter: writer,
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        for index in 0..<6 {
            store.add(ClipboardIntake.Entry(
                content: .text("侧栏里的第 \(index) 条记录"), thumbnail: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            ), timestamp: Date().addingTimeInterval(-Double(index) * 60))
        }

        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 240, y: 200, width: 320, height: 460),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))

        let mouse = MouseSynthesizer(window: window)

        // 行位置向表格问（见 `sidebarRowPoints` 的注释）。
        let rows = try sidebarRowPoints(in: host, count: 6)
        let lastRow = rows[rows.count - 1]
        let firstRow = rows[0]
        emit("TREE2 行矩形=\(rows.count) 收藏前=\(store.entries.filter(\.isFavorite).count) "
            + "写入=\(writer.writtenContents.count) 首行=\(NSStringFromPoint(firstRow.body)) "
            + "末行=\(NSStringFromPoint(lastRow.body))")

        // 自动化能钉住的那一半：列表是**真的多选表格**，而且行数是可见条目数 ——
        // 这就是 D-1 之后"拖选归系统、拖出归把手"的结构前提。行不再挂 `.onDrag` 由
        // `SidebarListSelectionTests.testDragAffordanceLivesOnlyOnTheHandle` 钉。
        let table = try XCTUnwrap(Self.firstTable(in: host))
        XCTAssertTrue(table.allowsMultipleSelection,
                      "`List(selection:)` 没开出多选 ⇒ shift/⌘/拖选都不可能出现")
        XCTAssertEqual(table.numberOfRows, store.filteredEntries.count,
                       "表格行数与可见条目数不一致：列表绑错了数据源")

        // 另一半只能观测：合成鼠标事件驱动不了 AppKit 表格的行选中（本轮实测：
        // 按下-拖动-抬起三段都投了，选中集纹丝不动；把 eventNumber 换成每段递增值也一样）。
        // 所以"真点一行会不会选中/双击会不会复制/拖选会不会扩"这三条走手工清单，
        // 记在 D-033 与 docs/MANUAL_TEST_v1.4.9_round3.md，不伪装成自动化结论。
        let selectedBefore = store.selectedEntry?.id
        let favoriteBefore = store.entries.filter(\.isFavorite).count
        let writesBefore = writer.writtenContents.count
        mouse.click(at: lastRow.body)
        mouse.click(at: lastRow.body, clickCount: 2)
        mouse.click(at: lastRow.leading)
        mouse.drag(from: firstRow.body, through: [rows[1].body, rows[2].body], to: rows[3].body)
        emit("OBSERVE 点/双击/星标/拖选之后：选中变化=\(store.selectedEntry?.id != selectedBefore) "
            + "选中数=\(store.selectedCount) 收藏+\(store.entries.filter(\.isFavorite).count - favoriteBefore) "
            + "复制+\(writer.writtenContents.count - writesBefore) lastClick=\(NSStringFromPoint(mouse.lastClickPoint))")
        // 归因用的一行：`clickedRow` 是 -1 说明事件根本没送到表格（探针限制）；
        // `clickedRow` 有值而 store 没变说明是**产品的绑定断了**（那是缺陷，不是限制）。
        emit("OBSERVE-TABLE clickedRow=\(table.clickedRow) selectedRow=\(table.selectedRow) "
            + "selectedRows=\(table.selectedRowIndexes) isKeyWindow=\(window.isKeyWindow) "
            + "isActive=\(NSApp.isActive) anchor=\(NSStringFromPoint(lastRow.body))")
    }

    /// D-1 的验收本体：**从第 1 行按下、拖到第 4 行，选中集必须扩到 4 行**。
    ///
    /// 审计给的验收是"真机 2 分钟"。合成事件能做到的是把 down / dragged…/ up 三段真的投进
    /// 那扇在屏窗口的真实列表里，再看 store 的选中集合 —— 这与"整行挂 onDrag 时拖选失效"
    /// 是可区分的形状：争用发生时选中集只会停在按下那一行。
    /// 行 y 坐标**取自每行的星标代理**（每行恰好一个 20×20），不靠"行高应该是多少"猜 ——
    /// 这一族探针已经两次因为按猜的几何点而误报产品缺陷。
    func testDragSelectExpandsSelectionInsideTheRealList() throws {
        try skipUnlessEnabled()
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        for index in 0..<8 {
            store.add(ClipboardIntake.Entry(
                content: .text("拖选探针第 \(index) 条记录"), thumbnail: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            ), timestamp: Date().addingTimeInterval(-Double(index) * 60))
        }
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 240, y: 200, width: 320, height: 460),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))

        let mouse = MouseSynthesizer(window: window)
        let rows = try sidebarRowPoints(in: host, count: 4)
        let table = try XCTUnwrap(Self.firstTable(in: host))
        emit("DRAGSELECT 行矩形=\(rows.count) 首行 body=\(NSStringFromPoint(rows[0].body))")

        let before = store.selectedCount
        mouse.drag(from: rows[0].body, through: [rows[1].body, rows[2].body], to: rows[3].body)
        emit("DRAGSELECT 拖之后选中=\(store.selectedCount) clickedRow=\(table.clickedRow) "
            + "selectedRows=\(table.selectedRowIndexes)")

        // 判据是**有条件的**：表格收到了这一下（clickedRow 不是 -1）才谈产品；
        // 没收到就是合成事件的限制，不许拿它判缺陷，也不许悄悄 skip 到看不见 ——
        // 限制本身要打印出来并写进手工清单。
        if table.clickedRow < 0 && store.selectedCount == before {
            emit("DRAGSELECT-LIMIT 合成拖动没有送到 NSTableView（clickedRow=-1），"
                 + "这条验收改由人工：真机在含 5 条文本的列表里从第 1 行按下拖到第 4 行，选中集应扩到 4 行")
            throw XCTSkip("合成鼠标事件驱动不了表格行选中（本轮实测），见 D-033 与手工清单第 2 节")
        }
        XCTAssertGreaterThanOrEqual(store.selectedCount, 4,
                                   "从第 1 行按下拖到第 4 行，选中集只扩到 \(store.selectedCount) 行 —— "
                                   + "这正是 D-1 的形状：拖出会话在阈值处抢走了这次拖动")
    }

    /// 用户报的现象：双击列表里的条目之后，整个左侧列表外面多了一圈蓝色边框。
    /// 那是 `.focusable()` 让列表容器成为 key view 后，AppKit 给它画的**系统焦点环**。
    /// 这条探针把"环在不在"变成一个可打印、可断言的量：沿第一响应者往上读 `focusRingType`。
    func testSidebarListFocusRingAfterClick() throws {
        try skipUnlessEnabled()
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        for index in 0..<6 {
            store.add(ClipboardIntake.Entry(
                content: .text("焦点环探针第 \(index) 条"), thumbnail: nil,
                sourceUTIs: ["public.utf8-plain-text"]
            ), timestamp: Date().addingTimeInterval(-Double(index) * 60))
        }
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 240, y: 200, width: 320, height: 460),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))

        // 点一行（走的是真实点击路径，和双击时容器拿到焦点是同一件事）。
        var rowProxies: [NSView] = []
        func walk(_ view: NSView) {
            if String(describing: type(of: view)) == "KeyViewProxy",
               view.frame.width > 200, view.frame.width < 290, view.frame.minX > 30, view.frame.height < 40 {
                rowProxies.append(view)
            }
            for sub in view.subviews { walk(sub) }
        }
        walk(host)
        guard let row = rowProxies.min(by: { $0.frame.minY < $1.frame.minY }) else {
            XCTFail("找不到行代理，探针无法点击")
            return
        }
        let windowPoint = row.convert(NSPoint(x: row.bounds.midX, y: row.bounds.midY), to: nil)
        func send(_ type: NSEvent.EventType) {
            if let event = NSEvent.mouseEvent(with: type, location: windowPoint, modifierFlags: [],
                                              timestamp: ProcessInfo.processInfo.systemUptime,
                                              windowNumber: window.windowNumber, context: nil,
                                              eventNumber: 0, clickCount: 1, pressure: 1.0) {
                NSApp.sendEvent(event)
            }
        }
        send(.leftMouseDown); send(.leftMouseUp)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))

        var chain: [String] = []
        var view = window.firstResponder as? NSView
        while let current = view {
            chain.append("\(type(of: current))=\(current.focusRingType.rawValue)")
            view = current === window.contentView ? nil : current.superview
        }
        print("FOCUSCHAIN-RING firstResponder=\(window.firstResponder.map { String(describing: type(of: $0)) } ?? "nil") "
            + "链(视图=focusRingType；0=none 1=default 2=around)：\(chain.joined(separator: " ← "))")

        // AppKit 的环这一路读出来是 .none ⇒ 那圈蓝框不是 AppKit 画的，是 SwiftUI 的 `_FocusRingView`。
        // 判据：点过一行之后，**不允许**存在覆盖整块列表的焦点环视图。
        // 实测（本机 macOS 27）：加 `focusEffectDisabled()` 之前共 15 个环视图，其中一个是列表整块
        // {{0,125},{320,335}} —— 正是用户看到的那圈蓝框；加上之后只剩 2 个，都是筛选 pill 自己的。
        var ringFrames: [NSRect] = []
        func collectRings(_ v: NSView) {
            if String(describing: type(of: v)).contains("FocusRing") { ringFrames.append(v.frame) }
            for sub in v.subviews { collectRings(sub) }
        }
        collectRings(host)
        let listSizedRings = ringFrames.filter {
            $0.width >= host.frame.width * 0.9 && $0.height > 200
        }
        print("RINGVIEWS 总数=\(ringFrames.count) 覆盖整块列表的=\(listSizedRings.map { NSStringFromRect($0) })")
        XCTAssertTrue(listSizedRings.isEmpty,
                      "列表容器上还挂着一圈覆盖整块列表的焦点环（用户要移除的蓝框）。"
                      + "如果这是在 macOS 13 及更早跑出来的：`focusEffectDisabled()` 需要 macOS 14+，那属于平台限制而不是回归。")
    }

    // MARK: - 右键菜单（issue #13）

    /// 用户那条路径上，AppKit 决定要弹的那份右键菜单长什么样（issue #13）。
    ///
    /// 三条实测结论决定了判据为什么长成这样：
    /// ① 编辑态下右键**不经过搜索框自己**：事件直接投给窗口共享的 field editor
    ///    （`NSTextView`，挂在 `_NSKeyboardFocusClipView` 下，`isDescendant(of: 搜索框) == true`）。
    ///    所以"用 `hitTest` 把右键让位给文本框"那套在这条路径上是走不到的分支 ——
    ///    拿它当判据只会测出一个**假缺陷**（本轮差点把探针的测不到当成产品坏）。
    /// ② 合成事件派发期间 `NSApp.currentEvent` 是 nil（HITTEST 日志逐条 nil），
    ///    任何"看当前事件类型"的分支都无法用合成事件验证。
    /// ③ 让它真弹起来也量不到：`popUpContextMenu` 是模态的，实测在 `didBeginTracking` 里调
    ///    `cancelTrackingWithoutAnimation()` **不能**让它返回（8 秒监视线程直接 exit(71)）。
    ///
    /// 所以仓库里的判据取 AppKit 决定"弹哪份菜单"的那个入口 —— `NSResponder.menu(for:)`：
    /// 右键要弹菜单时 AppKit 问的就是它。屏幕上真弹出来长什么样，留给手工清单核对。
    func testRightClickMenusAppKitWouldShowAreChinese() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        let (window, host) = makeWindow(width: 820, height: 600, origin: CGPoint(x: 200, y: 180), store: store)
        defer { window.orderOut(nil) }

        var fields: [ChineseMenuTextField] = []
        func walk(_ view: NSView) {
            if let field = view as? ChineseMenuTextField { fields.append(field) }
            for sub in view.subviews { walk(sub) }
        }
        walk(host)
        guard let search = fields.first else {
            XCTFail("窗口里找不到搜索框（ChineseMenuTextField），这条探针没测到东西")
            return
        }

        func send(_ type: NSEvent.EventType, to point: NSPoint, clicks: Int) {
            NSEvent.mouseEvent(with: type, location: point, modifierFlags: [],
                               timestamp: ProcessInfo.processInfo.systemUptime,
                               windowNumber: window.windowNumber, context: nil,
                               eventNumber: 0, clickCount: clicks, pressure: 1.0)
                .map { NSApp.sendEvent($0) }
        }
        let rightEvent = try XCTUnwrap(
            NSEvent.mouseEvent(with: .rightMouseDown, location: .zero, modifierFlags: [],
                               timestamp: ProcessInfo.processInfo.systemUptime,
                               windowNumber: window.windowNumber, context: nil,
                               eventNumber: 0, clickCount: 1, pressure: 1.0),
            "合成不了右键事件"
        )

        // 阳性对照：点击点得真的落在搜索框上（本轮已经踩过两次点错东西：筛选 pill 当成行、y 落在相邻行）。
        let frameInWindow = search.convert(search.bounds, to: nil)
        let center = NSPoint(x: frameInWindow.midX + 20, y: frameInWindow.midY)
        let hitChain = describeChain(host, at: center)
        emit("MENUS 搜索框(窗口坐标)=\(NSStringFromRect(frameInWindow)) 点击=\(NSStringFromPoint(center)) 命中链=\(hitChain)")
        XCTAssertTrue(hitChain.contains("ChineseMenuTextField"),
                      "点击点没命中搜索框（命中链：\(hitChain)），这条探针测不到右键菜单")

        // 真实左键进编辑态（makeFirstResponder 那条捷径不走用户那套路径）。
        send(.leftMouseDown, to: center, clicks: 1)
        send(.leftMouseUp, to: center, clicks: 1)
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        guard search.currentEditor() is NSTextView else {
            XCTFail("左键没能进入搜索框编辑态（editor=\(String(describing: search.currentEditor()))），右键那条路谈不上")
            return
        }

        // ① 编辑态：右键归共享 field editor，而它的 `menu`/`menu(for:)` 我们改不动
        //    （实测：挂上去会被 AppKit 复原；`menu(for:)` 每次现造一份新的）。
        //    所以这条判据量的是**拦截器**：事件是不是归我们、我们给出的是不是中文那六项。
        XCTAssertTrue(FieldEditorRightClickInterceptor.owns(event: rightEvent),
                      "编辑态右键没有被拦截器认领 —— 会弹 AppKit 那份系统菜单（issue #13 报的就是它）")
        // 反面对照：同一个拦截器在"不是我们的框在编辑"时必须放手，否则它会吞掉全 App 的右键。
        window.makeFirstResponder(host)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        XCTAssertFalse(FieldEditorRightClickInterceptor.owns(event: rightEvent),
                       "拦截器在搜索框没在编辑时也认领了右键 —— 那是把别人的菜单吞了")

        // 交付路径：装监视器 → 换掉真弹 → 投一个真实右键事件 → 看我们给出去的是哪份菜单。
        var presented: NSMenu?
        FieldEditorRightClickInterceptor.install()
        FieldEditorRightClickInterceptor.present = { _, _, menu in presented = menu }
        defer {
            FieldEditorRightClickInterceptor.uninstall()
            FieldEditorRightClickInterceptor.present = { view, event, menu in
                NSMenu.popUpContextMenu(menu, with: event, for: view)
            }
        }
        // 回到编辑态再投右键（第一响应者得是 field editor，拦截器才认领）。
        send(.leftMouseDown, to: center, clicks: 1)
        send(.leftMouseUp, to: center, clicks: 1)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        // 看门狗：拦截一旦断了，AppKit 会去弹它自己那份系统菜单 —— 那是**模态**的，
        // 实测取消不掉（`cancelTrackingWithoutAnimation` 也叫它不返回），探针就会挂住开发者的机器。
        // 变异实验（让 `handle` 不吞事件）正是这么挂住的，所以这条边界不是假设。
        let watchdog = PopupWatchdog()
        defer { watchdog.disarm() }
        watchdog.arm(after: 20, why: "拦截断了：AppKit 正在模态弹它自己那份 field editor 菜单")
        send(.rightMouseDown, to: center, clicks: 1)
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        watchdog.disarm()
        emit("MENUS 编辑态拦截器给出=\(presented.map { titles(of: $0) } ?? [])")
        let handedOver = try XCTUnwrap(
            presented,
            "装了监视器、投了右键，拦截器却没给出菜单 —— 要么 `addLocalMonitorForEvents` 看不到合成事件（那这条判据测不到，得改成手工核对），要么拦截路径断了"
        )
        assertChineseEditingMenu(handedOver, where: "编辑态拦截器给出的菜单")
        presented = nil

        // ② 非编辑态（还没进 field editor）时右键，AppKit 问的是文本框自己。
        window.makeFirstResponder(host)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        let fieldMenu = try XCTUnwrap(
            search.menu(for: rightEvent),
            "搜索框非编辑态的 menu(for:) 返回空 —— 用户右键会一个菜单都没有"
        )
        emit("MENUS 非编辑态 搜索框菜单=\(titles(of: fieldMenu)) plugIns=\(fieldMenu.allowsContextMenuPlugIns)")
        assertChineseEditingMenu(fieldMenu, where: "非编辑态的搜索框")

        // ③ 详情只读区：同一份判据。先选中一条，否则详情区是占位文案，压根没有文本视图。
        if let first = store.entries.first {
            store.perform(.selectOnly(first))
            RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        }
        var previews: [ChineseSelectableNSTextView] = []
        func walk2(_ view: NSView) {
            if let preview = view as? ChineseSelectableNSTextView { previews.append(preview) }
            for sub in view.subviews { walk2(sub) }
        }
        walk2(host)
        XCTAssertFalse(previews.isEmpty, "选中一条记录后详情区仍然没有只读文本视图 —— 这条判据没有对照物")
        for preview in previews {
            // 阳性对照：这个点得真的落在只读文本区上。取 visibleRect 而不是 bounds ——
            // 文本区可垂直缩放，bounds 可能比视口大得多，拿 bounds 的角去点会点到窗口外面。
            let visible = preview.visibleRect
            let previewPoint = preview.convert(
                NSPoint(x: visible.midX, y: visible.minY + min(20, visible.height / 2)),
                to: nil
            )
            let chain = describeChain(host, at: previewPoint)
            emit("MENUS 只读区 可见区=\(NSStringFromRect(visible)) 点(窗口)=\(NSStringFromPoint(previewPoint)) 命中链=\(chain)")
            XCTAssertTrue(chain.contains("ChineseSelectableNSTextView"),
                          "点击点没命中详情只读文本区（命中链：\(chain)）")

            let previewMenu = try XCTUnwrap(
                preview.menu(for: rightEvent),
                "只读文本区的 menu(for:) 返回空 —— 用户在详情区右键一个菜单都没有"
            )
            let previewTitles = titles(of: previewMenu)
            emit("MENUS 只读区菜单=\(previewTitles) plugIns=\(previewMenu.allowsContextMenuPlugIns)")
            XCTAssertEqual(previewTitles, ["复制", "全选", "查找…"], "详情只读区 AppKit 要弹的菜单被污染")
            XCTAssertFalse(previewMenu.allowsContextMenuPlugIns,
                           "只读区弹出来的菜单没关自动附加项 —— 系统项还能往里塞")
            for item in previewMenu.items where !item.isSeparatorItem {
                XCTAssertFalse(ChineseTextContextMenu.isBlocked(item), "只读区混进系统项：\(item.title)")
                XCTAssertTrue(containsCJK(item.title), "只读区混进非中文项：\(item.title)")
            }
        }
        emit("MENUS 只读区数量=\(previews.count)")
    }

    private func titles(of menu: NSMenu) -> [String] {
        menu.items.filter { !$0.isSeparatorItem }.map(\.title)
    }

    /// 搜索框两份菜单（编辑态 / 非编辑态）共用的判据：中文、只有那六项、没关的附加项通道、没混进系统项。
    private func assertChineseEditingMenu(_ menu: NSMenu, where place: String) {
        XCTAssertEqual(titles(of: menu), ["撤销", "重做", "剪切", "复制", "粘贴", "全选"],
                       "\(place) 里 AppKit 要弹的不是那份中文可编辑菜单")
        XCTAssertFalse(menu.allowsContextMenuPlugIns,
                       "\(place) 的菜单没关自动附加项 —— 系统项还能往里塞")
        for item in menu.items where !item.isSeparatorItem {
            XCTAssertFalse(ChineseTextContextMenu.isBlocked(item), "\(place) 混进系统项：\(item.title)")
            XCTAssertTrue(containsCJK(item.title), "\(place) 混进非中文项：\(item.title)")
        }
    }

    private func containsCJK(_ string: String) -> Bool {
        string.unicodeScalars.contains { (0x4E00...0x9FFF).contains($0.value) }
    }

    /// 真实列表里的行位置**向 `NSTableView` 自己问**（SwiftUI 的 `List` 底下就是它）。
    ///
    /// 为什么不能再用 KeyViewProxy 的几何：换成 `List` 之后宿主树里数不到行代理了
    /// （实测 `星标代理=0 行代理=0`），可点控件的代理被表格接管了；而猜行高这一族已经两次
    /// 把探针点空、报成产品缺陷。表格的 `rect(ofRow:)` 是唯一权威来源。
    /// 返回的是**窗口基坐标**（`NSEvent.mouseEvent` 要的那个）。
    /// 合成鼠标事件的投递器。`eventNumber` **每一段按下-抬起会话共用一个递增值**：
    /// SwiftUI 的自绘手势不在乎它（所以旧探针写 0 也能点中行），但 `NSTableView` 的行选中
    /// 走 AppKit 的鼠标跟踪状态机，`eventNumber` 恒为 0 时 down/up 配不成对 ⇒
    /// 表现为"点了没选中"，那是探针的错，不是产品的错（本轮实测踩过）。
    @MainActor
    private final class MouseSynthesizer {
        private let window: NSWindow
        private var session = 0
        var lastClickPoint = NSPoint.zero

        init(window: NSWindow) {
            self.window = window
        }

        func click(at windowPoint: NSPoint, clickCount: Int = 1) {
            session += 1
            let number = session
            lastClickPoint = windowPoint
            send(.leftMouseDown, at: windowPoint, clicks: max(1, clickCount), number: number)
            RunLoop.main.run(until: Date().addingTimeInterval(0.03))
            send(.leftMouseUp, at: windowPoint, clicks: max(1, clickCount), number: number)
            RunLoop.main.run(until: Date().addingTimeInterval(0.08))
        }

        /// 按下 → 依次经过 via → 在终点抬起：一整段拖动共用一个 eventNumber。
        func drag(from start: NSPoint, through via: [NSPoint], to end: NSPoint) {
            session += 1
            let number = session
            send(.leftMouseDown, at: start, clicks: 1, number: number)
            RunLoop.main.run(until: Date().addingTimeInterval(0.03))
            for point in via {
                send(.leftMouseDragged, at: point, clicks: 1, number: number)
                RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            }
            send(.leftMouseDragged, at: end, clicks: 1, number: number)
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            send(.leftMouseUp, at: end, clicks: 1, number: number)
            RunLoop.main.run(until: Date().addingTimeInterval(0.1))
        }

        private func send(_ type: NSEvent.EventType, at point: NSPoint, clicks: Int, number: Int) {
            guard let event = NSEvent.mouseEvent(with: type, location: point, modifierFlags: [],
                                                 timestamp: ProcessInfo.processInfo.systemUptime,
                                                 windowNumber: window.windowNumber, context: nil,
                                                 eventNumber: number, clickCount: clicks, pressure: 1.0) else { return }
            // 走 `window.sendEvent` 而不是 `NSApp.sendEvent`：xctest 进程里 `NSApp.isActive`
            // 起不来（实测 isKeyWindow=false isActive=false），应用级派发会把鼠标事件丢掉，
            // 于是表格的 `clickedRow` 恒为 -1 —— 那会被读成"点击没生效"的假产品缺陷。
            // 直接向窗口派发是同一条 AppKit 路径的入口，`NSTableView` 的行命中因此可测。
            window.sendEvent(event)
        }
    }

    private func sidebarRowPoints(in host: NSView, count: Int) throws -> [(body: NSPoint, leading: NSPoint)] {
        // 用 `is NSTableView` 而不是类名字符串：SwiftUI 底下那个类是 NSTableView 的**子类**，
        // 它自己的名字里没有 "NSTableView"（第一版按类名匹配 ⇒ 找不到 ⇒ 探针静默 skip，
        // 而 skip 会把"D-1 到底修没修"这条判据整个吃掉）。
        guard let table = Self.firstTable(in: host) else {
            var names: [String] = []
            func collect(_ view: NSView) {
                names.append(String(describing: type(of: view)))
                for sub in view.subviews { collect(sub) }
            }
            collect(host)
            // 抛错而不是 skip：skip 会把"D-1 到底修没修"这条判据整个吃掉。
            throw NSError(domain: "UIInteractionProbe", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "侧栏里找不到 NSTableView，无法取行几何。视图类名（前 30）：\(names.prefix(30))",
            ])
        }
        XCTAssertGreaterThanOrEqual(table.numberOfRows, count,
                                    "表格行数 \(table.numberOfRows) 少于探针要的 \(count) 行，几何无从取")
        return (0..<count).map { index in
            let rect = table.rect(ofRow: index)
            let midY = rect.midY
            return (
                body: table.convert(NSPoint(x: rect.midX, y: midY), to: nil),
                leading: table.convert(NSPoint(x: rect.minX + 14, y: midY), to: nil)
            )
        }
    }

    private static func firstTable(in view: NSView) -> NSTableView? {
        if let table = view as? NSTableView { return table }
        for sub in view.subviews {
            if let table = firstTable(in: sub) { return table }
        }
        return nil
    }

    private func describeChain(_ root: NSView, at point: NSPoint) -> String {
        var views: [String] = []
        var current: NSView? = root.hitTest(point)
        while let view = current {
            views.append(String(describing: type(of: view)))
            current = view.superview
        }
        return views.isEmpty ? "（命中为空）" : views.joined(separator: " ← ")
    }

    private func capture(window: NSWindow, to file: URL, dark: Bool) throws {
        let appearance: NSAppearance.Name = dark ? .darkAqua : .aqua
        let previous = NSApp.appearance
        NSApp.appearance = NSAppearance(named: appearance)
        defer { NSApp.appearance = previous }
        guard let contentView = window.contentView else { return }
        let bounds = contentView.bounds
        guard let rep = contentView.bitmapImageRepForCachingDisplay(in: bounds) else { return }
        NSAppearance(named: appearance)?.performAsCurrentDrawingAppearance {
            contentView.cacheDisplay(in: bounds, to: rep)
        }
        guard let cgImage = rep.cgImage,
              let data = NSBitmapImageRep(cgImage: cgImage).representation(using: .png, properties: [:]) else { return }
        try data.write(to: file)
    }
}

/// stderr 是无缓冲的：探针被监视线程/超时杀掉时，已经写出的行还在，`print` 的会丢。
/// 写在文件级而不是实例上，是因为 `@Sendable` 回调不能捕获 `self`。
private func emit(_ string: String) {
    FileHandle.standardError.write((string + "\n").data(using: .utf8)!)
}

/// 模态弹菜单的看门狗：到点还没被 `disarm` 就写清原因后退出进程。
/// 为什么必须是进程级：`NSMenu.popUpContextMenu` 在主线程模态循环里不返回，
/// 同线程没有任何办法打断它；让它挂在那儿等于把这条探针变成"跑一次就再也跑不动"。
private final class PopupWatchdog: @unchecked Sendable {
    private let lock = NSLock()
    private var armed = true

    func disarm() {
        lock.lock(); armed = false; lock.unlock()
    }

    private var isArmed: Bool {
        lock.lock(); defer { lock.unlock() }
        return armed
    }

    func arm(after seconds: TimeInterval, why: String) {
        DispatchQueue.global().asyncAfter(deadline: .now() + seconds) {
            guard self.isArmed else { return }
            emit("WATCHDOG 探针挂住：\(why)")
            exit(73)
        }
    }
}
