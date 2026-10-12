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

// MARK: - 场景夹具用的筛选

/// 「有没有图片」这个判断留在测试侧：为了写断言往 `HistoryStore` 上加一个 `imageEntries`
/// 是拿产品 API 换测试方便，不划算。
@MainActor private func plainTextEntries(_ store: HistoryStore) -> [ClipboardEntry] {
    store.entries.filter { if case .text = $0.content { return true }; return false }
}

@MainActor private func imageEntries(_ store: HistoryStore) -> [ClipboardEntry] {
    store.entries.filter { if case .image = $0.content { return true }; return false }
}
