import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R568：折叠规格 §3 第②段开场的那一问（`docs/FOLD_DUO_SPEC_2026-11-03.md` §4 第三条）——
/// **取证通道到底分不分得出「真黑」与「透明」**。
///
/// 为什么这一格必须先存在：第③段整个演的是「右页 alpha 归零 ⇒ 露出桌面」，而如果两条取证通道
/// 都把透明区拍成黑，那条动画做完了也验不了 —— 规格 §4 明写「不能区分则动画做完也验不了，
/// 这本身就是阻塞项」。阻塞要由读数说，不由我猜。
///
/// 探针形状：一张两半已知的视图 —— 左半画不透明黑，右半什么都不画（透明）。
/// 三条判据各司其职，谁也不替谁签字：
/// ① 分类器（纯函数，CI 每轮跑）：给它两半的 RGBA，它说这条通道分不分得出；
/// ② 离屏那一把（本机与 CI 都跑）：量出这条通道实际给的那一对数；
/// ③ 真机那一把（环境键才跑）：量出合成通道给的那一对数。
///
/// ⚠ 与 R458 同族：只看 RGB 的旧尺会把透明区读成黑。这一格就是那条课的制度化。
@MainActor
final class TransparencyForensicsTests: XCTestCase {
    // MARK: - ⑥ D4 的「透明区必须点击穿透」：本轮判得到的那一半

    /// D4 那一串里"点击穿透"这一腿，在产品**有真透明区**之前判不了（第③段才有那块东西）。
    /// 但有一件今天就能判、而且第③段一定要靠它的事：**底衬永远不吃命中**。
    ///
    /// ⚠ 这条判据不假装"点击已经穿透"。同一格里现读的那句是反面事实：
    /// 容器在那块内容没覆盖的空区**仍然返回自己** ⇒ 像素 alpha 不路由鼠标，
    /// 窗口级穿透必须由第③段用 `contentShape` / `ignoresMouseEvents` 显式做（BACKLOG 647）。
    /// 所以这一格判的是"命中落到**谁**"，而它的刀（M1481）改的就是那一个"谁"。
    func testTheBackingLayerNeverWinsAHitTest() throws {
        let container = WindowBackingContainer(frame: NSRect(x: 0, y: 0, width: 200, height: 120))
        let host = NSView(frame: NSRect(x: 0, y: 0, width: 40, height: 40))
        container.addSubview(host)   // 内容缩在左上角，右下一块只有底衬可命中
        let backing = try XCTUnwrap(container.subviews.first(where: { $0 is WindowBackingView }),
                                    "容器里没有底衬那一层 ⇒ 这一格没有对象（产品状态那格应当同时红）")
        var winnerOfBacking = 0, winnerOfContainer = 0, winnerOfHost = 0, probed = 0
        for point in [NSPoint(x: 150, y: 90), NSPoint(x: 190, y: 110), NSPoint(x: 60, y: 60)] {
            guard let winner = container.hitTest(point) else { continue }
            probed += 1
            if winner === backing { winnerOfBacking += 1 }
            else if winner === container { winnerOfContainer += 1 }
            else if winner === host { winnerOfHost += 1 }
        }
        CaptureReadings.emit("TRANSPARENCY_HITTEST 探针=\(probed) 空区命中=底衬\(winnerOfBacking)"
            + "/容器\(winnerOfContainer)/内容\(winnerOfHost)"
            + " 底衬自身 hitTest=\(backing.hitTest(NSPoint(x: 150, y: 90)) == nil ? "让位" : "吃掉")"
            + " ⇒ 容器仍吃命中 ⇒ 窗口级穿透需要 contentShape/ignoresMouseEvents（第③段）")
        XCTAssertEqual(probed, 3, "三个探针点都没有命中任何视图 ⇒ 夹具没铺开，这一格没有内容")
        XCTAssertEqual(winnerOfBacking, 0,
                       "底衬在 \(winnerOfBacking) 个点上赢了命中 ⇒ 那层不吃命中的约定断了，"
                           + "第③段一让位，点击就会落到一个什么都不画的层上")
        XCTAssertNil(backing.hitTest(NSPoint(x: 150, y: 90)),
                     "底衬自己返回了视图 ⇒ 它开始吃整窗的交互（M1481 那一刀的形状）")
    }

    /// 左半不透明黑、右半不画（透明）。`fills` 那一档是正对照用的"整片不透明"。
    private final class HalfBlackView: NSView {
        var fills = false
        override var isFlipped: Bool { true }
        override func draw(_ dirtyRect: NSRect) {
            NSColor.black.setFill()
            let width = fills ? bounds.width : bounds.width / 2
            NSRect(x: 0, y: 0, width: width, height: bounds.height).fill()
        }
    }

    /// 分类器：两半读数一模一样 ⇒ 这条通道分不出「真黑」与「透明」。
    private func distinguishes(_ black: (r: Int, g: Int, b: Int, a: Int),
                               _ clear: (r: Int, g: Int, b: Int, a: Int)) -> Bool {
        black.r != clear.r || black.g != clear.g || black.b != clear.b || black.a != clear.a
    }

    private func pixel(_ rep: NSBitmapImageRep, _ x: Int, _ y: Int) -> (r: Int, g: Int, b: Int, a: Int)? {
        guard let color = rep.colorAt(x: x, y: y) else { return nil }
        return (Int((color.redComponent * 255).rounded()),
                Int((color.greenComponent * 255).rounded()),
                Int((color.blueComponent * 255).rounded()),
                Int((color.alphaComponent * 255).rounded()))
    }

    private func captureOffscreen(size: NSSize) throws -> NSBitmapImageRep {
        let view = HalfBlackView(frame: NSRect(origin: .zero, size: size))
        let rep = try XCTUnwrap(view.bitmapImageRepForCachingDisplay(in: view.bounds),
                                 "离屏通道拿不到可缓存的位图 ⇒ 这一格没有内容")
        view.cacheDisplay(in: view.bounds, to: rep)
        return rep
    }

    // MARK: - ① 分类器：纯数据，CI 每轮跑，不靠截图门

    func testTheChannelClassifierIsNotAlwaysTrue() throws {
        let same = (r: 0, g: 0, b: 0, a: 255)
        XCTAssertFalse(distinguishes(same, same),
                       "两半读数逐字相同却还判分得出 ⇒ 分类器是恒真的，那 §4 那一问就永远算通过")
        XCTAssertTrue(distinguishes(same, (r: 0, g: 0, b: 0, a: 0)),
                      "只差 alpha 也判不出 ⇒ 分类器漏了 alpha 那一路（透明与黑的差别往往只剩 alpha）")
        XCTAssertTrue(distinguishes(same, (r: 255, g: 0, b: 255, a: 255)),
                      "RGB 明显不同还判不出 ⇒ 分类器坏了")
        XCTAssertTrue(distinguishes(same, (r: 1, g: 0, b: 0, a: 255)),
                      "alpha 相同、R 差 1 也算分得出 —— 这条通道只要有差别就能用，不预设要多大")
    }

    // MARK: - ② 离屏那一把：量出这条通道实际给的那一对数

    /// R568 现读结论：`cacheDisplay` 那条路把透明半区涂成不透明黑（`a=255`、RGB 全 0），
    /// 与左半逐字相同 ⇒ 离屏通道分不出真黑与透明。这一格钉的是这条通道现在就是这样；
    /// 哪天有人把捕获路径换成带 alpha 的写法，这一格会红 ⇒ 逼着重新回答 §4 那一问。
    func testOffscreenChannelFlattensTransparentToOpaqueBlack() throws {
        let size = NSSize(width: 200, height: 120)
        let rep = try captureOffscreen(size: size)
        let black = try XCTUnwrap(pixel(rep, 50, 60), "左半区读不到像素 ⇒ 探针没落地")
        let clear = try XCTUnwrap(pixel(rep, 150, 60), "右半区读不到像素 ⇒ 探针没落地")
        let canTell = distinguishes(black, clear)
        CaptureReadings.emit("TRANSPARENCY_CHANNEL 通道=离屏 位图=\(rep.pixelsWide)x\(rep.pixelsHigh)"
            + " hasAlpha=\(rep.hasAlpha ? 1 : 0)"
            + " 黑半区=(r\(black.r),g\(black.g),b\(black.b),a\(black.a))"
            + " 透明半区=(r\(clear.r),g\(clear.g),b\(clear.b),a\(clear.a))"
            + " 分得出=\(canTell ? 1 : 0)")
        XCTAssertEqual(black.a, 255,
                       "左半是不透明黑，alpha 却不是 255 ⇒ 这条通道的 alpha 语义与预期不同，下面那格会误判")
        XCTAssertFalse(canTell,
                       "离屏通道这次分得出了（透明半区 a=\(clear.a)）⇒ §4 那一问的答案变了，"
                           + "646 与本节结论要按新读数重写，不许沿用旧结论")
    }

    // MARK: - ③ 真机那一把：合成通道（环境键才跑；隐私上背景用自己的纯色窗）

    func testRealScreenChannelSeparatesOpaqueBlackFromTransparent() throws {
        guard ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_REALSCREEN"] == "1" else {
            throw XCTSkip("REALSCREEN_CHANNEL_NOT_RUN=env-off —— 这一把要真屏合成，CI 与默认本机都不开；"
                + "没开就具名不判，不许读成「真机通道分得出」")
        }
        let magenta = NSColor(red: 1, green: 0, blue: 1, alpha: 1)
        let backdrop = NSWindow(contentRect: NSRect(x: 120, y: 400, width: 400, height: 300),
                                styleMask: [.borderless], backing: .buffered, defer: false)
        let plate = NSView(frame: NSRect(x: 0, y: 0, width: 400, height: 300))
        plate.wantsLayer = true
        plate.layer?.backgroundColor = magenta.cgColor
        backdrop.contentView = plate
        backdrop.isOpaque = true
        backdrop.backgroundColor = magenta
        backdrop.orderFrontRegardless()

        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 200, height: 120),
                              styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.contentView = HalfBlackView(frame: NSRect(x: 0, y: 0, width: 200, height: 120))
        window.setFrameOrigin(NSPoint(x: 200, y: 520))
        window.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        defer { window.orderOut(nil); backdrop.orderOut(nil) }

        let file = FileManager.default.temporaryDirectory
            .appendingPathComponent("r568-realscreen-\(UUID().uuidString).png")
        // `screencapture -R` 用的是**左上原点**，而 AppKit 的 screen 坐标是左下原点 ⇒ 必须换算，
        // 不换算就截到别处去（本轮第一次就是这么错的：读到 (172,195,172) 那种根本不是我画的色）。
        let frame = window.convertToScreen(window.contentView!.bounds)
        let primaryHeight = NSScreen.screens.first?.frame.height ?? 0
        let topLeftY = primaryHeight - (frame.minY + frame.height)
        let region = "-R\(Int(frame.minX)),\(Int(topLeftY)),\(Int(frame.width)),\(Int(frame.height))"
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
        proc.arguments = ["-x", region, file.path]
        try proc.run()
        proc.waitUntilExit()
        defer { try? FileManager.default.removeItem(at: file) }
        guard proc.terminationStatus == 0,
              let image = NSImage(contentsOf: file),
              let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()) else {
            XCTFail("真机截图这一把没落地（退出码 \(proc.terminationStatus)）⇒ 这一格没有内容")
            return
        }
        let midY = rep.pixelsHigh / 2
        let black = try XCTUnwrap(pixel(rep, rep.pixelsWide / 4, midY))
        let clear = try XCTUnwrap(pixel(rep, rep.pixelsWide * 3 / 4, midY))
        CaptureReadings.emit("TRANSPARENCY_CHANNEL 通道=真机 位图=\(rep.pixelsWide)x\(rep.pixelsHigh)"
            + " hasAlpha=\(rep.hasAlpha ? 1 : 0)"
            + " 黑半区=(r\(black.r),g\(black.g),b\(black.b),a\(black.a))"
            + " 透明半区=(r\(clear.r),g\(clear.g),b\(clear.b),a\(clear.a))"
            + " 分得出=\(distinguishes(black, clear) ? 1 : 0)")
        XCTAssertTrue(distinguishes(black, clear),
                      "真机通道里透明半区与不透明黑一模一样（\(black.r),\(black.g),\(black.b)）⇒ 它没有把背后合成进来，"
                          + "第③段「露出桌面」在这条通道上也不可判 ⇒ §4 那一问的答案是两条都不能，阻塞")
        XCTAssertGreaterThan(clear.r, 120,
                             "透明半区没合成到品红背景上（r=\(clear.r)）⇒ 截图区域没盖住探针窗，这一格读的不是它声称的对象")
    }

    // MARK: - ④½ §4 第二条：窗口阴影按**可见形状**算，还是按**框架矩形**算

    /// 三态分类（阈值钉在纯函数里，不许在判据正文里手比）。
    enum ShadowOutcome: Equatable {
        case noShadowAtAll
        case followsShape(rightDarkness: Double, leftDarkness: Double)
        case dragsRectangle(rightDarkness: Double, leftDarkness: Double)
    }

    /// 这条通道得先"看得见阴影"（左半下方那条带比远处参考暗 ≥0.02），
    /// 否则"右半没拖出矩形阴影"这句话是**没有对象**的，不是成立。
    /// 看得见之后再比两半：右半（透明那半）仍然暗 ⇒ 阴影跟的是框架矩形。
    static func shadowOutcome(left: Double, right: Double) -> ShadowOutcome {
        guard left >= 0.02 else { return .noShadowAtAll }
        return right >= 0.02 ? .dragsRectangle(rightDarkness: right, leftDarkness: left)
                             : .followsShape(rightDarkness: right, leftDarkness: left)
    }

    func testShadowOutcomeNeedsAVisibleShadowFirst() {
        XCTAssertEqual(Self.shadowOutcome(left: 0.01, right: 0.00), .noShadowAtAll,
                       "两半都不暗 ⇒ 这条通道根本没拍到阴影，不许读成「阴影跟着形状走」")
        XCTAssertEqual(Self.shadowOutcome(left: 0.01, right: 0.09), .noShadowAtAll,
                       "只有右半暗而左半（一定有内容那半）不暗 ⇒ 带取错了地方，整格没有对象")
        XCTAssertEqual(Self.shadowOutcome(left: 0.09, right: 0.01),
                       .followsShape(rightDarkness: 0.01, leftDarkness: 0.09))
        XCTAssertEqual(Self.shadowOutcome(left: 0.09, right: 0.08),
                       .dragsRectangle(rightDarkness: 0.08, leftDarkness: 0.09),
                       "两半一样暗 = 透明区照样拖出矩形阴影 ⇒ 必须落在 dragsRectangle 那一路，"
                           + "不许因为「差得小」就判成套形状")
    }

    /// 真机合成通道上的那一问：把「右半透明」这扇窗**连阴影带**一起拍进来，
    /// 比"左半下方的阴影带"与"右半下方的同一条带"各自比远处参考暗多少。
    ///
    /// 背景仍是自建的纯色窗（不用桌面：桌面会把用户的东西写进判据，而且每次都不一样），
    /// 而且 `hasShadow=false` —— 否则对照的是**那扇背景窗自己的**阴影。
    func testTheWindowShadowFollowsTheVisibleShapeNotTheFrame() throws {
        guard ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_REALSCREEN"] == "1" else {
            throw XCTSkip("REALSCREEN_SHADOW_NOT_RUN=env-off —— 阴影画在框架**之外**，离屏通道里根本没有那一层；"
                + "没开环境键就具名不判，不许读成「阴影跟形状」也不许读成「拖出矩形」")
        }
        let pad = 40.0
        let size = NSSize(width: 240, height: 140)
        let backdrop = NSWindow(contentRect: NSRect(x: 60, y: 200, width: 1000, height: 800),
                                styleMask: [.borderless], backing: .buffered, defer: false)
        let plate = NSView(frame: NSRect(x: 0, y: 0, width: 1000, height: 800))
        plate.wantsLayer = true
        plate.layer?.backgroundColor = NSColor(white: 0.85, alpha: 1).cgColor
        backdrop.contentView = plate
        backdrop.hasShadow = false
        backdrop.orderFrontRegardless()

        let probe = NSWindow(contentRect: NSRect(x: 0, y: 0, width: size.width, height: size.height),
                             styleMask: [.borderless], backing: .buffered, defer: false)
        let content = HalfBlackView(frame: NSRect(origin: .zero, size: size))
        probe.contentView = content
        probe.isOpaque = false
        probe.backgroundColor = .clear
        probe.hasShadow = true
        probe.setFrameOrigin(NSPoint(x: 400, y: 600))
        probe.orderFrontRegardless()
        defer { probe.orderOut(nil); backdrop.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))

        let primaryHeight = NSScreen.screens.first?.frame.height ?? 0
        func stats(fills: Bool) throws -> (left: Double, right: Double, scale: Double) {
            content.fills = fills
            content.needsDisplay = true
            RunLoop.main.run(until: Date().addingTimeInterval(0.4))
            let frame = probe.convertToScreen(content.bounds)
            let region = NSRect(x: frame.minX - pad, y: frame.minY - pad,
                                width: frame.width + 2 * pad, height: frame.height + 2 * pad)
            let file = FileManager.default.temporaryDirectory
                .appendingPathComponent("r568-shadow-\(fills ? "full" : "half")-\(UUID().uuidString).png")
            defer { try? FileManager.default.removeItem(at: file) }
            let topLeftY = primaryHeight - (region.minY + region.height)
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
            proc.arguments = ["-x", "-R\(Int(region.minX)),\(Int(topLeftY)),\(Int(region.width)),\(Int(region.height))",
                              file.path]
            try proc.run()
            proc.waitUntilExit()
            XCTAssertEqual(proc.terminationStatus, 0, "截图失败（\(fills ? "整片" : "半片")那臂）")
            let image = try XCTUnwrap(NSImage(contentsOf: file), "读不出图（\(fills ? "整片" : "半片")）")
            let rep = try XCTUnwrap(NSBitmapImageRep(data: image.tiffRepresentation ?? Data()))
            let scale = Double(rep.pixelsWide) / region.width
            func mean(rows: Range<Int>, cols: Range<Int>) -> Double {
                var sum = 0.0, count = 0
                for y in rows {
                    for x in cols {
                        guard y < rep.pixelsHigh, x < rep.pixelsWide,
                              let color = rep.colorAt(x: x, y: y) else { continue }
                        sum += 0.2126 * color.redComponent + 0.7152 * color.greenComponent
                            + 0.0722 * color.blueComponent
                        count += 1
                    }
                }
                return count > 0 ? sum / Double(count) : -1
            }
            let windowBottom = Int((pad + frame.height) * scale)
            let windowLeft = Int(pad * scale), windowRight = Int((pad + frame.width) * scale)
            let mid = (windowLeft + windowRight) / 2
            let near = (windowBottom + Int(3 * scale))..<(windowBottom + Int(11 * scale))
            let reference = (windowBottom + Int(28 * scale))..<(windowBottom + Int(36 * scale))
            guard reference.upperBound < rep.pixelsHigh else {
                XCTFail("参考带跑到帧外（帧高 \(rep.pixelsHigh)px、参考 \(reference.upperBound)）⇒ 尺的底没对齐")
                return (-1, -1, scale)
            }
            func darkness(cols: Range<Int>) -> Double {
                let nearMean = mean(rows: near, cols: cols)
                let refMean = mean(rows: reference, cols: cols)
                guard nearMean >= 0, refMean >= 0 else { return -1 }
                return refMean - nearMean
            }
            return (darkness(cols: windowLeft..<mid), darkness(cols: mid..<windowRight), scale)
        }

        // 正对照：整片不透明时两半下方都必须暗 ⇒ 这条通道看得见阴影，"半片那臂如果不暗"才有意义。
        let full = try stats(fills: true)
        CaptureReadings.emit("TRANSPARENCY_SHADOW 正对照(整片不透明) 左带暗=\(String(format: "%.4f", full.left))"
            + " 右带暗=\(String(format: "%.4f", full.right)) 外扩=\(Int(pad))pt 倍率=\(String(format: "%.2f", full.scale))x")
        XCTAssertGreaterThanOrEqual(full.left, 0.02,
                                   "整片不透明的窗在左半下方都读不出阴影（\(full.left)）⇒ 这条通道拍不到阴影，"
                                       + "下面那半片的读数没有对象")
        XCTAssertGreaterThanOrEqual(full.right, 0.02,
                                   "整片不透明的窗在右半下方读不出阴影（\(full.right)）而左半读得出 ⇒ "
                                       + "两半取的不是同一条带，尺坏")

        let half = try stats(fills: false)
        let outcome = Self.shadowOutcome(left: half.left, right: half.right)
        let shapeFollowed = outcome == .followsShape(rightDarkness: half.right, leftDarkness: half.left)
        let verdict = shapeFollowed ? "套形状" : "非套形状"
        CaptureReadings.emit("TRANSPARENCY_SHADOW 半片透明 左带暗=\(String(format: "%.4f", half.left))"
            + " 右带暗=\(String(format: "%.4f", half.right))"
            + " 判=\(verdict)")
        if outcome == .noShadowAtAll {
            XCTFail("半片那臂左带只暗 \(half.left) ⇒ 连一定有内容的那半都读不出阴影了（正对照刚读到 \(full.left)）"
                + " ⇒ 这一格没有对象，不许读成「透明区没拖阴影」")
        }
        XCTAssertTrue(shapeFollowed,
                      "透明那半下方仍然暗 \(half.right)（有内容那半 \(half.left)）⇒ 窗口阴影按**框架矩形**算，"
                          + "D4 那句「阴影跟随可见形状」不成立：第③段一让位，透明区就会拖着一条矩形阴影")
    }



    // MARK: - ④ §4 第一条：非不透明窗口会不会把侧栏材质弄淡/弄花

    /// 与上面两把同一个道理：材质这一问**离屏通道答不了**（R206/R552 早就量过 `cacheDisplay`
    /// 拍不出侧栏材质 —— 那一块在离屏缓冲里本来就是黑的），所以这一把也走真机合成通道。
    ///
    /// 背景仍是我自己开的纯色窗：非不透明窗口的材质会**采样背后的东西**，
    /// 用桌面当背景等于把用户的桌面写进判据（而且每次都不一样）。品红是常量。
    ///
    /// 形状：同一扇真产品窗口，先按今天的样子（不透明）拍一张，再按 D4 要的样子
    /// （非不透明 + 透明底）拍一张，比同一条侧栏带的**平均亮度**与**字墨数**。
    /// 两张贴图都在量完立刻删，不入仓。
    func testGoingNonOpaqueDoesNotWashOutTheSidebarMaterial() throws {
        guard ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_REALSCREEN"] == "1" else {
            throw XCTSkip("REALSCREEN_MATERIAL_NOT_RUN=env-off —— 材质这一问离屏通道答不了（R552 实测那块是黑的），"
                + "只能在真机合成通道上问；没开环境键就具名不判，不许读成「材质没变」")
        }
        let suite = "r568-material-\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 6, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text("材质对照用的记录，长度够读出侧栏那一列的字墨。"),
                                        thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        let controller = MainWindowCollapseController(defaults: defaults)
        let delegate = AppDelegate(historyStore: store, collapseController: controller)
        defer {
            for window in NSApplication.shared.windows where WindowManager.isAppContentWindow(window) {
                window.delegate = nil
                window.orderOut(nil)
            }
            WindowManager.forgetMainWindowForTesting()
            withExtendedLifetime(delegate) { _ in }
        }
        NSApplication.shared.setActivationPolicy(.regular)
        WindowManager.showMainWindow()
        RunLoop.main.run(until: Date().addingTimeInterval(0.8))
        let window = try XCTUnwrap(NSApplication.shared.windows.first { WindowManager.isAppContentWindow($0) },
                                   "没建出主窗口 ⇒ 这一格没有内容")
        let savedOpaque = window.isOpaque
        let savedBackground = window.backgroundColor
        defer {
            window.isOpaque = savedOpaque
            window.backgroundColor = savedBackground
        }

        let magenta = NSColor(red: 1, green: 0, blue: 1, alpha: 1)
        let backdrop = NSWindow(contentRect: NSRect(x: 60, y: 200, width: 1200, height: 900),
                                styleMask: [.borderless], backing: .buffered, defer: false)
        let plate = NSView(frame: NSRect(x: 0, y: 0, width: 1200, height: 900))
        plate.wantsLayer = true
        plate.layer?.backgroundColor = magenta.cgColor
        backdrop.contentView = plate
        backdrop.isOpaque = true
        backdrop.backgroundColor = magenta
        backdrop.orderFrontRegardless()
        window.makeKeyAndOrderFront(nil)
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        defer { backdrop.orderOut(nil) }

        let primaryHeight = NSScreen.screens.first?.frame.height ?? 0
        func shot(_ tag: String) throws -> NSBitmapImageRep {
            let file = FileManager.default.temporaryDirectory
                .appendingPathComponent("r568-material-\(tag)-\(UUID().uuidString).png")
            defer { try? FileManager.default.removeItem(at: file) }
            let frame = window.convertToScreen(window.contentView!.bounds)
            let region = "-R\(Int(frame.minX)),\(Int(primaryHeight - (frame.minY + frame.height))),\(Int(frame.width)),\(Int(frame.height))"
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
            proc.arguments = ["-x", region, file.path]
            try proc.run()
            proc.waitUntilExit()
            XCTAssertEqual(proc.terminationStatus, 0, "\(tag)：截图失败")
            let image = try XCTUnwrap(NSImage(contentsOf: file), "\(tag)：读不出图")
            return try XCTUnwrap(NSBitmapImageRep(data: image.tiffRepresentation ?? Data()))
        }
        /// 侧栏那一条带（x 20…300pt、y 120…400pt）的平均亮度与字墨数。
        func band(_ rep: NSBitmapImageRep) -> (mean: Double, ink: Int, magenta: Int) {
            let contentWidth = Double(window.contentLayoutRect.width)
            let sx = contentWidth > 1 ? Double(rep.pixelsWide) / contentWidth : 2.0
            var sum = 0.0, count = 0, ink = 0, magentaPixels = 0
            var samples: [Double] = []
            let x0 = Int(20 * sx), x1 = min(Int(300 * sx), rep.pixelsWide)
            let y0 = Int(120 * sx), y1 = min(Int(400 * sx), rep.pixelsHigh)
            for y in y0..<y1 {
                for x in x0..<x1 {
                    guard let color = rep.colorAt(x: x, y: y) else { continue }
                    let luma = 0.2126 * color.redComponent + 0.7152 * color.greenComponent
                        + 0.0722 * color.blueComponent
                    sum += luma; count += 1
                    samples.append(luma)
                    if color.redComponent > 0.75 && color.greenComponent < 0.35 && color.blueComponent > 0.75 {
                        magentaPixels += 1
                    }
                }
            }
            // 字墨按**偏离本带众数**数，不按绝对阈值：侧栏正文是 secondary 灰（亮度 ~0.55），
            // 用 `luma < 0.45` 会把一整列文字读成 0（本轮第一版就是这么错的，两臂都读到 ink=0）。
            samples.sort()
            let mode = samples.isEmpty ? 0.0 : samples[samples.count / 2]
            for value in samples where abs(value - mode) > 0.12 { ink += 1 }
            return (count > 0 ? sum / Double(count) : -1, ink, magentaPixels)
        }

        window.isOpaque = true
        window.backgroundColor = .windowBackgroundColor
        let opaque = try band(shot("opaque"))
        window.isOpaque = false
        window.backgroundColor = .clear
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        let clear = try band(shot("nonopaque"))
        CaptureReadings.emit("TRANSPARENCY_MATERIAL 不透明 均值=\(String(format: "%.4f", opaque.mean))"
            + " 字墨=\(opaque.ink) 品红漏出=\(opaque.magenta)"
            + " || 非不透明 均值=\(String(format: "%.4f", clear.mean))"
            + " 字墨=\(clear.ink) 品红漏出=\(clear.magenta)"
            + " || 均值差=\(String(format: "%.4f", abs(clear.mean - opaque.mean)))"
            + " 字墨比=\(String(format: "%.3f", Double(clear.ink) / max(Double(opaque.ink), 1)))")
        XCTAssertGreaterThan(opaque.ink, 200, "不透明那一拍的字墨就读不到 ⇒ 带的位置/尺度不对，这一格没有内容")
        XCTAssertEqual(clear.magenta, 0,
                       "非不透明之后侧栏带里漏出 \(clear.magenta) 个背景像素 ⇒ 材质没盖住这一列，"
                           + "背后的东西会直接透进列表区（D4 的代价比预期大，§4 第一条不成立）")
        XCTAssertLessThanOrEqual(abs(clear.mean - opaque.mean), 0.05,
                                "侧栏带平均亮度移动了 \(String(format: "%.4f", abs(clear.mean - opaque.mean)))"
                                    + " ⇒ 非不透明把材质弄淡/弄花了（§4 第一条不成立），按规格停在这里")
        XCTAssertGreaterThan(clear.ink, opaque.ink / 2,
                             "字墨从 \(opaque.ink) 掉到 \(clear.ink) ⇒ 列表文字被背景冲淡，§4 第一条不成立")

        // 负臂（这一臂才是 §4 第一条的**答案**）：把产品自己那层底衬藏起来再拍一次。
        // 没有它，上面四条断言证明的是一件"永远不会发生的事"——底衬可有可无；
        // 有了它，§4 那句"材质会不会变淡"被钉成一条**撤掉底衬就会红**的规则。
        guard let container = window.contentView as? WindowBackingContainer,
              let backing = container.subviews.first(where: { $0 is WindowBackingView }) else {
            XCTFail("负臂找不到底衬那一层 ⇒ 这一臂没有对象（产品状态那格应当同时红，别把它读成跳过）")
            return
        }
        backing.isHidden = true
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        let bare = try band(shot("no-backing"))
        backing.isHidden = false
        RunLoop.main.run(until: Date().addingTimeInterval(0.4))
        let restored = try band(shot("backing-restored"))
        CaptureReadings.emit("TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=\(String(format: "%.4f", bare.mean))"
            + " 字墨=\(bare.ink) 品红漏出=\(bare.magenta)"
            + " 均值移动=\(String(format: "%.4f", abs(bare.mean - opaque.mean)))"
            + " || 放回底衬 均值=\(String(format: "%.4f", restored.mean)) 品红漏出=\(restored.magenta)")
        XCTAssertGreaterThan(abs(bare.mean - opaque.mean), 0.05,
                             "撤掉底衬之后侧栏带只移动了 \(String(format: "%.4f", abs(bare.mean - opaque.mean))) ⇒ "
                                 + "底衬不承重，那层白画的（§4 第一条其实是「不会淡」，本轮的结论要重写）")
        XCTAssertGreaterThan(bare.magenta, 0,
                             "撤掉底衬后品红仍然漏不出（\(bare.magenta) 颗）⇒ 这条通道拍不到"
                                 + "「背后的东西进到了列表区」这件事，负臂没有对象")
        XCTAssertLessThanOrEqual(abs(restored.mean - opaque.mean), 0.05,
                                 "底衬放回去之后带仍然偏 \(String(format: "%.4f", abs(restored.mean - opaque.mean))) ⇒ "
                                     + "这一臂不可逆，读数不能当对照")
        XCTAssertEqual(restored.magenta, 0, "放回底衬后仍漏出 \(restored.magenta) 颗背景像素 ⇒ 撤/放这一臂没收干净")
    }

    // MARK: - ⑤ 产品状态：窗口非不透明，但观感由自己那层底衬保住

    /// 这一格判的是 D4 前置**在产品里真的成立**：窗口非不透明 + 透明底 + 自己的不透明底衬，
    /// 并且底衬在离屏捕获路径里也真的把不透明画出来了（带内 alpha 处处 255）——
    /// 后者是"356 张帧不许变"那件事的机器证人，不靠我事后重捕才发现。
    func testTheProductWindowIsNonOpaqueWithItsOwnOpaqueBacking() throws {
        let suite = "r568-state-\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 6, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text("非不透明状态判据用的记录。"),
                                        thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        let controller = MainWindowCollapseController(defaults: defaults)
        let delegate = AppDelegate(historyStore: store, collapseController: controller)
        NSApplication.shared.setActivationPolicy(.regular)
        defer {
            for window in NSApplication.shared.windows where WindowManager.isAppContentWindow(window) {
                window.delegate = nil
                window.orderOut(nil)
            }
            WindowManager.forgetMainWindowForTesting()
            withExtendedLifetime(delegate) { _ in }
        }
        WindowManager.showMainWindow()
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        let window = try XCTUnwrap(NSApplication.shared.windows.first { WindowManager.isAppContentWindow($0) },
                                   "没建出唯一主窗口 ⇒ 这一格没有内容")
        let content = try XCTUnwrap(window.contentView, "主窗口没有 contentView")
        let hasBacking = content.subviews.contains { $0 is WindowBackingView }
        XCTAssertEqual(window.isOpaque, false,
                       "窗口还是不透明的 ⇒ D4 的「让位」在第③段根本没有可归零的 alpha，规格前置没落地")
        XCTAssertEqual(window.backgroundColor.alphaComponent, 0, accuracy: 0.001,
                       "窗口底色不是全透明（alpha=\(window.backgroundColor.alphaComponent)）⇒ 非不透明只是名义上的")
        XCTAssertTrue(hasBacking,
                      "没有那层自己的不透明底衬 ⇒ 材质会开始采样桌面（本轮实测均值 0.931 → 0.666 就是这一层缺席的形状）")

        let rep = try XCTUnwrap(content.bitmapImageRepForCachingDisplay(in: content.bounds),
                                "离屏通道拿不到缓存位图 ⇒ 这一格没有内容")
        content.cacheDisplay(in: content.bounds, to: rep)
        var minAlpha = 256, samples = 0, transparent = 0
        var firstHole = ""
        var box = (minX: 1 << 30, maxX: 0, minY: 1 << 30, maxY: 0)
        for y in stride(from: 20, to: rep.pixelsHigh - 20, by: 7) {
            for x in stride(from: 20, to: rep.pixelsWide - 20, by: 7) {
                guard let color = rep.colorAt(x: x, y: y) else { continue }
                let a = Int((color.alphaComponent * 255).rounded())
                minAlpha = min(minAlpha, a)
                samples += 1
                if a < 255 {
                    transparent += 1
                    box.minX = min(box.minX, x); box.maxX = max(box.maxX, x)
                    box.minY = min(box.minY, y); box.maxY = max(box.maxY, y)
                    if firstHole.isEmpty {
                        firstHole = "(x\(x),y\(y)) a=\(a) rgb=(\(Int((color.redComponent * 255).rounded())),\(Int((color.greenComponent * 255).rounded())),\(Int((color.blueComponent * 255).rounded())))"
                    }
                }
            }
        }
        CaptureReadings.emit("TRANSPARENCY_STATE isOpaque=\(window.isOpaque ? 1 : 0)"
            + " 窗口底色alpha=\(String(format: "%.3f", window.backgroundColor.alphaComponent))"
            + " 底衬=\(hasBacking ? 1 : 0) 采样=\(samples)"
            + " 带内最小alpha=\(minAlpha == 256 ? -1 : minAlpha)"
            + " 半透明样本=\(transparent)/\(samples)"
            + " 洞范围=\(transparent > 0 ? "x[\(box.minX)..\(box.maxX)] y[\(box.minY)..\(box.maxY)] 位图=\(rep.pixelsWide)x\(rep.pixelsHigh) 首个=\(firstHole)" : "无")")
        XCTAssertGreaterThan(samples, 100, "只采到 \(samples) 个像素 ⇒ 探针没铺开，这一格没有内容")
        XCTAssertEqual(minAlpha, 255,
                       "内容里有 alpha=\(minAlpha) 的像素 ⇒ 底衬没把不透明画到捕获路径上，"
                           + "那 356 张帧会变（透明区在离屏里被涂成黑，R458 那一族）")
    }

}
