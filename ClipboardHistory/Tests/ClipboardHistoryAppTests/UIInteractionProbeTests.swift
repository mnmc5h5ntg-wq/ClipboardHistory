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

    /// 在屏合成一次真实点击序列，验证行上的三个手势各自落到正确的动作上。
    ///
    /// 为什么值得单独一条：这三个动作的**接线**在离屏帧里看不见，而纯函数用例只钉了判定规则
    /// （`RowInteractionTests`），钉不住"SwiftUI 真的把这两击当成一次双击"。
    /// 这里刻意用一行孤立的窗口而不是整侧栏：几何完全已知，点不中就是点不中，不会和
    /// "列表里第几行在哪"纠缠。
    func testRowGesturesFireTheRightActions() throws {
        try skipUnlessEnabled()
        var selectFired = 0
        var copyFired = 0
        var favoriteFired = 0
        let entry = makeClipboardEntry(content: .text("双击我这条"), timestamp: Date())
        let row = HistoryRowButton(
            entry: entry,
            selected: false,
            action: { selectFired += 1 },
            copyAction: { copyFired += 1 },
            favoriteAction: { favoriteFired += 1 }
        )

        _ = NSApplication.shared
        let size = NSSize(width: 300, height: 74)
        let window = NSWindow(contentRect: NSRect(x: 260, y: 260, width: size.width, height: size.height),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: AnyView(row))
        host.frame = NSRect(origin: .zero, size: size)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.4))

        func click(_ viewPoint: NSPoint, clickCount: Int, down: Bool = true) {
            // 合成事件走的是 `locationInWindow`（窗口基坐标），所以要把视图坐标换算过去，
            // 而不是自己按 titlebar 高度猜 —— 换算交给 AppKit。
            let windowPoint = host.convert(viewPoint, to: nil)
            func event(_ type: NSEvent.EventType, count: Int) -> NSEvent? {
                NSEvent.mouseEvent(with: type,
                                   location: windowPoint,
                                   modifierFlags: [],
                                   timestamp: ProcessInfo.processInfo.systemUptime,
                                   windowNumber: window.windowNumber,
                                   context: nil,
                                   eventNumber: 0,
                                   clickCount: count,
                                   pressure: 1.0)
            }
            let count = max(1, clickCount)
            if down, let downEvent = event(.leftMouseDown, count: count) { NSApp.sendEvent(downEvent) }
            if let upEvent = event(.leftMouseUp, count: count) { NSApp.sendEvent(upEvent) }
            RunLoop.main.run(until: Date().addingTimeInterval(0.08))
        }

        // 坐标一律从宿主视图的真实高度推，不写死：这一版最初写 y=37（以为行高 74），
        // 而 `HistoryRowButton` 的自然高度是 47，星标只有 20pt 高，于是点在了它下面 ——
        // 表现为"点星标没反应"，其实是探针点错了地方（网格扫描 x=8..26 / y=16..28 全部命中）。
        let midY = host.frame.height / 2
        let rowCenter = NSPoint(x: 150, y: midY)
        let starCenter = NSPoint(x: 18, y: midY)
        print("HITTEST 行中心 y=\(Int(midY)) 命中链：\(describeChain(host, at: rowCenter))")
        click(rowCenter, clickCount: 1)
        let afterSingle = selectFired
        click(rowCenter, clickCount: 1)
        XCTAssertEqual(afterSingle, 1, "第一次单击没有触发行选中：点击根本没送进这一行")
        XCTAssertEqual(selectFired, 2, "第二次单击也应照常选中（复制走的是双击手势）")

        // 双击：两下紧凑的 clickCount 1→2。
        let copyBefore = copyFired
        click(rowCenter, clickCount: 1)
        click(rowCenter, clickCount: 2)
        print("GESTURE 双击之后 copyFired=\(copyFired - copyBefore) selectFired=\(selectFired)")
        XCTAssertEqual(copyFired - copyBefore, 1,
                       "合成双击没有触发复制：要么 SwiftUI 没把这两击当成一次双击，要么手势被 Button 吃掉了")

        // 星标：点它只该翻收藏，不该选中这一行。
        let selectBeforeStar = selectFired
        click(starCenter, clickCount: 1)
        print("GESTURE 星标之后 favoriteFired=\(favoriteFired) selectFired=\(selectFired - selectBeforeStar)")
        XCTAssertEqual(favoriteFired, 1, "点行首星标没有触发收藏")
        XCTAssertEqual(selectFired, selectBeforeStar, "点星标顺带把这一行选中了：两个控件的命中区重叠")
    }

    /// 上面那条点的是**孤立的一行**。真实列表里行外面还套着 `ScrollView` + `LazyVStack` +
    /// 列表级的拖选 `DragGesture` + `.focusable()`，双击要穿过的正是这一层。
    /// 所以这里把整条侧栏摆上屏，从视图树里按几何找出行/星标的可点代理再点它。
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

        func clickCenter(of view: NSView, count: Int = 1) {
            let windowPoint = view.convert(NSPoint(x: view.bounds.midX, y: view.bounds.midY), to: nil)
            func event(_ type: NSEvent.EventType, _ clicks: Int) -> NSEvent? {
                NSEvent.mouseEvent(with: type, location: windowPoint, modifierFlags: [],
                                   timestamp: ProcessInfo.processInfo.systemUptime,
                                   windowNumber: window.windowNumber, context: nil,
                                   eventNumber: 0, clickCount: clicks, pressure: 1.0)
            }
            if let down = event(.leftMouseDown, count) { NSApp.sendEvent(down) }
            if let up = event(.leftMouseUp, count) { NSApp.sendEvent(up) }
            RunLoop.main.run(until: Date().addingTimeInterval(0.08))
        }

        // 每个可点击控件在宿主视图里都有一个 KeyViewProxy。按几何挑：
        // 实测 6 个星标 (16, y, 20×20) 与 6 个行 (38, y, 266×31)；
        // 另有 148×25 的筛选 pill 和 320×335 的滚动区 —— 第一版把 pill 当成了行，
        // 于是"点行没反应"又是探针点错了东西，不是产品。
        var starProxies: [NSView] = []
        var otherProxies: [NSView] = []
        func walk(_ view: NSView) {
            if String(describing: type(of: view)) == "KeyViewProxy" {
                if view.frame.width < 26 { starProxies.append(view) } else { otherProxies.append(view) }
            }
            for sub in view.subviews { walk(sub) }
        }
        walk(host)
        let starCandidates = starProxies.filter { abs($0.frame.width - 20) < 1 && abs($0.frame.height - 20) < 1 }
        let rowCandidates = otherProxies.filter {
            $0.frame.width > 200 && $0.frame.width < 290 && $0.frame.minX > 30 && $0.frame.height < 40
        }
        print("TREE2 星标代理=\(starCandidates.count) 行代理=\(rowCandidates.count) "
            + "收藏前=\(store.entries.filter(\.isFavorite).count) 写入=\(writer.writtenContents.count)")
        let star = try XCTUnwrap(starCandidates.max { $0.frame.minY < $1.frame.minY }, "找不到行首星标代理")
        // 刻意点**最下面**那一行：默认选中的是最上面那条，点它看不出"选中变了"。
        let row = try XCTUnwrap(rowCandidates.min { $0.frame.minY < $1.frame.minY }, "找不到行代理")

        let favoriteBefore = store.entries.filter(\.isFavorite).count
        clickCenter(of: star)
        XCTAssertEqual(store.entries.filter(\.isFavorite).count, favoriteBefore + 1,
                       "真实侧栏里点星标没有翻收藏（孤立一行时是好的 —— 说明外层容器吃掉了这一下）")

        let selectedBefore = store.selectedEntry?.id
        clickCenter(of: row)
        let clickedEntryID = store.selectedEntry?.id
        XCTAssertNotNil(clickedEntryID, "真实侧栏里点行没有选中任何东西")
        XCTAssertNotEqual(clickedEntryID, selectedBefore,
                          "真实侧栏里点行没有改选中：外层滚动/拖选手势把点击截走了")

        // 双击同一行：列表级 DragGesture 与行内双击并存。判据取剪贴板写入 ——
        // 这条路径唯一的硬后果，而且能同时验证"复制的就是刚点中的那条"。
        let writesBefore = writer.writtenContents.count
        clickCenter(of: row, count: 1)
        clickCenter(of: row, count: 2)
        XCTAssertEqual(writer.writtenContents.count, writesBefore + 1,
                       "真实侧栏里双击没有触发复制（写了 \(writer.writtenContents.count - writesBefore) 次）："
                       + "双击被外层滚动手势截走了，或者 SwiftUI 没把这两击当成一次双击")
        XCTAssertEqual(writer.writtenContents.last,
                       store.entries.first(where: { $0.id == clickedEntryID })?.content,
                       "复制出去的不是刚点中的那一条")
        XCTAssertEqual(store.entries.first?.id, clickedEntryID,
                       "复制走的是 .copyAndPromote，这条应当被顶到列表最前")
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
