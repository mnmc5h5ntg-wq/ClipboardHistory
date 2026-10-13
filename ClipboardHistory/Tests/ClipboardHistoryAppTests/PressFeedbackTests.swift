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
        // R13：`hoverLevel` 是**新参数**，不测它等于"小控件抬一档"这句话只是注释。
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: true,
                                                      hoverLevel: VisualFill.controlHover),
                       VisualFill.controlHover)
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: true, isHovered: true,
                                                      hoverLevel: VisualFill.controlHover),
                       VisualFill.pressed,
                       "抬了悬停档之后，按下仍然要盖过悬停 —— 次序不能因为参数可变就翻")
        XCTAssertEqual(PressableAppearance.fillOpacity(isPressed: false, isHovered: false,
                                                      hoverLevel: VisualFill.controlHover), 0)
        XCTAssertLessThan(VisualFill.controlHover, VisualFill.pressed,
                          "小控件的悬停档也必须留在按下之下，否则整条 hover<press<selected 次序作废")
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
            // R13 把检测面从"只查 .plain"扩成"查所有拿掉反馈的样式"：
            // 侧栏那五颗批量按钮（含删除）用的是 `.buttonStyle(.borderless)`，
            // 这条守卫**扫不到它** —— 于是它在全绿的套件里活了很久。
            // "按一个拼写查一族" 与 "按名字查消费者会被前缀白拿" 是同一族：检测面比缺陷面窄。
            let noFeedback = [".buttonStyle(.plain)", ".buttonStyle(.borderless)",
                              ".buttonStyle(.link)", ".buttonStyle(.accessoryBar)"]
            for line in code.components(separatedBy: "\n") where noFeedback.contains(where: line.contains) {
                found.append(file)
            }
        }
        XCTAssertEqual(Set(found), Set(["MenuBarRecommendationsView.swift"]),
                       "这些文件还在用没有按压反馈的 .plain：接上 `.pressedStyle(in:)`，"
                           + "或把不接的理由写进代码旁边并加进白名单。现在扫到 \(found.sorted())")
        XCTAssertEqual(found.count, 2,
                       "菜单栏应当恰好两处（推荐项 + 收尾按钮）：\(found.sorted())")
    }

    /// 悬停那一档必须**真的可达**。R13 抓到的一条：`PressedStyle.makeBody` 里硬写着
    /// `isHovered: false`（因为 `ButtonStyle.makeBody` 不能有 `@State`），
    /// 于是 `VisualFill.hover` 在全 App 每一个按钮上都是死档 ——
    /// 而 `fillOpacity` 的真值表一直是绿的：**载荷绿、消费侧坏**。
    /// 所以这条守卫问的不是"函数对不对"，是"调用点有没有把两个分支都喂到"。
    func testHoverArmIsReachableFromTheButtonStyle() throws {
        let style = codeOnly(try productSource(named: "Views/PressableStyle.swift"))
        XCTAssertFalse(style.contains("isHovered: false"),
                       "按压样式又把悬停写死成 false ⇒ hover 那一档再次变成永远不可达的死参数")
        XCTAssertTrue(style.contains(".onHover"),
                      "悬停要由样式内部一个能持有状态的视图来记，否则 `makeBody` 里没有 @State 可用")
        XCTAssertTrue(style.contains("value: isHovered"),
                      "悬停那一档要进 `.hover` 的事务，不然它是硬切")
    }

    /// 上一条管的是"样式内部有没有悬停这一半"，这一条管的是**接缝**：
    /// 调用方给的 `hoverLevel` 有没有原样送到那个持有状态的视图手里。
    ///
    /// 为什么单独一条：`hoverLevel` 是 R13 新加的参数，真值表测了纯函数、白名单测了调用点，
    /// 唯独中间这一步没人钉 —— 变异 M58（`makeBody` 里把 `hoverLevel: hoverLevel`
    /// 换成 `hoverLevel: VisualFill.hover`）**全绿通过**，
    /// 而它的产品后果是"小控件抬一档"这句话在运行时根本不成立。
    /// 这一族叫**载荷绿、消费侧坏**，本轮它是被新参数自己重演了一遍。
    ///
    /// 判据形状用的是花括号配平的**区域**，不是整文件 `contains`：
    /// 整文件里"哪里"出现 `VisualFill.` 不算数（默认值那一行本来就该有它），
    /// 只有出现在转交点上才是重新供档。
    func testStyleForwardsItsParametersInsteadOfResupplyingDefaults() throws {
        let style = codeOnly(try productSource(named: "Views/PressableStyle.swift"))
        let body = region(in: style, named: "func makeBody")
        XCTAssertTrue(body.contains("PressedLabel("),
                      "makeBody 不再构造那个能持有悬停状态的视图 ⇒ 上面两条判据全部退化成纸上的")
        for input in ["fillShape: fillShape", "scales: scales",
                      "reduceMotion: reduceMotion", "hoverLevel: hoverLevel"] {
            XCTAssertTrue(body.contains(input),
                          "转交点丢了 \(input) ⇒ 调用方给的这一档在运行时被结构体默认值顶掉")
        }
        XCTAssertFalse(body.contains("VisualFill."),
                       "转交点出现常量 ⇒ 有人在接缝处重新供给默认档（M58 的形状）")

        // 新参数若没有调用点读它，它就只是一个类型定义。"加了参数"与"有人用"是两件事
        // （`feedback-counting-and-wording` 里那条"谁在读旧数字"的改口径审计同一族）。
        var consumers = 0
        for (file, source) in try productSources(in: "Views") {
            _ = file
            consumers += codeOnly(source)
                .components(separatedBy: "hoverLevel: VisualFill.controlHover").count - 1
        }
        XCTAssertEqual(consumers, 3,
                       "只有 \(consumers) 处小控件显式抬了悬停档：R13 收进来的是三处"
                       + "（侧栏五颗批量按钮、排除名单的「移除」、回执的 ×）。"
                       + "多一处要红（提醒把新位点判一遍），少一处也要红（等于把它退回 6% 那一档）")
    }

    /// 区域助手自己是**尺子**，所以它自己也要被量一次。
    /// 少了这一条，"区域"可以随时退化成整文件而没人知道 —— 那正是它要解决的弱点。
    func testRegionHelperIsATruthTable() throws {
        let style = codeOnly(try productSource(named: "Views/PressableStyle.swift"))
        let body = region(in: style, named: "func makeBody")
        XCTAssertTrue(body.contains("PressedLabel("), "区域助手取不到 makeBody 的内容")
        XCTAssertFalse(body.contains("var hoverLevel"),
                       "区域把下一个成员也吞了 ⇒ 它其实是整文件，'按区域判'的判别力是假的")
        let label = region(in: style, named: "var body: some View")
        XCTAssertTrue(label.contains(".onHover"), "区域助手取不到 PressedLabel.body 的内容")
        XCTAssertFalse(label.contains("func makeBody"), "同上：body 区域不许把 makeBody 也圈进来")
        // 取不到的那一路：哨兵串必须**不含**任何真实 needle，否则"找不到文件里的成员"
        // 会被读成"这里没有重新供档"—— 把红伪装成绿，仓库里记过不止一次。
        let missing = "\u{0}REGION-NOT-FOUND\u{0}"
        XCTAssertFalse(missing.contains("VisualFill."),
                       "哨兵串若含 needle，'区域取不到'会让禁止重新供档那条断言全绿")
    }

    /// 取某个成员（`func` 或 `var`）的**函数体**：从声明行开始，按花括号配平到闭合。
    /// 与 `DailyCopyHeatmapTests` 里那份同源同规矩（跨文件不共享：两边 needle 不同，
    /// 抽公共层会让一条测试文件依赖另一条测试文件的私有实现）。
    ///
    /// 取不到 ⇒ **当场 XCTFail** 并返回一个不可能匹配任何 needle 的哨兵串，
    /// 不许安静返回空串：空串会让下面所有 `XCTAssertFalse(contains:)` 全绿。
    private func region(in code: String, named declaration: String) -> String {
        let lines = code.components(separatedBy: "\n")
        guard let start = lines.firstIndex(where: { $0.contains(declaration) }) else {
            XCTFail("区域取不到：\(declaration) —— 守卫看不到被守卫的东西时必须红")
            return "\u{0}REGION-NOT-FOUND\u{0}"
        }
        var depth = 0
        var opened = false
        var collected: [String] = []
        for index in start..<lines.count {
            let line = lines[index]
            collected.append(line)
            depth += line.filter { $0 == "{" }.count
            if line.contains("{") { opened = true }
            depth -= line.filter { $0 == "}" }.count
            if opened, depth <= 0 { break }
        }
        return collected.joined(separator: "\n")
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let file = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory + "/" + name)
            if let text = try? String(contentsOf: file, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        XCTFail("找不到 \(relative) ⇒ 守卫看不到被守卫的东西时必须红")
        return ""
    }

    /// 接了按压态的调用点数量也要钉住：只查"文件里出现过 pressedStyle"的话，
    /// 把 9 处删到 1 处照样绿。
    func testPressFeedbackWiringCountDoesNotShrink() throws {
        var sites = 0
        for (file, source) in try productSources(in: "Views") {
            _ = file
            sites += codeOnly(source).components(separatedBy: ".pressedStyle(in:").count - 1
        }
        XCTAssertGreaterThanOrEqual(sites, 12,
                                    "只有 \(sites) 处接了按压态：R4 落地时 9 处，R13 把三处 `.borderless`"
                                    + "（侧栏五颗批量按钮、排除名单的「移除」、回执的 ×）收进来之后是 12 处。"
                                    + "删一处就等于把那个按钮退回'按了没反应'")
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
