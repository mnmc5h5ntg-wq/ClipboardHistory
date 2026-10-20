import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R236（BACKLOG 264 / D-220 的另一半）：13 那棵 SwiftUI 树里「都不是我想要的」那一行的墨，
/// 从此有**两轴**会红的判据，而不只是帧基线。
///
/// 为什么本轮才补：R235 把 12 那棵 AppKit 树的写死蓝交回系统（D-220），并在变异对照上实测过
/// 13 那棵没有牙 —— `M787`（把那颗蓝钉回 `MenuBarRecommendationsView`）跑出来是 **ESCAPED**，
/// 而 `App.swift:28` 就在实例化这棵树 ⇒ 它是活路径，只是没人管。只印不拦的读数等于没有读数。
///
/// 两轴各抓一种坏法，各自的刀：
/// ① 行为轴 —— 缝 `dismissRowInk` 给的墨（非 nil 时）必须在**静置底与选中底两种代理**上都过 D-220 那两条地板
///   （4.5 / 3.0）。抓「把墨钉进缝里」：M788 把缝改成 `.blue` ⇒ 亮档静置 3.52 ⇒ 红。
/// ② 结构轴 —— 这一行的标签必须经由 `dismissRowLabel()`，且该函数体内 `.foregroundStyle` 只能有一处、
///   且它的参数必须是缝给的 `ink`。抓「绕过缝就地钉色」：M787 就地钉 `.blue` ⇒ 出现第二处 ⇒ 红。
///
/// 尺与 12 那棵同一颗（WCAG 比值、固定外观下解 sRGB、参照臂先自证），地板也从 D-220 的实测继承，
/// 不新造数：本轮实测缝返回 nil ⇒ 走系统正文墨 `labelColor`，两档参照 16.67 / 21.00 过线。
///
/// 底色是**代理**：离屏进程画不出真菜单的 vibrant 材质（D-093），所以这里用系统给「静置/选中」的语义色当底，
/// 并把色号一起印出来，不许把代理说成实测的材质。悬停那一行的最终观感仍挂在人工批次（BACKLOG 265）。
///
/// 不覆盖管线：这里量的是「产品标签实际取自哪颗墨、它有没有绕过缝」，不是菜单内容/条数/脱敏
/// —— 那条管线判据在 `MenuBarPopulationTests`，帧侧基线在 `UICaptureTests` 的 `menubar-recommendations-*`。
final class MenuBarSwiftUIDismissRowInkTests: XCTestCase {
    private struct Comp { let r: Double, g: Double, b: Double, a: Double }

    private func srgb(_ color: NSColor, in appearance: NSAppearance) -> Comp? {
        var out: Comp?
        appearance.performAsCurrentDrawingAppearance {
            if let c = color.usingColorSpace(.sRGB) {
                out = Comp(r: Double(c.redComponent), g: Double(c.greenComponent),
                           b: Double(c.blueComponent), a: Double(c.alphaComponent))
            }
        }
        return out
    }

    private func luma(_ c: Comp) -> Double {
        func lin(_ v: Double) -> Double {
            v <= 0.04045 ? v / 12.92 : pow((v + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b)
    }

    private func ratio(_ a: Comp, _ b: Comp) -> Double {
        let x = luma(a), y = luma(b)
        return (max(x, y) + 0.05) / (min(x, y) + 0.05)
    }

    private func f2(_ v: Double) -> String { String(format: "%.2f", v) }
    private func triple(_ c: Comp) -> String {
        "\(Int((c.r * 255).rounded()))/\(Int((c.g * 255).rounded()))/\(Int((c.b * 255).rounded()))"
    }

    // MARK: ①尺自己的对照（先证明这把尺分得开同色与差色，才配给产品定罪）

    func testContrastRulerSeparatesSameColourFromDifferent() throws {
        let dark = try XCTUnwrap(NSAppearance(named: .darkAqua))
        let light = try XCTUnwrap(NSAppearance(named: .aqua))
        guard let white = srgb(.white, in: dark), let black = srgb(.black, in: dark),
              let blueDark = srgb(NSColor(Color.blue), in: dark),
              let blueLight = srgb(NSColor(Color.blue), in: light) else {
            return XCTFail("解析不出 sRGB ⇒ 这把尺没有对象，不判（不是通过）")
        }
        XCTAssertEqual(ratio(white, white), 1.0, accuracy: 0.001,
                       "同色读不出 1.00 ⇒ 后面所有数都没有意义")
        XCTAssertGreaterThan(ratio(white, black), 15.0, "黑白都拉不开 ⇒ 这把尺是坏的")
        XCTAssertNotEqual(triple(blueDark), triple(blueLight),
                          "缝给的这颗目录色不随外观动 ⇒ ②里那句「按档判」的前提要重查")
    }

    // MARK: ②行为轴：缝给的墨，两档 × 两种底色都要过 D-220 那两条地板

    /// `@MainActor` **不许删**：`MenuBarRecommendationsView`  conforms `View`，在本轮 runner 那套
    /// SDK 上整个类型的成员都被推断成 main-actor 隔离 ⇒ 非隔离上下文读 `dismissRowInk` 是
    /// **编译期 error**（run 39345462910 的 STEP[4] 就红在这一句，本机工具链放过）。
    /// 这一格本来就只在主线程解 `NSAppearance`，标注不改行为，只把「换台机器就编译不过」这件事
    /// 交给 `MenuBarSeamReaderIsolationTests` 钉住。
    @MainActor
    func testSeamInkClearsTheTextFloorInBothStates() throws {
        guard #available(macOS 13, *) else { throw XCTSkip("这棵 SwiftUI 树是 macOS 13 起的") }
        // 产品入口：这一行实际用的就是这条缝与这个标签构造器（③钉住它不许绕）。
        let seam: NSColor? = MenuBarRecommendationsView.dismissRowInk.map { NSColor($0) }
        let inkColor = seam ?? .labelColor
        var lines: [String] = []
        for (tag, appearance) in [("dark", NSAppearance(named: .darkAqua)!),
                                  ("light", NSAppearance(named: .aqua)!)] {
            guard let ink = srgb(inkColor, in: appearance),
                  let bg = srgb(.windowBackgroundColor, in: appearance),
                  let sel = srgb(.selectedTextBackgroundColor, in: appearance),
                  let ac = srgb(.controlAccentColor, in: appearance),
                  let ref = srgb(.labelColor, in: appearance) else {
                return XCTFail("档 \(tag)：某一侧解析不出 sRGB ⇒ 没有对象，不判")
            }
            let refNormal = ratio(ref, bg)
            XCTAssertGreaterThan(refNormal, 4.5,
                                 "档 \(tag) 的参照臂（正文墨 on 静置底）自己就只有 \(f2(refNormal)) ⇒ "
                                 + "这把尺在这一档没打开，不许据此判产品")
            let normal = ratio(ink, bg)
            let selected = ratio(ink, sel)
            XCTAssertGreaterThanOrEqual(normal, 4.5,
                "档 \(tag) 静置底上这一行的墨只有 \(f2(normal)):1（地板 4.5，来自 D-220 实测；"
                + "那颗写死的蓝当年是 亮 3.52 / 暗 5.16，同棵菜单正文参照 21.00 / 16.67）")
            XCTAssertGreaterThanOrEqual(selected, 3.0,
                "档 \(tag) 选中底上这一行的墨只有 \(f2(selected)):1（地板 3.0；"
                + "写死的蓝 = 亮 2.36 / 暗 1.93，压强调底 = 1.14 / 1.24，正文参照 = 14.08 / 6.23）")
            lines.append("档=\(tag) 墨=\(seam == nil ? "缝返回nil(交回系统)" : "缝钉死")\(triple(ink)) "
                         + "静置=\(f2(normal)) 选中=\(f2(selected)) 强调=\(f2(ratio(ink, ac))) "
                         + "参照静置=\(f2(refNormal)) 参照选中=\(f2(ratio(ref, sel)))")
        }
        CaptureReadings.emit("MENUBAR_SWIFTUI_DISMISS_INK 通道=产品的缝(dismissRowInk) " + lines.joined(separator: " | "))
    }

    // MARK: ③结构轴：这一行不许绕过缝就地钉色（正对照 = 变异刀 M787）

    func testDismissRowLabelRoutesThroughTheSeam() throws {
        let path = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // Tests/ClipboardHistoryAppTests
            .deletingLastPathComponent()   // Tests
            .deletingLastPathComponent()   // ClipboardHistory
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift")
        guard let raw = try? String(contentsOf: path, encoding: .utf8) else {
            return XCTFail("读不到产品源码 \(path.path) ⇒ 证据指针指不到东西，这一格不许绿")
        }
        let lines = raw.components(separatedBy: "\n")

        // 1) 这一行的标签必须经由缝出来（就地拼 Text 就不许）。
        //    剥掉行注释再数：文档注释里引用 `Self.dismissRowLabel()` 曾被这条守卫当成一处调用（本轮实测红过一次）。
        let stripped = raw.components(separatedBy: "\n").map { line in
            line.components(separatedBy: "//").first ?? line
        }
        let routed = stripped.filter { $0.contains("Self.dismissRowLabel()") }
        XCTAssertEqual(routed.count, 1,
                       "body 里没有且只有一处走 `Self.dismissRowLabel()` ⇒ 这一行又变成就地拼的 Text，"
                       + "缝就成了没人走的装饰（M787 那种钉法会重新隐形）")

        // 2) 标签构造器体内：着色只能有一处，而且必须拿缝给的那颗
        guard let start = lines.firstIndex(where: { $0.contains("static func dismissRowLabel") }) else {
            return XCTFail("文件里没有 `dismissRowLabel()` ⇒ 缝被删了，②③两侧判据同时失去对象")
        }
        var depth = 0
        var body: [String] = []
        var entered = false
        for line in lines[start...] {
            depth += line.filter { $0 == "{" }.count - line.filter { $0 == "}" }.count
            if line.contains("{") { entered = true }
            if entered { body.append(line) }
            if entered && depth <= 0 { break }
        }
        // 剥掉行注释：注释里提到 `.foregroundStyle` 不许被当成一次着色（R83 的老坑）
        let code = body.map { line in
            line.components(separatedBy: "//").first ?? line
        }
        let styled = code.enumerated().filter { $0.element.contains(".foregroundStyle(") }
        XCTAssertEqual(styled.count, 1,
                       "标签构造器里有 \(styled.count) 处 `.foregroundStyle(`（地板：恰好 1 处、且必须拿缝的值）。"
                       + "多出来的那些就是绕过缝就地钉的墨 ⇒ 行号 \(styled.map { start + $0.offset + 1 })；"
                       + "缝的定义在 \(lines.firstIndex(where: { $0.contains("static var dismissRowInk") }).map(String.init) ?? "?") 行")
        XCTAssertTrue(styled.first?.element.contains("ink") == true,
                      "那唯一一处着色没拿缝给的 `ink` ⇒ 缝不参与判定，②的读数说的就不是这一行")
    }
}
