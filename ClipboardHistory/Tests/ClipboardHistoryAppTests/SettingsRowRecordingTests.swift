// R412：设置快捷键行的「正在录制」行级状态。
//
// 不覆盖管线：这个文件判的是行的强调值、接线（源码）与像素尺本身；
// 整页录制帧的管线级判据在 `UICaptureHarness.testCaptureKeyViews` 的
// `RECORDER_ROW_EDGE` 那一段（从产品入口 `performClick` 点进录制态，再比两帧）。
// 这里刻意不渲染整页：组件级渲染替不了「三行里只有这一行被点亮」这个组合问题（D-206）。

import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class SettingsRowRecordingTests: XCTestCase {

    /// 强调值必须是模型值：静置恒 0（静置帧基线不动），录制时非 0 且与录音器同宽。
    func testRecordingRowEmphasisTruthTable() {
        XCTAssertEqual(SettingsRowEmphasis.recordingStrokeOpacity(isRecording: false), 0,
                       "静置还画描边 ⇒ 每一张快捷键静置帧都会被改写")
        XCTAssertGreaterThanOrEqual(SettingsRowEmphasis.recordingStrokeOpacity(isRecording: true), 0.5,
                                    "录制时描边淡到读不出 ⇒ 行级状态等于没做")
        XCTAssertEqual(SettingsRowEmphasis.recordingStrokeWidth(isRecording: false), 0,
                       "静置宽度不是 0 ⇒ 即使透明度为 0，边界上仍可能留下抗锯齿像素")
        XCTAssertEqual(SettingsRowEmphasis.recordingStrokeWidth(isRecording: true),
                       VisualStroke.highlight,
                       "行级描边与录音器自己那圈不同宽 ⇒ 同一句话的两个范围对不上")
    }

    /// 接线守卫：按钮把状态报出来，行把它接到描边上，动画驱动也必须在。
    ///
    /// 这三件事缺一件，像素上都会长成「录制帧没有行级状态」—— 但成因不同：
    /// ① 不报告 ⇒ 行永远不知道；② 不接 ⇒ 知道也不画；③ 不驱动 ⇒ 画了但瞬切（声明等于零）。
    func testRecordingRowIsWiredFromButtonToOutline() throws {
        let recorder = codeOnly(try productSourceText(named: "Views/HotKeyRecorderView.swift"))
        XCTAssertTrue(recorder.contains("var onRecordingChange: (Bool) -> Void = { _ in }"),
                      "录制器没有对外的状态出口 ⇒ 设置行拿不到「正在听」")
        XCTAssertTrue(recorder.contains("onRecordingChange(recording)"),
                      "录制器自己翻了状态却没有调用出口 ⇒ 行级描边永远不亮")

        let settings = codeOnly(try productSourceText(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("onRecordingChange: { isRecording = $0 }"),
                      "设置行没接录制回调 ⇒ 这一行永远不知道自己正在吃键")
        XCTAssertTrue(settings.contains("SettingsRowEmphasis.recordingStrokeOpacity(isRecording: isRecording)"),
                      "行级描边没有走 `SettingsRowEmphasis` ⇒ 上面的真值表测的是一个没人用的替身")
        XCTAssertTrue(settings.contains("SettingsRowEmphasis.recordingStrokeWidth(isRecording: isRecording)"),
                      "行级描边的宽度没有走 `SettingsRowEmphasis`")
        XCTAssertTrue(settings.contains(".animation(MotionCatalog.animation(for: .emphasis), value: isRecording)"),
                      "行级描边没有驱动 ⇒ 它只会瞬现瞬灭，声明等于零（MotionDriverTests 那一族）")
    }

    /// 像素尺的**跨倍率正对照**：同一张 100×40 的合成图，1×/2× 各一组。
    /// 录制臂画一圈 1pt 强调色边框，静置臂不画；两倍率都必须读到"有变化且有强调色"。
    /// 两臂都读 0 或只在一个倍率读到，说明这把尺量的是像素密度而不是状态（R107 那一族）。
    func testRecorderRowEdgeRulerSeesBothScales() throws {
        let band = CGRect(x: 0, y: 0, width: 100, height: 40)
        for scale in [1, 2] {
            let idle = try syntheticFrame(scale: scale, accent: false)
            let recording = try syntheticFrame(scale: scale, accent: true)
            let read = RecorderRowEdgeRuler.read(recording: recording, idle: idle,
                                                 bandPoints: band, frameWidthPoints: 100)
            CaptureReadings.emit("RECORDER_ROW_EDGE_SCALE \(scale)x 变化=\(read.changed) "
                                 + "强调=\(read.accentChanged) 总数=\(read.total) "
                                 + "均差=\(String(format: "%.2f", read.meanDelta))")
            XCTAssertGreaterThan(read.changed, 0, "\(scale)x：合成边框没有被读到 ⇒ 这把尺在这档是瞎的")
            XCTAssertGreaterThan(read.accentChanged, 0,
                                 "\(scale)x：只读到变化、读不到强调色 ⇒ 分不出「行在录」与「普通重绘」")
            let same = RecorderRowEdgeRuler.read(recording: idle, idle: idle,
                                                 bandPoints: band, frameWidthPoints: 100)
            XCTAssertEqual(same.changed, 0, "\(scale)x：两张相同的图也读到变化 ⇒ 地板失效")
            XCTAssertEqual(same.accentChanged, 0, "\(scale)x：两张相同的图也读到强调色 ⇒ 地板失效")
        }
    }

    /// 从产品入口点进录制态：真的 `HotKeySettingsRow` + 真的 `HotKeyRecorderButton`。
    /// 只拍**录音器左边那块行带**（标题 + 说明 + 行描边），把「行级状态」与「录音器自己的环」分开。
    func testRecordingOutlineAppearsOnTheRealRow() throws {
        _ = NSApplication.shared
        let action = HotKeyAction.quickPick
        let settings = HotKeySettings(action: action, shortcut: action.defaultShortcut)
        let host = NSHostingView(rootView: HotKeySettingsRow(
            settings: settings,
            shortcut: .constant(action.defaultShortcut))
            .padding(16)
            .frame(width: 620, height: 150, alignment: .topLeading)
            .background(Color(nsColor: .windowBackgroundColor)))
        host.frame = NSRect(x: 0, y: 0, width: 620, height: 150)
        let window = NSWindow(contentRect: host.frame, styleMask: [.titled],
                              backing: .buffered, defer: false)
        window.contentView?.addSubview(host)
        window.setFrameTopLeftPoint(NSPoint(x: -4000, y: -4000))
        window.orderFront(nil)
        host.layoutSubtreeIfNeeded()
        RunLoop.current.run(until: Date().addingTimeInterval(0.3))
        defer { window.orderOut(nil) }

        guard let button = Self.firstRecorder(in: host) else {
            XCTFail("视图树里找不到 `HotKeyRecorderButton` ⇒ 这一条没有对象（不许读成通过）")
            return
        }
        let idle = try Self.grab(host)
        let recorderFrame = host.convert(button.bounds, from: button)
        let band = CGRect(x: 6, y: 6,
                          width: max(1, recorderFrame.minX - 12),
                          height: max(1, host.bounds.height - 12))

        button.performClick(nil)
        XCTAssertEqual(button.title, "请输入快捷键", "点下去必须真的进入录制态（否则比的是两个静置态）")
        RunLoop.current.run(until: Date().addingTimeInterval(0.5))
        host.layoutSubtreeIfNeeded()
        let recording = try Self.grab(host)

        let idleRead = RecorderRowEdgeRuler.read(recording: idle, idle: idle,
                                                 bandPoints: band, frameWidthPoints: host.bounds.width)
        let recordingRead = RecorderRowEdgeRuler.read(recording: recording, idle: idle,
                                                      bandPoints: band, frameWidthPoints: host.bounds.width)
        let sizeText = "\(Int(band.width))x\(Int(band.height))pt"
        let deltaText = String(format: "%.2f", recordingRead.meanDelta)
        CaptureReadings.emit("RECORDER_ROW_EDGE 带=\(sizeText) "
                             + "录制变化=\(recordingRead.changed) 录制强调=\(recordingRead.accentChanged) "
                             + "静置强调=\(idleRead.accentChanged) 总数=\(recordingRead.total) "
                             + "均差=\(deltaText)")
        XCTAssertEqual(idleRead.accentChanged, 0,
                       "静置行带里读到 \(idleRead.accentChanged) 颗强调色 ⇒ 描边在没录制时也在画")
        XCTAssertGreaterThanOrEqual(recordingRead.accentChanged, 200,
                                    "录制行带里只有 \(recordingRead.accentChanged) 颗强调色（要 ≥200）"
                                        + " ⇒ 行级描边没画上，或按钮→回调→行 这条边断了")
        XCTAssertGreaterThan(recordingRead.changed, 200,
                             "录制与静置在行带里只差 \(recordingRead.changed) 个像素 ⇒ 行级状态没有可读的形状")
    }

    private static func firstRecorder(in view: NSView) -> HotKeyRecorderButton? {
        if let match = view as? HotKeyRecorderButton { return match }
        for sub in view.subviews {
            if let found = firstRecorder(in: sub) { return found }
        }
        return nil
    }

    private static func grab(_ view: NSView) throws -> NSBitmapImageRep {
        let size = view.bounds.size
        let rep = try XCTUnwrap(NSBitmapImageRep(bitmapDataPlanes: nil,
                                                 pixelsWide: Int(size.width) * 2,
                                                 pixelsHigh: Int(size.height) * 2,
                                                 bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                                 isPlanar: false, colorSpaceName: .deviceRGB,
                                                 bytesPerRow: 0, bitsPerPixel: 0))
        rep.size = size
        view.cacheDisplay(in: view.bounds, to: rep)
        return rep
    }

    /// 邻行隔离的尺必须分得开「整页底色差」与「真的强调描边泄漏」：
    /// runner 1x 的 idle/recording 帧邻行 changed=100%、accent=0（窗口焦点导致的底色），
    /// 而真的泄漏会带强调色。这条是 R412 那格 20740/0 的负对照。
    func testNeighborIsolationIgnoresTintButSeesAccentLeak() throws {
        let band = CGRect(x: 0, y: 0, width: 100, height: 40)
        let idle = try syntheticFrame(scale: 2, accent: false)
        let tint = try syntheticFrame(scale: 2, accent: false, tint: 0.82)
        let tintRead = RecorderRowEdgeRuler.read(recording: tint, idle: idle,
                                                 bandPoints: band, frameWidthPoints: 100)
        XCTAssertGreaterThan(tintRead.changed, 0,
                             "灰底色差没有被 changed 读到 ⇒ 这条负对照自己没对象")
        XCTAssertEqual(tintRead.accentChanged, 0,
                       "灰底色差被 accent 读成 \(tintRead.accentChanged) 颗 ⇒ 隔离判据会把焦点底色当泄漏")
        let accent = try syntheticFrame(scale: 2, accent: true)
        let accentRead = RecorderRowEdgeRuler.read(recording: accent, idle: idle,
                                                   bandPoints: band, frameWidthPoints: 100)
        XCTAssertGreaterThan(accentRead.accentChanged, 0,
                             "真的强调描边泄漏没有被 accent 读到 ⇒ 上面那条负对照是恒真")
    }

    /// 合成图的 y 坐标按 `NSBitmapImageRep.colorAt` 的读取方向直接写，
    /// 不依赖绘制上下文的翻转约定 —— 这条尺只负责读，不负责替渲染器定义坐标。
    private func syntheticFrame(scale: Int, accent: Bool, tint: CGFloat = 0.8) throws -> NSBitmapImageRep {
        let width = 100 * scale
        let height = 40 * scale
        let rep = try XCTUnwrap(NSBitmapImageRep(bitmapDataPlanes: nil,
                                                 pixelsWide: width, pixelsHigh: height,
                                                 bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                                 isPlanar: false, colorSpaceName: .deviceRGB,
                                                 bytesPerRow: 0, bitsPerPixel: 0))
        let background = NSColor(calibratedRed: tint, green: tint, blue: tint, alpha: 1)
        let blue = NSColor(calibratedRed: 0, green: 0.48, blue: 1, alpha: 1)
        let border = max(1, scale)
        for y in 0..<height {
            for x in 0..<width {
                let onBorder = x < border || x >= width - border || y < border || y >= height - border
                rep.setColor(accent && onBorder ? blue : background, atX: x, y: y)
            }
        }
        return rep
    }

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
        throw NSError(domain: "SettingsRowRecordingTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}

/// 整页录制帧的取样尺（R412）。抽成独立类型是为了让**跨倍率正对照**与
/// 真实帧判据走同一段读取代码 —— 两条各写一份，正对照证明的就不是判据那把尺。
enum RecorderRowEdgeRuler {
    struct Reading: Equatable {
        let changed: Int
        let accentChanged: Int
        let total: Int
        let meanDelta: Double
    }

    static func read(recording: NSBitmapImageRep, idle: NSBitmapImageRep,
                     bandPoints: CGRect, frameWidthPoints: CGFloat) -> Reading {
        let scale = Double(recording.pixelsWide) / Double(frameWidthPoints)
        let x0 = max(0, Int((bandPoints.minX * scale).rounded(.down)))
        let x1 = min(recording.pixelsWide, Int((bandPoints.maxX * scale).rounded(.up)))
        let y0 = max(0, Int((bandPoints.minY * scale).rounded(.down)))
        let y1 = min(recording.pixelsHigh, Int((bandPoints.maxY * scale).rounded(.up)))
        var changed = 0
        var accentChanged = 0
        var total = 0
        var deltaSum = 0.0
        guard x1 > x0, y1 > y0 else { return Reading(changed: 0, accentChanged: 0, total: 0, meanDelta: 0) }
        for y in y0..<y1 {
            for x in x0..<x1 {
                guard let a = recording.colorAt(x: x, y: y),
                      let b = idle.colorAt(x: x, y: y) else { continue }
                total += 1
                let dr = abs(a.redComponent - b.redComponent)
                let dg = abs(a.greenComponent - b.greenComponent)
                let db = abs(a.blueComponent - b.blueComponent)
                let delta = (dr + dg + db) / 3 * 255
                deltaSum += delta
                if dr + dg + db > 0.003 {
                    changed += 1
                    if isAccent(a) { accentChanged += 1 }
                }
            }
        }
        return Reading(changed: changed, accentChanged: accentChanged, total: total,
                       meanDelta: total > 0 ? deltaSum / Double(total) : 0)
    }

    static func isAccent(_ color: NSColor) -> Bool {
        let r = color.redComponent, g = color.greenComponent, b = color.blueComponent
        return b > r + 0.08 && b > g + 0.04 && b > 0.31
    }
}
