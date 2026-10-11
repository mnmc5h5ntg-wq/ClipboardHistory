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

    func testDetailViewConsumesThePublishedInset() throws {
        let source = try productSource(named: "Views/DetailView.swift")
        XCTAssertTrue(source.contains(".padding(.top, chrome.detailContentTopInset)"),
                      "详情头部没把让位量接上 —— 灯带一变化它就不跟着动")
        XCTAssertTrue(source.contains("@ObservedObject private var chrome: WindowChromeMetrics"),
                      "没观察窗口的几何变化：首帧之后窗口变了，头部也不会跟着让")
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
