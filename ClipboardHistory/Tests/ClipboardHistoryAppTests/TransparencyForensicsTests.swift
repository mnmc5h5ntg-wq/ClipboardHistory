import AppKit
import SwiftUI
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

    // MARK: - ⓪ R571 ③：第二条离屏通道 —— 自己建的带 alpha 位图上下文（规格 §4 第三问 / 646 第一条出路）

    /// 把一棵视图树渲进**我自己建的、带 alpha 的位图上下文**，栅格由参数给（2x / 1x 在同一台机器上都能读到），
    /// 而不是问 AppKit 要一块 backing store。
    ///
    /// 为什么是这一条：上一轮的读数是"离屏通道能不能保留 alpha **依倍率而定**"（本机 2x `分得出=0`、
    /// runner 1x `分得出=1`），而第③段的 D12「透明区 alpha 归零」需要一条**两档给同一个答案**的通道。
    /// 本轮用诊断臂逐条排除，剩下这条是唯一走得通的（读数在 `.scratch/motion-audit-2/r571-readings.md`）：
    /// · `bitmapImageRepForCachingDisplay` 给的位图 `bitmapFormat=0`（**没有 alpha 平面**）⇒ 透明半区被涂成 `a=255`；
    /// · 自建 alpha 位图喂给 `cacheDisplay` ⇒ 它根本不往里写（四个采样点全 `a=0`，连黑半区也是）；
    /// · `NSHostingView.draw(_:)` ⇒ SwiftUI 不在 `draw(_:)` 里画 ⇒ 同样全 `a=0`；
    /// · `dataWithPDF(inside:)` 再栅格化 ⇒ 产品那棵树画不出内容（只有我铺的背景色留下）；
    /// · `layer.render(in:)` 进 `premultipliedLast` 上下文、且图层声明**非不透明** ⇒ 黑半区 `a=255`、透明半区 `a=0`，
    ///   2x 与 1x 两种栅格都给同一个答案 —— 这就是下面这条路。
    ///
    /// ⚠ 像素读法必须是**原始字节**：同一条通道上 `NSBitmapImageRep.colorAt` 把 raw `a=255` 的那个点读成 `a=0`
    /// （诊断臂逐字对照过）⇒ 用 `colorAt` 会把"保住了 alpha"读成"整幅全透明"，那是一条假绿。
    private func captureTwoHalvesViaAlphaLayer(size: NSSize, scale: Double) throws
        -> (pixelsWide: Int, pixelsHigh: Int, black: (r: Int, g: Int, b: Int, a: Int),
            clear: (r: Int, g: Int, b: Int, a: Int)) {
        let hosting = NSHostingView(rootView: AnyView(
            HStack(spacing: 0) {
                Color.black
                Color.clear
            }
            .frame(width: size.width, height: size.height)))
        hosting.frame = NSRect(origin: .zero, size: size)
        hosting.wantsLayer = true
        hosting.layer?.isOpaque = false
        // 载体窗：SwiftUI 的外观解析与图层内容需要一个归属；刻意用 borderless + 不上屏，
        // 于是它既不会被 `CAPTURE_FOREIGN_WINDOW` 那条读数记成"捕获期间有 app 内容窗"，
        // 也不碰产品那条建窗路（不会写 `detailContentTopInset` 那格全局）。
        let window = NSWindow(contentRect: NSRect(origin: .zero, size: size),
                              styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.contentView = hosting
        defer { window.orderOut(nil) }
        hosting.layoutSubtreeIfNeeded()

        let pw = max(1, Int((size.width * scale).rounded()))
        let ph = max(1, Int((size.height * scale).rounded()))
        let layer = try XCTUnwrap(hosting.layer,
                                  "hosting 没有图层 ⇒ layer.render 这条路没有对象")
        layer.frame = CGRect(x: 0, y: 0, width: size.width, height: size.height)
        let raster = try renderLayerIntoAlphaRaster(layer, pixelsWide: pw, pixelsHigh: ph, size: size)
        let black = try XCTUnwrap(raster.rgba(topX: Int(size.width * scale * 0.25),
                                              topY: Int(size.height * scale * 0.5)),
                                  "黑半区读不到像素 ⇒ 这条通道的探针没落地")
        let clear = try XCTUnwrap(raster.rgba(topX: Int(size.width * scale * 0.75),
                                              topY: Int(size.height * scale * 0.5)),
                                  "透明半区读不到像素 ⇒ 这条通道的探针没落地")
        return (pw, ph, black, clear)
    }

    /// 这条通道的**唯一一块缓冲**从这里出去：`premultipliedLast`、不预先铺底、栅格由参数给。
    /// 「不预先铺底」就是 M1495/M1499 那一刀打的地方 —— 它刻意只有一处，
    /// 免得同一件坏法有两行写法、刀只能钉住其中一行（R568 那族「两处设置只留一处」同一课）。
    private func renderLayerIntoAlphaRaster(_ layer: CALayer, pixelsWide: Int, pixelsHigh: Int,
                                            size: NSSize) throws -> AlphaRaster {
        let space = CGColorSpace(name: CGColorSpace.sRGB) ?? CGColorSpaceCreateDeviceRGB()
        let context = try XCTUnwrap(CGContext(data: nil, width: pixelsWide, height: pixelsHigh,
                                              bitsPerComponent: 8, bytesPerRow: pixelsWide * 4,
                                              space: space,
                                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue),
                                    "建不出带 alpha 的位图上下文 ⇒ 这条通道今天不存在")
        context.scaleBy(x: CGFloat(pixelsWide) / size.width, y: CGFloat(pixelsHigh) / size.height)
        layer.render(in: context)
        let buffer = try XCTUnwrap(context.data, "上下文没有缓冲 ⇒ 读不到像素")
        let bytes = buffer.withMemoryRebound(to: UInt8.self, capacity: pixelsWide * pixelsHigh * 4) {
            Array(UnsafeBufferPointer(start: $0, count: pixelsWide * pixelsHigh * 4))
        }
        return AlphaRaster(pixelsWide: pixelsWide, pixelsHigh: pixelsHigh, bytes: bytes)
    }

    /// 一条通道拿到的栅格。像素**必须读原始字节**：同一条通道上 `NSBitmapImageRep.colorAt`
    /// 把 raw `a=255` 的那个点读成 `a=0`（R571 诊断臂逐字对照过）⇒ 用它会把"保住了 alpha"
    /// 读成"整幅全透明"，那是一条会自我庆祝的假绿。
    struct AlphaRaster {
        let pixelsWide: Int
        let pixelsHigh: Int
        let bytes: [UInt8]

        /// `topX/topY` 是"从顶往下"的探针坐标。**内存第 0 行就是顶行**：本轮拿旧通道那张当参照
        /// 两种假设各数一次异类（`/tmp/r572/orient.log`）—— 不翻 0/20160、翻 y 5002/20160、
        /// 只翻 x 1565、两个都翻 5431 ⇒ 这里不许再翻一次（翻了就把同一棵树读成两棵不同的）。
        func rgba(topX: Int, topY: Int) -> (r: Int, g: Int, b: Int, a: Int)? {
            guard topX >= 0, topX < pixelsWide, topY >= 0, topY < pixelsHigh else { return nil }
            let o = topY * pixelsWide * 4 + x4(topX)
            guard o + 3 < bytes.count else { return nil }
            return (Int(bytes[o]), Int(bytes[o + 1]), Int(bytes[o + 2]), Int(bytes[o + 3]))
        }

        private func x4(_ x: Int) -> Int { x * 4 }

        /// alpha 三分数（不透明 / 全透明 / 半透明）+ 「有没有画东西进来」的证人。
        /// 采样口径与旧通道同一句：栅格里每 `stride` 个像素取一个 —— 两通道要能逐字对拍，
        /// 就不能一个数整幅、另一个数网格（R565 那一课的"跨通道量要同一口径"）。
        func profile(step: Int) -> AlphaTriple {
            var samples = 0, opaque = 0, clear = 0, partial = 0, ink = 0
            for y in stride(from: 0, to: pixelsHigh, by: step) {
                for x in stride(from: 0, to: pixelsWide, by: step) {
                    guard let p = rgba(topX: x, topY: y) else { continue }
                    samples += 1
                    if p.a == 0 { clear += 1 } else if p.a == 255 { opaque += 1 } else { partial += 1 }
                    if p.r + p.g + p.b > 0 { ink += 1 }
                }
            }
            return AlphaTriple(samples: samples, opaque: opaque, clear: clear,
                               partial: partial, ink: ink)
        }
    }

    /// 一棵**产品真实视图树**（不是两半已知的合成夹具）：名字、建法、尺寸。
    /// 两棵各有用处：主窗那棵是第③段真要判的对象，浮层那棵是产品今天**唯一真有透明区**的树。
    private func productTree(_ which: String) throws
        -> (name: String, view: NSView, size: NSSize, teardown: () -> Void) {
        switch which {
        case "主窗":
            let size = NSSize(width: 420, height: 300)
            let host = NSHostingView(rootView: AnyView(ContentView(historyStore: try fixtureStore(tag: "r572-main"))))
            host.frame = NSRect(origin: .zero, size: size)
            let container = try XCTUnwrap(WindowBackingContainer.wrapping(host), "主窗那棵树包不出容器")
            container.frame = NSRect(origin: .zero, size: size)
            let window = NSWindow(contentRect: NSRect(origin: .zero, size: size),
                                  styleMask: [.borderless], backing: .buffered, defer: false)
            window.isOpaque = false
            window.backgroundColor = .clear
            window.contentView = container
            window.appearance = NSAppearance(named: .aqua)
            return ("主窗", container, size, { window.orderOut(nil) })
        default:
            // 浮层走产品自己的入口：`QuickPickController.windowForCapture`（不 `orderFront`、不 `activate`，
            // 所以它既不打扰用户在跑的那扇窗，也不会被 `CAPTURE_FOREIGN_WINDOW` 记成"捕获期间有 app 内容窗"）。
            let store = try fixtureStore(tag: "r572-quickpick", entries: 6)
            let controller = QuickPickController(historyStore: { store }, commit: { _ in })
            let panel = try XCTUnwrap(controller.windowForCapture(query: ""), "浮层面板没建起来 ⇒ 这一格没有对象")
            let content = try XCTUnwrap(panel.contentView, "浮层没有 contentView")
            return ("浮层", content, content.bounds.size, {
                withExtendedLifetime(controller) { _ in }
                panel.orderOut(nil)
            })
        }
    }

    /// 判据自带的夹具store：临时 suite、固定文本，**一个字都不来自用户**（隐私规矩与 356 张帧同一套）。
    private func fixtureStore(tag: String, entries: Int = 3) throws -> HistoryStore {
        let suite = "\(tag)-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defaults.removePersistentDomain(forName: suite)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 8, maxAgeDays: nil))
        for i in 1...entries {
            store.add(ClipboardIntake.Entry(content: .text("产品树取证判据的固定测试文本 \(i)。"),
                                            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                                            sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                      timestamp: Date(timeIntervalSince1970: TimeInterval(i)))
        }
        return store
    }

    /// 650 的成对判法：同一棵树、同一块栅格，**旧通道走一遍之后再走新通道** ⇒ 两边的 alpha 三分数必须逐字相同。
    /// 为什么必须成对判，而不是只判"新通道分得出"：本轮读到的反面事实是 ——
    /// 少了这一步时 `layer.render` 对主窗那棵树读到**整幅 a=0**（`不透明=0/20160`、`有墨=0`），
    /// 而 a=0 正是第③段要判的「alpha 归零」那一格 ⇒ 在这条通道里「没画」与「归零」是同一个形状。
    /// 只有"与那一条**确实画得出内容**的旧通道同数"这句话把两者分开。
    /// 同一棵树、同一块栅格上两条通道的**逐点对照**结果。
    /// 判的是"同一颗探针两条通道给同一类"，而不是各自的总数落在某个容差里 ——
    /// 容差会把"少画了一块"糊过去，而逐点判法不会：那块没了，那个位置就从 255 变成 0，异类数就跳。
    /// ⚠ 反面事实（本轮自己造的）：第一版这里读到浮层差 142 颗采样、逐点异类 5434，
    /// 我差点把它写成"两条通道在边缘带就是不同数"的契约。**实际是我把内存行序当成了底朝上**
    /// （探针 `/tmp/r572/orient.log`：不翻 0/20160 异类、翻 y 5002、只翻 x 1565）⇒ 同一棵树被我读成了
    /// 两棵不同的树。方向修正后两通道逐点 0 异类、三分数逐字相等。教训写进 650 追记。
    struct ProductTreePairing {
        let name: String
        let rasterW: Int
        let rasterH: Int
        let samples: Int
        let old: AlphaTriple
        let new: AlphaTriple
        let cold: AlphaTriple
        let opaqueProbe: (x: Int, y: Int)?
        let clearProbe: (x: Int, y: Int)?
        /// 两通道分类不同的采样点数（按 全透明 / 半透明 / 不透明 三类判）。
        let disagreements: Int
        /// 新通道在**旧通道选出的**那颗不透明探针上读到 255 吗（"内容真的画进来了"的证人）。
        let opaqueProbeAgrees: Bool
        /// 新通道在旧通道选出的那颗真透明探针上读到 0 吗；旧通道没这种探针时是 nil（无对象，不是通过）。
        let clearProbeAgrees: Bool?

        var line: String {
            "位图=\(rasterW)x\(rasterH) 采样=\(samples) 旧三分=\(old.opaque)/\(old.clear)/\(old.partial)"
                + " 新三分=\(new.opaque)/\(new.clear)/\(new.partial) 逐点异类=\(disagreements)"
                + " 旧有墨=\(old.ink) 新有墨=\(new.ink)"
        }

        var driftLine: String {
            "TRANSPARENCY_PRODUCT_ALPHA_DRIFT 树=\(name) 不透明差=\(new.opaque - old.opaque)"
                + " 全透明差=\(new.clear - old.clear) 半透明差=\(new.partial - old.partial)"
                + " 采样=\(samples) 逐点异类=\(disagreements) 旧有墨=\(old.ink) 新有墨=\(new.ink)"
                + " ⇒ 有墨两条不相等是旧通道 `colorAt` 的解码差，不是画差（R571 读过同一颗坑）"
        }
    }

    struct AlphaTriple {
        let samples: Int, opaque: Int, clear: Int, partial: Int, ink: Int
    }

    private func alphaProfile(of rep: NSBitmapImageRep, step: Int) -> AlphaTriple {
        var samples = 0, opaque = 0, clear = 0, partial = 0, ink = 0
        for y in stride(from: 0, to: rep.pixelsHigh, by: step) {
            for x in stride(from: 0, to: rep.pixelsWide, by: step) {
                guard let p = pixel(rep, x, y) else { continue }
                samples += 1
                if p.a == 0 { clear += 1 } else if p.a == 255 { opaque += 1 } else { partial += 1 }
                if p.r + p.g + p.b > 0 { ink += 1 }
            }
        }
        return AlphaTriple(samples: samples, opaque: opaque, clear: clear, partial: partial, ink: ink)
    }

    private func captureProductTreePaired(_ which: String) throws -> ProductTreePairing {
        let tree = try productTree(which)
        defer { tree.teardown() }
        let view = tree.view
        func forceLayer(_ v: NSView) {
            v.wantsLayer = true
            v.subviews.forEach(forceLayer)
        }
        forceLayer(view)
        view.layoutSubtreeIfNeeded()
        let layer = try XCTUnwrap(view.layer, "\(tree.name)：这棵树没有图层 ⇒ layer.render 这条路没有对象")
        layer.frame = CGRect(x: 0, y: 0, width: tree.size.width, height: tree.size.height)

        // 前置缺席那一臂：只打点、不判（它是"为什么必须成对"的证人，不是一条契约 ——
        // 把仪器现状钉成契约是 R465 那一族"静态断言把 bug 钉成规矩"的形状）。
        let cold = try renderLayerIntoAlphaRaster(layer,
                                                  pixelsWide: max(1, Int((tree.size.width * 2).rounded())),
                                                  pixelsHigh: max(1, Int((tree.size.height * 2).rounded())),
                                                  size: tree.size).profile(step: 5)
        CaptureReadings.emit("TRANSPARENCY_PRODUCT_ALPHA 树=" + tree.name + " 前置=缺席 采样=\(cold.samples)"
            + " 不透明=\(cold.opaque) 全透明=\(cold.clear) 有墨=\(cold.ink)"
            + " ⇒ 这一臂的 a=0 不能当「alpha 归零」用")

        // 旧通道先画一遍：它既当**探针的来源**（哪颗像素真被产品画成不透明 / 哪颗真是透明），
        // 也当这条新通道的焐热前置（本轮实测：少了它，新通道对主窗那棵树读到整幅 a=0）。
        let rep = try XCTUnwrap(view.bitmapImageRepForCachingDisplay(in: view.bounds),
                                "\(tree.name)：旧通道拿不到位图 ⇒ 这一格没有内容")
        view.cacheDisplay(in: view.bounds, to: rep)
        let old = alphaProfile(of: rep, step: 5)
        let raster = try renderLayerIntoAlphaRaster(layer, pixelsWide: rep.pixelsWide,
                                                    pixelsHigh: rep.pixelsHigh, size: tree.size)
        let warm = raster.profile(step: 5)

        // 逐点对照：探针由**旧通道**选，新通道必须在同一颗探针上给同一类。
        var opaqueProbe: (x: Int, y: Int)? = nil
        var clearProbe: (x: Int, y: Int)? = nil
        var different = 0
        for y in stride(from: 0, to: rep.pixelsHigh, by: 5) {
            for x in stride(from: 0, to: rep.pixelsWide, by: 5) {
                guard let before = pixel(rep, x, y), let after = raster.rgba(topX: x, topY: y) else { continue }
                if alphaClass(before) != alphaClass(after) { different += 1 }
                if opaqueProbe == nil, before.a == 255 { opaqueProbe = (x, y) }
                if clearProbe == nil, before.a == 0 { clearProbe = (x, y) }
            }
        }
        let opaqueAgrees: Bool
        if let probe = opaqueProbe, let p = raster.rgba(topX: probe.x, topY: probe.y) {
            opaqueAgrees = p.a == 255
        } else {
            opaqueAgrees = false
        }
        let clearAgrees: Bool?
        if let probe = clearProbe, let p = raster.rgba(topX: probe.x, topY: probe.y) {
            clearAgrees = p.a == 0
        } else {
            clearAgrees = nil
        }
        return ProductTreePairing(name: tree.name, rasterW: rep.pixelsWide, rasterH: rep.pixelsHigh,
                                  samples: warm.samples, old: old, new: warm, cold: cold,
                                  opaqueProbe: opaqueProbe, clearProbe: clearProbe,
                                  disagreements: different,
                                  opaqueProbeAgrees: opaqueAgrees, clearProbeAgrees: clearAgrees)
    }

    /// 一颗像素按 alpha 分三类 —— 两通道要"同类"就按这个分类判，不按 RGB 判
    /// （`colorAt` 与原始字节在 RGB 上本来就不逐字相等，R571 读过一次）。
    private func alphaClass(_ p: (r: Int, g: Int, b: Int, a: Int)) -> Int {
        p.a == 0 ? 0 : (p.a == 255 ? 2 : 1)
    }

    // MARK: - ⓪½ R572 ③ 的三格判据（650：这条通道对产品真实视图树）

    /// 650 ①：两棵产品真实树上，新通道都必须在**旧通道选出的不透明探针**上读到 255。
    /// 这一句把本轮读到的那个致命同形分开：缺前置时新通道把整幅读成 a=0，
    /// 而第③段要判的「右页 alpha 归零」给的也是 a=0 ⇒ 单看"新通道看得见透明"会一路绿灯。
    func testTheAlphaLayerChannelDrawsProductTreesWhereTheOldChannelDrawsThem() throws {
        for which in ["主窗", "浮层"] {
            let pair = try captureProductTreePaired(which)
            CaptureReadings.emit("TRANSPARENCY_PRODUCT_ALPHA 树=" + pair.name + " 通道=成对 前置=走过 " + pair.line)
            CaptureReadings.emit(pair.driftLine)
            XCTAssertNotNil(pair.opaqueProbe,
                            "\(pair.name)：旧通道里找不到一颗不透明探针 ⇒ 这棵树什么都没画，"
                                + "这一格没有对象（先查树，别把这一格撤掉）")
            XCTAssertTrue(pair.opaqueProbeAgrees,
                          "\(pair.name)：旧通道画出来的不透明内容，新通道在**同一颗探针**上读到不是 255 ⇒ "
                              + "这条通道对这棵树少画了；它给的 a=0 是「没画」而不是「透明」，"
                              + "第③段不能拿它判 alpha 归零（读数 " + pair.line + "）")
            XCTAssertEqual(pair.disagreements, 0,
                           "\(pair.name)：同一棵树、同一块栅格，两条通道在 \(pair.disagreements) 颗探针上"
                               + "给的 alpha 类别不一样（" + pair.line + "）⇒ 其中一条在**挪动**内容而不是"
                               + "如实记录它；先分清是哪一条、错在哪一片，不许放容差把它糊过去")
        }
    }

    /// 650 ②：产品里今天**真有透明区**的那棵树（QuickPick 浮层）上，旧通道选出真透明探针，
    /// 新通道在同一颗探针上必须读到 0 ⇒ 这条通道对产品树确实保 alpha，两种栅格都判。
    /// 这是 R571 那一格（两半已知的合成夹具）判不到的东西：对象是产品自己的树。
    func testTheAlphaLayerChannelKeepsRealTransparencyOfTheProductOverlayTree() throws {
        let pair = try captureProductTreePaired("浮层")
        CaptureReadings.emit("TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=离屏-alpha图层 判=真透明探针 " + pair.line)
        XCTAssertNotNil(pair.clearProbe,
                        "浮层在旧通道下没有一颗真透明像素 ⇒ 对象消失了；"
                            + "那 94% 的透明区是产品今天真有的东西（`CAPTURE_PROBE quickpick transparent=`），"
                            + "要先解释它为什么没了")
        XCTAssertEqual(pair.clearProbeAgrees, true,
                       "浮层里旧通道判为真透明的那颗像素，新通道读到 a≠0 ⇒ 它把透明又涂成不透明了，"
                           + "§4 第三问对产品树的答案要按新读数重写（不许改登记表消红）")

        // 两种栅格各判一次"分得出"：R571 那句"两档一致"当时只在两半已知的合成夹具上证过，
        // 这一格把对象换成产品自己的树（夹具那一格不能替它签字）。
        let tree = try productTree("浮层")
        defer { tree.teardown() }
        func forceLayer(_ v: NSView) {
            v.wantsLayer = true
            v.subviews.forEach(forceLayer)
        }
        forceLayer(tree.view)
        tree.view.layoutSubtreeIfNeeded()
        let layer = try XCTUnwrap(tree.view.layer, "浮层没有图层 ⇒ 这条路没有对象")
        layer.frame = CGRect(x: 0, y: 0, width: tree.size.width, height: tree.size.height)
        // 前置：与成对那一格同一句话 —— 缺它就只能读到"没画"，而"没画"的 a=0 会冒充"归零"。
        let warmRep = try XCTUnwrap(tree.view.bitmapImageRepForCachingDisplay(in: tree.view.bounds),
                                    "浮层：旧通道拿不到位图 ⇒ 前置没有对象")
        tree.view.cacheDisplay(in: tree.view.bounds, to: warmRep)
        for scale in [2.0, 1.0] {
            let pw = max(1, Int((tree.size.width * scale).rounded()))
            let ph = max(1, Int((tree.size.height * scale).rounded()))
            let prof = try renderLayerIntoAlphaRaster(layer, pixelsWide: pw, pixelsHigh: ph,
                                                      size: tree.size).profile(step: 5)
            let canTell = prof.opaque > 0 && prof.clear > 0
            CaptureReadings.emit("TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=离屏-alpha图层 位图=" + "\(pw)x\(ph)"
                + " 栅格选择=" + String(format: "%.2fx", scale)
                + " 采样=\(prof.samples) 不透明=\(prof.opaque) 全透明=\(prof.clear)"
                + " 半透明=\(prof.partial) 有墨=\(prof.ink) 分得出=\(canTell ? 1 : 0)")
            XCTAssertGreaterThan(prof.ink, 0,
                                 "倍率=" + String(format: "%.2f", scale) + "x：一个墨都没有 ⇒ 这一臂是「没画」，"
                                     + "不许把它的 a=0 数进「分得出」")
            XCTAssertTrue(canTell,
                          "倍率=" + String(format: "%.2f", scale) + "x：产品浮层这棵树在这条通道下分不出真黑与透明"
                              + "（不透明=\(prof.opaque) 全透明=\(prof.clear)）⇒ §4 第三问对**产品树**"
                              + "又回到依栅格而定，第③段选签字口径时要按这条重写")
        }
    }

    /// 650 ③：主窗那棵树**今天没有可判的透明对象** —— 底衬把整幅铺成不透明。
    /// 反面证人两半都要：新通道画得出（有墨 == 采样）＋ 全透明样本为 0；
    /// 只给后半句就是拿"什么都没画"冒充结论（R490：两臂都 0 不许当通道缺席）。
    func testTheProductMainTreeStillGivesTheAlphaChannelNoTransparentObject() throws {
        let pair = try captureProductTreePaired("主窗")
        XCTAssertNil(pair.clearProbe,
                     "主窗内容里有真透明探针（旧通道读到 a=0 的位置）⇒ 底衬没铺满，或第③段已经开工了："
                         + "这一格从「无对象」变成「有对象」，650 与 646 要按新数重写，不许直接把断言反过来消红")
        XCTAssertEqual(pair.new.clear, 0,
                       "主窗在新通道下有 \(pair.new.clear) 颗全透明像素，而旧通道说那位置是画了内容的 ⇒ "
                           + "这条通道对主窗少画了（同 ① 那一格的红话）")
        XCTAssertGreaterThanOrEqual(pair.new.ink, pair.new.samples - 1,
                                    "主窗那棵树在新通道里画不出墨（有墨=\(pair.new.ink)/采样=\(pair.new.samples)）"
                                        + "⇒ 这一格没有内容")
        CaptureReadings.emit("TRANSPARENCY_PRODUCT_ALPHA 树=主窗 判=无透明对象 采样=\(pair.new.samples)"
            + " 全透明=\(pair.new.clear) 不透明=\(pair.new.opaque) 有墨=\(pair.new.ink)"
            + " 逐点异类=\(pair.disagreements)")
        CaptureReadings.emit("PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree"
            + " ⇒ 第③段有真透明区之后这一格必须重开")
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

    // MARK: - ② 离屏那一把：量出这条通道实际给的那一对数，并按倍率对登记表

    /// R569 的改账（上一轮把这格写成了通用契约，runner 第一跑就判反）：
    /// 本机 2x 读到 `透明半区=(r0,g0,b0,a255) 分得出=0`，而 runner 1x 读到
    /// `透明半区=(r0,g0,b0,a0) 分得出=1` ⇒ **"离屏通道能不能保留 alpha" 依捕获倍率而定**
    /// （R555/R568 那一族的第二次：同一个几何/像素量在 2x 与 1x 不是同一个对象）。
    /// 所以这一格不再断言"哪一种答案是真理"，而是断言**这台机器的答案必须等于登记过的那一个**：
    /// 任一台哪天翻了，这一格就红 ⇒ 逼着重新回答 §4 那一问，而不是让结论悄悄过期。
    /// 登记表里只有两个观测值（2x / 1x），别的倍率一律**不猜**。
    enum OffscreenAlphaVerdict: Equatable {
        case flattensToOpaqueBlack
        case preservesAlpha
    }

    static func registeredOffscreenVerdict(scale: Double) -> OffscreenAlphaVerdict? {
        if abs(scale - 2.0) < 0.01 { return .flattensToOpaqueBlack }   // 本机 Retina，R568/R569 两跑同值
        if abs(scale - 1.0) < 0.01 { return .preservesAlpha }          // CI runner 1x，R569 现读
        return nil
    }

    func testTheOffscreenAlphaAnswerIsRegisteredPerScale() {
        XCTAssertEqual(Self.registeredOffscreenVerdict(scale: 2.0), .flattensToOpaqueBlack,
                       "2x 那一档的登记被改 ⇒ 上一轮本机那两条逐字读数就没有人管了")
        XCTAssertEqual(Self.registeredOffscreenVerdict(scale: 1.0), .preservesAlpha,
                       "1x 那一档的登记被改 ⇒ runner 那朵红（分得出=1）就又变成没人认领的形状")
        XCTAssertNil(Self.registeredOffscreenVerdict(scale: 3.0),
                     "没观测过的倍率必须回 nil ⇒ 回一个值是猜的，而猜出来的契约下一轮一定红")
        XCTAssertNotEqual(Self.registeredOffscreenVerdict(scale: 2.0),
                          Self.registeredOffscreenVerdict(scale: 1.0),
                          "两档登记成同一个答案 ⇒ 这一格就不再读'依倍率而定'这件事了")
    }

    /// R571 ③ · 这条新通道在**同一台机器上**把 2x 与 1x 两种栅格各读一遍：
    /// 两档都必须 `分得出=1`，透明半区的 a 不是 255，而**黑半区的 a 必须是 255**。
    /// 三条断言各钉一种坏法：只判 `分得出` 会让"整幅都没画"这种缓冲蒙过去（诊断臂里 C/O 两档就是这个形状），
    /// 所以黑半区那一档是**正对照**，不是附加要求（R488 那一族：内容不足必须红）。
    func testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales() throws {
        let size = NSSize(width: 200, height: 120)
        for scale in [2.0, 1.0] {
            let shot = try captureTwoHalvesViaAlphaLayer(size: size, scale: scale)
            let canTell = distinguishes(shot.black, shot.clear)
            CaptureReadings.emit("TRANSPARENCY_CHANNEL 通道=离屏-alpha图层 位图=\(shot.pixelsWide)x\(shot.pixelsHigh)"
                + " 倍率=" + String(format: "%.2fx", scale)
                + " 黑半区=(r\(shot.black.r),g\(shot.black.g),b\(shot.black.b),a\(shot.black.a))"
                + " 透明半区=(r\(shot.clear.r),g\(shot.clear.g),b\(shot.clear.b),a\(shot.clear.a))"
                + " 分得出=\(canTell ? 1 : 0)")
            XCTAssertTrue(canTell,
                          "倍率=\(String(format: "%.2f", scale))x：这条通道把透明半区与真黑读成同一个东西 ⇒ "
                              + "第③段的「右页 alpha 归零」又没有能判的通道了")
            XCTAssertNotEqual(shot.clear.a, 255,
                              "倍率=\(String(format: "%.2f", scale))x：透明半区 a=255 ⇒ alpha 又被涂成不透明了")
            XCTAssertEqual(shot.black.a, 255,
                           "倍率=\(String(format: "%.2f", scale))x：连画了黑的那半都不是不透明"
                               + "（读到 a=\(shot.black.a)）⇒ 这条通道根本没画内容，"
                               + "它给的 a=0 不能算「透明被保住了」")
        }
    }

    func testOffscreenChannelMatchesTheRegisteredAlphaAnswerForItsScale() throws {
        let size = NSSize(width: 200, height: 120)
        let rep = try captureOffscreen(size: size)
        let black = try XCTUnwrap(pixel(rep, 50, 60), "左半区读不到像素 ⇒ 探针没落地")
        let clear = try XCTUnwrap(pixel(rep, 150, 60), "右半区读不到像素 ⇒ 探针没落地")
        let canTell = distinguishes(black, clear)
        let scale = Double(rep.pixelsWide) / size.width
        let measured: OffscreenAlphaVerdict = canTell ? .preservesAlpha : .flattensToOpaqueBlack
        let registered = Self.registeredOffscreenVerdict(scale: scale)
        let measuredText = canTell ? "保留 alpha" : "涂成不透明黑"
        let registeredText = registered == nil ? "未登记"
            : (registered == .preservesAlpha ? "保留 alpha" : "涂成不透明黑")
        CaptureReadings.emit("TRANSPARENCY_CHANNEL 通道=离屏 位图=\(rep.pixelsWide)x\(rep.pixelsHigh)"
            + " 倍率=\(String(format: "%.2f", scale))x hasAlpha=\(rep.hasAlpha ? 1 : 0)"
            + " 黑半区=(r\(black.r),g\(black.g),b\(black.b),a\(black.a))"
            + " 透明半区=(r\(clear.r),g\(clear.g),b\(clear.b),a\(clear.a))"
            + " 分得出=\(canTell ? 1 : 0) 实测=\(measuredText) 登记=\(registeredText)")
        XCTAssertEqual(black.a, 255,
                       "左半是不透明黑，alpha 却不是 255 ⇒ 这条通道的 alpha 语义与预期不同，下面那格会误判")
        guard let registered else {
            // 这台机器的倍率从没观测过 ⇒ 具名不判，并把两个真数打在上面那行里。
            // 不许拿另一台的答案替它签字（R555 那条：不同倍率不是同一对象）。
            CaptureReadings.emit("OFFSCREEN_ALPHA_NOT_RUN=unregistered-scale 倍率=\(String(format: "%.2f", scale))x"
                + " 分得出=\(canTell ? 1 : 0) ⇒ §4 第三条在这一档没有登记过答案，不判")
            return
        }
        XCTAssertEqual(measured, registered,
                       "倍率 \(String(format: "%.2f", scale))x 这台的离屏通道给了没登记过的答案："
                           + "实测「\(measuredText)」而登记的是「\(registeredText)」⇒ "
                           + "§4 第三条与 646 要按新读数重写（两台里有一台换了行为），不许改登记表来消红")
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
        // R569：真建一扇主窗就会把 `detailContentTopInset` 这个**进程内全局**写成那扇窗实测到的值，
        // 而判据卷里几十张 `detail-*`/`content-*` 帧是在同一个进程里拍的 ⇒ 必须还原（R525 红过一次、
        // R568 是第二次，见 `testEveryFileThatOpensARealMainWindowRestoresTheChromeMetric`）。
        let savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        let controller = MainWindowCollapseController(defaults: defaults)
        let delegate = AppDelegate(historyStore: store, collapseController: controller)
        defer {
            for window in NSApplication.shared.windows where WindowManager.isAppContentWindow(window) {
                window.delegate = nil
                window.orderOut(nil)
            }
            WindowManager.forgetMainWindowForTesting()
            WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedDetailContentTopInset)
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
        // R569：真建一扇主窗就会把 `detailContentTopInset` 这个**进程内全局**写成那扇窗实测到的值，
        // 而判据卷里几十张 `detail-*`/`content-*` 帧是在同一个进程里拍的 ⇒ 必须还原（R525 红过一次、
        // R568 是第二次，见 `testEveryFileThatOpensARealMainWindowRestoresTheChromeMetric`）。
        let savedDetailContentTopInset = WindowChromeMetrics.shared.detailContentTopInset
        let controller = MainWindowCollapseController(defaults: defaults)
        let delegate = AppDelegate(historyStore: store, collapseController: controller)
        NSApplication.shared.setActivationPolicy(.regular)
        defer {
            for window in NSApplication.shared.windows where WindowManager.isAppContentWindow(window) {
                window.delegate = nil
                window.orderOut(nil)
            }
            WindowManager.forgetMainWindowForTesting()
            WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(savedDetailContentTopInset)
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

    // MARK: - ⑦ R569 的制度位：谁开真主窗，谁必须还原那条全局

    /// `WindowChromeMetrics.shared.detailContentTopInset` 是**进程内全局**：真建一扇主窗，产品就会把它
    /// 写成那扇窗实测到的值（52pt 量级），而判据卷里几十张 `detail-*` / `content-*` 帧是在**同一个进程**
    /// 里拍的。R525 因为"某一格没还原它"红过一次 runner 的详情帧；R568 我自己那一格又做了同一件事
    /// （`41751994049` 那跑 STEP[15] 里四支 `detail-*` 旧判据后一批整体挪 54pt 并丢墨，
    /// 本机并行与串行两种排法都不复现）⇒ 这条扫描把"要记得还原"从记忆变成会红的门。
    ///
    /// 判的是**源码里的成对出现**：出现 `WindowManager.showMainWindow()` 的文件必须也出现
    /// `restoreDetailContentTopInsetForTesting`。豁免表里每条都要带理由，而理由里必须写退场。
    static func chromeMetricFileViolates(text: String) -> Bool {
        text.contains("WindowManager.showMainWindow()")
            && !text.contains("restoreDetailContentTopInsetForTesting")
    }

    /// 扫描本身抽成一个可对任何目录跑的函数 —— 这样它能被**合成目录**锤一次（真建一个违规文件、
    /// 一个合规文件），而不是只在真目录上"今天没红"。分级：合成目录 = 机制级证人，真目录 = 端到端。
    static func chromeMetricScan(dir: URL) throws -> (files: Int, openers: [String], violating: [String]) {
        let files = try FileManager.default.contentsOfDirectory(atPath: dir.path)
            .filter { $0.hasSuffix(".swift") }.sorted()
        var openers: [String] = [], violating: [String] = []
        for name in files {
            guard let text = try? String(contentsOf: dir.appendingPathComponent(name), encoding: .utf8) else {
                continue
            }
            if text.contains("WindowManager.showMainWindow()") {
                openers.append(name)
                if chromeMetricFileViolates(text: text) { violating.append(name) }
            }
        }
        return (files.count, openers, violating)
    }

    func testTheChromeMetricScanKnowsWhatAViolationLooksLike() throws {
        let violating = "final class X {\n  func t() { WindowManager.showMainWindow() }\n}\n"
        let compliant = "final class X {\n  func t() { WindowManager.showMainWindow() }\n"
            + "  func d() { WindowChromeMetrics.shared.restoreDetailContentTopInsetForTesting(1) }\n}\n"
        let unrelated = "final class X {\n  func t() { NSSize(width: 750, height: 560) }\n}\n"
        XCTAssertTrue(Self.chromeMetricFileViolates(text: violating),
                      "开真窗而不还原必须被判违规 ⇒ 判不出就是恒绿，这一格就没有对象")
        XCTAssertFalse(Self.chromeMetricFileViolates(text: compliant),
                       "还原过的文件被判成违规 ⇒ 这条扫描会把合规当坏，下一轮就会被当成噪声绕开")
        XCTAssertFalse(Self.chromeMetricFileViolates(text: unrelated),
                       "没开真窗的文件不该被管 ⇒ 管太宽会让豁免变成常态")

        // 机制级正对照：合成目录里放一个违规 + 一个合规 + 一个无关，扫描必须只点名那一支。
        let dir = FileManager.default.temporaryDirectory
            .appendingPathComponent("r569-chrome-scan-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        try violating.write(to: dir.appendingPathComponent("AOpenerWithoutRestore.swift"), atomically: true, encoding: .utf8)
        try compliant.write(to: dir.appendingPathComponent("BOpenenerWithRestore.swift"), atomically: true, encoding: .utf8)
        try unrelated.write(to: dir.appendingPathComponent("CUnrelated.swift"), atomically: true, encoding: .utf8)
        let synthetic = try Self.chromeMetricScan(dir: dir)
        CaptureReadings.emit("CHROME_METRIC_GUARD_SELFTEST 合成文件=\(synthetic.files) 开真窗=\(synthetic.openers.count)"
            + " 违规=[\(synthetic.violating.joined(separator: ","))]")
        XCTAssertEqual(3, synthetic.files, "合成目录里只扫到 \(synthetic.files) 个 .swift ⇒ 扫描没看到盘上的东西")
        XCTAssertEqual(2, synthetic.openers.count, "只认出 \(synthetic.openers.count) 个开真窗的文件 ⇒ 名单空转")
        XCTAssertEqual(["AOpenerWithoutRestore.swift"], synthetic.violating,
                       "合成违规没有被点名（或合规的被误点）⇒ 这条扫描不能上真目录")
    }

    func testEveryFileThatOpensARealMainWindowRestoresTheChromeMetric() throws {
        let dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        let scan = try Self.chromeMetricScan(dir: dir)
        // 唯一豁免：那一格判的正是"没装工厂时 `showMainWindow()` 不建窗"⇒ 没有可泄漏的量。
        // 退场：若那一格以后真建出窗，这条豁免必须删掉并补还原。
        let exempt: Set<String> = ["WindowManagerTests.swift"]
        CaptureReadings.emit("CHROME_METRIC_GUARD 文件=\(scan.files) 开真窗=\(scan.openers.count)"
            + " 违规=\(scan.violating.count) 名单=[\(scan.violating.joined(separator: ","))]"
            + " 豁免=[\(exempt.sorted().joined(separator: ","))] "
            + "未豁免违规=\(scan.violating.filter { !exempt.contains($0) }.count)")
        XCTAssertGreaterThanOrEqual(scan.openers.count, 4,
                                    "只认出 \(scan.openers.count) 个开真窗的文件 ⇒ 名单空转（R568 那一格就在里面），"
                                        + "这条扫描今天看不见任何东西")
        let unexempted = scan.violating.filter { !exempt.contains($0) }
        XCTAssertEqual([], unexempted,
                       "这些文件开了真主窗却没还原 `detailContentTopInset`：[\(unexempted.joined(separator: ","))] ⇒ "
                           + "同一进程里后面的 `detail-*`/`content-*` 帧会被那扇窗实测到的值挪位"
                           + "（R525 / R568 两次 runner 红的形状）")
    }

}
