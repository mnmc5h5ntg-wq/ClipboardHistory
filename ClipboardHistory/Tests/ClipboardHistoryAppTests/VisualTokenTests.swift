import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 视觉令牌（R1）的判据。
///
/// 这一轮的产出是"几何与材质参数只有一个作者"，而**"是作者"这件事只能靠扫描来钉**：
/// 纯值断言只能证明令牌里的数是对的，证明不了视图真的在读它们 —— 上一轮 MC-12 就栽在
/// "表里全对、没人调用"。所以本文件多数判据是源码扫描，且每条都带一个正向对照
/// （检测器必须真的看得见东西），否则把被扫的东西全删掉也会同样"绿"。
///
/// 不覆盖管线：本文件钉的是几何与材质的单一作者，不是交互行为。
/// 状态反馈的管线级判据在 `MotionCatalogTests` / `RowInteractionTests` / `PipelineAcceptanceTests`，
/// 像素级的在 `MotionFilmstripTests`，字号规范本体在 `Round3StateLanguageTests`。
final class VisualTokenTests: XCTestCase {

    // MARK: - 圆角：只有一个出口，而且永远是连续曲率

    /// 视图里不许再自己 `RoundedRectangle(cornerRadius:)`。
    ///
    /// 为什么值得钉：R0 审计数出 6 种圆角（4 / 5 / 6 / 7 / 8 / 9），其中 4pt 的四处还漏了 `style:` ——
    /// 于是同一屏并存两种曲率语言（小方块是"圆弧接直线"，卡片是 squircle）。
    /// 逐个补 `.continuous` 也能解决，但那只是把六个字面量换成六个带参数的字面量，
    /// 下一个人照样能加第七个。
    func testCornersComeFromTheShapeFactory() throws {
        let tokens = codeOnly(try productSource(named: "Utilities/VisualTokens.swift"))
        let factory = tokens.linesMatching("RoundedRectangle(cornerRadius:")
        XCTAssertEqual(factory.count, 1,
                       "圆角出口应当恰好一个（`VisualShape.rounded`），现在 \(factory.count) 个：\(factory)")
        XCTAssertTrue(factory.first?.contains("style: .continuous") == true,
                      "出口自己就没写 `.continuous`：那这条守卫只是在保护一个错的东西")

        var offenders: [String] = []
        for (file, source) in try allProductSources() where file != "VisualTokens.swift" {
            for line in codeOnly(source).linesMatching("RoundedRectangle(cornerRadius:") {
                offenders.append("\(file): \(line.trimmingCharacters(in: .whitespaces))")
            }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "这些视图还在自己构圆角矩形，应该走 `VisualShape.rounded(...)`：\n" + offenders.joined(separator: "\n"))
    }

    /// 令牌的内部一致性：半径的**嵌套次序**必须和视觉层级同向。
    /// 把 chip 抬到比 control 大，编译照过、测试照跑，只是角上开始互相打架。
    func testRadiusTiersAreMonotonic() {
        XCTAssertLessThan(VisualRadius.chip, VisualRadius.control, "16pt 的小方块不该比 24pt 的胶囊更圆")
        XCTAssertLessThan(VisualRadius.control, VisualRadius.card)
        XCTAssertLessThan(VisualRadius.card, VisualRadius.panel, "整块区域的表面该比一颗控件更收")
        XCTAssertEqual(VisualRadius.track, VisualRadius.control + 1,
                       "轨道必须比它容纳的滑块大 1pt：同值时内层的角会切进外层描边里")
    }

    /// 状态强度的次序是**语义**，不是数值巧合：越持久的状态要越显眼。
    func testStateIntensityOrderMatchesStatePersistence() {
        XCTAssertLessThanOrEqual(VisualFill.hover, VisualFill.controlHover,
                                 "44pt 的符号按钮面积只有一小条，底色不能比整行还淡")
        XCTAssertLessThan(VisualFill.hover, VisualFill.selected,
                          "hover 是瞬时态、选中是持久态：瞬时态更显眼时，用户读不出自己到底选了哪一条")
        XCTAssertLessThanOrEqual(VisualFill.fieldIdle, VisualFill.fieldActive,
                                 "输入框激活时应当更实，不是更虚")
        XCTAssertLessThan(VisualTint.fieldIdleStroke, VisualTint.fieldActiveStroke)
    }

    // MARK: - 投影：只有两档，而且分组合成跟着档位走

    /// 视图里不许再自己 `.shadow(color:…)`。
    ///
    /// 这条要防的不是"数值不一致"那么大，而是 R0 抓到的那半件：视频控件写了 8pt/3pt 的投影却漏了
    /// `.compositingGroup()`，于是同一种"浮起的玻璃"在两处给出两个结果 —— 材质是独立图层，
    /// 不分组合成就会给每一层各打一次阴影。把 `groupsFirst` 绑进投影定义本身，
    /// "漏掉那一句"就从"忘了写"变成"编不出来"。
    func testShadowsComeFromTheTokens() throws {
        let tokens = codeOnly(try productSource(named: "Utilities/VisualTokens.swift"))
        let applier = tokens.linesMatching(".shadow(color:")
        XCTAssertEqual(applier.count, 2,
                       "出口里应当只有「分组合成 / 不分组合」两条 `.shadow` 分支，现在 \(applier.count) 条")
        XCTAssertTrue(applier.allSatisfy { $0.contains("edge.") },
                      "出口没读令牌 ⇒ 它保护的只是自己的形状，不是那两个数")

        var offenders: [String] = []
        for (file, source) in try allProductSources() where file != "VisualTokens.swift" {
            for line in codeOnly(source).linesMatching(".shadow(") {
                offenders.append("\(file): \(line.trimmingCharacters(in: .whitespaces))")
            }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "这些视图还在自己打投影，应该走 `.visualShadow(VisualShadow.flat / .raised)`：\n"
                          + offenders.joined(separator: "\n"))
    }

    // MARK: - 线宽

    /// `lineWidth:` 后面只准跟令牌。
    ///
    /// 匹配前先证明"这个词没有撞进别人的名字里"：`static let minimumTimelineWidth: CGFloat = 56`
    /// 含有子串 `lineWidth:`，裸 `contains` 会把一个字段名报成违规（R1 写这条时真撞上过一次）。
    func testLineWidthsComeFromTheTokens() throws {
        var offenders: [String] = []
        var tokenised = 0
        for (file, source) in try allProductSources() where file != "VisualTokens.swift" {
            for line in codeOnly(source).linesMatching("lineWidth:") {
                guard VisualTokenScan.hasStandaloneKeyword("lineWidth", in: line) else { continue }
                if line.contains("VisualHairline.") || line.contains("VisualStroke.") {
                    tokenised += 1
                } else if VisualTokenScan.firstSignificant(after: "lineWidth:", in: line)?.isNumber == true {
                    offenders.append("\(file): \(line.trimmingCharacters(in: .whitespaces))")
                }
            }
        }
        XCTAssertGreaterThanOrEqual(tokenised, 7,
                                    "只有 \(tokenised) 处线宽在读令牌：R1 落地时是 7 处，掉下去说明扫描瞎了")
        XCTAssertTrue(offenders.isEmpty,
                      "这些行的线宽是就地写死的数字：\n" + offenders.joined(separator: "\n"))
    }

    // MARK: - 令牌不许是装饰

    /// 每个令牌都必须被**产品代码**读到。
    ///
    /// 与 `MotionCatalogTests.testEveryCatalogConstantIsRead` 同一族：上一轮 MC-5 删掉的
    /// `emphasisScale` / `slideOffset` 就是"声明了、没人用"，而它看起来完全像在管东西。
    /// 这里刻意只数产品代码：判据自己读某个令牌不算消费者，否则加一条断言就能"救活"一个死令牌。
    func testEveryVisualTokenIsReadByTheProduct() throws {
        let declarations = codeOnly(try productSource(named: "Utilities/VisualTokens.swift"))
        let names = VisualTokenScan.tokenNames(declarations: declarations)
        XCTAssertGreaterThanOrEqual(names.count, 40,
                                    "只认出 \(names.count) 个令牌声明，低于 R3 落地后的 40：解析器或文件锚点坏了")

        let product = try allProductSources()
            .filter { $0.file != "VisualTokens.swift" }
            .map { codeOnly($0.source) }
            .joined(separator: "\n")
        for (family, name) in names {
            XCTAssertTrue(VisualTokenScan.reads(family, name, in: product),
                          "令牌 `\(family).\(name)` 只有声明没有消费者：接上它，或者把它删掉"
                              + "（按族查而不是按名字查：`control` 在两族里都有，按名字会互相白拿）")
        }
    }

    /// 字号只准从刻度里取（R3）。与圆角那条同一族：**"统一"如果没有判据，就只是一句共识**。
    ///
    /// R0 数出来的是 8 个文本字号（9/10/11/12/13/14/15/16）+ 5 个大符号（28/32/36/40/48），
    /// 其中两处是真缺陷而不是"风格分歧"：侧栏的"15 条记录"比区块标题"时间剪史"还大一号
    /// （次要信息盖过了标题），而"固定"徽标是 9pt（2× 下笔画并在一起，状态看不清等于没有状态）。
    func testTextSizesComeFromTheScale() throws {
        var offenders: [String] = []
        var tokenised = 0
        for (file, source) in try productSources(in: "Views") {
            for line in codeOnly(source).components(separatedBy: "\n") {
                guard let range = line.range(of: ".font(.system(size: ") else { continue }
                let rest = line[range.upperBound...]
                if let first = rest.first, first.isNumber {
                    offenders.append("\(file): \(line.trimmingCharacters(in: .whitespaces))")
                } else if rest.hasPrefix("VisualFont.") || rest.hasPrefix("VisualGlyph.")
                    || rest.hasPrefix("StatePresentation.") || rest.hasPrefix("DetailTypography.") {
                    tokenised += 1
                }
            }
        }
        XCTAssertGreaterThanOrEqual(tokenised, 35,
                                    "只有 \(tokenised) 处在读字号刻度：R3 落地时是 35 处，掉了说明扫描瞎了")
        XCTAssertTrue(offenders.isEmpty,
                      "这些行还在就地写字号：\n" + offenders.joined(separator: "\n"))
    }

    /// 字号刻度自身的次序：正文级不许出现"次要信息比标题响"。
    func testTypeScaleIsMonotonicAndNeverBelowTheLegibilityFloor() throws {
        XCTAssertLessThan(VisualFont.meta, VisualFont.row, "11 是次要比行标题更弱")
        XCTAssertLessThan(VisualFont.row, VisualFont.body)
        XCTAssertLessThan(VisualFont.body, VisualFont.title,
                          "标题必须比正文响 —— 侧栏那句计数以前是 15，比 14 的标题还大")
        XCTAssertGreaterThanOrEqual(VisualGlyph.badge, 10,
                                    "10pt 是这个 App 的下限：再小的符号在 2× 下笔画会并在一起")
        XCTAssertLessThan(VisualFont.meta, StatePresentation.messageFontSize,
                          "状态文案是那句话的全部信息，必须比次要字更可读")
        // **按来源判，不按数值判**：变异对照 P4 证明"13 == 13"这条数值断言打不红
        // 把引用换成字面量 13 的改动 —— 而那个改动正是"两处各写一个数、日后各改各的"的起点。
        let tokens = try productSource(named: "Utilities/VisualTokens.swift")
        let bodyLine = tokens.components(separatedBy: "\n")
            .first { $0.contains("static let body:") } ?? ""
        XCTAssertTrue(bodyLine.contains("StatePresentation.messageFontSize"),
                      "正文档必须**引用**规范本体，不许抄一个同样等于 13 的字面量：\(bodyLine.trimmingCharacters(in: .whitespaces))")
    }

    // MARK: - 死表面

    /// `Views/` 里每一个 `struct X: View` 都必须至少有一个构造点。
    ///
    /// 这条是 R1 删掉两个东西之后立的地基：`GlassCircleButton`（产品零调用点，只被一条测试当符号
    /// 夹具养着）和 `HistoryRow`（注释写着"保留给夹具与详情以外的调用点复用"，实测夹具里也没有）。
    /// 死表面不是"多余几行"：它是**下一个施工者会去改、改完还以为自己在管界面**的东西。
    ///
    /// 条数下限独立数过（`grep -c ': View {' Sources/ClipboardHistoryApp/Views/*.swift` 之和 = 39），
    /// 防止识别器一条都没认出来时的假绿。
    func testNoDeadSurfaceInViews() throws {
        let views = try productSources(in: "Views")
        let product = try allProductSources().map { codeOnly($0.source) }.joined(separator: "\n")
        var scanned = 0
        var orphans: [String] = []
        for (file, source) in views {
            for name in codeOnly(source).viewStructNames() {
                scanned += 1
                if !product.contains("\(name)(") {
                    orphans.append("\(file): \(name)")
                }
            }
        }
        XCTAssertGreaterThanOrEqual(scanned, 30,
                                    "只认出 \(scanned) 个视图结构体，低于独立计数的 30：识别器坏了，这条判据没有内容")
        XCTAssertTrue(orphans.isEmpty,
                      "这些视图没有任何构造点（死表面）：\n" + orphans.joined(separator: "\n"))
    }

    // MARK: - 状态文案取自家规范

    /// 详情预览里那三句状态话（加载 / 失败 / 读不到信息）的字号必须取规范。
    ///
    /// R0 抓到的是"规范写着 13，加载那句写 12"。这条不看数值（数值由 `Round3StateLanguageTests` 钉），
    /// 看的是**接线**：12 和 13 都是"看着挺合理"的数，只有"谁提供它"才能区分。
    /// 反向也要查：文件里不许再出现裸的 `size: 12` / `size: 13` 状态字，否则有人把令牌换回字面量时
    /// 条数照样对得上（把 `StatePresentation.messageFontSize` 改成 `13` 就正好是这种漏网）。
    func testStateTextComesFromTheSpecification() throws {
        let preview = codeOnly(try productSource(named: "Views/DetailPreviewViews.swift"))
        XCTAssertEqual(StatePresentation.messageFontSize, 13, "规范本体先要是对的，否则下面的接线没有意义")
        XCTAssertEqual(preview.components(separatedBy: "StatePresentation.messageFontSize").count - 1, 3,
                       "详情预览的三句状态话（加载 / 失败 / 视频信息读不到）应当都取规范字号")
        for forbidden in ["font(.system(size: 12))", "font(.system(size: 13))"] {
            XCTAssertFalse(preview.contains(forbidden),
                           "状态行里又出现就地字号 \(forbidden)：那是「三处对齐」散掉的第一步")
        }
    }

    /// 胶囊里的分隔线只有一个作者。
    ///
    /// 以前它是同一段代码手抄三遍（`Rectangle().fill(.separator).frame(width: 28, height: 1)`），
    /// 于是"改一颗胶囊的呼吸"要记得数清有三处 —— 而没有人会记得。
    func testPillDividersComeFromOnePlace() throws {
        let glass = codeOnly(try productSource(named: "Views/GlassControls.swift"))
        XCTAssertEqual(glass.components(separatedBy: "GlassPillDivider()").count - 1, 3,
                       "四颗按钮之间应当恰好 3 条分隔线")
        XCTAssertEqual(glass.linesMatching("height: VisualHairline.divider").count, 1,
                       "分隔线的粗细不该有第二个作者")
        XCTAssertEqual(glass.components(separatedBy: "Rectangle()").count - 1, 1,
                       "有人又开始就地画分隔线本体了：它应该只在 `GlassPillDivider` 里出现一次")
    }

    // MARK: - 扫描器自证

    /// 上面那几条 `contains` 之所以可信，全靠这条。
    /// `minimumTimelineWidth: CGFloat = 56` 与 `lineWidth:` 撞子串是 R1 真踩过的坑。
    func testScanHelpersDoNotFallForSubstringCollisions() {
        XCTAssertFalse(
            VisualTokenScan.hasStandaloneKeyword("lineWidth", in: "static let minimumTimelineWidth: CGFloat = 56"),
            "把字段名当成了线宽：那这条守卫会把不相关的行报成违规")
        XCTAssertTrue(VisualTokenScan.hasStandaloneKeyword("lineWidth", in: ".stroke(color, lineWidth: 0.5)"))
        XCTAssertTrue(VisualTokenScan.hasStandaloneKeyword("lineWidth", in: "lineWidth: VisualHairline.edge"),
                      "行首也算独立词：否则扫描会漏掉以它开头的那一行")

        XCTAssertEqual(VisualTokenScan.firstSignificant(after: "lineWidth:", in: "lineWidth: 0.5"), "0")
        XCTAssertEqual(VisualTokenScan.firstSignificant(after: "lineWidth:", in: "lineWidth: VisualHairline.edge"), "V")
        XCTAssertNil(VisualTokenScan.firstSignificant(after: "lineWidth:", in: "no match here"))

        XCTAssertTrue(VisualTokenScan.reads("VisualFill", "hover", in: "x VisualFill.hover y"))
        XCTAssertFalse(VisualTokenScan.reads("VisualFill", "control", in: "x VisualFill.controlHover y"),
                       "前缀命中不算读取：这条边界就是变异 P3 漏掉的那个洞")
        XCTAssertTrue(VisualTokenScan.reads("VisualFill", "control", in: "x VisualFill.control y"),
                       "加了边界之后不许把真读取也漏掉（那会让守卫只会报绿）")
        XCTAssertTrue(VisualTokenScan.reads("VisualFont", "body", in: "结尾就是 VisualFont.body"),
                       "出现在行尾也要认得")

        XCTAssertEqual(
            VisualTokenScan.tokenNames(declarations: """
            enum VisualRadius {
            static let chip: CGFloat = 4
            static var raised = Edge(color: .black)
            // static let commented: CGFloat = 1
            let instance: CGFloat = 2
            }
            enum VisualGlyph {
            static let chipSymbol: CGFloat = 11
            }
            """).map { "\($0.family).\($0.name)" },
            ["VisualRadius.chip", "VisualGlyph.chipSymbol"],
            "只认非注释的 `static let`，并且要连族一起认：var / 实例常量 / 注释都不算")

        XCTAssertEqual(
            "private struct GlassBorder<S: InsettableShape>: View {\nstruct HistoryRowButton: View {\nstruct NotAView: ViewModifier {".viewStructNames(),
            ["GlassBorder", "HistoryRowButton"],
            "泛型视图要认得（`<…>` 那一截得剥掉），非 View 的 struct 不许认")
    }

    // MARK: - 夹具

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        let found = try productSources(in: directory).first { $0.file == name }
        return try XCTUnwrap(found?.source, "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红")
    }

    private func productSources(in directory: String) throws -> [(file: String, source: String)] {
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
        throw NSError(domain: "VisualTokenTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(directory)：守卫找不到被守卫的东西时必须红"])
    }

    /// 产品源码的**全部**目录，包括 target 根目录那层（`App.swift` 在那里）。
    ///
    /// 这条差点造成一次假红：`ContentView` 与 `MenuBarRecommendationsView` 只在 `App.swift` 里
    /// 构造，第一次扫描没把根目录算进来，于是两个活视图被报成死表面。
    /// 反过来也成立：漏一个目录就会漏一类构造点。所以扫描集合本身也要被证伪 ——
    /// 见 `testNoDeadSurfaceInViews` 里那条"必须扫到 App.swift"。
    private func allProductSources() throws -> [(file: String, source: String)] {
        var out: [(file: String, source: String)] = []
        for directory in ["", "Views", "Utilities", "Managers", "Intelligence", "Models"] {
            out += try productSources(in: directory)
        }
        XCTAssertTrue(out.contains { $0.file == "App.swift" },
                      "扫描集合里没有 App.swift：根目录没被算进来，所有'谁构造了它'的判据都不可信")
        return out
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }
}

/// 扫描辅助。放在类外是为了能被那条自证用例单独钉住 ——
/// 这些细节（标识符边界、取第一个有效字符）正是最容易写错的地方。
enum VisualTokenScan {
    /// 这一行里 `keyword` 是否是一个**独立标识符**，而不是别人名字的一段。
    /// 只看第一次出现：本仓库的用法是一行一处，写成全量扫描反而会把"同行两处"的
    /// 假想情况当成需求（而它没有判据）。
    static func hasStandaloneKeyword(_ keyword: String, in line: String) -> Bool {
        guard let range = line.range(of: keyword) else { return false }
        guard range.lowerBound > line.startIndex else { return true }
        let previous = line[line.index(before: range.lowerBound)]
        return !(previous.isLetter || previous.isNumber)
    }

    /// `keyword:` 之后第一个非空白字符。用来区分 `lineWidth: 0.5`（违规）与
    /// `lineWidth: VisualHairline.edge`（合规）。
    static func firstSignificant(after keyword: String, in line: String) -> Character? {
        guard let range = line.range(of: keyword) else { return nil }
        for character in line[range.upperBound...] where character != " " && character != "\t" {
            return character
        }
        return nil
    }

    /// `text` 里是否真的读了 `Family.name` —— **带标识符边界**。
    ///
    /// 为什么不能直接 `contains("\(family).\(name)")`：变异对照 P3 就是这么漏的 ——
    /// 往 `VisualFill` 里塞一个没人读的 `control`，守卫照样绿，
    /// 因为 `VisualFill.controlHover` 里含 `VisualFill.control` 这个前缀。
    /// 名字必须是**整段**才算一次读取。
    static func reads(_ family: String, _ name: String, in text: String) -> Bool {
        let needle = family + "." + name
        var search = text.startIndex
        while let range = text.range(of: needle, range: search..<text.endIndex) {
            let next = range.upperBound
            if next == text.endIndex || !text[next].isLetter { return true }
            search = text.index(after: range.lowerBound)
        }
        return false
    }

    /// `static let NAME: Type = …` 里的名字，**连同它所在的族**。
    ///
    /// 族必须一起认：`control` 在 `VisualRadius` 与 `VisualGlyph` 里都有，
    /// 只按名字查"有没有人读"会让其中一族白拿另一族的消费者（R3 实测就是这样漏掉一处）。
    static func tokenNames(declarations: String) -> [(family: String, name: String)] {
        var family = ""
        return declarations.components(separatedBy: "\n").compactMap { rawLine in
            let line = rawLine.trimmingCharacters(in: .whitespaces)
            if line.hasPrefix("enum ") {
                family = line.dropFirst(5).components(separatedBy: " ").first?
                    .replacingOccurrences(of: "{", with: "") ?? ""
                return nil
            }
            let parts = line.split(separator: " ", omittingEmptySubsequences: true)
            guard parts.count >= 3, parts[0] == "static", parts[1] == "let" else { return nil }
            let name = String(parts[2].split(separator: ":").first ?? "")
            guard !name.isEmpty, !family.isEmpty else { return nil }
            return (family, name)
        }
    }
}

private extension String {
    /// 含 `needle` 的行（注释行由调用方先用 `codeOnly` 滤掉）。
    func linesMatching(_ needle: String) -> [String] {
        components(separatedBy: "\n").filter { $0.contains(needle) }
    }

    /// 本文件里声明的视图结构体名字，含泛型形式与 `private` / `fileprivate` 前缀。
    func viewStructNames() -> [String] {
        components(separatedBy: "\n").compactMap { rawLine in
            let line = rawLine.trimmingCharacters(in: .whitespaces)
            guard line.contains("struct "), line.hasSuffix(": View {") else { return nil }
            guard let afterStruct = line.components(separatedBy: "struct ").dropFirst().first else { return nil }
            let name = afterStruct.trimmingCharacters(in: .whitespaces)
                .components(separatedBy: "<").first?
                .components(separatedBy: ":").first ?? ""
            return name.isEmpty ? nil : name
        }
    }
}
