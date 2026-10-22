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
///
/// **R28 把"0.0000"这个数读出了方向**（第 22 项重新判一遍时量到的，不是推断）：
/// 亮色帧里 `command` / `hand.raised` / `folder` 那三列的像素是 **(255,255,255)**，背景 (248,248,248)
/// —— 偏离只有 7，所以 `ink()` 报 0；暗色帧里换 `wand.and.stars` / `chart.bar` 两列变成 **(0,0,0)** 对 (24,24,24)。
/// 每一枚符号的 RGB 在两张帧里**恒定、不随外观变**，而被选中的那枚（走 accent color）两帧都对。
/// 所以这不是"没画"，是**画成了反的**：语义色在离屏管线上被解析到了另一套外观。
/// 这条探针现在把两者分开数（`signedInk`）：反相放行，整列一个像素都没动过才红。
@MainActor
final class OffscreenSymbolInkProbeTests: XCTestCase {
    private struct Region { let x0: Int; let x1: Int }

    /// 一列图标 / 一列文字（2× 倍率下的像素坐标）。
    private static let iconColumn = Region(x0: 26, x1: 66)
    private static let textColumn = Region(x0: 78, x1: 170)
    /// 探针要量的符号 = **产品侧栏现在真的在用那些**。
    ///
    /// 原来这里是一份手抄的字面量数组，于是它漂了两次都没人喊：
    /// `sparkles` 早就不是推荐分类的图标（现在是 `wand.and.stars`），
    /// 而新增的 `chart.bar` 根本不在名单里 ——
    /// 一条"每次视觉审计都重新量一遍"的探针，量的是五个已经不存在的图标（BACKLOG 16 / U-31）。
    /// 从枚举取之后它不可能再漂；下面 `testProbeCoversEveryCategory` 钉住这条推导关系。
    ///
    /// 计算属性而不是 `static let`：`static let = <带调用的初始化器>` 这个形状
    /// 在 CI 的 Swift 6.1.2 上崩过一次（D-069），别在测试里再摆一份。
    private static var symbolNames: [String] { SettingsCategory.allCases.map(\.icon) }

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

    /// **带符号**的墨：分别数"比背景亮"和"比背景暗"的像素。
    ///
    /// 为什么 `ink()` 不够用（R28）：它只看"偏离背景多少"，于是
    /// **"画成了白色的图标"和"什么都没画"在它眼里是同一个数 0.0000**。
    /// 实测亮色帧里未选中那几枚符号的整列像素是 (255,255,255)，背景是 (248,248,248)
    /// ⇒ 偏离 7 ⇒ `ink = 0`；而暗色帧里另外两枚是 (0,0,0) 对 (24,24,24) ⇒ 同样 0。
    /// 两种故障的修法相反：前者是离屏管线的语义色解析反了（不能动产品），
    /// 后者是符号名写错或这枚在目标系统上不存在（必须动产品）。
    private func signedInk(_ frame: (width: Int, height: Int, luminances: [Int]),
                           x: Region, yRange: ClosedRange<Int>,
                           threshold: Int) -> (brighter: Int, darker: Int) {
        let bg = background(frame.luminances)
        var brighter = 0, darker = 0
        for y in yRange {
            for column in x.x0..<min(x.x1, frame.width) {
                let delta = frame.luminances[y * frame.width + column] - bg
                if delta > threshold { brighter += 1 }
                if delta < -threshold { darker += 1 }
            }
        }
        return (brighter, darker)
    }

    /// 与产品同构的一列 `Label`（List(.sidebar) 行内），颜色由参数决定。
    /// `wrappedInButton` 对应产品里那层 `Button { Label(...) }.buttonStyle(.plain)` ——
    /// 实测边界就在这层上（见 `testSemanticColorResolutionInListRowIcons` 打印的三档对比）。
    private func sidebarColumn(iconColor: AnyShapeStyle,
                               wrappedInButton: Bool = false,
                               names: [String]? = nil) -> AnyView {
        let symbols = names ?? Self.symbolNames
        return AnyView(
            List {
                ForEach(symbols, id: \.self) { name in
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
    ///
    /// 判据取"整条图标列"的墨水，不数"有几行"：CI 的 macos-15 runner 上这段列表只数出 4 行
    /// （本机 26 是 5 行）—— 行高与行距是实现细节，把它写进断言就是第五次犯"本机数字进断言"。
    func testPipelineRendersSymbolsWithExplicitColor() throws {
        let frame = try rasterize(sidebarColumn(iconColor: AnyShapeStyle(Color.black), wrappedInButton: true),
                                 size: NSSize(width: 360, height: 300))
        let bands = rowBands(frame)
        let strip = ink(frame, x: Self.iconColumn, yRange: 0...(frame.height - 1))
        CaptureReadings.emit("INK 前提(固定色, Button 包装)：整列图标墨水=\(String(format: "%.4f", strip)) 文字行数=\(bands.count)")
        XCTAssertGreaterThan(strip, 0.01, "固定色都画不出来：这条管线不能用来判图标可见性")
    }

    /// 探针的名单必须**就是**产品在用的那份。
    ///
    /// 这条不测产品，测的是尺子的覆盖面 —— 上一版名单是手抄的，漂了两次（`sparkles` 早已换掉、
    /// 新分类的 `chart.bar` 没进来）而探针一路全绿。现在名单从枚举推导，
    /// 所以"覆盖全"这句话**必须**由一条会红的判据钉住：把推导改成字面量、
    /// 或者以后有人给 `SettingsCategory` 加一档而名单没跟着长，都要红。
    func testProbeCoversEveryCategoryIcon() throws {
        let probe = Self.symbolNames
        let product = SettingsCategory.allCases.map(\.icon)
        XCTAssertEqual(probe, product,
                       "探针量的符号与产品侧栏在用的不是一回事 ⇒ 这条尺子在量已经不存在的图标")
        XCTAssertFalse(probe.isEmpty, "名单空了会让上面那条恒真")
        // 刻意**没有**再写一条"源码里不许出现字面量名单"的扫描：
        // 名单一旦退回字面量，只要它今天恰好等于产品，那条扫描会绿、而这条会红 ——
        // 红的是"以后产品改了它没跟着改"，那正是漂的本身。扫自己源码还会踩自匹配
        // （needle 写在断言消息里就会命中自己），收益为零。
    }

    /// 每一枚图标都得**真的画得出东西**（固定色那条前提之下）。
    ///
    /// 这条抓的不是审美，是"符号名写错 / 这枚在 macOS 12 上不存在"：
    /// 那种情况下 SwiftUI 不报错，只是**什么都不画**，
    /// 于是设置侧栏少一个图标而全仓 658 条用例一条都不会红。
    /// 逐枚量而不只看整列：整列墨水 >0.01 会被其余五枚抬着走，一枚空白的没人喊。
    func testEveryCategoryIconActuallyDrawsSomething() throws {
        var readings: [String: Double] = [:]
        for name in SettingsCategory.allCases.map(\.icon) {
            let frame = try rasterize(
                sidebarColumn(iconColor: AnyShapeStyle(Color.black), wrappedInButton: true, names: [name]),
                size: NSSize(width: 360, height: 300))
            readings[name] = ink(frame, x: Self.iconColumn, yRange: 0...(frame.height - 1))
        }
        CaptureReadings.emit("INK 逐枚 " + readings.keys.sorted().map {
            "\($0)=\(String(format: "%.4f", readings[$0] ?? 0))"
        }.joined(separator: " "))
        for (name, value) in readings {
            XCTAssertGreaterThan(value, 0.002,
                                 "「\(name)」在图标列里一个像素都没画出来 ⇒ 符号名写错，或这枚在目标系统上不存在")
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
            clearHistoryAction: { nil },
            initialCategory: .general
        ))
        let frame = try rasterize(product, size: NSSize(width: 720, height: 540))
        let bands = rowBands(frame)
        var lines: [String] = []
        var collapsed = 0
        var absent = 0
        var wrongSide = 0
        for (index, category) in SettingsCategory.allCases.enumerated() where index < bands.count {
            let fraction = ink(frame, x: Self.iconColumn, yRange: bands[index])
            if fraction < 0.005 { collapsed += 1 }
            // R28：把"0 墨"拆成两种完全相反的故障。
            // 阈值取 4（不是 32）：这一档只问"这块地方动不动过"，不问"动得够不够黑"。
            let signed = signedInk(frame, x: Self.iconColumn, yRange: bands[index], threshold: 4)
            if fraction < 0.005 && signed.brighter + signed.darker == 0 { absent += 1 }
            // 这一臂是 `.aqua` ⇒ "画反了"只可能是**画成白的**。
            // 如果哪天偏暗的那一侧反而更多，那已经不是这条注释描述的那个伪影了，
            // 必须让它红到有人来改写这段（而不是继续拿"已知不可信"当挡箭牌）。
            if fraction < 0.005 && signed.brighter + signed.darker > 0 && signed.darker >= signed.brighter {
                wrongSide += 1
            }
            lines.append("\(category.icon)=\(String(format: "%.4f", fraction))"
                         + (fraction < 0.005
                            ? "（亮\(signed.brighter)/暗\(signed.darker)）" : ""))
        }
        CaptureReadings.emit("INK 产品设置侧栏(语义色) \(lines.joined(separator: " "))")
        CaptureReadings.emit(collapsed == 0
              ? "INK 结论 产品侧栏五个图标都画得出来 ⇒ 可以按帧判图标可见性"
              : "INK 结论 \(collapsed)/\(SettingsCategory.allCases.count) 行的图标列是 0.0000，"
                + "而同一套管线里固定色的同款符号能画到 0.18 以上 ⇒ "
                + "settings-* 帧的未选中行图标列不可信，不能据此判产品缺陷（也不能据此改产品颜色）")
        // **这一条有牙**：`absent` 不是"淡"，是"整列一个像素都没动过"。
        //
        // 上面那段结论打印把这族故障统一叫"不可信"，而 R28 实测它是**反相**：
        // 亮色帧里未选中的符号整列是 255（背景 248），暗色帧里另外几枚是 0（背景 24），
        // 每一枚符号的颜色在两帧里**恒定不随外观变** —— 那是离屏管线的语义色解析，不是产品。
        // "反相"要放行（不能为讨好帧把 `.primary` 换成固定色，审计第二轮就警告过），
        // "整列空白"不能放行：那是符号名写错 / 这枚在目标系统上不存在，
        // 而 `testEveryCategoryIconActuallyDrawsSomething` 量的是**复刻列**，量不到产品这一列。
        XCTAssertEqual(absent, 0,
                       "产品侧栏有 \(absent) 行的图标列连一个像素都没动过 ⇒ 这不是"
                       + "已知的反相伪影（那种情况像素会全部偏向背景的一侧），"
                       + "而是这枚符号真的没有进入画面：查符号名与目标系统可用性")
        XCTAssertEqual(wrongSide, 0,
                       "亮色帧里有 \(wrongSide) 行未选中符号偏**暗**的那一侧更多 ⇒ 它不是 R28 记下的"
                       + "那个「语义色被解析成白色」的伪影，而是另一件事。"
                       + "别把这条断言改成恒真：去读 `AGENT_UI_AUDIT` 第 22 项那段，重新判一遍再决定放行还是修产品")
    }
}
