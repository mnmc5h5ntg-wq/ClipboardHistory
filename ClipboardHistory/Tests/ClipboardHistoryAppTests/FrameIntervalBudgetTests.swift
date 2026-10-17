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
        let needle = "print" + "(\""
        let source = try String(contentsOf: URL(fileURLWithPath: "UIInteractionProbeTests.swift", relativeTo: URL(fileURLWithPath: #filePath).deletingLastPathComponent()), encoding: .utf8)
        var markers: [String] = []
        for line in source.split(separator: "\n", omittingEmptySubsequences: false) where line.contains(needle) {
            let text = String(line)
            guard let found = text.range(of: needle) else { continue }
            var marker = ""
            for character in text[found.upperBound...] {
                if character == " " || character == "\\" { break }
                marker.append(character)
            }
            markers.append(marker)
        }
        // R143 实测：10 行 print 读数、9 种标记（`NOTE` 两行）。FPS- 那一族不在名单里，
        // 因为它已经全部走 emit —— 若有人把它写回 print，Set 里会冒出一个没登记的标记而红。
        XCTAssertEqual(Set(markers), Set([
            "FOCUS-CHAIN", "TAB-KEY-CHAIN", "TAB-KEY-KINDS", "KEYBOARD-UIMODE",
            "NOTE", "AX-VISITED", "AX-UNNAMED", "FOCUSCHAIN-RING", "RINGVIEWS",
        ]), "探针里的 print 读数与名册不符 ⇒ 要么有未登记的新读数，要么有已退场的旧登记")
        XCTAssertEqual(markers.count, 10,
            "同一标记的行数变了（多一行/少一行）⇒ 名册那份计数过期，请连理由一起改（NOTE 那两条是条件注记）")
    }
}
