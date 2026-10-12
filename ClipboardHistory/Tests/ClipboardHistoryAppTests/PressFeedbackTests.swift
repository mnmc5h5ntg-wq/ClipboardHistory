import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 按压态与焦点态（R4）的判据。
///
/// 不覆盖管线：本文件钉的是"按压的表达存在、可见、且真的接在按钮上"。
/// 点击之后的**结果**（复制、收藏、筛选）由 `RowInteractionTests` / `PipelineAcceptanceTests` 管，
/// 提示条与过渡的像素由 `MotionFilmstripTests` 管。
final class PressFeedbackTests: XCTestCase {

    // MARK: - 表达本身：三态真值表

    func testPressAppearanceTruthTable() {
        XCTAssertEqual(PressableAppearance.scale(isPressed: false, reduceMotion: false), 1.0,
                       "没按的时候不许有任何缩放：那会让静止界面看起来在抖")
        XCTAssertEqual(PressableAppearance.scale(isPressed: true, reduceMotion: false),
                       MotionCatalog.pressScale, "按下必须缩，而且缩多少只能由目录说")
        XCTAssertEqual(PressableAppearance.scale(isPressed: true, reduceMotion: true), 1.0,
                       "减弱动态时不许缩放：缩放是物理隐喻，不是信息")
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: true), VisualFill.pressed,
                       "减弱动态时缩放归零了，底色必须还在 —— 否则按下这件事完全没有表达")
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true), VisualFill.hover)
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: false), 0)
    }

    /// 强度次序是语义：hover < pressed < selected。反过来就是"瞬时态盖过持久态"。
    func testPressIntensitySitsBetweenHoverAndSelection() {
        XCTAssertLessThan(VisualFill.hover, VisualFill.pressed,
                          "按下比悬停更近一步，底色却更淡 ⇒ 界面在说反话")
        XCTAssertLessThan(VisualFill.pressed, VisualFill.selected,
                          "按下是瞬时态，不许盖过会留下来的选择")
        XCTAssertLessThan(MotionCatalog.pressScale, 1.0, "缩放必须往里，不是往外弹")
        XCTAssertGreaterThan(MotionCatalog.pressScale, 0.9,
                             "低于 0.9 的缩放会让图标跳位，读成'点歪了'而不是'按下去了'")
    }

    /// 那两个数**推得动像素**吗 —— 而且要**分通道**量。
    ///
    /// 为什么分开量：第一版这里只比"按下 vs 没按下"，于是变异对照（把 `pressScale` 改成 1.0）
    /// **绿着通过** —— 因为底色那一层还在变像素。一个把两件事混在一起的断言，
    /// 只能证明"这两幅图不一样"，证明不了"缩放本身有用"。缩放与底色各一条，
    /// 才各自打得住"把它调成恒等"的变异。
    func testPressedAppearanceIsVisibleAt44PointsChannelByChannel() {
        let idle = renderPill(scale: 1.0, fill: 0)

        let scaled = renderPill(scale: PressableAppearance.scale(isPressed: true, reduceMotion: false), fill: 0)
        let scaledFraction = Self.changedFraction(idle, scaled)
        XCTAssertGreaterThan(scaledFraction, 0.005,
                             "只改缩放时读不出任何像素差（\(String(format: "%.4f", scaledFraction))）⇒ 0.97 这一档是装饰")

        let filled = renderPill(scale: 1.0, fill: VisualFill.pressed)
        let filledFraction = Self.changedFraction(idle, filled)
        XCTAssertGreaterThan(filledFraction, 0.02,
                             "只改底色时读不出变化 ⇒ 减弱动态那条退化（只剩底色）是空的")

        let both = renderPill(scale: PressableAppearance.scale(isPressed: true, reduceMotion: false),
                              fill: VisualFill.pressed)
        // 不是"合起来必须更大"（那是量级问题，不是设计问题），而是**两通道互不遮蔽**：
        // 在已缩放的图上再加底色要看得见，在已有底色的图上再缩放也要看得见。
        XCTAssertGreaterThan(Self.changedFraction(both, scaled), 0.02,
                             "缩放之上再叠底色读不出来 ⇒ 两通道互相遮蔽，其中一条是白占位置")
        XCTAssertGreaterThan(Self.changedFraction(both, filled), 0,
                             "底色之上再缩放读不出来 ⇒ 缩放那一档在合成里根本没生效")

        XCTAssertEqual(Self.changedFraction(idle, idle), 0, "尺子在两幅相同的图上读出了变化 ⇒ 上面三个数都不算数")
    }

    // MARK: - 接线：不许只有表达、没有消费者

    /// 非菜单按钮必须全部接上按压态。
    ///
    /// 判据形状与 `testMotionParametersOutsideTheCatalogAreWhitelisted` 一样是**文件集合相等**：
    /// 多一个 `.plain` 要红（新按钮忘了接），少一个也要红（白名单过期）。
    /// 白名单只有菜单栏那一处，理由写在其代码旁边：系统菜单自己的高亮就是反馈。
    func testEveryNonMenuButtonHasPressFeedback() throws {
        var found: [String] = []
        for (file, source) in try productSources(in: "Views") {
            let code = codeOnly(source)
            for line in code.components(separatedBy: "\n") where line.contains(".buttonStyle(.plain)") {
                found.append(file)
            }
        }
        XCTAssertEqual(Set(found), Set(["MenuBarRecommendationsView.swift"]),
                       "这些文件还在用没有按压反馈的 .plain：接上 `.pressedStyle(in:)`，"
                           + "或把不接的理由写进代码旁边并加进白名单。现在扫到 \(found.sorted())")
        XCTAssertEqual(found.count, 2,
                       "菜单栏应当恰好两处（推荐项 + 收尾按钮）：\(found.sorted())")
    }

    /// 接了按压态的调用点数量也要钉住：只查"文件里出现过 pressedStyle"的话，
    /// 把 9 处删到 1 处照样绿。
    func testPressFeedbackWiringCountDoesNotShrink() throws {
        var sites = 0
        for (file, source) in try productSources(in: "Views") {
            _ = file
            sites += codeOnly(source).components(separatedBy: ".pressedStyle(in:").count - 1
        }
        XCTAssertGreaterThanOrEqual(sites, 9,
                                    "只有 \(sites) 处接了按压态：R4 落地时是 9 处。删一处就等于把那个按钮退回'按了没反应'")
    }

    // MARK: - 渲染夹具

    /// 44pt 圆控件，按 `scale` / `fill` 画一次，返回位图。
    private func renderPill(scale: CGFloat, fill: Double) -> NSBitmapImageRep {
        let size = 44
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 0, bitsPerPixel: 0)!
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        let context = NSGraphicsContext.current!.cgContext
        context.setFillColor(NSColor.white.cgColor)
        context.fill(CGRect(x: 0, y: 0, width: size, height: size))
        let side = CGFloat(size) * scale
        let rect = CGRect(x: (CGFloat(size) - side) / 2, y: (CGFloat(size) - side) / 2, width: side, height: side)
        context.setFillColor(NSColor(white: 0.55, alpha: 1).cgColor)
        context.fillEllipse(in: rect)
        if fill > 0 {
            context.setFillColor(NSColor(white: 0, alpha: fill).cgColor)
            context.fillEllipse(in: rect)
        }
        NSGraphicsContext.restoreGraphicsState()
        return rep
    }

    private static func changedFraction(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {
        let width = a.pixelsWide, height = a.pixelsHigh
        guard width == b.pixelsWide, height == b.pixelsHigh else { return 0 }
        var changed = 0
        var total = 0
        for y in stride(from: 0, to: height, by: 2) {
            for x in stride(from: 0, to: width, by: 2) {
                total += 1
                let pa = a.colorAt(x: x, y: y)!, pb = b.colorAt(x: x, y: y)!
                let delta = abs(pa.redComponent - pb.redComponent)
                    + abs(pa.greenComponent - pb.greenComponent)
                    + abs(pa.blueComponent - pb.blueComponent)
                if delta > 0.02 { changed += 1 }
            }
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    // MARK: - 夹具

    private func productSources(in directory: String) throws -> [(String, String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory, isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            return names.filter { $0.hasSuffix(".swift") }.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "PressFeedbackTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(directory)：守卫找不到被守卫的东西时必须红"])
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }
}
