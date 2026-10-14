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

        // 动效审计 §6："加完动画必须重测"。同一条驱动、同一个窗口，把目录曲线换成零时长
        // 再跑一遍 —— 没有这一条，上面那行 p95 到底是"动画的代价"还是"本来就这样"没人知道。
        // 只报数不判红：两臂之差受机器负载影响，把它做成闸门就会变成"环境吵就红"的假守卫。
        // 判据仍然是动画那一臂（那才是交付配置）。
        MotionCatalog.animationsEnabled = false
        let offMeter = FrameMeter()
        offMeter.start()
        var offPhase = 0
        let offDeadline = Date().addingTimeInterval(3.2)
        var offNextStep = Date()
        while Date() < offDeadline {
            if Date() >= offNextStep {
                let count = max(store.entries.count, 1)
                switch offPhase % 4 {
                case 0: store.perform(.select(store.entries[offPhase % count]))
                case 1: store.perform(.updateSearch(offPhase % 2 == 0 ? "记录 3" : ""))
                case 2: store.perform(.updateFilter(offPhase % 4 == 2 ? .favorites : .all))
                default: store.perform(.toggleSelection(store.entries[offPhase % count]))
                }
                offPhase += 1
                offNextStep = Date().addingTimeInterval(0.1)
            }
            RunLoop.main.run(until: Date().addingTimeInterval(0.008))
        }
        let off = offMeter.stats()
        offMeter.stop()
        MotionCatalog.animationsEnabled = true

        print("FPS-BASELINE n=\(baseline.n) p50=\(String(format: "%.2f", baseline.p50))ms p95=\(String(format: "%.2f", baseline.p95))ms worst=\(String(format: "%.1f", baseline.worst))ms >16.7ms:\(baseline.over16) >33.4ms:\(baseline.over33)")
        print("FPS-MOTION-OFF n=\(off.n) p50=\(String(format: "%.2f", off.p50))ms p95=\(String(format: "%.2f", off.p95))ms worst=\(String(format: "%.1f", off.worst))ms >16.7ms:\(off.over16) >33.4ms:\(off.over33)")
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

    /// R61 / BACKLOG 61 的管线级验收：程序化选中一条**视口外**的行时，
    /// 列表必须自己滚过去把它亮出来；而选中一条已经看得见的行时，**不许动视口**。
    ///
    /// 这条从产品入口进（`store.perform(.setSelection)`），在**在屏**窗口里读
    /// `NSTableView.selectedRowIndexes` 与 `documentVisibleRect` —— 不是内部纯函数。
    /// 纯函数那一半（行号怎么算）在 `SelectedRowRevealTests.testRowIndexTruthTable`。
    ///
    /// 四臂，顺序不能换：
    ///   臂 1 近处 ⇒ 落点=2 且 **originY 纹丝不动**。后半句是 R22 那一族的自伤闸：
    ///          "跟随选中"最省事的写法是无条件滚，那会把用户刚点的那一行也甩到中间去。
    ///   臂 2 视口外 ⇒ 落点=最后一条、且它落在可视区里、且 originY 真的动了。
    ///          originY 必须一起判：只判"选中了"会放过"表格本来就滚在那里"这种假绿。
    ///   臂 3 用户自己滚开、再走一次**同一个**选中 ⇒ originY 保持不动。
    ///          这条钉的是"行号变了才滚"，不是"每次重算都滚"。
    ///   臂 4 通道前提（放在最前跑）：视口内落得上、行数够长、有 NSScrollView。
    ///
    /// 本轮在它之前先量死了一条**不能这样修**的路（读数都在这条的正文里）：
    /// * SwiftUI 的 `ScrollViewReader` + `.id` + `scrollTo` 在产品这棵树上不滚。
    ///   临时插桩 `GLUE_DEBUG` 证明胶水执行了、id 也解析到了，表格一步没动；
    ///   同一份形状在孤立 spike 里 0.25s 就从第 1 行滚到第 60 行，
    ///   六臂 bisect（focusEffectDisabled / onDrop+overlay+animation / VStack 在 reader 内 /
    ///   Button 行 / 产品形状的行 / reader 在 if/else 里）全绿，找不到哪一件按死的它。
    /// * 只用 `table.selectedRow` 判"有没有选中"是读错轴（它读**主选中行**），
    ///   所以每条读数都同时打 `selectedRowIndexes`；本轮臂 2 的结论就靠这一轴才敢下。
    /// * 更早那版探针的泵条件是"选中行变没变" —— `2 → -1` 也算变了，于是 0.2s 就收工，
    ///   把"还没滚到位"和"永远不会滚到位"读成同一个数。现在按**期望那一行**泵并如实报"到没到"。
    func testOffScreenProgrammaticSelectionIsRevealedAndNotJumped() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 260, y: 220, width: 320, height: 300),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))

        let table = try XCTUnwrap(Self.firstTable(in: host))
        let count = table.numberOfRows
        guard count > 6 else {
            XCTFail("表格只有 \(count) 行 ⇒ 这一格没有「往视口外选」这件事可问（夹具的数据不够长）")
            return
        }
        guard let view = table.enclosingScrollView else {
            XCTFail("表格外面没有 NSScrollView ⇒ 探针量不到可视区，四条读数全部作废（夹具坏了，不是产品坏了）")
            return
        }
        let rowHeight = max(1, table.rect(ofRow: 0).height)
        func originY() -> CGFloat { view.documentVisibleRect.origin.y }
        emit("REVEAL 行数=\(count) 可视高=\(String(format: "%.0f", view.documentVisibleRect.height)) "
             + "行高=\(String(format: "%.0f", rowHeight)) 文档高="
             + "\(String(format: "%.0f", view.documentView?.frame.height ?? -1)) "
             + "⇒ 视口约装 \(String(format: "%.1f", view.documentVisibleRect.height / rowHeight)) 行")

        /// 走产品入口把选中设成第 `index` 条，泵到**表格的选中集合正好是那一行**为止。
        ///
        /// 判集合，不判 `selectedRow`：后者读的是**主选中行**，本轮实测它会在揭示之后仍停在旧行上
        /// （读数：`选中集合=[2, 60]` 而 `主选中行=2`）。同一族的轴错本轮已经犯过两次
        /// （"有没有一行被选中"、"选中行变没变"），这是第三次 —— 所以两条轴都打出来，
        /// 判据只认"我要的那一行在不在集合里、集合里有没有多余的行"。
        /// `inside` 同理按**问的那一行**算，不按主选中行算。
        func selectViaStore(_ index: Int, tag: String) -> (set: [Int], primary: Int, storeOK: Bool, inside: Bool, pumped: Double) {
            let beforeRow = table.selectedRow
            let wanted = store.filteredEntries[index].id
            store.perform(.setSelection([wanted]))
            var pumped = 0.0
            while table.selectedRowIndexes != IndexSet(integer: index) && pumped < 2.0 {
                RunLoop.main.run(until: Date().addingTimeInterval(0.1))
                pumped += 0.1
            }
            let set = Array(table.selectedRowIndexes.sorted())
            let primary = table.selectedRow
            let storeOK = store.selectedEntryIDs == [wanted]
            let rect = table.rect(ofRow: index)
            let inside = rect.height > 0 && view.documentVisibleRect.intersects(rect)
            emit("REVEAL \(tag) 想选第\(index)条 之前主选中行=\(beforeRow) 主选中行=\(primary) "
                 + "选中集合=\(set) 只有它=\(set == [index]) 该行在可视区=\(inside) "
                 + "store 对不对=\(storeOK) originY=\(String(format: "%.1f", originY())) "
                 + "泵了 \(String(format: "%.2f", pumped))s")
            return (set, primary, storeOK, inside, pumped)
        }

        // 臂 4（先跑的前提）：视口内能落上，通道才是活的。
        let near = selectViaStore(2, tag: "臂1 近处")
        XCTAssertEqual(near.set, [2],
                       "视口内的程序化选中都没落到表格 ⇒ 探针↔store↔表格这条通道是死的，"
                         + "后面三条读数一概不算数（先修探针，别修产品）")
        XCTAssertTrue(near.inside, "臂 1 想选的那一行本来就该在视口里 ⇒ 视口判定坏了，臂 2/3 都会误判")

        // 臂 1 的后半句：已经可见 ⇒ 不许滚。
        XCTAssertEqual(Double(originY()), 0, accuracy: 1.0,
                       "选中一条**已经看得见**的行也把视口推动了 ⇒ 这就是 R22 那一族的自伤："
                         + "用户点一下，列表自己跳。修法必须按「不在可视区才滚」判")

        // 臂 2：缺陷本体 + 修法生效的证据。
        let originBeforeFar = originY()
        let far = selectViaStore(count - 1, tag: "臂2 视口外")
        XCTAssertTrue(far.storeOK, "store 没落上 ⇒ 这条读的是探针不是产品")
        XCTAssertEqual(far.set, [count - 1],
                       "选中视口外那一行之后表格没有**只**选中它 ⇒ 要么揭示没发生（61 复发，"
                         + "先查 `SelectedRowRevealer` 还挂没挂在侧栏上、找没找到表格），"
                         + "要么上一行的选中没被撤掉（列表亮两行、详情讲一条 = 新的分裂，另立条目）")
        XCTAssertTrue(far.inside, "那一行不在可视区 ⇒ 选中跟了、滚动没跟，61 的那个症状还在")
        XCTAssertGreaterThan(originY(), originBeforeFar + 1,
                             "选中一条视口外的行而视口一点没动 ⇒ 「落上了」只能是巧合（比如表格本来就滚在那儿），"
                                 + "不能算修法生效")

        // 臂 3：用户自己滚开之后，同一个选中不许把他拽回来。
        view.contentView.scroll(to: NSPoint(x: 0, y: 0))
        view.reflectScrolledClipView(view.contentView)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        let originAfterUserScroll = originY()
        // 臂 3 要判的是"选中没变、但视图重算了 ⇒ 不许动"。**不能用"再走一次同一个选中"来触发重算**：
        // 那样 SwiftUI 读到的值没变，压根不会重画 ⇒ `updateNSView` 一次都没被调用，
        // 于是"行号变了才滚"那道闸拆掉也照样绿 —— M313 第一版就是这么活下来的
        // （判据没有分辨率，却长得像一条通过的判据）。
        // 换一个**真的会重算、又不碰选中**的产品入口：给别的条目加/撤收藏。
        let other = store.filteredEntries.first { $0.id != store.selectedEntry?.id }
        XCTAssertNotNil(other, "夹具里没有第二条可点的条目 ⇒ 这一臂造不出『重算但选中没变』")
        if let other {
            store.perform(.toggleFavorite(other))
            RunLoop.main.run(until: Date().addingTimeInterval(0.6))
            store.perform(.toggleFavorite(other))
            RunLoop.main.run(until: Date().addingTimeInterval(0.6))
            emit("REVEAL 臂3 用户滚开后、选中没变而视图重算了两次（收藏+撤） originY="
                 + "\(String(format: "%.1f", originY())) 选中集合=\(Array(table.selectedRowIndexes.sorted()))")
            XCTAssertEqual(Double(originY()), Double(originAfterUserScroll), accuracy: 1.0,
                           "选中没变、只是列表重算了一次，就把视口拽回选中行 ⇒ 「每次重算都滚」取代了"
                             + "「选中变了才滚」：用户往下翻看时，任意一次收藏/撤收藏都会把他弹回去")
        }

        // 臂 3 顺手量到一件本轮没修的事（读数：表格 `选中集合=[0, 60]` 而 store 只有 1 条）：
        // 手工把视口滚回顶部之后，`List` 会把**第一行也留在选中集里** ——
        // 于是"列表亮两行、详情讲一条"。它不是"选中被回写进 store"（同一行读数里
        // `store 里条数=1`，所以我最初那句"批量动作会作用在没选过的记录上"是**推过头了**，
        // 已按读数改回来）：分裂只在表格这一侧，批量动作仍按 store 走。
        // 另立 BACKLOG 90。本轮不修、也**不判红**：把这条判据写成断言会让整个套件红，
        // 而红要留给 61 本身 —— 所以它是一条显式登记的观察，不是被藏起来的失败。
        emit("REVEAL 臂3 观察（不判）：选中集合=\(Array(table.selectedRowIndexes.sorted())) "
             + "store 里条数=\(store.selectedEntryIDs.count) ⇒ 集合被 List 回写进 store 了=\(store.selectedEntryIDs.count > 1) "
             + "—— BACKLOG 90")
    }

    /// 臂 5 单独一条：**行号漂了不算"选中变了"**。
    ///
    /// 为什么必须单独一条：把它接在臂 3 后面，前提会被臂 3 那次手工滚动污染
    /// （`List` 把第 0 行并进了选中集并回写 store ⇒ `selectedEntry` 已经不是第 60 行，
    /// 行号漂移这件事就造不出来了 —— 第一次跑就是这么红的：`Optional(0)→Optional(0)`）。
    ///
    /// 这一臂给的是"闸门按什么键"的分辨率：把 `SelectedRowRevealer` 的闸门从"选中 id"
    /// 改成"行号"（M313），只有这里会红 —— 因为删掉顶部一条无关记录时，
    /// 选中项的 **id 没变、行号变了**，视口不该动。
    func testRowIndexDriftDoesNotMoveTheViewport() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 260, y: 220, width: 320, height: 300),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        let table = try XCTUnwrap(Self.firstTable(in: host))
        guard let view = table.enclosingScrollView else {
            XCTFail("没有 NSScrollView ⇒ 量不到可视区，这条不判")
            return
        }
        let count = table.numberOfRows
        guard count > 6 else {
            XCTFail("表格只有 \(count) 行 ⇒ 造不出「删顶部一条、下面的行号漂移」")
            return
        }
        func originY() -> CGFloat { view.documentVisibleRect.origin.y }

        // 先让选中落在最后一条（这一步正该滚：臂 2 已经判过它滚得到）
        let farID = store.filteredEntries[count - 1].id
        store.perform(.setSelection([farID]))
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        let originAfterReveal = originY()
        let indexBefore = store.filteredEntries.firstIndex { $0.id == farID }
        emit("DRIFT 选中最后一条之后 originY=\(String(format: "%.1f", originAfterReveal)) 行号=\(String(describing: indexBefore))")
        XCTAssertTrue(originAfterReveal > 1, "揭示本身没发生 ⇒ 这一臂没有前提可言（先查臂 2 那条）")

        // 回到顶部（模拟用户自己在往上翻），然后删掉**顶部那条无关记录**：
        // 选中项 id 不变、行号 -1 ⇒ 视口必须保持不动。
        view.contentView.scroll(to: .zero)
        view.reflectScrolledClipView(view.contentView)
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        let originAtTop = originY()
        let topUnrelated = store.filteredEntries.first { $0.id != farID }
        XCTAssertNotNil(topUnrelated, "夹具里没有第二条可删 ⇒ 这一臂造不出漂移")
        if let topUnrelated {
            store.perform(.delete(topUnrelated))
            RunLoop.main.run(until: Date().addingTimeInterval(0.6))
            let indexAfter = store.filteredEntries.firstIndex { $0.id == farID }
            emit("DRIFT 删掉顶部一条无关记录 ⇒ 行号 \(String(describing: indexBefore))→\(String(describing: indexAfter)) "
                 + "store 仍选中它=\(store.selectedEntryIDs == [farID]) originY=\(String(format: "%.1f", originY())) "
                 + "（回到顶部时是 \(String(format: "%.1f", originAtTop))）")
            XCTAssertNotNil(indexAfter, "删完找不到那条了 ⇒ 前提没了，判据是空的（先修夹具）")
            XCTAssertNotEqual(indexBefore, indexAfter,
                              "这一臂没造出行号漂移 ⇒ 判据是空的（先修夹具，别改产品）")
            XCTAssertEqual(Double(originY()), Double(originAtTop), accuracy: 1.0,
                           "选中项只是**行号漂了**（id 没变、选中没变）视口却动了 ⇒ 闸门按行号判而不是按选中判："
                             + "用户在读列表时删一条记录，就会被弹回选中行")
        }
    }

    /// 这条缺陷需要用户点鼠标吗？R61 实测：**不需要**，采集入口自己就能把它送到视口外。
    ///
    /// 机制（读过代码、也量过）：`HistoryStore.add` 末尾调
    /// `reconcileSelection(preferredEntryID: 新条目.id)` —— 新记录一进来就被选中；
    /// 而它的落点是 `EntryOrdering.promotionIndex` = 开头那段固定项的长度。
    /// 于是"前面固定了 K 条 + 视口只装得下 V 行（K > V）"这一格，新记录落在视口外，
    /// 于是**一次普通复制**就触发选中-不可见，全程没有一次点击。
    ///
    /// 这条同时更正账本 eeb16d0 里的一句话：那里写的"被选中的那条会一路往下漂出视口"是**错的**
    /// —— 选中项不会漂，它每次都被**换成新记录**；真正的问题是新记录的落点。
    /// 用户逐字对台账，所以这句更正写进正文，而不是悄悄改掉。
    func testIntakeBehindATallPinnedBlockRevealsTheNewRow() throws {
        try skipUnlessEnabled()
        let store = syntheticStore()
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 260, y: 220, width: 320, height: 300),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(HistorySidebarView(historyStore: store)))
        host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        let table = try XCTUnwrap(Self.firstTable(in: host))
        guard let view = table.enclosingScrollView else {
            XCTFail("没有 NSScrollView ⇒ 量不到可视区，这条不判")
            return
        }

        let rowHeight = max(1, table.rect(ofRow: 0).height)
        let visibleRows = Int(view.documentVisibleRect.height / rowHeight)
        let pinCount = visibleRows + 2
        guard pinCount >= 2, store.filteredEntries.count > pinCount + 2 else {
            XCTFail("夹具不够长或视口太大（可见 \(visibleRows) 行、要固定 \(pinCount) 条、共 \(store.filteredEntries.count) 条）"
                    + "⇒ 这一格没有「固定块顶开新记录」这件事可问")
            return
        }

        // 把最前面 pinCount 条固定住 —— 走的都是产品入口。
        let pinIDs = Set(store.filteredEntries.prefix(pinCount).map(\.id))
        store.perform(.setSelection(pinIDs))
        store.perform(.pinSelection(isPinned: true))
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        let pinnedNow = store.filteredEntries.prefix(pinCount).filter(\.isPinned).count
        emit("INTAKE_PIN 可见行=\(visibleRows) 固定了=\(pinnedNow)/\(pinCount) "
             + "开头那段固定项长度=\(store.filteredEntries.prefix(while: \.isPinned).count)")
        XCTAssertEqual(pinnedNow, pinCount,
                       "固定没落到开头那段 ⇒ 插入位没被顶下去，这一臂的前提不成立，探针先修")

        // 回到顶部，模拟"用户正在看最上面"。新记录会落在 pinCount 那一行 = 视口外。
        view.contentView.scroll(to: NSPoint(x: 0, y: 0))
        view.reflectScrolledClipView(view.contentView)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        let originBefore = view.documentVisibleRect.origin.y
        try capture(window: window, to: shotsURL("reveal-before-320x300-light.png"), dark: false)

        let before = Set(store.entries.map(\.id))
        store.add(ClipboardIntake.Entry(
            content: .text("R61 新增的这一条：用来测「落在视口外」这件事"),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.TextEdit", sourceAppName: "TextEdit"),
            timestamp: Date())
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        let added = store.entries.filter { !before.contains($0.id) }
        guard let newEntry = added.first else {
            XCTFail("采集没进列表 ⇒ 入口没走到，这条不判产品")
            return
        }
        let landingIndex = store.filteredEntries.firstIndex { $0.id == newEntry.id }
        let storeSelected = store.selectedEntryIDs == [newEntry.id]
        let tableSet = Array(table.selectedRowIndexes.sorted())
        let onScreen = landingIndex.map {
            view.documentVisibleRect.intersects(table.rect(ofRow: $0)) && table.rect(ofRow: 0).height > 0
        } ?? false
        emit("INTAKE_READING 新记录落点=\(String(describing: landingIndex)) 在屏=\(onScreen) "
             + "store 选中它=\(storeSelected) 表格选中集合=\(tableSet) "
             + "originY \(String(format: "%.1f", originBefore))→\(String(format: "%.1f", view.documentVisibleRect.origin.y)) ⇒ "
             + (!storeSelected
                ? "采集入口这次没把选中给新记录 ⇒ 机制段读错了，回到 reconcileSelection 重读"
                : ((landingIndex ?? 0) <= visibleRows
                    ? "新记录本来就落在视口内 ⇒ 这一格没造出「固定块顶开」，夹具要调（窗口高度或固定数）"
                    : (tableSet == landingIndex.map { [$0] } && onScreen
                        ? "**无需点击**：一次普通复制之后，列表自己滚到新记录并把它亮出来 ⇒ 61 在这条路径上已修"
                        : "新记录在视口外而列表没亮它（集合=\(tableSet) 在屏=\(onScreen)）⇒ 采集路径上 61 还在"))))
        // 视觉取证：本轮的"真实视觉审查"就落在这一对帧上 —— 读数说列表滚过去了、
        // 新记录带高亮，帧里必须看得见同一件事。两件事一并留档：
        // 这**不是**帧基线的那 116 张（`FRAME_BASELINE_CHANGED=0`：静态帧里选中永远在第一行，
        // 揭示器正确地什么都不做 ⇒ 离屏通道结构上看不到本轮的改动），
        // 也别忘了 `cacheDisplay` 是离屏重绘，高亮由真实表格画，所以这对话只作取证、不进判据。
        try capture(window: window, to: shotsURL("reveal-after-320x300-light.png"), dark: false)

        XCTAssertTrue(storeSelected, "采集入口没把新记录设成选中 ⇒ 这条判的不是它声称的那件事")
        XCTAssertEqual(tableSet, landingIndex.map { [$0] },
                       "一次普通复制把选中送到视口外、列表没有跟上 ⇒ BACKLOG 61 在采集路径上复发")
        XCTAssertTrue(onScreen, "表格说选中了但那一行不在可视区 ⇒ 高亮仍然看不见，症状没修掉")
    }


    /// 宿主里**所有**表格（不是第一个）：一屏里可能同时有侧栏列表和详情区里的表，
    /// 只拿第一个会把"我拿错了表"当成"产品没响应"。
    /// 产品源码（按相对路径），去掉 `//` 注释行。
    ///
    /// 为什么要 `codeOnly`：声明守卫如果连注释一起读，那"注释里写着滚动跟随"就会算成一次声明，
    /// 于是守卫判的是文档而不是代码 —— 而这一族的缺陷恰恰是「代码里声明、屏幕上没有」。
    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        // 刻意不 `throw XCTSkip`（同 `Round3DetailTypographyTests.productSource` 那条）：
        // 守卫找不到被守卫的文件时应当**红**，而不是安静跳过 —— 会跳过的守卫和通过的守卫在报表里长得一样。
        throw NSError(domain: "UIInteractionProbeTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)：声明守卫会假绿，先修路径解析"])
    }

    private static func allTables(in view: NSView) -> [NSTableView] {
        var found: [NSTableView] = []
        if let table = view as? NSTableView { found.append(table) }
        for sub in view.subviews { found.append(contentsOf: allTables(in: sub)) }
        return found
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
    // D-1 原本在这里有一条拖选探针（从第 1 行按下拖到第 4 行，断言选中集扩到 4 行）。
    // 它随账本 D-034 一起删除：真机验证 `List` 会把行内任何 `.onDrag` 提升成整行拖拽源，
    // 于是拖选与拖出在系统列表里不能共存，取舍是保留拖出、放弃拖选，
    // 所以这个手势在产品里已经不存在了 —— 留一条永远点不出效果的探针就是留一个假闸门。
    // 它当初也没真的门住过什么：合成事件驱动不了表格（见上一条探针里的 OBSERVE 行）。

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
            // 失败消息要自带"当时看到了什么"：这条探针红过一次，而"找不到行代理"那五个字
            // 什么都没告诉我们 —— 是行没画出来，还是行的无障碍结构变了（一行变成两个代理）。
            // 后者才是真问题，而只有把代理的帧打出来才分得开。
            var seen: [String] = []
            func dumpAll(_ view: NSView) {
                let name = String(describing: type(of: view))
                if name.contains("Proxy") || name.contains("ListTableRowView") { seen.append("\(name)@\(view.frame)") }
                for sub in view.subviews { dumpAll(sub) }
            }
            dumpAll(host)
            XCTFail("找不到行代理（要求 KeyViewProxy 宽 200…290、高 <40），"
                    + "宿主 \(host.frame)、窗口内容区 \(window.contentLayoutRect)，"
                    + "实际看到的行相关视图：\(seen.prefix(14))。"
                    + "如果一行变成**两个**半宽代理，那是无障碍结构的问题，不是探针的几何没调对")
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

    // MARK: - Markdown 渲染与那颗控件（第四轮新增功能）

    /// 「右侧预览渲染 Markdown」的**活路径**判据：磁盘上一个真的 `.md` 文件，
    /// 选中之后详情区画出来的必须是渲染结果（标题字号、标记消失、编号保留）。
    /// 名字里刻意不再写"点击生效"：那颗控件的点击在这个环境里量不到，原因见方法末尾那段。
    ///
    /// 为什么在在屏探针而不是离屏帧/普通用例里：`DetailFileView` 靠 SwiftUI 的 `.task(id:)`
    /// 异步加载，而 `.task` 在"从未 ordered front 的窗口"里不启动 ——
    /// 实测离屏树永远停在 `NSProgressIndicator`。这一路只有真窗口能量（D-019/D-041 同一族）。
    /// 判据只钉可归因的三件事：渲染发生了、控件存在且点得动、切换双向有效。
    func testMarkdownFilePreviewRendersInARealWindow() throws {
        try skipUnlessEnabled()
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent("markdown-preview-probe-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let url = directory.appendingPathComponent("说明.md")
        let source = "# 发布说明\n\n这一段有 **粗体** 和 `code`。\n\n- 第一项\n3. 第三步\n\n## 安装\n\n结束。\n"
        try source.write(to: url, atomically: true, encoding: .utf8)

        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        store.add(ClipboardIntake.Entry(content: .file(url), thumbnail: nil,
                                        sourceUTIs: ["public.file-url"],
                                        sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"),
                  timestamp: Date())
        store.perform(.selectOnly(store.entries[0]))
        let (window, host) = makeWindow(width: 900, height: 640, origin: CGPoint(x: 180, y: 180), store: store)
        defer { window.orderOut(nil) }

        func bodies() -> [ChineseSelectableNSTextView] {
            var found: [ChineseSelectableNSTextView] = []
            func walk(_ view: NSView) {
                if let body = view as? ChineseSelectableNSTextView { found.append(body) }
                for sub in view.subviews { walk(sub) }
            }
            walk(host)
            return found
        }

        // 等异步加载把正文画出来。等不到就是**失败**，不是跳过：
        // 跳过的判据和通过的判据在报表里长得一样，而这一条存在的意义就是"渲染真的发生了"。
        let deadline = Date().addingTimeInterval(6.0)
        while bodies().first?.string.contains("第三步") != true, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        let body = try XCTUnwrap(
            bodies().first,
            "选中一个 .md 文件后详情区没有只读正文视图（预览没加载出来？）"
        )
        XCTAssertTrue(body.string.contains("第三步"),
                      "正文没加载出来，量不到渲染：\(body.string.prefix(60))")
        XCTAssertFalse(body.string.contains("# 发布说明"),
                       "文件预览没渲染 Markdown：标题标记还在正文里")
        XCTAssertFalse(body.string.contains("**粗体**"), "强调标记没被吃掉")
        XCTAssertTrue(body.string.contains("3."), "有序项的编号被渲染吃掉了")
        let headingRange = (body.string as NSString).range(of: "发布说明")
        XCTAssertNotEqual(headingRange.location, NSNotFound)
        let headingFont = try XCTUnwrap(
            body.attributedString().attribute(.font, at: headingRange.location, effectiveRange: nil) as? NSFont
        )
        XCTAssertEqual(headingFont.pointSize, MarkdownPresentation.headingFontSize(level: 1),
                       "标题在真窗口里没有标题字号")
        emit("MARKDOWN 渲染态 正文长度=\(body.string.count) 标题字号=\(headingFont.pointSize)")

        // 这颗控件"按下去有效"这一件事，三条自动化路都试过，只有两条能量到、第三条量不到：
        // ① 跨进程 `AXUIElement*`：要求本进程有"辅助功能"授权，`swift test` 起的进程
        //    实测整棵 AX 树是空的（连一个有名元素都没有）；
        // ② 进程内 `NSAccessibilityProtocol`：SwiftUI 的 hosting view 只回一个没有子节点的
        //    `AXGroup`（实测打印过），按钮压根不在树里；
        // ③ 按几何算窗口坐标投鼠标事件：实测从正文滚动视图量出来的矩形是
        //    `{{280, 0}, {620, 633}}` —— 比"窗口高度减去头部"还高，说明它不在我以为的那层，
        //    算出来的点落在窗口外（点击后状态没翻，判据如实报红）。
        // 所以这里只把**渲染真的发生在真窗口里**这一条钉死，"按一下会不会切换"
        // 留在手工清单（`docs/MANUAL_TEST_v1.4.9_round3.md` 批次 6 第 2 条）。
        // 两帧 `detail-markdown-rendered` / `detail-markdown-source` 能证明两种状态都画得出来、
        // 标题也跟着状态变，但它们是**注入初始态**拍的，不是按出来的 —— 这个区别写在这里，
        // 免得下一个人把帧当成"点击有效"的证据。
        emit("MARKDOWN 控件自动化=不可量（AX 空树 / 几何不可归因），见手工清单批次 6")
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

    /// 探针的输出目录（与 `captureFocusFrames` 同一个环境变量，缺省时落到 /tmp）。
    private func shotsURL(_ name: String) -> URL {
        let dir = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"] ?? "/tmp/shots-probe"
        try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        return URL(fileURLWithPath: dir).appendingPathComponent(name)
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
