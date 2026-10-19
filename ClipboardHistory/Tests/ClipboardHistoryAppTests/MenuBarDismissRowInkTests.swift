import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R235（第 234 轮 / Round 232）：菜单栏「都不是我想要的」那一行的墨，**从产品真菜单项上读**。
///
/// 起因是看图：`menubar-recommendations-320x320` 最右下面那条「都不是我想要的」是全页唯一
/// 一块有彩度的墨。目测只能得出"它是蓝的"，而**这一句在台账里不算读数**（形容词第七次）。
/// 另两句目测（"理由被切成半字""行顶到 x≈0"）恰好全在 D-093 禁止的那一侧 —— 菜单栏帧
/// **可以**判颜色档，**不可以**判宽度 / 截断 / 对齐 / 命中区，所以那两句不配开条目、不配改产品。
///
/// 本轮量的这一件能从产品入口问：`MenuBarController.populate(_:)` 交出来的真 `NSMenuItem`
/// 上，那一行的墨原先是**显式写死**的一颗蓝（13 那棵走 `MenuBarRecommendationsView`）。
/// 墨写死就不参与系统为选中态准备的换色，于是有两种解释、修法相反：
/// ① 悬停底色铺强调色而墨还是蓝 ⇒ 蓝压蓝，那一行读不出来；
/// ② 系统把显式色覆盖掉 ⇒ 蓝只在静置态存在，问题退回"这块彩度是否喧宾夺主"。
/// 分辨①②要真机把菜单打开悬停取图（离屏进程没有走窗口服务器的通道，D-093；真机通道
/// 2026-10-17 起在本机关闭）。**但两档实测之后不需要分辨**：写死那颗蓝在静置底上
/// 3.52（亮）/ 5.16（暗）、在同棵菜单正文参照上是 21.00 / 16.67；在选中底代理上 2.36 / 1.93，
/// 压强调底 1.14 / 1.24。**两种态它都输** ⇒ ①②无论哪个成立，这颗墨都得交回系统（D-220）。
///
/// 底色是**代理**：离屏画不出真菜单的 vibrant 材质，所以这里用系统给"静置/选中"的语义色当底，
/// 并把色号一起打出来，不许把代理说成实测的材质。悬停那一行的最终观感仍挂在人工批次上。
///
/// 不覆盖管线：这里量的是"产品交出去的菜单项上那颗墨的身份，与它在两种底色代理上的对比"。
/// 菜单内容/条数/脱敏那条管线判据在 `MenuBarPopulationTests`。
@MainActor
final class MenuBarDismissRowInkTests: XCTestCase {
    private struct Comp { let r: Double, g: Double, b: Double, a: Double }
    private final class Box { var value: Comp? }

    private func waitUntil(
        _ description: String,
        timeout: TimeInterval = 5.0,
        condition: @MainActor () -> Bool
    ) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立")
    }

    private func entry(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text), thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari")
    }

    private func populatedStore() -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        store.add(entry("普通的一条记录 abcdef"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(entry("ghp_" + String(repeating: "K", count: 36)), timestamp: Date(timeIntervalSince1970: 2))
        return store
    }

    /// 产品入口：`populate(_:)` 交出来的真菜单 + 那一行本身。
    private func dismissItem(in store: HistoryStore) -> (NSMenu, NSMenuItem)? {
        let controller = MenuBarController()
        controller.configure(commandHandler: { _ in }, historyStore: store, pasteHandler: nil)
        let menu = NSMenu()
        controller.populate(menu)
        let title = AppCommand.dismissAllRecommendations.title
        guard let item = menu.items.first(where: { $0.title == title }) else { return nil }
        return (menu, item)
    }

    // MARK: 尺（把目录色在**固定外观**下解成 sRGB 分量；外观不钉死就会读到看天吃饭的数）

    private func srgb(_ color: NSColor, in appearance: NSAppearance) -> Comp? {
        let box = Box()
        appearance.performAsCurrentDrawingAppearance {
            if let c = color.usingColorSpace(.sRGB) {
                box.value = Comp(r: Double(c.redComponent), g: Double(c.greenComponent),
                                 b: Double(c.blueComponent), a: Double(c.alphaComponent))
            }
        }
        return box.value
    }

    /// WCAG 相对亮度（sRGB 分量先解伽马）—— 与账里其他对比度同一把尺。
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

    // MARK: ①尺自己的对照：分得开"同色"与"差色"，才配给产品定罪

    func testContrastRulerSeparatesSameColourFromDifferent() {
        let dark = NSAppearance(named: .darkAqua)!
        guard let white = srgb(.white, in: dark), let black = srgb(.black, in: dark),
              let blue = srgb(.systemBlue, in: dark) else {
            return XCTFail("解析不出 sRGB ⇒ 尺没有对象，不判（不是通过）")
        }
        XCTAssertEqual(ratio(white, white), 1.0, accuracy: 0.001,
                       "同色读不出 1.00 ⇒ 后面所有数都没有意义")
        XCTAssertEqual(ratio(blue, blue), 1.0, accuracy: 0.001)
        XCTAssertGreaterThan(ratio(white, black), 15.0, "黑白都拉不开 ⇒ 这把尺是坏的")
        // 这颗目录色按外观解析（本轮实测 0/145/255 与 0/136/255）：它随**外观**变，
        // 不随**选中态**变 —— 这正是"写死墨 ⇒ 悬停不换色"的机制前提。
        guard let lightBlue = srgb(.systemBlue, in: NSAppearance(named: .aqua)!) else {
            return XCTFail("亮档解析不出参照色 ⇒ 这一档没有对象，不判")
        }
        XCTAssertNotEqual(triple(blue), triple(lightBlue),
                          "两档解出同一个色号 ⇒ 这颗色不随外观动，上面那句机制前提要重查")
    }

    // MARK: ②那一行的墨：两档 × 两种底色都必须过同两条地板

    /// 地板来自本轮实测，不是先写数再找理由：
    /// 静置 4.5（正文下限；参照臂 labelColor 实测 16.67/21.00，写死的蓝 5.16/**3.52** ⇒ 亮档当场红）；
    /// 选中 3.0（非正文下限；参照臂实测 6.23/14.08，写死的蓝 1.93/2.36 ⇒ 两档都红）。
    func testDismissRowInkClearsTheTextFloorInBothStates() {
        let store = populatedStore()
        waitUntil("推荐非空（否则菜单走「暂无推荐」那一支，根本没有 dismiss 行）") {
            !store.predictionSuggestionEntries.isEmpty
        }
        guard let (menu, item) = dismissItem(in: store) else {
            return XCTFail("菜单里没有「\(AppCommand.dismissAllRecommendations.title)」这一行 ⇒ 本轮尺的对象没了")
        }
        XCTAssertTrue(item.isEnabled,
                      "dismiss 行若被禁掉，选中态就不存在，两种底色都失去对象")
        // 分组由分隔线承担（去掉写死的墨之后，这一行的身份 = 它在最后一段 + 上面那条分隔线）。
        guard let idx = menu.items.firstIndex(where: { $0 === item }), idx > 0 else {
            return XCTFail("找不到 dismiss 行在菜单里的位置 ⇒ 分隔线那一格没有对象")
        }
        XCTAssertTrue(menu.items[idx - 1].isSeparatorItem,
                      "dismiss 行前面没有分隔线 ⇒ 它既没有彩度也没有分组，会和其他命令混成一片")

        // 产品写死了墨就拿它判；交回系统就拿系统正文那颗（labelColor = 参照臂）判。
        // 两条路共用同两条地板 ⇒ "把那颗蓝钉回去"和"钉成别的彩度"都会红。
        let explicit: NSColor? = item.attributedTitle.flatMap { attributed in
            attributed.attributes(at: 0, effectiveRange: nil)[
                NSAttributedString.Key.foregroundColor] as? NSColor
        }
        let inkColor = explicit ?? NSColor.labelColor
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
                "档 \(tag) 静置底上 dismiss 行的墨只有 \(f2(normal)):1（地板 4.5；"
                + "本轮实测写死那颗蓝 = 亮 3.52 / 暗 5.16，同一棵菜单正文参照 = 21.00 / 16.67）")
            XCTAssertGreaterThanOrEqual(selected, 3.0,
                "档 \(tag) 选中底上 dismiss 行的墨只有 \(f2(selected)):1（地板 3.0；"
                + "写死那颗蓝 = 亮 2.36 / 暗 1.93，压强调底 = 1.14 / 1.24，正文参照 = 14.08 / 6.23）")
            lines.append("档=\(tag) 墨=\(explicit == nil ? "交回系统" : "产品写死")\(triple(ink)) "
                         + "静置=\(f2(normal)) 选中=\(f2(selected)) 强调=\(f2(ratio(ink, ac))) "
                         + "参照静置=\(f2(refNormal)) 参照选中=\(f2(ratio(ref, sel))) "
                         + "选中底色号=\(triple(sel)) 强调底色号=\(triple(ac))")
        }
        CaptureReadings.emit("MENUBAR_DISMISS_INK 通道=产品真菜单项 " + lines.joined(separator: " | "))
    }
}
