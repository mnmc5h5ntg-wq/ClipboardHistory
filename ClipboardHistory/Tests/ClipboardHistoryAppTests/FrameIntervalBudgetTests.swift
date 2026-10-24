import XCTest

/// R142 / BACKLOG 176：帧间隔判据的形状，与它的读数通道。
///
/// 为什么单独一个文件：探针那一卷的**用例名册**是 `probe_coverage_gate.py` 的被数对象
/// （源码用例=11）。把两条不需要显示器的纯函数用例塞进那个文件，等于让"在屏探针覆盖率"这道闸门
/// 数错东西 —— 这一条是电池先发现的（四格同时红），不是我先想到的。
/// **不覆盖管线**：这里只有比值判据与读数通道的形状；三臂的真测量在
/// `UIInteractionProbeTests.testFrameIntervalsUnderStateChanges`（要 `CLIPBOARD_HISTORY_UI_INTERACTION=1`）。
/// R142 / BACKLOG 176：帧间隔判据的**形状**（纯函数，真值表直接喂，不需要显示器）。
///
/// 为什么预算是 3.0 而不是 1.25：**这个倍率还没在 runner 上量过**。
/// 本机现在这条采样通道是死的（`FRAME_CHANNEL baseline_n=0`，R91 那一格的原样），
/// 而 runner 我只拿得到 `loaded_p95=26.94` 这一个数 —— 参照臂的数从来没能被收集到
/// （那三行 `FPS-` 走的是 `print`：CI 那一步是 `swift test … > /tmp/ui.log 2>&1`，两条通道其实都进了同一个文件，
///   真正丢的原因是无缓冲/块缓冲，见下面那条守卫）。
/// **R143 更正**：R142 只把新增的那一条 `PROBE_FPS` 走成了 `emit`，三行 `FPS-` 原地没动，
/// 而当时这句注释就写着"本轮改成 emit" ⇒ 台账与代码相反、守卫照绿（U-480）。
/// 现在三行也是 `emit`，并且守卫加了一格"这一条用例里不许再有 `print("FPS-`"。
/// 所以这一轮的处置是**把会换班的假闸门换成宽但不恒真的守卫**：
/// 3.0 倍仍然抓得住真正的回归（动画让 p95 翻倍就是红），而它不会因为 runner 今天负载高就红。
/// 收紧欠一次 runner 读数 —— 176 保持开着，判据账，不是产品缺陷。
enum FrameIntervalBudget {
    static let ratio: Double = 3.0

    /// R176 / BACKLOG 206：`worst ≤ 120ms` 原来按**单遍最大值**判，而最大值是一卷里最不稳的量。
    /// 触发它的事实：run `39157963970`（`0dbcbb5`，只改台账那一笔）红在 `320.65 > 120`，
    /// 而相邻两跑 `e61796c` / `9e1d3d4` 拿着同一份判据是绿的 ⇒ 120ms 这条线正落在 runner 的单帧离群分布里。
    /// 处置**不是删锚点**（那是删弱尺），是要求它被样本数撑着：一帧超锚点 = 离群，≥2 帧才红。
    static let worstFrameAnchorMs: Double = 120
    static let worstFrameOutlierTolerance = 1

    /// `true` = 判成卡顿级红。三种形状：
    /// ① `worst ≤ 锚点` ⇒ 不红；② 超锚点且只有 `tolerance` 颗 ⇒ **不红**（单帧离群，登记成读数）；
    /// ③ 超锚点却数到 0 颗 ⇒ 两把尺自相矛盾 ⇒ 红（回头修尺，不许当成"没超"）。
    static func isWorstFrameJank(worstMs: Double, overAnchorCount: Int) -> Bool {
        if worstMs <= worstFrameAnchorMs { return false }
        if overAnchorCount == 0 { return true }
        return overAnchorCount > worstFrameOutlierTolerance
    }

    /// `nil` = 无从判定（两个参照臂都是 0 ⇒ 分母是空的）。
    /// 这不是"通过"，也不是"红"：它必须有自己的名字，否则又会变成一个静默的绿。
    static func isWithinBudget(loadedP95: Double, baselineP95: Double, offP95: Double) -> Bool? {
        let reference = max(baselineP95, offP95)
        guard reference > 0 else { return nil }
        return loadedP95 / reference <= ratio
    }
}

/// 这一卷不需要显示器、也不需要环境变量：它判的是纯函数的形状（所以 CI 上一定会跑到它）。
final class FrameIntervalBudgetTests: XCTestCase {
    /// 真值表：期望值全部**手算过再写**（U-432 那一族：这次先写后算，红的时候才发现是期望错）。
    func testTheBudgetIsATruthTable() {
        // 参照取两臂里**更宽**的那一个：空转那一臂本来就可能比关动画更慢（机器刚醒）。
        XCTAssertEqual(FrameIntervalBudget.isWithinBudget(loadedP95: 30, baselineP95: 16, offP95: 16), true)
        XCTAssertEqual(FrameIntervalBudget.isWithinBudget(loadedP95: 48, baselineP95: 16, offP95: 16), true,
                       "恰好 3.0 倍算通过（边界不许两边都算红）")
        XCTAssertEqual(FrameIntervalBudget.isWithinBudget(loadedP95: 48.1, baselineP95: 16, offP95: 16), false,
                       "超过预算就必须红 —— 这一格是这条判据唯一的牙")
        XCTAssertEqual(FrameIntervalBudget.isWithinBudget(loadedP95: 45, baselineP95: 10, offP95: 30), true,
                       "参照必须是 max(baseline, off)：取 min 会把 4.5 倍算成红")
        XCTAssertNil(FrameIntervalBudget.isWithinBudget(loadedP95: 20, baselineP95: 0, offP95: 0),
                     "分母是 0 要报「无从判定」，既不许是 true 也不许是 false")
        XCTAssertEqual(FrameIntervalBudget.isWithinBudget(loadedP95: 0, baselineP95: 16, offP95: 0), true,
                       "loaded=0 是「这一臂没帧」，由 n>60 那条抓；这里只管比值")
    }

    /// R176 的锚点判据：期望值全部手算（U-432 那一族：先写后算会把自己红成假案）。
    func testTheWorstFrameAnchorNeedsMoreThanOneOutlier() {
        XCTAssertFalse(FrameIntervalBudget.isWorstFrameJank(worstMs: 119, overAnchorCount: 0))
        XCTAssertFalse(FrameIntervalBudget.isWorstFrameJank(worstMs: 120, overAnchorCount: 0),
                       "恰好等于锚点算通过（边界不许两边都红）")
        XCTAssertFalse(FrameIntervalBudget.isWorstFrameJank(worstMs: 320.65, overAnchorCount: 1),
                       "CI run 39157963970 的真实形状：一帧离群不判产品（相邻两跑同一份判据是绿的）")
        XCTAssertTrue(FrameIntervalBudget.isWorstFrameJank(worstMs: 320.65, overAnchorCount: 2),
                      "两帧就红：这条不许被写成「单帧永远不算」")
        XCTAssertTrue(FrameIntervalBudget.isWorstFrameJank(worstMs: 130, overAnchorCount: 0),
                      "worst 超锚点却数到 0 颗 ⇒ 两把尺矛盾，红给尺而不是绿")
        XCTAssertTrue(FrameIntervalBudget.isWorstFrameJank(worstMs: 400, overAnchorCount: 40),
                      "一批帧都掉到锚点之上 = 真卡顿，必须红")
    }

    /// R178：锚点判据不是纸上概念 —— 探针那一卷必须**真的**用它，而且用的是 `overAnchor` 这一格。
    /// 扫源码而不是跑探针：这条采样通道在本机是死的（R91 `baseline_n=0`），
    /// 所以"接没接线"只能按形状判，真产物那半由 CI 的 `PROBE_WORST_FRAME` 读数签（BACKLOG 206）。
    func testTheProbeWiresTheAnchorToTheSampleCount() throws {
        let src = try String(contentsOf: URL(fileURLWithPath: "UIInteractionProbeTests.swift",
                                            relativeTo: URL(fileURLWithPath: #filePath).deletingLastPathComponent()),
                             encoding: .utf8)
        let lines = src.components(separatedBy: "\n").filter { !$0.trimmingCharacters(in: CharacterSet(charactersIn: "/ ")).isEmpty && !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
        let joined = lines.joined(separator: "\n")
        XCTAssertEqual(1, joined.components(separatedBy: "let overAnchor = loaded.overAnchor").count - 1,
                       "探针里 `overAnchor` 的取数处必须恰好一处（0 = 没接线；2 = 两把尺各数各的）")
        XCTAssertEqual(1, joined.components(separatedBy: "XCTAssertFalse(FrameIntervalBudget.isWorstFrameJank(worstMs: loaded.worst, overAnchorCount: overAnchor)").count - 1,
                       "锚点判据必须以 `overAnchor` 为参数被断言一次 ⇒ 改成别的形状（比如又拿 worst 单判）这一格会红")
        // R180 / BACKLOG 208：针脚数的是**形状**，不是某个易变的插值串
        //（完整插值串要在 Swift 字面量里套 ASCII 双引号，R179 就是在这里失手的）。
        // 契约：颗数必须**同时**活在 `PROBE_FPS`（经 `fpsTail` 这个局部尾段）与独立读数行里 ——
        // 只活在尾部那一行的读数是拿不到证人的（runner `39161493538`：FPS 完整、`PROBE_WORST_FRAME` 整卷 0 次）。
        XCTAssertEqual(1, joined.components(separatedBy: "let fpsTail = ").count - 1,
                       "FPS 行的尾段要先算成局部常量：直接拼长插值会让编译器 type-check 超时（R176 实测）")
        XCTAssertEqual(1, joined.components(separatedBy: "+ fpsTail)").count - 1,
                       "`PROBE_FPS` 必须拼上那个尾段 —— 颗数不在活下来的那一行里，CI 上就没人替『离群还是真卡顿』作证")
        // 实测载体是**三处**：`fpsTail`（跟着 `PROBE_FPS` 落地）、独立行 `PROBE_WORST_FRAME`、
        // 以及离群时的 `WORST_OUTLIER`。少任何一处都意味着某条通道被悄悄撤掉 ⇒ 这一格按次数判，不按"提过"判。
        let countHits = joined.components(separatedBy: "超锚点帧=").count - 1
        XCTAssertEqual(3, countHits,
                       "『超锚点帧』要出现在三处（FPS 尾段 / 独立读数行 / 离群提示行），实到 \(countHits) 次"
                       + " ⇒ 有一处被删或被合并掉了；只活在尾部那一行等于 CI 上没人作证（208）")
    }

    /// 读数与「退掉的绝对判据」都要被钉住：
    /// ① `PROBE_FPS` 必须走 `emit`（stderr / 文件通道）而不是 `print` —— 那三行 `FPS-` 在 CI 里
    ///    从来没被收集到过（块缓冲 + 看门狗收进程），所以收紧这条判据欠的那份读数一直不存在；
    /// ② 本机数 `loaded.p95 ≤ 20` 不许被悄悄放回判据位置（BACKLOG 42 第三次生效就是这一族）。
    func testTheReadingsUseTheChannelAndTheLocalNumberStaysRetired() throws {
        let source = try String(contentsOf: URL(fileURLWithPath: "UIInteractionProbeTests.swift", relativeTo: URL(fileURLWithPath: #filePath).deletingLastPathComponent()), encoding: .utf8)
        // 搜索串**拼出来**：直接写全名，这一条守卫自己就是文件里最后一次出现那个串的地方，
        // `.last` 就会取到"我自己之后的文本"，于是永远读不到被测物（R94 那一族：整文件 contains 会命中自己引用的注释）。
        let marker = "func testFrameIntervals" + "UnderStateChanges() throws {"
        // 结束锚点必须是**下一条用例**：`syntheticStore` 定义在这一条之前（第 83 行），
        // 拿它当结束符等于一路取到文件末尾 —— 那会把这条守卫自己也读进来，
        // 于是"不许含 loaded.p95, 20"这一格会被自己的搜索串喂饱。
        let endMarker = "func testAccessibility" + "TreeCoverage() throws {"
        let parts = source.components(separatedBy: marker)
        XCTAssertEqual(parts.count, 2, "定义行要么没找到、要么找到两处 ⇒ 这条守卫无从判定（不许猜哪一段是要读的）")
        let body = parts[1].components(separatedBy: endMarker).first ?? ""
        XCTAssertFalse(body.isEmpty, "取不到那一条用例的正文 ⇒ 这条守卫无从判定")
        XCTAssertTrue(body.contains("emit(\"PROBE_FPS"),
            "帧间隔的三臂读数没走 emit ⇒ CI 收不到，而收紧预算这件事就永远欠一份数（R90 那一族）")
        XCTAssertFalse(body.contains("print" + "(\"FPS-"),
            "R142 的台账写着「三臂 + 比值 + 机器键一律走 emit」，可那三行 `FPS-` 当时原地没动 ⇒ "
                + "这条判据现在钉的是**全部** FPS 读数，不只是新增那一行（U-480）")
        XCTAssertFalse(body.contains("loaded.p95, 20"),
            "本机量出来的 20ms 被放回了判据位置 ⇒ 这一臂又会在 runner 上换班（BACKLOG 176 的原样）")
        XCTAssertTrue(body.contains("MotionFilmstripTests.filmstripMachineKey()"),
            "读数没带机器键 ⇒ 两台机器的数会混成一条曲线（R38 那一族）")
    }

    /// R143：探针文件里「还在用 `print` 的读数」要有一份**名册**，不是一个计数。
    /// 为什么不用上限：写成「≤10 条」时「转走一条 + 新加一条」照样绿，而那正是这次要防的形状
    /// （R142 转走了新增那一行，三行旧的留着，台账却说全改了）。
    /// 名册双向相等 ⇒ 新写法红（没登记）、旧写法退场也红（登记过期）—— 与 R78 那两把轴的处置同形。
    /// 搜索串拼出来：这条守卫自己就含 `print` 加左引号的形状，写全等于把守卫自己数进名册（U-473）。
    func testProbeFilePrintReadingsAreARosterNotACount() throws {
        let printNeedle = "print" + "(\""
        let emitNeedle = "emit" + "(\""
        // R303 的另一格教训：搬进 emit 之后，「按 print 找读数」的名单就瞎了 ——
        // 刀 M731（把 KEYCHAIN_FKA 改名）本轮真的 ESCAPED 过一次。所以这张名册问的是
        // **这个文件的读数清单**，通道由名册自己登记：搬过的文件按 emit 数，没搬的按 print 数。
        // 「谁还没搬」由 `scripts/tests/test_readings_channel_coverage.py` 那根棘轮管，两格判的是两句不同的话。
        // R303 / BACKLOG 360 第一步：这张名册的**主语从一份文件变成一批文件**。
        // 起因是本轮把 `UIInteractionProbeTests.swift` 里 15 行读数全搬进 `CaptureReadings.emit`
        // —— 那一格如果只扫这一个文件，搬完之后就变成「空名册对空读数」：仍然绿，
        // 却什么都不再判（恒真的名单遍历，U- 家族里写过两次）。所以把 360 队列里接下来的
        // 探针文件一起放进来，每个文件各自登记标记与行数：
        //   · 已搬空的文件留在名单里、登记为空 ⇒ 谁把读数写回 print，立刻红（退场可复查）；
        //   · 还没搬的文件必须有名字与行数 ⇒ 新写法红（没登记），搬走也红（登记过期）。
        // 与 `scripts/tests/test_readings_channel_coverage.py` 的分工：那一卷数的是**全部判据文件**
        // 的裸 stdout 行数（一根双向棘轮），这一格数的是**按文件按标记**的清单（谁能被读到）。
        // 三份名单并存是本回合到的另一件事，记在 361。
        let registered: [String: [String]] = [
            // R303：这一份的读数全部走 emit ⇒ 名单按 emit 数，而且登记的是**这个文件的全部读数**，
            // 不只是本轮搬走的那 15 行 —— 名册问的是「这些读数有没有名字」，与它走哪条通道无关。
            // 现读 53 行 / 42 种标记（MENUS 6 行、REVEAL 4 行是循环里逐次打的同一标记）。
            "UIInteractionProbeTests.swift": [
                "MENUS", "REVEAL", "NOTE", "DRIFT", "MARKDOWN", "PROBE_PULSE", "PROBE_DONE",
                "FOCUS-CHAIN", "TAB-KEY-CHAIN", "TAB-KEY-KINDS", "KEYBOARD-UIMODE",
                "FRAME_CHANNEL", "FPS-BASELINE", "FPS-MOTION-OFF", "FPS-LOADED", "PROBE_FPS",
                "PROBE_WORST_FRAME", "WORST_OUTLIER", "AX-VISITED", "AX-UNNAMED", "TREE2",
                "DRAG-LIMIT", "OBSERVE", "OBSERVE-TABLE", "INTAKE_PIN", "INTAKE_READING",
                "KEYCHAIN", "KEYCHAIN_TREE", "KEYCHAIN_FKA", "FILTER_FOCUS",
                "FILTER_PILL_FOCUS_UNCOVERED", "FOCUSCHAIN-RING", "RINGVIEWS",
                "ROW_PROXY_TRUTHTABLE", "ROW_PROXY_CENSUS", "ROW_PROXY[", "ROW_PROXY_LISTROWS",
                "TAB_STOPS_NOT_RUN=NO_PROXY", "TAB_STOPS_FROM_TOP_ROW", "ROW_PROXY_CONTRAST",
                "ROW_PROXY_CONTRAST_NOT_RUN=QUICKPICK_WINDOW_NIL", "WATCHDOG",
            ],
            "PressInteractionProbeTests.swift": ["PRESS_PROBE", "INTERACTION_NOT_RUN=synthetic-mouse-"],
            "OffscreenSymbolInkProbeTests.swift": ["INK"],
            "WindowChromeLayoutTests.swift": ["CHROME", "SIDEBAR_PIN"],
            "MotionDriverTests.swift": ["RECEIPT_DRIVE", "DERIVED_KEY_EXPANSION", "BANNER_DRIVE"],
            "PressFeedbackTests.swift": ["PRESS_AXIS", "FILL_STEP"],
            "SettingsFailureReceiptTests.swift": ["FEEDBACK_EXPORT_RECEIPT_TRUTH_TABLE",
                                                  "EXPORT_FEEDBACK_CHANNEL", "ARCHIVE_TRANSFER_RECEIPT",
                                                  "ARCHIVE_ACTION_CHANNEL", "RECEIPT_FIXTURE_COPY"],
            // R336：`MD_RENDER_COST` 当场登记在这张表里，而不是让它先红一轮再说"那就去改名册"。
            // 这一格问的是「这些读数有没有名字」，与它走哪条通道无关 —— 新增一行 emit 而名册不动，
            // 就是 R143/U-473 那一族（未登记的读数不许存在）。它同时把这张表的行数从 3 抬到 4，
            // 与下面 `counts` / `total` 两格**同一笔**改到现读（分两笔改会让中间那一跑是红的）。
            "PerfBudgetTests.swift": ["PERF", "PERF[", "MD_RENDER_COST"],
        ]
        let counts: [String: Int] = [
            "UIInteractionProbeTests.swift": 53,
            "PressInteractionProbeTests.swift": 2,
            "OffscreenSymbolInkProbeTests.swift": 3,
            "WindowChromeLayoutTests.swift": 3,
            "MotionDriverTests.swift": 3,
            "PressFeedbackTests.swift": 5,
            "SettingsFailureReceiptTests.swift": 5,
            "PerfBudgetTests.swift": 4,
        ]
        let dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        // R304：搬进 emit 的文件变成一张表（不是单个 if）—— 每搬一份就要在这里换一次通道，
        // 否则名册会像 R303 那样对「标记被改名」瞎掉（刀 M878 钉这一侧）。
        // R306：第三批里有两份住在这张名册的 8 个文件之内 —— 它们的读数换了腿，
        // 于是通道表必须跟着加名字（D-284：名册登记的是名字，通道是另一件事，两者都要显式）。
        let emitChannel: Set<String> = [
            "UIInteractionProbeTests.swift", "PressFeedbackTests.swift",
            "SettingsFailureReceiptTests.swift", "MotionDriverTests.swift",
            "OffscreenSymbolInkProbeTests.swift", "PerfBudgetTests.swift",
        ]
        func channel(_ file: String) -> String { emitChannel.contains(file) ? emitNeedle : printNeedle }
        var measured: [String: [String]] = [:]
        var total = 0
        for name in registered.keys.sorted() {
            let source = try String(contentsOf: URL(fileURLWithPath: name, relativeTo: dir), encoding: .utf8)
            var markers: [String] = []
            for line in source.split(separator: "\n", omittingEmptySubsequences: false) where line.contains(channel(name)) {
                let text = String(line)
                guard let found = text.range(of: channel(name)) else { continue }
                var marker = ""
                for character in text[found.upperBound...] {
                    if character == " " || character == "\\" { break }
                    marker.append(character)
                }
                markers.append(marker)
            }
            measured[name] = markers
            total += markers.count
        }
        for name in registered.keys.sorted() {
            XCTAssertEqual(Set(measured[name] ?? []), Set(registered[name] ?? []),
                "\(name) 的 print 读数与名册不符 ⇒ 要么有未登记的新读数，要么有已退场的旧登记"
                    + "（R143/U-473：先登记才允许存在；R303：搬走之后名字留着、清单变空）")
            XCTAssertEqual((measured[name] ?? []).count, counts[name] ?? -1,
                "\(name) 的行数与登记不符（多一行/少一行）⇒ 名册那份计数过期，请连理由一起改")
        }
        XCTAssertEqual(total, 78,   // R336 现读 78（原 77 + `MD_RENDER_COST` 一行）
            "这张名册覆盖的探针文件里裸 stdout 读数总数变了 ⇒ 要么 360 搬走了一批（那就把上面两张表"
                + "一起改到现读，并把搬空的文件留在名单里登记为空），要么新写了只走 stdout 的读数")
    }
}
