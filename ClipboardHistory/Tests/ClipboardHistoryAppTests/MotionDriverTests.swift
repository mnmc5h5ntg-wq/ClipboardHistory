import XCTest
import SwiftUI
@testable import ClipboardHistoryApp

/// R6：**驱动那一侧**的判据（R5 那条 A6 的镜像）。
///
/// 第五轮修的是"声明了过渡却没有供电"（挂在 `Spacer()` 上、挂在没有 `.animation` 的 `body` 上）。
/// 这一轮钉相反的那一半：**挂了 `.animation(value:)`，而那个键永远不变**。
/// 两者是同一族缺陷的两个方向，而第二个更阴 —— 它连"这里写了过渡"这句话都不留给你，
/// 读代码的人只看到"动画已接"，屏幕上却一帧都不演。
///
/// 本文件不覆盖管线：这些是**源码级**判据（扫产品源码里的形状）。
/// 管线级判据是同文件里那两条走 `HistoryStore` 的（`testClearHistoryReceiptCountsTheRealRemoval`）
/// 与动效胶片套件（`MotionFilmstripTests`，按像素判"到底演没演"）。
@MainActor
final class MotionDriverTests: XCTestCase {

    // MARK: - 恒假的动画键

    /// `Views/` 一族里不许有 `.animation(_:value:)` 的键是**字面量**。
    /// 字面量键 = 这条动画永远不会被触发 = 一行不会执行的声明（与 A6 同族）。
    func testNoConstantAnimationKeysAcrossViews() throws {
        var offenders: [String] = []
        for entry in try productViewSources() {
            let code = Self.stripCommentLines(entry.source)
            for key in Self.animationKeys(in: code) where Self.isConstantKey(key) {
                offenders.append("\(entry.file)：.animation 的键是常量「\(key)」⇒ 这条动画永远不会被触发")
            }
        }
        XCTAssertTrue(offenders.isEmpty, offenders.joined(separator: "\n"))
    }

    /// 上面那条扫描器的真值表：抓得住恒假键，也不把合法写法误报。
    /// 不门控、不开窗口 ⇒ CI 每轮都跑（R5 那一课的延续：**能被打红的东西才叫判据**）。
    func testAnimationKeyScanIsATruthTable() {
        // ① 字面量键 ⇒ 必须抓到（三种写法各来一次）。
        XCTAssertEqual(Self.animationKeys(in: "view.animation(.easeInOut, value: true)"), ["true"])
        XCTAssertEqual(Self.animationKeys(in: "view.animation(.spring(), value: 0)"), ["0"])
        XCTAssertEqual(Self.animationKeys(in: "view.animation(a, value: \"x\")"), ["\"x\""])
        XCTAssertTrue(Self.isConstantKey("true"))
        XCTAssertTrue(Self.isConstantKey(" 0.2 "), "数字字面量算常量")
        XCTAssertTrue(Self.isConstantKey(""), "没有键 ⇒ 也算恒假")

        // ② 合法写法不许误报：比较表达式、状态属性、可选布尔。
        XCTAssertEqual(Self.animationKeys(in: "v.animation(a, value: store.filteredEntries.isEmpty)"),
                       ["store.filteredEntries.isEmpty"])
        XCTAssertFalse(Self.isConstantKey("clearReceipt == nil"))
        XCTAssertFalse(Self.isConstantKey("previewStage"))
        XCTAssertFalse(Self.isConstantKey("historyStore.selectedEntry == nil"))

        // ③ 跨行写法必须能找到（本仓库的写法就是换行的，找不到等于判据空转）。
        let multiline = """
        someView
            .animation(MotionCatalog.animation(for: .contentFade),
                       value: isDropTargeted)
        """
        XCTAssertEqual(Self.animationKeys(in: multiline), ["isDropTargeted"])

        // ④ 嵌套括号不许把调用截断：`animation(MotionCatalog.animation(for: .x))` 里还有一层括号。
        let nested = "v.animation(MotionCatalog.animation(for: .hover, reduceMotion: false), value: isHovered)"
        XCTAssertEqual(Self.animationKeys(in: nested), ["isHovered"])

        // ⑤ 没有 `value:` 的 `.animation` 不产出键（那是另一族：隐式动画，本条不判）。
        XCTAssertTrue(Self.animationKeys(in: "v.animation(.default)").isEmpty)
    }

    // MARK: - 驱动的**有无**（R42 / BACKLOG 53）

    /// 产品里每一个 `ReceiptLine` 调用点的**门控条件**（"谁决定这条回执出现/消失"）。
    ///
    /// 写成名单而不是"找到几个判几个"，因为这一族要**两个方向都会红**：
    /// 外面新冒出一个没登记的调用点会红（它可能根本没有驱动），
    /// 名单里某个调用点消失了也会红（有人删了回执却忘了删这条账）。
    static let receiptDriveExpectations: Set<String> = [
        "let exclusionReceipt", "let message = exportMessage", "let archiveMessage",
    ]

    /// **`ReceiptLine` 自己挂着 `.transition(.contentFade)`，而 SwiftUI 的过渡只有在外层
    /// 事务被动画化时才演** —— 所以"这里写了过渡"这句话本身不构成任何承诺。
    ///
    /// 这一条是 R42 复核 BACKLOG 53 量出来的，而复核把原账**改窄了**：
    /// 原账写"SettingsView 全文 0 个 `withAnimation` ⇒ 回执瞬间插入瞬间消失"，
    /// 那是按关键字数的，而这一族真正该问的是"这个调用点外面有没有一条 `.animation(value:)`"。
    /// 逐点看到的形状是（行号是修前的）：
    /// - `:659` 清空回执：键 `clearReceipt == nil` ⇒ **有驱动**（而且它不是 `ReceiptLine`，是自己写的 HStack）；
    /// - `:489` 排除名单：键**只有** `excludedBundleIDsRaw` ⇒ 名单真变了才演，
    ///   而"重复添加 / 输入不合法"这两种情况下名单没变，回执仍然是**瞬间弹出来**的；
    /// - `:555` 导出反馈、`:619` 导出/导入历史：**父容器一条 `.animation` 都没有** ⇒ 那两句 `.transition` 是死的。
    ///
    /// 判据不许只判"文件里有 `.animation`"（那会被同一个文件里另一处的驱动白拿），
    /// 也不许拿子串当命中（`exportMessage` 能被 `exportMessageDraft` 冒充）—— 见真值表第 ④ 格。
    func testEveryReceiptLineCallSiteIsDriven() throws {
        let source = try productSource(named: "Views/SettingsView.swift")
        let code = Self.stripCommentLines(source)

        let gates = Self.receiptGateConditions(in: code)
        // 两边都排好序再比：`Set` 的打印顺序**每次进程都可能不同**，而这条断言的失败消息
        // 同时是变异电池的 needle 来源 —— 拿一个顺序不稳定的字符串当 needle，
        // 电池就会"红得不对"（R42 实测：M198 第一版就是这么判失败的）。
        XCTAssertEqual(gates.sorted(), Self.receiptDriveExpectations.sorted(),
                       "ReceiptLine 调用点的门控名单和产品不一致（实际读到 \(gates.sorted())）"
                       + " ⇒ 要么新加了一个没登记的调用点（它可能根本没有驱动），"
                       + "要么有人删了某条回执却忘了删这条账")

        let keys = Self.animationKeys(in: code)
        var undriven: [String] = []
        for gate in gates where !Self.receiptGateIsDriven(gate, by: keys) {
            undriven.append(gate)
        }
        XCTAssertTrue(undriven.isEmpty,
                      "这些回执的门控状态没出现在任何一条 .animation 的键里：\(undriven.sorted())"
                      + " ⇒ `ReceiptLine` 里那句 `.transition(.contentFade)` 是**死的**，"
                      + "用户看到的是瞬间插入、瞬间消失。要么供电，要么把那句声明撤掉"
                      + "（挂一臂不存在的过渡比不挂更坏：读代码的人会以为这里已经动了）")
        print("RECEIPT_DRIVE 调用点 \(gates.count) 个，无驱动 \(undriven.count) 个，键总数=\(keys.count)")
    }

    /// 上面那两条尺自己的真值表（不门控、不开窗口 ⇒ CI 每轮都跑）。
    func testReceiptGateScanIsATruthTable() {
        // ① `if let 局部 = 状态 {` ⇒ 门控里认的是**状态**；局部名当键是**假驱动**。
        XCTAssertEqual(Self.receiptGateConditions(in: """
            if let message = exportMessage {
                ReceiptLine(text: message) { self.exportMessage = nil }
            }
            """), ["let message = exportMessage"])
        XCTAssertFalse(Self.receiptGateIsDriven("let message = exportMessage", by: ["value: message == nil"]),
                       "`message` 是解包出来的局部常量，它变了不代表回执出现 —— 认它等于认一个恒真的键")
        XCTAssertTrue(Self.receiptGateIsDriven("let message = exportMessage",
                                              by: ["value: exportMessage == nil"]))

        // ② `if let 状态 {`（Swift 的缩写写法）。
        XCTAssertEqual(Self.receiptGateConditions(in: """
            if let archiveMessage {
                ReceiptLine(text: archiveMessage) { self.archiveMessage = nil }
            }
            """), ["let archiveMessage"])

        // ③ 非 `let` 的门控（一个布尔状态）也要认得出来 —— 只认 `if let` 的扫描器会**看不见**这一类调用点，
        //    于是"新加了一条没驱动的回执"能安静通过。
        XCTAssertEqual(Self.receiptGateConditions(in: """
            if showExportAlert {
                ReceiptLine(text: "x") {}
            }
            """), ["showExportAlert"])

        // ④ 调用点上面没有 `if` ⇒ 抠不出来，于是它不进名单；主判据会因为"名单两边不等"而红，
        //    而不是安静地少判一个。
        XCTAssertTrue(Self.receiptGateConditions(in: "ReceiptLine(text: whatever) {}").isEmpty)

        // ⑤ 标识符边界：前缀不许冒充。`exportMessageDraft` 含 `exportMessage` 这串字符，
        //    但它不是那个状态 —— 拿 `contains` 判会恒绿。
        XCTAssertTrue(Self.mentions("value: exportMessage == nil", identifier: "exportMessage"))
        XCTAssertFalse(Self.mentions("value: exportMessageDraft == nil", identifier: "exportMessage"),
                       "前缀命中不算驱动 ⇒ 这一格挡的是'名字像但推不动'")
        XCTAssertTrue(Self.mentions("value: (excludedBundleIDsRaw, exclusionReceipt == nil)",
                                    identifier: "exclusionReceipt"),
                      "复合表达式里的成员必须认得出来 —— 产品**没有**这么写（Swift 的元组不 conform "
                      + "Equatable，那样写直接编不过），这一格判的是扫描器对复合写法的耐受性")

        // ⑥ 键里换了**别的**状态（编译得过、读起来也像"这里接了动画"）必须判成没驱动。
        XCTAssertFalse(Self.receiptGateIsDriven("let archiveMessage",
                                               by: ["value: exclusionReceipt == nil"]),
                       "同一文件里另一处的驱动不许被白拿：那推的是别的回执")
    }

    // MARK: - 清空历史那条回执（管线级）

    /// 回执里的数字必须等于**真的被删掉的那些**。
    ///
    /// 从产品入口进（AGENTS.md 定义 of done 第 1 条）：建一个真 `HistoryStore`，
    /// 用真 `add` / `perform(.toggleFavorite)` 摆出"2 条收藏 + 3 条未收藏"，
    /// 按**控制器用的同一条表达式**取回执，再 `perform(.clear)`，
    /// 然后拿回执里的数字与 Store 的真实剩余去对。
    /// 这条同时钉住两件事：数字对不对，以及"先数再清"那个顺序（顺序错了回执会说 0 条）。
    func testClearHistoryReceiptCountsTheRealRemoval() throws {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 10, maxAgeDays: nil)
        )
        for text in ["a", "b", "c", "d", "e"] { store.add(intakeEntry(text: text)) }
        XCTAssertEqual(store.entries.count, 5)
        for entry in store.entries.prefix(2) { store.perform(.toggleFavorite(entry)) }

        // 与 `SettingsWindowController` 里那一行**同一个表达式**：先数，再清。
        let receipt = ClearHistoryReceiptPolicy.receipt(isFavorites: store.entries.map(\.isFavorite))
        store.perform(.clear)

        XCTAssertTrue(receipt.contains("已清空 3 条"), "回执：\(receipt)")
        XCTAssertTrue(receipt.contains("2 条收藏保留"), "回执：\(receipt)")
        XCTAssertEqual(store.entries.count, 2, "回执说清了 3 条，Store 里却还剩 \(store.entries.count) 条")
        XCTAssertTrue(store.entries.allSatisfy(\.isFavorite), "「清空未收藏」不许动收藏")
    }

    /// 一条不可撤销的删除之后，"什么都没发生"是最坏的回执。
    func testClearHistoryReceiptNeverSilentEvenWithNothingToRemove() {
        XCTAssertEqual(ClearHistoryReceiptPolicy.receipt(isFavorites: []),
                       "没有可清空的记录（0 条收藏保留）。")
        XCTAssertEqual(ClearHistoryReceiptPolicy.receipt(isFavorites: [true, true]),
                       "没有可清空的记录（2 条收藏保留）。")
        XCTAssertEqual(ClearHistoryReceiptPolicy.tally(isFavorites: [false, false, true]).removed, 2)
    }

    /// "先数再清"这个顺序是这条回执的全部价值，所以它必须**会红**。
    /// 上一轮教训（R3/R4：值断言证明不了来源）：这里不比对文案，比对**两行代码的先后**。
    func testReceiptIsComputedBeforeTheStoreIsCleared() throws {
        let controller = try productSource(named: "Managers/SettingsWindowController.swift")
        let receiptAt = try XCTUnwrap(controller.range(of: "ClearHistoryReceiptPolicy.receipt"),
                                      "清空回执不再走 ClearHistoryReceiptPolicy：文案有两个作者了")
        let clearAt = try XCTUnwrap(controller.range(of: "store.perform(.clear)"),
                                    "找不到 perform(.clear)：锚点失效")
        XCTAssertLessThan(controller.distance(from: controller.startIndex, to: receiptAt.lowerBound),
                          controller.distance(from: controller.startIndex, to: clearAt.lowerBound),
                          "回执改成在 perform(.clear) **之后**数 ⇒ 永远报 0 条")
    }

    /// 回执必须**渲染在按钮旁边**并且淡入（R6 / 审计 B-P1-2 的那半条）。
    func testClearReceiptIsRenderedAndFaded() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("clearReceipt = clearHistoryAction?()"),
                      "清空按钮的结果没有落到界面上（回执被丢掉了）")
        XCTAssertTrue(settings.contains("value: clearReceipt == nil"),
                      "回执没有淡入驱动：它突然出现，用户不知道是哪一下带来的")
        XCTAssertTrue(settings.contains("clearHistoryAction: (() -> String?)?"),
                      "clearHistoryAction 又变回 () -> Void：那条链路只能「做」，不能说结果")
        XCTAssertTrue(settings.contains("VoiceOverReceipt.announce(clearReceipt)"),
                      "清空回执只剩视觉表达：看不见屏幕的人按完一次不可撤销的删除之后，什么都收不到")
    }

    // MARK: - 详情预览三态（R6 / 审计 B-P1-1）

    /// 加载 / 成功 / 失败三态都要有过渡声明，并且有**一个**按阶段的驱动。
    func testPreviewStagesAreFed() throws {
        let preview = codeOnly(try productSource(named: "Views/DetailPreviewViews.swift"))
        let body = try XCTUnwrap(preview.components(separatedBy: "private var previewStage").first,
                                 "找不到 previewStage：那条按值动画的键没了")
        XCTAssertEqual(body.components(separatedBy: "\n")
            .filter { $0.contains(".transition(MotionCatalog.transition(for:") }.count, 3,
                       "三态里有人没有过渡声明 ⇒ 那一态是硬换")
        XCTAssertTrue(preview.contains("value: previewStage"),
                      "三态切换没有驱动（或者驱动换成了别的键）")
        // 键必须是**阶段**而不是整值：`FilePreview` 不是 Equatable，也不该整值比较。
        let stage = try XCTUnwrap(preview.components(separatedBy: "private var previewStage").dropFirst().first)
            .components(separatedBy: "}").first ?? ""
        XCTAssertEqual(Set(["0", "1", "2"]).subtracting(Self.returnedInts(stage)), [],
                       "previewStage 少了一档：\(stage)")
    }

    // MARK: - 展开箭头（R6 / 审计 B-P2）

    /// 箭头不许换符号名字，必须转 —— 而且挂在**同一条**揭示曲线上。
    func testChevronRotatesInsteadOfSwappingSymbolNames() throws {
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertFalse(detail.contains("\"chevron.down\""),
                       "箭头又回到换名字：那是一帧硬换，而旁边的内容正在用 0.22s 展开，两者对不上")
        XCTAssertTrue(detail.contains("rotationEffect(.degrees(isExpanded ? 90 : 0))"),
                      "箭头没有旋转表达")
        XCTAssertTrue(detail.contains(".animation(MultiFilePreviewLayout.animation, value: isExpanded)"),
                      "箭头的动画不是揭示那一条 ⇒ 又会各走各的")
    }

    // MARK: - 派生键（R44 / BACKLOG 64）

    /// `ContentView` 那五条 `NoticeBanner` 的驱动**不是**五个状态，而是一条派生键：
    /// `:32` 的 `.animation(bannerIn, value: noticeSignature)`，
    /// 而 `noticeSignature`（`:36-44`）把五条的存在性压成一个 bitmask。
    /// ⇒ 上一轮那把"按名字匹配"的尺如果直接推广过去，会把**五条全部误报成没电**——
    /// 而它们确实是有的电的（R22 用像素量过插入位移）。所以推广之前先补这一跳：
    /// **键里出现的名字如果在同一个文件里有 computed property 定义，就把它 body 里点到的状态并进来**。
    ///
    /// 只展开一跳，且**只增不减**：展开失败不会让判据变绿，只会退回按名字匹配那条路。
    /// 这一条是刻意的 —— 一个会"因为读不懂而放行"的守卫比一个会"读不懂而红"的更难查。
    static func drivingStates(for keys: [String], in source: String) -> Set<String> {
        var states: Set<String> = []
        for key in keys {
            let names = identifiers(in: key)
            states.formUnion(names)
            for name in names where !name.contains(".") {
                // 只有裸名字才去找定义：`store.foo` 这种带点的不是本文件的计算属性。
                if let body = computedPropertyBody(name, in: source) {
                    states.formUnion(identifiers(in: body))
                }
            }
        }
        return states
    }

    /// `var <name>` 后面那对大括号里的内容（配平，跨行）。找不到返回 nil。
    static func computedPropertyBody(_ name: String, in source: String) -> String? {
        for needle in ["var \(name):", "var \(name) :"] {
            guard let found = source.range(of: needle) else { continue }
            guard let brace = source.range(of: "{", range: found.upperBound..<source.endIndex) else { continue }
            var index = brace.upperBound
            var depth = 1
            var body = ""
            while index < source.endIndex {
                let character = source[index]
                if character == "{" { depth += 1 }
                else if character == "}" {
                    depth -= 1
                    if depth == 0 { return body }
                }
                body.append(character)
                index = source.index(after: index)
            }
        }
        return nil
    }

    /// 一段表达式里的**标识符**：整串点路径与它的最后一段都算
    /// （键里写 `historyStore.transferNotice`，门控里可能只写 `transferNotice`，两边要能对上）。
    static func identifiers(in expression: String) -> Set<String> {
        var found: Set<String> = []
        var current = ""
        for character in expression + " " {
            if character.isLetter || character.isNumber || character == "_" || character == "." {
                current.append(character)
            } else {
                flushIdentifier(current, into: &found)
                current = ""
            }
        }
        return found
    }

    private static func flushIdentifier(_ token: String, into found: inout Set<String>) {
        var name = token
        while name.hasSuffix(".") { name.removeLast() }
        guard !name.isEmpty else { return }
        let keywords: Set<String> = ["true", "false", "nil", "and", "or", "Int", "String", "Bool", "var", "let", "return"]
        guard !keywords.contains(name), !name.allSatisfy(\.isNumber) else { return }
        found.insert(name)
        if let last = name.split(separator: ".").last, last != Substring(name) {
            found.insert(String(last))
        }
    }

    /// 门控有没有被某条驱动推动（**展开派生键**之后的版本）。
    static func receiptGateIsDriven(_ gate: String, by keys: [String], in source: String) -> Bool {
        let states = drivingStates(for: keys, in: source)
        return gateStateNames(gate).contains { states.contains($0) }
    }

    /// 上面那把尺自己的真值表：派生键必须被展开，而**读不懂时不许安静放行**。
    func testDerivedKeyExpansionIsATruthTable() throws {
        let bannerFile = """
        var body: some View {
            notices
                .animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)
        }
        private var noticeSignature: Int {
            var bits = 0
            if historyStore.transferNotice != nil { bits |= 2 }
            if historyStore.pasteFailureNotice != nil { bits |= 8 }
            return bits
        }
        """
        // ① 派生键展开之后，门控里的状态名（含点路径的**最后一段**）必须认得出来。
        let keys = Self.animationKeys(in: bannerFile)
        XCTAssertEqual(keys, ["noticeSignature"], "先确认键抠对了，否则下面几格是在比空气")
        XCTAssertTrue(Self.receiptGateIsDriven("let transfer = historyStore.transferNotice",
                                              by: keys, in: bannerFile),
                      "派生键没展开 ⇒ 五条真有电的横幅会被误报成没电（BACKLOG 64 的原始动机）")
        XCTAssertTrue(Self.receiptGateIsDriven("let pasteFailure = historyStore.pasteFailureNotice",
                                              by: keys, in: bannerFile))

        // ② 没被签名读到的那条状态，**仍然**算没电 —— 展开不是"把所有东西都放行"。
        XCTAssertFalse(Self.receiptGateIsDriven("let dropped = historyStore.droppedFilesNotice",
                                               by: keys, in: bannerFile),
                       "签名里没点它 ⇒ 它进出都不会触发这条动画，这正是该红的形状")

        // ③ 读不懂（键指向一个本文件里不存在的属性）⇒ 退回按名字匹配，**不**变成恒绿。
        XCTAssertFalse(Self.receiptGateIsDriven("let x = someState", by: ["ghostKey"], in: bannerFile),
                       "找不到定义时如果放行，这条守卫就成了免检牌")

        // ④ 直接状态（R42 那一族）不许被展开逻辑弄坏。
        XCTAssertTrue(Self.receiptGateIsDriven("let archiveMessage",
                                              by: ["archiveMessage == nil"], in: bannerFile))

        // ⑤ 带点的键表达式不会被误当成"本文件的计算属性"去查定义；
        //    展开只到"最后一段"，不拆出前缀（`store` 单独出现在状态集合里没有意义）。
        XCTAssertEqual(Self.drivingStates(for: ["store.foo == nil"], in: bannerFile),
                       Set(["store.foo", "foo"]))
        print("DERIVED_KEY_EXPANSION 五格：展开认最后一段 / 没点到的仍算没电 / 读不懂不放行")
    }

    /// 推广：`NoticeBanner` 那五个调用点，每个都必须被某条驱动**真的**推到。
    ///
    /// 这一条是 R42 那把尺换到第二个组件上跑 —— 而它同时是 BACKLOG 64 的验收：
    /// 如果派生键展开没做，这一条会**五条全红**（假阳性），所以它自己就是那件事的正对照。
    func testNoticeBannerCallSitesArePoweredByTheirDerivedKey() throws {
        let source = try productSource(named: "Views/ContentView.swift")
        let code = Self.stripCommentLines(source)
        let gates = Self.receiptGateConditions(in: code, callSite: "NoticeBanner(")
        XCTAssertEqual(gates.sorted(), Self.noticeBannerGateExpectations.sorted(),
                       "NoticeBanner 调用点的门控名单和产品不一致（实际读到 \(gates.sorted())）"
                       + " ⇒ 要么新加了一条没人供电的横幅，要么有人删了一条而忘了删这条账")
        let keys = Self.animationKeys(in: code)
        let undriven = gates.filter { !Self.receiptGateIsDriven($0, by: keys, in: code) }
        XCTAssertTrue(undriven.isEmpty,
                      "这些横幅的门控状态没被任何一条驱动（含派生键展开）推到：\(undriven.sorted())"
                      + " ⇒ `NoticeBanner` 外面那句 `.transition` 是死的")
        print("BANNER_DRIVE 调用点 \(gates.count) 个、键 \(keys.count) 条、"
              + "展开后状态 \(Self.drivingStates(for: keys, in: code).count) 个、无驱动 \(undriven.count) 个")
    }

    static let noticeBannerGateExpectations: Set<String> = [
        "let recovery = historyStore.historyRecoveryNotice",
        "let transfer = historyStore.transferNotice",
        "let dropped = historyStore.droppedFilesNotice",
        "let pasteFailure = historyStore.pasteFailureNotice",
        "let retention = historyStore.retentionNotice",
    ]

    // MARK: - 扫描器

    /// `.animation(...)` 调用里 `value:` 后面的表达式（含跨行、含嵌套括号）。
    static func animationKeys(in source: String) -> [String] {
        var keys: [String] = []
        let needle = ".animation("
        var search = source.startIndex
        while let open = source.range(of: needle, range: search..<source.endIndex) {
            var index = open.upperBound
            var depth = 1
            var body = ""
            while index < source.endIndex {
                let character = source[index]
                if character == "(" { depth += 1 }
                else if character == ")" {
                    depth -= 1
                    if depth == 0 { break }
                }
                body.append(character)
                index = source.index(after: index)
            }
            search = source.index(after: index)
            if let range = body.range(of: "value:") {
                keys.append(String(body[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines))
            }
        }
        return keys
    }

    /// 这个键是不是**永远不变**的东西（字面量 / 空）。
    static func isConstantKey(_ expression: String) -> Bool {
        let key = expression.trimmingCharacters(in: .whitespacesAndNewlines)
        if key.isEmpty { return true }
        if key == "true" || key == "false" { return true }
        if Double(key) != nil { return true }
        if key.hasPrefix("\"") { return true }
        return false
    }

    /// `ReceiptLine` 调用点**上面最近那条 `if`** 的条件文本（去掉 `if ` 与尾部的 `{`，压掉多余空白）。
    /// 三种写法都认：`if let 状态 {`、`if let 局部 = 状态 {`、`if 布尔状态 {`。
    /// 只认 `if let` 的扫描器会**看不见**第三类调用点 —— 那正是"新加一条没驱动的回执"能安静过去的洞。
    /// 找不到 `if` ⇒ 不产出这一条，于是主判据红在"名单两边不等"，而不是少判一个。
    static func receiptGateConditions(in source: String, callSite: String = "ReceiptLine(") -> [String] {
        let lines = source.components(separatedBy: "\n")
        var found: [String] = []
        for (index, line) in lines.enumerated() where line.contains(callSite) {
            for back in stride(from: index - 1, through: max(0, index - 6), by: -1) {
                let trimmed = lines[back].trimmingCharacters(in: .whitespaces)
                guard trimmed.hasPrefix("if ") else { continue }
                var condition = String(trimmed.dropFirst("if ".count))
                while condition.hasSuffix("{") {
                    condition = String(condition.dropLast()).trimmingCharacters(in: .whitespaces)
                }
                condition = condition.components(separatedBy: .whitespaces)
                    .filter { !$0.isEmpty }.joined(separator: " ")
                if !condition.isEmpty { found.append(condition) }
                break
            }
        }
        return found
    }

    /// 这条门控有没有被某条 `.animation` 的键推动。
    static func receiptGateIsDriven(_ gate: String, by keys: [String]) -> Bool {
        gateStateNames(gate).contains { name in keys.contains { mentions($0, identifier: name) } }
    }

    /// 门控条件里的**状态名**：`let 局部 = 状态` 只取等号右边（局部名是解包出来的常量，
    /// 认它等于认一个恒真的键），其余按标识符切开并丢掉关键字与字面量。
    static func gateStateNames(_ gate: String) -> [String] {
        var text = gate
        if text.hasPrefix("let ") { text = String(text.dropFirst("let ".count)) }
        if let equals = text.range(of: "=") { text = String(text[equals.upperBound...]) }
        let keywords: Set<String> = ["true", "false", "nil", "and", "or", "isEmpty"]
        var names: [String] = []
        var current = ""
        for character in text + " " {
            if character.isLetter || character.isNumber || character == "_" || character == "." {
                current.append(character)
            } else {
                if !current.isEmpty { names.append(current) }
                current = ""
            }
        }
        return names.filter { name in
            !keywords.contains(name) && !name.allSatisfy(\.isNumber) && !name.isEmpty
        }.flatMap { name in
            // `store.foo` 这种写法：整串与最后一段都算候选（键里出现哪一个都算被推动）。
            name.contains(".") ? [name, String(name.split(separator: ".").last ?? "")] : [name]
        }
    }

    /// 表达式里有没有**整词**出现的标识符。前缀命中不算：
    /// `exportMessageDraft` 含 `exportMessage` 这串字符，但它不是那个状态 ——
    /// 拿 `String.contains` 判"这条回执有没有被驱动"会恒绿（同一个坑见账本"按名字查消费者"）。
    static func mentions(_ expression: String, identifier: String) -> Bool {
        let haystack = Array(expression)
        let needle = Array(identifier)
        guard !needle.isEmpty, haystack.count >= needle.count else { return false }
        func isWord(_ character: Character) -> Bool {
            character.isLetter || character.isNumber || character == "_"
        }
        for start in 0...(haystack.count - needle.count) {
            guard Array(haystack[start..<(start + needle.count)]) == needle else { continue }
            let beforeIsBoundary = start == 0 || !isWord(haystack[start - 1])
            let after = start + needle.count
            let afterIsBoundary = after == haystack.count || !isWord(haystack[after])
            if beforeIsBoundary && afterIsBoundary { return true }
        }
        return false
    }

    /// 从一段源码里抠出 `return <整数>` 的那几个整数（用来数 previewStage 的档位）。
    static func returnedInts(_ source: String) -> Set<String> {
        var found: Set<String> = []
        for line in source.components(separatedBy: "\n") {
            guard let range = line.range(of: "return ") else { continue }
            let tail = line[range.upperBound...].trimmingCharacters(in: .whitespaces)
            if tail.allSatisfy({ $0.isNumber }), !tail.isEmpty { found.insert(tail) }
        }
        return found
    }

    static func stripCommentLines(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func codeOnly(_ source: String) -> String { Self.stripCommentLines(source) }

    /// `Sources/ClipboardHistoryApp/Views/*.swift`。
    /// 这里自己写一份而不是复用别的测试文件里的同名扫描器：那几个都是 `private`，
    /// 而**按族判据的取目录逻辑必须能被本文件独立证伪**（复用别人的私有工具，
    /// 它就跟着那个文件一起被改坏而本文件不知道）。取不到目录 ⇒ 抛错，不静默返回空集。
    private func productViewSources() throws -> [(file: String, source: String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/Views", isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            let swift = names.filter { $0.hasSuffix(".swift") }
            XCTAssertFalse(swift.isEmpty, "Views 目录是空的：这条按族扫描没有守卫对象")
            return swift.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "MotionDriverTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Views 目录"])
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory + "/" + name)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "MotionDriverTests", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 \(relative)：守卫找不到被守卫的东西时必须红"])
    }

    private func intakeEntry(text: String) -> ClipboardIntake.Entry {
        // 固定来源 App：否则排序随测试期间谁在焦点上而随机失败（同 HistoryStoreTests 的注释）。
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
    }
}
