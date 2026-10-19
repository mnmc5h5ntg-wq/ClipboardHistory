import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 按压态与焦点态（R4）的判据。
///
/// 不覆盖管线：本文件钉的是"按压的表达存在、可见、且真的接在按钮上"。
/// 点击之后的**结果**（复制、收藏、筛选）由 `RowInteractionTests` / `PipelineAcceptanceTests` 管，
/// 提示条与过渡的像素由 `MotionFilmstripTests` 管。
///
/// `@MainActor`：R14 起这个文件要真的画像素（`renderFill` 走 `NSHostingView` + `cacheDisplay`），
/// 而 AppKit 的绘制入口全在主线程上 —— 不加这个标注，编译器会给出八条
/// "main actor-isolated … can not be referenced from a nonisolated context"，
/// 而 CI 是零告警的（与 `UICaptureTests` / `OffscreenSymbolInkProbeTests` 同一处理）。
@MainActor
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
    ///
    /// R77 再加一根轴：`PRESS_AXIS` 那三行把每一次比较的**亮度差 / alpha差 / 并集差**都打出来。
    /// 理由不是"多打点信息"，是这一族的夹具画的正是 `NSColor(white: 0, alpha: fill)` ——
    /// 黑墨按透明度叠，理论上可以只在 alpha 上动；而旧尺子读那一下是 0，
    /// 于是"减弱动态只剩底色"会被判成**空的**（判错产品，不是判错尺子）。
    /// 今天这两根轴各读到多少，写在账本 R77 那一节，来源就是这三行。
    func testPressedAppearanceIsVisibleAt44PointsChannelByChannel() {
        let idle = renderPill(scale: 1.0, fill: 0)

        let scaled = renderPill(scale: PressableAppearance.scale(isPressed: true, reduceMotion: false), fill: 0)
        let scaledFraction = Self.changedFraction(idle, scaled)
        print("PRESS_AXIS 缩放 " + Self.axisLine(idle, scaled))
        XCTAssertGreaterThan(scaledFraction, 0.005,
                             "只改缩放时读不出任何像素差（\(String(format: "%.4f", scaledFraction))）⇒ 0.97 这一档是装饰")

        let filled = renderPill(scale: 1.0, fill: VisualFill.pressed)
        let filledFraction = Self.changedFraction(idle, filled)
        print("PRESS_AXIS 底色 " + Self.axisLine(idle, filled))
        XCTAssertGreaterThan(filledFraction, 0.02,
                             "只改底色时读不出变化 ⇒ 减弱动态那条退化（只剩底色）是空的")

        let both = renderPill(scale: PressableAppearance.scale(isPressed: true, reduceMotion: false),
                              fill: VisualFill.pressed)
        // 不是"合起来必须更大"（那是量级问题，不是设计问题），而是**两通道互不遮蔽**：
        // 在已缩放的图上再加底色要看得见，在已有底色的图上再缩放也要看得见。
        print("PRESS_AXIS 缩放之上叠底色 " + Self.axisLine(both, scaled))
        print("PRESS_AXIS 底色之上叠缩放 " + Self.axisLine(both, filled))
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
        // R15：`labelPadding` 走的是同一条路（样式字段 → 转交 → 真的挂上）。
        // 少任何一环，"命中区跟着药丸一起长"这句话就是注释。
        XCTAssertTrue(style.contains("labelPadding: labelPadding"),
                      "样式把调用方给的 labelPadding 丢了 ⇒ 三处小控件的命中区又回到贴着笔画那一圈")
        XCTAssertTrue(style.contains(".padding(labelPadding)"),
                      "padding 挂上去了但挂的是常量 ⇒ 参数是装饰")
    }

    /// 药丸/命中区这一档必须**有人用**。R13 的教训：新参数没有消费者，
    /// 它就只是一个类型定义（"加了"与"有人用"是两件事）。
    ///
    /// R20 顺手改了这两处，两处都是被自己的变异逼出来的：
    /// ① 从"一个总数"改成"按文件点名"：总数只能告诉"变了"，点名能告诉**哪一处**变了 ——
    ///    与本轮在 `hoverLevel` 那条上犯的同一个错对照着看，一个只报数的守卫最容易把"没做完"读成"做完了"。
    /// ② 从"出现过 `labelPadding:` 字样"改成"**值必须大于 0**"：
    ///    变异 M88 把清除 × 写成 `labelPadding: 0`，旧写法**全绿通过** —— 它在数字符串，不在数参数。
    ///    `labelPadding: 0` 的意思就是"没有命中区"，而它是这条守卫眼里的"有"。
    ///    这一族叫"按名字查消费者会被前缀白拿"。
    func testSmallControlsAskForThePillPadding() throws {
        var expected: [String: Int] = [
            // 侧栏五颗批量按钮（一次调用管一排）
            "HistorySidebarView.swift": 1,
            // 排除名单的「移除」+ 回执的 ×
            "SettingsView.swift": 2,
            // R20：清除 ×。它的 label 之前**只有字形那么大**（约 14pt，没有 frame），
            // 是全 App 最小的一颗可点控件。
            "SearchField.swift": 1,
        ]
        for (file, source) in try productSources(in: "Views") {
            // 声明这个参数的那个文件必须**先摘掉**：它自己就有五处 `labelPadding:`
            // （字段、转交、`.padding(...)`、扩展的默认值与转交），
            // 不摘的话这条"有没有消费者"会拿声明当消费 —— 与"扫自身源码的守卫要先把守卫自己摘掉"同族。
            if file == "PressableStyle.swift" { continue }
            let hits = Self.callArguments(in: codeOnly(source), named: ".pressedStyle(")
                .filter { (Self.number(after: "labelPadding:", in: $0) ?? 0) > 0 }
                .count
            if hits > 0 {
                XCTAssertEqual(expected[file], hits,
                               "\(file) 的 `labelPadding` 位点数是 \(hits)，账本记的是 \(expected[file] ?? 0)"
                               + " ⇒ 有人加/删了一处小控件的命中区，重判它该不该有（整行类按钮不该加，它有自己的内边距）")
                expected[file] = nil
            }
        }
        XCTAssert(expected.isEmpty,
                  "这些文件里的 `labelPadding` 位点不见了：\(expected.keys.sorted())"
                  + " ⇒ 那颗按钮又退回'贴着笔画的一圈'，命中区也跟着缩回字形大小")
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
        //
        // **R20 把这条从"数个数"改成了"按形状要求每一处都表态"。**
        // 旧版写的是 `XCTAssertEqual(consumers, 3)`，于是它把"清扫只做了三处"这件事
        // 钉成了"这就是完成态"：剩下五处圆形图标按钮（行首星标、清除 ×、播放、静音、
        // 药丸四颗）一直用着给整行定的 0.06，而守卫全绿。
        // **一条只数已完成部分的守卫，会把没做完的工作伪装成边界** —— 这是本轮最该记的一条。
        var circular = 0
        var silent: [String] = []
        for (file, source) in try productSources(in: "Views") {
            for arguments in Self.callArguments(in: codeOnly(source), named: ".pressedStyle(") {
                guard arguments.contains("in: Circle()") else { continue }
                circular += 1
                if !arguments.contains("hoverLevel:") { silent.append(file) }
            }
        }
        XCTAssertEqual(silent, [],
                       "这些圆形图标按钮没有表态自己用哪一档悬停，于是它们拿的是给整行定的 0.06："
                       + "\(silent)。圆形按钮都是小控件，要么写 `VisualFill.controlHover`，"
                       + "要么像详情区药丸那样**自己已经画了一层**就写 `hoverLevel: 0`")
        XCTAssertEqual(circular, 5,
                       "圆形 `pressedStyle` 调用点从 5 处变成 \(circular) 处 ⇒ 新增/删除位点要重新判一遍档")

        // 抬档这件事的"消费者计数"仍然留着，但它不再是唯一的网。
        var consumers = 0
        for (file, source) in try productSources(in: "Views") {
            _ = file
            consumers += codeOnly(source)
                .components(separatedBy: "hoverLevel: VisualFill.controlHover").count - 1
        }
        XCTAssertEqual(consumers, 8,
                       "显式抬到控件档的位点从 8 处变成 \(consumers) 处：R15 的三处（侧栏批量按钮、"
                       + "「移除」、回执 ×）+ R20 的四处（行首星标、清除 ×、播放、静音）"
                       + "+ R230 的一处（药丸里的 `GlassPillButton`：它以前不走样式表、自己在 `.compositingGroup()` "
                       + "内部画那一层，同一名义 alpha 实测比共用路径弱 ⇒ 搬进来，第 8 处）。"
                       + "多一处要红（提醒把新位点判一遍），少一处也要红（等于把它退回 6% 那一档）")
    }

    /// 按括号配平取出某个调用的**实参文本**（跨行也算）。
    /// 存在的理由：`pressedStyle` 现在会写成三行，按行扫的判据会把它读成"没表态"。
    static func callArguments(in code: String, named needle: String) -> [String] {
        var results: [String] = []
        var search = code[...]
        while let range = search.range(of: needle) {
            let open = range.upperBound
            var depth = 1
            var cursor = open
            while cursor < code.endIndex, depth > 0 {
                switch code[cursor] {
                case "(": depth += 1
                case ")": depth -= 1
                default: break
                }
                if depth == 0 { break }
                cursor = code.index(after: cursor)
            }
            guard depth == 0 else { break }
            results.append(String(code[open..<cursor]))
            search = code[code.index(after: cursor)...]
        }
        return results
    }

    /// 取出某个具名实参的**整数值**（没有这个实参就返回 nil）。
    ///
    /// 为什么要读值而不是数出现：变异 M88 把清除 × 写成 `labelPadding: 0`，旧写法**全绿通过**
    /// —— 它在数字符串，不在数参数。而 `labelPadding: 0` 的意思就是"没有命中区"，
    /// 恰恰是这条守卫要抓的那件事。与"按名字查消费者会被前缀白拿"同族。
    static func number(after label: String, in arguments: String) -> Int? {
        guard let range = arguments.range(of: label) else { return nil }
        var digits = ""
        for character in arguments[range.upperBound...] {
            if character.isNumber {
                digits.append(character)
            } else if !digits.isEmpty {
                break
            } else if !character.isWhitespace && character != ":" {
                break
            }
        }
        return Int(digits)
    }

    /// `.tertiary` 这一档**只留给非控件的笔画**（R21 / U-43）。
    ///
    /// 触发它的是两处实测：搜索框清除 × 静置 **1.86（亮）/ 2.22（暗）**，
    /// 多文件行那颗展开箭头 **1.88 / 2.27** —— 两者都是"能点的东西"，
    /// 而地板是 `InkFloor.controlInk` = 3.0。同一帧旁边的 `.secondary` 图标是 3.95 / 5.9。
    /// 也就是说 `.tertiary` 从来不是"次要"，它是"**看不见**"。
    ///
    /// 为什么还要一条源码判据（帧探针已经在了）：探针表只能覆盖**量过框的那几处**，
    /// 新加一颗按钮不会碰到任何探针。这条按文件点名 ⇒ 想再往控件上用这一档，
    /// 必须先在这里登记，而登记要写清"它为什么不是可点的东西"。
    /// 与 R20 那条"按文件点名的账本"同一手法：总数只能报"变了"，点名才能报"哪一处"。
    func testTheFaintestInkTierIsReservedForNonControls() throws {
        // R27 之后这本账是**空的**：原来登记在册的三处（热图的月份 / 星期 / 图例）
        // 被重新判了一遍 —— 它们量的数与被 R21 判死的那两颗控件一模一样（1.88 / 2.27），
        // 唯一的区别是"那两颗能点，这三处要读"。要读的标签没有理由比能点的笔画更淡，
        // 于是三处全部提到 `.secondary`（见 D-086）。
        // 留这本空账的意义：**产品里任何一处想用这一档，都必须在这里点名并写清为什么**，
        // 而不是"反正刻度可以"。
        var ledger: [String: Int] = [:]
        for (file, source) in try productSources(in: "Views") {
            let hits = Self.countIdentifiers(named: "tertiary", in: codeOnly(source))
            if let expected = ledger[file] {
                XCTAssertEqual(expected, hits,
                               "\(file) 里 `.tertiary` 从 \(expected) 处变成 \(hits) 处 ⇒ 重新判一遍："
                               + "可点的笔画不许用这一档（实测 1.86–2.27，地板 3.0），"
                               + "非控件的刻度文字要留就留在这里并写清为什么")
                ledger[file] = nil
            } else {
                XCTAssertEqual(hits, 0,
                               "\(file) 出现了 \(hits) 处 `.tertiary` 而账本里没有它 ⇒ "
                               + "控件一律至少 `.secondary`；确实不是控件（纯装饰/刻度文字）"
                               + "才登记进 `testTheFaintestInkTierIsReservedForNonControls` 的账本")
            }
        }
        XCTAssert(ledger.isEmpty, "这些文件里的 `.tertiary` 不见了：\(ledger.keys.sorted())"
                  + " ⇒ 那一档被撤干净了是好事，把账本条目一起删掉，别留一条会自己变红的旧账")
    }

    /// 数**标识符**而不是数字符串：`.tertiary` 不能被 `.tertiaryLabelColor` 白拿一次
    /// （R20 的"按名字查消费者会被前缀白拿"同族）。
    static func countIdentifiers(named name: String, in code: String) -> Int {
        var count = 0
        var search = code[...]
        while let range = search.range(of: name) {
            let before = range.lowerBound > code.startIndex
                ? code[code.index(before: range.lowerBound)] : " "
            let after = range.upperBound < code.endIndex
                ? code[range.upperBound] : " "
            let isWord: (Character) -> Bool = { $0.isLetter || $0.isNumber || $0 == "_" }
            if !isWord(before), !isWord(after) { count += 1 }
            search = code[range.upperBound...]
        }
        return count
    }

    /// 详情区药丸那四颗**只允许有一层悬停底色**（R20 抓到的是叠了两层）。
    ///
    /// `GlassIconControl` 自己在 44pt 的圆上画 `.primary.opacity(controlHover)`，
    /// 而 `pressedStyle` 默认还要再叠一层 `VisualFill.hover`=0.06 ——
    /// 两层相加悬停时约 0.14，**比全仓"控件"那一档高 1.75 倍**，
    /// 而它是这一圈里唯一被画两层的表面。修法：那一处的 `hoverLevel` 必须是 0。
    func testGlassPillPaintsExactlyOneHoverLayer() throws {
        // R20 立的规矩是**一层**，不是"由谁画这一层"。R230 把这一层从药丸内部搬到共用换算上：
        // `GlassIconControl` 原来在 `.compositingGroup()` **内部**自绘 `.fill(.primary.opacity(isHovered ? …))`，
        // 而同一名义 alpha 画在共用的 `PressedLabel` overlay 上实测更亮 —— 亮档自绘版只有 1.175:1
        // （地板 1.20），共用路径 1.220:1（读数在 `HOVER_DIRECT_READ_PROOF`，帧 `glass-pill-hover`）。
        // 所以旧版那两条断言（"药丸自己画一层" + "`pressedStyle` 必须 `hoverLevel: 0`"）**方向整个翻了**：
        // 保留的是"只有一层"这个不变量，两条断言各守一侧 —— 一侧不许回来，另一侧必须在。
        let code = codeOnly(try productSource(named: "Views/GlassControls.swift"))
        XCTAssertFalse(code.contains("isHovered ?"),
                       "药丸文件里又出现了按 `isHovered` 自己算的一层灰 ⇒ 它叠在 `pressedStyle` 那层之上（R20 的 0.14），"
                       + "而且会重新掉进「组内自绘比共用路径弱」这个坑（R230）")
        XCTAssertFalse(code.contains("hoverLayer"),
                       "`hoverLayer` 那个子视图回来了 ⇒ 上面那条 `isHovered ?` 只是换了写法，病没走")
        let calls = Self.callArguments(in: code, named: ".pressedStyle(")
        XCTAssertEqual(calls.count, 1, "药丸文件里的 `pressedStyle` 调用点数量变了，重新判一遍叠层")
        XCTAssertTrue(calls[0].contains("hoverLevel: VisualFill.controlHover"),
                      "药丸那一层现在**只**由 `pressedStyle` 画；这里写成 0 就等于药丸完全没有悬停反馈"
                      + "（两档读数会一起掉到 1.000，`UICaptureTests` 那条直接读数判据会红）")
    }

    /// 只读数值不许说"可点"（R18 · 权重页那一列）。
    ///
    /// 缺陷是**看帧**看出来的：`weights-520x880-dark` 里 9 行因子的数值「默认」字形是
    /// `#007AFF`（与系统强调色逐通道相同），而同一页里真正那颗「恢复默认」按钮是中性白字
    /// `(223,223,223)`。macOS 里蓝色文字 = 链接/可点，于是这一页看起来有 9 个链接，
    /// 点了哪一个都没反应；而唯一能点的那颗反而比它们安静。
    /// 旧版还有第二条错：`>1.0` 涂橙 —— 把说明文字里写着的合法取值（200% = 双倍）画成警示色。
    ///
    /// 这里判的是**决定本身**（真值表）与**接线**（行必须用这个决定，不许自己再算一遍）。
    /// 产物那一侧由 `weights` / `weights-adjusted` 两帧看着：只有一态的梯子等于没有梯子。
    func testReadOnlyWeightValueDoesNotWearTheActionableColor() throws {
        // ① 真值表：文字与色调必须出自同一个四舍五入后的整数百分比。
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 0.0), "0%")
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 0.4), "40%")
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 1.0), "默认")
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 1.6), "160%")
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 2.0), "200%")
        XCTAssertEqual(WeightValuePresentation.tone(value: 0.4), .lowered)
        XCTAssertEqual(WeightValuePresentation.tone(value: 1.0), .atDefault)
        XCTAssertEqual(WeightValuePresentation.tone(value: 1.6), .raised)
        // 边界：0.999 会被四舍五入成 100% ⇒ 文字说「默认」、色调也必须说"没动过"。
        // 这两件事若各算各的，就会出现"写着默认、却按改过的颜色画"。
        XCTAssertEqual(WeightValuePresentation.percent(value: 0.999), 100)
        XCTAssertEqual(WeightValuePresentation.tone(value: 0.999), .atDefault)
        XCTAssertEqual(WeightValuePresentation.percentageText(value: 0.999), "默认")

        // ② 接线：行必须用上面那个决定，而且不许在行里再算一遍百分比。
        //    锚点要先落到**行**上：这个文件里有两个 `var body: some View`
        //    （外层那一页 + 单行），第一轮就是这么读到外层去、于是两条断言一起红
        //    —— 与 R16 的 DetailView 守卫同一族错误（锚点过宽 = 区域形同虚设）。
        let source = codeOnly(try productSource(named: "Views/RecommendationWeightsView.swift"))
        guard let rowStart = source.range(of: "struct WeightSliderRow") else {
            return XCTFail("找不到 WeightSliderRow ⇒ 守卫看不到被守卫的东西时必须红")
        }
        let rowSource = String(source[rowStart.lowerBound...])
        XCTAssertTrue(rowSource.contains("tintColor"), "截取的那一段不是权重行")
        let row = region(in: rowSource, named: "var body: some View")
        XCTAssertTrue(row.contains("Slider(value:"), "区域取的不是权重行的 body")
        XCTAssertTrue(row.contains("WeightValuePresentation.percentageText(value: value)"),
                      "数值文字没走 `WeightValuePresentation` ⇒ 真值表测的就不是产物")
        XCTAssertTrue(row.contains("foregroundStyle(tintColor)"),
                      "颜色通道没接 ⇒ 色调判断只活在测试里")
        XCTAssertFalse(row.contains("rounded()"),
                       "行里自己又算了一遍百分比 ⇒ 文字与颜色可以各自漂")

        // ③ 颜色映射：强调色与橙色都不许出现在这一列上。
        let tint = region(in: rowSource, named: "private var tintColor: Color")
        XCTAssertFalse(tint.contains(".accentColor"),
                       "只读数值又用上强调色了：那是「可点」的语言，而这一格点不动")
        XCTAssertFalse(tint.contains(".orange"),
                       "200% 是合法取值，不该画成警示色")
        XCTAssertTrue(tint.contains(".secondary") && tint.contains(".primary"),
                      "两态必须分开：没动过 = 次级、动过 = 主色")
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

    // MARK: - 表达那一半：三档底色画出来到底看不看得出来

    /// 悬停这一档**如果**被触发，画面上看不看得出来 —— 相邻两档逐一比 × 两种外观 × 控件真实尺寸。
    ///
    /// 为什么单独立这一条：R14 想做"合成 hover 取证"，三条路实测全部走不通
    /// （数据与复现命令记在 `.scratch/motion-audit-2/spike_hover_channel.md`）：
    /// ① `CGEvent(...).post(tap: .cghidEventTap)` 在无辅助功能授权的进程里被窗口服务器丢弃 ——
    ///    连自建的 `NSTrackingArea` 都收不到 `mouseEntered:`（`appkit_enters=0`）；
    /// ② 直接对 `NSHostingView` 调 `mouseEntered(with:)` / `mouseMoved(with:)`：
    ///    SwiftUI 的 hover tracking area 的 owner 就是 hosting view 本身（mask=643，
    ///    含 `mouseEnteredAndExited`），但两个入口都试过，`.onHover` 一次都没回调；
    /// ③ `window.sendEvent(合成的 mouseEntered)` 直接崩在 `+[NSEvent mouseEventWithType:…]` 里。
    ///
    /// 所以这件事被拆成两半分开记账：**触发**那半只能人眼验（批次 22），
    /// **表达**那半可以量 —— 也就是这条。不许因为一半量不了就把整件事写成"没做"，
    /// 也不许反过来把能量到的这半当成"悬停已经验过了"。
    ///
    /// 量的是**控件自己那么大**（图标那颗 22pt：R13 像素 diff 实测侧栏那五颗的 label 包围盒
    /// 46 设备像素 = 23pt；行 44pt），不是"随便一块平面"：同一档 6% 铺在一整行上读得出来、
    /// 铺在 22pt 上读不读得出来，正是这条要回答的（圆角占的面积比例也只有在真实尺寸上才对）。
    func testFillLaddersAreVisibleOnBothControlClasses() throws {
        let ladders = Self.makeLadders()
        for ladder in ladders {
            for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
                let tag = appearance == .darkAqua ? "dark" : "light"
                // 起点是**梯子自己的第一步**，不是"0"。
                // 第一版写死 `level: 0` 再 `dropFirst()`，对行/控件没错（它们第一步就是 idle=0），
                // 但输入框这辈子不是从 0 开始的（静止态就是 `fieldIdle`）——
                // 于是那条梯子量的其实是"idle→fieldActive"，
                // 而 `fieldIdle→fieldActive` 这一步**从来没被比过**：
                // 变异 M66（把两档并成一档）因此**全绿通过**。尺子自己错了。
                let firstStep = ladder.steps[0]
                var previousName = firstStep.0
                var previous = try renderFill(level: firstStep.1, appearance: appearance,
                                              size: ladder.size)
                var previousLevel = firstStep.1
                for (name, level) in ladder.steps.dropFirst() {
                    let current = try renderFill(level: level, appearance: appearance, size: ladder.size)
                    let step = Self.meanChannelDelta(previous, current)
                    // R77：`meanChannelDelta` 被登记成"允许只读三根通道"，登记的理由是"这一族夹具铺实底、
                    // alpha 不会动"。下面这一行把那句理由变成**读数**，而再下面那条断言把它变成**会红的判据**：
                    // 一旦有一档状态只活在透明度上（RGB 读 0 而 alpha 明显在动），豁免自己作废。
                    let alphaStep = Self.meanAlphaDelta(previous, current)
                    // 读数里带上**两档各自的令牌值**：R15 在这里栽过一次 ——
                    // 改了令牌之后读数一模一样，而日志里看不出量的是哪两个数，
                    // 只能靠再跑一遍去猜是不是用了旧二进制。
                    print("FILL_STEP \(ladder.name)/\(tag) \(previousName)(\(String(format: "%.3f", previousLevel)))"
                        + "->\(name)(\(String(format: "%.3f", level))) "
                        + "均值通道差=\(String(format: "%.2f", step))/255 "
                        + "alpha差=\(String(format: "%.2f", alphaStep))/255")
                    XCTAssertFalse(step < Self.perceptibleStep255 && alphaStep > 8.0,
                                   "\(ladder.name)/\(tag)：\(previousName)→\(name) 在亮度那一根上读 "
                                       + "\(String(format: "%.2f", step))/255（低于可辨地板），"
                                       + "而 alpha 那一根读 \(String(format: "%.2f", alphaStep))/255 ⇒ "
                                       + "这一档只活在透明度上，而这条判据的尺子看不见它。"
                                       + "`meanChannelDelta` 的豁免理由（夹具铺实底、alpha 不动）到此作废")
                    XCTAssertGreaterThanOrEqual(step, Self.perceptibleStep255,
                                                "\(ladder.name)/\(tag)：从 \(previousName) 按到 \(name) 画面上只差 "
                                                + "\(String(format: "%.2f", step))/255，低于地板 ⇒ 令牌上是两档、"
                                                + "屏幕上是同一档。要么把这一档拉开，要么承认它不存在并并掉")
                    // 方向也要判：亮色下每一档更暗、暗色下每一档更亮。
                    // 只判"差多少"会放过一档反向的错（比如某档误用 secondary 而不是 primary）。
                    let gotDarker = Self.meanLuma(current) < Self.meanLuma(previous)
                    XCTAssertEqual(gotDarker, appearance == .aqua,
                                   "\(ladder.name)/\(tag)：\(name) 比上一档\(gotDarker ? "更暗" : "更亮")，方向反了")
                    previous = current
                    previousName = name
                    previousLevel = level
                }
            }
        }
    }

    /// 一类控件的**状态序列**（不是四档排成的梯子）。
    ///
    /// 为什么按"同一颗控件依次经过的状态"判，而不是把四档排一排两两比较：
    /// 一行这辈子不会经过 `controlHover`，一颗 22pt 图标也不会经过 `selected` ——
    /// 跨控件比两档差多少，量的是一件不存在的事；
    /// 而"按下这颗图标时，它比悬停时看得出来吗"是**每一次点击都会发生**的事。
    /// （同族：同一个词在两个判据里含义不同，就别统一成一个布尔值。）
    struct Ladder {
        let name: String
        let size: NSSize
        let steps: [(String, Double)]

        var tierNames: Set<String> { Set(steps.map { $0.0 }) }
    }

    /// 三条梯子 = 产品里三族"会换底色"的东西，各自**依次经过**的状态。
    ///
    /// 写成**一个函数**（不是 `static let`）：守卫与判据必须读同一份定义，
    /// 否则"覆盖了哪些档"这句话会有两个答案（这一族记过：同一个词两个判据里含义不同）；
    /// 而它**不能**是静态存储 —— 它的初始化器里有调用（`NSSize(width:height:)`、读令牌），
    /// 那正是 CI 的 Swift 6.1.2 在 `emitLazyGlobalInitializer` 里 SIGSEGV 的那一族（账本 D-069）。
    /// 本机 6.2.1 不复现，所以这条只能靠"根本不建那个全局"来躲。
    ///
    /// `field` 那条是 R15 补的：`fieldIdle 0.035 → fieldActive 0.06` 这一步从来没被量过，
    /// 而它是输入框**唯一**的状态通道（搜索框不会 hover 变色，只会"激活/没激活"）。
    static func makeLadders() -> [Ladder] {
        [
            Ladder(name: "row", size: NSSize(width: 44, height: 44),
               steps: [("idle", 0), ("hover", VisualFill.hover),
                       ("pressed", VisualFill.pressed), ("selected", VisualFill.selected)]),
            // 第二步的名字写**令牌名**（controlHover）而不是状态名（hover）：
            // 同一颗控件的"悬停"用的是另一档，如果两族都叫 hover，
            // 下面那条集合相等守卫就会被白拿（"同一个词在两个判据里含义不同"那一族）。
            Ladder(name: "control", size: NSSize(width: 22, height: 22),
                   steps: [("idle", 0), ("controlHover", VisualFill.controlHover),
                           ("pressed", VisualFill.pressed)]),
            Ladder(name: "field", size: NSSize(width: 280, height: 28),
                   steps: [("fieldIdle", VisualFill.fieldIdle),
                           ("fieldActive", VisualFill.fieldActive)])
        ]
    }

    /// 每个 `VisualFill` 档位都必须出现在某条梯子里 —— 集合相等，多一个少一个都红。
    ///
    /// 这条是 R13→R14 那一课的工程化：R13 抬了一档，只证明了"它比 0 看得出来"，
    /// 没证明"它与相邻那一档还分得开"，于是修好悬停、弄没按压，全绿。
    /// 规矩"改令牌必须跑完整梯子"要成立，就得有人盯着"哪些档根本没进梯子"——
    /// 新加一档而没人量它，正是上一轮那种事故的下一个版本。
    func testEveryVisualFillTierIsCoveredByALadder() throws {
        let source = codeOnly(try productSource(named: "Utilities/VisualTokens.swift"))
        let body = region(in: source, named: "enum VisualFill")
        var declared: Set<String> = []
        for line in body.components(separatedBy: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard trimmed.hasPrefix("static let"), trimmed.contains(": Double") else { continue }
            guard let name = trimmed.components(separatedBy: "static let ").dropFirst().first?
                .components(separatedBy: ":").first?.trimmingCharacters(in: .whitespaces) else { continue }
            declared.insert(name)
        }
        // "idle" 不是令牌，是"什么都没叠"的那个状态；`0` 由 `Color.primary.opacity(0)` 表达。
        let covered = Self.makeLadders().reduce(Set<String>()) { $0.union($1.tierNames) }
            .subtracting(["idle"])
        XCTAssertEqual(declared, covered,
                       "VisualFill 里有档位没进梯子（只声明没被量）或梯子里有档位已被删掉。\n"
                       + "令牌侧: \(declared.sorted())\n梯子侧: \(covered.sorted())\n"
                       + "新加一档 ⇒ 同时加进它所属那一族的梯子，并看它**左右两个邻居**的台阶")
    }

    /// 一块平面底色上"看得出来"的地板（0–255 的均值通道差）。
    ///
    /// 取 4 ≈ 1.6%：大平面上恰可察觉的亮度台阶通常记在 1–3% 之间。取中间偏松的一侧，
    /// 是为了让这条判据抓的是"两档其实是同一档"，不是抓"这一步比那一步小一点"（那是口味）。
    static let perceptibleStep255: Double = 4

    // MARK: - 渲染夹具

    /// 用 SwiftUI 自己画一遍产品的组合：窗口底色 + `Color.primary.opacity(level)` 的控件圆角。
    ///
    /// 刻意走 `NSHostingView` + `cacheDisplay`（与帧夹具同一套机器），而不是在 Core Graphics 里
    /// 手搓一个"长得像"的圆角矩形 —— 后者测的是替身。`level` 由调用方从
    /// `PressableAppearance.fillOpacity(...)` 拿，所以这条判据覆盖的是
    /// **产品真正会画的那一层**，只是绕过了"谁把它翻成非零"那一半。
    private func renderFill(level: Double, appearance: NSAppearance.Name,
                            size renderSize: NSSize = NSSize(width: 22, height: 22),
                            scale: CGFloat = 4) throws -> NSBitmapImageRep {
        // `NSApp` 在这个套件里是 **nil**：它是 `NSApplication.shared` 被访问过之后才被赋的全局，
        // 而本文件其余判据从不碰 AppKit 外观。第一次实测就是 `Fatal error: Unexpectedly
        // found nil while implicitly unwrapping`（信号 5 = 崩溃，不是"没跑"）。
        // 与 `MotionFilmstripTests.recordFrames` 里那句 `_ = NSApplication.shared` 同一个理由。
        let app = NSApplication.shared
        let previousAppearance = app.appearance
        app.appearance = NSAppearance(named: appearance)
        defer { app.appearance = previousAppearance }

        let rep = NSBitmapImageRep(bitmapDataPlanes: nil,
                                   pixelsWide: Int(renderSize.width * scale),
                                   pixelsHigh: Int(renderSize.height * scale),
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 0, bitsPerPixel: 0)!
        rep.size = renderSize
        let root = AnyView(
            ZStack {
                Color(nsColor: .windowBackgroundColor)
                VisualShape.rounded(VisualRadius.control)
                    .fill(Color.primary.opacity(level))
            }
            .frame(width: renderSize.width, height: renderSize.height)
        )
        let host = NSHostingView(rootView: root)
        host.frame = NSRect(origin: .zero, size: renderSize)
        host.appearance = NSAppearance(named: appearance)
        host.cacheDisplay(in: NSRect(origin: .zero, size: renderSize), to: rep)
        return rep
    }

    /// 两张图的均值通道差（0–255）。用**均值**而不是"变化像素占比"：
    /// 一层均匀底色会把 100% 的像素都改变一点点，占比那条轴在这里恒等于 1，没有判别力
    /// （账本里"只用亮度判两态可否分辨是用错轴"的镜像：这里要用台阶，不能用占比）。
    private static func meanChannelDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {
        let width = min(a.pixelsWide, b.pixelsWide)
        let height = min(a.pixelsHigh, b.pixelsHigh)
        guard width > 0, height > 0 else { return 0 }
        var total = 0.0
        for y in 0..<height {
            for x in 0..<width {
                guard let pa = a.colorAt(x: x, y: y), let pb = b.colorAt(x: x, y: y) else { continue }
                total += abs(pa.redComponent - pb.redComponent)
                    + abs(pa.greenComponent - pb.greenComponent)
                    + abs(pa.blueComponent - pb.blueComponent)
            }
        }
        return total / Double(width * height) / 3.0 * 255.0
    }

    /// `meanChannelDelta` 的 alpha 那一根（R77）。
    ///
    /// 为什么要单独一条：`meanChannelDelta` 登记成"允许只读三根通道"，而那条豁免的前提是
    /// "这一族夹具铺的是实底，alpha 不会动"。前提必须**被量**，不能写在注释里 ——
    /// 这一列就是那条前提的读数：哪天出现 `均值通道差=0.00 alpha差=8.00`，
    /// 说明有一档状态只活在透明度上，豁免立刻作废（判据得改）。
    private static func meanAlphaDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {
        let width = min(a.pixelsWide, b.pixelsWide)
        let height = min(a.pixelsHigh, b.pixelsHigh)
        guard width > 0, height > 0 else { return 0 }
        var total = 0.0
        for y in 0..<height {
            for x in 0..<width {
                guard let pa = a.colorAt(x: x, y: y), let pb = b.colorAt(x: x, y: y) else { continue }
                total += abs(pa.alphaComponent - pb.alphaComponent)
            }
        }
        return total / Double(width * height) * 255.0
    }

    private static func meanLuma(_ rep: NSBitmapImageRep) -> Double {
        let width = rep.pixelsWide, height = rep.pixelsHigh
        guard width > 0, height > 0 else { return 0 }
        var total = 0.0
        for y in 0..<height {
            for x in 0..<width {
                guard let p = rep.colorAt(x: x, y: y) else { continue }
                total += 0.299 * p.redComponent + 0.587 * p.greenComponent + 0.114 * p.blueComponent
            }
        }
        return total / Double(width * height) * 255.0
    }

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

    /// 两态相减：RGB 或 alpha 任一通道过地板就算这一像素变了（R77 / BACKLOG 107）。
    ///
    /// alpha 这一路是新加的：夹具 `renderPill` 往 hasAlpha 的位图上画的是
    /// `NSColor(white: 0, alpha: fill)` —— **黑墨按透明度叠**。黑墨在预乘表示里 RGB 恒为 0，
    /// 所以"底色那一档"理论上可以只在 alpha 上动，而旧尺子会读 0 并让
    /// `filledFraction > 0.02` 那条判红成"减弱动态只剩底色 = 空的"（判错产品）。
    /// 这一格今天到底在哪根轴上，由下面那条判据打出来的 `PRESS_AXIS` 说了算，不由注释说。
    ///
    /// 三通道求和那道地板（0.02）原样保留：账本里 `按压缩放/底色` 那几个数是这根尺读的。
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
                let alphaDelta = abs(pa.alphaComponent - pb.alphaComponent)
                if delta > 0.02 || alphaDelta > 0.02 { changed += 1 }
            }
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    /// RGB 那一根单独的变化占比。
    private static func rgbFraction(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {
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

    /// alpha 那一根单独的变化占比。
    private static func alphaFraction(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {
        let width = a.pixelsWide, height = a.pixelsHigh
        guard width == b.pixelsWide, height == b.pixelsHigh else { return 0 }
        var changed = 0
        var total = 0
        for y in stride(from: 0, to: height, by: 2) {
            for x in stride(from: 0, to: width, by: 2) {
                total += 1
                let pa = a.colorAt(x: x, y: y)!, pb = b.colorAt(x: x, y: y)!
                if abs(pa.alphaComponent - pb.alphaComponent) > 0.02 { changed += 1 }
            }
        }
        return total > 0 ? Double(changed) / Double(total) : 0
    }

    /// 三根轴一起打（R77 要求每条两态判据都打这一行）：
    /// 只打并集分不出"这一下动在哪根轴上"，只打两根轴又没人知道判据实际读的是哪个数。
    static func axisLine(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> String {
        func p(_ v: Double) -> String { String(format: "%.4f", v) }
        return "亮度差=\(p(rgbFraction(a, b))) alpha差=\(p(alphaFraction(a, b))) 并集差=\(p(changedFraction(a, b)))"
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
