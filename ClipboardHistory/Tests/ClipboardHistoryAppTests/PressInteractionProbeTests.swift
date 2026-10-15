import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 真按下：合成一次真实的 `leftMouseDown`，按住不放，看画面到底变没变（R4）。
///
/// 为什么必须有这一条：`PressFeedbackTests` 已经钉住了表达（真值表）、可见性（分通道量像素）
/// 与接线（9 处、文件集合）。但那些都不经过 AppKit 的鼠标跟踪 ——
/// **"我写了一个会在按下时缩放的 ButtonStyle"离"用户按下去真的看到了缩放"之间，
/// 还差一个事件循环**。上一轮就有过一次"源码已接、产物未量"的账（D-055 / CI 那三条），
/// 所以这条探针存在的首要目的是：如果合成事件驱动不了它，我要先知道并且如实记账，
/// 而不是拿"我加了 `.pressedStyle`"当已交付。
///
/// 需要 `CLIPBOARD_HISTORY_UI_INTERACTION=1`（报告型，CI 上跑不到就记 not-run）。
///
/// 不覆盖管线：这里只判"按下那一下画面变了没有"。点击的**结果**（收藏、复制、筛选）
/// 由 `RowInteractionTests` 与 `PipelineAcceptanceTests` 管。
final class PressInteractionProbeTests: XCTestCase {

    @MainActor
    func testHoldingAnIconButtonChangesThePicture() throws {
        try skipUnlessEnabled()

        // 送达回执：事件到底有没有走到那颗按钮。没有这一句，"按住读不出差别"有两种解释
        // （事件根本没到 / 到了但按下态画在 `cacheDisplay` 抓不到的图层里），而处置完全不同。
        let delivery = DeliveryBox()
        let pill = GlassPill(isFavorite: false, favoriteAction: { delivery.count += 1 },
                             isPinned: false, pinAction: {},
                             copyAction: {}, deleteAction: {})
        let host = NSHostingView(rootView: AnyView(pill))
        let size = NSSize(width: 120, height: 232)
        host.frame = NSRect(origin: .zero, size: size)
        let window = NSWindow(contentRect: NSRect(x: 260, y: 220, width: size.width, height: size.height),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        defer { window.orderOut(nil) }

        // 坐标不猜、也不问无障碍树（那条 API 在不同版本上返回类型不一致，实测踩过）：
        // 浮层的布局是**它自己的常数**决定的 —— padding 4、每颗 44pt、分隔线 1pt，
        // 四竖排从上往下。算出来之后还要用"按下有没有变化"反过来验坐标点对了没有。
        let padding: CGFloat = 4
        let button: CGFloat = 44
        let divider: CGFloat = 1
        let centers: [NSPoint] = (0..<4).map { index in
            let fromTop = padding + button / 2 + CGFloat(index) * (button + divider)
            return NSPoint(x: size.width / 2, y: size.height - fromTop)
        }

        var best = (index: -1, held: 0.0, released: 0.0)
        var deliveries = 0
        for (index, point) in centers.enumerated() {
            let before = delivery.count
            let idle = Self.bitmap(of: host)
            Self.send(.leftMouseDown, to: window, at: point)
            RunLoop.main.run(until: Date().addingTimeInterval(0.06))
            let held = Self.bitmap(of: host)
            Self.send(.leftMouseUp, to: window, at: point)
            RunLoop.main.run(until: Date().addingTimeInterval(0.2))
            let released = Self.bitmap(of: host)
            let heldDelta = Self.changedFraction(idle, held)
            let releasedDelta = Self.changedFraction(idle, released)
            // 两轴分开打（R77）：`按住差` 是并集那一根（历史字段名，账本引用过），
            // 后面三个数是"这一下到底动在哪根轴上"。少了后三列，一条只在 alpha 上的
            // 按压反馈会被读成"0.0000 ⇒ 这条路量不到"，而那正是 U-132 的形状。
            print("PRESS_PROBE 第\(index + 1)颗 送达=\(delivery.count - before) 点=(\(Int(point.x)),\(Int(point.y))) "
                + "按住差=\(String(format: "%.4f", heldDelta)) 松手后残余=\(String(format: "%.4f", releasedDelta)) "
                + "按住[" + Self.axisLine(idle, held) + "] 松手[" + Self.axisLine(idle, released) + "]")
            deliveries += delivery.count - before
            if heldDelta > best.held { best = (index, heldDelta, releasedDelta) }
        }
        let heldDelta = best.held
        let releasedDelta = best.released

        guard heldDelta > 0.0002 else {
            // 这一支不是"判据失败"，是"这条路量不到"：合成事件可能进不了 Button 的跟踪循环，
            // 也可能按压态真的没接上。两者必须分开写，否则下一次会把尺子的盲区读成产品缺陷。
            let reason = deliveries > 0
                ? "delivered-but-unobservable：事件走到了那颗按钮（送达 \(deliveries) 次），"
                    + "但 `cacheDisplay` 抓不到按下态那一层 —— 它抓的是模型树，与 D-055 那条同一族"
                    + " ⇒ 按压态记为'源码已接、产物未量'，转人工批次 12.1"
                : "not-delivered：合成事件没走到那颗按钮（\(Self.keyStateNote())）。"
                    + "SwiftUI 的 Button 跟踪要看窗口是不是 key，而 xctest 进程里起不来"
                    + "（`UIInteractionProbeTests` 里 NSTableView 那一族就是靠绕开这一点才可测的）"
                    + " ⇒ 这条路量不到，不能据此判产品；转人工批次 12.1"
            print("INTERACTION_NOT_RUN=synthetic-mouse-\(deliveries > 0 ? "delivered" : "missing")："
                + "按住与没按住读不出差别（\(String(format: "%.4f", heldDelta))）。\(reason)")
            throw XCTSkip("INTERACTION_NOT_RUN=synthetic-mouse-\(deliveries > 0 ? "delivered" : "missing")")
        }
        XCTAssertLessThan(releasedDelta, 0.002,
                          "松手之后画面还停在按下态（残余 \(String(format: "%.4f", releasedDelta))）⇒ 按压态粘住了")
    }

    /// 把"当时窗口到底是什么状态"打进结论里：只说"事件没到"分不开"探针坏了"与"平台不给 key"。
    @MainActor
    private static func keyStateNote() -> String {
        let window = NSApp.keyWindow
        return "keyWindow=\(window == nil ? "nil" : "有") isActive=\(NSApp.isActive)"
    }

    /// 计数盒子（class 才能被闭包改到）。
    final class DeliveryBox { var count = 0 }

    // MARK: - 夹具

    private func skipUnlessEnabled() throws {
        let flag = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_INTERACTION"]
        try XCTSkipIf(flag == nil || flag?.isEmpty == true,
                      "未设置 CLIPBOARD_HISTORY_UI_INTERACTION，跳过在屏交互探针")
    }

    @MainActor
    private static func send(_ type: NSEvent.EventType, to window: NSWindow, at point: NSPoint) {
        let event = NSEvent.mouseEvent(with: type, location: point, modifierFlags: [],
                                        timestamp: ProcessInfo.processInfo.systemUptime,
                                        windowNumber: window.windowNumber, context: nil,
                                        eventNumber: 1, clickCount: 1, pressure: type == .leftMouseDown ? 1 : 0)
        if let event { window.sendEvent(event) }
    }

    @MainActor
    private static func bitmap(of view: NSView) -> [UInt8] {
        guard let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { return [] }
        view.cacheDisplay(in: view.bounds, to: rep)
        guard let cg = rep.cgImage else { return [] }
        let width = cg.width, height = cg.height
        var buffer = [UInt8](repeating: 0, count: width * height * 4)
        let space = CGColorSpace(name: CGColorSpace.sRGB)!
        let context = CGContext(data: &buffer, width: width, height: height, bitsPerComponent: 8,
                                bytesPerRow: width * 4, space: space,
                                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
        context.draw(cg, in: CGRect(x: 0, y: 0, width: width, height: height))
        return buffer
    }

    /// 两态相减：任一通道动过地板就算这一像素变了（R77 / BACKLOG 107）。
    ///
    /// 为什么要把 alpha 加进来：`bitmap(of:)` 把 `cacheDisplay` 的位图 draw 进**零初始化的预乘缓冲区**，
    /// 于是"暗墨变透明"这一族在 R/G/B 上就是 0→0 —— 与 MotionFilmstripTests 的 `raster` 同一个形状，
    /// 而 R76 的 U-132 已经在这条通道上实物量到过（两张 PNG 去掉 alpha 逐像素相同）。
    /// 这一族的失败形状是**假 not-run**：按住那颗按钮时若只有 alpha 在动，旧尺子读 0，
    /// 于是走 `heldDelta > 0.0002` 那一支报"这条路量不到"，把"我没看见"写成"它没动"。
    ///
    /// 三条 RGB 通道的地板原样保留（历史读数 `PRESS_PROBE 按住差=…` 账本里引用过），
    /// alpha 用的是同一道 6/255 —— 两轴共用门槛，那两个数才可比。
    @MainActor
    private static func changedFraction(_ a: [UInt8], _ b: [UInt8]) -> Double {
        guard !a.isEmpty, a.count == b.count else { return 0 }
        var changed = 0
        var total = 0
        var index = 0
        while index + 3 < a.count {
            total += 1
            let delta = abs(Int(a[index]) - Int(b[index]))
                + abs(Int(a[index + 1]) - Int(b[index + 1]))
                + abs(Int(a[index + 2]) - Int(b[index + 2]))
            let alphaDelta = abs(Int(a[index + 3]) - Int(b[index + 3]))
            if delta > 6 || alphaDelta > 6 { changed += 1 }
            index += 4 * 7   // 每 7 个像素采一个，控制耗时
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    /// alpha 那一通道单独的变化占比（R77）。
    /// 只为把"这一档只在 alpha 上"这件事打进读数，不参与任何断言。
    @MainActor
    static func alphaFraction(_ a: [UInt8], _ b: [UInt8]) -> Double {
        guard !a.isEmpty, a.count == b.count else { return 0 }
        var changed = 0
        var total = 0
        var index = 0
        while index + 3 < a.count {
            total += 1
            if abs(Int(a[index + 3]) - Int(b[index + 3])) > 6 { changed += 1 }
            index += 4 * 7
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    /// RGB 那一通道单独的变化占比：地板与 `changedFraction` 里那条三通道求和是同一道。
    /// 与上面那条一起就是 `R77` 要求每个两态判据打出来的"两根轴"。
    @MainActor
    static func rgbFraction(_ a: [UInt8], _ b: [UInt8]) -> Double {
        guard !a.isEmpty, a.count == b.count else { return 0 }
        var changed = 0
        var total = 0
        var index = 0
        while index + 3 < a.count {
            total += 1
            let delta = abs(Int(a[index]) - Int(b[index]))
                + abs(Int(a[index + 1]) - Int(b[index + 1]))
                + abs(Int(a[index + 2]) - Int(b[index + 2]))
            if delta > 6 { changed += 1 }
            index += 4 * 7
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    /// 一行两轴读数：`亮度差=… alpha差=… 并集差=…`。
    /// 三个数一起打，是因为只打并集就分不出"这一下到底在哪根轴上"（R76 那一档就是靠这个分出来的）。
    @MainActor
    static func axisLine(_ a: [UInt8], _ b: [UInt8]) -> String {
        func p(_ v: Double) -> String { String(format: "%.4f", v) }
        return "亮度差=\(p(rgbFraction(a, b))) alpha差=\(p(alphaFraction(a, b))) 并集差=\(p(changedFraction(a, b)))"
    }
}
