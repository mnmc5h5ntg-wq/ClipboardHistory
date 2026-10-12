import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 动效取证：在**真实在屏窗口**里逐帧抓取一次状态变更的过程，量化每对帧的变化面积，
/// 用来区分「有过渡」与「瞬间跳变」。
///
/// 来源与出处：这套方法是第四轮动效审计（`~/Documents/时间剪史_审计_2026-10-12_动效专项/`）
/// 提供的，它量出了"四件最常发生的事都是一帧跳变"。本轮把动效加上之后，
/// 同一把尺子必须反过来能证明它们**不再是**跳变 —— 否则"我加了 .transition"这句话
/// 和当初"全仓 17 处动画声明"一样，只是源码层的事实。
///
/// 四条判据的来历（都是踩过之后写下来的）：
/// 1. **必须先拍 3 帧改前基线**。第一版探针没有 pre-roll，notice-banner 整段测出 0.00%，
///    因为改动落在第 0 帧之前 —— 那会被读成"什么都没发生"，而实际是"没拍到发生"。
/// 2. **判据是"这次变化分摊到几帧"，不是"总共变了多少像素"**，而且门槛是**相对峰值步长**的
///    比例 + 一个绝对地板。第一版用的是"变化面积 >5%"这种绝对量，它有一个致命偏差：
///    一块只占窗口百分之几的横幅哪怕完整淡入，每对帧也只有 0.01 上下在变 ——
///    于是"淡入"和"跳变"都会读成"没变化"，判据稳定地把过渡判成跳变。
///    绝对地板拦的是另一个方向：整段都是噪声时，相对门槛会把每一帧都算成在动。
/// 3. **判据的归因要有对照**：`testTheRulerAttributesTheMotionToOurAnimation` 把目录曲线
///    换成零时长再量同一个场景，数字必须掉下来；`testTheRulerSeesNothingWhenNothingChanges`
///    是什么都不触发，必须读到 0。少了这两条，"≥3 帧在动"完全可能是图片解码或滚动条淡出。
/// 4. **帧数不足 ⇒ 显式失败**，不许悄悄通过。驱动现在是一个 16ms 的 `Timer`：
///    第一版用 `CADisplayLink`，而它依附于"显示器正在刷新一帧" —— 本机显示器一休眠，
///    `ticks` 就恒为 0，六条判据一起变成"只抓到 0 帧"。那种情况必须红，
///    报"通过"就是假绿（账本里记着一整族这种形状）。
///
/// 尺子自己的时间分辨率也打在同一行日志里（`采样≈Nms`）：本机实测约 46ms/帧（≈22fps），
/// 所以一次 150ms 的淡入只有 3 帧可分。判据取 3 帧不是松，是**这台机器上能分辨的最小值**；
/// 采样再慢就该先修尺子，而不是把门槛降到 1。
///
/// 开关：`CLIPBOARD_HISTORY_UI_MOTION=1`（会抢前台并开窗，所以默认不跑）。
/// 抓帧走 `cacheDisplay`（离屏合成），驱动是 16ms 的 `Timer`，所以**没有版本门槛**：
/// macOS 12/13/14/15/27 都能跑。第一版用 `CADisplayLink`（15+）时，整个类带着
/// `@available(macOS 15.0, *)`，低版本上 XCTest 静默不跑它 —— 那是"守卫在低版本上不存在"。
@MainActor
final class MotionFilmstripTests: XCTestCase {
    private static let isEnabled = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_MOTION"] == "1"

    /// `requireObservableMotion` 的缓存。`nonisolated(unsafe)` 是因为它是个一次性布尔，
    /// 而且只在主线程的测试里读写（整个类是 `@MainActor`）。
    nonisolated(unsafe) static var motionIsObservable: Bool?

    private var outDir: URL {
        let url = URL(fileURLWithPath: ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_MOTION_OUT"]
            ?? "/tmp/motion-films", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    /// 判据：一次过渡 = **有好几帧都还在变**，而不是"某一帧变了很大一片"。
    ///
    /// 为什么不是固定占比（第一版是"峰值之后还有 ≥2 帧变化面积 >5%"）：变化面积是
    /// **绝对量**，一块只占窗口百分之几的横幅哪怕完整淡入，每对帧也只有 0.01 上下的
    /// 像素在变 —— 用绝对尺子量，"淡入"和"跳变"都会读成"没变化"，
    /// 于是判据稳定地把过渡判成跳变（notice-banner 实测 0.10/0.18/0.08 三帧，被读成 1 帧）。
    /// 改成相对量：**扛得住峰值步长一定比例的帧有几帧**。跳变只有 1 帧，真过渡至少 3 帧。
    private static let minimumTransitionFrames = 3
    /// "这一帧还在动"的门槛：峰值步长的这个比例以下算噪声（光标闪烁、抗锯齿）。
    private static let stepFloorRatio = 0.15
    /// 绝对地板：峰值连这个量都不到 ⇒ 这次变更**根本没被拍到**，不是"没有过渡"。
    /// 有了它，相对门槛才不会在"整段都是噪声"时把每一帧都算成在动。
    private static let minimumVisibleChange = 0.005

    /// 峰值之后不再单独用；这里给两个测试共用。
    static func transitionFrameCount(_ fractions: [Double]) -> Int {
        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return 0 }
        let floor = peak * stepFloorRatio
        return fractions.filter { $0 >= floor }.count
    }

    /// 从触发到"落定"要几帧：以每帧到**最终态**的距离计，峰值之后仍然差得远的帧数。
    /// 这条量的是 MC-2 的定量部分——"声明 150ms 的那一档实际跑多久"。
    static func settleFrames(_ frames: [CGImage], after preRollCount: Int,
                             band: CGRect? = nil) -> Int {
        let bitmaps = frames.map(raster)
        guard bitmaps.count > preRollCount + 2, let last = bitmaps.last, !last.pixels.isEmpty else { return 0 }
        let distances = bitmaps.dropLast().map { changedFraction($0, last, band: band) }
        let window = Array(distances.dropFirst(preRollCount))
        guard let peak = window.max(), peak >= minimumVisibleChange else { return 0 }
        return window.filter { $0 >= peak * stepFloorRatio }.count
    }

    static func peak(_ fractions: [Double]) -> Double { fractions.max() ?? 0 }

    /// 把窗口切成 cols×rows 的格子，打印"峰值那一格里每格的变化量"——用来回答
    /// "到底哪里变了"，而不是靠猜像素坐标去框区域（猜错的结果是整条判据读到 0.000，
    /// 看着像"没动"，其实是我没框到）。
    static func changeGrid(_ frames: [CGImage], index: Int, cols: Int, rows: Int) -> String {
        let bitmaps = frames.map(raster)
        guard index + 1 < bitmaps.count else { return "无帧" }
        var cells: [String] = []
        for row in 0..<rows {
            for col in 0..<cols {
                let band = CGRect(x: CGFloat(col) / CGFloat(cols), y: CGFloat(row) / CGFloat(rows),
                                  width: 1 / CGFloat(cols), height: 1 / CGFloat(rows))
                let v = changedFraction(bitmaps[index], bitmaps[index + 1], band: band)
                cells.append(v > 0.25 ? "#" : v > 0.08 ? "+" : v > 0.015 ? "-" : ".")
            }
            cells.append("|")
        }
        return String(cells.joined())
    }

    static func peakIndex(_ fractions: [Double]) -> Int {
        fractions.indices.max(by: { fractions[$0] < fractions[$1] }) ?? 0
    }

    /// 「落定得有多干脆」：从触发那一刻起，每一帧到**最终态**的距离，取峰值之后最大的那一格，
    /// 再按峰值距离归一。
    ///
    /// 一帧到位 ⇒ 峰值之后所有帧就是最终态 ⇒ ≈0。
    /// 淡入 ⇒ 中间帧是半透明的 ⇒ 明显大于 0（0→1 的淡入在 46ms 采样下约 0.4）。
    ///
    /// 为什么不用相邻帧之差来判"有没有淡入"：淡入的第一帧同时是"旧内容消失"的那一帧，
    /// 相邻差的最大值永远是那一下硬换，淡入的部分被压在门槛以下 ——
    /// 于是真淡入会被读成跳变（本轮 `selection-detail-swap` 就是这么量出 1 帧的）。
    /// 和"最终态"比就没有这个问题。
    static func settleResidualRatio(_ frames: [CGImage], after preRollCount: Int,
                                    band: CGRect? = nil) -> Double {
        let bitmaps = frames.map(raster)
        guard bitmaps.count > preRollCount + 2, let last = bitmaps.last, !last.pixels.isEmpty else { return 0 }
        let distances = bitmaps.dropLast().map { changedFraction($0, last, band: band) }
        let window = Array(distances.dropFirst(preRollCount))
        guard let peak = window.max(), peak >= minimumVisibleChange,
              let peakIndex = window.firstIndex(of: peak), peakIndex + 1 < window.count else { return 0 }
        let tail = window[(peakIndex + 1)...].max() ?? 0
        return tail / peak
    }

    /// 有效采样间隔（ms）。判据是"几帧在动"，所以**必须**把尺子自己的时间分辨率写出来：
    /// 一次 150ms 的淡入在 12fps 的抓取下只有 2 帧可分，这时候"没量到过渡"
    /// 说的是尺子，不是产品。
    static func sampleIntervalMilliseconds(_ stamps: [TimeInterval]) -> Int {
        guard stamps.count > 2 else { return 0 }
        var steps: [TimeInterval] = []
        for index in 1..<stamps.count {
            let step = stamps[index] - stamps[index - 1]
            if step > 0.0001 { steps.append(step) }
        }
        guard !steps.isEmpty else { return 0 }
        steps.sort()
        return Int((steps[steps.count / 2] * 1000).rounded())
    }

    /// 尺子本身会不会区分"一帧跳变"和"分摊到几帧的过渡"——纯数据，不需要窗口，CI 每次都跑。
    ///
    /// 为什么需要这一条：上一版的对照是拿**产品场景**当"已知跳变"的，而这一轮把动效加上之后，
    /// 那个场景（换选）已经不再是跳变了 —— "找不到会跳变的真实场景"不等于"尺子松了"。
    /// 判据的判别力必须自己可证，不依赖某个恰好还没动起来的界面。
    func testTheRulerDistinguishesAStepFromARamp() throws {
        // 一帧跳变：某一对帧变了 14%，其余全是 1% 的噪声。
        let step: [Double] = [0, 0, 0.14, 0, 0.01, 0.01, 0.01, 0, 0, 0]
        // 同总量的过渡：摊到 6 帧，每帧 2%~4%。
        let ramp: [Double] = [0, 0, 0.04, 0.04, 0.03, 0.03, 0.02, 0.01, 0, 0]
        // 什么都没发生：整段只有噪声。
        let idle: [Double] = [0, 0.001, 0.002, 0.001, 0.002, 0.001, 0, 0.001, 0.001, 0]

        XCTAssertEqual(Self.transitionFrameCount(step), 1, "一帧跳变必须读成 1 帧")
        XCTAssertGreaterThanOrEqual(Self.transitionFrameCount(ramp), Self.minimumTransitionFrames,
                                    "分摊到几帧的变化必须读成过渡")
        XCTAssertEqual(Self.transitionFrameCount(idle), 0,
                       "全是噪声时相对门槛会把每帧都算成在动 —— 绝对地板就是拦这个的")
    }

    /// 空白对照：开着同一个窗口、什么也不触发，尺子必须读到"没有过渡"。
    /// 这条是 `minimumVisibleChange` 的变异捕手：地板一旦被调成 0，这里就会红。
    func testTheRulerSeesNothingWhenNothingChanges() throws {
        try skipUnlessEnabledAndCapable()
        let frames = record(Scenario.blank()).frames
        guard frames.count > 4 else {
            XCTFail("只抓到 \(frames.count) 帧，对照无效")
            return
        }
        let fractions = Self.deltas(frames)
        let span = Self.transitionFrameCount(fractions)
        print("MOTION_BLANK frames=\(frames.count) 峰值=\(String(format: "%.4f", fractions.max() ?? 0)) 过渡帧数=\(span)")
        XCTAssertEqual(span, 0, "什么都没发生却量到了过渡 ⇒ 尺子在把重绘噪声读成动画")
    }

    func testTransitionsAreActuallyRunning() throws {
        try skipUnlessEnabledAndCapable()
        var verdicts: [(String, Int, Int)] = []   // 场景, 峰值序号, 峰值后明显变化帧数

        for scenario in Scenario.all() {
            let film = record(scenario)
            let frames = film.frames
            guard frames.count > 4 else {
                XCTFail("\(scenario.name)：只抓到 \(frames.count) 帧，判据没有对照物")
                continue
            }
            let fractions = Self.deltas(frames)
            let span = Self.transitionFrameCount(fractions)
            print("MOTION \(scenario.name) frames=\(frames.count) "
                + "采样≈\(Self.sampleIntervalMilliseconds(film.stamps))ms 过渡帧数=\(span) "
                + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
            writeStrip(scenario.name, frames)
            verdicts.append((scenario.name, Self.peakIndex(fractions) + 1, span))
            XCTAssertGreaterThanOrEqual(span, Self.minimumTransitionFrames,
                                        "\(scenario.name)：整段只有 \(span) 帧还在变 ⇒ 是一帧跳变，不是过渡")
        }
        print("MOTION_SUMMARY " + verdicts.map { "\($0.0)=\($0.2)" }.joined(separator: " "))
    }

    /// A/B 对照：**同一个场景、同一条产品路径**，把目录里的曲线关掉再量一次。
    /// 关掉之后必须读成"一帧跳变"。
    ///
    /// 为什么需要它：光有"过渡帧数 ≥3"这句话，归因是空的 —— 窗口里随时有图片解码、
    /// 滚动条淡出、OCR 回来后重排，它们也能凑出几帧变化。把曲线换成 `.none`
    /// 而事务与 `.transition` 声明都还在，如果数字不掉下来，说明量的根本不是我们的动画。
    ///
    /// 上一版这里量的是一个"已知没有过渡"的产品场景（换选时详情硬换一条）。
    /// 那一轮做完之后那个场景已经有过渡了 —— 而"找不到还在跳变的真实场景"并不等于
    /// "尺子松了"，拿它当对照等于把尺子绑在一个恰好还没动起来的界面上。
    /// 所以判别力改由两条不依赖界面的东西钉住：本条 A/B + `testTheRulerDistinguishesAStepFromARamp`。
    func testTheRulerAttributesTheMotionToOurAnimation() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.noticeBanner()
        MotionCatalog.animationsEnabled = false
        defer { MotionCatalog.animationsEnabled = true }

        let film = record(scenario)
        let frames = film.frames
        guard frames.count > 4 else {
            XCTFail("只抓到 \(frames.count) 帧，对照无效")
            return
        }
        let fractions = Self.deltas(frames)
        let span = Self.transitionFrameCount(fractions)
        print("MOTION_AB \(scenario.name) 曲线关闭 采样≈\(Self.sampleIntervalMilliseconds(film.stamps))ms 过渡帧数=\(span) "
            + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
        XCTAssertLessThan(span, Self.minimumTransitionFrames,
                          "关掉目录曲线之后仍然读到 \(span) 帧在动 ⇒ 判据量的不是我们的动画，上面的绿不可信")
        XCTAssertGreaterThan(fractions.max() ?? 0, Self.minimumVisibleChange,
                             "关掉曲线后这一帧都没变 ⇒ 场景本身没生效，A/B 无效")
    }

    /// M1 的**归因**判据（本轮最重要的一条）：侧栏的行到底有没有在动 —— 答案是没有，
    /// 而这条守卫钉住"不许再假装它在动"。
    ///
    /// 为什么整窗那几条绿不够：审计报告 §13.2 的 S5 用最小复现量到"`withAnimation` 直接
    /// 包住数据变更仍是一帧跳变"。本轮把事务挂到变更漏斗（`HistoryStore.perform` / `add`）上之后，
    /// **整窗**读数确实变成了 4 帧斜坡 —— 但整窗读数分不清"行在滑"和"详情区在淡"。
    /// 分带一量就清楚了：列表中部那条带（第 4~8 行，既不是进来的那行也不是被选中的那行）
    /// 是 `0.283` 一帧到位、落定残余 0.000，和把曲线关掉时**一模一样**。
    /// 斜坡全部来自右侧详情区。所以报告的结论成立：`List`（`NSTableView` 后端）拿不到
    /// SwiftUI 的行级 transition，四种写法都不行。
    ///
    /// 于是 M1 被砍，行过渡声明也从 `HistorySidebarView` 上摘掉了。这条判据留下做两件事：
    /// ① 量到的仍然是"一帧"（如果哪天 SwiftUI 支持了，这里会红，提醒我们重新评估）；
    /// ② 源码里不许再出现挂在 `List` 行上的 `.transition` —— 一个不执行的声明比没有更坏，
    ///    它会让下一个人以为已经做过了。
    func testListRowsDoNotAnimateAndNothingClaimsTheyDo() throws {
        try skipUnlessEnabledAndCapable()
        // 侧栏宽约 280/760、行高约 44/560：这条带是窗口高度的 35%~65%，即第 4~8 行。
        let band = CGRect(x: 0.02, y: 0.35, width: 0.32, height: 0.30)
        let scenario = Scenario.listInsertNewRecord()

        let film = record(scenario)
        let residual = Self.settleResidualRatio(film.frames, after: 3, band: band)
        let fractions = Self.deltas(film.frames, band: band)
        print("MOTION_CUT \(scenario.name) 带内过渡帧数=\(Self.transitionFrameCount(fractions)) "
            + "落定残余=\(String(format: "%.3f", residual)) "
            + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
        XCTAssertLessThan(residual, 0.15,
                          "带内出现了慢慢落定的过程 ⇒ `List` 的行过渡哪天能跑了，M1 要重新评估（先读这段注释）")
        // 阳性对照：同一条量法量一次**真的有过渡**的场景，必须读出明显大于 0 的残余。
        // 没有这一句，上面那条只是"这里本来就什么都不会动"，量不出尺子在这个维度上工作。
        let fading = record(Scenario.noticeBanner()).frames
        let fadingResidual = Self.settleResidualRatio(fading, after: 3)
        print("MOTION_CUT_CONTROL notice-banner 落定残余=\(String(format: "%.3f", fadingResidual))")
        XCTAssertGreaterThan(fadingResidual, 0.15,
                             "连横幅淡入都读不出残余 ⇒ 这把尺子在这个维度上没有分辨率，上面那条绿是空的")

    }

    /// 上面那条判据的**源码那一半**，单独一条、不开窗口。
    ///
    /// 为什么不并在一起：那半条要量像素，整条被 `CLIPBOARD_HISTORY_UI_MOTION` 门住了 ——
    /// 一个纯文本的"不许留不执行的声明"跟着一起被跳过，就等于 CI 上它从来没跑过。
    /// 拆出来之后它在任何机器上都是硬判据。
    func testNoTransitionIsClaimedOnListRows() throws {
        let sidebar = try productSource(named: "Views/HistorySidebarView.swift")
        let afterList = sidebar.components(separatedBy: "List(selection: selectionBinding) {").dropFirst().first
        let listBody = try XCTUnwrap(afterList, "找不到 `List(selection:)` 这一段：锚点失效，这条守卫无从判定")
            .components(separatedBy: "\n        }").first ?? ""
        XCTAssertFalse(codeOnly(listBody).contains(".transition("),
                       "`List` 的行上又出现了 .transition：它在 macOS 上不会执行，只会让下一个人以为已经做过了")
    }

    /// 详情区的换页：**换类型才软交接，换字不演**（M4 的可行版本）。
    ///
    /// 两半都要量，因为只测一半的话，"淡入"这个说法没有内容：
    /// 文本→图片必须读得出一个落定过程（有过渡），文本→文本必须读不出（不演）。
    func testDetailPreviewCrossfadesOnlyWhenTheKindChanges() throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.40, y: 0.12, width: 0.58, height: 0.76)   // 详情区，避开标题栏

        let kindChange = record(Scenario.detailKindChange())
        let crossfade = Self.settleResidualRatio(kindChange.frames, after: 3, band: band)
        let kindFractions = Self.deltas(kindChange.frames, band: band)
        print("MOTION_DETAIL kind-change 带内过渡帧数=\(Self.transitionFrameCount(kindFractions)) "
            + "落定残余=\(String(format: "%.3f", crossfade))")
        XCTAssertGreaterThan(crossfade, 0.15,
                             "换类型时详情区一帧到位 ⇒ 那条 `.transition` 没接上线（或又被谁摘掉了）")

        let sameKind = record(Scenario.detailSameKind())
        let snap = Self.settleResidualRatio(sameKind.frames, after: 3, band: band)
        let sameFractions = Self.deltas(sameKind.frames, band: band)
        print("MOTION_DETAIL same-kind 带内过渡帧数=\(Self.transitionFrameCount(sameFractions)) "
            + "落定残余=\(String(format: "%.3f", snap))")
        XCTAssertLessThan(snap, 0.15,
                          "两条文本之间也在淡 ⇒ 每次方向键翻记录都演一遍，那是负债")
    }

    /// 位移档的**真实时长**（MC-2 的像素那一半）。
    ///
    /// 说清楚这条能证明什么、不能证明什么：本机有效采样约 50ms，所以它分辨不出
    /// "150ms 还是 200ms"——那需要 4ms 一帧。它能证明的是**没有跑飞**：
    /// 声明 0.15s 的滑入如果实际要 0.4s 才落定，这里就会超过上限。
    /// 第一版的病正在相反的方向：`duration(for:)` 写 0.15，而 `animation(for:)` 在位移档
    /// 里用写死的 `response: 0.32`，纯值守卫一声不响（报告场景 C：声明 150ms、实测 200ms）。
    /// 那一半已经由 `testCurveSecondsComeFromTheDurationTable` 钉住；这条钉的是产物。
    func testSlidingRoleSettlesWithinItsBudget() throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.05, y: 0.02, width: 0.90, height: 0.20)   // 横幅那一条
        let film = record(Scenario.noticeBanner())
        let settle = Self.settleFrames(film.frames, after: 3, band: band)
        let interval = Self.sampleIntervalMilliseconds(film.stamps)
        print("MOTION_SETTLE banner-in 到位帧数=\(settle) 采样≈\(interval)ms ⇒ 上界约 \(settle * interval)ms")
        XCTAssertGreaterThan(settle, 1, "一帧就落定 ⇒ 这条位移档根本没有过程，上面的过渡判据要重新看")
        XCTAssertLessThanOrEqual(settle, 6,
                                 "横幅滑入要 \(settle) 帧才落定（≈\(settle * max(interval, 1))ms），远超声明的 150ms")
    }

    /// 系统符号动效（`contentTransition(.symbolEffect(.replace))` / `symbolEffect(.bounce)`）
    /// **不在这把尺的可测范围内** —— 这条测试的作用是把"测不到"钉成一个事实，而不是留一句
    /// "我加了过渡所以它在动"。
    ///
    /// 实测（本机，同一份帧数据两臂对照）：把收藏星在**列表行里**切换，
    /// 动画开与目录曲线归零**读数完全相同**（`0.190` 单帧，两臂过渡帧数都是 1）。
    /// 这有两种解释，我分不开：① `List` 行内也不吃 SwiftUI 过渡（与 M1 同根因）；
    /// ② 系统符号动效是 SF Symbols 自己的图层动画，`cacheDisplay` 抓的是模型树 ⇒ 抓不到。
    /// ②的先例就在本文件头上写着（报告 §13.2 也实测过 `animationKeys` 恒空而像素确有斜坡），
    /// 所以我**没有**据此把行内的 `symbolMotion` 摘掉 —— 那是拿尺子的盲区当产品的结论。
    ///
    /// 这里保留一条真正能判的断言：**如果**哪天这把尺看得见它了（比如换成自绘的淡入），
    /// 那它必须两臂有别；否则就还是"未知"，不许写进"已交付"。
    func testSystemSymbolEffectsAreOutOfThisRulersReach() throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.005, y: 0.26, width: 0.05, height: 0.12)   // 侧栏第 4 行的星标列
        let scenario = Scenario.toggleFavoriteInRow()
        let on = Self.deltas(record(scenario).frames, band: band)
        MotionCatalog.animationsEnabled = false
        let off = Self.deltas(record(scenario).frames, band: band)
        MotionCatalog.animationsEnabled = true
        print("MOTION_SYMBOL row-star 开 帧数=\(Self.transitionFrameCount(on)) 峰值=\(String(format: "%.3f", Self.peak(on)))")
        print("MOTION_SYMBOL row-star 关 帧数=\(Self.transitionFrameCount(off)) 峰值=\(String(format: "%.3f", Self.peak(off)))")
        XCTAssertGreaterThan(Self.peak(on), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 我连星标在哪都没框到，这条'测不到'的结论本身不成立")
        XCTAssertEqual(Self.transitionFrameCount(on), Self.transitionFrameCount(off),
                       "两臂现在有差别了 ⇒ 这把尺重新看得见系统符号动效，把这条改成真判据，"
                       + "并把 `AGENT_UI_AUDIT` 里那条'量不到'的边界撤掉")
    }

    /// 这把尺看不看得见 **AppKit 自己的行动画**（`insertRows/removeRows(withAnimation:)`）——
    /// 快速选择浮层（M1 的替代路径）动效的成败全押在它上面，所以先量尺子，再谈交付。
    ///
    /// 为什么不能用 SwiftUI 那套结论外推：`List` 的四种写法量出来都是一帧到位（D-055 / M1），
    /// 而那条路的根因是"SwiftUI 的 `.transition` 在 NSTableView 后端上不执行"。
    /// 这里走的是**同一张表的原生 API**（AppKit 自己插删行），是另一件事，必须单独量。
    ///
    /// 两臂由 `QuickPickController.rowAnimationOptions` 给 —— 也就是**产品实际传给 AppKit 的那两个值**，
    /// 不是我在测试里另写的一份。这样"关掉之后什么都不动"这条对照，测的确实是产品开关。
    ///
    /// 判据的形状和 `testSystemSymbolEffectsAreOutOfThisRulersReach` 一样是**双向**的：
    /// 两臂读数必须不同。如果相同 ⇒ 尺子看不见 AppKit 的图层动画（`cacheDisplay` 抓的是模型树），
    /// 那 ① 就只能记成"源码已接、产物未量"，**不许**写进"已交付"。
    func testNativeRowAnimationIsVisibleToTheRuler() async throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.04, y: 0.10, width: 0.92, height: 0.78)   // 表格区，避开标题栏
        let probe = TableProbe()

        let animatedFilm = probe.record(animation: QuickPickController.rowAnimationOptions(
            reduceMotion: false, animationsEnabled: true))
        let animated = Self.deltas(animatedFilm, band: band)
        let animatedInterval = Self.sampleIntervalMilliseconds(probe.lastStamps)
        let instantFilm = probe.record(animation: QuickPickController.rowAnimationOptions(
            reduceMotion: true, animationsEnabled: true))
        let instant = Self.deltas(instantFilm, band: band)
        let instantInterval = Self.sampleIntervalMilliseconds(probe.lastStamps)
        let animatedSpan = Self.transitionFrameCount(animated)
        let instantSpan = Self.transitionFrameCount(instant)
        print("MOTION_NATIVE row-insert 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated))) 采样≈\(animatedInterval)ms")
        print("MOTION_NATIVE row-insert 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant))) 采样≈\(instantInterval)ms")
        // 数字先打，再决定"是产品没动还是这台机器看不见"。
        try await requireObservableMotion()
        XCTAssertGreaterThan(Self.peak(animated), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 我连表格在哪都没框到，两臂相同这条结论不成立（是探针坏了，不是动效坏了）")
        XCTAssertLessThanOrEqual(instantSpan, 1,
                                 "关掉动画那一档本该是一帧到位，却量到 \(instantSpan) 帧在动 ⇒ 带里有别的动在跑（滚动条淡出？），两臂对照失效")
        XCTAssertGreaterThanOrEqual(animatedSpan, Self.minimumTransitionFrames,
                                    "开了 `.effectFade` 仍只读到 \(animatedSpan) 帧 ⇒ 这把尺看不见 AppKit 的行动画"
                                    + "（`cacheDisplay` 抓的是模型树）。① 只能记成'源码已接、产物未量'，不许写进已交付")
    }

    /// **产品形状的行动画判据**：插完行之后紧跟的那两句（`selectRowIndexes` + `scrollRowToVisible`）
    /// 不能把刚起的行动画吃掉。
    ///
    /// 这条是被一次虚警逼出来的：`testNativeRowAnimationIsVisibleToTheRuler` 量的是"只插行"，
    /// 而产品里 `queryChanged` 从来不会只插行 —— 它每次都跟着改选中。
    /// 九臂实验（数字记在 D-056）给出的答案是：
    /// **选中真的变了 ⇒ 行动画被吃掉；写的是同一个选中 ⇒ 动画活着。**
    /// 打字时候选下标恒为 0，写下去的就是同一个行号 ⇒ 产品路径成立，代码不用改。
    /// 两臂都留成判据：第一臂防"以后有人把选中写歪"，第二臂把"变了就会被吃掉"这个已知边界钉住
    /// —— 哪天 AppKit 不这么表现了，第二条会红，那时才谈得上"顺手把方向键也做上动画"。
    func testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt() async throws {
        try skipUnlessEnabledAndCapable()
        let probe = TableProbe()
        let sameRow = Self.deltas(probe.recordProductSequence(selectionChanges: false))
        let moved = Self.deltas(probe.recordProductSequence(selectionChanges: true))
        let sameSpan = Self.transitionFrameCount(sameRow)
        let movedSpan = Self.transitionFrameCount(moved)
        print("MOTION_SEQUENCE 选中没变 帧数=\(sameSpan) 峰值=\(String(format: "%.3f", Self.peak(sameRow)))")
        print("MOTION_SEQUENCE 选中变了 帧数=\(movedSpan) 峰值=\(String(format: "%.3f", Self.peak(moved)))")
        try await requireObservableMotion()
        XCTAssertGreaterThan(Self.peak(sameRow), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 探针坏了，两臂结论都不成立")
        XCTAssertGreaterThanOrEqual(sameSpan, Self.minimumTransitionFrames,
                                    "产品每次插行后都跟着写选中；写的是同一个选中就把行动画吃掉了 ⇒ ① 在真实调用点上是死的")
        XCTAssertLessThanOrEqual(movedSpan, 1,
                                 "选中变了却仍然读到 \(movedSpan) 帧在动：AppKit 的行为变了。"
                                 + "先确认这不是探针误读，再把'方向键也做动画'重新评估")
    }

    // MARK: - 骨架扫光（M9）

    /// 骨架扫光（M9）到底有没有在扫 —— 这条必须量，因为"我加了 `repeatForever`"
    /// 和"我加了 `.transition`"是同一种话，而后者已经被证明过可以不落地（D-055 / MC-12）。
    ///
    /// 判据与别的场景**不一样**，因为常驻循环没有"落定"这回事：
    /// - 该动的那一档：必须**连续**有好几对帧都在变（一条静止的灰杠只会有一对；
    ///   一次到位的跳变也只有一对）；
    /// - 减弱动态那一档：应当**几乎什么都不变**（峰值低于绝对地板）——
    ///   这一臂反过来证明"上面那几对在变"确实是扫光，而不是这张图的噪声。
    ///
    /// **不带 band**：这张图里除了骨架什么都没有，"整窗"就是"这一件事"。
    /// 别的场景必须分带，是因为那个窗口里同时有横幅、列表、详情在动；
    /// 这里再框一块，框错的代价反而是把一条真的在扫的动画读成"没动" ——
    /// 第一版就是这样（条带位置与分带的 y 翻转对不上，读到 0.000，
    /// 差点把结论写成"这把尺看不见渐变"，见 `testTheRulerSeesAStateDrivenSwiftUIUpdate` 的对照臂）。
    func testSkeletonSweepActuallySweeps() async throws {
        try skipUnlessEnabledAndCapable()
        let probe = SkeletonProbe()
        let runningFrames = probe.record(reduceMotion: false)
        let running = Self.deltas(runningFrames)
        let interval = Self.sampleIntervalMilliseconds(probe.lastStamps)
        let stopped = Self.deltas(probe.record(reduceMotion: true))
        print("MOTION_SHIMMER 扫 帧数=\(runningFrames.count) 变化帧对=\(Self.transitionFrameCount(running)) 峰值=\(String(format: "%.3f", Self.peak(running))) 采样≈\(interval)ms")
        print("MOTION_SHIMMER 停 变化帧对=\(Self.transitionFrameCount(stopped)) 峰值=\(String(format: "%.3f", Self.peak(stopped)))")
        try await requireObservableMotion()
        XCTAssertGreaterThan(Self.peak(running), Self.minimumVisibleChange,
                             "该扫的那一档什么都没变 ⇒ 扫光没落地（先看上面那行的帧数与尺寸，0 帧和 0 变化是两种病）")
        XCTAssertGreaterThanOrEqual(Self.transitionFrameCount(running), Self.minimumTransitionFrames,
                                    "只读到 \(Self.transitionFrameCount(running)) 对在变 ⇒ 那不是循环，是一次跳变")
        XCTAssertLessThan(Self.peak(stopped), Self.minimumVisibleChange,
                          "减弱动态那一档还在变 ⇒ 常驻动画没被门住（HIG 与 WCAG 2.3.3 要的就是这一条）")
    }

    /// **这把尺的边界探针**：一个自己会数数的 SwiftUI 视图（`@State` + 定时器驱动，
    /// 每 50ms 换一次文字并平移一个方块）。它该动，而且动的是一等公民属性（文字 + offset）。
    ///
    /// 它存在的理由：`testSkeletonSweepActuallySweeps` 读到"30 帧一帧不变"时，
    /// 有两种完全不同的解释 —— ① 这把尺看不见离屏 root 视图上的 `@State` 更新（尺的锅）；
    /// ② 扫光那条路没落地（产品的锅）。不先把 ① 排除掉，就不许把结论写进产品账本
    /// （账本里记过一整族"拿探针的故障当被测系统的故障"）。
    /// 两臂对照在这里反过来用：**已知该动的东西必须动**，否则尺子不合格。
    func testTheRulerSeesAStateDrivenSwiftUIUpdate() throws {
        try skipUnlessEnabledAndCapable()
        let frames = StateTickProbe().record()
        let fractions = Self.deltas(frames)
        print("MOTION_CONTROL 计数方块 帧数=\(frames.count) 峰值=\(String(format: "%.3f", Self.peak(fractions))) 变化帧对=\(Self.transitionFrameCount(fractions))")
        XCTAssertGreaterThan(Self.peak(fractions), Self.minimumVisibleChange,
                             "连一个每 50ms 换文字 + 平移方块的视图都量不到 ⇒ 这把尺看不见离屏 root 视图上的 @State 更新，"
                             + "所有'量不到'的结论都要改写成'测不了'，包括扫光那条")
        // 第二臂：只动渐变端点。它读成什么，决定 `SkeletonPreviewView` 那句话该怎么写。
        let gradient = StateTickProbe().record(gradient: true)
        let gradientFractions = Self.deltas(gradient)
        print("MOTION_CONTROL 渐变端点 帧数=\(gradient.count) 峰值=\(String(format: "%.3f", Self.peak(gradientFractions))) 变化帧对=\(Self.transitionFrameCount(gradientFractions))")
    }

    /// **这台机器能不能观察到"一次状态变更被分摊到几帧"** —— 用一个已知该动的视图问一次，缓存下来。
    ///
    /// 为什么需要：CI 的无头 runner 不绘制 SwiftUI 内容（82 帧里那两帧 95% 空白是既有事实），
    /// 于是"读不到动"有两种可能 —— 产品没动，或者这台机器看不见动。**把后者判成前者，
    /// 就是拿探针的故障当被测系统的故障**（账本里记过整族）。
    /// 所以新加的三条像素判据都先问这一句：问不出来就 `MOTION_NOT_RUN=` + skip，
    /// 而不是红，也不是绿。数字仍然先打出来，日志里永远有读数可查。
    private func requireObservableMotion() async throws {
        if let cached = Self.motionIsObservable {
            try XCTSkipIf(!cached, "MOTION_NOT_RUN=runner-cannot-observe-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
            return
        }
        let control = Self.deltas(StateTickProbe().record())
        let observable = Self.peak(control) > Self.minimumVisibleChange
        Self.motionIsObservable = observable
        if !observable {
            print("MOTION_NOT_RUN=runner-cannot-observe-motion 对照臂峰值=\(String(format: "%.4f", Self.peak(control)))")
        }
        try XCTSkipIf(!observable, "MOTION_NOT_RUN=runner-cannot-observe-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
    }

    /// 对照臂本身：**已知该动的东西必须动**。
    /// 它同时是上面那句 `requireObservableMotion` 的判据来源，所以它不 skip、只报数；
    /// 但如果这台机器连它都看不见，那结论只能是"测不了"（skip），不是"产品全坏了"。
    func testTheRulerSeesAStateDrivenSwiftUIUpdate() async throws {
        try skipUnlessEnabledAndCapable()
        let frames = StateTickProbe().record()
        let fractions = Self.deltas(frames)
        print("MOTION_CONTROL 计数方块 帧数=\(frames.count) 峰值=\(String(format: "%.3f", Self.peak(fractions))) 变化帧对=\(Self.transitionFrameCount(fractions))")
        let gradient = StateTickProbe().record(gradient: true)
        let gradientFractions = Self.deltas(gradient)
        print("MOTION_CONTROL 渐变端点 帧数=\(gradient.count) 峰值=\(String(format: "%.3f", Self.peak(gradientFractions))) 变化帧对=\(Self.transitionFrameCount(gradientFractions))")
        let observable = Self.peak(fractions) > Self.minimumVisibleChange
        Self.motionIsObservable = observable
        try XCTSkipUnless(observable,
                          "MOTION_NOT_RUN=runner-cannot-observe-motion：每 50ms 换文字 + 平移方块都量不到 ⇒ 这把尺在这台机器上看不见 @State 驱动的位移")
        XCTAssertGreaterThan(Self.transitionFrameCount(fractions), Self.minimumTransitionFrames,
                             "看得见变化但只分摊到一帧 ⇒ 这个视图的时钟没在跑，`requireObservableMotion` 会跟着失效")
    }

    // MARK: - 场景

    private struct Scenario {
        let name: String
        let size: NSSize
        /// 触发一次状态变更。`HistoryStore` 是 `@MainActor` 的，所以闭包也得是。
        let trigger: @MainActor (HistoryStore) -> Void
        /// 开窗**之前**先把界面摆到起点（比如"现在选中的是一条文本记录"）。
        /// 没有这一步就没法测"换类型才演"——因为夹具建完时的选中态是它自己决定的。
        let prepare: (@MainActor (HistoryStore) -> Void)?

        init(name: String, size: NSSize,
             prepare: (@MainActor (HistoryStore) -> Void)? = nil,
             _ trigger: @escaping @MainActor (HistoryStore) -> Void) {
            self.name = name
            self.size = size
            self.prepare = prepare
            self.trigger = trigger
        }

        /// 实例方法而不是 `static let`：闭包不是 `Sendable`，静态存储会被 Swift 6 判成共享可变状态。
        /// 只列**该有过渡**的场景。不该有的那些（侧栏行、同类型换字）在
        /// `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 与
        /// `testDetailPreviewCrossfadesOnlyWhenTheKindChanges` 里反向钉着。
        static func all() -> [Scenario] { [noticeBanner(), detailKindChange(), emptyState()] }

        static func listInsertNewRecord() -> Scenario {
            Scenario(name: "list-insert-new-record", size: NSSize(width: 760, height: 560)) { store in
                store.add(ClipboardIntake.Entry(
                    content: .text("动效取证：新进入列表的一条记录 \(UUID().uuidString.prefix(6))"),
                    thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                    sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                    timestamp: Date())
            }
        }

        static func promotionToTop() -> Scenario {
            Scenario(name: "promotion-to-top", size: NSSize(width: 760, height: 560)) { store in
                // 复制一条旧记录 ⇒ 它浮到最前。这是 M1 想教给用户的那件事。
                guard let last = store.filteredEntries.last else { return }
                store.perform(.copyAndPromote(last))
            }
        }

        static func noticeBanner() -> Scenario {
            Scenario(name: "notice-banner", size: NSSize(width: 760, height: 560)) { store in
                store.reportPasteFailure("系统未授权本 App 控制「System Events」，无法自动粘贴。")
            }
        }

        /// 文本 → 图片：整块预览被换掉，该有一次软交接。
        static func detailKindChange() -> Scenario {
            Scenario(name: "detail-kind-change", size: NSSize(width: 760, height: 560),
                     prepare: { store in store.perform(.selectOnly(plainTextEntries(store).first!)) }) { store in
                store.perform(.selectOnly(imageEntries(store).first!))
            }
        }

        /// 文本 → 文本：只换字，不该演。
        static func detailSameKind() -> Scenario {
            Scenario(name: "detail-same-kind", size: NSSize(width: 760, height: 560),
                     prepare: { store in store.perform(.selectOnly(plainTextEntries(store).first!)) }) { store in
                let texts = plainTextEntries(store)
                store.perform(.selectOnly(texts.count > 1 ? texts[1] : texts[0]))
            }
        }

        /// 清空 → 空态：整块列表被"没有记录"换掉。
        static func emptyState() -> Scenario {
            Scenario(name: "empty-state", size: NSSize(width: 380, height: 520)) { store in
                store.perform(.clear)
            }
        }

        static func searchReflow() -> Scenario {
            Scenario(name: "search-reflow", size: NSSize(width: 380, height: 520)) { store in
                store.perform(.updateSearch("记录 5"))
            }
        }

        /// 在**列表里**点某一行的收藏星：只换那一格里的符号，不动位置、不动选中。
        static func toggleFavoriteInRow() -> Scenario {
            Scenario(name: "row-favorite-star", size: NSSize(width: 760, height: 560)) { store in
                store.perform(.toggleFavorite(store.filteredEntries[3]))
            }
        }

        /// 空白对照：同一个窗口、同一个夹具，什么都不触发。
        static func blank() -> Scenario {
            Scenario(name: "blank", size: NSSize(width: 760, height: 560)) { _ in }
        }
    }

    /// 一次抓取：帧 + 每帧的时刻（判据说"几帧在动"，所以必须同时报出每帧多久）。
    private struct Film {
        let frames: [CGImage]
        let stamps: [TimeInterval]
    }

    private func record(_ scenario: Scenario) -> Film {
        let store = makeStore()
        scenario.prepare?(store)
        return recordFrames(scenario, store: store)
    }

    private func recordFrames(_ scenario: Scenario, store: HistoryStore) -> Film {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: scenario.size.width, height: scenario.size.height),
                              styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: ContentView(historyStore: store))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))

        let grabber = Grabber(view: host, limit: 30)

        // 抓帧的时钟就是**这个自旋循环本身**：runloop 每醒一次抓一张。
        //
        // 换掉两版驱动的原因都是实测：
        // - `CADisplayLink` 依附于"这台显示器正在刷新一帧"。本机显示器一休眠，
        //   `ticks` 就恒为 0，六条判据一起变成"只抓到 0 帧"（窗口、视图、
        //   `bitmapImageRepForCachingDisplay` 全都是好的）。
        // - `Timer` 看着与屏幕无关，但会被 App Nap / 合盖节流整批推迟：实测一次都不响。
        // 抓帧走 `cacheDisplay`（离屏合成，不需要屏幕在刷新），所以自旋驱动在任何
        // 显示状态下都成立。有效采样间隔仍然打印出来（`采样≈Nms`）——它由抓帧耗时决定，
        // 判据看的是"分摊到几帧"，所以这个时钟只要单调就够用。
        let prerollDeadline = Date().addingTimeInterval(0.15)
        while grabber.ticks < 3, Date() < prerollDeadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        scenario.trigger(store)
        let deadline = Date().addingTimeInterval(3.0)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        return Film(frames: grabber.frames, stamps: grabber.stamps)
    }

    /// 逐对帧的变化像素占比（每 7 个像素采一个，控制耗时）。
    private static func deltas(_ frames: [CGImage], band: CGRect? = nil) -> [Double] {
        let bitmaps = frames.map(raster)
        guard !bitmaps.isEmpty else { return [] }
        return (1..<bitmaps.count).map { changedFraction(bitmaps[$0 - 1], bitmaps[$0], band: band) }
    }

    /// 一张帧的像素。`width`/`height` 必须跟着走：没有它们就没法在二维上框区域，
    /// 而"整窗分数"会把一小块在动稀释成噪声（见 `band` 的注释）。
    private struct Bitmap {
        let pixels: [UInt8]
        let width: Int
        let height: Int
    }

    private static func raster(_ image: CGImage) -> Bitmap {
        let width = image.width, height = image.height
        var buffer = [UInt8](repeating: 0, count: width * height * 4)
        guard let space = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(data: &buffer, width: width, height: height, bitsPerComponent: 8,
                                      bytesPerRow: width * 4, space: space,
                                      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
            return Bitmap(pixels: [], width: 0, height: 0)
        }
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        return Bitmap(pixels: buffer, width: width, height: height)
    }

    /// 两张位图在 `band` 里有多少采样像素不同。
    ///
    /// `band` 是**归一化**矩形（0…1），坐标按"屏幕视角"给：`minY` 从窗口**顶边**往下算。
    /// 之所以要显式翻转：`CGBitmapContext` 的缓冲区第 0 行是它的**最低**一行，
    /// 也就是画面的底边 —— 不翻的话"列表中部"会框到窗口上方，量到的东西和名字对不上，
    /// 而这类错位不会让任何断言变红（它只是安静地量错地方）。
    /// `band = nil` 就是整窗。
    private static func changedFraction(_ a: Bitmap, _ b: Bitmap, band: CGRect?) -> Double {
        guard !a.pixels.isEmpty, a.pixels.count == b.pixels.count, a.width == b.width, a.height == b.height,
              a.width > 0, a.height > 0 else { return 0 }
        let xStart, xEnd, yStart, yEnd: Int
        if let band {
            xStart = max(0, Int(band.minX * CGFloat(a.width)))
            xEnd = min(a.width, Int(band.maxX * CGFloat(a.width)))
            yStart = max(0, Int((1 - band.maxY) * CGFloat(a.height)))
            yEnd = min(a.height, Int((1 - band.minY) * CGFloat(a.height)))
        } else {
            xStart = 0; xEnd = a.width; yStart = 0; yEnd = a.height
        }
        guard xEnd > xStart, yEnd > yStart else { return 0 }
        var changed = 0
        var sampled = 0
        var y = yStart
        while y < yEnd {
            var x = xStart
            while x < xEnd {
                let p = (y * a.width + x) * 4
                let d = max(abs(Int(a.pixels[p]) - Int(b.pixels[p])),
                            max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[p + 1])),
                                abs(Int(a.pixels[p + 2]) - Int(b.pixels[p + 2]))))
                if d > 8 { changed += 1 }
                sampled += 1
                x += 7
            }
            y += 7
        }
        return Double(changed) / Double(max(sampled, 1))
    }

    private func writeStrip(_ name: String, _ frames: [CGImage]) {
        guard frames.count > 1, let first = frames.first else { return }
        let cols = min(6, frames.count)
        let rows = (frames.count + cols - 1) / cols
        let fw = first.width / 2, fh = first.height / 2
        let canvas = CGRect(x: 0, y: 0, width: fw * cols, height: fh * rows)
        guard let space = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(data: nil, width: Int(canvas.width), height: Int(canvas.height),
                                      bitsPerComponent: 8, bytesPerRow: 0, space: space,
                                      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return }
        context.setFillColor(CGColor(red: 0.25, green: 0.25, blue: 0.28, alpha: 1))
        context.fill(canvas)
        for (index, frame) in frames.enumerated() {
            let rect = CGRect(x: CGFloat(index % cols) * CGFloat(fw),
                              y: canvas.height - CGFloat(index / cols + 1) * CGFloat(fh),
                              width: CGFloat(fw), height: CGFloat(fh))
            context.draw(frame, in: rect)
        }
        guard let out = context.makeImage() else { return }
        let data = NSBitmapImageRep(cgImage: out).representation(using: .png, properties: [:])
        try? data?.write(to: outDir.appendingPathComponent("\(name)-strip.png"))
    }

    // MARK: - 夹具

    /// 读产品源码（那半条"源码里不许出现不执行的声明"的判据要用）。
    /// 找不到文件必须红：守卫找不到被守卫的东西时，它就是空跑的。
    private func productSource(named relative: String) throws -> String {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + relative)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "MotionFilmstripTests", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红",
        ])
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func skipUnlessEnabledAndCapable() throws {
        try XCTSkipUnless(Self.isEnabled,
                          "动效胶片探针：设 CLIPBOARD_HISTORY_UI_MOTION=1 才跑（会抢前台并开窗）")
    }

    private static func insertProbeRecord(_ store: HistoryStore) {
        store.add(ClipboardIntake.Entry(
            content: .text("诊断用新记录 \(UUID().uuidString.prefix(6))"),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
            timestamp: Date())
    }

    private func makeStore() -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let image = try! makeStoredImage(color: .systemTeal, size: NSSize(width: 240, height: 140))
        for index in 0..<14 {
            store.add(ClipboardIntake.Entry(
                content: .text("动效取证记录 \(index)：一段用于观察列表重排与选中态过渡的文本"),
                thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"),
                timestamp: Date().addingTimeInterval(-Double(index) * 60))
        }
        store.add(ClipboardIntake.Entry(content: .image(image), thumbnail: image, sourceUTIs: ["public.png"],
                                        sourceAppBundleID: "com.apple.Preview", sourceAppName: "预览"),
                  timestamp: Date().addingTimeInterval(-3))
        return store
    }
}

/// 每帧抓一张。`CADisplayLink` 的回调是 `@Sendable` 语境，所以要 `assumeIsolated` 回主线程。
///
/// 每帧**新建**一张位图：`NSBitmapImageRep.cgImage` 是包着同一块缓冲的壳，
/// 复用 rep 会让上一帧的内容在下一拍被就地覆盖 —— 于是所有帧都一样、逐对差值恒为 0，
/// 一把"看起来在工作"的尺子其实什么也没量。采样间隔由 `stamps` 报出来，不够用时先看它。
@MainActor
private final class Grabber: NSObject {
    var frames: [CGImage] = []
    /// 每帧的时刻（`systemUptime`），用来报出有效采样间隔。
    var stamps: [TimeInterval] = []
    var ticks = 0
    var finished = false
    let limit: Int
    weak var view: NSView?

    init(view: NSView, limit: Int) {
        self.view = view
        self.limit = limit
        super.init()
    }

    func tick() {
        ticks += 1
        if let view,
           let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) {
            view.cacheDisplay(in: view.bounds, to: rep)
            if let cg = rep.cgImage {
                frames.append(cg)
                stamps.append(ProcessInfo.processInfo.systemUptime)
            }
        }
        if ticks >= limit { finished = true }
    }
}

// MARK: - AppKit 行动画探针

/// 一张**真 `NSTableView`** 的抓帧夹具，只为回答一个问题：这把尺看不看得见 AppKit 自己的
/// 行动画（`insertRows(at:withAnimation:)`）。
///
/// 为什么不复用产品的浮层：`QuickPickController.table` 是私有的，为了测试把面板暴露出去不划算；
/// 而"产品的接线对不对"由 `QuickPickRowDiffTests.testRebuildRowsIsWiredToTheAnimatedAPI` 钉住。这里只测尺子的能力，
/// 所以表头的**配置照抄产品**（view-based、rowHeight 34、同样的 cell 工厂）——
/// 因为"淡入"这件事本身就依赖行是有视图的：cell-based 的表把内容画进 frame view，
/// 没有可以逐行淡的图层，探针要是在那种形状上读到"看不见"，结论就归错了地方。
@MainActor
private final class TableProbe: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    private var texts: [String] = []
    /// 最近一次抓取的时刻序列：判据说"分摊到几帧"，而"几帧"要换算成毫秒才说得出时长。
    private(set) var lastStamps: [TimeInterval] = []

    /// 返回逐帧画面。`animation` 由调用方给**产品实际会传的那两个值**
    /// （`QuickPickController.rowAnimationOptions` 的两种输出），不是我另写的一份。
    func record(animation: NSTableView.AnimationOptions) -> [CGImage] {
        // 每次都从同一批行开始：上一次抓取插进来的行会让两臂的**起点**不同，
        // 而起点不同的对照量出来的差别，说不清是动画的还是布局的。
        texts = (1...6).map { "探针记录 \($0)：一行用来观察淡入的文字" }
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 300),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let table = NSTableView()
        table.addTableColumn(NSTableColumn(identifier: NSUserInterfaceItemIdentifier("probeColumn")))
        table.headerView = nil
        table.rowHeight = 34
        table.backgroundColor = .clear
        table.dataSource = self
        table.delegate = self
        let scroll = NSScrollView()
        scroll.documentView = table
        scroll.hasVerticalScroller = false
        window.contentView = scroll
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))

        let grabber = Grabber(view: scroll, limit: 24)
        let prerollDeadline = Date().addingTimeInterval(0.15)
        while grabber.ticks < 3, Date() < prerollDeadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        // 先改模型、再告诉表格插了哪一行：`insertRows` 当场就会回读 `numberOfRows` 和新行内容。
        texts.insert("刚插进来的一行：它该淡入而不是把别人挤一下就算完", at: 2)
        table.insertRows(at: IndexSet(integer: 2), withAnimation: animation)
        let deadline = Date().addingTimeInterval(2.0)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        lastStamps = grabber.stamps
        return grabber.frames
    }

    /// 产品形状的那一拍：`rebuildRows()` 插完行之后，`queryChanged` 紧跟着会做
    /// `selectRowIndexes` + `scrollRowToVisible`（`selectCurrentRow()` 那两句）。
    /// 这一臂回答一个问题：**那两句会不会把刚起的行动画吃掉。**
    ///
    /// 答案是"看选中有没有真的变"：
    /// - `selectionChanges: true`（写一个别的行）⇒ 行动画被吃掉（1 对，峰值 0.129）；
    /// - `selectionChanges: false`（打字时的真实形状：下标恒为 0，写的是**同一个**行）
    ///   ⇒ 动画活着（11 对，峰值 0.028，和完全不写选中一样）。
    /// 也就是说产品不需要为此改代码：AppKit 自己短路了重复的选中写入。
    /// 而"把它推到下一拍"和 `CATransaction.setDisableActions(true)` 两条都**救不回来**
    /// （各臂数字见 D-056），所以那两条路都没走。
    func recordProductSequence(selectionChanges: Bool) -> [CGImage] {
        texts = (1...6).map { "探针记录 \($0)：一行用来观察淡入的文字" }
        let target = selectionChanges ? 4 : 0
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 300),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let table = NSTableView()
        table.addTableColumn(NSTableColumn(identifier: NSUserInterfaceItemIdentifier("probeColumn")))
        table.headerView = nil
        table.rowHeight = 34
        table.backgroundColor = .clear
        table.dataSource = self
        table.delegate = self
        let scroll = NSScrollView()
        scroll.documentView = table
        scroll.hasVerticalScroller = false
        window.contentView = scroll
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))
        // 起点必须已经是选中第 0 行 —— 否则"写同一个选中"这一臂就不成立
        // （从"没选中"到"选中 0"本身就是一次真的选中变化）。
        table.selectRowIndexes(IndexSet(integer: 0), byExtendingSelection: false)
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))

        let grabber = Grabber(view: scroll, limit: 400)
        let prerollDeadline = Date().addingTimeInterval(0.15)
        while grabber.ticks < 3, Date() < prerollDeadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        texts.insert("刚插进来的一行：它该淡入而不是把别人挤一下就算完", at: 2)
        table.insertRows(at: IndexSet(integer: 2), withAnimation: .effectFade)
        table.selectRowIndexes(IndexSet(integer: target), byExtendingSelection: false)
        table.scrollRowToVisible(target)
        let deadline = Date().addingTimeInterval(2.5)
        while !grabber.finished, Date() < deadline {
            // 与 `record(animation:)` **同一个采样节奏**：两臂要能横比，
            // 否则"帧对少了"可能只是"每帧更长了"。
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        lastStamps = grabber.stamps
        return grabber.frames
    }

    func numberOfRows(in tableView: NSTableView) -> Int { texts.count }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let identifier = NSUserInterfaceItemIdentifier("probeCell")
        let cell = (tableView.makeView(withIdentifier: identifier, owner: self) as? NSTableCellView) ?? {
            let text = NSTextField(labelWithString: "")
            text.lineBreakMode = .byTruncatingTail
            text.font = .systemFont(ofSize: 13)
            text.identifier = identifier
            let created = NSTableCellView()
            created.addSubview(text)
            created.textField = text
            text.translatesAutoresizingMaskIntoConstraints = false
            NSLayoutConstraint.activate([
                text.leadingAnchor.constraint(equalTo: created.leadingAnchor, constant: 6),
                text.trailingAnchor.constraint(equalTo: created.trailingAnchor, constant: -6),
                text.centerYAnchor.constraint(equalTo: created.centerYAnchor),
            ])
            return created
        }()
        cell.textField?.stringValue = texts[row]
        return cell
    }
}

// MARK: - 骨架扫光探针

/// 在离屏窗口里 host 一个 `SkeletonPreviewView`，连抓 30 帧。
///
/// 为什么不通过 `DetailFileView` 走：那条路要真去读一个文件的预览，`MediaLoader` 什么时候回来
/// 由磁盘和 QuickLook 决定 —— 拿它做"这段里有没有连续变化"的判据，红绿会跟着机器状态漂。
/// 这里量的是**这把尺能不能看见渐变位移**；"骨架接在加载分支上"那半条由
/// `SkeletonMotionTests.testSkeletonIsWiredIntoTheDetailLoadingBranch` 钉住。
@MainActor
private final class SkeletonProbe {
    private(set) var lastStamps: [TimeInterval] = []

    func record(reduceMotion: Bool) -> [CGImage] {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 220),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: SkeletonPreviewView(reduceMotion: reduceMotion))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        // 少等一点：`onAppear` 里起的就是这个循环，等久了只是多烧几帧，判据不变。
        RunLoop.main.run(until: Date().addingTimeInterval(0.25))
        // **抓够 2.5 秒，而不是抓够 30 帧。**
        // 这一条是量出来之后才发现的：这张图很小，`cacheDisplay` 一拍只要 4ms，
        // 于是"30 帧"只覆盖 120ms —— 而扫光一圈是 1.5 秒，120ms 里亮带只走 8%，
        // 分摊到每对帧的变化面积远在噪声地板以下。第一版据此读到"峰值 0.000"，
        // 差点把结论写成"这把尺看不见渐变动画"，而实际是**胶片太短**。
        // 采样间隔仍然打印出来（`采样≈Nms`），但它只说明"每帧多久"，不说明"总共看了多久"。
        let grabber = Grabber(view: host, limit: 400)
        let deadline = Date().addingTimeInterval(2.5)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            grabber.tick()
        }
        lastStamps = grabber.stamps
        return grabber.frames
    }
}

// MARK: - 尺子边界对照：自己会动的 SwiftUI 视图

/// 每 50ms 换一次数字、并把方块往右挪 12pt。动的是 `Text` 内容与 `.offset` ——
/// 这两样都不依赖渐变、不依赖符号图层，是这把尺**最应该**看得见的东西。
@MainActor
private struct TickCounterView: View {
    @State private var tick = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("tick \(tick)")
                .font(.system(size: 44, weight: .bold))
            RoundedRectangle(cornerRadius: 4)
                .fill(Color.accentColor)
                .frame(width: 60, height: 24)
                .offset(x: CGFloat(tick % 12) * 12)
        }
        .padding(16)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .onReceive(Timer.publish(every: 0.05, on: .main, in: .common).autoconnect()) { _ in
            tick += 1
        }
    }
}

@MainActor
private final class StateTickProbe {
    func record() -> [CGImage] { record(gradient: false) }

    /// `gradient: true` 时换一张**只动渐变端点**的图 —— 用来分清"尺看不见 @State 更新"
    /// 与"尺看不见渐变端点的移动"，这两句写错一句就会把产品判成死的（或反过来）。
    func record(gradient: Bool) -> [CGImage] {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 220),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: gradient ? AnyView(GradientTickView()) : AnyView(TickCounterView()))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.25))
        let grabber = Grabber(view: host, limit: 400)
        let deadline = Date().addingTimeInterval(2.0)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            grabber.tick()
        }
        return grabber.frames
    }
}

/// 只动 `LinearGradient` 的两个端点，其它一切都不动。
@MainActor
private struct GradientTickView: View {
    @State private var phase: CGFloat = 0

    var body: some View {
        skeleton(phase: phase)
            .onReceive(Timer.publish(every: 0.05, on: .main, in: .common).autoconnect()) { _ in
                phase = SkeletonMotion.advance(phase, by: 0.05)
            }
    }

    /// 与 `SkeletonPreviewView` **同一套画法**（GeometryReader + ForEach + 渐变填充），
    /// 只有驱动方式不同：这里是视图自己的 `@State`。
    /// 分成两个视图而不是只测一个，是为了把"驱动方式"和"画法"这两个嫌疑分开 ——
    /// 否则读到不动时，仍然不知道该改时钟还是该改布局。
    private func skeleton(phase: CGFloat) -> some View {
        GeometryReader { proxy in
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(SkeletonMotion.barFractions.enumerated()), id: \.offset) { _, fraction in
                    RoundedRectangle(cornerRadius: 4)
                        .fill(LinearGradient(
                            stops: [.init(color: .primary.opacity(0.06), location: 0),
                                    .init(color: .primary.opacity(0.45), location: 0.5),
                                    .init(color: .primary.opacity(0.06), location: 1)],
                            startPoint: SkeletonMotion.unitPoints(phase: phase).start,
                            endPoint: SkeletonMotion.unitPoints(phase: phase).end))
                        .frame(width: max(1, proxy.size.width * fraction), height: 8)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }
}

// MARK: - 场景夹具用的筛选

/// 「有没有图片」这个判断留在测试侧：为了写断言往 `HistoryStore` 上加一个 `imageEntries`
/// 是拿产品 API 换测试方便，不划算。
@MainActor private func plainTextEntries(_ store: HistoryStore) -> [ClipboardEntry] {
    store.entries.filter { if case .text = $0.content { return true }; return false }
}

@MainActor private func imageEntries(_ store: HistoryStore) -> [ClipboardEntry] {
    store.entries.filter { if case .image = $0.content { return true }; return false }
}
