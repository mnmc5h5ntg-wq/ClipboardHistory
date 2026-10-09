import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 视觉审计的一条**前提检查**：离屏帧能不能用来判断"图标有没有画出来"。
///
/// 起因（审计第二轮 1.9）：设置侧栏那列符号在 `settings-*-light.png` 里几乎看不见。
/// 当时记成"捕获伪影"，理由只是一句推断（"真机不可能长这样"）。本轮把它量成了数字：
///   · 产品 `SettingsView` 里未选中四行的图标列墨水 = **0.0000**，选中行 0.39（那是高亮底色，不是图标）；
///   · 把产品里那个图标的颜色从 `.primary` 换成固定的 `Color.black`，同一套管线立刻画出 0.175–0.402；
///   · 而在线下复刻的 List(.sidebar) 行里（带不带 `.plain` Button 都试了），`.primary` 与固定色**一样**能画出来。
/// 三条合起来：产品那列的不可见**只在完整视图里出现**，且只与"语义色"这一步有关 ——
/// 所以 `settings-*` 帧的未选中行图标列不能用来判产品缺陷，也不能为了讨好这一帧把语义色换成固定色。
/// 具体是哪一层（NavigationSplitView 侧栏样式？行内的模板色？）没有定论，这条探针负责在每次视觉审计时
/// 把数字重新量一遍：如果哪天 `INK 结论` 变成"五个图标都画得出来"，本段与 `AGENT_UI_AUDIT` 都要改写。
@MainActor
final class OffscreenSymbolInkProbeTests: XCTestCase {
    private struct Region { let x0: Int; let x1: Int }

    /// 一列图标 / 一列文字（2× 倍率下的像素坐标）。
    private static let iconColumn = Region(x0: 26, x1: 66)
    private static let textColumn = Region(x0: 78, x1: 170)
    private static let symbolNames = ["command", "gearshape", "hand.raised", "sparkles", "folder"]

    private func rasterize(_ rootView: AnyView, size: NSSize) throws -> (width: Int, height: Int, luminances: [Int]) {
        _ = NSApplication.shared
        let window = NSWindow(
            contentRect: NSRect(origin: .zero, size: size),
            styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.appearance = NSAppearance(named: .aqua)
        let host = NSHostingView(rootView: rootView.environment(\.colorScheme, .light))
        host.frame = NSRect(origin: .zero, size: size)
        window.contentView = host
        window.layoutIfNeeded()
        host.layoutSubtreeIfNeeded()
        window.makeFirstResponder(nil)
        guard let contentView = window.contentView,
              let rep = contentView.bitmapImageRepForCachingDisplay(in: contentView.bounds) else {
            throw XCTSkip("无法创建位图缓存")
        }
        window.appearance?.performAsCurrentDrawingAppearance {
            contentView.cacheDisplay(in: contentView.bounds, to: rep)
        }
        guard let data = rep.bitmapData else { throw XCTSkip("位图没有数据") }
        let width = rep.pixelsWide, height = rep.pixelsHigh
        let bytesPerRow = rep.bytesPerRow, bpp = rep.bitsPerPixel / 8
        // 位图带 alpha：透明处按 RGB 读会算成黑色，于是"整列都有墨"。
        // 先按 alpha 合成到窗口底色（亮色 aqua ≈ 246），与 `UICaptureHarness.flattenedPNG` 同一件事。
        let backdrop = 246
        var luminances = [Int](repeating: 0, count: width * height)
        for y in 0..<height {
            let rowBase = y * bytesPerRow
            for x in 0..<width {
                let offset = rowBase + x * bpp
                let r = Int(data[offset]), g = Int(data[offset + 1]), b = Int(data[offset + 2])
                var value = (r * 3 + g * 6 + b) / 10
                if bpp >= 4 {
                    let alpha = Int(data[offset + 3])
                    value = (value * alpha + backdrop * (255 - alpha)) / 255
                }
                luminances[y * width + x] = value
            }
        }
        return (width, height, luminances)
    }

    private func background(_ luminances: [Int]) -> Int {
        var counts: [Int: Int] = [:]
        for value in luminances { counts[value, default: 0] += 1 }
        return counts.max { $0.value < $1.value }?.key ?? 255
    }

    private func ink(_ frame: (width: Int, height: Int, luminances: [Int]),
                     x: Region, yRange: ClosedRange<Int>) -> Double {
        let bg = background(frame.luminances)
        var inked = 0, total = 0
        for y in yRange {
            for column in x.x0..<min(x.x1, frame.width) {
                total += 1
                if abs(frame.luminances[y * frame.width + column] - bg) > 32 { inked += 1 }
            }
        }
        return total == 0 ? 0 : Double(inked) / Double(total)
    }

    /// 用一定会画的文字列反推每一行的 y 段，避免写死坐标。
    private func rowBands(_ frame: (width: Int, height: Int, luminances: [Int])) -> [ClosedRange<Int>] {
        let bg = background(frame.luminances)
        var hasInk: [Bool] = []
        for y in 0..<frame.height {
            var rowInked = false
            for x in Self.textColumn.x0..<min(Self.textColumn.x1, frame.width) {
                if abs(frame.luminances[y * frame.width + x] - bg) > 32 { rowInked = true; break }
            }
            hasInk.append(rowInked)
        }
        var bands: [ClosedRange<Int>] = []
        var start: Int?
        for (y, inked) in hasInk.enumerated() {
            if inked, start == nil { start = y }
            if !inked, let s = start {
                if y - s >= 6 { bands.append(s...(y - 1)) }
                start = nil
            }
        }
        if let s = start { bands.append(s...(hasInk.count - 1)) }
        return bands
    }

    /// 与产品同构的一列 `Label`（List(.sidebar) 行内），颜色由参数决定。
    /// `wrappedInButton` 对应产品里那层 `Button { Label(...) }.buttonStyle(.plain)` ——
    /// 实测边界就在这层上（见 `testSemanticColorResolutionInListRowIcons` 打印的三档对比）。
    private func sidebarColumn(iconColor: AnyShapeStyle, wrappedInButton: Bool = false) -> AnyView {
        AnyView(
            List {
                ForEach(Self.symbolNames, id: \.self) { name in
                    let label = Label(name, systemImage: name)
                        .foregroundStyle(iconColor)
                        .symbolRenderingMode(.hierarchical)
                        .font(.system(size: 13))
                    if wrappedInButton {
                        Button(action: {}) { label }
                            .buttonStyle(.plain)
                    } else {
                        label
                    }
                }
            }
            .listStyle(.sidebar)
            .frame(width: 360, height: 300)
            .background(Color(nsColor: .windowBackgroundColor))
        )
    }

    /// 前提：管线画得出这些符号（固定色，跨系统版本都成立），而且是在**和产品一样的
    /// `.plain` Button 包装**里。画不出来的话，下面那条语义色测量就没有意义，所以这条留在常规套件里跑。
    func testPipelineRendersSymbolsWithExplicitColor() throws {
        let frame = try rasterize(sidebarColumn(iconColor: AnyShapeStyle(Color.black), wrappedInButton: true),
                                 size: NSSize(width: 360, height: 300))
        let bands = rowBands(frame)
        XCTAssertGreaterThanOrEqual(bands.count, Self.symbolNames.count,
                                    "文字列只数出 \(bands.count) 行，无法逐行核对图标")
        var perRow: [(String, Double)] = []
        for (index, name) in Self.symbolNames.enumerated() where index < bands.count {
            perRow.append((name, ink(frame, x: Self.iconColumn, yRange: bands[index])))
        }
        print("INK 固定色(List 行图标) \(perRow.map { "\($0.0)=\(String(format: "%.4f", $0.1))" }.joined(separator: " "))")
        for (name, fraction) in perRow {
            XCTAssertGreaterThan(fraction, 0.02, "固定色都画不出来：这条管线不能用来判图标可见性（\(name)）")
        }
    }

    /// 结论打印：量**产品自己的** `SettingsView`（语义色那条路径）里五个图标的墨水占比。
    /// 只在视觉审计时跑（与捕获套件同一个开关）：具体数字随系统版本与 SwiftUI 内部实现而变，
    /// 把它写成断言只会得到"CI 环境红"，而不是"产品有缺陷"。
    func testProductSettingsSidebarIconInk() throws {
        guard ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"] != nil else {
            throw XCTSkip("离屏语义色探针与视觉审计同开关：设 CLIPBOARD_HISTORY_UI_SHOTS 时才量")
        }
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let product = AnyView(SettingsView(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
            contextPreferences: ContextPreferenceSettings(),
            weightsStore: store.weightsStore,
            feedbackStore: store.feedbackStore,
            clearHistoryAction: {},
            initialCategory: .general
        ))
        let frame = try rasterize(product, size: NSSize(width: 720, height: 540))
        let bands = rowBands(frame)
        var lines: [String] = []
        var collapsed = 0
        for (index, category) in SettingsCategory.allCases.enumerated() where index < bands.count {
            let fraction = ink(frame, x: Self.iconColumn, yRange: bands[index])
            if fraction < 0.005 { collapsed += 1 }
            lines.append("\(category.icon)=\(String(format: "%.4f", fraction))")
        }
        print("INK 产品设置侧栏(语义色) \(lines.joined(separator: " "))")
        print(collapsed == 0
              ? "INK 结论 产品侧栏五个图标都画得出来 ⇒ 可以按帧判图标可见性"
              : "INK 结论 \(collapsed)/\(SettingsCategory.allCases.count) 行的图标列是 0.0000，"
                + "而同一套管线里固定色的同款符号能画到 0.18 以上 ⇒ "
                + "settings-* 帧的未选中行图标列不可信，不能据此判产品缺陷（也不能据此改产品颜色）")
    }
}
