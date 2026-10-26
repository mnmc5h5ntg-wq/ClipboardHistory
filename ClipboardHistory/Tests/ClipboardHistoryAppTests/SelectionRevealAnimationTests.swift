// R413：滚动到位动画的**管线级**证据。
//
// 两层分开记，别混：
// ① 产品运动：真 NSScrollView + 真 NSTableView + 产品 `SelectionRevealHostView`，
//    在动画途中逐时读 `documentVisibleRect.origin.y`。旧的瞬移在这一层是 0 个中间值，
//    新的长跳是 8/17 个中间值、末值落到目标。
// ② 像素通道：离屏 `cacheDisplay` 能不能拍到 AppKit bounds 动画的中段？用一张**静态文档**
//    （self-drawn 条带）证明能（起点/中段/落点三张帧、中段与两端都不同）。
//    NSTableView 的懒物化行在离屏滚动后不会被 `cacheDisplay` 画出来（产品表格的中段/落点帧
//    是空白）—— 那是**夹具通道边界**，不是产品缺陷，具名
//    `SCROLL_REVEAL_FRAME_PRODUCT_NOT_RUN=table-lazy-rows`。
// 帧里只有合成的"第 N 行"标签，不含任何剪贴板原文。

import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class SelectionRevealAnimationTests: XCTestCase {

    /// 产品运动：慢放到 0.6s 才读得到稳定的中段 origin；时长仍由
    /// `SelectionRevealMotion.plan` 给，`revealDurationOverride` 只是读取夹具。
    func testAnimatedRevealProducesIntermediateOffsets() throws {
        let world = try makeWorld()
        defer { world.window.orderOut(nil) }
        let start = world.scroll.documentVisibleRect.origin.y
        let target = try systemTarget(world, row: 80)
        XCTAssertGreaterThan(target, start + 200,
                             "夹具前提：第 80 行必须在视口下一次屏之外（否则不会走长跳动画）")

        world.host.revealDurationOverride = 0.6
        let startFrame = try grab(world.scroll)
        world.host.revealIfSelectionChanged(key: "row-80", row: 80)
        RunLoop.current.run(until: Date().addingTimeInterval(0.15))
        let mid = world.scroll.documentVisibleRect.origin.y
        let midFrame = try grab(world.scroll)
        RunLoop.current.run(until: Date().addingTimeInterval(0.6))
        let end = world.scroll.documentVisibleRect.origin.y
        let endFrame = try grab(world.scroll)

        // 产品表格的中段/落点像素帧在离屏 cacheDisplay 里是空白（懒物化行不重画）；
        // 这里仍留三张帧与读数，但**不拿它们判产品**，只记通道边界。
        let dir = shotsDirectory()
        let startToMid = differingPixels(startFrame, midFrame)
        let midToEnd = differingPixels(midFrame, endFrame)
        _ = try? save(startFrame, name: "scroll-reveal-product-start.png", in: dir)
        _ = try? save(midFrame, name: "scroll-reveal-product-mid.png", in: dir)
        _ = try? save(endFrame, name: "scroll-reveal-product-end.png", in: dir)
        CaptureReadings.emit("SCROLL_REVEAL_OFFSET 起点=\(String(format: "%.1f", start)) "
                             + "中段=\(String(format: "%.1f", mid)) "
                             + "落点=\(String(format: "%.1f", end)) "
                             + "目标=\(String(format: "%.1f", target)) "
                             + "中段是否严格在两端之间=\(mid > start + 1 && mid < target - 1)")
        CaptureReadings.emit("SCROLL_REVEAL_FRAME_PRODUCT_NOT_RUN=table-lazy-rows "
                             + "起→中变化=\(startToMid) 中→落变化=\(midToEnd) "
                             + "目录=\(dir.path) ⇒ 离屏 NSTableView 滚动后的新物化行不被 cacheDisplay 画出；"
                             + "产品运动由上面的逐时 origin 读数作证，像素通道另由静态文档正对照证明")

        XCTAssertGreaterThan(mid, start + 1,
                             "0.15s 时视口还在起点（中段=\(mid)）⇒ 动画没有开始，或宿主没找到表格")
        XCTAssertLessThan(mid, target - 1,
                          "0.15s 时已经到落点（中段=\(mid)、目标=\(target)）⇒ 这一档仍是瞬移")
        XCTAssertEqual(end, target, accuracy: 1.5,
                       "动画结束没落到目标（落点=\(end)、目标=\(target)）")
    }

    /// 产品时长（不覆盖）：原点必须经过中间值再落到目标。
    func testProductDurationRevealStillMovesOverTime() throws {
        let world = try makeWorld()
        defer { world.window.orderOut(nil) }
        let target = try systemTarget(world, row: 80)
        CaptureReadings.emit("SCROLL_REVEAL_PLAN reduce=\(MotionCatalog.motionShouldBeReduced) "
                             + "override=\(String(describing: world.host.revealReduceMotionOverride))")
        world.host.revealIfSelectionChanged(key: "row-80", row: 80)
        var samples: [CGFloat] = []
        let begun = Date()
        while Date().timeIntervalSince(begun) < 0.4 {
            RunLoop.current.run(until: Date().addingTimeInterval(0.02))
            samples.append(world.scroll.documentVisibleRect.origin.y)
        }
        let intermediates = samples.filter { $0 > 1 && $0 < target - 1 }
        CaptureReadings.emit("SCROLL_REVEAL_TIME 采样=\(samples.count) "
                             + "中间值=\(intermediates.count) "
                             + "首=\(String(format: "%.1f", samples.first ?? -1)) "
                             + "末=\(String(format: "%.1f", samples.last ?? -1)) "
                             + "目标=\(String(format: "%.1f", target)) "
                             + "时长=\(String(format: "%.2f", MotionCatalog.duration(for: .slider)))")
        XCTAssertFalse(intermediates.isEmpty,
                       "产品时长下没有任何中间 origin（\(samples)）⇒ 这是瞬移，不是过程")
        XCTAssertEqual(samples.last ?? 0, target, accuracy: 1.5,
                       "产品时长结束后没有落到目标（末=\(samples.last ?? -1)、目标=\(target)）")
    }

    /// 近步（距离 < 一屏）走 instant，但落点必须是**同一个纯目标**，不能退回系统
    /// `scrollRowToVisible` 那条会多露一截的老路（R413 实测差 8pt）。
    func testNearRevealUsesTheSameInstantTarget() throws {
        let world = try makeWorld()
        defer { world.window.orderOut(nil) }
        let target = try systemTarget(world, row: 11)
        XCTAssertLessThan(target, world.scroll.documentVisibleRect.height,
                          "夹具前提：第 11 行的目标位移必须小于一屏（否则会走动画）")
        world.host.revealIfSelectionChanged(key: "row-11", row: 11)
        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
        let origin = world.scroll.documentVisibleRect.origin.y
        CaptureReadings.emit("SCROLL_REVEAL_INSTANT 目标=\(String(format: "%.1f", target)) "
                             + "落点=\(String(format: "%.1f", origin))")
        XCTAssertEqual(origin, target, accuracy: 1.0,
                       "近步落点 \(origin) 与纯目标 \(target) 不一致 ⇒ instant 分支又走回了另一条路")
    }

    /// 像素通道的正对照：**静态文档**（self-drawn 条带）走同一套 AppKit bounds 动画，
    /// 起点/中段/落点三帧必须两两不同；中段 origin 必须在两端之间。
    /// 它证明的是"cacheDisplay 能拍 AppKit bounds 动画的中段"，不是产品表格的像素。
    func testStaticDocumentScrollAnimationIsCapturable() throws {
        _ = NSApplication.shared
        let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: 240, height: 200))
        scroll.drawsBackground = true
        scroll.backgroundColor = .white
        let doc = NSView(frame: NSRect(x: 0, y: 0, width: 240, height: 2000))
        for index in 0..<50 {
            let band = RevealStripeView(frame: NSRect(x: 0, y: CGFloat(index) * 40,
                                                      width: 240, height: 20))
            band.index = index
            doc.addSubview(band)
        }
        scroll.documentView = doc
        let window = NSWindow(contentRect: scroll.frame, styleMask: [.titled],
                              backing: .buffered, defer: false)
        window.contentView = scroll
        window.setFrameTopLeftPoint(NSPoint(x: -4000, y: -4000))
        window.orderFront(nil)
        scroll.layoutSubtreeIfNeeded()
        doc.layoutSubtreeIfNeeded()
        scroll.contentView.scroll(to: .zero)
        scroll.reflectScrolledClipView(scroll.contentView)
        RunLoop.current.run(until: Date().addingTimeInterval(0.2))
        defer { window.orderOut(nil) }

        let start = scroll.documentVisibleRect.origin.y
        let startFrame = try grab(scroll)
        let clip = scroll.contentView
        let target = NSPoint(x: 0, y: 600)
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.6
            context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            clip.animator().setBoundsOrigin(target)
        }
        RunLoop.current.run(until: Date().addingTimeInterval(0.15))
        let mid = scroll.documentVisibleRect.origin.y
        let midFrame = try grab(scroll)
        RunLoop.current.run(until: Date().addingTimeInterval(0.6))
        let end = scroll.documentVisibleRect.origin.y
        let endFrame = try grab(scroll)

        let startToMid = differingPixels(startFrame, midFrame)
        let midToEnd = differingPixels(midFrame, endFrame)
        let dir = shotsDirectory()
        _ = try? save(startFrame, name: "scroll-reveal-static-start.png", in: dir)
        _ = try? save(midFrame, name: "scroll-reveal-static-mid.png", in: dir)
        _ = try? save(endFrame, name: "scroll-reveal-static-end.png", in: dir)
        CaptureReadings.emit("SCROLL_REVEAL_CHANNEL 起点=\(String(format: "%.1f", start)) "
                             + "中段=\(String(format: "%.1f", mid)) "
                             + "落点=\(String(format: "%.1f", end)) "
                             + "起→中变化=\(startToMid) 中→落变化=\(midToEnd) "
                             + "目录=\(dir.path)")
        XCTAssertGreaterThan(mid, start + 1, "静态文档的中段没有离开起点 ⇒ 通道没在演")
        XCTAssertLessThan(mid, target.y - 1, "静态文档的中段已经到落点 ⇒ 通道只看到瞬移")
        XCTAssertGreaterThan(startToMid, 500, "静态文档起点→中段只差 \(startToMid) 像素")
        XCTAssertGreaterThan(midToEnd, 500, "静态文档中段→落点只差 \(midToEnd) 像素")
    }

    private struct World {
        let window: NSWindow
        let scroll: NSScrollView
        let table: NSTableView
        let host: SelectionRevealHostView
    }

    private func makeWorld() throws -> World {
        _ = NSApplication.shared
        let table = NSTableView(frame: NSRect(x: 0, y: 0, width: 240, height: 2000))
        table.headerView = nil
        table.rowHeight = 20
        table.intercellSpacing = .zero
        table.gridStyleMask = []
        table.backgroundColor = .white
        let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("row"))
        column.width = 240
        table.addTableColumn(column)
        let data = RevealDataSource(rows: 100)
        table.dataSource = data
        table.delegate = data
        table.reloadData()

        let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: 240, height: 200))
        scroll.hasVerticalScroller = true
        scroll.drawsBackground = true
        scroll.backgroundColor = .white
        scroll.documentView = table
        let host = SelectionRevealHostView(frame: NSRect(x: 0, y: 0, width: 1, height: 1))
        // 单测要验「动画路径」；产品的默认仍读系统减弱动态开关，见 revealReduceMotionOverride 的注释。
        host.revealReduceMotionOverride = false
        table.addSubview(host)

        let window = NSWindow(contentRect: scroll.frame, styleMask: [.titled],
                              backing: .buffered, defer: false)
        window.contentView = scroll
        window.setFrameTopLeftPoint(NSPoint(x: -4000, y: -4000))
        window.orderFront(nil)
        scroll.layoutSubtreeIfNeeded()
        table.layoutSubtreeIfNeeded()
        scroll.contentView.scroll(to: .zero)
        scroll.reflectScrolledClipView(scroll.contentView)
        RunLoop.current.run(until: Date().addingTimeInterval(0.2))
        guard table.numberOfRows == 100 else {
            window.orderOut(nil)
            XCTFail("表格只有 \(table.numberOfRows) 行 ⇒ 夹具没建起来，这条判据没有对象")
            throw NSError(domain: "SelectionRevealAnimationTests", code: 1)
        }
        return World(window: window, scroll: scroll, table: table, host: host)
    }

    /// 系统的「最小滚动」目标：临时滚一次、读 clip 原点、再回到起点。
    /// 产品现在先调 `scrollRowToVisible`（物化/选中 + 量目标），再回起点演到同一个目标；
    /// 这条 helper 让判据与产品量的是**同一个系统目标**，不另造一套几何。
    private func systemTarget(_ world: World, row: Int) throws -> CGFloat {
        let start = world.scroll.documentVisibleRect.origin.y
        world.table.scrollRowToVisible(row)
        world.table.layoutSubtreeIfNeeded()
        world.table.scrollRowToVisible(row)
        world.scroll.layoutSubtreeIfNeeded()
        let target = world.scroll.documentVisibleRect.origin.y
        world.scroll.contentView.scroll(to: NSPoint(x: 0, y: start))
        world.scroll.reflectScrolledClipView(world.scroll.contentView)
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
        return target
    }

    private func grab(_ view: NSView) throws -> NSBitmapImageRep {
        let rep = try XCTUnwrap(view.bitmapImageRepForCachingDisplay(in: view.bounds),
                                "cacheDisplay 没给位图 ⇒ 这一格拍不到")
        view.cacheDisplay(in: view.bounds, to: rep)
        return rep
    }

    private func differingPixels(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Int {
        let w = min(a.pixelsWide, b.pixelsWide)
        let h = min(a.pixelsHigh, b.pixelsHigh)
        var changed = 0
        for y in 0..<h {
            for x in 0..<w {
                guard let ca = a.colorAt(x: x, y: y), let cb = b.colorAt(x: x, y: y) else { continue }
                if ca.redComponent != cb.redComponent
                    || ca.greenComponent != cb.greenComponent
                    || ca.blueComponent != cb.blueComponent {
                    changed += 1
                }
            }
        }
        return changed
    }

    private func shotsDirectory() -> URL {
        let dir = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"]
            .map { URL(fileURLWithPath: $0, isDirectory: true) }
            ?? FileManager.default.temporaryDirectory
                .appendingPathComponent("scroll-reveal-\(UUID().uuidString)", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    private func save(_ rep: NSBitmapImageRep, name: String, in dir: URL) throws -> URL {
        let data = try XCTUnwrap(rep.representation(using: .png, properties: [:]),
                                 "位图转 PNG 失败 ⇒ 这一格没有可看的帧")
        let url = dir.appendingPathComponent(name)
        try data.write(to: url)
        return url
    }
}

private final class RevealDataSource: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    let rows: Int

    init(rows: Int) {
        self.rows = rows
    }

    func numberOfRows(in tableView: NSTableView) -> Int { rows }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let identifier = NSUserInterfaceItemIdentifier("cell")
        let cell = tableView.makeView(withIdentifier: identifier, owner: nil) as? RevealCellView
            ?? {
                let created = RevealCellView()
                created.identifier = identifier
                return created
            }()
        cell.row = row
        return cell
    }
}

/// 自绘单元格：背景与文字都在 `draw` 里，不用 layer 背景。
private final class RevealCellView: NSView {
    var row: Int = 0

    override func draw(_ dirtyRect: NSRect) {
        let even = row % 2 == 0
        let background = even
            ? NSColor(calibratedWhite: 0.98, alpha: 1)
            : NSColor(calibratedRed: 0.88, green: 0.93, blue: 1.0, alpha: 1)
        background.setFill()
        bounds.fill()
        let text = "第 \(row) 行 · scroll reveal"
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.monospacedDigitSystemFont(ofSize: 11, weight: .regular),
            .foregroundColor: NSColor.labelColor
        ]
        text.draw(at: NSPoint(x: 8, y: 2), withAttributes: attributes)
    }
}

/// 静态文档的条带：像素通道正对照，不是产品表格。
private final class RevealStripeView: NSView {
    var index: Int = 0

    override func draw(_ dirtyRect: NSRect) {
        let even = index % 2 == 0
        let background = even
            ? NSColor(calibratedWhite: 0.98, alpha: 1)
            : NSColor(calibratedRed: 0.88, green: 0.93, blue: 1.0, alpha: 1)
        background.setFill()
        bounds.fill()
        let text = "第 \(index) 行 · static channel"
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.monospacedDigitSystemFont(ofSize: 11, weight: .regular),
            .foregroundColor: NSColor.labelColor
        ]
        text.draw(at: NSPoint(x: 8, y: 2), withAttributes: attributes)
    }
}
