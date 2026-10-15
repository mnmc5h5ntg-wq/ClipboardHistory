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

    /// `requireObservableMotion` 的缓存（每一类位移各一个判定）。
    /// `nonisolated(unsafe)` 是因为它只在主线程的测试里读写（整个类是 `@MainActor`）。
    nonisolated(unsafe) static var observableCache: [MotionClass: Bool] = [:]
    /// 淡入时钟探针跑一次就缓存（R66）。与上面同一个理由：这是**环境属性**，
    /// 不会在一卷测试跑到一半时变好；而它一次要 2 秒，让它跟着每条判据各跑一遍，
    /// 就是拿"这条判据跑得完吗"去换"这条判据说得准吗"。
    nonisolated(unsafe) static var fadeClockCache: FadeClockReading?

    /// 胶片与读数共用的输出目录（R56：两条证据通道必须住在同一个地方，见 `readingsURL`）。
    private static var filmsDirectory: URL {
        let url = URL(fileURLWithPath: ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_MOTION_OUT"]
            ?? "/tmp/motion-films", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    private var outDir: URL { Self.filmsDirectory }

    // MARK: - 读数的第二条通道（R56 / BACKLOG 79）

    /// 读数的**第二条通道**：与胶片同一个目录里的一个文件。
    ///
    /// 为什么要有它：CI run 38543090198 与本机 2026-10-14 18:58 那一次是同一种坏法 ——
    /// 测试全过、stderr 一切正常、**胶片 9 张写出来了**，而 `print` 的读数一行不剩。
    /// 也就是说 **FileManager 那条路活着，stdout 那条死了**。
    /// 而覆盖率地板、R55 的归因、`MOTION_SUMMARY` 的键集合，全都住在会死的那条上。
    /// 所以读数从现在起**同时**进文件：这不是"多打一份日志"，是让"这一天的判据"
    /// 不再依赖一条已知会整次消失的通道。
    static var readingsURL: URL {
        filmsDirectory.appendingPathComponent("motion-readings.log")
    }

    /// 每个进程第一次写要**整份重写**：上一遍的读数冒充这一遍，比没有读数更坏
    /// （`MOTION_RESOLVE_SUMMARY judged=4/4` 会是从昨天带上来的）。
    nonisolated(unsafe) static var readingsOpened = false

    /// 实例侧的同名转发。Swift 不允许实例方法不加限定地调静态成员（编译期就挡），
    /// 而 44 处读数散在两种语境里 —— 与其到处写 `Self.emit`，不如让两条语境共用一个名字。
    private func emit(_ line: String) { Self.emit(line) }

    /// 打一行读数，**并且**把它记进文件通道。所有 `MOTION_*` 行都必须走这里
    /// （`testMotionReadingsUseTheFileChannel` 钉着这条规矩）。
    static func emit(_ line: String) {
        print(line)
        guard let payload = (line + "\n").data(using: .utf8) else { return }
        let url = readingsURL
        do {
            if !readingsOpened {
                readingsOpened = true
                try payload.write(to: url)
                return
            }
            let handle = try FileHandle(forWritingTo: url)
            handle.seekToEndOfFile()
            handle.write(payload)
            try? handle.close()
        } catch {
            // 文件通道坏了**不许**把判据变成红（那是拿环境问题判产品）。
            // 但它必须被看见。这一行为什么故意不叫 `MOTION_*`：它不是一条读数，而是
            // "文件通道坏了"这件事本身，且只能走 stdout。带上 MOTION_ 前缀就会被
            // `testMotionReadingsUseTheFileChannel` 的扫描判成"有条读数没进文件"——
            // 而那正是它要抓的形状，所以这条元信息**不能**借用读数的命名空间
            // （否则任何人加一行 `print("MOTION_…")` 都能把那条扫描变成恒红，或者反过来
            //  逼守卫开一个"例外名单"，例外名单就是这种规矩腐烂的地方）。
            // 通道坏的真信号在下一步：文件里没有结论行，CI 会打 `MOTION_READINGS_FILE_ABSENT=1`。
            print("READINGS_FILE_FAILED=\(type(of: error)) 路径=\(url.path)")
        }
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

    /// 从触发到"落定"要几帧这件事，由 `settledAtFrame(_:band:)` 回答（R2）——
    /// 它返回**帧号**，调用方乘以实测采样间隔得到毫秒，于是判据表达的是时间而不是帧数。
    /// 这里以前是一个"预卷之后还有几帧在动"的计数器：它的两个上限（`>1`、`≤6`）都是帧数，
    /// 而一帧是 31ms 还是 90ms 取决于抓帧耗时，所以同一条判据在两种时钟下一个松一个紧。

    static func peak(_ fractions: [Double]) -> Double { fractions.max() ?? 0 }

    /// 两块区域比"什么时候停"，必须用**同一条绝对线**（R59）。
    ///
    /// 为什么不是 `transitionFrameCount`：它的门槛是**各自峰值**的 `stepFloorRatio`，
    /// 两块各自归一化 ⇒ 峰值大的那块被一条更高的绝对线先判停。
    /// 本机实测的分栏卷：侧栏峰值 0.305 ⇒ 线 = 0.046；详情区峰值 0.237 ⇒ 线 = 0.036，
    /// 于是**墨多的那一栏永远显得先落定**。拿它做分栏对比，量的是墨量，不是时间。
    /// 这里用两块峰值里较大的那个 × 同一个比例 —— 一条线，套在两栏上。
    static func sharedMovingFloor(_ regions: [[Double]]) -> Double {
        (regions.map { peak($0) }.max() ?? 0) * stepFloorRatio
    }

    /// 同一条线下"最后一个还在变的帧号"；`nil` = 这一块在这条线下没有任何一次可见变化。
    static func lastMovingFrame(_ fractions: [Double], floor: Double) -> Int? {
        guard peak(fractions) >= minimumVisibleChange else { return nil }
        // 第二道地板管的是**共享线自己塌到 0**：两栏全零时线也是 0，而 `0 >= 0`
        // 会让每一帧都算"还在变"，"作废"那格反而报成"两栏都动到最后一帧"
        // —— 真值表的 (c) 第一次就是这么红的。
        return fractions.lastIndex { $0 >= max(floor, minimumVisibleChange) }
    }

    /// 分栏落定时刻那句话**由数字生成**，不由"我看图看到了什么"生成（R59）。
    ///
    /// 为什么单独一个纯函数：本轮的教训正是"读数写成了结论"（`差 2–5 帧 ⇒ 侧栏先落定`），
    /// 而那 2–5 帧是各自峰值归一的产物。措辞进了函数，就能被真值表钉住
    /// （见 `testSharedFloorColumnComparisonIsATruthTable`）。
    /// **不覆盖管线**：这条合成的是**尺子的措辞**，产品那一条是
    /// `testBannerDismissColumnAsymmetryIsMeasured`，它跑的是真卷。
    static func columnSettlementVerdict(left: [Double], right: [Double]) -> String {
        let floor = sharedMovingFloor([left, right])
        let lastLeft = lastMovingFrame(left, floor: floor)
        let lastRight = lastMovingFrame(right, floor: floor)
        switch (lastLeft, lastRight) {
        case (nil, nil):
            return "两栏在这条线下都没有变化(线=\(String(format: "%.4f", floor))，"
                + "峰值 \(String(format: "%.3f", peak(left))) / \(String(format: "%.3f", peak(right))))"
                + " ⇒ 这条对比作废，不许据此说任何一栏先落定"
        case (nil, let r?):
            return "只有详情区在变(第\(r)帧)，侧栏一次都没有 ⇒ 分界线/框选算错了，对比作废"
        case (let l?, nil):
            return "只有侧栏在变(第\(l)帧)，详情区一次都没有 ⇒ 分界线/框选算错了，对比作废"
        case (let l?, let r?):
            let diff = r - l
            if diff == 0 {
                return "同一条绝对线下两栏在**同一帧**落定(第\(l)帧，线=\(String(format: "%.4f", floor)))"
                    + " ⇒ 观察到的不是时长差；各自的峰值归一尺子会给出不同的帧数，那是墨量"
            }
            return "同一条绝对线下差 \(abs(diff)) 帧（侧栏第\(l)帧 / 详情区第\(r)帧，"
                + "线=\(String(format: "%.4f", floor))) ⇒ 时间轴上确实有先后，"
                + "谁先谁后由帧号决定，不由看图的感觉决定"
        }
    }

    /// "画面还在变"覆盖了多长**时间**（ms），而不是几帧 —— 但注意：这是**首尾跨度**，不是连续的一段。
    ///
    /// 为什么是时间不是帧数（R2）：`transitionFrameCount` 数的是帧，而一帧多长由抓帧耗时决定。
    /// R2 把判据的**要求**换成了时间，但**读数**仍然是帧数，于是它跟着采样相位漂：
    /// 本机实测同一份代码三次跑出 `2 / 3 / 2`（HEAD 上也给过 2）。
    ///
    /// 为什么改名（R48）：名字里的 "run" 是假的 —— 它取的是
    /// 「第一个还在变的帧 → 最后一个还在变的帧之后一帧」，**不要求中间连续**。
    /// 本机 R46/R47 抓到过 `时长=265ms 帧数=2 整卷中位=8ms`：两帧连续变化最多覆盖 8–16ms，
    /// 265ms 只能来自"两波变化中间隔着一段静止"。所以那条读数说的"淡入演了 265ms"
    /// 是**尺子的算法造出来的**，不是画面给的（BACKLOG 70）。
    ///
    /// 要"一段连续的过程"请用 `contiguousChangedRun`。这里保留跨度语义是有意的：
    /// R2 那批夹具（含 `coarseSampling` 那种中间掉回 0.001 的形状）就是按跨度写的，
    /// 而那个形状本身在真机上是否可能，需要逐条重问 —— 那是 BACKLOG 72，不在本轮顺手改。
    /// 返回 `nil` = 整段没有一次可见变化 ⇒ 无从判定，调用方必须报 not-run，不许判绿。
    static func changedSpanElapsedMilliseconds(stamps: [TimeInterval], fractions: [Double]) -> Double? {
        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return nil }
        let moving = fractions.indices.filter { fractions[$0] >= peak * stepFloorRatio }
        guard let first = moving.first, let last = moving.last,
              first < stamps.count, last + 1 < stamps.count else { return nil }
        // `fractions[i]` 是"第 i 帧 → 第 i+1 帧"之间的变化，所以这段变更覆盖
        // stamps[first] 到 stamps[last + 1] 这段时间。
        return max(0, (stamps[last + 1] - stamps[first]) * 1000)
    }

    /// 一段**连续**的变化（R48 / BACKLOG 70）。
    struct ChangedRun: Equatable {
        /// 这一段第一个变化帧的下标（`fractions[start]` = 该帧到下一帧的变化量）
        let startFrame: Int
        /// 这一段最后一个变化帧的下标；这一段时间覆盖 `stamps[startFrame] … stamps[endFrame + 1]`
        let endFrame: Int
        let peak: Double
        let elapsedMilliseconds: Double
        /// 这一段内部**最粗的一次采样间隔**（ms）。
        /// R48 加这个字段是因为一条真读数：`时长=266ms 帧数=2 整卷中位=7ms` ——
        /// 时长不是被"过程很长"撑出来的，是被段内**一次 260ms 的抓帧空档**撑出来的（整卷中位只有 8ms）。
        /// 没有这一项，`elapsed` 与"声明 160ms"的比较就是在拿被卡住的钟量动画。
        let worstIntervalMilliseconds: Double
    }

    /// 把整卷切成**连续**的变化段：相邻的 `fractions[i] ≥ 峰值 × stepFloorRatio` 才算同一段，
    /// 中间掉下去一次就断成两段。
    ///
    /// 为什么需要它（而不是把上面那个函数直接改掉）：一条淡入的**时长**必须来自"它一直在演"的那一段。
    /// 跨度算法会把「触发后 7ms 内演完 + 静止 250ms + 别的东西又动了一下」读成 258ms 的淡入，
    /// 于是任何"时长在声明附近"的判据都会被一次无关的抖动喂成绿 —— 那是把探针的毛病当产品进步。
    static func contiguousChangedRuns(stamps: [TimeInterval], fractions: [Double]) -> [ChangedRun] {
        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return [] }
        let floor = peak * stepFloorRatio
        var runs: [ChangedRun] = []
        var start: Int?
        // 多走一格（`index == fractions.count` 时 `moving` 必为 false）当**收尾哨兵**，
        // 这样"最后一段一直变到卷尾"也能被正常闭合，不用在循环外再抄一遍收尾逻辑。
        for index in 0...fractions.count {
            let moving = index < fractions.count && fractions[index] >= floor
            if moving {
                if start == nil { start = index }
                continue
            }
            guard let from = start else { continue }
            let through = index - 1
            start = nil
            // 越界就不记这一段：宁可少一段让调用方报 not-run，也不许拿一个算不出时长的段冒充读数。
            guard from < stamps.count, through + 1 < stamps.count else { continue }
            // 段内最粗的一次采样：`stamps[k] → stamps[k+1]`，k 从 from+1 到 through+1。
            // 与 `worstIntervalInsideChangedRun` 同一个取法（用最大值不用中位数：
            // 决定分辨率的是过程正在演的那一段里最稀的一次）。
            var worst: Double = 0
            for k in (from + 1)...(through + 1) {
                worst = max(worst, (stamps[k] - stamps[k - 1]) * 1000)
            }
            runs.append(ChangedRun(
                startFrame: from, endFrame: through,
                peak: fractions[from...through].max() ?? 0,
                elapsedMilliseconds: max(0, (stamps[through + 1] - stamps[from]) * 1000),
                worstIntervalMilliseconds: worst))
        }
        return runs
    }

    /// **包含峰值**的那一段连续变化（R48）。
    ///
    /// 为什么是"含峰值"而不是"最长"：一卷里可能既有淡入又有一次晚到的抖动，
    /// 抖动那一段可能因为采样稀而覆盖更久；判"这条过渡演了多久"必须看动画真正在演的那一段。
    /// 返回 `nil` = 整卷没有可见变化 ⇒ 无从判定（调用方必须报 not-run，不许判绿）。
    static func contiguousChangedRun(stamps: [TimeInterval], fractions: [Double]) -> ChangedRun? {
        contiguousChangedRuns(stamps: stamps, fractions: fractions)
            .max { $0.peak == $1.peak ? $0.elapsedMilliseconds < $1.elapsedMilliseconds : $0.peak < $1.peak }
    }

    /// 原生行**移动**那一条 A/B 的结论（R50 / BACKLOG 75）。
    enum NativeMoveVerdict: Equatable {
        /// 开臂明显比对照臂多帧 ⇒ 移动在动。
        case animated
        /// 两臂形状一致（帧数与峰值都相同）⇒ 这一次移动是**瞬移**。
        /// 这一格是产品侧的结论，红得起：同一卷里 `row-insert` 看得见，
        /// 所以"通道瞎了"这个解释已经被排掉一半，另一半由 `wasActive` 排掉。
        case notAnimated(animatedSpan: Int, animatedPeak: Double, instantSpan: Int, instantPeak: Double)
        /// 帧数都是 1 但峰值不一样 ⇒ 说不清是没动还是采样错过，**不判产品**。
        case samplingMissed(animatedSpan: Int, animatedPeak: Double, instantSpan: Int, instantPeak: Double)
    }

    /// 两臂峰值差多少以内算"形状一致"。与 `fadeVisibility` 那条 A/B 用的是同一个量级：
    /// 峰值差小于这个数时，两卷看起来就是同一件事发生了一次。
    static let nativeMovePeakTolerance: Double = 0.02

    static func nativeMoveVerdict(animatedSpan: Int, animatedPeak: Double,
                                  instantSpan: Int, instantPeak: Double,
                                  minimumFrames: Int = 2) -> NativeMoveVerdict {
        if animatedSpan >= minimumFrames { return .animated }
        let sameShape = abs(animatedPeak - instantPeak) <= nativeMovePeakTolerance
        return sameShape
            ? .notAnimated(animatedSpan: animatedSpan, animatedPeak: animatedPeak,
                           instantSpan: instantSpan, instantPeak: instantPeak)
            : .samplingMissed(animatedSpan: animatedSpan, animatedPeak: animatedPeak,
                              instantSpan: instantSpan, instantPeak: instantPeak)
    }

    /// 这条 A/B 有没有看见纯 opacity 的淡入（R47 / BACKLOG 68 / U-73，R48 补分辨率轴）。
    ///
    /// 为什么单独抽出来：`testHeatmapFadeIsNotVisibleToThisRuler` 原来直接写
    /// `onSpan == offSpan && |peak(on) - peak(off)| < 0.02` —— 第一个条件用的是**帧数**，
    /// 而帧数正是本文件上面自己宣布过"会随采样相位漂"的量（R2：同一份代码本机跑过 2/3/2）。
    ///
    /// **本轮撤回一句旧结论**：R11/R47 的台账把这条通道写成"对纯 opacity 淡入可见性 = 0"。
    /// R48 给这条 A/B 第一次补上条带图（`heat-first-record-开A-strip.png`），
    /// 第 3 帧是**半透明中间态**（空态那行字与整块日历叠在一起）⇒ 这条通道看得见这条淡入，
    /// 只是不每次都抓得到：抓帧占空比决定它今天能不能看见。
    /// 所以正确的形状是三态，不是两态：看见了 / 没看见 / **今天的钟粗到判不了**。
    /// 把第三态并进第二态，就是本轮那条 266ms 读数干的事（它连"看不见"都没资格说）。
    enum FadeVisibility: Equatable {
        /// 触发没让图长出来 ⇒ 探针坏了。两种结论都不许下（既不许说看得见，也不许说看不见）。
        case noControl
        /// 看不见 ⇒ 记「源码已接、产物未量」，不许写进已交付，也不许反过来判产品没做。
        case notVisibleToThisRuler
        /// 两遍同臂互相矛盾 ⇒ 这条通道今天没有结论。报矛盾，不许挑一次算数。
        case inconsistent(onA: Double?, onB: Double?)
        /// 段内最粗的一次采样比声明还粗到判不了 ⇒ **今天既不能说看得见也不能说看不见**（R48）。
        /// 与 `judgeMotion` 的 `.clockTooCoarse` 同一个意思：钟卡住的时长读数没有资格参与判定。
        case clockTooCoarse(worstOnA: Double, worstOnB: Double)
        /// 两遍都说看得见 ⇒ 调用方必须把这个场景放回 `Scenario.all()` 当真判据。
        case visibleToThisRuler
    }

    /// "一段变化够长才算看得见"的门槛：声明时长的这个比例。
    /// 与 `judgeMotion` 里那句"事件内最粗采样 > 0.3×声明 ⇒ 时钟太粗"是同一把分辨率尺，
    /// 两处用同一个数，是为了让"切不出过程"与"看见了过程"不会各说各话。
    private static let coarseRunRatio = 0.3

    /// 段内最粗采样超过声明的这个比例 ⇒ 这条通道的钟粗到没法拿时长当判据。
    /// 沿用 `judgeMotion` 中间档的上限（0.5）：那里 0.3–0.5 还能靠"至少两帧在变"判，
    /// 而这条 A/B 的判据**只有时长一个量**，所以直接到 0.5 就放弃判定。
    private static let unresolvableIntervalRatio = 0.5

    /// 单臂：这一次有没有看见一段**属于这条淡入的**"还在变"的时间。`nil` = 这一臂没有对照物。
    ///
    /// 两个门槛，不是一個：
    /// * 下限 `0.3×声明` —— 短于此就是一帧跳变，切不出"过程"这个概念；
    /// * 上限 `声明 + 2×采样间隔` —— **一段比声明还长出一截的变化不是这条动画**。
    ///   这条是 R47 被实测逼出来的：本机反复抓到一段 `258–260ms` 的变化段
    ///   （声明只有 160ms），而它一次进程只出现一次、出现在第几遍抓取上不固定 ——
    ///   那更像账本去抖落盘/首次布局，不是 opacity 淡入。
    ///   只设下限的话，这段别的变化会被读成"这把尺终于看见淡入了"，
    ///   然后那条判据会催我把场景放进 `Scenario.all()` —— 那是把探针的毛病当产品进步。
    private static func fadeSawProcess(elapsed: Double?, peakOn: Double,
                                       declaredMilliseconds: Double,
                                       intervalMilliseconds: Double) -> Bool? {
        guard peakOn >= minimumVisibleChange else { return nil }
        guard let elapsed else { return false }      // 读不出变化段 = 没看见，不是"看不见也算数"
        return elapsed >= declaredMilliseconds * coarseRunRatio
            && elapsed <= declaredMilliseconds + 2 * max(intervalMilliseconds, 1)
    }

    /// 注意这里**故意不收** `peakOff`：关掉曲线之后如果那一臂整段都没变化
    /// （`peakOff` 低于地板），那恰恰说明"变化是动画带来的"——它是证据，不是反例。
    /// 一个不进判定的参数留在签名里，只会让下一个读这段代码的人以为它参与了判定。
    static func fadeVisibility(elapsedOnA: Double?, elapsedOnB: Double?, elapsedOff: Double?,
                               peakOn: Double,
                               declaredMilliseconds: Double,
                               intervalMilliseconds: Double,
                               worstOnA: Double = 0,
                               worstOnB: Double = 0) -> FadeVisibility {
        guard let a = fadeSawProcess(elapsed: elapsedOnA, peakOn: peakOn,
                                     declaredMilliseconds: declaredMilliseconds,
                                     intervalMilliseconds: intervalMilliseconds),
              let b = fadeSawProcess(elapsed: elapsedOnB, peakOn: peakOn,
                                     declaredMilliseconds: declaredMilliseconds,
                                     intervalMilliseconds: intervalMilliseconds)
        else { return .noControl }
        // 分辨率门放在一致性**之前**：钟卡住的时候两个时长读数没有可比的量纲，
        // 拿它们比"矛不矛盾"是在给一个没测到的东西编结论。
        // `worst == 0` = 调用方没测这一项（真值表里那些格子就是这种），不参与这道门。
        if declaredMilliseconds > 0,
           max(worstOnA, worstOnB) > declaredMilliseconds * unresolvableIntervalRatio {
            return .clockTooCoarse(worstOnA: worstOnA, worstOnB: worstOnB)
        }
        if a != b { return .inconsistent(onA: elapsedOnA, onB: elapsedOnB) }
        guard a else { return .notVisibleToThisRuler }
        // 归因那一半：开着曲线的**两臂都**要比"关掉曲线"的对照臂长出至少一个采样间隔，
        // 否则这段"还在变"不是动画带来的（可能是重排、图片解码、落定抖动）。
        guard let off = elapsedOff, let first = elapsedOnA, let second = elapsedOnB else {
            return .notVisibleToThisRuler
        }
        return min(first, second) - off >= intervalMilliseconds
            ? .visibleToThisRuler : .notVisibleToThisRuler
    }

    /// 把窗口切成 cols×rows 的格子，打印"峰值那一格里每格的变化量"——用来回答
    /// "到底哪里变了"，而不是靠猜像素坐标去框区域（猜错的结果是整条判据读到 0.000，
    /// 看着像"没动"，其实是我没框到）。
    static func changeGrid(_ frames: [CGImage], index: Int, cols: Int, rows: Int) -> String {
        changeGrid(bitmaps: frames.map(raster), index: index, cols: cols, rows: rows)
    }

    /// 位图版才是真正干活的那个 —— 拆出来只为了**行序能被合成用例钉住**（BACKLOG 84）：
    /// R58 之前它第 0 行打印的是窗口底部，而它只输出字符串、不参与任何断言，
    /// 所以那半年里所有按**行**读过的网格都得重看一遍才敢引用。
    private static func changeGrid(bitmaps: [Bitmap], index: Int, cols: Int, rows: Int) -> String {
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

    // MARK: - 采样率感知（R2：判据表达的是时间，不是帧号）

    /// 这段过渡在这把尺下**最多**能被切成几帧。
    /// 抓帧是同步 `cacheDisplay`，间隔由抓取耗时决定：本机实测在 31–90ms 之间漂，
    /// 而声明的过渡只有 150–160ms —— 所以"过渡帧数 ≥3"这种写法量的其实是抓帧耗时。
    ///
    /// `nonisolated`（R68）：这是一条纯算术判据，而 `FadeClockReading.qualifies` 也要用它。
    /// 嵌套类型**不继承**外层类的 `@MainActor`（Swift 6.1 在 CI 上直接编译不过），
    /// 于是"要么把公式抄第二份、要么让它能被子域调用"二选一 —— 抄第二份迟早会算出两个"可分段数"
    /// （R57 那条"两份各写一遍迟早会算出两个中位"同一课），所以改的是隔离，不是复制。
    nonisolated static func resolvableFrames(durationMilliseconds: Double, sampleMilliseconds: Int) -> Int {
        guard sampleMilliseconds > 0, durationMilliseconds > 0 else { return 0 }
        return Int(durationMilliseconds / Double(sampleMilliseconds))
    }

    /// 判据：这段变更是"演了一段"还是"跳了一下"。
    ///
    /// 为什么 R5 把"几帧在动"换成"动了多久"：本机同一份代码三次实测 `empty-state` 的
    /// 过渡帧数是 `3 / 2 / 2`（HEAD 上也读到过 2），而**变化段时长**是 `131 / 119 / 125ms` ——
    /// 帧数跟着采样相位翻脸，时长不翻脸。一条会翻脸的判据在判的是尺子，不是产品
    /// （BACKLOG 第 6 条那一族）。
    ///
    /// 那两个常数不是调出来的，是解出来的。设整段过渡时长 `d`、事件那一段最粗的一次采样 `s`：
    /// - 真过渡的"还在变"时间最少 `d − 2s`（首、末各可能错开一个采样）；
    /// - 一次跳变的只有 `s`。
    /// 要"真过渡必判绿、跳变必判红"就要 `d − 2s ≥ 0.4d` 且 `s < 0.4d` ⇒ **`s ≤ 0.3d` 时两条同时成立**。
    /// 所以 `s > 0.3d` 时改用"至少两帧在变"这一档（见下），`s > 0.5d` 才报 `.clockTooCoarse`，
    /// 既不判红也不判绿（把尺子的盲区写成产品缺陷，和写成"已交付"一样是假证据）。
    static func judgeMotion(elapsedMilliseconds: Double,
                           worstIntervalMilliseconds: Double,
                           declaredDurationMilliseconds: Double,
                           changedFrames: Int) -> MotionVerdict {
        guard declaredDurationMilliseconds > 0, worstIntervalMilliseconds > 0 else { return .clockTooCoarse }
        let duration = declaredDurationMilliseconds
        if worstIntervalMilliseconds <= 0.3 * duration {
            return elapsedMilliseconds >= 0.4 * duration ? .transition : .jump
        }
        if worstIntervalMilliseconds <= 0.5 * duration {
            // 中间档（R8 的 CI 把这一档逼出来的）：一次跳变只占 1 帧，而这段过渡至少占 2 帧
            // ⇒ **在这一点上帧数是够用的判别量**，不必因为时钟稍粗就放弃判定。
            // runner 实测事件内 ~55ms 一帧、声明 160ms ⇒ 三个场景全掉进这里，
            // 只有一档判据时 `judged` 从 3/3 掉到 0/3，而覆盖率闸门如实报红。
            // 那一轮的选择是**把中间档判起来**，不是把闸门放松。
            return changedFrames >= 2 ? .transition : .jump
        }
        return .clockTooCoarse
    }

    enum MotionVerdict {
        /// 画面连续变了至少声明时长的四成 ⇒ 过渡在演。
        case transition
        /// 变化只覆盖了一个采样左右的时长 ⇒ 一帧跳变。
        case jump
        /// 事件那一段的采样比整段过渡的三成还粗 ⇒ 无从判定。
        case clockTooCoarse
    }

    /// 事件那一段（第一个还在变的帧 → 最后一个还在变的帧之后一帧）**最粗的一次采样间隔**（ms）。
    /// 用最大值而不是中位数：中位数会被"落定之后连拍的一堆快帧"拉低，
    /// 而决定分辨率的是过渡正在演的那一段里最稀的一次。
    /// 返回 `nil` = 整段没有可见变化 ⇒ 无从判定。
    static func worstIntervalInsideChangedRun(stamps: [TimeInterval], fractions: [Double]) -> Double? {
        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return nil }
        let moving = fractions.indices.filter { fractions[$0] >= peak * stepFloorRatio }
        guard let first = moving.first, let last = moving.last, last + 1 < stamps.count else { return nil }
        var worst: Double = 0
        for index in (first + 1)...(last + 1) {
            worst = max(worst, (stamps[index] - stamps[index - 1]) * 1000)
        }
        return worst
    }

    /// "过渡的中点"对应的帧号 —— 给"必须还差得远"这类**阳性对照**用。
    /// `nil` = 连过渡的一半都落在同一帧里 ⇒ 无从判定。
    static func midFlightPreRollFrames(durationMilliseconds: Double,
                                       sampleMilliseconds: Int) -> Int? {
        guard sampleMilliseconds > 0, durationMilliseconds > 0 else { return nil }
        let half = Int((0.5 * durationMilliseconds) / Double(sampleMilliseconds))
        return half >= 1 ? half : nil
    }

    // MARK: - 淡入时钟探针（R66 / BACKLOG 100）

    /// 一张帧的**平均亮度**（0…1：sRGB 三通道均值，每 7 个像素采一个）。
    ///
    /// 为什么量电平而不是量"两帧之差"：淡入探针要回答的是「这一帧上那层遮罩有多透明」，
    /// 而 `changedFraction` 只说"这两帧不一样" —— 一步跳变和一条斜坡的头几帧在它眼里都是 0.9，
    /// 分不出"有没有过程"。要数中间态就必须有个**带极性的量**，所以这里读电平。
    /// 读不到像素返回 −1 而不是 0：把"没量到"写成 0，下游会当成"整帧全黑"
    /// （`median` 的 −1 是同一族规矩）。
    static func meanLevel(_ image: CGImage) -> Double {
        let bitmap = raster(image)
        guard bitmap.pixels.count >= 4 else { return -1 }
        var sum = 0.0
        var sampled = 0
        var index = 0
        while index + 2 < bitmap.pixels.count {
            sum += (Double(bitmap.pixels[index]) + Double(bitmap.pixels[index + 1])
                        + Double(bitmap.pixels[index + 2])) / 765.0
            sampled += 1
            index += 28     // 4 字节 × 7 像素
        }
        return sampled == 0 ? -1 : sum / Double(sampled)
    }

    enum FadeClockVerdict: Equatable {
        /// 夹具自己就没动 —— 探针坏了，与产品和机器都无关，必须判红。
        case probeDead
        /// 这台机器+这条通道能把 150ms 的淡入切成多级 ⇒ 淡入判据在这里有分辨率。
        case resolves
        /// 夹具动了，但只读出头尾两级 ⇒ 这台机器今天看不见淡入的过程（环境，不是产品）。
        case snaps
    }

    /// 淡入时钟的一次读数，连它自己的三条线。
    ///
    /// 三条线为什么住在这个类型里而不是 `MotionFilmstripTests` 的类级常量：嵌套类型**不继承**
    /// 外层类的 `@MainActor`（Swift 6.1 在 CI 上直接编译不过 —— 一条"算个判定"的纯代码
    /// 不该被要求在主线程上跑）。放在这儿，`verdict` 与它用的数就是同一个作用域，
    /// 也没有"改了外层常量、这里还在用旧值"的可能。
    struct FadeClockReading {
        /// 探针"夹具到底动没动"的跨度地板。夹具是白底上盖满一块黑，实测跨度在 0.4 以上，
        /// 而纯噪声在 0.01 以下 —— 中间没有可争的地带，所以这个数不需要标定得很准。
        static let deadSpan: Double = 0.05
        /// 两端各留这个比例的幅度**不算**中间态：太贴头的是"还没开始"，太贴尾的是"已经落定"。
        static let endpointMargin: Double = 0.2
        /// "这台机器看得见过程"的最小中间态帧数。
        ///
        /// 取 2 而不是复用 `minimumTransitionFrames`(3)：这条判据问的是**通道的分辨能力**。
        /// 一次 150ms 的淡入在 60ms 的采样率下本来就只有两级可分，要 3 级就把"勉强能分辨"
        /// 的机器判成"分辨不了" ⇒ 那等于凭空造出第二个 `clock-too-coarse`，把该红的说成没跑。
        static let minimumIntermediateFrames = 2

        let frames: Int
        let span: Double
        let intermediate: Int
        let samplingMilliseconds: Int

        var verdict: FadeClockVerdict {
            if frames < 4 || span < Self.deadSpan { return .probeDead }
            return intermediate >= Self.minimumIntermediateFrames ? .resolves : .snaps
        }

        /// 这个证人**有没有资格**给"这台机器看不见"这句话签字（R68 / BACKLOG 104）。
        ///
        /// 判据只有一条：**证人自己得能把自己那条淡入切成可数的中间态**。
        /// 理由不是形式，是 R66 那次 CI 的实物：runner 上证人采样 ≈80ms、
        /// 而它要作证的 `testTransitionsAreActuallyRunning` 用"事件内最粗 35ms"。
        /// 一条 150ms 的淡入在 80ms 间隔上本来就只有 1 段可分 ⇒ `中间态帧数=0` 是**证人的分辨率**，
        /// 不是产品的跳变。拿它去 skip，等于把"我没看清"写成"它没动" ——
        /// 与 R66 的 M356 同一个形状，只是这次方向相反（M356 是"能分辨时不许 skip"）。
        ///
        /// 为什么线取"段数 ≥ `minimumIntermediateFrames` + 1"而不是"证人采样 ≤ 判据采样"：
        /// 后者我第一版就是这么写的，本机当场读到 `证人≈20ms 判据≈11ms ⇒ 不合格` ——
        /// 那是**把两根不同的尺硬比大小**：判据那 11ms 里含它自己夹具的成本，
        /// 与"证人能不能分辨一条淡入"没有关系（同一族：R47 那条"判据别拿帧数当时长用"）。
        /// 现在这条线全部由证人自己的量推导：声明时长 ÷ 采样 = 可分数段，
        /// 而"要几段才叫能分辨"用的就是它自己那条 `minimumIntermediateFrames`。
        func qualifies(declaredDurationMilliseconds: Int) -> Bool {
            MotionFilmstripTests.resolvableFrames(
                durationMilliseconds: Double(declaredDurationMilliseconds),
                sampleMilliseconds: samplingMilliseconds) >= Self.minimumIntermediateFrames + 1
        }
    }

    /// 一条电平序列 → 淡入时钟读数。纯函数：合成数据就能钉住，不开窗口、CI 每轮都跑
    /// （`testTheFadeClockClassifierIsATruthTable`）。
    static func fadeClockReading(levels: [Double], samplingMilliseconds: Int) -> FadeClockReading {
        // −1 = 那一帧没读到像素。它**必须**被滤掉而不是当成 0：
        // 当成 0 会把跨度撑到 1.0，一次"抓取失败了一半"就能冒充"夹具动得很厉害"。
        let readable = levels.filter { $0 >= 0 }
        guard readable.count > 3, let lo = readable.min(), let hi = readable.max(), hi > lo else {
            return FadeClockReading(frames: readable.count,
                                    span: max(0, (readable.max() ?? 0) - (readable.min() ?? 0)),
                                    intermediate: 0,
                                    samplingMilliseconds: samplingMilliseconds)
        }
        let span = hi - lo
        let low = lo + span * FadeClockReading.endpointMargin
        let high = hi - span * FadeClockReading.endpointMargin
        let intermediate = readable.filter { $0 >= low && $0 <= high }.count
        return FadeClockReading(frames: readable.count, span: span, intermediate: intermediate,
                                samplingMilliseconds: samplingMilliseconds)
    }

    /// 从触发那帧起，画面**停止变化**是在第几帧（相邻帧差跌到峰值的 `stepFloorRatio` 以下，
    /// 并且一路待到底 —— 所以它读的是"最后一次还在动"之后那一帧）。
    ///
    /// 为什么用相邻差而不是"到最终态的距离"：MC-2 那句"声明 150ms 实际跑多久"问的是
    /// **什么时候停下来**，而"到最终态的距离"在两种真实场景下会失效 ——
    /// ① 提示条这类状态会在抓取窗口内回来（触发前后逐像素相同 ⇒ 距离恒为 0）；
    /// ② 交叉淡入的两端都稳定，中段才是过程。两种都会把"有过程"读成"没过程"。
    /// 返回 `nil` = 整段没有任何一次可见的变化 ⇒ 无从判定（调用方报 not-run，不许判绿）。
    static func settledAtFrame(_ frames: [CGImage], band: CGRect? = nil) -> Int? {
        let steps = deltas(frames, band: band)
        guard let peak = steps.max(), peak >= minimumVisibleChange,
              let lastMoving = steps.lastIndex(where: { $0 >= peak * stepFloorRatio }) else { return nil }
        return lastMoving + 1
    }

    /// 前提检查：触发必须让画面**变得不一样**（拿触发前最后一帧与整卷最后一帧比）。
    ///
    /// 不成立就报 not-run，而不是判红也不是判绿。这条是被本机实测逼出来的：
    /// notice-banner 那一卷**首尾逐像素相同**，而模型里提示条一直在（全仓只有
    /// `dismissPasteFailure()` 会清它，没人调）⇒ 离屏 `cacheDisplay` 抓不到"落定之后的横幅"，
    /// 中段那 3 帧变化于是只是一次抖动。少了这道前提，`MOTION_SUMMARY notice-banner=3`
    /// 会被读成"插入动画量到了"，而它其实什么都没保证。
    static func premisePictureChanged(_ frames: [CGImage], band: CGRect? = nil) -> Bool {
        guard frames.count > 4, let first = frames.first, let last = frames.last else { return false }
        return changedFraction(raster(first), raster(last), band: band) >= minimumVisibleChange
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

    /// 淡入时钟分类器的**真值表**（R66 / BACKLOG 100）：斜坡 / 跳变 / 平的 / 噪声 / 读不到。
    ///
    /// 为什么这条必须存在而且不许只靠开窗口的那条：这台机器"能不能看见淡入的过程"这句话
    /// 现在是 `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 的**免检凭据** —— 它一说是，
    /// 那条判据就 skip 掉自己的阳性对照。一个只会说"是"的分类器等于把红撤了。
    /// 所以它的判别力要在合成数据上钉死，不能等某个恰好还没动起来的界面来证明。
    func testTheFadeClockClassifierIsATruthTable() {
        let rising = Self.fadeClockReading(levels: [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0],
                                           samplingMilliseconds: 20)
        XCTAssertEqual(rising.verdict, .resolves, "8 帧里 4 帧在两级之间，必须读成「这台机器看得见过程」")
        XCTAssertGreaterThanOrEqual(rising.intermediate, FadeClockReading.minimumIntermediateFrames)
        XCTAssertEqual(rising.span, 1.0, accuracy: 1e-9)

        // 极性检查：反向斜坡必须给**同一个数**。
        // 不钉这一条，分类器就可以偷偷把"变亮"当成"有过程"、把"变暗"当成"跳变"，
        // 而淡出那一臂正好是变暗 —— 那是 R58 分带映射上下颠倒同一族的错（关于中线的不对称没人查）。
        let falling = Self.fadeClockReading(levels: [1.0, 0.8, 0.6, 0.4, 0.2, 0, 0, 0],
                                            samplingMilliseconds: 20)
        XCTAssertEqual(falling.intermediate, rising.intermediate,
                       "同一条斜坡倒过来读出的中间态帧数就变了 ⇒ 分类器在用极性而不是幅度")
        XCTAssertEqual(falling.verdict, .resolves)

        let stepUp = Self.fadeClockReading(levels: [0, 0, 0, 1, 1, 1, 0, 0], samplingMilliseconds: 20)
        XCTAssertEqual(stepUp.verdict, .snaps, "一帧跳变必须读成「这台机器看不见过程」")
        XCTAssertEqual(stepUp.intermediate, 0)
        XCTAssertEqual(stepUp.span, 1.0, accuracy: 1e-9,
                       "跨度仍然要是 1.0：它没动是「跳」，不是「坏」—— 判红与 skip 的分界就在这儿")
        XCTAssertEqual(Self.fadeClockReading(levels: [1, 1, 1, 0, 0, 0, 1, 1], samplingMilliseconds: 20).verdict,
                       .snaps, "反向跳变也一样")

        // 判别力：同一跨度下，斜坡与跳变必须给出**不同**判定。少了这两行，
        // "全都返回 .resolves" 和"全都返回 .snaps"都能通过上面那些断言的一半。
        XCTAssertNotEqual(rising.verdict, stepUp.verdict, "分类器分不开斜坡与跳变 ⇒ 它没有资格给判据发放免检")

        XCTAssertEqual(Self.fadeClockReading(levels: [0.5, 0.5, 0.5, 0.5, 0.5], samplingMilliseconds: 20).verdict,
                       .probeDead, "夹具压根没动 ⇒ 是探针坏了，不许读成「这台机器看不见淡入」")
        XCTAssertEqual(Self.fadeClockReading(levels: [0.500, 0.505, 0.495, 0.502, 0.498, 0.501],
                                             samplingMilliseconds: 20).verdict, .probeDead,
                       "纯噪声不能冒充「动了但只有一级」：跨度地板就是拦这个的")
        XCTAssertEqual(Self.fadeClockReading(levels: [0, 1, 0], samplingMilliseconds: 20).verdict, .probeDead,
                       "帧数不够时不许判机器 ⇒ 那是一次没抓到的抓取")

        // −1（那一帧读不到像素）必须被滤掉。当成 0 用会把跨度撑满，
        // 于是"一半帧抓取失败"能冒充"夹具动得很厉害"。
        let halfUnreadable = Self.fadeClockReading(levels: [-1, -1, 0.5, 0.5, 0.5, 0.5], samplingMilliseconds: 20)
        XCTAssertEqual(halfUnreadable.frames, 4)
        XCTAssertEqual(halfUnreadable.span, 0, accuracy: 1e-9)
        XCTAssertEqual(halfUnreadable.verdict, .probeDead, "读不到的帧被当成黑色参与了跨度 ⇒ 探针坏了会伪装成能判")
        XCTAssertEqual(Self.fadeClockReading(levels: [-1, -1, -1, -1], samplingMilliseconds: 20).frames, 0)
    }

    /// 前提检查自己也要有判别力（合成帧，不开窗口）。
    func testPremiseCheckSeesAChangeAndItsAbsence() {
        XCTAssertTrue(Self.premisePictureChanged(Self.syntheticFrames(grays: [0, 0, 0.5, 1, 1, 1])),
                      "触发前后确实不同却报「没变化」⇒ 这道前提会把真判据全关掉")
        XCTAssertFalse(Self.premisePictureChanged(Self.syntheticFrames(grays: [0.5, 0.6, 0.4, 0.55, 0.5, 0.5])),
                       "首尾相同的一卷必须被判成「看不到这次变更」，哪怕中段抖得再凶")
        XCTAssertFalse(Self.premisePictureChanged(Self.syntheticFrames(grays: [0, 1, 0])),
                       "帧数太少时不许硬判成立（那等于没有前提检查）")
    }

    /// 锚点必须落在**触发前最后一帧**：预卷不能进判据。
    ///
    /// 这条是 `motionFrames` 自己的判别力。没有它，"把整卷都当从触发开始算"这种改法
    /// 不会让任何判据变红 —— 而所有 `after: 1`、所有"到位帧数"都会静默地往前挪几帧，
    /// 量到的东西与名字不再相干（合成帧不依赖窗口与采样率，CI 每次都跑）。
    func testMotionFramesAnchorsAtTheTriggerNotAtTheWindow() {
        let all = Self.syntheticFrames(grays: [0, 0, 0, 1, 1])   // 前 3 帧是预卷，第 4 帧才是触发之后
        let film = Film(frames: all, stamps: [0, 1, 2, 3, 4], triggerFrame: 3)
        XCTAssertEqual(film.motionFrames.count, 3,
                       "锚点没落在触发前那一帧：预卷漏进了判据，后面所有帧号都对不上时刻")
        XCTAssertGreaterThan(Self.deltas(film.motionFrames).first ?? 0, Self.minimumVisibleChange,
                             "第一对帧读不出变化 ⇒ 这一卷不是从触发开始算的")
        // 越界与 0 都要有定义：抓取失败时 triggerFrame 可能是 0。
        XCTAssertEqual(Film(frames: all, stamps: [0, 1, 2, 3, 4], triggerFrame: 0).motionFrames.count, 5)
        XCTAssertEqual(Film(frames: all, stamps: [0, 1, 2, 3, 4], triggerFrame: 99).motionFrames.count, 1)
    }

    /// `settledAtFrame` 的两个合成用例：一次斜坡、一次跳变，外加一段"什么都没变"。
    ///
    /// 为什么单独要一条：这条度量原来只在开窗口的那条判据里被用，而窗口那条在粗时钟下
    /// 会**主动放弃**"有没有过程"那一半（报 not-run）—— 于是"到位帧数算错了"这种缺陷
    /// 在本机可能一条判据都抓不到。合成帧不依赖窗口、不依赖动画、也不依赖采样率。
    func testSettledAtFrameReadsSyntheticRampsAndSteps() {
        let ramp = Self.settledAtFrame(Self.syntheticFrames(grays: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0]))
        XCTAssertEqual(ramp, 5, "分摊到 5 帧的斜坡必须读成「第 5 帧才停下来」，实测 \(String(describing: ramp))")

        let step = Self.settledAtFrame(Self.syntheticFrames(grays: [0.0, 1.0, 1.0, 1.0, 1.0]))
        XCTAssertEqual(step, 1, "一帧跳变必须读成第 1 帧就停下来（这是地板 2 帧还能打红的前提），实测 \(String(describing: step))")

        XCTAssertNil(Self.settledAtFrame(Self.syntheticFrames(grays: [0.5, 0.5, 0.5, 0.5, 0.5])),
                     "整段什么都没变时不许报一个帧号：那会被读成「它停得真快」")
    }

    /// 造一批纯色小图当合成帧。尺寸刻意小：这条判据要的是形状，不是像素量。
    private static func syntheticFrames(grays: [CGFloat]) -> [CGImage] {
        grays.map { gray in
            let size = 40
            var pixels = [UInt8](repeating: UInt8(gray * 255), count: size * size * 4)
            for index in stride(from: 3, to: pixels.count, by: 4) { pixels[index] = 255 }
            let space = CGColorSpace(name: CGColorSpace.sRGB)!
            let context = CGContext(data: &pixels, width: size, height: size, bitsPerComponent: 8,
                                    bytesPerRow: size * 4, space: space,
                                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
            // 刻意不调 fill()：位图数据已经是想要的颜色，再 fill 会被默认填充色（黑）盖掉。
            return context.makeImage()!
        }
    }

    /// 证人自己要先上台：夹具必须真的动，读数必须每轮都在（R66 / BACKLOG 100）。
    ///
    /// 为什么单独立一条，而不是等阳性对照掉到 0.15 以下时顺带跑到：本机横幅的残余是 0.974，
    /// 那条判据**永远不会**去问证人 ⇒ 证人一次都没被调用过，却被拿来给 runner 上的红免检。
    /// 这条判据把它每轮都跑一遍：`span` 读不出来 ⇒ 红（夹具坏了、探针瞎了，是工具的问题，
    /// 必须有人看见）；`verdict == .snaps` ⇒ 不红，那正是它的证词内容，红在"能分辨的那台机器"上。
    func testTheFadeClockWitnessMovesAtAll() throws {
        try skipUnlessEnabledAndCapable()
        let clock = fadeClock()
        XCTAssertNotEqual(clock.verdict, .probeDead,
                          "淡入时钟的夹具自己没读出过程（跨度=\(String(format: "%.3f", clock.span)) "
                              + "帧数=\(clock.frames)）⇒ 证人是个摆设：它一开口替机器说话，"
                              + "说的其实是「我什么都没看见」。先修夹具，再谈阳性对照")
        // 夹具的跨度必须**足够大**才算"真的动过"：0.05 那条线是"动没动"，不是"动得够不够"。
        // 这里再钉一条下限，是因为白底盖黑理论上跨度接近 0.5；读出来是 0.06 那种"刚过线"，
        // 说的是这层的遮罩没铺满、或者帧是空的 —— 那种证人同样不能替任何人说话。
        XCTAssertGreaterThan(clock.span, 0.2,
                             "夹具跨度只有 \(String(format: "%.3f", clock.span))，而白底盖满黑应该在 0.5 上下 ⇒ "
                                 + "要么遮罩没铺满视口，要么这条通道抓到的是空帧")
    }

    /// 采样率感知那几个纯函数的**真值表**（R2 的核心）。
    ///
    /// 为什么单独立一条而不是只靠跑窗口的用例：这几个数字决定"什么时候判红、什么时候报无从判定"，
    /// 而本机时钟今天恰好偏细（31ms）时所有窗口用例都是绿的 —— 那不等于判据在 90ms 的时钟上
    /// 也是对的。CI 那台 runner 是 26–30ms，本地负载高时能到 90ms，两个方向都必须钉住。
    func testResolutionHelpersAreATruthTableNotAStory() {
        XCTAssertEqual(Self.resolvableFrames(durationMilliseconds: 150, sampleMilliseconds: 30), 5)
        XCTAssertEqual(Self.resolvableFrames(durationMilliseconds: 150, sampleMilliseconds: 90), 1)
        XCTAssertEqual(Self.resolvableFrames(durationMilliseconds: 0, sampleMilliseconds: 30), 0,
                       "没声明时长就没有可分辨帧数可言")
        XCTAssertEqual(Self.resolvableFrames(durationMilliseconds: 150, sampleMilliseconds: 0), 0,
                       "时钟没测到 ⇒ 不能当成「无限细」往下判")

        // MARK: R5 —— 判据从"几帧在动"换成"动了多久"，判别力必须重新钉一遍
        //
        // 原来这里钉的是 `requiredTransitionFrames`（"还在变的帧数 ≥ 几"）。R5 把它换成了
        // 时长判据，所以那三行断言跟着删 —— **不留只被真值表喂着的旧判据**：
        // 一个只有测试在读的辅助函数，读起来像"这条判据还在"，比没有更坏。

        // 本机实测：`empty-state` 同一份代码三次跑出过渡帧数 `3 / 2 / 2`（HEAD 上也读到 2），
        // 而变化段时长是 `131 / 119 / 125ms`。下面两组合成数据就是那两次：
        // **帧数不同、时长相同** —— 这就是"帧数在判采样相位"的最小复现。
        let stamps = [0.0, 0.045, 0.090, 0.135, 0.180, 0.225, 0.270]
        let fineSampling: [Double] = [0.05, 0.06, 0.05, 0.001, 0.0, 0.0]
        let coarseSampling: [Double] = [0.11, 0.001, 0.10, 0.0, 0.0, 0.0]
        XCTAssertEqual(Self.transitionFrameCount(fineSampling), 3)
        XCTAssertEqual(Self.transitionFrameCount(coarseSampling), 2,
                       "这两组读数是同一段 135ms 的淡入，只是采样相位不同")
        for (name, fractions) in [("细相位", fineSampling), ("粗相位", coarseSampling)] {
            let elapsed = Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: fractions) ?? -1
            XCTAssertEqual(elapsed, 135, accuracy: 1, "\(name)：时长读数不该跟着相位翻脸")
            let worst = Self.worstIntervalInsideChangedRun(stamps: stamps, fractions: fractions) ?? -1
            XCTAssertEqual(worst, 45, accuracy: 1, "事件内最粗采样 = 45ms")
            XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: elapsed,
                                            worstIntervalMilliseconds: worst,
                                            declaredDurationMilliseconds: 160,
                                            changedFrames: 3), .transition,
                           "\(name)：两种相位都必须判成「过渡在演」")
        }

        // 一帧跳变：变化段只剩一个采样 ⇒ 必须红（这条是上面那条绿的全部代价所在）。
        let jump: [Double] = [0.12, 0.0, 0.0, 0.0, 0.0, 0.0]
        let jumpElapsed = Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: jump) ?? -1
        let jumpWorst = Self.worstIntervalInsideChangedRun(stamps: stamps, fractions: jump) ?? -1
        XCTAssertEqual(jumpElapsed, 45, accuracy: 1, "跳变的「变化段」就是一个采样的长度")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: jumpElapsed,
                                        worstIntervalMilliseconds: jumpWorst,
                                        declaredDurationMilliseconds: 160,
                                        changedFrames: 1), .jump,
                       "45ms 的变化段对 160ms 的声明 ⇒ 必须判成跳变，否则这条判据没有判别力")
        // 门槛之下：63ms 的变化段（160ms 声明、时钟 45ms）仍然算没演完。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 63, worstIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 1), .jump)
        // 边界：s = 0.3d 时真过渡的最坏读数 d−2s 正好等于 0.4d ⇒ 判据在边界上仍然自洽
        //（"真过渡必过、跳变必红"这两个要求同时成立的那个点）。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 64, worstIntervalMilliseconds: 48,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .transition)
        XCTAssertNotEqual(Self.judgeMotion(elapsedMilliseconds: 48, worstIntervalMilliseconds: 48,
                                           declaredDurationMilliseconds: 160, changedFrames: 1), .transition,
                         "跳变的最坏读数（=s）不许过线")
        // MARK: R8 —— 三档。CI 实测把这条逼出来的：runner 事件内 ~55ms 一帧，
        // 三个场景全掉进中间档，`judged` 从 3/3 掉到 **0/3**，新加的覆盖率闸门如实报红。
        // 中间档（0.3d < s ≤ 0.5d）：跳变 1 帧、过渡至少 2 帧 ⇒ 帧数在这里够用。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 110, worstIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .transition,
                       "CI 那档时钟必须仍然判得出东西，否则覆盖率闸门会长期红着")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 55, worstIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 1), .jump,
                       "中间档里的一帧跳变仍然要红")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 110, worstIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 0), .jump,
                       "变化帧数读成 0 却报绿 ⇒ 中间档没有地板")
        // 细时钟档：只看时长，帧数不参与 ⇒ 相位翻脸抓不住它
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 135, worstIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 2), .transition,
                       "细时钟下 2 帧也判绿：这一档看的是时长不是帧数")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 45, worstIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 2), .jump,
                       "时长不够就红，哪怕帧数到了 2")
        // 太粗档（s > 0.5d）⇒ 无从判定，既不判红也不判绿。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 200, worstIntervalMilliseconds: 100,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .clockTooCoarse,
                       "事件那一段 100ms 一帧、整段过渡只有 160ms ⇒ 是尺子看不见，不是产品没动")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 999, worstIntervalMilliseconds: 0,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .clockTooCoarse,
                       "时钟没测到 ⇒ 不能当成「无限细」往下判")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 999, worstIntervalMilliseconds: 30,
                                        declaredDurationMilliseconds: 0, changedFrames: 3), .clockTooCoarse,
                       "没声明时长就没有门槛可言")
        // 整段没有一次可见变化 ⇒ 两个读数都必须 nil（调用方报 not-run，不许判绿）。
        let idleFractions: [Double] = [0.0, 0.001, 0.0, 0.001, 0.0, 0.0]
        XCTAssertNil(Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: idleFractions))
        XCTAssertNil(Self.worstIntervalInsideChangedRun(stamps: stamps, fractions: idleFractions))

        XCTAssertEqual(Self.midFlightPreRollFrames(durationMilliseconds: 150, sampleMilliseconds: 40), 1,
                       "中点取样点至少要在过渡里面")
        XCTAssertNil(Self.midFlightPreRollFrames(durationMilliseconds: 150, sampleMilliseconds: 90),
                     "过渡的一半落在同一帧里 ⇒ 取不到中点，阳性对照必须报无从判定")
        XCTAssertNil(Self.midFlightPreRollFrames(durationMilliseconds: 0, sampleMilliseconds: 40))
    }

    /// 判据里不许再出现"第 N 帧"这种绝对预卷（R2 的自我约束，扫的是本文件自己）。
    ///
    /// 这条存在的理由和 R1 那三条源码守卫一样：**「我们已经改成按时间表达了」这句话，
    /// 靠注释是保不住的** —— 下一轮有人图省事把 `after: 3` 抄回来，注释不会变红。
    /// 允许的形状只有两种：`after: 1`（触发那一帧，定义上与采样无关）与
    /// `after: <某个 *PreRollFrames(...) 推出来的变量>`。
    func testMotionCriteriaDoNotUseAbsoluteFramePrerolls() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        XCTAssertFalse(source.isEmpty, "读不到本文件：这条守卫没有守卫对象")

        // 扫之前先把守卫自己的代码摘掉：它每一行都带着它要找的 needle
        // （`XCTAssertFalse(own.contains { $0.contains("Self.settleFrames(") })` 这一行本身就含
        // `Self.settleFrames(`）。不摘的话它会自己判自己红；而那句"必须走采样率感知"的正向对照
        // 会被自己白送命中 —— **恒真的对照等于没有对照**（本仓库同类错误记过不止一次）。
        let own = source.components(separatedBy: "\n").filter { !$0.contains(".contains(") && !$0.contains("contains {") }
        var offenders: [String] = []
        for (index, raw) in own.enumerated() {
            let line = raw.trimmingCharacters(in: .whitespaces)
            guard let range = line.range(of: "after:") else { continue }
            // 只看 `after:` 后面第一个有效字符：数字 ⇒ 写死的帧号（违规），
            // 标识符首字符 ⇒ 由采样率推出来的变量（合规），其它（引号等）⇒ 本条守卫自己的代码。
            // 用"contains 一个词"来判会把自己的代码也算进去，而 `after: 1` 这种合规写法
            // 又会挡住真正违规的 `after: 12` —— 所以取字符，不取子串。
            let first = line[range.upperBound...].first { !$0.isWhitespace }
            if let digit = first, digit.isNumber, digit != "1" {
                offenders.append("\(index + 1): \(line)")
            }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "这些行的预卷是写死的帧号（一帧是 31ms 还是 90ms 取决于抓帧耗时）：\n"
                          + offenders.joined(separator: "\n"))

        XCTAssertFalse(own.contains { $0.contains("Self.settleFrames(") },
                       "那个「预卷之后还有几帧在动」的计数器又被拿来当判据了：它的上限是帧数，会跟着时钟漂，见 `settledAtFrame`")
        XCTAssertTrue(own.contains { $0.contains("Self.judgeMotion(") },
                      "过渡判据没走「按声明时长与事件内采样判」那条路 ⇒ 上面那两条就成了空转。"
                          + "（R5 之前这里钉的是 `requiredTransitionFrames`：换判据时这条自己红了，"
                          + "说明它真的在看调用点，不是注释。）")
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
        emit("MOTION_BLANK frames=\(frames.count) 峰值=\(String(format: "%.4f", fractions.max() ?? 0)) 过渡帧数=\(span)")
        XCTAssertEqual(span, 0, "什么都没发生却量到了过渡 ⇒ 尺子在把重绘噪声读成动画")
    }

    /// **两臂都要有人判**（R22 / U-44）。
    ///
    /// 立这条的理由是 R16 那一族：`ContentView` 那五张横幅写的是
    /// `asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，
    /// 而胶片清单里**只有插入那一臂** —— 于是"移除到底在不在演"四轮以来没有任何读数。
    ///
    /// 这条不判产品，判的是**判据自己有没有覆盖到**：名单少一臂就红。
    /// （为什么不用"CI 的 `MOTION_SUMMARY` 里有两个键"来判：那是产物侧的形状，
    /// 而今天本机四条场景里只有一条能分辨过程 —— 键在不在取决于时钟，不取决于清单。）
    func testBothBannerArmsAreJudged() {
        let scenarios = Scenario.all()
        let names = scenarios.map { $0.name }
        XCTAssert(names.contains("notice-banner"),
                  "胶片清单里没有插入那一臂 ⇒ 横幅的进入从此没人判")
        XCTAssert(names.contains("notice-banner-dismiss"),
                  "胶片清单里没有**移除**那一臂 ⇒ `.bannerOut` 那 120ms 又回到没人看着的状态，"
                  + "这一族 R16 记过（只有一臂在演的过渡等于没有过渡）")
        // 撤走那一臂必须有起点：`prepare` 先把横幅摆上，否则量到的是"从没出现过"而不是"消失了"。
        let dismiss = scenarios.first { $0.name == "notice-banner-dismiss" }
        XCTAssertNotNil(dismiss?.prepare,
                        "notice-banner-dismiss 没有 prepare ⇒ 起点是空态，那条卷量不到'消失'")
        XCTAssertEqual(dismiss?.declaredDurationMilliseconds,
                       MotionCatalog.duration(for: .bannerOut) * 1000,
                       "撤走那一臂声明的时长不是 `.bannerOut` ⇒ 判据用来算分辨率的档会对错")
    }

    func testTransitionsAreActuallyRunning() throws {
        try skipUnlessEnabledAndCapable()
        var rows: [(name: String, span: Int)] = []      // 每个场景都进 MOTION_SUMMARY，形状不许因为"看不见"而少一项
        var judged = 0
        var notRun: [String] = []

        for scenario in Scenario.all() {
            let film = record(scenario)
            let frames = film.motionFrames
            guard frames.count > 4 else {
                XCTFail("\(scenario.name)：只抓到 \(frames.count) 帧，判据没有对照物")
                continue
            }
            let interval = Self.sampleIntervalMilliseconds(film.motionStamps)
            let fractions = Self.deltas(frames)
            let span = Self.transitionFrameCount(fractions)
            let elapsed = Self.changedSpanElapsedMilliseconds(stamps: film.motionStamps, fractions: fractions)
            let worstInRun = Self.worstIntervalInsideChangedRun(stamps: film.motionStamps, fractions: fractions)
            // 每个场景都进 MOTION_SUMMARY（哪怕这一条今天判不了）：CI 那一步与它的自测夹具
            // 都按"三个键都在"的形状读，少一个键会让下游把"没测"读成"测了且为 0"。
            rows.append((scenario.name, span))
            guard film.clockIsWarm else {
                notRun.append(scenario.name)
                emit("MOTION_NOT_RUN=clock-not-warm \(scenario.name)：触发那一刻采样还是冷的"
                    + "（最后一格 >\(Int(Self.warmIntervalMilliseconds))ms）⇒ 一次 "
                    + "\(Int(scenario.declaredDurationMilliseconds))ms 的过程最多被拍到两三个样本，"
                    + "这把尺量不到「过程」这件事 —— 报没测到，不判产品没动")
                continue
            }
            guard Self.premisePictureChanged(frames) else {
                notRun.append(scenario.name)
                // 报 not-run 时要说清**是哪一种** not-run。以前只说"逐像素相同"，
                // 而这一条在本机今天就是这样红的（`notice-banner` 插入明明演了 3 帧，
                // 首尾却相同）—— 分不清"变更发生在第一帧之前"与"演完又落回原样"，
                // 下一轮就只能再猜一次。两个数都打出来：首尾差、卷内最大差。
                let deltas = Self.deltas(frames)
                emit("MOTION_NOT_RUN=premise-not-visible \(scenario.name)：首尾两帧逐像素相同 ⇒ "
                    + "这一卷里看不到「这次变更」，后面读到的几帧变化不能算在过渡头上。"
                    + "卷内最大逐帧差=\(deltas.max().map { String(format: "%.3f", $0) } ?? "无") "
                    + "过渡帧数=\(span)（>0 就说明变更演过了，只是没留在首尾对照里）")
                continue
            }
            // 时钟自己也要进记录。`采样≈` 那一列是**整卷中位数**，它盖不住 burst：
            // 落定之后连拍的一堆快帧会把中位数拉到 21ms，而过渡正在演的那一段实际是 45ms 一帧 ——
            // 本机就是这样把"采样相位"读成"产品只跳了一帧"的。所以另外两列：
            // `事件内最粗` = 变化段里最稀的一次采样（判分辨率用这个），`变化段时长` = 判过渡用这个。
            let gaps = stride(from: 1, to: film.motionStamps.count, by: 1).map {
                Int(((film.motionStamps[$0] - film.motionStamps[$0 - 1]) * 1000).rounded())
            }
            emit("MOTION \(scenario.name) frames=\(frames.count) "
                + "声明=\(Int(scenario.declaredDurationMilliseconds))ms 整卷中位=\(interval)ms "
                + "事件内最粗=\(worstInRun.map { String(format: "%.0f", $0) } ?? "无")ms "
                + "变化段时长=\(elapsed.map { String(format: "%.0f", $0) } ?? "无")ms 过渡帧数=\(span) "
                + "时刻ms=[\(gaps.map(String.init).joined(separator: " "))] "
                + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
            writeStrip(scenario.name, frames)
            guard let elapsed, let worstInRun else {
                notRun.append(scenario.name)
                emit("MOTION_NOT_RUN=no-changed-run \(scenario.name)：读不出「变化段」的时长 ⇒ 既不判红也不判绿")
                continue
            }
            switch Self.judgeMotion(elapsedMilliseconds: elapsed,
                                    worstIntervalMilliseconds: worstInRun,
                                    declaredDurationMilliseconds: scenario.declaredDurationMilliseconds,
                                    changedFrames: span) {
            case .clockTooCoarse:
                notRun.append(scenario.name)
                emit("MOTION_NOT_RUN=clock-coarse-in-window \(scenario.name)：事件那一段最粗 \(String(format: "%.0f", worstInRun))ms "
                    + "一帧、整段过渡只有 \(Int(scenario.declaredDurationMilliseconds))ms（门槛 0.3×声明）⇒ "
                    + "这把尺在过渡正在演的那一段切不出「过程」这个概念，既不判红也不判绿"
                    + Self.grabAttributionLabel(worstIntervalMilliseconds: worstInRun,
                                                worstGrabMilliseconds: film.worstGrabMilliseconds))
            case .jump:
                judged += 1
                XCTFail("\(scenario.name)：画面只变了 \(String(format: "%.0f", elapsed))ms 就停了，"
                    + "而声明的过渡是 \(Int(scenario.declaredDurationMilliseconds))ms（事件内最粗采样 "
                    + "\(String(format: "%.0f", worstInRun))ms）⇒ 这是一帧跳变，不是过渡")
            case .transition:
                judged += 1
            }
        }
        // 形状固定：MOTION_SUMMARY 永远列出全部场景（CI 那一步与它的自测夹具都按这个形状读）。
        emit("MOTION_SUMMARY " + rows.map { "\($0.name)=\($0.span)" }.joined(separator: " "))
        emit("MOTION_RESOLVE_SUMMARY judged=\(judged)/\(rows.count) not-run=\(notRun.isEmpty ? "-" : notRun.joined(separator: ","))")
        guard judged > 0 else {
            throw XCTSkip("MOTION_NOT_RUN=clock-too-coarse：\(notRun.count) 个场景全都分辨不了（采样比整段过渡还粗），这一条今天没有内容")
        }
    }

    /// R11 开的那条；R47 把它从"判帧数"改成"判时长 + 同臂抓两遍"。
    ///
    /// 为什么要专门写一条"量不到"的判据：`heat-first-record` 第一次跑就把 main 判红了，
    /// 读数 `0.004 / 0.027 / 0.220 / 0.000…`（一帧到位）。这很容易读成"产品没做动画"，
    /// 而 `cacheDisplay` 抓的是**模型树** —— 纯 opacity 的交叉淡入只活在 presentation 层，
    /// 同一个根因在 `MOTION_NATIVE`（AppKit 行动画）那条上已经踩过一次并写进账本。
    ///
    /// R47 改两处，都是被实测逼的（BACKLOG 68 / U-73）：
    /// ① **轴换掉**。原来的放行条件里有 `onSpan == offSpan`，而帧数由采样相位决定
    ///    （R2 本机实测同一份代码 2/3/2）。R46 真跑一遍就撞上：
    ///    `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— 峰值完全相同、只有帧数不同，
    ///    旧条件因此把"尺子看不见"判成"尺子看得见"，红的是尺。
    /// ② **同臂抓两遍（A/A/B）**。R47 实测这条通道占空比不是 100%：
    ///    全量 suite 里读出过 `开 265ms / 关 7ms`（看得见），单独连跑 7 次全是
    ///    `开 6–7ms / 关 6–7ms`（看不见）。只抓一遍就等于让"这一次恰好撞上"当结论，
    ///    判的是进程历史而不是产品。两遍不一致 ⇒ 报 `inconsistent`，不挑一次算数。
    ///
    /// 结论形状不变：看不见 ⇒ 记「源码已接、产物未量」，**既不许写进已交付，
    /// 也不许反过来判产品没做**（人眼判据在人工批次 24/49）；两遍都说看得见 ⇒ 红，
    /// 逼着把场景放回 `Scenario.all()` 当真判据，而不是留这条当免责。
    func testHeatmapFadeIsNotVisibleToThisRuler() throws {
        try skipUnlessEnabledAndCapable()
        let saved = MotionCatalog.animationsEnabled
        // R47 实测：同一个场景**在一个进程里第一次抓取必然读不出东西**（6–7ms / 1 帧），
        // 第二遍有时读出 258–266ms。所以第一遍当**预热**丢掉，判定用第 2、3 遍。
        //
        // R48 原本要给这件事一个解释，而且给错了：我写的是"265ms 配帧数=2、中位=8ms，
        // 两帧连续最多 8–16ms ⇒ 那一定是跨度算法把两波并成一段"。**这条判断没被数据支持**：
        // 给这条 A/B 补上 per-run 打印与条带图之后，真形状是
        // `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms` —— **一段连续的**变化，
        // 只是段内有一次 **260ms 的抓帧空档**（首次布局整块日历时主线程被占住，抓帧器挤不进去）。
        // 也就是说 266ms 不是"过程演了 266ms"，也不是"两波被并起来"，而是**钟在过程中间停了**。
        // （本轮还犯过一次可笑的错：我在**还没读到 `worstIntervalMilliseconds` 之前**，
        //  就往注释里写了"约 130ms"——那是拿 266 ÷ 2 估的。实测是 260ms，一次空档而不是两次。
        //  同一条规矩的第三个面：注释里的数也只能从读数来。）
        // 连续段那把尺仍然要（它管的是"不许把无关的两波算成一段"），
        // 但它解释不了这条读数 —— 解释它的是段内最粗采样，于是本轮把那一轴接进判定。
        let warmup = record(Scenario.heatFirstRecord())
        let onFilmA = record(Scenario.heatFirstRecord())
        let onFilmB = record(Scenario.heatFirstRecord())
        MotionCatalog.animationsEnabled = false
        let offFilm = record(Scenario.heatFirstRecord())
        MotionCatalog.animationsEnabled = saved

        // R48：这条 A/B 判了三轮"看不见"，却从来没留过一张画面给人对账。
        // 本轮的靶正好是"读数与画面对不上"，所以三臂各出一张条带 ——
        // 看图的人从此可以问"你说看不见，那这几帧到底长什么样"，而不必信我的一行日志。
        writeStrip("heat-first-record-开A", onFilmA.motionFrames)
        writeStrip("heat-first-record-开B", onFilmB.motionFrames)
        writeStrip("heat-first-record-关", offFilm.motionFrames)

        let onA = Self.deltas(onFilmA.motionFrames)
        let onB = Self.deltas(onFilmB.motionFrames)
        let off = Self.deltas(offFilm.motionFrames)
        // 帧数照旧打印，但**不参与判定**：它由采样相位决定。
        let scenario = Scenario.heatFirstRecord()
        // R48：判定用**连续段**的时长，跨度只当对照一起打印。
        // 两把尺的差就是本轮的靶 —— 一条淡入的时长必须来自"它一直在演"的那一段，
        // 而跨度会把"演完 + 静止 + 别的东西又动了一下"算成一条更长的淡入。
        let warmupFractions = Self.deltas(warmup.motionFrames)
        let runWarm = Self.contiguousChangedRun(stamps: warmup.motionStamps, fractions: warmupFractions)
        let runA = Self.contiguousChangedRun(stamps: onFilmA.motionStamps, fractions: onA)
        let runB = Self.contiguousChangedRun(stamps: onFilmB.motionStamps, fractions: onB)
        let runOff = Self.contiguousChangedRun(stamps: offFilm.motionStamps, fractions: off)
        let elapsedWarm = runWarm?.elapsedMilliseconds
        let elapsedA = runA?.elapsedMilliseconds
        let elapsedB = runB?.elapsedMilliseconds
        let elapsedOff = runOff?.elapsedMilliseconds
        let spanA = Self.changedSpanElapsedMilliseconds(stamps: onFilmA.motionStamps, fractions: onA)
        let spanB = Self.changedSpanElapsedMilliseconds(stamps: onFilmB.motionStamps, fractions: onB)
        let interval = Double(Self.sampleIntervalMilliseconds(onFilmA.motionStamps))
        let verdict = Self.fadeVisibility(elapsedOnA: elapsedA, elapsedOnB: elapsedB,
                                          elapsedOff: elapsedOff, peakOn: Self.peak(onA),
                                          declaredMilliseconds: scenario.declaredDurationMilliseconds,
                                          intervalMilliseconds: interval,
                                          worstOnA: runA?.worstIntervalMilliseconds ?? 0,
                                          worstOnB: runB?.worstIntervalMilliseconds ?? 0)
        func ms(_ value: Double?) -> String { value.map { String(format: "%.0f", $0) } ?? "读不出" }
        /// 把一卷切成"起–止@峰值/段内最粗"的清单（时刻**相对卷首**），用于事后对账：
        /// 长读数到底是连续一段还是两波带空隙、时长是被过程撑出来还是被停顿撑出来，看这一行就知道。
        /// 相对而不是绝对：`motionStamps` 是系统启动以来的秒数，直接乘 1000 会打出
        /// `731797829–731797842` 这种没人能对账的数（R48 第一版就是这么红的）。
        func runs(_ stamps: [TimeInterval], _ fractions: [Double]) -> String {
            guard let zero = stamps.first else { return "无" }
            let list = Self.contiguousChangedRuns(stamps: stamps, fractions: fractions).map {
                String(format: "%.0f–%.0f@%.3f/粗%.0f",
                       (stamps[$0.startFrame] - zero) * 1000,
                       (stamps[min($0.endFrame + 1, stamps.count - 1)] - zero) * 1000,
                       $0.peak, $0.worstIntervalMilliseconds)
            }
            return list.isEmpty ? "无" : list.joined(separator: ",")
        }
        emit("MOTION_HEAT_RUNS 开A [\(runs(onFilmA.motionStamps, onA))] 开B [\(runs(onFilmB.motionStamps, onB))]"
            + " 关 [\(runs(offFilm.motionStamps, off))]"
            + "  跨度A=\(ms(spanA))ms 跨度B=\(ms(spanB))ms 整卷中位=\(ms(interval))ms")
        func label(_ v: FadeVisibility) -> String {
            switch v {
            case .noControl: return "无对照物"
            case .notVisibleToThisRuler: return "看不见"
            case .inconsistent: return "两遍矛盾"
            case .clockTooCoarse: return "钟太粗"
            case .visibleToThisRuler: return "看得见"
            }
        }
        emit("MOTION_HEAT_FADE_A/B 预热 时长=\(ms(elapsedWarm))ms 帧数=\(Self.transitionFrameCount(Self.deltas(warmup.motionFrames)))"
            + " 开A 时长=\(ms(elapsedA))ms 帧数=\(Self.transitionFrameCount(onA))"
            + " 开B 时长=\(ms(elapsedB))ms 帧数=\(Self.transitionFrameCount(onB))"
            + " 峰值=\(String(format: "%.3f", Self.peak(onA)))"
            + "  关 时长=\(ms(elapsedOff))ms 帧数=\(Self.transitionFrameCount(off))"
            + " 峰值=\(String(format: "%.3f", Self.peak(off)))"
            + "  整卷中位=\(ms(interval))ms 声明=\(Int(scenario.declaredDurationMilliseconds))ms"
            + " 冷闸=\(onFilmA.clockIsWarm && onFilmB.clockIsWarm && offFilm.clockIsWarm)"
            + " 判定=\(label(verdict))")
        XCTAssertGreaterThan(Self.peak(onA), Self.minimumVisibleChange,
                             "两臂什么都没变 ⇒ 触发没让图长出来，这条 A/B 没有对照物（是探针坏了，不是动效坏了）")
        // 冷闸必须**过**：拿一段还没热起来的采样去下"尺子看不见"的结论，
        // 那是把探针的毛病写成产品的极限 —— 与"把没跑写成跑过"同一族，只是方向相反。
        XCTAssertTrue(onFilmA.clockIsWarm && onFilmB.clockIsWarm && offFilm.clockIsWarm,
                      "有一臂是在冷采样下抓的 ⇒ 三臂相同不能算尺子的极限，这条结论今天不成立")
        switch verdict {
        case .noControl:
            XCTFail("判定是 noControl ⇒ 探针没有对照物，这条 A/B 今天什么都没说")
        case .inconsistent(let a, let b):
            // 这一格**不红**，但必须把两个数打出来：它说的是"这条通道不能当判据"，
            // 而把"抓不到"判成产品缺陷就是 R39 那一族的恒红。
            emit("MOTION_NOT_RUN=fade-channel-duty-cycle heat-first-record："
                + "同一条产品路径连抓两遍，一遍算看得见（\(ms(a))ms）、一遍算看不见（\(ms(b))ms）⇒ "
                + "这条通道的占空比不是 100%，今天既不能说看得见也不能说看不见")
        case .clockTooCoarse(let worstA, let worstB):
            // 这一格**不红**，而且它连"看不见"都不许说：钟在过程中间停过，
            // 时长读数就没有资格参与判定（R48 的靶就是把这一格从"看不见"里分出来）。
            emit("MOTION_NOT_RUN=clock-coarse-in-window heat-first-record："
                + "峰值那一段内部最粗的一次采样是 \(ms(worstA)) / \(ms(worstB))ms，"
                + "而这条过渡声明 \(Int(scenario.declaredDurationMilliseconds))ms ⇒ "
                + "今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT）"
                // R55：这一格是本机那 260ms 空档的现场，两臂各自归因一次。
                // 只给一臂的话，"是抓帧还是主线程"这个问题就又变回靠一句注释回答了。
                // 打在**同一行**：CI 那一步 grep 的是 `MOTION_NOT_RUN`，换行就等于把归因挤出可读范围。
                + " ｜A 臂" + Self.grabAttributionLabel(worstIntervalMilliseconds: worstA,
                                                        worstGrabMilliseconds: onFilmA.worstGrabMilliseconds)
                + " ｜B 臂" + Self.grabAttributionLabel(worstIntervalMilliseconds: worstB,
                                                         worstGrabMilliseconds: onFilmB.worstGrabMilliseconds))
        case .visibleToThisRuler:
            XCTFail("两遍都说「还在变」覆盖的时长比对照臂长出一个采样间隔以上 ⇒ 这把尺现在**看得见**这条淡入 ⇒ "
                    + "把 `heatFirstRecord()` 放回 `Scenario.all()` 当真判据，别留这条当免责")
        case .notVisibleToThisRuler:
            emit("MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay heat-first-record："
                + "两遍开臂的时长读数没有落进「≥0.3×声明 且 ≤声明+2×间隔」这条窗口"
                + "（\(ms(elapsedA)) / \(ms(elapsedB)) vs 声明 \(Int(scenario.declaredDurationMilliseconds))ms，"
                + "对照臂 \(ms(elapsedOff))ms）⇒ 今天这把尺没看见这条淡入，只能记「源码已接、产物未量」。"
                + "**注意**：R48 已撤回「这条通道对淡入可见性=0」那句旧结论 —— "
                + "条带图里出现过半透明中间态，所以这是**没抓到**，不是**看不见**")
        }
    }

    /// 按声明取一个成员的**函数体**（花括号配平），取不到 ⇒ 当场红。
    ///
    /// 为什么不用行号区间或"到下一个 MARK 为止"：那两种写法都随排版漂移，
    /// 而守卫随排版漂移就变成"今天恰好还在管"的那种东西。
    /// 取不到时**不许**安静返回空串：空串会让下面所有 `XCTAssertFalse(contains:)` 全绿，
    /// 于是"把那个成员删了"被读成"修好了"（本仓库记过不止一次）。
    ///
    /// 为什么按**行首**匹配而不是 `contains`（R53 实测逼出来的）：守卫自己也要在源码里
    /// 写下被守卫者的名字（`region(in: source, named: "func testXxx")`），
    /// 于是"谁包含这个名字"会先命中**守卫自己的那一行** —— 区域就成了守卫自己的函数体，
    /// 里面当然没有 `XCTFail(`。R53 第一版就是这么红的：三条断言里两条"通过"是因为
    /// 在被搜索的文本里读到了守卫自己写的字面量。扫自身源码的守卫，先把守卫自己摘掉。
    private func region(in code: String, named declaration: String) -> String {
        let lines = code.components(separatedBy: "\n")
        let trimmedDeclaration = declaration.trimmingCharacters(in: .whitespaces)
        guard let start = lines.firstIndex(where: {
            $0.trimmingCharacters(in: .whitespaces).hasPrefix(trimmedDeclaration)
        }) else {
            XCTFail("区域取不到：\(declaration) —— 守卫找不到被守卫的东西时必须红")
            return "\u{0}REGION-NOT-FOUND\u{0}"
        }
        var depth = 0
        var opened = false
        var body: [String] = []
        for index in start..<lines.count {
            let line = lines[index]
            body.append(line)
            depth += line.filter { $0 == "{" }.count
            if line.contains("{") { opened = true }
            depth -= line.filter { $0 == "}" }.count
            if opened, depth <= 0 { break }
        }
        return body.joined(separator: "\n")
    }

    /// 把源码里的每个 `func test…` 切成**它自己的函数体**。
    ///
    /// 切法：按 `\n    func test` 分段，每段截到**第一行正好是四个空格的 `}`** 为止
    /// （SwiftUI 风格的缩进里，那一个花括号就是函数自己的收尾；嵌套的都比它深）。
    /// 为什么不用花括号计数：字符串字面量里有不成对的 `{`（本文件就有 `"\u{0}…"`），
    /// 数出来的 `cursor` 会跨过好几个用例 —— 实测第一版只切出 6 段，
    /// 于是这条守卫既漏扫又报假红。**扫描器坏了的时候守卫是空跑，比红更需要防。**
    static func testCaseBodies(in code: String) -> [(name: String, body: String)] {
        var out: [(name: String, body: String)] = []
        for chunk in code.components(separatedBy: "\n    func test").dropFirst() {
            let lines = chunk.components(separatedBy: "\n")
            guard let firstLine = lines.first else { continue }
            let name = "test" + firstLine.prefix { $0.isLetter || $0.isNumber || $0 == "_" }
            var body: [String] = ["func test" + firstLine]
            for line in lines.dropFirst() {
                if line == "    }" { break }
                body.append(line)
            }
            out.append((String(name), body.joined(separator: "\n")))
        }
        return out
    }

    /// 在一个用例体里找"把归一化分带套到**带捕获那一卷**上"的现场，返回被这样用的胶片变量名。
    ///
    /// 为什么不是"这个函数里既出现了带捕获场景、又出现了 `band:`"：那样会假红。
    /// `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 正是那种形状 —— 它的主判据用整窗那卷
    /// （正常传 `band`），阳性对照用横幅那卷（**不传** `band`）。第一版守卫就是这么误报的，
    /// 而假红的代价是有人去把一条本来正确的判据改松。
    /// 所以这里做一点点数据流：场景变量 → 胶片变量 → 传了非 nil `band` 的调用点。
    static func nestedBandFilms(in body: String, bandFactories: [String]) -> [String] {
        let factories = bandFactories.joined(separator: "|")
        func groups(_ pattern: String) -> [[String]] {
            guard let re = try? NSRegularExpression(pattern: pattern) else { return [] }
            let range = NSRange(body.startIndex..., in: body)
            return re.matches(in: body, range: range).map { match in
                (1..<match.numberOfRanges).compactMap { i in
                    Range(match.range(at: i), in: body).map { String(body[$0]) }
                }
            }
        }
        // ① 哪些变量是"带捕获的场景"，哪些胶片直接来自它。
        let bandScenarios = Set(groups("let (\\w+) = Scenario\\.(?:\(factories))\\(\\)").flatMap { $0 })
        var bandFilms = Set(groups("let (\\w+) = record\\(Scenario\\.(?:\(factories))\\(\\)\\)").flatMap { $0 })
        for pair in groups("let (\\w+) = record\\((\\w+)\\)") where pair.count == 2 {
            if bandScenarios.contains(pair[1]) { bandFilms.insert(pair[0]) }
        }
        // ② 哪些调用点把非 nil 的 band 传给了某卷的帧。
        let passed = groups("Self\\.\\w+\\((\\w+)\\.(?:motionFrames|frames)\\b[^)]*\\bband: (?!nil)").flatMap { $0 }
        return passed.filter { bandFilms.contains($0) }
    }

    /// 带捕获：**便宜必须是真的，而且不能把被测的动效裁掉**（R57 / BACKLOG 77 路 a）。
    ///
    /// 为什么这条判据存在，而不是直接改完就宣布快了：
    /// "捕获区域变小 ⇒ 抓帧变快"这句在本仓库是**推出来的**（R55 的面积判据），
    /// 而推出来的东西可以在实现里静默失效 —— 最省事的一种失效是
    /// `rect` 根本没被 `bitmapImageRepForCachingDisplay` 采纳（帧还是整窗那么大），
    /// 于是成本没降、判据也没变，而我在台账里写"已经收窄了"。
    /// 所以第 ① 格先判**帧的尺寸真的变小了**，再判成本，最后判信号。
    ///
    /// 第 ③ 格是这条改动的**代价**：视野一小，"变化的比例"就变大（分母小了）。
    /// 那不是错（本仓库 R2 之后一直在防的恰恰是"整窗像素把动效归因给错的元素"），
    /// 但它必须是**已知**的：所以这里断言带上的峰值不低于整窗的峰值 ——
    /// 也就是"横幅确实在这一条带里"，而不是我猜它在。
    ///
    /// 两臂各跑两遍并**交错**（带→整窗→带→整窗），比较各自**最好的一遍**：
    /// 顺序跑会让后跑那一臂背上热漂移，读出来的"便宜"里混着时间。
    func testBandCaptureIsCheaperAndStillSeesTheMotion() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.noticeBannerDismiss()
        _ = record(scenario)                       // 预卷：新窗口的头一帧要 250ms 上下（R11）
        let bandFirst = record(scenario)
        let fullFirst = record(scenario, fullCapture: true)
        let bandSecond = record(scenario)
        let fullSecond = record(scenario, fullCapture: true)
        let band = [bandFirst, bandSecond]
        let full = [fullFirst, fullSecond]

        func medianInterval(_ film: Film) -> Double {
            let stamps = film.motionStamps
            guard stamps.count >= 2 else { return .greatestFiniteMagnitude }
            let gaps = stride(from: 1, to: stamps.count, by: 1).map { (stamps[$0] - stamps[$0 - 1]) * 1000 }
            return Self.median(gaps)
        }
        func peak(_ film: Film) -> Double { Self.peak(Self.deltas(film.motionFrames)) }
        func worstGrab(_ films: [Film]) -> Double {
            films.map { $0.worstGrabMilliseconds }.min() ?? -1
        }
        func medianGrab(_ films: [Film]) -> Double {
            Self.median(films.map { $0.medianGrabMilliseconds })
        }
        func motionFrames(_ film: Film) -> Int { Self.transitionFrameCount(Self.deltas(film.motionFrames)) }
        // ① 捕获区域真的生效了吗：帧的像素高度必须变小（不是"我传了个 rect"）。
        guard let bandHeight = bandFirst.frames.first?.height,
              let fullHeight = fullFirst.frames.first?.height,
              let bandWidth = bandFirst.frames.first?.width,
              let fullWidth = fullFirst.frames.first?.width else {
            XCTFail("任何一臂都没帧 ⇒ 这条 A/B 什么都没比（是探针坏了，不是产品没动）")
            return
        }
        XCTAssertLessThan(bandHeight, fullHeight,
            "带捕获出来的帧高 \(bandHeight)px 不小于整窗的 \(fullHeight)px ⇒ rect 被忽略了，"
                + "`captureRect` 是个装饰，而台账里会写着\u{201C}已收窄\u{201D}")
        XCTAssertEqual(bandWidth, fullWidth,
            "带的宽度不该变（`bannerBand` 是整宽 × 48pt）⇒ 变了就是几何写错，不是收窄")
        // ② 便宜必须是真的。整窗那一臂的抓帧成本 R55 实测 38.7–49.7ms，
        //    面积判据在 1/5.9 面积上量到 ~1/4.8 ⇒ 这里要求**至少省一半**，
        //    而不是要求"像拟合说的那样省 4 倍"（拟合是推算，判据只能判已测的形状）。
        let bandMedian = medianGrab(band)
        let fullMedian = medianGrab(full)
        XCTAssertGreaterThan(bandMedian, 0, "带那一臂没量到抓帧成本 ⇒ 归因会是 unmeasured，这条对账没有内容")
        XCTAssertLessThanOrEqual(bandMedian, fullMedian / Self.bandCaptureSavingFloor,
            "带捕获中位 \(String(format: "%.1f", bandMedian))ms，整窗 \(String(format: "%.1f", fullMedian))ms，"
                + "只省了 \(String(format: "%.2f", fullMedian / max(bandMedian, 0.001))) 倍 ⇒ "
                + "BACKLOG 77 路 a 的前提（缩区域能把采样变细）在这台机器上不成立，"
                + "该改的是那条建议而不是把地板调低")
        // ③ 信号不能被裁掉 —— 但**不能用峰值比**（本轮在这里想错了一次，值得留在注释里）：
        //    第一版写的是"带上的峰值 ≥ 整窗的峰值"，实测 0.079 < 0.201 就红了，
        //    看着像"带没盖住横幅"。两个理由都跟"带没盖住"无关：
        //      · 峰值是**相邻两帧**之间变化的像素占比。采样从 44ms 变细到 9ms 之后，
        //        同一次淡出被切成 12 小步，每一步自然比 2 大步小 —— 拿它跨臂比是拿速率比信号。
        //      · 整窗那 0.201 里还含**横幅消失后下面整块列表的位移**（R22 量过的布局塌陷），
        //        那部分本来就不属于这条过渡，是污染而不是信号。
        //    ⇒ 与速率无关的前提是"**首尾之差**"：起点横幅在、终点横幅没了，
        //    带必须装得下这份差别。地板在下面那条 `XCTAssert` 里，由本行的实测决定。
        let bandPeak = max(peak(bandFirst), peak(bandSecond))
        let fullPeak = max(peak(fullFirst), peak(fullSecond))
        func beforeAfter(_ film: Film) -> Double {
            guard let first = film.motionFrames.first, let last = film.motionFrames.last,
                  first !== last || film.motionFrames.count > 1 else { return -1 }
            return Self.deltas([first, last]).first ?? -1
        }
        // ③′ **位置同一性**：带必须就是整窗顶部那一条，而不是"某个在变的地方"。
        //     为什么这条存在：第一版的带子抓错了位置（`isFlipped`，见 `bannerBand` 的注释），
        //     量到的是横幅消失后**下面列表的位移**，而"有变化"那几条前提一条都没拦住
        //     （位移也是变化）。上一版这里用的是一条颜色判据（"带里必须有警告粉"），
        //     它被实测推翻了：横幅那层底调在我给它写的阈值下只有 r−g≈12，
        //     而阈值写的是 >18 ⇒ 恒红，量的既不是产品也不是几何，是一个我猜的数。
        //     ⇒ 换成不需要猜数的形状：带上的首尾差必须与"整窗顶部同高一条带"的首尾差**相等**，
        //     带一旦挪走（底部、中部、整宽变了）这两个数立刻分家（错带实测 0.069 对 0.885，差一个数量级）。
        let bandSpan = max(beforeAfter(bandFirst), beforeAfter(bandSecond))
        let fullSpan = max(beforeAfter(fullFirst), beforeAfter(fullSecond))
        let (headDiff, tailDiff) = Self.bandHeadTailDiff(bandFirst.frames.first, fullFirst.frames.first)
        XCTAssertGreaterThanOrEqual(headDiff, 0, "两臂读不到可比的帧 ⇒ 位置同一性没比成（是探针坏了）")
        XCTAssertLessThanOrEqual(headDiff, Self.bandMustMatchFullHeadFraction,
            "带的那一帧与整窗那一帧的**同一头 \(bandHeight) 行**有 \(String(format: "%.3f", headDiff)) 的像素不同 ⇒ "
                + "`captureRect` 没照它声称的那个 rect 抓（rect 变了、缓存串了、或者抓帧器换了坐标系）。"
                + "这时候带上的任何读数都不是「横幅那一条」的读数")
        XCTAssertGreaterThanOrEqual(tailDiff, Self.bandMustDifferFromFullTailFraction,
            "带的那一帧与整窗**另一头** \(bandHeight) 行只差 \(String(format: "%.3f", tailDiff))（要求 ≥ "
                + "\(Self.bandMustDifferFromFullTailFraction)）⇒ 带落在哪一头都无所谓，因为两头一模一样，"
                + "上面那条同一性判据就成了恒真的装饰（本仓库「自适应阈值恒真」那一族）")
        XCTAssertGreaterThan(bandSpan, 0, "带那一卷读不出首尾差 ⇒ 一帧或零帧，这条对账没有内容")
        XCTAssertGreaterThan(fullSpan, 0, "整窗那一卷读不出首尾差 ⇒ 同上")
        XCTAssertGreaterThanOrEqual(bandPeak, Self.minimumVisibleChange,
            "带上的峰值低于可见地板 ⇒ 这一卷里看不见任何变化，`premise-not-visible` 会把它记成没测到")
        XCTAssertGreaterThanOrEqual(bandSpan, Self.bandMustHoldChangeFraction,
            "带上的首尾差只有 \(String(format: "%.3f", bandSpan))（整窗 \(String(format: "%.3f", fullSpan))）⇒ "
                + "横幅不在这一条带里，或者它已经挪走了。这时带上的任何判定都是在量一片别的东西，"
                + "而 `Scenario.bannerBand` 那个 48pt 常数就是错的")
        // ④ 收窄之后必须**更能看清过程**（这才是这一改动的目的）：过渡帧数不许变少。
        XCTAssertGreaterThanOrEqual(max(motionFrames(bandFirst), motionFrames(bandSecond)),
                                    max(motionFrames(fullFirst), motionFrames(fullSecond)),
                                    "带捕获之后的过渡帧数反而比整窗少 ⇒ 采样变细没换来过程，"
                                        + "这一臂仍然只能记 not-run，那这条路就白走了")
        // ⑤ 采样必须真的变细（这才是要的目的：让那一臂从 clock-coarse 变成判得到）。
        XCTAssertLessThanOrEqual(medianInterval(bandSecond), medianInterval(fullSecond),
            "带捕获之后整卷中位间隔没有变细 ⇒ 省下的钱没进采样率，这一臂仍然判不了")
        emit("MOTION_BAND dismiss 带：首尾差=\(String(format: "%.3f", bandSpan)) "
              + "整窗首尾差=\(String(format: "%.3f", fullSpan)) "
              + "位置同一性 带vs整窗头=\(String(format: "%.3f", headDiff)) "
              + "带vs整窗尾=\(String(format: "%.3f", tailDiff)) ｜ "
              + "带：抓帧中位=\(String(format: "%.1f", bandMedian))ms "
              + "峰值=\(String(format: "%.3f", bandPeak)) 过渡帧数=\(max(motionFrames(bandFirst), motionFrames(bandSecond))) "
              + "间隔中位=\(String(format: "%.0f", medianInterval(bandSecond)))ms 帧=\(bandWidth)x\(bandHeight)px ｜ "
              + "整窗：抓帧中位=\(String(format: "%.1f", fullMedian))ms "
              + "峰值=\(String(format: "%.3f", fullPeak)) 过渡帧数=\(max(motionFrames(fullFirst), motionFrames(fullSecond))) "
              + "间隔中位=\(String(format: "%.0f", medianInterval(fullSecond)))ms 帧=\(fullWidth)x\(fullHeight)px ｜ "
              + "最慢一次抓帧 带=\(String(format: "%.1f", worstGrab(band)))ms 整窗=\(String(format: "%.1f", worstGrab(full)))ms")
        writeStrip("dismiss-带捕获", bandFirst.motionFrames)
        writeStrip("dismiss-整窗", fullFirst.motionFrames)
    }

    /// 逐帧堆叠图里两帧之间的分隔线宽度（R59）。写图与判图必须读同一个常数：
    /// 各自写一个字面量，哪天改了一处，另一处就会红在「尺寸不对」上，而理由是假的。
    static let stackGap: Int = 2

    /// 图标质心的跨度算"在动"的分界（**原始像素**，本机 2x ⇒ ≈2pt）（R59）。
    ///
    /// 这条线是**尺子的**分类线，不是产品的判据，所以它进代码而不是留在文字里：
    /// 本机五遍读到的跨度是 12.7 / 9.4 / 12.7 / 5.3 / 9.4px
    /// （`.scratch/motion-audit-2/r59_motion_readings.log` 第 3 节），全在线上方 ⇒
    /// 本轮没有一格结论挂在这条线下面，"它在动"不是这条线造出来的。
    /// 反过来，若哪天读数掉到 3px，结论会翻成"原地淡出"，那时该先怀疑的是这条线。
    static let trackMoveClassifierPixels: Double = 4

    /// 外框上下沿"算不算挪了"的容差（原始像素，R59）。
    ///
    /// 这条线**本轮没有标定过**，写清楚是为了别让它冒充判据：它只决定"形状分类"那句话
    /// 怎么措辞，没有任何一格结论挂在它上面。本机五遍的外框挪动量级是 0–4px，
    /// 而**全帧质心**的漂移是 7.7–12.7px（那条不是位移，见 `testBannerOutTracksWhetherItFadesOrSlides`）
    /// ⇒ 4px 这个量恰好卡在两者中间，所以这一格分不开的时候，读数会直接说"分不开"，
    ///   不会替我挑一个好看的解释。
    static let trackEdgeTolerancePixels: Int = 2

    /// 横幅撤走时，左右两栏的**落定时刻**要有一个数（R59，只测不判）。
    ///
    /// 为什么这条存在：R59 第一次把带捕获那卷按原始像素堆成逐帧图
    /// （`testBannerFrameStacksAreReadableEvidence`）之后，看图看见一个说不通的状态 ——
    /// 第 4~5 帧（约 45–55ms）里，侧栏那一侧（x<280pt）的横幅文字被**横着切掉半截**、
    /// 搜索框已经滑进横幅的位置；而详情区那一侧（x>280pt）同一行文字的尾巴与那颗"知道了"
    /// 还在原来的高度上。`ContentView.swift:8` 里 `notices` 是**整幅**的一行（在 splitView 之上），
    /// 一条整幅视图不该有两个 y。
    ///
    /// **本轮后半段把这条自己写的那个"时长差"证伪了**（第一次读数写进台账时它还是结论）：
    /// 五遍的 `侧栏过渡帧数=8–11 / 详情区=13` 用的是 `transitionFrameCount`，
    /// 而它的门槛是**各自峰值**的 15% —— 侧栏峰值 0.305 ⇒ 线 0.046，详情区 0.237 ⇒ 线 0.036。
    /// 两条线不一样，比出来的"谁先停"就是**墨量差**，不是时间差。
    /// 换成同一条绝对线（`sharedMovingFloor`）之后：本机五遍两栏**"最后一个还在变的帧号"完全相同**
    /// （16/16、17/17、17/17、17/17、16/16，见 `r59_motion_readings.log` 第 3.1 节；
    ///  那一帧两栏同时出现 ~0.10/~0.11 的抖动，是同一次回流，不是先后）。
    /// ⇒ "侧栏先落定 2–5 帧"这句话作废。留下的只有**看图看见的那半截字**，
    /// 它是一个形状/裁切问题，不是时长问题，仍然要真机才能判（批次 59.1、BACKLOG 85 已改写）。
    ///
    /// 判据形状：两条"必须成立"的前提（两栏都得真的在变）+ 一条"读数必须由数字生成"
    /// 的措辞函数（`columnSettlementVerdict`，被合成真值表钉住）。仍然**不判产品**。
    func testBannerDismissColumnAsymmetryIsMeasured() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.noticeBannerDismiss()
        _ = record(scenario)
        let film = record(scenario)
        let frames = film.motionFrames
        guard frames.count > 6 else {
            XCTFail("只抓到 \(frames.count) 帧 ⇒ 这条测量没有过程可分栏（是采样，不是产品）")
            return
        }
        // 侧栏 280pt / 窗口 760pt ⇒ 归一化分界线 0.368。两栏各取整条带的高度。
        let sidebar = CGRect(x: 0, y: 0, width: 0.368, height: 1)
        let detail = CGRect(x: 0.368, y: 0, width: 1 - 0.368, height: 1)
        let left = Self.deltas(frames, band: sidebar)
        let right = Self.deltas(frames, band: detail)
        // 前提：两栏都必须**真的在变**，否则"两栏时长差多少"是两句空话。
        XCTAssertGreaterThan(left.max() ?? 0, Self.minimumVisibleChange,
            "侧栏那一侧在这卷里最大相邻差只有 \(String(format: "%.3f", left.max() ?? -1)) ⇒ 分界线算错了，"
                + "或者这一卷根本没拍到横幅")
        XCTAssertGreaterThan(right.max() ?? 0, Self.minimumVisibleChange,
            "详情区那一侧最大相邻差只有 \(String(format: "%.3f", right.max() ?? -1)) ⇒ 同上")
        let leftSettled = Self.transitionFrameCount(left)
        let rightSettled = Self.transitionFrameCount(right)
        let interval = Self.sampleIntervalMilliseconds(film.motionStamps)
        let shared = Self.sharedMovingFloor([left, right])
        let lastLeft = Self.lastMovingFrame(left, floor: shared) ?? -1
        let lastRight = Self.lastMovingFrame(right, floor: shared) ?? -1
        // 前提：同一条线下两栏都得**有**一个"最后还在变"的帧，否则下面的对比是空话。
        XCTAssertGreaterThanOrEqual(lastLeft, 0,
            "侧栏在共享线 \(String(format: "%.4f", shared)) 下一次变化都没有 ⇒ 这条对比作废")
        XCTAssertGreaterThanOrEqual(lastRight, 0, "详情区同上")
        emit("MOTION_COLUMN dismiss 分栏 ｜ 旧轴(各自峰值归一) 侧栏=\(leftSettled) 详情区=\(rightSettled) "
             + "差=\(abs(leftSettled - rightSettled))帧 ⇒ **这条轴的差是墨量，不是时间**（见函数注释） "
             + "｜ 新轴(同一条绝对线 \(String(format: "%.4f", shared))，=两栏较大峰值×\(Self.stepFloorRatio)) "
             + "最后还在变的帧号 侧栏=\(lastLeft) 详情区=\(lastRight) "
             + "采样≈\(interval)ms ｜ 侧栏逐帧=[\(left.map { String(format: "%.3f", $0) }.joined(separator: " "))] "
             + "｜ 详情区逐帧=[\(right.map { String(format: "%.3f", $0) }.joined(separator: " "))] "
             + "⇒ \(Self.columnSettlementVerdict(left: left, right: right))")
    }

    /// `columnSettlementVerdict` 的真值表（R59，合成用例）。
    ///
    /// 为什么要有这一条：本轮那句"侧栏先落定 2–5 帧"就是从**没有真值表**的措辞里长出来的。
    /// 把措辞变成函数之后，四种形状必须先在这里说清，才轮到真卷去跑。
    /// **不覆盖管线**：这四组数组是人造的，它们钉的是尺子的措辞；
    /// 产品那一条是 `testBannerDismissColumnAsymmetryIsMeasured`。
    func testSharedFloorColumnComparisonIsATruthTable() throws {
        // (a) 本轮真卷的形状：两栏在**同一帧**停，但各自峰值归一的旧尺子给不同帧数。
        let aLeft: [Double] = [0.000, 0.305, 0.100, 0.040, 0.000]
        let aRight: [Double] = [0.000, 0.237, 0.080, 0.040, 0.000]
        XCTAssertEqual(Self.sharedMovingFloor([aLeft, aRight]), 0.305 * Self.stepFloorRatio,
            "共享线必须由**较大**那个峰值导出，否则又变成各自归一")
        XCTAssertNotEqual(Self.transitionFrameCount(aLeft), Self.transitionFrameCount(aRight),
            "旧轴在这组上必须给两个数 —— 它给不出，就说明这组没复刻到真卷的形状（墨量差冒充时长差）")
        XCTAssertTrue(Self.columnSettlementVerdict(left: aLeft, right: aRight).contains("同一帧"),
            "两栏在同一帧停 ⇒ 措辞不许出现\u{201C}先落定\u{201D}这类时间差的说法")

        // (b) 真的有时间差：详情区多演了一帧，而且那一帧在共享线之上。
        let bRight: [Double] = [0.000, 0.237, 0.080, 0.100, 0.000]
        let bVerdict = Self.columnSettlementVerdict(left: aLeft, right: bRight)
        XCTAssertTrue(bVerdict.contains("差 1 帧"), "读数应说\u{201C}差 1 帧\u{201D}，实际：\(bVerdict)")

        // (c) 两栏都平：不许生成任何\u{201C}谁先谁后\u{201D}。
        let flat: [Double] = [0.000, 0.000, 0.000]
        XCTAssertTrue(Self.columnSettlementVerdict(left: flat, right: flat).contains("作废"),
            "整段没变化时这条对比必须自认作废")

        // (d) 只有一栏在变 ⇒ 分界线算错了，同样不许冒充结论。
        let dVerdict = Self.columnSettlementVerdict(left: aLeft, right: flat)
        XCTAssertTrue(dVerdict.contains("分界线"), "只有一栏在变应报分界线/框选错，实际：\(dVerdict)")
    }

    /// 撤走那一下，横幅到底是**在原地淡出**还是**滑出去**（R59）。
    ///
    /// 为什么重新量一次：R22 当年写的是"帧 2 是原地的半透明 ⇒ 它是淡出，不是塌陷" ——
    /// 那是**一帧中间态**给的结论（当时整卷只拍得到 1 格中间态）。R57 之后同一卷有 10–13 格，
    /// 所以这句话现在要么被证实、要么被推翻，不该继续当既有事实引用。
    ///
    /// 量法：横幅左边那颗警告图标（`exclamationmark.arrow.circlepath`，实心红）是这一条带里
    /// 唯一"高饱和红 + 位置已知"的东西。逐帧求它的**质心 y**（只看侧栏那一段宽度，
    /// 免得被详情区的回流污染），再看它相对第一帧挪了多少、同时它的像素数怎么变。
    /// ⇒ 质心基本不动而像素数在掉 = 原地淡出；质心往上跑 = 有位移。
    ///
    /// 本机五遍的实测（`.scratch/motion-audit-2/r59_motion_readings.log` 第 3.2 节）：
    /// **全帧**质心跨度 11.0 / 9.4 / 9.4 / 7.7 / 12.7 px —— 第一遍读数出来时我把它写成了"图标在上移"，
    /// 那是**这条尺自己在动**：图标淡到判色线以下时还活着的只剩一部分，质心必然朝那半边漂。
    /// 所以本轮补了两条不靠"整卷都看得见它"的轴：强帧（像素数 ≥ 首帧一半）的质心跨度，
    /// 以及强帧的**外框**上下沿（`MOTION_TRACK_BOX`）。五遍实测：
    /// 强帧质心跨度 2.6 / 0 / 0 / 0 / 0 px（都在那条 4px 分类线以下），
    /// 外框 **4/5 遍一格没挪**（首末都是 [29,50]），只有第 1 遍下沿上移 4px。
    /// ⇒ 能说的只有：**原来那个"上移 6.5pt"作废**（它比外框能看到的任何数都大 3 倍以上）；
    /// 但"绝对没动"也不许写成结论 —— 那 4px 正好落在"淡出时高饱和边缘先脱落"的量级里，
    /// ±2px 的容差分不开"边缘脱落"与"一边被裁"。要分开得换一条不吃饱和度的轴
    /// （跟几何轮廓走，而不是跟颜色走）—— 那是下一轮的活，不在本轮顺手加。
    /// 顺带：**R22 那句"它是淡出，不是塌陷"在"淡出"这一半被证实**（当年只有一帧可看，结论对但没证据）。
    /// 剩下的"横幅那半截字"是另一件事，归 BACKLOG 85；它的"时长差"那半边本轮也作废了
    /// （见 `testBannerDismissColumnAsymmetryIsMeasured`）。这一条仍然**只测不判**产品好坏。
    func testBannerOutTracksWhetherItFadesOrSlides() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.noticeBannerDismiss()
        _ = record(scenario)
        let film = record(scenario)
        let frames = film.motionFrames
        guard frames.count > 6 else {
            XCTFail("只抓到 \(frames.count) 帧 ⇒ 没有过程可跟踪")
            return
        }
        func iconBox(_ image: CGImage) -> (top: Int, bottom: Int, y: Double, pixels: Int) {
            let bitmap = Self.raster(image)
            guard bitmap.width > 0, bitmap.height > 0,
                  bitmap.pixels.count == bitmap.width * bitmap.height * 4 else { return (-1, -1, -1, 0) }
            var sum = 0.0, hit = 0, top = -1, bottom = -1
            for y in 0..<bitmap.height {
                // 只看侧栏那一段（图标在 x≈30–50pt ⇒ 60–100px），避开详情区的回流。
                for x in 40..<200 where x < bitmap.width {
                    let p = (y * bitmap.width + x) * 4
                    let r = Int(bitmap.pixels[p]), g = Int(bitmap.pixels[p + 1]), b = Int(bitmap.pixels[p + 2])
                    if r > 120, r - g > 60, r - b > 60 {
                        sum += Double(y); hit += 1
                        if top < 0 { top = y }
                        bottom = y
                    }
                }
            }
            // 缓冲区第 0 行 = 画面顶边（R57 实测，见 `changedFraction` 的注释）。
            // ⇒ 数值变小 = 在画面上**往上**走。
            return (top, bottom, hit == 0 ? -1 : sum / Double(hit), hit)
        }
        let track = frames.map(iconBox)
        let seen = track.filter { $0.pixels > 0 }
        // 地板 4：本机连跑五遍，认得出那颗图标的帧数是 6 / 5 / 5 / 5 / 6（最小 5，地板留一格余量），
        // 而整条卷只有 27 帧 —— 后面那 21~22 帧它已经淡到判色线以下。
        // 同一批里"强帧"（像素数 ≥ 首帧一半）只有 4~5 帧：判"在不在动"用的就是那几帧。
        // 为什么不是 1 或 2：一条只剩一帧可跟踪的"跟踪"，给出的跨度永远是 0，
        // 而那正好长得像本轮想排除的那个结论（"原地不动"）。M303 打的就是这一格
        // （把 x 区间清空 ⇒ `seen.count = 0`）。
        // 用 guard 而不是 XCTAssert：M303 第一次跑就把这一格打成**崩溃**而不是红 ——
        // 断言失败之后代码继续往下走，`seen[0]` 在空数组上越界，测试进程直接没了，
        // 于是"Test Case … failed"那行根本没打出来，电池只能报 BROKEN-MUTATION。
        // 红要能被读，崩溃不能（同一族：守卫里的 try! 把红伪装成没跑）。
        // R60 改：这一格在 runner 上是**假红**。run 38586812301 原文：
        //   `整卷只找到 0 帧里有那颗红色图标`（本机同一把尺是 5–6 帧）。
        // 0 帧不是"过程太快没抓到"，是**那颗图标在这台机器上根本没被认出来**：
        // runner 是 1x 缩放（带卷 760×48px），这颗 ~22px 高的实心红符号几乎没有纯色核心像素，
        // `r>120, r-g>60, r-b>60` 一条都不满足 ⇒ 判色前提在这台机器上不成立。
        // 所以它不能红：红会说成"产品没画图标"。也不能反过来当"没动画"的证据。
        // 用 MOTION_TRACK_VOID 而不是 MOTION_NOT_RUN：后者是覆盖率闸门的输入，
        // 而这一臂**确实被判到了**（`MOTION_SUMMARY` 里有它），作废的只是这条新测量。
        // 顺手把诊断一起发出去（缩放、单帧最多几根红像素、扫过的 x 范围），
        // 下一轮据此决定是放宽判色还是把窗口按 pt 表达 —— 不靠猜。
        // 缩放不假设，从帧自己读出来：runner 的带卷是 760px 宽（1x），本机是 1520px（2x），
        // 而那条扫描窗是**写死成像素**的 ⇒ 两边看的不是同一块内容（R60）。
        let scale = Double(frames[0].width) / 760.0
        let maxRedPixels = track.map { $0.pixels }.max() ?? 0
        guard seen.count >= 4 else {
            emit("MOTION_TRACK_VOID dismiss 认得出图标的帧=\(seen.count)/\(frames.count) "
                 + "单帧最多红像素=\(maxRedPixels) 缩放=\(String(format: "%.2f", scale))x "
                 + "扫描窗=写死的 x∈[40,200)px（=\(Int(40 / scale))…\(Int(200 / scale))pt） "
                 + "⇒ 这条测量在这台机器上作废（判色前提不成立），"
                 + "既不许写进已交付，也不许反过来当\u{201c}产品没画图标/没动画\u{201d}的证据")
            // 但**不许两边都不红**：2x 那台机器上这个前提是被实测撑住的（本机五遍 5–6 帧），
            // 所以 2x 上认出 0 帧只能是跟踪被弄坏了 —— M303（把扫描窗清空）必须红在这一格。
            XCTAssert(scale < 2.0,
                "在 \(String(format: "%.2f", scale))x 这台机器上，五遍实测都能认出 5–6 帧图标；"
                + "这一卷只认出 \(seen.count) 帧（单帧最多 \(maxRedPixels) 根红像素）⇒ "
                + "是**跟踪坏了**（窗口/判色/带的位置），不是产品没画那颗图标")
            return
        }
        let ys = seen.map { $0.y }
        let spread = (ys.max() ?? 0) - (ys.min() ?? 0)
        let firstPixels = seen.first?.pixels ?? 0
        let lastPixels = seen.last?.pixels ?? 0
        // 只看"强帧"（像素数不低于首帧一半）的**外框**，用来把三种形状分开：
        // 淡出会让高饱和边缘先掉到判色线以下 ⇒ 框是从两头**往里**缩的，
        // 拿最后一帧的框去比第一帧，就会把"淡"读成"裁"。强帧还够得着判色线，边缘没掉。
        //   上下沿同向等量移动  ⇒ 整颗图标在平移（真的带位移）
        //   上沿不动、下沿上移  ⇒ 下边被盖住/裁掉（内容往上顶到横幅上）
        //   下沿不动、上沿上移  ⇒ 上边被裁
        //   两头都往里           ⇒ 只是淡
        let strong = seen.filter { $0.pixels * 2 >= firstPixels }
        let ref = strong.first ?? seen[0]
        let last = strong.last ?? seen[seen.count - 1]
        let topShift = Double(last.top - ref.top)
        let bottomShift = Double(last.bottom - ref.bottom)
        let tol = Double(Self.trackEdgeTolerancePixels)
        let shape: String
        switch (abs(topShift) <= tol, abs(bottomShift) <= tol) {
        case (true, true): shape = "外框没挪 ⇒ 只是淡"
        case (false, false):
            shape = abs(topShift - bottomShift) <= tol
                ? "上下沿同向等量(差\(String(format: "%.0f", abs(topShift - bottomShift)))px) ⇒ 整颗图标在平移"
                : "两头反向 ⇒ 框在变形（淡/裁混在一起），分不开"
        case (true, false): shape = "上沿不动、下沿\(bottomShift < 0 ? "上移" : "下移")\(String(format: "%.0f", abs(bottomShift)))px ⇒ 一边被盖住/裁掉"
        case (false, true): shape = "下沿不动、上沿\(topShift < 0 ? "上移" : "下移")\(String(format: "%.0f", abs(topShift)))px ⇒ 一边被裁"
        }
        emit("MOTION_TRACK_BOX dismiss 强帧数=\(strong.count) 外框 首=[\(ref.top),\(ref.bottom)] "
             + "末=[\(last.top),\(last.bottom)] 上沿移=\(String(format: "%.0f", topShift))px "
             + "下沿移=\(String(format: "%.0f", bottomShift))px（负=往上）"
             + "｜ 容差±\(Self.trackEdgeTolerancePixels)px 是尺子的线 "
             + "⇒ 形状分类：\(shape)")
        // 结论必须带着**声明**一起读：`.bannerOut` 的形状只设 `isExit`、不设 `slides`
        // （`MotionCatalog.shape(for:)`），所以"质心在动"绝不能被打印成"这一版是滑走"——
        // 那是把**别的来源**（布局塌陷 / 带内被裁 / 捕获通道）的位移，记到了动画设计头上。
        // 到底是哪一种，这条量的通道分不开 ⇒ 读数里只写"排除了什么"，不写解释。
        let declared = MotionCatalog.shape(for: .bannerOut, reduceMotion: false).slides
        let saysSlides = declared != .none
        // **判"在不在动"用强帧的跨度，不用全帧的**：淡到后面判色线只吃得到图标的一部分，
        // 质心会朝"还活着的那一半"漂 —— 本机五遍全帧跨度 7.7~12.7px，而强帧跨度只有
        // 2.6/0/0/0/0px、外框 4/5 遍一格没挪。拿全帧跨度说"它在动"，说的其实是**阈值在动**。
        // （这是本轮第二次把读数从尺子自己的产物上搬回画面：第一次是分栏那条。）
        let strongYs = strong.map { $0.y }
        let strongSpread = (strongYs.max() ?? 0) - (strongYs.min() ?? 0)
        let moves = strongSpread > Self.trackMoveClassifierPixels
        let classifier = "（分类线 \(String(format: "%.0f", Self.trackMoveClassifierPixels))px≈2pt："
            + "这条线是**尺子**的分界，不是产品的判据）"
        emit("MOTION_TRACK dismiss 图标质心y(px,2x) 全帧=\(ys.map { String(format: "%.0f", $0) }) "
             + "全帧跨度=\(String(format: "%.1f", spread))px（**别拿这条当位移**，见注释） "
             + "｜ 强帧=\(strongYs.map { String(format: "%.0f", $0) }) 强帧跨度=\(String(format: "%.1f", strongSpread))px "
             + "像素数 首=\(firstPixels) 末=\(lastPixels) "
             + "帧数=\(track.count) 有图标帧=\(seen.count) 强帧数=\(strong.count) "
             + "｜ .bannerOut 声明的位移档=\(String(describing: declared)) "
             + "⇒ 观察\(moves ? "在动" : "不动")\(classifier)"
             + "/声明\(saysSlides ? "带位移" : "不带位移")"
             + "：" + (moves && !saysSlides
                ? "只排除了一件事：这不是设计声明的滑走（`slides=.none`）。"
                    + "上移从哪来（行高在塌 / 带内被裁 / 捕获通道产物）本轮的量分不开 ⇒ 不写解释，见 BACKLOG 85"
                : (moves ? "设计与观察一致：声明了位移、也确实带位移"
                    : "设计与观察一致：图标的外框不动、像素在掉 ⇒ **原地淡出**")))
        // 唯一敢判的一格：跨度必须落在"能读懂"的量级里 —— 超过半条带（>48px）说明
        // 我跟丢了这个图标（判色阈值抓到了别的东西），那时这条读数没有意义，要红而不是静默。
        XCTAssertLessThanOrEqual(spread, 48,
            "图标质心的纵向跨度 \(String(format: "%.1f", spread))px 已经超过半条带 ⇒ 跟丢了的跟踪"
                + "不能拿来回答\u{201C}淡出还是滑走\u{201D}（先修判色，再谈结论）")
    }

    /// 逐帧图必须**存在、按原始像素堆、且真的不是一叠同一张图**（R59）。
    ///
    /// 为什么单独一条：这一轮的"真实视觉审查"要看的就是这几张。带捕获那一卷只有 96px 高，
    /// 而 `writeStrip` 按 `width/2` 画 ⇒ 横幅那条被压成 38px 的一行色块，
    /// "看过中间态"这句话就没有承载物了。所以这里判三件事：文件在不在、
    /// 尺寸是不是**原始像素**（不是除二）、以及这一叠里至少有一对帧真的不同
    /// —— 最后那条是关键：一叠同一张图也能写出正确尺寸的文件。
    func testBannerFrameStacksAreReadableEvidence() throws {
        try skipUnlessEnabledAndCapable()
        for scenario in [Scenario.noticeBanner(), Scenario.noticeBannerDismiss()] {
            _ = record(scenario)                       // 预卷：头一帧要 250ms 上下（R11）
            let film = record(scenario)
            let frames = Array(film.motionFrames.prefix(10))
            guard frames.count > 1, let first = frames.first else {
                XCTFail("\(scenario.name) 只截到 \(frames.count) 帧 ⇒ 没有中间态可看，"
                    + "这一轮的看图不成立（是采样不够细，不是产品没动）")
                continue
            }
            let gaps = Self.stackGap
            guard let url = writeStack("\(scenario.name)-逐帧", frames) else {
                XCTFail("\(scenario.name) 的逐帧图没写出来 ⇒ 台账里那句「看过」是空的")
                continue
            }
            guard let png = try? Data(contentsOf: url),
                  let rep = NSBitmapImageRep(data: png) else {
                XCTFail("写出来的 \(url.lastPathComponent) 读不回来 ⇒ 那张图谁也没法看")
                continue
            }
            XCTAssertEqual(rep.pixelsWide, first.width,
                "逐帧图宽 \(rep.pixelsWide)px，帧宽 \(first.width)px ⇒ 又被缩过，看图的人看到的是色块")
            XCTAssertEqual(rep.pixelsHigh, (first.height + gaps) * frames.count,
                "逐帧图高 \(rep.pixelsHigh)px，按 \(frames.count) 帧×(\(first.height)+\(gaps)) 应该是 "
                    + "\((first.height + gaps) * frames.count)px ⇒ 少画了帧，而台账会按帧数说\u{201C}逐帧看过\u{201D}")
            let adjacent = Self.deltas(frames)
            XCTAssertGreaterThan(adjacent.max() ?? 0, Self.minimumVisibleChange,
                "这一叠 \(frames.count) 帧里最大相邻差只有 \(String(format: "%.3f", adjacent.max() ?? -1)) ⇒ "
                    + "文件在、尺寸对，但**十张是同一张**：那种图能骗过任何只看文件的审查")
            emit("MOTION_REVIEW \(scenario.name) 逐帧图=\(url.lastPathComponent) 帧数=\(frames.count) "
                 + "尺寸=\(rep.pixelsWide)x\(rep.pixelsHigh) 最大相邻差=\(String(format: "%.3f", adjacent.max() ?? -1)) "
                 + "逐帧=[\(adjacent.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
        }
    }

    /// 带捕获必须真的接在横幅**两臂**上（R57 / BACKLOG 77 结案的另一半）。
    ///
    /// 为什么 A/B 那条不够：`testBandCaptureIsCheaperAndStillSeesTheMotion` 判的是
    /// "带这件事值不值"，而它读的是**自己当场构造的**场景。哪天有人把某一臂的
    /// `captureRect:` 删了（或新加一臂忘了传），那条 A/B 仍然全绿 —— 它比的是"带 vs 整窗"，
    /// 不是"这一臂用没用带"。于是"横幅两臂都判得到"会安静退回一臂，
    /// 而覆盖地板要等下一次 not-run 才报（R44 那一族就是这么发现的）。
    ///
    /// 不开 `CLIPBOARD_HISTORY_UI_MOTION` 门：理由与 `testMotionReadingsUseTheFileChannel` 同 ——
    /// 它管的是接线，而 CI 的全量运行正是唯一每次都跑得到接线的地方。
    func testBandCaptureIsWiredIntoBothBannerArms() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        // 判据本身必须**能说不**（R56 那一族：一条"什么都找不到也算过"的扫描是装饰）。
        // 所以把它写成可喂合成文本的闭包，正对照与真场景走同一个谓词。
        func usesBand(_ text: String) -> Bool { text.contains("captureRect: Scenario.bannerBand") }
        XCTAssertFalse(usesBand("Scenario(name: \"x\", size: s) { store in }"),
                       "谓词在一段**没有** captureRect 的场景构造上返回了 true ⇒ 它恒真，"
                           + "下面两条就只是把注释抄了一遍")
        for name in ["static func noticeBanner()", "static func noticeBannerDismiss()"] {
            let body = region(in: source, named: name)
            XCTAssertTrue(usesBand(body),
                "\(name) 不再声明 captureRect ⇒ 这一臂回到整窗捕获（实测抓一帧 39.5–39.8ms、"
                    + "整卷中位间隔 44–45ms），而登记表已经写着 must_judge=true —— "
                    + "回到 R52 那种「两台机器都判不到」的形状，只是这次会红在 UNDERCOVERED")
        }
        // 接线：rect 必须真的进抓帧器，而不是被算出来又扔掉。
        let wiring = region(in: source, named: "private func recordFrames")
        XCTAssertTrue(wiring.contains("rect: capture"),
                      "`recordFrames` 算出了 capture 却没传给 `Grabber` ⇒ 带捕获是装饰，"
                          + "而 A/B 那一臂的「便宜」会变成两边一样")
        let tickBody = region(in: source, named: "func tick()")
        XCTAssertTrue(tickBody.contains("rect ?? view.bounds"),
                      "`Grabber.tick` 不再使用 rect ⇒ 上面那条传进去的参数没人读，"
                          + "两臂量的都是整窗，A/B 的全部结论作废")
        // 登记表与这条守卫必须同向：两臂都要求判到。
        // 找文件用**往上走**而不是"数固定层数"：第一版这里写死两层，
        // 于是算出来的是 `ClipboardHistory/scripts/…`，守卫红在"读不到"上
        // —— 红是对的形状（找不到必须红），但理由是我自己数错了目录。
        // 同一个形状 `productSource(named:)` 已经在用（有界上溯，找不到就红）。
        var dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var registryURL: URL? = nil
        for _ in 0..<6 {
            let candidate = dir.appendingPathComponent("scripts/motion_floor_expectations.json")
                .standardizedFileURL
            if FileManager.default.fileExists(atPath: candidate.path) {
                registryURL = candidate
                break
            }
            dir = dir.deletingLastPathComponent()
        }
        guard let found = registryURL,
              let registry = try? String(contentsOf: found, encoding: .utf8) else {
            XCTFail("读不到 scripts/motion_floor_expectations.json ⇒ 这条守卫没比成就红：登记表不在，"
                + "正是「带捕获接上了但没人要求判到」那种半修状态最可能的现场")
            return
        }
        for arm in ["notice-banner", "notice-banner-dismiss"] {
            XCTAssertTrue(registry.contains("\"\(arm)\": {\n      \"must_judge\": true"),
                "登记表里 \(arm) 不是 must_judge=true ⇒ 带捕获白做："
                    + "判得到也没人要求它判到，掉回 not-run 时闸门不会红")
        }
    }

    /// 归一化分带矩形必须落在它**声称的那一头**（R58 / BACKLOG 80）。
    ///
    /// 为什么这条存在：R57 实测发现 `changedFraction(band:)` 把带**上下颠倒**了 ——
    /// 那里的注释写着"缓冲区第 0 行是画面的底边"，而实测第 0 行是**顶边**：
    /// 带那一帧与整窗那一帧的第 0–95 行逐像素相同（0.000）、与末尾 96 行差 0.954
    /// （`.scratch/motion-audit-2/r57_motion_readings.log` 的 `MOTION_BAND` 行）。
    /// 后果是这个文件里 7 处 `band:` 量的都是镜像位置，
    /// 而**关于中线对称的那两条（详情区 y 0.12–0.88、列表中部 y 0.35–0.65）永远不会红** ——
    /// 这是"量错地方"最坏的一种：尺子看起来在判，实际在判另一块，且没有任何一条判据会喊。
    ///
    /// 为什么用合成位图而不是真帧：真帧只能证明"某一处对不上"，
    /// 合成位图能证明**四个方向**（上/下/左/整幅）各自的对应关系 ——
    /// 颠倒这种错恰恰只在"另一头"才暴露，只测一头会把它放过去。
    /// 锚点（"缓冲区第 0 行 = 画面顶边"）来自上面那次实测，不是注释、不是 CG 的推理。
    func testBandRectMapsToTheEndItClaims() {
        let width = 70, height = 100
        let top = CGRect(x: 0, y: 0, width: 1, height: 0.2)         // 画面**顶边**那 20%
        let bottom = CGRect(x: 0, y: 0.8, width: 1, height: 0.2)    // 画面**底边**那 20%
        let left = CGRect(x: 0, y: 0, width: 0.2, height: 1)
        let right = CGRect(x: 0.8, y: 0, width: 0.2, height: 1)
        let head = Self.syntheticPair(width: width, height: height, differingRows: 0..<20)
        let tail = Self.syntheticPair(width: width, height: height, differingRows: 80..<100)

        // ⓪ 夹具自己先要能判红黑：差异不成立时后面每一格都无从解释（本仓库"探针不自检"那一族）。
        XCTAssertEqual(Self.changedFraction(head.0, head.1, band: nil),
                       Self.changedFraction(tail.0, tail.1, band: nil), accuracy: 0.001,
                       "两份合成位图在整幅上读出的变化占比不相等 ⇒ 夹具本身不对称，"
                           + "下面的方向判据就分不清是映射坏了还是数据坏了")
        XCTAssertGreaterThan(Self.changedFraction(head.0, head.1, band: nil), 0,
                             "整幅都读不到差异 ⇒ 差异根本没写进位图，四条方向判据全是空的")

        // ① 差异在画面顶边 ⇒ 只有"顶边那条带"看得见它。
        XCTAssertGreaterThanOrEqual(Self.changedFraction(head.0, head.1, band: top), 0.9,
            "差异写在缓冲区第 0–19 行（= 画面顶边，实测锚点），而 band.minY=0 读不到它 ⇒ "
                + "映射又反了：`minY` 不是从顶边往下算的")
        XCTAssertLessThanOrEqual(Self.changedFraction(head.0, head.1, band: bottom), 0.1,
            "顶边的差异被 `band.minY=0.8` 读到了 ⇒ 它取的是画面的**上**面一条，"
                + "与它自己名字说的相反（这正是 BACKLOG 80 记的那个形状）")
        // ② 差异在画面底边 ⇒ 反过来。
        XCTAssertGreaterThanOrEqual(Self.changedFraction(tail.0, tail.1, band: bottom), 0.9,
            "差异写在缓冲区末尾 20 行（= 画面底边），而 band.minY=0.8 读不到它 ⇒ 映射反了")
        XCTAssertLessThanOrEqual(Self.changedFraction(tail.0, tail.1, band: top), 0.1,
            "底边的差异被 `band.minY=0` 读到了 ⇒ 顶部那条带量的其实是底部")
        // ③ 横轴不许"顺手也对"：它没有翻转，所以这一组同时钉住"别把 x 也翻一次"。
        let west = Self.syntheticPair(width: width, height: height, differingColumns: 0..<14)
        XCTAssertGreaterThanOrEqual(Self.changedFraction(west.0, west.1, band: left), 0.9,
            "差异写在每行最左 20 列，而 band.minX=0 读不到 ⇒ 横轴被多翻了一次（它本来不该翻）")
        XCTAssertLessThanOrEqual(Self.changedFraction(west.0, west.1, band: right), 0.1,
            "最左的差异被 band.minX=0.8 读到了 ⇒ 横轴也反了")
        // ④ 整幅 = 各占 20%（15 行里采到 3 行）：这条把"分带"与"不分带"接上，
        //    于是"带退化成整幅"那种坏法（比如忘了裁剪）也会在这一格红。
        XCTAssertEqual(Self.changedFraction(head.0, head.1, band: nil), 0.2, accuracy: 0.02,
            "整幅读数不是 0.2 ⇒ 夹具的采样比例变了，上面那六格的地板要重算")
    }

    /// `changeGrid` 的第 0 行必须是**画面顶边**那一行（R60 / BACKLOG 84）。
    ///
    /// 为什么单独一条：R58 修映射之前它打印的行序是反的（第 0 行 = 窗口底部），而它
    /// **只输出字符串、不参与任何断言** ⇒ 那半年里所有按**行**读过的网格（R2/R3 的诊断段）
    /// 都得重看一遍才敢引用。修好了不等于钉住了，这一条就是那颗钉子。
    /// 与 `testBandRectMapsToTheEndItClaims` 同一族：合成位图、差异只放一条边。
    /// **不覆盖管线**：这条钉的是尺子的行序，不是产品像素；产品那一侧的对应判据是
    /// `testAttributionGridSeesTheMotionTheRulerSees` 那一族（走真卷）。
    func testChangeGridPrintsRowZeroAtTheTop() throws {
        let width = 60, height = 120, cols = 3, rows = 4
        let bandHeight = height / rows, bandWidth = width / cols
        func grid(differingRows: Range<Int>? = nil,
                  differingColumns: Range<Int>? = nil) -> [String] {
            let pair = Self.syntheticPair(width: width, height: height,
                                          differingRows: differingRows,
                                          differingColumns: differingColumns)
            let text = Self.changeGrid(bitmaps: [pair.0, pair.1], index: 0, cols: cols, rows: rows)
            // 每行后面都跟一个 '|'，所以切完要丢掉末尾那段空串
            let parts = text.split(separator: "|", omittingEmptySubsequences: false).dropLast()
            XCTAssertEqual(parts.count, rows, "网格没切出 \(rows) 行：\(text)")
            return parts.map(String.init)
        }
        func bright(_ line: String) -> Int { line.filter { $0 == "#" || $0 == "+" }.count }

        let top = grid(differingRows: 0..<bandHeight)
        XCTAssertEqual(bright(top[0]), cols, "差异在画面**顶边**，第 0 行必须整行亮：\(top)")
        for r in 1..<rows {
            XCTAssertEqual(bright(top[r]), 0, "第 \(r) 行不该亮（差异只在顶边）：\(top)")
        }
        let bottom = grid(differingRows: (height - bandHeight)..<height)
        XCTAssertEqual(bright(bottom[rows - 1]), cols,
            "差异在画面**底边**，最后一行才该亮 ⇒ 行序又反了：\(bottom)")
        for r in 0..<(rows - 1) {
            XCTAssertEqual(bright(bottom[r]), 0, "底边那一格漏到了第 \(r) 行：\(bottom)")
        }
        // 列序顺手一起钉：它和行序是同一处映射的两半，坏也只坏一半过。
        let left = grid(differingColumns: 0..<bandWidth)
        for r in 0..<rows {
            XCTAssertEqual(bright(String(left[r].prefix(1))), 1, "第 \(r) 行的第 0 列该亮：\(left)")
            XCTAssertEqual(bright(String(left[r].dropFirst())), 0, "第 \(r) 行的右侧两列不该亮：\(left)")
        }
    }

    /// 带捕获的那几卷上，不许再套第二层归一化框（R58 / BACKLOG 80 的第二半）。
    ///
    /// 为什么单独一条：`band:` 是**相对整幅帧**的归一化矩形。R57 把横幅两臂的整幅换成顶部那条带
    /// 之后，同一句 `band = CGRect(x:0.05, y:0.02, width:0.90, height:0.20) // 横幅那一条`
    /// 量的不再是"横幅那一条"，而是**带里再框一条 9.5pt 的窄缝**（连文字都不在里面）。
    /// 实测后果：`MOTION_SETTLE banner-in` 从 帧 11 / ≈121ms 变成 帧 6 / ≈66ms，
    /// 而**两条判据都还绿** —— 也就是说"换了捕获区域"会安静地改掉别人的测量对象。
    /// 镜像（映射反了）与嵌套（框里再框）是同一族里的两种坏法，各需要一条判据；
    /// 前者由 `testBandRectMapsToTheEndItClaims` 钉，这条钉后者。
    ///
    /// 不开能力闸门：它判的是源码里两件事是否同时出现，与产品像素无关（同 `testMotionReadingsUseTheFileChannel`）。
    func testNoTestFramesABandInsideABandCapturedFilm() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        let bandFactories = ["noticeBanner", "noticeBannerDismiss"]
        // ① 带捕获的现场必须**全在这份清单里**（新增一臂忘了进来 ⇒ 这条先红，
        //    而不是让下面那半安静地少扫一个名字）。
        //    needle 分两半拼，并且取到 `) { store in` 那一截：守卫自己那行
        //    `text.contains("captureRect: Scenario.bannerBand")` 也含前半截，
        //    不拆开就会把自己数成一个现场（R55 的 M276 就是这一族，规矩是"被搜的串不许原样
        //    出现在搜它的那一行里"）。
        let declarationNeedle = "captureRect: Scenario." + "bannerBand) { store in"
        let sites = source.components(separatedBy: declarationNeedle).count - 1
        XCTAssertEqual(sites, bandFactories.count,
            "源码里有 \(sites) 处带捕获声明，清单里是 \(bandFactories.count) 个（\(bandFactories)）⇒ "
                + "要么新加了一臂没进清单，要么有一臂被撤了没撤干净")

        // ② 谓词必须**能说不**（R56 那一族）。两段合成样本都**拼出来**写：
        //    如果它们以完整形态出现在源码里，第三段的扫描就会把守卫自己报成违规
        //    （它扫的就是这个文件的文本）。
        let factoryRef = "notice" + "Banner"
        let violation = "let f = record(Scenario." + factoryRef + "())\n"
            + "Self.deltas(f.motion" + "Frames, band: rect)\n"
        let legitimate = "let f = record(Scenario." + "detailKindChange())\n"
            + "Self.deltas(f.motion" + "Frames, band: rect)\n"
        XCTAssertEqual(Self.nestedBandFilms(in: violation, bandFactories: bandFactories), ["f"],
                       "谓词在一段明显的嵌套现场上什么都没报 ⇒ 下面那条扫描是装饰")
        XCTAssertTrue(Self.nestedBandFilms(in: legitimate, bandFactories: bandFactories).isEmpty,
                      "谓词在**没录带捕获那卷**的样本上也报嵌套 ⇒ 它判的是'有没有 band 矩形'，"
                          + "不是'有没有嵌套'，会把整窗那几卷的正常分带全判成违规")

        // ③ 逐个体扫。
        let cases = Self.testCaseBodies(in: source)
        XCTAssertGreaterThan(cases.count, 20,
            "只切出 \(cases.count) 个用例体（这个文件有几十条判据）⇒ 扫描器自己坏了，"
                + "而它坏了的时候这条守卫是**空跑**，比红更需要防")
        let offenders = cases.compactMap { entry -> String? in
            let hits = Self.nestedBandFilms(in: entry.body, bandFactories: bandFactories)
            return hits.isEmpty ? nil : "\(entry.name)→\(hits.sorted().joined(separator: ","))"
        }
        XCTAssertTrue(offenders.isEmpty,
            "这些用例把归一化分带套到了**带捕获那一卷**上：\(offenders.sorted()) ⇒ "
                + "名字写着量 A，实际量的是 A 里的一条窄缝，而且不会红。"
                + "带捕获那一卷的「整幅」就已经是那条带，要用 band: nil")
    }

    /// 判"带捕获够便宜"所需的**最小节省倍数**（整窗中位 ÷ 带中位）。
    ///
    /// 取 2 而不是拟合出来的 4.8：这一格要抓的是"rect 没起作用/成本与面积无关"，
    /// 不是抓机器抖动。真数在 `MOTION_BAND` 那行里，两遍各自多少都看得见。
    static let bandCaptureSavingFloor: Double = 2

    /// 带捕获必须**装得下**这次变更的最小首尾差（本机实测 0.883 / 0.885，两遍）。
    ///
    /// 为什么是绝对数而不是"整窗首尾差的某个比例"：整窗那个数（实测 0.222）里含
    /// 横幅消失后**下面整块列表的位移**（R22 量过的布局塌陷），那部分不属于这条过渡。
    /// 拿污染当分母，等于允许"带里什么都没有"通过。0.02 留了 40 多倍余量，
    /// 它抓的是"带整条空着"（0.00x）这一类，而不是抓抖动。
    static let bandMustHoldChangeFraction: Double = 0.02

    /// 位置同一性（③′）的两条线，本机实测：带 vs 整窗头 96 行 = 0.000，
    /// 带 vs 整窗尾 96 行 = 0.954（同一份缓冲区逐行比，不经过 `changedFraction` 的归一化映射）。
    ///
    /// 为什么是**这一对**而不是"带的首尾差 ≥ 某个数"：首尾差大不代表带在横幅上 ——
    /// 横幅撤走之后下面整块列表在位移，位移也是变化（本轮第一次的带抓在窗口底部，
    /// 首尾差照样 0.069，四条"有变化"的前提一条都没拦住）。
    /// 能拦住的是"带就是整窗的那一头"：同一头必须逐像素相同、另一头必须明显不同，
    /// 两条一起才既不许带跑掉、也不许整窗两头本来就一样（那会让第一条恒真）。
    static let bandMustMatchFullHeadFraction: Double = 0.005
    static let bandMustDifferFromFullTailFraction: Double = 0.5

    /// 抓成本归因的真值表（R55 / BACKLOG 77）。
    ///
    /// ①② 用的是**本机真读数**（`.scratch/motion-audit-2/r55_motion_local.log` 里
    /// `MOTION_GRAB` 与 `MOTION … 事件内最粗` 那两列），不是我编的数 ——
    /// 这一族在本仓库记过：真值表里必须有一格是真读数，否则它只证明"我想要的形状"。
    /// 而这一次"真读数那一格"恰好把设计改写了：第一版只有两档，
    /// 真读数 97/87.9 落在余量外 1.1ms，被判成"不是抓帧器的锅"——那条建议是错的。
    /// 没有这两格，这个错误会一直留在日志里当结论用。
    func testGrabAttributionIsATruthTable() {
        // ⓪ 两条线自己也必须是**能判红死的数**（本仓库"自适应阈值恒真"那一族）：
        //     余量写成 0 ⇒ 每一次略长的间隔都掉出 probeBound；写成 1e9 ⇒ 全部算撑满。
        //     比例线写成 0 ⇒ 一切都说"缩区域有用"；写成 1 ⇒ 一切都说"不是抓帧的锅"。
        XCTAssertGreaterThan(GrabAttribution.allowanceMilliseconds, 0)
        XCTAssertLessThanOrEqual(GrabAttribution.allowanceMilliseconds, 20,
                                 "余量到 20ms 以上，那 `probe-grab-bound` 就把「间隔比抓帧多 15ms」也说成撑满了")
        XCTAssertGreaterThan(GrabAttribution.dominatesRatio, 0)
        XCTAssertLessThan(GrabAttribution.dominatesRatio, 1,
                          "比例线取 1 意味着只有「完全等于抓帧」才算大头 —— 那是把上面那一档删掉")
        // 归因值里带浮点，所以这里按"是哪一格 + 那两个数近似对不对"三件事判，
        // 不用 `XCTAssertEqual(枚举, 枚举)`：97 − 87.9 在二进制里是 9.100000000000009，
        // 拿它和字面量 9.1 判等会红得让人以为是逻辑错了（本仓库"像素容差为 0 时抗锯齿淹没分类器"同一族）。
        func attribute(_ interval: Double, _ grab: Double) -> (String, Double, Double) {
            switch Self.grabAttribution(worstIntervalMilliseconds: interval, worstGrabMilliseconds: grab) {
            case .unknown: return ("unknown", .nan, .nan)
            case .probeBound(let ratio, let over): return ("probeBound", ratio, over)
            case .grabDominates(let ratio, let over): return ("grabDominates", ratio, over)
            case .outsideTheGrab(let ratio, let over): return ("outsideTheGrab", ratio, over)
            }
        }
        // ① 真读数：`notice-banner-dismiss` 事件段最粗 97ms，同卷抓帧最慢 87.9ms。
        //    ⇒ 抓帧解释了 91%，但余量（8ms）没盖住 ⇒ 这一条既不是"完全由抓帧决定"，
        //    更不是"与抓帧无关"。三档里它落在中间那一档，而这一档必须给出**能修**的建议。
        XCTAssertEqual(attribute(97, 87.9).0, "grabDominates")
        XCTAssertEqual(attribute(97, 87.9).1, 0.906, accuracy: 0.001)
        XCTAssertEqual(attribute(97, 87.9).2, 9.1, accuracy: 0.01)
        // ② 真读数：`heat-first-record` 峰值段最粗 260ms，同卷抓帧最慢 255.2ms
        //    ⇒ 差 4.8ms，正好是一次等 runloop 的时间 ⇒ `probeBound`。
        //    而它**中位只有 1.5ms** ⇒ 这不是常态像素成本，是新生子树第一帧被强制布局，
        //    落在同一个调用里（R49 那 260ms 空档的机制，本轮从"主线程被占住"收窄成"这一帧的抓取调用里"）。
        XCTAssertEqual(attribute(260, 255.2).0, "probeBound")
        XCTAssertEqual(attribute(260, 255.2).2, 4.8, accuracy: 0.01)
        // ③ 余量边界：差正好等于 8ms ⇒ 仍算撑满。写成 `<` 会在这一格翻脸。
        XCTAssertEqual(attribute(100, 92).0, "probeBound")
        XCTAssertEqual(attribute(100, 92).2, 8, accuracy: 0.0001)
        // ④ 刚过界 0.1ms ⇒ 换一档。这一格钉的是"8 这条线真的在判东西"。
        XCTAssertEqual(attribute(100.1, 92).0, "grabDominates")
        XCTAssertEqual(attribute(100.1, 92).2, 8.1, accuracy: 0.01)
        // ⑤ 比例边界：抓帧正好占一半 ⇒ 还算大头（`>=`）；少 0.1% ⇒ 换档。
        //    这一格管的是"两条线是不是只有一条在动" —— 只有余量那条线的话，
        //    `grabDominates` 就永远等于"余量外的一切"，比例这个词是空的。
        XCTAssertEqual(attribute(100, 50).0, "grabDominates")
        XCTAssertEqual(attribute(100, 49.9).0, "outsideTheGrab")
        // ⑥ 没量过 ⇒ unknown，而且**不许**被读成"抓帧器的锅"或"不是抓帧器的锅"。
        //    （不能用 `XCTAssertEqual(值, .nan)`：NaN 不等于自己，那一格会恒红。）
        XCTAssertEqual(attribute(120, -1).0, "unknown")
        XCTAssertTrue(attribute(120, -1).1.isNaN,
                      "unknown 必须带「没有数」，而不是带 0 —— 0 会被下游读成「解释 0%」")
        // ⑦ 间隔 ≤ 0 也是 unknown：除比例会出 inf，而 `解释=inf%` 打出去看着像读数。
        XCTAssertEqual(attribute(0, 5).0, "unknown")
        XCTAssertEqual(attribute(-10, 5).0, "unknown")
        // ⑧ 抓帧只占一小截：120ms 的间隔里抓帧只 20ms ⇒ 剩下 100ms 说不清，
        //    这时候去缩捕获区域就是"修不到地方的改动"。
        XCTAssertEqual(attribute(120, 20).0, "outsideTheGrab")
        XCTAssertEqual(attribute(120, 20).1, 20.0 / 120.0, accuracy: 0.0001)
        XCTAssertEqual(attribute(120, 20).2, 100, accuracy: 0.0001)
        // ⑨ 令牌必须是英文：这一行是 CI 那一步要 grep 的，中文短语会被连词切半。
        XCTAssertTrue(Self.grabAttributionLabel(worstIntervalMilliseconds: 260, worstGrabMilliseconds: 255.2)
                        .contains("归因=probe-grab-bound"))
        XCTAssertTrue(Self.grabAttributionLabel(worstIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
                        .contains("归因=grab-dominates"))
        XCTAssertTrue(Self.grabAttributionLabel(worstIntervalMilliseconds: 120, worstGrabMilliseconds: 20)
                        .contains("归因=not-the-grab"))
        XCTAssertTrue(Self.grabAttributionLabel(worstIntervalMilliseconds: 120, worstGrabMilliseconds: -1)
                        .contains("归因=grab-unmeasured"))
        // ⑩ 比例要**打在日志里**：分档是我的判读，`解释=NN%` 才是能复核的数。
        XCTAssertTrue(Self.grabAttributionLabel(worstIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
                        .contains("解释=91%"),
                      "标签里没了比例 ⇒ 读日志的人只能信我的分档，没法自己看 87.9/97")
        // ⑪ 归因不许改 not-run 的**令牌**：`clock-coarse-in-window` 是登记表里的理由，
        //    换掉它会让覆盖率地板报 BAD_REASON（那是我们想要的"新形状"，不是本轮的意图）。
        //    这一格钉的是：归因只能**追加**在结论后面，不能自己再打一个 `MOTION_NOT_RUN=` 前缀
        //    —— 闸门每行只取第一个匹配，多打一个就会把真理由顶掉。
        XCTAssertFalse(Self.grabAttributionLabel(worstIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
                        .contains("MOTION_NOT_RUN"),
                       "归因串里出现了 not-run 的前缀 ⇒ 它会和理由行抢同一个解析位")
    }

    /// 归因必须真的接在**结论行**上，而不是只活在一个没人调的纯函数里（R55 的接线守卫）。
    ///
    /// 为什么这条比真值表更需要：上面那一格测的是 `grabAttribution` 这个函数，
    /// 而产品日志里读到的那句话是**两个东西拼起来**的 ——
    /// `Film.worstGrabMilliseconds` 有数 + 结论行把它打出去。
    /// 这两处任何一处断掉，真值表全都还绿着，而日志会安静地变成
    /// `归因=grab-unmeasured`（一个看起来像"今天没量到"、实际是"线没接上"的读数）。
    /// 本仓库那一族叫"数值断言证明不了来源"：这里判的正是来源。
    func testGrabAttributionIsWiredIntoTheCoarseNotRunLines() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        // ① 两个粗钟 not-run 现场都得带上归因，且 A/B 那处是两臂各一次。
        let expected: [(String, Int)] = [
            ("func testTransitionsAreActuallyRunning", 1),
            ("func testHeatmapFadeIsNotVisibleToThisRuler", 2),
        ]
        for (name, count) in expected {
            let body = region(in: source, named: name)
            XCTAssertTrue(body.contains("MOTION_NOT_RUN=clock-coarse-in-window"),
                          "\(name) 里那行粗钟 not-run 不见了 ⇒ 被守卫的东西没了，这条守卫要先红而不是静默通过")
            let wired = body.components(separatedBy: "Self.grabAttributionLabel(").count - 1
            XCTAssertGreaterThanOrEqual(wired, count,
                "\(name) 里那行 not-run 只接了 \(wired) 次归因，应有 \(count) 次 ⇒ "
                    + "日志会报「最粗 Nms」而不说这 N 里有多少是抓帧，BACKLOG 77 又回到靠注释猜")
        }
        // ② `Film` 必须真的从抓帧器拿数：默认值是 −1，忘了传就永远 `grab-unmeasured`。
        let wiring = region(in: source, named: "private func recordFrames")
        XCTAssertTrue(wiring.contains("worstGrabMilliseconds: grabber.worstGrabMilliseconds"),
                      "`recordFrames` 没把抓帧器的最慢值传进 Film ⇒ 归因恒为 unmeasured，"
                          + "而每条 skip 行看着都像「今天没量到」，实际是线没接上")
        // ③ 抓帧器自己得计时：不计时的那一版会给出恒 0，比例判据会把它读成"不是抓帧器的锅"。
        //    这一格本轮先写错过一次，值得留进注释：第一版是 `source.contains("grabMilliseconds.append")`，
        //    于是**守卫自己那一行**里就含被找的串 —— 把真调用删掉之后守卫仍然在自己的消息文本里
        //    读到它，绿着放过了 M276。R53 已经为 `region()` 记过同一族（按行首匹配才不撞），
        //    但那一族的完整说法是"**被搜的文本必须限定在被守卫的区域内**"，而不只是"锚点要按行首"。
        let tickBody = region(in: source, named: "func tick()")
        XCTAssertTrue(tickBody.contains("grabMilliseconds.append"),
                      "`Grabber.tick` 不再记录每次抓帧耗时 ⇒ 上面两条接的都是一个空数组")
    }

    /// 读数必须有第二条通道，而且**所有**读数都得走它（R56 / BACKLOG 79 / U-82）。
    ///
    /// 为什么这条判据不开 `CLIPBOARD_HISTORY_UI_MOTION` 门：它管的是"证据能不能活下来"，
    /// 而不是"产品动没动"。CI 上那些**没有**开 motion 门的全量运行，正好是这条判据唯一
    /// 每次都能跑的地方 —— 一开闸门，它就变成只有本机才有的判据，而丢读数的正是 CI。
    ///
    /// 两半各管一种坏法：
    /// ① 源码扫描：还留着 `print("MOTION_` 的那一行等于把那条读数留在会死的通道上；
    /// ② 通道本身：`emit` 之后必须能在文件里读到，而且**后写的行必须在文件末尾**
    ///    （只判"文件里有这行"抓不到"每次都整份重写"那种坏法 —— 那会只留下最后一行）。
    func testMotionReadingsUseTheFileChannel() throws {
        // ① 被搜的串不能原样出现在守卫自己的文本里（R55 的 M276 就栽过一次：
        //    守卫在自己的失败消息里读到了被搜的串，于是把真调用删掉它仍然绿）。
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        // 规则要写成**两半**（R57 改的）：一行里同时出现 `print(` 与「引号 + MOTION」就是游离读数。
        // 为什么不用一串完整字面量去列举写法：R56 那版列了两种
        // （`print("MOTION_` 与 `print(String(format: "MOTION_`），
        // 而**每卷逐帧读数那一行写的是 `print("MOTION \(scenario.name) …`**（MOTION 后面是空格）——
        // 它不在列表里，于是那条最重要的读数整整一天都没进文件通道，
        // 而守卫一直绿。**发现它靠的是去数文件里有多少行，不是靠守卫报警。**
        // ⇒ 一条靠"列举形式"的扫描，形式一多就会漏；改成"两个必要条件同时成立"。
        let quote = "\""
        let readingPrefix = "MOTION"
        let positiveControl = ["  print(" + quote + readingPrefix + "_X 1)",
                               "  print(String(format: " + quote + readingPrefix + "_Y %@\", a))",
                               "  print(" + quote + readingPrefix + " \(name) frames=1)",
                               "  emit(" + quote + readingPrefix + "_Z 1)"]
        let caught = positiveControl.filter { $0.contains("print(") && $0.contains(quote + readingPrefix) }
        XCTAssertEqual(caught.count, 3,
            "正对照只抓到 \(caught.count)/3 种写法 ⇒ 这条扫描本身是坏的（第 4 条是 emit，必须**不**被抓到），"
                + "下面那句\"没有游离读数\"因此什么都没说")
        let strays = source.components(separatedBy: "\n").filter { line in
            line.contains("print(") && line.contains(quote + readingPrefix)
        }
        XCTAssertTrue(strays.isEmpty,
            "有 \(strays.count) 行读数只走 stdout：\(strays.prefix(3).map { String($0.trimmingCharacters(in: .whitespaces).prefix(48)) })"
                + " ⇒ 通道丢一次的那天，这些读数一条都不剩（BACKLOG 79）。改走 `emit`")
        // ② 通道本身。marker 带 uuid：同一台机器上并跑两遍时，读到别人的行也算通过的话，
        //    这条判据就只是在读"有人写过这个文件"。
        let marker = "MOTION_SELFTEST_\(UUID().uuidString.prefix(8))"
        let second = marker + "-2"
        emit(marker)
        emit(second)
        let text: String
        do {
            text = try String(contentsOf: Self.readingsURL, encoding: .utf8)
        } catch {
            XCTFail("文件通道没写出来（\(Self.readingsURL.path)）⇒ `emit` 只剩 print，BACKLOG 79 没修")
            return
        }
        let lines = text.split(separator: "\n").map(String.init)
        // 先判"这一遍的 marker 在不在里面"。顺序要紧：只判末尾两格的话，
        // **上一遍留下的同名文件**也能让这一格红得让人以为是追加逻辑坏了
        // （R56 电池第一次跑 M278 就是这个形状：红是对的，理由写错了）。
        XCTAssertTrue(text.contains(marker),
            "文件里没有这一遍的 marker ⇒ 要么没落盘，要么读到的是**上一遍**的旧文件"
                + "（末尾现在是 \(lines.suffix(2))）")
        XCTAssertEqual(Array(lines.suffix(2)), [marker, second],
            "marker 在文件里，但**不在末尾两格** ⇒ 追加逻辑坏了（整份重写会吃掉前面的读数），"
                + "或者写的顺序反了。末尾实际是：\(lines.suffix(2))")
        // ③ 这条通道必须与胶片同目录：CI 那一步只知道一个 `CLIPBOARD_HISTORY_MOTION_OUT`，
        //    落在别处等于没落。
        XCTAssertEqual(Self.readingsURL.deletingLastPathComponent().path,
                       Self.filmsDirectory.path,
                       "读数文件不在胶片目录里 ⇒ CI 那一步找不到它，补不回来")
    }

    /// 归因说"该缩小捕获区域"——**这句话本身必须是可证的**（R55 / BACKLOG 77 的前提）。
    ///
    /// 为什么单独立一条，而不是信"位图越大越慢"这种直觉：
    /// `probe-grab-bound` / `grab-dominates` 那两条建议的全部价值在于"缩区域真的能把采样变细"。
    /// 如果 `cacheDisplay` 的成本其实由固定开销主导（分配、SwiftUI 重排、一次全视图合成），
    /// 那缩区域省不下时间，BACKLOG 77 的路 a/b 就是**两条白花时间的路**，
    /// 而我已经在日志里把它当成建议打出去了。直觉在这种地方靠不住：只能测。
    ///
    /// 本机测出来了（2026-10-14，数值见 `grabAreaCostRatioFloor` 那段）：面积差 29.8 倍只换来
    /// 成本差 12.3–13.0 倍 ⇒ 建议成立但不是免费子弹，缩到一条横幅能把 41.7ms 打到 8.7ms，
    /// 而 3ms 那一截地板无论怎么缩都在。
    ///
    /// 测法是**交错**跑三种区域（全 / 一条横幅 / 一小块），同一轮里轮流抓，各取中位：
    /// 顺序跑的话，先跑的那一组会拿走冷缓存、后跑的那一组会被节流，
    /// 读出来的"面积效应"里混着时间漂移 —— 这一族本仓库记过（A/B 要同一台机器同一段时间）。
    /// 判定只用**两端**，中间那档打印出来供对账：三档全单调是一个比两个极端更强的主张，
    /// 而它会被噪声轻易打破，把判据写成恒红没有意义。
    func testGrabCostScalesWithCapturedArea() throws {
        try skipUnlessEnabledAndCapable()
        // 地板自己先过一遍：写成 1.0 就成了"任何比值都算面积有影响"的恒真判据，
        // 而这条测的东西恰好就是"比值够不够大"。
        XCTAssertGreaterThan(Self.grabAreaCostRatioFloor, 1.0,
                             "地板 ≤1 ⇒ 这一格恒真：面积与成本毫无关系也能算「通过」")
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 760, height: 673),
                              styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: ContentView(historyStore: makeStore()))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        host.layoutSubtreeIfNeeded()
        let bounds = host.bounds
        guard bounds.width > 400, bounds.height > 400 else {
            XCTFail("夹具只有 \(Int(bounds.width))×\(Int(bounds.height))pt ⇒ 三档区域分不开，"
                    + "这条测量会在一个假视图上「证明」面积效应")
            return
        }
        // 三档面积比按真尺寸算，不写死「1/28」这种数：写死一次，改了夹具尺寸就读错了档。
        let arms: [(name: String, rect: NSRect)] = [
            ("全视图", bounds),
            ("横幅带", NSRect(x: 0, y: bounds.height - 120, width: bounds.width, height: 120)),
            ("小块", NSRect(x: 0, y: bounds.height - 60, width: 300, height: 60)),
        ]
        let fullArea = Double(arms[0].rect.width * arms[0].rect.height)
        let tinyArea = Double(arms[2].rect.width * arms[2].rect.height)
        XCTAssertGreaterThan(fullArea / tinyArea, 8,
                             "夹具的端到端面积比不到 8 ⇒ 就算成本真按面积走，也量不出差；这是夹具坏了")

        var samples: [[Double]] = [[], [], []]
        func grab(_ rect: NSRect) -> Double {
            let began = DispatchTime.now()
            if let rep = host.bitmapImageRepForCachingDisplay(in: rect) {
                host.cacheDisplay(in: rect, to: rep)
            }
            return Double(DispatchTime.now().uptimeNanoseconds - began.uptimeNanoseconds) / 1_000_000
        }
        // 预卷：新窗口的头两次 `cacheDisplay` 要 260–340ms（R11 记过的那段冷缓存）。
        // 让它进中位数就会把「面积效应」读成「首帧效应」。
        for _ in 0..<4 { for arm in arms { _ = grab(arm.rect) } }
        for _ in 0..<9 {
            for index in arms.indices { samples[index].append(grab(arms[index].rect)) }
        }
        let medians = samples.map { Self.median($0) }
        for index in arms.indices {
            emit("MOTION_GRAB_AREA \(arms[index].name) 面积=\(String(format: "%.0f", Double(arms[index].rect.width * arms[index].rect.height)))pt²"
                  + " 样本=\(samples[index].count) 中位=\(String(format: "%.1f", medians[index]))ms"
                  + " 最慢=\(String(format: "%.1f", samples[index].max() ?? -1))ms")
        }
        let big = medians[0]
        let small = medians[2]
        XCTAssertEqual(samples[0].count, 9, "每档必须够 9 个样本才谈中位数")
        // 地板判之前先钉"确实抓到了东西"：`bitmapImageRepForCachingDisplay` 返回 nil 时
        // 那一格只花了取时刻的钱 ≈0ms，接着会掉进下面的"这台机器太快"分支**绿着通过**。
        // 「快机器」与「抓取根本没执行」在只比大小的判据里长得一模一样，这一格就是用来拆开它们的。
        XCTAssertGreaterThan(big, 0.5,
            "全视图抓一帧的中位是 \(String(format: "%.2f", big))ms ⇒ 抓取没真的执行（rep 为 nil 或视图是空的），"
                + "这不是「机器快」，是夹具坏了")
        guard big >= Self.grabCostFloorMilliseconds else {
            // 打出来，不判红：这台机器上整帧抓完不到 5ms，面积差落在噪声里，
            // 此时「面积不影响成本」与「面积影响但看不出来」两种说法无法区分。
            emit("MOTION_GRAB_AREA_SKIP=below-noise-floor 全视图中位=\(String(format: "%.1f", big))ms"
                  + " 低于 \(Self.grabCostFloorMilliseconds)ms ⇒ 今天量不出面积效应，"
                  + "不许据此说 BACKLOG 77 的缩区域无效")
            return
        }
        XCTAssertGreaterThan(small, 0, "小块的中位是 0 ⇒ 这条测量什么都没量到，任何倍率都是除出来的假数")
        XCTAssertGreaterThanOrEqual(big / small, Self.grabAreaCostRatioFloor,
            "全视图抓一帧 \(String(format: "%.1f", big))ms，只比 \(String(format: "%.0f", tinyArea))pt² "
                + "那一块的 \(String(format: "%.1f", small))ms 慢 \(String(format: "%.2f", big / small)) 倍"
                + " ⇒ 成本由固定开销主导，缩小捕获区域省不下采样时间，"
                + "而 `grabAttributionLabel` 的 `probe-grab-bound` / `grab-dominates` 两支正在把它当修法建议打出去："
                + "要么改那两条建议，要么把抓帧换成按区域分配的写法")
        // 中间那档只打印不判定（见上方注释）：三档全单调是比端到端更强的主张，
        // 而它会被抖动轻易打破 —— 把判据写成恒红没有意义，读数留在日志里供对账。
        XCTAssertGreaterThan(medians[1], 0, "横幅带的中位是 0 ⇒ 抓取压根没执行，那条打印行是空的")
        window.orderOut(nil)
    }

    /// 判"面积效应存在"所需的最小倍率（全视图 / 小块）。
    ///
    /// 本机 2026-10-14 实测（`.scratch/motion-audit-2/r55_grab_area.log`，三遍分别是 12.5 / 12.3 / 13.0 倍）：
    /// 全视图 535800pt² 中位 **41.7ms**、横幅带 91200pt² **8.7ms**、小块 18000pt² **3.4ms**
    /// ⇒ 端到端 **12.3–13.0 倍**（三遍各自 12.5 / 12.3 / 13.0），而面积比是 29.8 倍 —— 成本是"固定开销（≈3ms 的分配与调用）
    /// + 按面积那一项"，不是纯线性。这条子线性正是 BACKLOG 77 路 a/b 的性价比上限：
    /// 缩到一条横幅能省掉 41.7 里的 33ms 上下，但省不掉那 3ms 的地板。
    /// CI runner 没量过 ⇒ 地板取 1.5 而不是 12：这一格要抓的是"面积完全不影响成本"
    /// （比值≈1，说明成本全是固定开销）那种失效，不是抓抖动。
    static let grabAreaCostRatioFloor: Double = 1.5

    /// 低于这个成本就不判（ms）：整帧只要 2ms 的机器上，面积差是噪声而不是信息。
    static let grabCostFloorMilliseconds: Double = 5

    /// 中位数（偶数个取中间两个的平均）。空数组返回 −1 = "没量"，**不是 0**。
    static func median(_ values: [Double]) -> Double {
        guard !values.isEmpty else { return -1 }
        let sorted = values.sorted()
        let middle = sorted.count / 2
        return sorted.count % 2 == 1 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2.0
    }

    ///
    /// 为什么这条要守卫，而不是"记得放对位置"：R50 加这行时我把它留在 `requireAppWasActive` 后面，
    /// 于是 runner 每次跳过这一臂，日志就只剩"两臂读数有、结论行没有"——
    /// 那正是 R50 想消灭的那种含糊（把一种读法当成另一种），而它自己又造了一个新的：
    /// run 38543090198 与 38543812477 两次都打了四行 `MOTION_NATIVE`，
    /// 而 `MOTION_NATIVE_MOVE 判定=` 一次都没出现。
    /// 顺序是"这一臂被跳过时仍然留得下证据"的**唯一**条件，所以它必须会红。
    func testNativeMoveVerdictPrintsBeforeTheSkipGuards() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        let body = region(in: source, named: "func testNativeRowMoveIsVisibleToTheRuler")
        let printAt = body.range(of: "MOTION_NATIVE_MOVE 判定=")
        let skipAt = body.range(of: "try requireAppWasActive(probe.wasActive)")
        XCTAssertNotNil(printAt, "结论行没了 ⇒ runner 一跳过，这一臂就又没有任何结论（BACKLOG 75）")
        XCTAssertNotNil(skipAt, "skip 那道闸没了 ⇒ 非激活进程里的读数会被当成产品结论")
        if let printAt, let skipAt {
            XCTAssertLessThan(printAt.lowerBound, skipAt.lowerBound,
                              "结论行必须在 skip 之前打：它说的是**读数怎么读**，不是产品结论。"
                              + "换回后面的顺序，runner 每次跳过都会让这一臂没有任何结论行")
        }
        // 反过来也要钉住：**判红**仍然在 skip 之后（否则非激活进程里的一次 skip
        // 会被读成"产品瞬移"，那就是 U-76 的成因本身）。
        // 找的是 `XCTFail(` 而不是失败消息里的中文：消息会随措辞改，而"这一格有人负责"这件事不会。
        let failAt = body.range(of: "XCTFail(")
        XCTAssertNotNil(failAt, "`notAnimated` 那一格的 XCTFail 没了 ⇒ 三态里最要紧的一格不再有人负责")
        if let failAt, let skipAt {
            XCTAssertGreaterThan(failAt.lowerBound, skipAt.lowerBound,
                                 "判红必须留在 skip **之后**：读法可以提前打，责任不能提前担")
        }
    }

    /// 那条 A/B 必须用**连续段**那把尺，不许悄悄换回跨度（R48 / BACKLOG 70 / U-74）。
    ///
    /// 为什么真值表不够：真值表钉的是 `contiguousChangedRun` 算得对，
    /// 它钉不住**调用点** —— 把 `elapsedA` 换回 `changedSpanElapsedMilliseconds`，
    /// 真值表仍然全绿，而那条 A/B 下一次又会把一次晚到的抖动读成 265ms 的淡入。
    /// "测的轴与用的轴不是一根"这一族，R43/R44 的调用点级守卫是同一个来源。
    func testFadeABReadsTheContiguousRulerNotTheSpan() throws {
        let source = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        XCTAssertFalse(source.isEmpty, "读不到本文件：这条守卫没有守卫对象")
        let body = region(in: source, named: "func testHeatmapFadeIsNotVisibleToThisRuler")
        XCTAssertTrue(body.contains("let verdict = Self.fadeVisibility("),
                      "区域取到的不是那条 A/B ⇒ 下面的计数判据全是空的")
        // 区域助手自己是尺，所以它自己也要被量一次（R45 的规矩）：
        // 取多了（把下一个成员吞进来）与取不到都必须红。
        XCTAssertFalse(body.contains("func testChangedRunMustBeContiguousNotFirstToLast"),
                       "区域把下一个成员也吞了 ⇒ 它其实是整文件，'按区域判'的判别力是假的")

        // 三臂**各自**都必须从连续段那把尺取值。
        //
        // 为什么不是"数区域里出现几次 `contiguousChangedRun(`"（本条的第一版就是这么写的）：
        // 那个计数被变异 M237 当场证伪 —— 把 `elapsedB` 改成直接抄 `elapsedA`，
        // 区域里仍然有 3 次调用（预热、开A、关），计数照样过。
        // **一个没被证伪过的计数，判的是"这文件里出现过这个词"，不是"这条判据还成立"。**
        let codeLines = body.components(separatedBy: "\n")
        // 检查的是**段绑定**（runA/runB/runOff）而不是 elapsedA/B/Off：
        // 后者现在只是 `runX?.elapsedMilliseconds` 的解包，真判据在段是哪来的。
        for (name, source, elapsedName) in [("runA", "onFilmA.motionStamps", "elapsedA"),
                                            ("runB", "onFilmB.motionStamps", "elapsedB"),
                                            ("runOff", "offFilm.motionStamps", "elapsedOff")] {
            guard let at = codeLines.firstIndex(where: { $0.contains("let \(name) =") }) else {
                XCTFail("区域里找不到 `let \(name)` 这条赋值 ⇒ 判定的输入被搬走了，守卫必须红")
                continue
            }
            // 语句边界按**括号配平**取，不取固定两行：
            // 固定两行被变异 M237 当场证伪 —— 那条赋值被改成一行之后，
            // 第二行就是**下一条**赋值，于是"含不含 contiguousChangedRun"判的其实是邻居。
            var statement = codeLines[at]
            var depth = statement.filter { $0 == "(" }.count - statement.filter { $0 == ")" }.count
            var next = at + 1
            // 括号不配平时**停在下一条 `let` 之前**：宁可少读一行让下面的边界断言红，
            // 也不许一路吞到文件尾（那等于把整份文件当语句）。
            while depth > 0, next < codeLines.count,
                  !codeLines[next].trimmingCharacters(in: .whitespaces).hasPrefix("let ") {
                statement += " " + codeLines[next]
                depth += codeLines[next].filter { $0 == "(" }.count
                depth -= codeLines[next].filter { $0 == ")" }.count
                next += 1
            }
            XCTAssertEqual(statement.components(separatedBy: "let ").count - 1, 1,
                           "语句边界取多了 ⇒ 这条守卫在读邻居的赋值：\(statement.trimmingCharacters(in: .whitespaces))")
            XCTAssertTrue(statement.contains("contiguousChangedRun("),
                          "`let \(name)` 不是从连续段那把尺来的：\(statement.trimmingCharacters(in: .whitespaces))")
            XCTAssertTrue(statement.contains(source),
                          "`let \(name)` 读的不是 \(source) ⇒ 那一臂被换掉了（抄别的臂也算换掉）")
            // 判定用的时长必须**就是这一段的时长**：不许有人把它换成整卷跨度、帧数或峰值。
            XCTAssertTrue(codeLines.contains { $0.contains("let \(elapsedName) =")
                && $0.contains("\(name)?.elapsedMilliseconds") },
                          "`\(elapsedName)` 不再是 `\(name)` 那一段的时长 ⇒ 判定输入被换轴了")
        }
        // 跨度那把尺在这个区域里**只许出现在打印里**（当对照给人看），不许出现在判定用的赋值里。
        // 取"同一行既有 `let elapsed` 又调用跨度"这个合取，而不是"区域里含不含跨度"：
        // 后者会把 `let spanA = …` 这种合规写法也判成违规，那等于逼下一个人删掉对照打印。
        for line in body.components(separatedBy: "\n") where line.contains("changedSpanElapsedMilliseconds") {
            XCTAssertFalse(line.contains("let elapsed"),
                           "判定用的时长又改回跨度那把尺：\(line.trimmingCharacters(in: .whitespaces))")
        }
        // 判定调用必须把**分辨率**那一轴传进去（R48）。
        // 不传的话函数里那道门永远不生效，而真值表里那三格照样全绿 ——
        // **轴长在函数里不等于接在调用点上**（R43 那条"调用点级判据"是同一个坑）。
        guard let callAt = codeLines.firstIndex(where: { $0.contains("= Self.fadeVisibility(") }) else {
            XCTFail("区域里找不到 fadeVisibility 的调用点 ⇒ 分辨率轴无从检查")
            return
        }
        var call = codeLines[callAt]
        var callDepth = call.filter { $0 == "(" }.count - call.filter { $0 == ")" }.count
        var cursor = callAt + 1
        while callDepth > 0, cursor < codeLines.count {
            call += " " + codeLines[cursor]
            callDepth += codeLines[cursor].filter { $0 == "(" }.count
            callDepth -= codeLines[cursor].filter { $0 == ")" }.count
            cursor += 1
        }
        XCTAssertTrue(call.contains("worstOnA:"),
                      "调用点没传段内最粗采样 ⇒ 分辨率那道门是死的：" + call)
        XCTAssertTrue(call.contains("worstOnB:"),
                      "调用点只传了一臂的最粗采样 ⇒ 另一臂卡钟时仍会进判定：" + call)
        // 取不到的那一路：哨兵串不许含任何真实 needle，否则"找不到"会被读成"这里没有违规"。
        let missing = "\u{0}REGION-NOT-FOUND\u{0}"
        XCTAssertFalse(missing.contains("changedSpanElapsedMilliseconds"))
        XCTAssertEqual(missing.components(separatedBy: "\n").filter { $0.contains("contiguousChangedRun(") }.count, 0)
    }

    /// `fadeVisibility` 的真值表（R47 / BACKLOG 68）。
    ///
    /// 这条**不开窗口**，所以 CI 每次都跑 —— 上面那条 A/B 要 `CLIPBOARD_HISTORY_UI_MOTION=1`
    /// 才动，而本轮修的就是那条判据用的轴。修尺子的代码如果只被一把"平时不跑"的判据守着，
    /// 那它下一次漂回去是没人知道的。
    ///
    /// 第 ⑤ ⑥ 格是本轮的靶：两臂**时长**接近而**帧数**不同（采样相位），
    /// 旧写法 `onSpan == offSpan` 会把它们判成"这把尺看得见"，而正确结论是"看不见"。
    func testFadeVisibilityJudgesTimeNotFrameCount() {
        let declared = 250.0      // `.contentFade` 声明的毫秒数（这里要的是数，不是真令牌）
        let interval = 31.0       // 一个采样间隔

        func verdict(_ a: Double?, _ b: Double?, _ off: Double?, peak: Double = 0.2,
                     worstOnA: Double = 0, worstOnB: Double = 0) -> FadeVisibility {
            Self.fadeVisibility(elapsedOnA: a, elapsedOnB: b, elapsedOff: off, peakOn: peak,
                                declaredMilliseconds: declared, intervalMilliseconds: interval,
                                worstOnA: worstOnA, worstOnB: worstOnB)
        }

        // ① 峰值低于地板 ⇒ 触发根本没让图长出来：探针坏了，不许下任何一种结论。
        XCTAssertEqual(verdict(120, 120, 31, peak: 0.001), .noControl,
                       "没有对照物时说「看不见」，等于把探针故障写成产品的极限")
        // ② 真过渡：两遍开臂都覆盖 120ms（≥ 0.3×声明），对照臂只有一帧 ⇒ 看得见。
        XCTAssertEqual(verdict(120, 130, 7), .visibleToThisRuler)
        // ③ 三臂都只有一帧 ⇒ 看不见（这就是本机今天的形状：6–7ms / 6–7ms / 7ms）。
        XCTAssertEqual(verdict(7, 7, 7), .notVisibleToThisRuler)
        // ④ "读不出变化段"是**证据缺席**，不是"证明没有"。所以：
        //    两遍都读不出 ⇒ 看不见（没有任何一遍说看见）；
        //    一遍说看见、另一遍读不出 ⇒ 通道不可靠，报矛盾，**不许挑一次算数**。
        XCTAssertEqual(verdict(nil, nil, 7), .notVisibleToThisRuler)
        XCTAssertEqual(verdict(nil, 120, 7), .inconsistent(onA: nil, onB: 120))
        XCTAssertEqual(verdict(120, nil, 7), .inconsistent(onA: 120, onB: nil))
        //    对照臂读不出 ⇒ 归因没有着落：这时候说「看得见」就是自己给自己发证。
        XCTAssertEqual(verdict(120, 130, nil), .notVisibleToThisRuler)
        // ⑤ **只漂帧数不许算看得见**：80 vs 60 —— 差 20ms，不到一个采样间隔。
        //    旧写法看的是帧数，这种形状下两臂帧数会不同 ⇒ 它会红说"尺子看得见"。
        XCTAssertEqual(verdict(80, 80, 60), .notVisibleToThisRuler,
                       "两臂时长差不到一个采样间隔 ⇒ 那是一帧的相位差，不是过程被看见了")
        // ⑥ 归因那一半：关掉曲线之后"还在变"照样覆盖 190ms ⇒ 量的不是我们的动画。
        XCTAssertEqual(verdict(200, 210, 190), .notVisibleToThisRuler,
                       "对照臂也这么长 ⇒ 这段变化不是动画带来的")
        // ⑦ 两遍同臂互相矛盾 ⇒ 报矛盾，不许挑一次算数（R47 实测的形状：265 / 7）。
        XCTAssertEqual(verdict(265, 7, 7), .inconsistent(onA: 265, onB: 7))
        // ⑧ 边界：两遍都正好 0.3×声明、正好差一个间隔 ⇒ 算看得见（门槛含等号）。
        XCTAssertEqual(verdict(75, 75, 44), .visibleToThisRuler,
                       "两个门槛都含等号：写成严格不等式会让「刚好够」这一格随浮点误差翻脸")
        // ⑨ **上限那一格就是本机今天的真读数**：声明 160ms，抓到 259ms ⇒ 那不是这条淡入。
        //    没有上限的话，这段别的变化会让判据喊"尺子终于看见了，快放进 Scenario.all()"。
        XCTAssertEqual(Self.fadeVisibility(elapsedOnA: 259, elapsedOnB: 260, elapsedOff: 7,
                                           peakOn: 0.226, declaredMilliseconds: 160,
                                           intervalMilliseconds: 8),
                       .notVisibleToThisRuler,
                       "259ms 比声明的 160ms 长出一截 ⇒ 这是别的变化在动，不是 opacity 淡入")
        // ⑪ 下限唯一的独立证人：两臂都只有 40ms（< 0.3×声明），比对照臂长出 40ms > 一个间隔。
        //    没有下限的话归因门会放行它 —— 一段 40ms 的变化不可能是 250ms 的过渡，
        //    它只是"两臂各自抖了一下"。
        XCTAssertEqual(verdict(40, 40, 0), .notVisibleToThisRuler,
                       "短于 0.3×声明的一段变化不许因为「比对照臂长」就算看见过程")
        // ⑫ 归因必须看**两臂里较短的那一个**：A=140 / B=120 / 对照=100 ⇒ 较短的那个只差 20ms，
        //     不算看见。写成"只看第一臂"（变异 M229 干的事）这一格就会红。
        XCTAssertEqual(verdict(140, 120, 100), .notVisibleToThisRuler,
                       "两臂里较短的那个没超过对照臂一个间隔 ⇒ 不许拿运气好的那遍当结论")
        // ⑩ 真过渡的尺度：声明 160ms、抓到 150ms、对照臂 7ms ⇒ 看得见。
        XCTAssertEqual(Self.fadeVisibility(elapsedOnA: 150, elapsedOnB: 158, elapsedOff: 7,
                                           peakOn: 0.226, declaredMilliseconds: 160,
                                           intervalMilliseconds: 8),
                       .visibleToThisRuler,
                       "上限收得太紧会把真过渡也判成看不见 —— 这一格钉的是上限别过头")
        // ⑬ **分辨率轴**（R48）：段内最粗采样 200ms 而声明只有 250ms 的 0.5 倍 ⇒ 判不了。
        //     这一格来自本机真读数 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`：
        //     时长 266ms 不是"过程演了 266ms"，是钟在过程中间停了。
        XCTAssertEqual(verdict(266, 266, 7, worstOnA: 200, worstOnB: 190),
                       .clockTooCoarse(worstOnA: 200, worstOnB: 190),
                       "钟卡住时的时长读数不许参与判定")
        // ⑭ 粗钟**优先于**"看不见"：两臂时长都短（本来会被判成看不见），但段内最粗采样超限 ⇒
        //     结论必须是"今天判不了"，不是"这条淡入看不见"。
        //     这一格是本轮真正的产品结论所在：R11 那句"这条通道对淡入可见性=0"就是从这里撤回的。
        XCTAssertEqual(verdict(7, 7, 7, worstOnA: 200, worstOnB: 200),
                       .clockTooCoarse(worstOnA: 200, worstOnB: 200),
                       "把判不了写成看不见，等于拿探针的占空比给产品定性")
        // ⑮ 边界：最粗采样**正好** 0.5×声明 ⇒ 还在可判范围内（门槛取严格大于），
        //     与 `judgeMotion` 中间档同一个含等号的写法。
        XCTAssertEqual(verdict(150, 150, 31, worstOnA: 125, worstOnB: 125), .visibleToThisRuler,
                       "写成 ≥ 会让这一格随浮点误差翻脸，且与 judgeMotion 的 0.5 档口径不一致")
    }

    /// 「变化段」必须真的**连续**（R48 / BACKLOG 70 / U-74）。
    ///
    /// 这一条不开窗口、CI 每次都跑，理由与上一条相同：修尺子的代码如果只被一把
    /// "平时不跑"的判据守着，它下一次漂回去是没人知道的。
    ///
    /// 第 ② 格是**本机真读到过的形状**（`时长=265ms 帧数=2 整卷中位=8ms`）：
    /// 两帧连续变化不可能覆盖 265ms，所以那不是淡入演了那么久，是跨度算法把一次晚到的抖动并了进来。
    func testChangedRunMustBeContiguousNotFirstToLast() {
        // 每 8ms 一帧，中间在 32ms→340ms 之间留一大段静止（就是本机那卷的形状）。
        let stamps: [TimeInterval] = [0, 0.008, 0.016, 0.024, 0.032, 0.340, 0.348, 0.356]
        let floorValue = 0.2 * 0.15          // `peak × stepFloorRatio`，下面几格都按这个地板摆

        // ① 单波：连续段与首尾跨度**该相等** —— 这条钉的是"改法没把正常形状改坏"。
        let single: [Double] = [0.2, 0.15, 0.1, 0.001, 0, 0, 0]
        XCTAssertEqual(Self.contiguousChangedRun(stamps: stamps, fractions: single)?
                       .elapsedMilliseconds ?? -1, 24, accuracy: 1,
                       "0/1/2 三帧一直在变 ⇒ 覆盖 stamps[0]…stamps[3] = 24ms")
        XCTAssertEqual(Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: single) ?? -1,
                       24, accuracy: 1, "连续的时候两把尺必须给同一个数")

        // ② **两波带空隙**（本机今天的真形状）：跨度把 348ms 说成"淡入演了 348ms"，
        //    而连续段只认动画真在演的那 8ms。
        let twoWaves: [Double] = [0.2, 0.001, 0.001, 0.001, 0.001, 0.05, 0]
        let runElapsed = Self.contiguousChangedRun(stamps: stamps, fractions: twoWaves)?
            .elapsedMilliseconds ?? -1
        let spanElapsed = Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: twoWaves) ?? -1
        XCTAssertEqual(runElapsed, 8, accuracy: 1, "峰值那一格只有它自己 ⇒ 一段 = 一个采样")
        XCTAssertEqual(spanElapsed, 348, accuracy: 1, "跨度仍然会把第二波并进来（它没被改，只是不再进判定）")
        XCTAssertLessThan(runElapsed, spanElapsed,
                          "两把尺必须在这一格分道扬镳 —— 没分开就等于本轮什么都没改")

        // ③ 峰值在**第二波**：该取第二波，不许拿"最早的那一段"当过渡。
        let peakLate: [Double] = [0.05, 0.001, 0.001, 0.2, 0.1, 0, 0]
        XCTAssertEqual(Self.contiguousChangedRun(stamps: stamps, fractions: peakLate)?
                       .elapsedMilliseconds ?? -1, 316, accuracy: 1,
                       "峰值那一段是 fractions[3…4] ⇒ 覆盖 stamps[3]=24ms 到 stamps[5]=340ms = 316ms；"
                       + "取第一段就是把开头那一下抖当成过程")
        XCTAssertEqual(Self.contiguousChangedRuns(stamps: stamps, fractions: peakLate).count, 2,
                       "分段本身要能被数出来：这一卷是两段，不是一段 308ms 或一段 348ms")

        // ④ **含峰值 ≠ 最长**：后头那三帧是别的东西在慢慢变，时长比淡入长得多，
        //    但它不是这条淡入。取最长会把"环境里有个慢过程"算成动画演得久。
        let longTailStamps: [TimeInterval] = [0, 0.008, 0.016, 0.024, 0.032, 0.040, 0.300, 0.360, 0.420]
        let longTail: [Double] = [0.2, 0.001, 0.001, 0.001, 0.001, 0.05, 0.05, 0.05]
        let chosen = Self.contiguousChangedRun(stamps: longTailStamps, fractions: longTail)
        XCTAssertEqual(chosen?.elapsedMilliseconds ?? -1, 8, accuracy: 1,
                       "380ms 那段峰值只有 0.05 ⇒ 不是淡入；含峰值的那段才是")
        XCTAssertEqual(chosen?.peak ?? -1, 0.2, accuracy: 6, "选中的那段必须真的含峰值")

        // ⑤ 整卷安静 ⇒ 一段都没有，两把尺都读不出（不许读成 0ms）。
        let quiet: [Double] = [0.001, 0, 0, 0, 0, 0, 0]
        XCTAssertTrue(Self.contiguousChangedRuns(stamps: stamps, fractions: quiet).isEmpty)
        XCTAssertNil(Self.contiguousChangedRun(stamps: stamps, fractions: quiet))
        XCTAssertNil(Self.changedSpanElapsedMilliseconds(stamps: stamps, fractions: quiet))

        // ⑥ 地板**含等号**：正好等于 `峰值×0.15` 的那一帧算"还在变"。
        let onFloor: [Double] = [0.2, floorValue, 0.001, 0, 0, 0, 0]
        XCTAssertEqual(Self.contiguousChangedRun(stamps: stamps, fractions: onFloor)?
                       .elapsedMilliseconds ?? -1, 16, accuracy: 1,
                       "写成严格不等式会让这一格随浮点误差翻脸（与 R47 真值表第 ⑧ 格同一个道理）")

        // ⑦ **最后一段一直变到卷尾**也必须被闭合：实现里靠的是收尾哨格，
        //    没有它的话"变到最后一帧"会一段都不报 —— 少一段比多一段更难被发现。
        let tailStamps: [TimeInterval] = [0, 0.008, 0.016, 0.024]
        let tail: [Double] = [0.001, 0.1, 0.2]
        XCTAssertEqual(Self.contiguousChangedRun(stamps: tailStamps, fractions: tail)?
                       .elapsedMilliseconds ?? -1, 16, accuracy: 1)

        // ⑧ R2 那批夹具的形状在这里被看清：`coarseSampling` 其实是**两波**，不是一段 135ms 的淡入。
        //    本轮不改它（它喂的是别的判据），但把这件事记进 BACKLOG 72：
        //    一个"中间掉回 0.001"的形状在真机上是否可能，需要逐条重问。
        let r2Stamps: [TimeInterval] = [0.0, 0.045, 0.090, 0.135, 0.180, 0.225, 0.270]
        let r2Coarse: [Double] = [0.11, 0.001, 0.10, 0.0, 0.0, 0.0]
        XCTAssertEqual(Self.changedSpanElapsedMilliseconds(stamps: r2Stamps, fractions: r2Coarse) ?? -1,
                       135, accuracy: 1, "R2 钉的是跨度 = 135ms（这条断言本轮**原样保留**）")
        XCTAssertEqual(Self.contiguousChangedRuns(stamps: r2Stamps, fractions: r2Coarse).count, 2,
                       "同一份数据在连续段这把尺下是两段 ⇒ 这就是 BACKLOG 72 的入口")
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
        let frames = film.motionFrames
        guard frames.count > 4 else {
            XCTFail("只抓到 \(frames.count) 帧，对照无效")
            return
        }
        let fractions = Self.deltas(frames)
        let span = Self.transitionFrameCount(fractions)
        emit("MOTION_AB \(scenario.name) 曲线关闭 采样≈\(Self.sampleIntervalMilliseconds(film.motionStamps))ms 过渡帧数=\(span) "
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
        // 否定判据从**触发那一帧**起算（`after: 1` + `motionFrames`），不再写"第 3 帧"：
        // 预卷的长度由抓帧耗时决定，用帧号表达就等于让判据跟着机器负载漂
        // （三臂交替实测：同一份代码给出三套不同的红集合，BACKLOG 第 6 条）。
        let residual = Self.settleResidualRatio(film.motionFrames, after: 1, band: band)
        let fractions = Self.deltas(film.motionFrames, band: band)
        emit("MOTION_CUT \(scenario.name) 带内过渡帧数=\(Self.transitionFrameCount(fractions)) "
            + "落定残余=\(String(format: "%.3f", residual)) "
            + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
        XCTAssertLessThan(residual, 0.15,
                          "带内出现了慢慢落定的过程 ⇒ `List` 的行过渡哪天能跑了，M1 要重新评估（先读这段注释）")
        // 阳性对照：同一条量法量一次**真的有过渡**的场景，必须读出明显大于 0 的残余。
        // 没有这一句，上面那条只是"这里本来就什么都不会动"，量不出尺子在这个维度上工作。
        // 取样点必须在过渡**中间**（以前固定在"第 3 帧"，90ms 采样时那已经是落定之后，
        // 于是对照自己读成 0.000，把整条判据变成"没有分辨率"却仍然报红）。
        let banner = Scenario.noticeBanner()
        let fading = record(banner)
        let interval = Self.sampleIntervalMilliseconds(fading.motionStamps)
        guard let mid = Self.midFlightPreRollFrames(durationMilliseconds: banner.declaredDurationMilliseconds,
                                                   sampleMilliseconds: interval) else {
            emit("MOTION_NOT_RUN=clock-too-coarse control=notice-banner 采样≈\(interval)ms "
                + "声明=\(Int(banner.declaredDurationMilliseconds))ms ⇒ 过渡的一半落在同一帧里")
            throw XCTSkip("MOTION_NOT_RUN=clock-too-coarse：阳性对照无从判定。它一缺席，"
                + "上面那条「行没在动」就没有分辨率证据 ⇒ 报 skip 并说明，不报绿也不报红")
        }
        let fadingResidual = Self.settleResidualRatio(fading.motionFrames, after: mid)
        emit("MOTION_CUT_CONTROL notice-banner 采样≈\(interval)ms 中点帧=\(mid) "
            + "落定残余=\(String(format: "%.3f", fadingResidual))")
        // 这一支原来是一条**无条件**的 `XCTAssertGreaterThan(fadingResidual, 0.15)`。
        // 它就是把 CI 的动效那一步弄红两次的东西（BACKLOG 100），而红当时没有名字：
        // 那一步 `continue-on-error: true`，覆盖率地板只数自己那四臂 ⇒ `exit: 1` 与 `REDS=0` 同屏。
        //   runner：采样≈21ms 中点帧=3 落定残余=0.025
        //   本机：  采样≈10ms 中点帧=7 落定残余=0.974
        // 同一条淡入在另一把尺下也一起变了：`MOTION_SETTLE banner-in` 在 runner 上是
        // 到位帧=4 ⇒ 实测落定≈76ms，本机是 到位帧=16 ⇒ ≈160ms，而两边**声明都是 150ms**。
        // ⇒ "读不出过程"的那个可能是这台机器的动画时钟，不一定是产品。
        // 但"可能是机器"不能由可疑的那次测量自己宣布 —— 那正好是 BACKLOG 49 警告的免检牌。
        // 所以请一个与被告无关、机制相同的证人（`FadeClockProbe`），证人没有分辨率时它自己
        // 也得能被判红（`testTheFadeClockClassifierIsATruthTable` 钉着它的判别力）。
        let clock = fadeClock()
        func fmt(_ value: Double) -> String { String(format: "%.3f", value) }
        // R68 / BACKLOG 104：证人能不能给"这台机器看不见"签字，取决于它**自己那条淡入分不分得开**。
        // 上一轮 runner 上的实物是证人 ≈80ms ⇒ 150ms 在它那里只有 1 段可分，
        // 于是"证人也看不见过程"说的只是证人自己的分辨率，不是产品的跳变。
        let declared = Int(FadeClockView.declaredDurationMilliseconds)
        let segments = Self.resolvableFrames(durationMilliseconds: Double(declared),
                                             sampleMilliseconds: clock.samplingMilliseconds)
        let qualifies = clock.qualifies(declaredDurationMilliseconds: declared)
        emit("MOTION_WITNESS notice-banner 证人采样≈\(clock.samplingMilliseconds)ms 声明=\(declared)ms "
            + "可分数段=\(segments) 合格=\(qualifies ? "是" : "否") 判定=\(Self.fadeClockLabel(clock.verdict)) "
            + "（判据自身采样≈\(interval)ms）")
        switch Self.controlJudgment(residual: fadingResidual, clock: clock.verdict,
                                    witnessQualifies: qualifies) {
        case .green:
            break
        case .witnessIsDead:
            XCTFail("淡入时钟探针的夹具自己读不出过程（跨度=\(fmt(clock.span)) 中间态帧数=\(clock.intermediate) "
                + "帧数=\(clock.frames)），而产品横幅在同一条件下也读不出（落定残余=\(fmt(fadingResidual))）⇒ "
                + "这两条现在没有一条能证明这把尺看得见淡入。判红而不 skip：坏的是探针，得有人去修它")
        case .witnessCannotAdjudicate:
            XCTFail("证人读不出这条淡入的过程，而它**连自己都分辨不了**"
                + "（证人≈\(clock.samplingMilliseconds)ms、声明 \(declared)ms ⇒ 只切得出 \(segments) 段，"
                + "少于『中间态 + 1』那三段的地板）⇒ 它没资格作证："
                + "一条 150ms 的过程在 80ms 的采样上本来就会塌成一帧，"
                + "所以'证人也是跳变'说的只是证人自己的分辨率，不能拿来解释产品这条读不出残余的横幅。"
                + "红着，去把证人降成本 / 加密采样（BACKLOG 104）；"
                + "把 skip 当解药等于把'我没看清'写成'它没动'")
        case .productSnapped:
            XCTFail("这台机器**看得见** 150ms 的淡入（夹具中间态 \(clock.intermediate) 帧、跨度 \(fmt(clock.span))、"
                + "采样≈\(clock.samplingMilliseconds)ms），产品横幅在同一条量法下却读不出残余"
                + "（落定残余=\(fmt(fadingResidual)) 采样≈\(interval)ms 中点帧=\(mid)）⇒ "
                + "这不是环境限制：上面那条「行没在动」仍然是空的绿，而横幅的淡入值得单独查一轮")
        case .notRun:
            emit("MOTION_NOT_RUN=fade-clock-snaps-here control=notice-banner "
                + "夹具跨度=\(fmt(clock.span)) 中间态帧数=\(clock.intermediate) 帧数=\(clock.frames) "
                + "采样≈\(clock.samplingMilliseconds)ms 而横幅落定残余=\(fmt(fadingResidual)) ⇒ "
                + "这台机器把一条声明 150ms 的淡入拍成了跳变（证人自己动了，所以不是探针坏）")
            throw XCTSkip("MOTION_NOT_RUN=fade-clock-snaps-here：阳性对照的证人在这台机器上同样看不见淡入的过程。"
                + "它一缺席，上面那条「行没在动」就没有分辨率证据 ⇒ 与 clock-too-coarse 同一处置，"
                + "不报绿也不报红。能分辨的那台机器（本机）上这条判据仍然会红，见 BACKLOG 100")
        }
    }

    /// 阳性对照那一步的**决定**：读数 + 证人的判定 → 绿 / 两种红 / 无从判定。
    ///
    /// 为什么把它抽成纯函数（R66）：这一段今天决定"runner 上那条红算不算数"，
    /// 而它原来长在只有窗口才跑得起来、且**只有走进 `residual <= floor` 那一支才会被执行**的代码里。
    /// 本机横幅的残余是 0.719–0.974，永远不进那一支 ⇒ 分支里的三条判定在本机一条都没有被执行过，
    /// 更没被证伪过（"只有真值表喂着的判据"与"只有某台机器才会走到的判据"是同一族风险）。
    /// 抽出来之后六格真值表就能钉死它，不需要一台恰好会 snap 的机器。
    /// （变异 M356–M361 的实测结果在 .scratch/motion-audit-2/r66_mutation_battery.log。）
    enum ControlJudgment: Equatable {
        case green
        /// 判红：证人自己也没读出过程 ⇒ 是探针坏了。
        case witnessIsDead
        /// 判红：这台机器能分辨，产品横幅却没读出过程 ⇒ 不是环境问题。
        case productSnapped
        /// 判红（R68）：证人读不出过程，但它采得比判据还粗 ⇒ **它没资格作证**，红不许被换成 skip。
        case witnessCannotAdjudicate
        /// 报 skip：这台机器今天看不见 150ms 淡入的过程，而且证人采得不比判据粗。
        case notRun
    }

    /// 决定表多了一根轴（R68 / BACKLOG 104）：证人的**采样率**。
    ///
    /// 原来 `.snaps` 直接 ⇒ `.notRun`，这一步偷偷假定了"证人读不出 = 这台机器读不出"。
    /// 那个假定在 runner 上被自己的读数证伪了：证人采样 ≈80ms，判据采样 35ms，
    /// 而 150ms 的淡入在 80ms 间隔上本来就只剩 1–2 帧 ⇒ 证人的 `中间态帧数=0` 说的是证人自己。
    /// ⇒ skip 现在需要**两个**条件：证人看不见过程 **且** 证人采得不比判据粗。
    /// 少了后面那半条，"我没看清"就能给"它没动"签字（与 M356 同族，方向相反）。
    static func controlJudgment(residual: Double, clock: FadeClockVerdict,
                                witnessQualifies: Bool) -> ControlJudgment {
        if residual > controlResidualFloor { return .green }
        switch clock {
        case .probeDead: return .witnessIsDead
        case .resolves: return .productSnapped
        case .snaps: return witnessQualifies ? .notRun : .witnessCannotAdjudicate
        }
    }

    /// 上面那张决定表的真值表（不开窗口，CI 每轮都跑）。
    ///
    /// R68 起是**八格**：`residual` 两档 × 证人三种判定 ×（在 `.snaps` 那一档上）证人合不合格两档。
    /// 特别是"residual 高 + 证人死了"这一格必须**绿** —— 反过来（证人死了就一律红）
    /// 会让 CI 在阳性对照已经没问题的情况下多一条假红，而假红的代价（R60 那次）
    /// 是下一次真红没人信。
    func testTheControlJudgmentIsATruthTable() {
        let qualified = true
        XCTAssertEqual(Self.controlJudgment(residual: 0.974, clock: .resolves, witnessQualifies: qualified), .green)
        XCTAssertEqual(Self.controlJudgment(residual: 0.974, clock: .snaps, witnessQualifies: qualified), .green,
                       "读数已经证明有过程，就不该回头问证人")
        XCTAssertEqual(Self.controlJudgment(residual: 0.974, clock: .probeDead, witnessQualifies: qualified), .green,
                       "同上：证人死没死都不改变'这次读出了过程'")
        XCTAssertEqual(Self.controlJudgment(residual: 0.025, clock: .resolves, witnessQualifies: qualified),
                       .productSnapped,
                       "这台机器能分辨而产品读不出 ⇒ 必须是红，不许被登记之外的任何东西吞掉")
        XCTAssertEqual(Self.controlJudgment(residual: 0.025, clock: .snaps, witnessQualifies: true), .notRun,
                       "证人同样看不见、且采得不比判据粗 ⇒ 环境限制，报 skip；判红就是拿机器判产品")
        XCTAssertEqual(Self.controlJudgment(residual: 0.025, clock: .probeDead, witnessQualifies: qualified),
                       .witnessIsDead,
                       "读不出过程、证人也坏了 ⇒ 两条都没有分辨率，必须红着让人去修")
        // 边界：正好等于地板不算"读出了过程"（`>` 而不是 `>=`，与它替掉的那条
        // `XCTAssertGreaterThan` 同一条线，不许在重构时悄悄改判据）。
        XCTAssertEqual(Self.controlJudgment(residual: Self.controlResidualFloor, clock: .resolves,
                                            witnessQualifies: qualified),
                       .productSnapped, "把 `>` 改成 `>=` 会让'刚好等于地板'的读数从红变成绿")

        // —— R68 新增的那一根轴：证人合不合格（采样率）。两格都必须与上面不同。
        XCTAssertEqual(Self.controlJudgment(residual: 0.025, clock: .snaps, witnessQualifies: false),
                       .witnessCannotAdjudicate,
                       "证人采得比判据粗时 `.snaps` 不许落到 skip —— 那等于让'我没看清'给'它没动'签字")
        XCTAssertEqual(Self.controlJudgment(residual: 0.025, clock: .resolves, witnessQualifies: false),
                       .productSnapped,
                       "证人能分辨 ⇒ 判据是红还是绿与它采得多粗无关（不合格只影响 skip 那一支）")
        // 这一格是本轮真正要钉的东西：同一个 `(residual, clock)` 对，
        // 只改证人采样率就必须给出**不同**的处置。少了这条断言，
        // 有人把 `witnessQualifies` 参数删掉、退回 `.snaps ⇒ .notRun` 也照样全绿。
        XCTAssertNotEqual(Self.controlJudgment(residual: 0.025, clock: .snaps, witnessQualifies: true),
                          Self.controlJudgment(residual: 0.025, clock: .snaps, witnessQualifies: false),
                          "`witnessQualifies` 这一根轴没有改变任何输出 ⇒ 它等于没写（BACKLOG 104 的原始形状）")
    }

    /// `qualifies(declaredDurationMilliseconds:)` 自己的真值表：合格线由**证人自己的量**推导
    /// （`声明 ÷ 采样 ≥ minimumIntermediateFrames + 1`），不是挑的一个毫秒数。
    ///
    /// 为什么单独一条：上面那张表吃的是已经算好的布尔值，
    /// 于是"把 `>=` 写成 `>`"或者"把线挪到 100ms"都不会被它抓到 —— 那是本体的两条边界。
    func testTheFadeClockWitnessQualificationIsATruthTable() {
        func reading(_ sampling: Int) -> FadeClockReading {
            FadeClockReading(frames: 30, span: 1.0, intermediate: 0, samplingMilliseconds: sampling)
        }
        // 声明 150ms、要 2 级中间态 ⇒ 至少要能切成 3 段 ⇒ 采样 ≤ 50ms。
        XCTAssertTrue(reading(20).qualifies(declaredDurationMilliseconds: 150),
                      "本机实测那一档（证人≈20ms）必须合格，否则阳性对照在这台机器上永远只能报红")
        XCTAssertTrue(reading(50).qualifies(declaredDurationMilliseconds: 150),
                      "边界：正好 3 段算合格（`>=`，与 `minimumIntermediateFrames` 那条同一条线）")
        XCTAssertFalse(reading(51).qualifies(declaredDurationMilliseconds: 150),
                       "边界：3 段差一点点就不算 —— 这条线一挪，skip 的门槛就跟着变")
        XCTAssertFalse(reading(80).qualifies(declaredDurationMilliseconds: 150),
                       "runner 那一遍的实测形状（证人≈80ms ⇒ 150/80 只有 1 段）⇒ 必须不合格，"
                           + "否则 skip 就是免检牌（BACKLOG 104 的原始缺陷）")
        XCTAssertFalse(reading(0).qualifies(declaredDurationMilliseconds: 150),
                       "读不出采样率 ⇒ 什么都不知道，不许给任何结论签字")
        XCTAssertFalse(reading(-1).qualifies(declaredDurationMilliseconds: 150),
                       "同上（`sampleIntervalMilliseconds` 空数组返回 −1）")
        XCTAssertFalse(reading(20).qualifies(declaredDurationMilliseconds: 0),
                       "声明时长读不出来 ⇒ 没有'能不能分辨'这回事")
        // 判定本身不受这根轴影响：证人"看不见过程"这个读数与它够不够细是两件事。
        XCTAssertEqual(reading(80).verdict, .snaps)
        XCTAssertEqual(reading(35).verdict, .snaps)
    }

    /// 阳性对照"读出过渡了"的地板。
    ///
    /// 刻意**不与上面那条「行没在动」的 0.15 共用一个常量**：那个 0.15 说的是"带里不许有
    /// 慢慢落定的过程"（产品的形状），这个 0.15 说的是"这把尺在这个维度上有分辨率"（尺子的形状）。
    /// 两个含义共用一个数，就等于哪天调其中一个时把另一个也悄悄改了（同一族：
    /// 「同一个词在两个判据里含义不同，就别统一成一个布尔值」）。
    static let controlResidualFloor: Double = 0.15

    /// 这台机器 + 这条捕获通道，能不能把一次声明 150ms 的透明度淡入切成几级？跑一次，缓存。
    private func fadeClock() -> FadeClockReading {
        if let cached = Self.fadeClockCache { return cached }
        let run = FadeClockProbe().record()
        let reading = Self.fadeClockReading(levels: run.levels,
                                            samplingMilliseconds: run.samplingMilliseconds)
        Self.fadeClockCache = reading
        // 结论行在闸门之前（R53）：`.snaps` 那一支马上要抛 skip，抛出去之后这行读数
        // 就是那次判定在这台机器上唯一的痕迹。
        emit("MOTION_FADE_CLOCK 声明=\(Int(FadeClockView.declaredDurationMilliseconds))ms "
            + "跨度=\(String(format: "%.3f", reading.span)) 中间态帧数=\(reading.intermediate) "
            + "帧数=\(reading.frames) 采样≈\(reading.samplingMilliseconds)ms "
            + "判定=\(Self.fadeClockLabel(reading.verdict))")
        writeStrip("fade-clock", run.frames)
        return reading
    }

    static func fadeClockLabel(_ verdict: FadeClockVerdict) -> String {
        switch verdict {
        case .probeDead: return "探针坏了"
        case .resolves: return "能分辨"
        case .snaps: return "拍成跳变"
        }
    }

    /// 全 `Views/` 一族的"不许留不会执行的过渡声明"（R5 扩的族）。
    ///
    /// 原来这条守卫只读 `HistorySidebarView.swift` 一个文件，于是同一族缺陷在另外三处各活了一次：
    /// `MenuBarRecommendationsView` 挂着 `.transition` 而整个文件 `grep -c "animation(" = 0`；
    /// `DetailView` 的详情空态挂在没有驱动的 `body` 上；侧栏那条干脆挂在 `Spacer()` 上
    /// （Spacer 没有可见内容 —— 于是"空态淡入"在代码里存在、在屏幕上不存在）。
    /// **按名字/按文件扫的守卫，漏一个文件就等于没写**（与 R3 那条"按族查消费者"同一课）。
    func testNoUnexecutedTransitionClaimsAcrossViews() throws {
        let offenders = Self.unexecutedTransitionOffenders(
            try Self.viewsSources().map { (file: $0.0, source: $0.1) })
        XCTAssertTrue(offenders.isEmpty,
                      "这些文件留着不会执行的过渡声明（比没有更坏：下一个人会以为已经做了）：\n"
                          + offenders.joined(separator: "\n"))

        // 详情空态：过渡要挂在**有可见内容的那一支**上，并且 body 要有驱动。
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("value: historyStore.selectedEntry == nil"),
                      "详情空态的 .transition 又变成孤儿声明了：body 上没有按「有没有选中」驱动的动画")
        // 侧栏空态：过渡必须落在 EmptyStateView 那一段里，不是后面的 Spacer。
        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        let emptyBranch = try XCTUnwrap(
            sidebar.components(separatedBy: "EmptyStateView(").dropFirst().first?
                .components(separatedBy: "Spacer()").first,
            "找不到侧栏空态那一段：锚点失效")
        XCTAssertTrue(emptyBranch.contains(".transition(MotionCatalog.transition(for: .contentFade))"),
                      "侧栏空态的过渡不在 EmptyStateView 这一段里 —— 挂在 Spacer 上等于没挂")
    }

    /// 上面那条扫描器的**真值表**：两边都要钉住，一条只测"抓得住"的守卫会在下一次改排除项时失去刹车。
    ///
    /// 为什么单独一条：变异 M6 实测过 —— 往一个没有任何动画的文件里塞回
    /// `.transition(MotionCatalog.transition(for: .contentFade))`，扫描器一声不响（ESCAPED），
    /// 原因就在排除项写成了"这一行含 content 子串"。那种 bug 只有直接喂源码给扫描器才测得出来，
    /// 不该等到有人在产品里写出同样的声明才发现。这条不开窗口、不受 `CLIPBOARD_HISTORY_UI_MOTION` 门，
    /// CI 上每轮都跑。
    func testTransitionClaimScanIsATruthTable() throws {
        func lines(_ source: String) -> [String] {
            Self.stripCommentLines(source).components(separatedBy: "\n")
        }

        // ① 角色名不是豁免：`.contentFade` 里含 "content"，但它是给某一屏许愿的声明，必须抓到。
        let roleNamed = """
        struct DeadPane: View {
            var body: some View {
                Text("空态")
                    .transition(MotionCatalog.transition(for: .contentFade))
            }
        }
        """
        XCTAssertEqual(Self.transitionClaimLines(lines(roleNamed), declaresContentPlaceholder: false), [3],
                       "带角色名 .contentFade 的死声明没被抓到（这就是变异 M6 曾经 ESCAPED 的那一支）")
        XCTAssertEqual(Self.unexecutedTransitionOffenders([("DeadPane.swift", roleNamed)]),
                       ["DeadPane.swift：1 处 .transition 声明，整个文件没有任何动画驱动"],
                       "整个文件没有驱动时，扫描器要报出这个文件")

        // ② 裸写法也逃不掉：以前只数 MotionCatalog 的两个工厂名，`.transition(.opacity)` 从尺子底下走过去。
        let bare = """
        struct BarePane: View {
            var body: some View {
                Text("空态").transition(.opacity)
            }
        }
        """
        XCTAssertEqual(Self.transitionClaimLines(lines(bare), declaresContentPlaceholder: false).count, 1,
                       "`.transition(.opacity)` 这种不经过目录的声明不在检测面上")

        // ③ 工厂那一条确实要豁免（否则守卫在 `SymbolMotion` 上是假阳性，而假阳性会逼人把守卫删掉）。
        let factory = """
        struct SymbolMotion: ViewModifier {
            func body(content: Content) -> some View {
                content.id("x").transition(MotionCatalog.transition(for: .contentFade))
            }
        }
        """
        XCTAssertTrue(Self.transitionClaimLines(lines(factory), declaresContentPlaceholder: true).isEmpty,
                      "ViewModifier 工厂里挂在占位符 content 上的过渡被当成违规：这是守卫的假阳性")

        // ④ 豁免要有前提：文件里没有 `func body(content: Content)`（占位符根本不存在）时，
        //    同一行 `content.x.transition(...)` 不能再买到免死金牌。
        XCTAssertEqual(Self.transitionClaimLines(lines(factory), declaresContentPlaceholder: false).count, 1,
                       "没有 ViewModifier 占位符的文件里，content. 开头的行仍被豁免 ⇒ 排除项成了漏洞")

        // ⑤ 换行写法：链根在上一行。
        let split = """
        func body(content: Content) -> some View {
            content
                .transition(MotionCatalog.transition(for: .bannerIn))
        }
        """
        XCTAssertTrue(Self.transitionClaimLines(lines(split), declaresContentPlaceholder: true).isEmpty,
                      "content 换行再挂 .transition 的写法没被认成工厂链")

        // ⑥ 注释里的例子不是声明（`MotionModifiers` 的文档注释就写着 `.transition(.opacity)`）。
        let documented = """
        // 退化成交叉淡入（身份变了 + `.transition(.opacity)`）
        struct P: View { var body: some View { Text("x") } }
        """
        XCTAssertTrue(Self.transitionClaimLines(lines(documented), declaresContentPlaceholder: false).isEmpty,
                      "注释里的例子被当成了产品声明")
    }

    /// 上面那条按族扫描的**判据本体**：给定 (文件名, 源码)，返回"声明了过渡、整个文件却没有驱动"的报告。
    ///
    /// 抽成纯函数只为一件事：它能被真值表直接测（`testTransitionClaimScanIsATruthTable`），
    /// 而不用等某人哪天手滑把一条死声明塞回产品里。
    ///
    /// 排除项只有一条，而且必须是**结构**的：`ViewModifier` 工厂里挂在占位符 `content` 上的那条
    /// 不是"给某一屏许愿"的过渡，是给别人造过渡的工厂，它自己没有驱动是正常的（驱动来自调用方
    /// 所在的那棵树）。**这一条曾经写成 `!line.contains("content")`** —— 于是 `.contentFade`
    /// 这个*角色名*把它本来最该抓的那类声明整行豁免了（变异 M6 实测 ESCAPED：往
    /// `MenuBarRecommendationsView` 塞回 `.transition(MotionCatalog.transition(for: .contentFade))`，
    /// 守卫一声不响）。名字里带 content 不算豁免；豁免要求这一行的修饰链根就是标识符 `content`，
    /// 并且这个文件真的声明了 `func body(content: Content)` —— 否则任何普通视图里出现
    /// 一句 "content." 也能买到免死金牌。
    static func unexecutedTransitionOffenders(_ sources: [(file: String, source: String)]) -> [String] {
        var offenders: [String] = []
        for entry in sources {
            let code = stripCommentLines(entry.source)
            let lines = code.components(separatedBy: "\n")
            let claims = transitionClaimLines(lines,
                                              declaresContentPlaceholder: code.contains("func body(content: Content)"))
            guard !claims.isEmpty else { continue }
            // 声明了过渡，这个文件里就必须有能驱动它的东西（事务或按值的动画）。
            if !code.contains("withAnimation(") && !code.contains(".animation(") {
                offenders.append("\(entry.file)：\(claims.count) 处 .transition 声明，整个文件没有任何动画驱动")
            }
        }
        return offenders
    }

    /// 返回"这一行给某一屏许愿了过渡"的行下标。
    ///
    /// 匹配的是修饰符本身（`.transition(`），不是某个目录的函数名 —— 原来只数
    /// `MotionCatalog.transition(for:` 与 `asymmetricTransition(`，于是有人写
    /// `.transition(.opacity)` 这条死声明就直接从尺子底下走过去（同族第三次：检测面比缺陷面窄）。
    static func transitionClaimLines(_ lines: [String], declaresContentPlaceholder: Bool) -> [Int] {
        var claims: [Int] = []
        for (index, raw) in lines.enumerated() {
            guard raw.contains(".transition(") else { continue }
            if declaresContentPlaceholder, isPlaceholderChain(raw, lines: lines, at: index) { continue }
            claims.append(index)
        }
        return claims
    }

    /// 这一行的修饰链根是不是 ViewModifier 的占位符 `content`（两种写法都要认：
    /// `content.id(x).transition(...)` 一行写法，以及 `content` 换行再挂修饰符的两行写法）。
    private static func isPlaceholderChain(_ raw: String, lines: [String], at index: Int) -> Bool {
        let trimmed = raw.trimmingCharacters(in: .whitespaces)
        if trimmed.hasPrefix("content.") || trimmed.hasPrefix("content ") || trimmed == "content" { return true }
        var previous = index - 1
        while previous >= 0 {
            let candidate = lines[previous].trimmingCharacters(in: .whitespaces)
            if candidate.isEmpty { previous -= 1; continue }
            // 只回看第一处非空行：链根在那儿就是 `content`，在别处就不算豁免。
            return candidate == "content" || candidate.hasSuffix(" content")
        }
        return false
    }

    /// 列出 `Sources/ClipboardHistoryApp/Views/*.swift`。
    /// 本文件原来只有 `productSource(named:)`（按一个文件名取），而**按族扫**需要整目录 ——
    /// 没有它就只能一个文件一个文件写死，那正是这条守卫原来漏掉三处的原因。
    private static func viewsSources() throws -> [(String, String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/Views", isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            return names.filter { $0.hasSuffix(".swift") }.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "MotionFilmstripTests", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Views 目录：这条按族扫描的守卫没有扫描对象时必须红"])
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

        let scenario = Scenario.detailKindChange()
        let kindChange = record(scenario)
        let interval = Self.sampleIntervalMilliseconds(kindChange.motionStamps)
        // 阳性那一半必须在过渡**中间**取残差：固定在"第 3 帧"时，粗采样下那已经是落定之后，
        // 残差读成 0 ⇒ 判据把尺子的分辨率问题报成"过渡没接上"（本机三臂实测就是这样红的）。
        guard let mid = Self.midFlightPreRollFrames(durationMilliseconds: scenario.declaredDurationMilliseconds,
                                                   sampleMilliseconds: interval) else {
            emit("MOTION_NOT_RUN=clock-too-coarse detail-kind-change 采样≈\(interval)ms "
                + "声明=\(Int(scenario.declaredDurationMilliseconds))ms ⇒ 取不到过渡中点")
            throw XCTSkip("MOTION_NOT_RUN=clock-too-coarse：这一半无从判定，既不判红也不判绿")
        }
        let crossfade = Self.settleResidualRatio(kindChange.motionFrames, after: mid, band: band)
        let kindFractions = Self.deltas(kindChange.motionFrames, band: band)
        emit("MOTION_DETAIL kind-change 采样≈\(interval)ms 中点帧=\(mid) "
            + "带内过渡帧数=\(Self.transitionFrameCount(kindFractions)) "
            + "落定残余=\(String(format: "%.3f", crossfade))")
        XCTAssertGreaterThan(crossfade, 0.15,
                             "换类型时详情区一帧到位 ⇒ 那条 `.transition` 没接上线（或又被谁摘掉了）")

        // 否定那一半从触发帧起算：文本→文本"不该演"，越早取越严格（第 1 帧就该是最终态）。
        let sameKind = record(Scenario.detailSameKind())
        let snap = Self.settleResidualRatio(sameKind.motionFrames, after: 1, band: band)
        let sameFractions = Self.deltas(sameKind.motionFrames, band: band)
        emit("MOTION_DETAIL same-kind 带内过渡帧数=\(Self.transitionFrameCount(sameFractions)) "
            + "落定残余=\(String(format: "%.3f", snap))")
        XCTAssertLessThan(snap, 0.15,
                          "两条文本之间也在淡 ⇒ 每次方向键翻记录都演一遍，那是负债")
    }

    /// 空态 ↔ 内容这一层到底演没演（R16）—— 先问尺子看不看得见，再问产品。
    ///
    /// 为什么不能直接断"过渡帧数 > 1"：R11 已经量过一件事 ——
    /// `cacheDisplay` 抓的是**模型树**，纯 opacity 的交叉淡活在 presentation 层。
    /// 而这一层两臂内容与位置都不同，理论上比热图那条更可见，所以**不能沿用 R11 的结论**，
    /// 必须重做一次双向 A/B：开着动画与关着动画各抓一卷。
    /// 两臂不同 ⇒ 尺子看得见，那就该把它当**硬判据**（本条会红，逼着升级）；
    /// 两臂相同 ⇒ 只能记「源码已接、产物未量」，接线由 `MotionCatalogTests`
    /// 那条"两臂必须成对"的结构守卫看着。
    func testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind() throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.40, y: 0.12, width: 0.58, height: 0.76)   // 详情区，避开标题栏
        let scenario = Scenario.detailEmptyToContent()
        let saved = MotionCatalog.animationsEnabled
        let onFilm = record(scenario)
        MotionCatalog.animationsEnabled = false
        let offFilm = record(scenario)
        MotionCatalog.animationsEnabled = saved

        // 两臂各写一条胶片带：这条判据读不出差别，那就**让人看见"读不出差别"**。
        // 只看数字会把"尺子瞎"和"产品没动"混成一件事；把两卷并排放着，
        // 人眼至少能确认"这两卷确实一样"，而不是猜探针是不是根本没抓到东西。
        writeStrip("detail-empty-to-content-开", onFilm.motionFrames)
        writeStrip("detail-empty-to-content-关", offFilm.motionFrames)

        let on = Self.deltas(onFilm.motionFrames, band: band)
        let off = Self.deltas(offFilm.motionFrames, band: band)
        let onSpan = Self.transitionFrameCount(on)
        let offSpan = Self.transitionFrameCount(off)
        emit("MOTION_DETAIL_AB empty-to-content 开 帧数=\(onSpan) 峰值=\(String(format: "%.3f", Self.peak(on)))"
            + " 冷闸=\(onFilm.clockIsWarm)  关 帧数=\(offSpan) 峰值=\(String(format: "%.3f", Self.peak(off)))"
            + " 采样≈\(Self.sampleIntervalMilliseconds(onFilm.motionStamps))ms")
        XCTAssertGreaterThan(Self.peak(on), Self.minimumVisibleChange,
                             "两臂什么都没变 ⇒ 触发没让图长出来，这条 A/B 没有对照物（是探针坏了，不是动效坏了）")
        XCTAssertTrue(onFilm.clockIsWarm && offFilm.clockIsWarm,
                      "有一臂是在冷采样下抓的 ⇒ 两臂相同不能算尺子的极限，这条结论今天不成立")
        if onSpan == offSpan, abs(Self.peak(on) - Self.peak(off)) < 0.02 {
            emit("MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content："
                + "开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」")
        } else {
            XCTFail("两臂读数不同 ⇒ 这把尺**看得见**这条交叉淡 ⇒ 把本条改成硬判据"
                    + "（开着的过渡帧数必须大于关着的），别留一句免责")
        }
    }

    /// 位移档的**真实时长**（MC-2 的像素那一半），用毫秒表达。
    ///
    /// 以前它写的是"到位帧数 ≤6"，而 6 帧在 31ms 采样下是 186ms、在 90ms 采样下是 540ms ——
    /// 同一个数字在两种时钟下一个是松一个是紧，紧的那一侧就是那条间歇性红。
    /// 现在判的是**落定耗时**：`到位帧 × 实测采样间隔`，上限 = 声明时长的两倍再让一个采样间隔。
    ///
    /// 说清楚这条能证明什么、不能证明什么：本机有效采样约 31–90ms，所以它分辨不出
    /// "150ms 还是 200ms"——那需要 4ms 一帧。它能证明的是**没有跑飞**：
    /// 声明 0.15s 的滑入如果实际要 0.4s 才落定，这里就会超过上限。
    /// 第一版的病正在相反的方向：`duration(for:)` 写 0.15，而 `animation(for:)` 在位移档
    /// 里用写死的 `response: 0.32`，纯值守卫一声不响（报告场景 C：声明 150ms、实测 200ms）。
    /// 那一半已经由 `testCurveSecondsComeFromTheDurationTable` 钉住；这条钉的是产物。
    ///
    /// **R58 把这里的 `band` 去掉了，理由值得留在原地**：这一卷从 R57 起只拍顶部那条带
    /// （1520×96px），于是"整幅"就已经是"横幅那一条"；再套一层归一化矩形
    /// （`y 0.02–0.22`）量的是**带里再框一条 9.5pt 的窄缝**（横幅顶边那点底色，文字都不在里面）。
    /// 同一卷的读数因此从"落定≈121ms/帧 11"变成"66ms/帧 6" —— 两个数都没让这条判据变红，
    /// 也就是说**换了捕获区域之后，这条判据安静地量了别的东西**（BACKLOG 80 的第二半：
    /// 镜像是一半，嵌套是另一半）。由 `testNoTestFramesABandInsideABandCapturedFilm` 钉住不再复发。
    func testSlidingRoleSettlesWithinItsBudget() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.noticeBanner()
        let film = record(scenario)
        let interval = Self.sampleIntervalMilliseconds(film.motionStamps)
        guard Self.premisePictureChanged(film.motionFrames, band: nil) else {
            emit("MOTION_NOT_RUN=premise-not-visible banner-in 带内触发前后逐像素相同 ⇒ 这次变更在画面里不存在")
            throw XCTSkip("MOTION_NOT_RUN=premise-not-visible：落定态与起始态相同，落定时长无从谈起")
        }
        guard let settled = Self.settledAtFrame(film.motionFrames, band: nil) else {
            let steps = Self.deltas(film.motionFrames, band: nil)
            emit("MOTION_NOT_RUN=no-visible-change banner-in 帧数=\(film.motionFrames.count) 采样≈\(interval)ms "
                + "峰值相邻差=\(String(format: "%.4f", steps.max() ?? -1)) "
                + "带内逐帧相邻差=\(steps.map { String(format: "%.3f", $0) })"
                + " ⇒ 这一带从头到尾没变过（没触发，或者没框到）")
            throw XCTSkip("MOTION_NOT_RUN=no-visible-change：这条判据今天没有对照物")
        }
        let duration = scenario.declaredDurationMilliseconds
        let settledMilliseconds = Double(settled) * Double(max(interval, 1))
        emit("MOTION_SETTLE banner-in 到位帧=\(settled) 采样≈\(interval)ms ⇒ 实测落定≈\(Int(settledMilliseconds))ms"
            + "（声明 \(Int(duration))ms；R58 起量的是整条带，不再套第二层框）")
        // "有过程"那一半只在时钟切得出至少 3 帧时才判：否则一次正确的过渡本来就会在两帧内到位。
        if Self.resolvableFrames(durationMilliseconds: duration, sampleMilliseconds: interval) >= 3 {
            XCTAssertGreaterThanOrEqual(settled, 2,
                                        "触发后的第 \(settled) 帧就已经是最终态 ⇒ 这条位移档没有过程")
        } else {
            emit("MOTION_NOT_RUN=clock-too-coarse settle-process 采样≈\(interval)ms 声明=\(Int(duration))ms"
                + " ⇒ 「有几帧在动」这一半无从判定（上限那一半照判）")
        }
        XCTAssertLessThanOrEqual(settledMilliseconds, duration * 2 + Double(interval),
                                 "横幅滑入实测落定 ≈\(Int(settledMilliseconds))ms，远超声明的 \(Int(duration))ms："
                                 + "曲线跑飞或者有别的东西在重排这一带")
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
        emit("MOTION_SYMBOL row-star 开 帧数=\(Self.transitionFrameCount(on)) 峰值=\(String(format: "%.3f", Self.peak(on)))")
        emit("MOTION_SYMBOL row-star 关 帧数=\(Self.transitionFrameCount(off)) 峰值=\(String(format: "%.3f", Self.peak(off)))")
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
        emit("MOTION_NATIVE row-insert 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated))) 采样≈\(animatedInterval)ms")
        emit("MOTION_NATIVE row-insert 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant))) 采样≈\(instantInterval)ms")
        // 数字先打，再决定"是产品没动还是这台机器没给前提"。问的是**布局那一臂**：
        // runner 上行动画量得到（3 帧），拿渐变那一臂去问会把它一起 skip 掉。
        try await requireObservableMotion(.layout)
        try requireAppWasActive(probe.wasActive)
        XCTAssertGreaterThan(Self.peak(animated), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 我连表格在哪都没框到，两臂相同这条结论不成立（是探针坏了，不是动效坏了）")
        XCTAssertLessThanOrEqual(instantSpan, 1,
                                 "关掉动画那一档本该是一帧到位，却量到 \(instantSpan) 帧在动 ⇒ 带里有别的动在跑（滚动条淡出？），两臂对照失效")
        XCTAssertGreaterThanOrEqual(animatedSpan, Self.minimumTransitionFrames,
                                    "开了 `.effectFade` 仍只读到 \(animatedSpan) 帧 ⇒ 这把尺看不见 AppKit 的行动画"
                                    + "（`cacheDisplay` 抓的是模型树）。① 只能记成'源码已接、产物未量'，不许写进已交付")
    }

    /// 行**移动**这把尺看不看得见（R17）。
    ///
    /// 为什么单独一条：`testNativeRowAnimationIsVisibleToTheRuler` 量的是插行，
    /// 而 `moveRow(at:to:)` 是另一条 API —— 它没有 `withAnimation:`，
    /// 动不动完全由 `NSAnimationContext.allowsImplicitAnimation` 决定。
    /// 本轮把"刚复制的那条被顶到最前"从整表硬刷新改成一次 `moveRow`，
    /// **前提就是它真的会动**；这条判据量的正是这个前提。
    /// 两臂用产品实际会传的那两个值（`rowAnimationOptions` 的两种输出），不是我另写的。
    func testNativeRowMoveIsVisibleToTheRuler() async throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.04, y: 0.10, width: 0.92, height: 0.78)   // 表格区，避开标题栏
        let probe = TableProbe()
        probe.appliesMoveInsteadOfInsert = true

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
        emit("MOTION_NATIVE row-move 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated)))"
            + " 采样≈\(animatedInterval)ms")
        emit("MOTION_NATIVE row-move 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant)))"
            + " 采样≈\(instantInterval)ms")
        // R53：结论行**打在两道 skip 之前**。
        //
        // R50 加这条三态判据时，我把 `print` 留在了 `requireAppWasActive` 后面，于是
        // "runner 跳过这一臂"与"runner 判出瞬移"在日志里长得一模一样：两臂读数打得出来，
        // 结论行却永远不出现（run 38543090198 / 38543812477 两次都只留下四行 `MOTION_NATIVE`，
        // 而 `MOTION_NATIVE_MOVE 判定=` 一次都没有）。
        // 结论是**读数的一种读法**，不是产品结论；谁为它负责才需要那两道 skip。
        // 所以：读法先打，判红与否在后面（下面那个 `switch` 一行没动）。
        let verdict = Self.nativeMoveVerdict(animatedSpan: animatedSpan, animatedPeak: Self.peak(animated),
                                             instantSpan: instantSpan, instantPeak: Self.peak(instant))
        let verdictLabel: String = {
            switch verdict {
            case .animated: return "动了"
            case .notAnimated: return "瞬移"
            case .samplingMissed: return "采样错过"
            }
        }()
        emit("MOTION_NATIVE_MOVE 判定=\(verdictLabel) 峰值容差="
            + String(format: "%.3f", Self.nativeMovePeakTolerance)
            + "（同一卷的 insert 读数在上一行：insert 能看见多帧 ⇒ 通道不瞎）"
            + "；这一行只说读数怎么读，产品结论要过下面两道 skip 才算")
        try await requireObservableMotion(.layout)
        try requireAppWasActive(probe.wasActive)
        XCTAssertGreaterThan(Self.peak(animated), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 连表格在哪都没框到，两臂对照失效（是探针坏了，不是移动没发生）")
        XCTAssertLessThanOrEqual(instantSpan, 1,
                                 "关掉隐式动画那一档本该一帧到位，却量到 \(instantSpan) 帧在动"
                                 + " ⇒ 带里有别的动在跑，两臂对照失效")
        // R50：原来这里只有一句"帧数 ≥2 否则红"。runner 第一次跑到这条时给的是
        // `开 帧数=1 峰值=0.047 / 关 帧数=1 峰值=0.047` —— 那句话**没说清**这是"瞬移"还是"错过"，
        // 而这两种结论的性质不同（前者是产品少做了一段动画，后者是这台机器今天量不了）。
        switch verdict {
        case .animated:
            break
        case .notAnimated(let a, let ap, let i, let ip):
            XCTFail("两臂形状一致（开 \(a) 帧/峰值 \(String(format: "%.3f", ap))、"
                    + "关 \(i) 帧/峰值 \(String(format: "%.3f", ip))）⇒ 这次 `moveRow` 是**瞬移**。"
                    + "同一卷里 `MOTION_NATIVE row-insert` 的开臂是能看见多帧的，"
                    + "而 `wasActive` 为真 ⇒ "
                    + "「通道瞎了」与「进程没激活」这两个解释都不成立（BACKLOG 75）")
        case .samplingMissed(let a, let ap, let i, let ip):
            emit("MOTION_NOT_RUN=native-move-sampling-missed row-move："
                + "两臂都只读到 \(a)/\(i) 帧，但峰值差 \(String(format: "%.3f", abs(ap - ip))) "
                + "超过 \(String(format: "%.3f", Self.nativeMovePeakTolerance)) ⇒ "
                + "说不清是没动还是采样错过，今天不判产品")
        }
    }

    /// `nativeMoveVerdict` 的真值表（R50 / BACKLOG 75）。
    ///
    /// 这条不开窗口、CI 每次都跑。理由与 R47 那条一样：**修尺子的代码如果只被一把
    /// "平时不跑"的判据守着，它下一次漂回去是没人知道的** —— 而这条判据今天还从来没在
    /// 本机跑过（本机进程无法激活），它的全部风险都在"读日志的人怎么解释 1 帧"。
    func testNativeMoveVerdictSeparatesJumpFromMissedSampling() {
        // ① 开臂多帧 ⇒ 动了（这是唯一能写"看得见"的形状）。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 4, animatedPeak: 0.052,
                                              instantSpan: 1, instantPeak: 0.061), .animated)
        // ② **runner 今天的真读数**：两臂帧数与峰值都一样 ⇒ 瞬移，不许被写成"量不到"。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 1, animatedPeak: 0.047,
                                              instantSpan: 1, instantPeak: 0.047),
                       .notAnimated(animatedSpan: 1, animatedPeak: 0.047,
                                    instantSpan: 1, instantPeak: 0.047),
                       "两臂一模一样还说'说不清'，等于把产品缺陷降级成噪声")
        // ③ 帧数都是 1、峰值差得远 ⇒ 采样错过，**不判产品**。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 1, animatedPeak: 0.090,
                                              instantSpan: 1, instantPeak: 0.047),
                       .samplingMissed(animatedSpan: 1, animatedPeak: 0.090,
                                       instantSpan: 1, instantPeak: 0.047))
        // ④ 边界：峰值差**正好**等于容差 ⇒ 仍算形状一致（门槛含等号）。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 1, animatedPeak: 0.060,
                                              instantSpan: 1, instantPeak: 0.040),
                       .notAnimated(animatedSpan: 1, animatedPeak: 0.060,
                                    instantSpan: 1, instantPeak: 0.040))
        // ⑤ 边界：帧数正好等于最低要求 ⇒ 算动了（含等号，理由同上）。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 2, animatedPeak: 0.047,
                                              instantSpan: 1, instantPeak: 0.047), .animated)
        // ⑦ 峰值差必须取**绝对值**：开臂比对照臂"变得少"（0.030 vs 0.090）也是形状不一致，
        //    写成有符号减法会让它被读成"一致"⇒ 判成瞬移，而它其实是"开臂动得比对照还小"，
        //    那是探针或带选错了的信号，不是产品的结论。（变异 M248 就是去符号化这一格。）
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 1, animatedPeak: 0.030,
                                              instantSpan: 1, instantPeak: 0.090),
                       .samplingMissed(animatedSpan: 1, animatedPeak: 0.030,
                                       instantSpan: 1, instantPeak: 0.090))
        // ⑥ 对照臂自己抖了（3 帧）也不许把结论翻成"看得见"：判定只看开臂帧数与两臂形状。
        XCTAssertEqual(Self.nativeMoveVerdict(animatedSpan: 1, animatedPeak: 0.047,
                                              instantSpan: 3, instantPeak: 0.047),
                       .notAnimated(animatedSpan: 1, animatedPeak: 0.047,
                                    instantSpan: 3, instantPeak: 0.047))
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
        emit("MOTION_SEQUENCE 选中没变 帧数=\(sameSpan) 峰值=\(String(format: "%.3f", Self.peak(sameRow)))")
        emit("MOTION_SEQUENCE 选中变了 帧数=\(movedSpan) 峰值=\(String(format: "%.3f", Self.peak(moved)))")
        try await requireObservableMotion(.layout)
        try requireAppWasActive(probe.wasActive)
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
        emit("MOTION_SHIMMER 扫 帧数=\(runningFrames.count) 变化帧对=\(Self.transitionFrameCount(running)) 峰值=\(String(format: "%.3f", Self.peak(running))) 采样≈\(interval)ms")
        emit("MOTION_SHIMMER 停 变化帧对=\(Self.transitionFrameCount(stopped)) 峰值=\(String(format: "%.3f", Self.peak(stopped)))")
        // 骨架扫光属于**渐变几何**那一类 —— 必须问同一类的对照臂，
        // 否则 runner 看得见布局位移、看不见渐变位移，会把这条判成产品坏了（run 38259612264 就是这个形状）。
        try await requireObservableMotion(.gradient)
        XCTAssertGreaterThan(Self.peak(running), Self.minimumVisibleChange,
                             "该扫的那一档什么都没变 ⇒ 扫光没落地（先看上面那行的帧数与尺寸，0 帧和 0 变化是两种病）")
        XCTAssertGreaterThanOrEqual(Self.transitionFrameCount(running), Self.minimumTransitionFrames,
                                    "只读到 \(Self.transitionFrameCount(running)) 对在变 ⇒ 那不是循环，是一次跳变")
        XCTAssertLessThan(Self.peak(stopped), Self.minimumVisibleChange,
                          "减弱动态那一档还在变 ⇒ 常驻动画没被门住（HIG 与 WCAG 2.3.3 要的就是这一条）")
    }

    /// `NSTableView` 的行动画只在**激活的 App** 里跑（实测：同一份代码 active 时 11 对在变、
    /// 非 active 时 1 对，而总变化量相同）。裸 `swift test` 进程拿不到激活态是不稳定的，
    /// 所以这是一个**前提**而不是判据：拿不到就报 not-run。
    /// 产品里这个前提天然成立 —— 浮层是 `makeKeyAndOrderFront` + `NSApp.activate`（D-041）。
    private func requireAppWasActive(_ wasActive: Bool) throws {
        if !wasActive { emit("MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画") }
        try XCTSkipUnless(wasActive,
                          "MOTION_NOT_RUN=app-not-active：这一卷是在非激活进程里抓的，"
                          + "AppKit 本来就不跑行动画 ⇒ 不能据此判产品没动")
    }

    /// **这把尺的边界探针**见下面 `testTheRulerSeesAStateDrivenSwiftUIUpdate`
    /// 与 `requireObservableMotion(_:)`：两臂读数决定"量不到"该记在尺子上还是产品上。
    ///
    /// **这台机器能不能观察到某一类位移** —— 用一个已知该动的视图问一次，缓存下来。
    ///
    /// 为什么需要：CI 的无头 runner 不绘制 SwiftUI 内容（82 帧里那两帧 95% 空白是既有事实），
    /// 于是"读不到动"有两种可能 —— 产品没动，或者这台机器看不见动。**把后者判成前者，
    /// 就是拿探针的故障当被测系统的故障**（账本里记过整族）。
    ///
    /// 关键是**要问对那一类**。run 38259612264 第一次把两行读数打出来之后现场很清楚：
    /// 同一台 runner 上「换文字 + 平移方块」读到 17 对在变（峰值 0.025），
    /// 而「只动渐变端点」读到 **0 对、峰值 0.000** —— 也就是说它能看见布局型位移，
    /// 看不见渐变几何的位移。所以骨架扫光必须问渐变那一臂（问不到就 skip），
    /// 而 AppKit 行动画那两条要问布局那一臂（它在那台机器上确实量得到，不许被一起 skip 掉）。
    /// 问不出来就 `MOTION_NOT_RUN=` + skip，而不是红，也不是绿；数字永远先打出来。
    enum MotionClass {
        case layout      // 换内容 / 平移：`TickCounterView`
        case gradient    // 只动 `LinearGradient` 的端点：`GradientTickView`
    }

    private func requireObservableMotion(_ klass: MotionClass) async throws {
        let marker = klass == .layout ? "layout" : "gradient"
        if let cached = Self.observableCache[klass] {
            try XCTSkipIf(!cached, "MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
            return
        }
        let frames = StateTickProbe().record(motionClass: klass)
        let control = Self.deltas(frames)
        let observable = Self.peak(control) > Self.minimumVisibleChange
        Self.observableCache[klass] = observable
        if !observable {
            emit("MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion 对照臂峰值=\(String(format: "%.4f", Self.peak(control))) 帧数=\(frames.count)")
        }
        try XCTSkipIf(!observable, "MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
    }

    /// 对照臂本身：**已知该动的东西必须动**，而且**两类各问一次**。
    /// 它是 `requireObservableMotion(_:)` 的判据来源，所以它自己只在"连布局位移都看不见"时
    /// 报 skip（那是环境），而不是红；渐变那一臂只报数 —— 它看不见是**事实**，不是失败。
    func testTheRulerSeesAStateDrivenSwiftUIUpdate() async throws {
        try skipUnlessEnabledAndCapable()
        let frames = StateTickProbe().record(motionClass: .layout)
        let fractions = Self.deltas(frames)
        emit("MOTION_CONTROL 计数方块 帧数=\(frames.count) 峰值=\(String(format: "%.3f", Self.peak(fractions))) 变化帧对=\(Self.transitionFrameCount(fractions))")
        let gradient = StateTickProbe().record(motionClass: .gradient)
        let gradientFractions = Self.deltas(gradient)
        emit("MOTION_CONTROL 渐变端点 帧数=\(gradient.count) 峰值=\(String(format: "%.3f", Self.peak(gradientFractions))) 变化帧对=\(Self.transitionFrameCount(gradientFractions))")
        let layoutObservable = Self.peak(fractions) > Self.minimumVisibleChange
        Self.observableCache[.layout] = layoutObservable
        Self.observableCache[.gradient] = Self.peak(gradientFractions) > Self.minimumVisibleChange
        try XCTSkipUnless(layoutObservable,
                          "MOTION_NOT_RUN=runner-cannot-observe-layout-motion：每 50ms 换文字 + 平移方块都量不到 ⇒ 这把尺在这台机器上看不见 @State 驱动的位移")
        XCTAssertGreaterThan(Self.transitionFrameCount(fractions), Self.minimumTransitionFrames,
                             "看得见变化但只分摊到一帧 ⇒ 这个视图的时钟没在跑，`requireObservableMotion` 会跟着失效")
    }

    // MARK: - 场景

    private struct Scenario {
        let name: String
        let size: NSSize
        /// 这个场景**声明**的过渡时长（ms），来自 `MotionCatalog.duration(for:)`。
        /// 0 = 这场景没有该动的东西（空白对照、换选同类型、列表行——后者是"确认动不了"的那族）。
        ///
        /// 判据要用"声明时长 ÷ 事件那一段的采样"来决定这次到底能不能分辨过程，
        /// 所以场景必须自带声明时长；写死在判据里的数字（"≥3 帧""第 3 帧之后"）
        /// 量的其实是抓帧耗时（见 `judgeMotion` 的推导注释）。
        let declaredDurationMilliseconds: Double
        /// 触发一次状态变更。`HistoryStore` 是 `@MainActor` 的，所以闭包也得是。
        let trigger: @MainActor (HistoryStore) -> Void
        /// 开窗**之前**先把界面摆到起点（比如"现在选中的是一条文本记录"）。
        /// 没有这一步就没法测"换类型才演"——因为夹具建完时的选中态是它自己决定的。
        let prepare: (@MainActor (HistoryStore) -> Void)?
        /// 这个场景要拍的**根视图**。`nil` = 主窗口 `ContentView`。
        ///
        /// R11 加这一层，是为了让"设置页里的东西"也能被真窗口驱动。
        /// 关键约束：根视图必须是**产品自己的**那个（`DailyCopyStatsSection` 为此从
        /// `private` 放开到 internal）—— 探针一旦自带一份"长得像"的宿主视图，
        /// 它测的就是替身而不是产品，那一族在仓库里记过（第二轮 N-1 的守卫绕开 adapter）。
        let root: (@MainActor (HistoryStore) -> AnyView)?
        /// 换一份 store。`nil` = `makeStore()`（15 条记录、**没有**按日账本）。
        let storeFactory: (@MainActor () -> HistoryStore)?
        /// 只抓这一块区域（R57 / BACKLOG 77 路 a）。`nil` = 整个视图。
        ///
        /// 为什么要有这一层：R55 量到"事件段内最粗 Nms"里 ~91% 是抓帧器自己的像素成本，
        /// 而 R55 的面积判据又量出成本随面积**子线性**走（端到端 12.3–13.0 倍 / 面积 29.8 倍）。
        /// ⇒ 把捕获区域收到被测元素那一条带上，是唯一一条**今天就能做**的降采样成本的路。
        /// 代价不是零：视野变小之后，"变化的比例"会变大（分母小了），
        /// 所以用它必须同时被 `testBandCaptureIsCheaperAndStillSeesTheMotion` 钉住
        /// "裁掉的那部分里没有被测的动效"。
        let captureRect: (@MainActor (NSView) -> NSRect)?

        init(name: String, size: NSSize,
             prepare: (@MainActor (HistoryStore) -> Void)? = nil,
             declaredDurationMilliseconds: Double = 0,
             root: (@MainActor (HistoryStore) -> AnyView)? = nil,
             storeFactory: (@MainActor () -> HistoryStore)? = nil,
             captureRect: (@MainActor (NSView) -> NSRect)? = nil,
             _ trigger: @escaping @MainActor (HistoryStore) -> Void) {
            self.name = name
            self.size = size
            self.prepare = prepare
            self.declaredDurationMilliseconds = declaredDurationMilliseconds
            self.root = root
            self.storeFactory = storeFactory
            self.captureRect = captureRect
            self.trigger = trigger
        }

        /// 提示条那一条带（R57）。**顶部 48pt、整宽**。
        ///
        /// 48pt 不是猜的：把那一帧存成 PNG（`/tmp/r57e-motion/diag-band-first.png`，
        /// 用 `/tmp/r57scan/scan.swift` 逐行扫）—— 从画面顶边数起第 0–75 行是横幅那条
        /// （2x ⇒ 38pt）、76–77 行是分隔线、第 78 行起才是搜索框
        /// ⇒ 48pt 装得下横幅还余 10pt，而面积只有整窗的 1/14（96 ÷ 1346）。
        ///
        /// 为什么要写 `isFlipped` 这一层（本轮栽过，值得留在注释里）：
        /// 第一版按 AppKit 的"原点在左下"写成 `y = height - 48`，
        /// 而 `NSHostingView` 是**翻转**的（y=0 在顶上）—— 于是那条带抓到了窗口的**底部**，
        /// 而"带里必须装得下这次变更"那条前提**照样通过**：横幅消失之后下面整块列表在位移，
        /// 位移也是变化。⇒ 拦得住这件事的不是"有没有变化"，而是
        /// `testBandCaptureIsCheaperAndStillSeesTheMotion` 里那对**位置同一性**判据
        /// （带必须逐像素等于整窗的那一头、且不等于另一头）。
        /// 中间那一版在这里写过一条颜色判据（"带里必须有警告粉"），它被实测推翻了：
        /// 横幅那层 `Color.orange.opacity(0.12)` 在预乘缓冲区里 r 只有 31，
        /// 而我写的阈值是 r>60 且 r−g>18 ⇒ 恒红。判一个自己没量过的色号，不叫判据。
        @MainActor static func bannerBand(view: NSView) -> NSRect {
            let height = min(48, view.bounds.height)
            let y = view.isFlipped ? 0 : max(0, view.bounds.height - height)
            return NSRect(x: 0, y: y, width: view.bounds.width, height: height)
        }

        /// 实例方法而不是 `static let`：闭包不是 `Sendable`，静态存储会被 Swift 6 判成共享可变状态。
        /// 只列**该有过渡**的场景。不该有的那些（侧栏行、同类型换字）在
        /// `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 与
        /// `testDetailPreviewCrossfadesOnlyWhenTheKindChanges` 里反向钉着。
        static func all() -> [Scenario] {
            [noticeBanner(), noticeBannerDismiss(), detailKindChange(), emptyState()]
        }

        /// 提示条**撤走**那一臂（R22 / U-44）。
        ///
        /// 为什么单独立一条：`ContentView` 那五张横幅写的是
        /// `asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，
        /// 而 `notice-banner` 那条只触发**插入** —— 于是"移除那一臂到底在不在演"
        /// 四轮以来没有任何读数。这正是 R16 记过的那一族：
        /// **只有一臂在演的过渡等于没有过渡**，而上一次发现它靠的是人眼。
        ///
        /// `prepare` 把横幅摆成"已经在"，`trigger` 才是要判的那一下 ——
        /// 没有 prepare 的话起点就是空态，量到的会是"从没出现过"而不是"消失了"。
        static func noticeBannerDismiss() -> Scenario {
            Scenario(name: "notice-banner-dismiss", size: NSSize(width: 760, height: 560),
                     prepare: { store in
                         store.reportPasteFailure("系统未授权本 App 控制「System Events」，无法自动粘贴。")
                     },
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .bannerOut) * 1000,
                     // R57：整窗那一臂抓一帧 39.5–39.8ms（R55 的归因：抓帧解释了 91% 的间隔），
                     // 而这条过渡声明只有 120ms ⇒ 判不了。收到顶部那条带之后实测
                     // 4.4–4.6ms 一帧、过渡帧数 10–11（`.scratch/motion-audit-2/r57_motion_readings.log`），
                     // 登记表里这一臂已经改回 must_judge=true。
                     captureRect: Scenario.bannerBand) { store in
                store.dismissPasteFailure()
            }
        }

        // `heatFirstRecord()` **不在这里** —— 它量到的是"一帧到位"，而关掉动画之后读数不变，
        // 也就是说这把尺看不见这条淡入（见 `testHeatmapFadeIsNotVisibleToThisRuler`）。
        // 把它放进 `all()` 等于让一条"量不到的东西"每天判产品一次红。

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
            Scenario(name: "notice-banner", size: NSSize(width: 760, height: 560),
                     // 横幅插入走 .bannerIn（`ContentView.swift` 那句
                     // `.animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)`）。
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .bannerIn) * 1000,
                     // R57：整窗 1520×1346px 抓一帧实测 39.5–39.8ms（R55 也在 38.7–49.7 这个量级），
                     // 而这条过渡声明只有 150ms ⇒ 采样粗细是被捕获面积决定的，不是产品。
                     // 收到顶部那一条带（1520×96px，面积 1/14）之后同一卷 4.4–4.6ms、
                     // 过渡帧数 10–13（`testBandCaptureIsCheaperAndStillSeesTheMotion` 当场对账，
                     // `testBandCaptureIsWiredIntoBothBannerArms` 钉住"这一臂确实用了带"）。
                     captureRect: Scenario.bannerBand) { store in
                store.reportPasteFailure("系统未授权本 App 控制「System Events」，无法自动粘贴。")
            }
        }

        /// 空账本 → 第一条复制：整块日历该淡进来（R9 给两臂补的过渡 + `counts.isEmpty` 驱动）。
        ///
        /// 为什么是这一条而不是另外两条：R9 一共加了三条动画，
        /// ① 悬停描边要真鼠标悬停（合成事件期间 `NSApp.currentEvent` 是 nil，那一族记过），
        /// ② 单格加深只动 11pt ≈ 全帧的 0.1%，低于 `minimumVisibleChange`(0.005) ⇒ 尺子看不见，
        /// ③ 只有"空↔网格"换掉的是约三成画面。
        /// 所以这一条是**能证的**，另外两条继续只由结构判据看着 —— 别把它算成"三条都验过了"。
        static func heatFirstRecord() -> Scenario {
            Scenario(name: "heat-first-record", size: NSSize(width: 430, height: 250),
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .contentFade) * 1000,
                     root: { store in
                         // 没有账本时画一个空视图：那会让前提检查报 `premise-not-visible`，
                         // 也就是**如实报没测到**，而不是拿一张空白窗口冒充"这里没有过渡"。
                         let section: AnyView = store.dailyCopyLedger
                             .map { AnyView(DailyCopyStatsSection(ledger: $0)) } ?? AnyView(EmptyView())
                         return AnyView(
                             section
                                 .padding(16)
                                 .frame(width: 430, height: 250, alignment: .topLeading)
                                 .background(Color(nsColor: .windowBackgroundColor))
                         )
                     },
                     storeFactory: {
                         let url = heatLedgerURL()
                         // 上一次的残留会让账本**开局就有内容** ⇒ 空↔网格这次根本没有可演的变化，
                         // 于是这条判据会静默变成"什么都没测"。先删干净，让起点真的是空。
                         try? FileManager.default.removeItem(at: url)
                         return HistoryStore(
                             clipboardWriter: TestClipboardWriter(),
                             // `load()` 返回 [] ⇒ 构造期的回填不会把账本填满（它只在有存档时间戳时才动）
                             persistence: RecordingHistoryPersistence(),
                             dailyCopyLedger: DailyCopyLedger(fileURL: url))
                     }) { store in
                store.add(ClipboardIntake.Entry(
                    content: .text("动效取证：让热图从空态长出来的那一条 \(UUID().uuidString.prefix(6))"),
                    thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                    sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                    timestamp: Date())
            }
        }

        private static func heatLedgerURL() -> URL {
            URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent("heat-filmstrip-\(ProcessInfo.processInfo.processIdentifier).json")
        }

        /// 文本 → 图片：整块预览被换掉，该有一次软交接。
        static func detailKindChange() -> Scenario {
            Scenario(name: "detail-kind-change", size: NSSize(width: 760, height: 560),
                     prepare: { store in store.perform(.selectOnly(plainTextEntries(store).first!)) },
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .contentFade) * 1000) { store in
                store.perform(.selectOnly(imageEntries(store).first!))
            }
        }

        /// 文本 → 文本：只换字，不该演。
        /// 详情区"空 ↔ 内容"整块换人（R16）。
        ///
        /// 为什么单独一条：`detail-kind-change` 量的是**内容臂内部**预览换类型那一层；
        /// 这一条量的是 `selectedEntry == nil` 那个布尔翻面 —— 那一层以前只有空臂挂了过渡，
        /// 内容臂是一帧硬切（于是删掉最后一条时整块空白约 160ms）。
        /// 判据与 `detailKindChange` 同一形状：**过渡中点**取残差，不在落定之后取。
        static func detailEmptyToContent() -> Scenario {
            Scenario(name: "detail-empty-to-content", size: NSSize(width: 760, height: 560),
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .contentFade) * 1000,
                     storeFactory: { Scenario.makeEmptyStore() }) { store in
                store.add(ClipboardIntake.Entry(
                    content: .text("动效取证：详情区从空态换成一条真记录 \"\(UUID().uuidString.prefix(6))\""),
                    thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                    sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                    timestamp: Date())
                guard let first = store.entries.first else { return }
                store.perform(.selectOnly(first))
            }
        }

        /// 一条记录都没有的 store ⇒ `selectedEntry == nil` ⇒ 详情区是空态。
        /// 不复用 `makeStore()` 再删：删到最后那条走的是另一条代码路径，
        /// 那会把"删除"这件事混进这条只管"空 ↔ 内容"的场景里。
        @MainActor static func makeEmptyStore() -> HistoryStore {
            HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
            )
        }

        static func detailSameKind() -> Scenario {
            Scenario(name: "detail-same-kind", size: NSSize(width: 760, height: 560),
                     prepare: { store in store.perform(.selectOnly(plainTextEntries(store).first!)) }) { store in
                let texts = plainTextEntries(store)
                store.perform(.selectOnly(texts.count > 1 ? texts[1] : texts[0]))
            }
        }

        /// 清空 → 空态：整块列表被"没有记录"换掉。
        static func emptyState() -> Scenario {
            Scenario(name: "empty-state", size: NSSize(width: 380, height: 520),
                     // 侧栏的空态 ↔ 列表那一层 `.transition` 声明在 `.contentFade` 上
                     // （`HistorySidebarView.swift` 里 EmptyStateView 那一段）。
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .contentFade) * 1000) { store in
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
        /// 触发那一刻落在第几帧。
        ///
        /// 以前判据写的是"第 3 帧之后"，而**触发并不在第 0 帧**：前面还有三帧预卷，
        /// 预卷的长度取决于抓一帧要多久（抓帧是同步 `cacheDisplay`，大窗口更慢）。
        /// 于是同一句"第 3 帧"在不同负载下指的是不同的时刻 —— 这就是三臂交替跑出三套红集合的根因
        /// （BACKLOG 第 6 条 / D-058）。所有时间判据从这个锚点起算。
        let triggerFrame: Int

        /// 触发前最后一帧开始的片段：`motionDeltas[0]` 就是"触发那一下"的变化。
        var motionFrames: [CGImage] {
            Array(frames[min(max(triggerFrame - 1, 0), max(frames.count - 1, 0))...])
        }

        var motionStamps: [TimeInterval] {
            Array(stamps[min(max(triggerFrame - 1, 0), max(stamps.count - 1, 0))...])
        }

        /// 触发那一刻采样是否已经热到能看过程。`false` ⇒ 这一卷只能报 not-run，
        /// **不许**判产品"没有过渡"（R11 就是被这条救回来的：见 `recordFrames` 里那段实测）。
        /// 带默认值的存储属性（不是计算属性）：`record()` 的其它调用点不传它，
        /// 而那些场景不经过新的预卷循环时也不该被这条新闸门误伤。
        var clockIsWarm: Bool = true

        /// 这一卷抓帧成本的**中位数**（ms）。−1 = 没量。
        ///
        /// 为什么与 `worst` 一起带出来（R57）：A/B 比的是"整条带的常态成本 vs 整窗的常态成本"，
        /// 只看最慢那一次会被冷首帧主导（`heat-first-record` 就是中位 1.5ms / 最慢 255ms）。
        var medianGrabMilliseconds: Double = -1

        /// 这一卷里**最慢的一次抓帧**花了多少毫秒（`cacheDisplay` 那一段）。
        ///
        /// 默认 −1 = "没量"（不是"抓帧不花钱"）：那些不经过 `recordFrames` 的夹具构造点
        /// 会拿到 −1，而 `grabAttribution` 对 −1 给的是 `unknown`，不是"归因于抓帧器"。
        var worstGrabMilliseconds: Double = -1
    }

    // MARK: - 抓帧成本归因（R55 / BACKLOG 77）

    /// "这一段为什么分辨不了"的**归因**：那 N 毫秒里有多少是抓帧器自己的像素成本。
    ///
    /// 为什么需要它：`clock-coarse-in-window` 从 R2 起就在报"最粗 Nms 一帧"，
    /// 但 N 从来是一个**混合量** —— 里面既有 `cacheDisplay` 的像素成本，也有
    /// runloop 没醒的时间与产品自己被强制同步布局的那一段。三种归因的修法完全不同：
    /// 像素成本 ⇒ 缩捕获区域/降尺度真能把采样变细；runloop 没醒 ⇒ 那样做白费；
    /// 强制布局 ⇒ 那是产品成本，缩区域只把它挪进另一个调用里。
    ///
    /// 本机 2026-10-14 那一次 `CLIPBOARD_HISTORY_UI_MOTION=1` 的真读数（`/tmp/r55_motion_local.log`）
    /// 就是这一族必须分三档的原因：`notice-banner-dismiss` 的事件段最粗 **97ms**，
    /// 而同卷抓帧最慢一次是 **87.9ms**。第一版这里只有两档（余量 8ms），它把这一条报成了
    /// `not-the-grab ⇒ 先别动捕获尺寸` —— **建议是错的**：抓帧解释了这个间隔的 91%，
    /// 缩区域正是主杠杆，那 9ms 只是没解释完的零头。两档的判法把"主要归因"和"完全归因"混成了一件。
    /// 现在拆成三档，并把**解释比例**本身打进日志，让人能复核而不是信我的分档。
    ///
    /// ⚠ "抓帧那一调用里"不等于"探针的开销"：`cacheDisplay` 会强制布局与绘制，
    /// 产品自己那一次冷启动的整块布局（R49 的 260ms 空档）就落在这同一个数里。
    /// 所以 `probeBound` 说的是"这段时间花在抓这一帧的调用里"，
    /// 而"缩区域省不省得下"要由 `testGrabCostScalesWithCapturedArea` 那条面积判据回答。
    enum GrabAttribution: Equatable {
        case unknown                                                   // 没量过，或间隔 ≤ 0（除不出来比例）
        case probeBound(explainedRatio: Double, overshootMilliseconds: Double)     // 间隔≈抓帧+一次等待
        case grabDominates(explainedRatio: Double, overshootMilliseconds: Double)  // 抓帧是大头，但还剩一截别的时间
        case outsideTheGrab(explainedRatio: Double, overshootMilliseconds: Double) // 抓帧只占一小截

        /// 判"间隔能不能被这一次抓帧 + 一次等待解释完"的余量（ms）。
        ///
        /// 由来：驱动抓帧的那个循环每圈最多等 4ms（`recordFrames` 里那句
        /// `RunLoop.main.run(until: +0.004)`），再加一倍当抖动余量 ⇒ 8。
        /// **不许把这条写成 0**：那样任何一次比抓帧略长的间隔都会掉出 `probeBound`，
        /// 而间隔本来就含一次等待。
        static let allowanceMilliseconds: Double = 8

        /// "抓帧算不算大头"的比例线。取 0.5 而不是 0.8：
        /// 这一档只回答"该先看哪里"，不回答"够不够" —— 具体还剩多少 ms 由日志里的数说。
        static let dominatesRatio: Double = 0.5

        static func classify(worstIntervalMilliseconds: Double,
                             worstGrabMilliseconds: Double) -> GrabAttribution {
            guard worstGrabMilliseconds >= 0, worstIntervalMilliseconds > 0 else { return .unknown }
            let explained = worstGrabMilliseconds / worstIntervalMilliseconds
            let overshoot = worstIntervalMilliseconds - worstGrabMilliseconds
            if overshoot <= allowanceMilliseconds {
                return .probeBound(explainedRatio: explained, overshootMilliseconds: overshoot)
            }
            return explained >= dominatesRatio
                ? .grabDominates(explainedRatio: explained, overshootMilliseconds: overshoot)
                : .outsideTheGrab(explainedRatio: explained, overshootMilliseconds: overshoot)
        }
    }

    static func grabAttribution(worstIntervalMilliseconds: Double,
                                worstGrabMilliseconds: Double) -> GrabAttribution {
        GrabAttribution.classify(worstIntervalMilliseconds: worstIntervalMilliseconds,
                                 worstGrabMilliseconds: worstGrabMilliseconds)
    }

    /// 归因怎么说进日志。**令牌必须是英文**（`probe-grab-bound` / `grab-dominates` / `not-the-grab` /
    /// `grab-unmeasured`）：中文短语里的连词与括号会被下游的 grep 切成两半，而这一行是 CI 那一步要读的东西。
    /// 比例也一起打出来：分档是我给的判读，而 `解释=NN%` 是可复核的数。
    static func grabAttributionLabel(worstIntervalMilliseconds: Double,
                                     worstGrabMilliseconds: Double) -> String {
        func percent(_ ratio: Double) -> String { String(format: "%.0f%%", ratio * 100) }
        func ms(_ value: Double) -> String { String(format: "%.0f", value) }
        switch grabAttribution(worstIntervalMilliseconds: worstIntervalMilliseconds,
                               worstGrabMilliseconds: worstGrabMilliseconds) {
        case .unknown:
            return " 归因=grab-unmeasured（这一卷没量抓帧成本，或间隔≤0 ⇒ 不许把间隔赖给抓帧器，也不许说不是它）"
        case .probeBound(let explained, let over):
            return " 归因=probe-grab-bound（解释=\(percent(explained))：这一卷最慢一次抓帧 \(ms(worstGrabMilliseconds))ms，"
                + "而间隔 \(ms(worstIntervalMilliseconds))ms 只比它多 \(ms(over))ms ⇒ 差值就是一次等 runloop 的时间）"
                + " ⇒ 采样粗细由抓这一帧的调用决定；缩不省时间要由面积判据回答"
        case .grabDominates(let explained, let over):
            return " 归因=grab-dominates（解释=\(percent(explained))：抓帧 \(ms(worstGrabMilliseconds))ms 是大头，"
                + "但还有 \(ms(over))ms 不是它） ⇒ 缩捕获区域是主杠杆，"
                + "而剩下的 \(ms(over))ms 得另查（BACKLOG 76 那条分段时间轴）"
        case .outsideTheGrab(let explained, let over):
            return " 归因=not-the-grab（解释=\(percent(explained))：抓帧只 \(ms(worstGrabMilliseconds))ms，"
                + "另有 \(ms(over))ms 与像素无关） ⇒ 先别动捕获尺寸，那是修不到地方的改动"
        }
    }

    /// `fullCapture: true` 强制抓整窗（R57 的 A/B 要用：同一场景、同一进程，
    /// 一条带与整窗各跑一遍）。默认 `false` = 用场景自己声明的捕获区域。
    /// 为什么不是"改场景再跑"：那会让两臂的 store/prepare 也一起变，
    /// 差值就不只属于"捕获区域"这一个变量（本仓库 A/B 的规矩：同一台机器同一段时间，只动一件事）。
    private func record(_ scenario: Scenario, fullCapture: Bool = false) -> Film {
        let store = scenario.storeFactory?() ?? makeStore()
        scenario.prepare?(store)
        return recordFrames(scenario, store: store, fullCapture: fullCapture)
    }

    private func recordFrames(_ scenario: Scenario, store: HistoryStore, fullCapture: Bool = false) -> Film {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: scenario.size.width, height: scenario.size.height),
                              styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: scenario.root?(store) ?? AnyView(ContentView(historyStore: store)))
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))

        // R57 / BACKLOG 77 路 a：只抓被测元素那一条带。`fullCapture` 是 A/B 的另一臂。
        let capture = fullCapture ? nil : scenario.captureRect?(host)
        let grabber = Grabber(view: host, limit: 30, rect: capture)

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
        // **等到时钟热起来再触发**（R11 实测加的这一层）。
        //
        // 新窗口的头两次 `cacheDisplay` 要 260–340ms 一帧（第一次绘制要填字形栅格化
        // 与位图分配的冷缓存）。R11 的 `heat-first-record` 正好撞在这段上：
        // 一次 160ms 的淡入只被拍到两个样本 —— 中间那一格变化量 0.027，
        // 刚好落在"峰值 0.220 的 15%"这块地板（0.033）之下，于是被判成
        // "6ms 一帧跳变"。**产品是对的，尺子的采样相位把它读错了。**
        // 这不是把门槛调松（一个数字都没动），是把触发时机挪到尺子能看见过程的地方。
        // 等不到就报 `clock-not-warm`：环境测不了 ≠ 产品没动。
        // 预卷最多 6 帧：抓帧预算只有 30 帧，全花在预卷上就没有"过程"可看了。
        while grabber.ticks < 6, Date() < prerollDeadline.addingTimeInterval(1.2) {
            let previous = grabber.stamps.last
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
            guard grabber.ticks >= 3, let previous, let now = grabber.stamps.last else { continue }
            if (now - previous) * 1000 <= Self.warmIntervalMilliseconds { break }
        }
        let clockIsWarm: Bool = {
            guard grabber.stamps.count >= 2 else { return false }
            let last = grabber.stamps.count - 1
            return (grabber.stamps[last] - grabber.stamps[last - 1]) * 1000 <= Self.warmIntervalMilliseconds
        }()
        scenario.trigger(store)
        let triggerFrame = grabber.frames.count
        let deadline = Date().addingTimeInterval(3.0)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        // R55 / BACKLOG 77：把"这一卷为什么分辨不了"拆成两半 ——
        // **抓帧器自己的像素成本**（`cacheDisplay` 那一段）与 **runloop 没醒的时间**。
        // 不拆的后果不是难看，是修错东西：若 N 全是抓帧成本，该做的是缩小捕获区域或按 1× 拍；
        // 若 N 是 runloop 没醒，那两条都白做（而 `clock-coarse-in-window` 只会一遍遍报"N 太大"）。
        // 这一行是**证据**，不是判据：它不决定红绿，决定的是 BACKLOG 77 那三条候选路该走哪条。
        let pixels = grabber.frames.first.map { "\($0.width)×\($0.height)px" } ?? "无帧"
        emit(String(format: "MOTION_GRAB %@ 帧数=%d 抓帧中位=%.1fms 抓帧最慢=%.1fms "
                     + "视图=%.0f×%.0fpt 像素=%@ 声明=%dms",
                     scenario.name, grabber.frames.count, grabber.medianGrabMilliseconds,
                     grabber.worstGrabMilliseconds, host.bounds.width, host.bounds.height, pixels,
                     Int(scenario.declaredDurationMilliseconds)))
        return Film(frames: grabber.frames, stamps: grabber.stamps,
                    triggerFrame: triggerFrame, clockIsWarm: clockIsWarm,
                    medianGrabMilliseconds: grabber.medianGrabMilliseconds,
                    worstGrabMilliseconds: grabber.worstGrabMilliseconds)
    }

    /// "这一格采样热到能看过程"的上界（ms）。
    ///
    /// 取 120 而不是 50：本机热起来之后是 6–20ms，CI runner 事件内实测 55–62ms（R8b），
    /// 设太紧会把 CI 整卷判成 not-run —— 那不是更准，是少一批读数。
    /// 判据本身要求的是 `s ≤ 0.3d = 48ms` 才走细档，热不上但没热透的仍然会走中间档，
    /// 所以这一层只挡"冷缓存那两三次"，不改变任何一档的门槛。
    static let warmIntervalMilliseconds: Double = 120

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

    /// 带那一臂的一帧与整窗那一臂的同一帧，**逐行**比两个数：
    /// 带的第 0…h 行 vs 整窗的**头** h 行、vs 整窗的**尾** h 行。
    ///
    /// 为什么不用 `changedFraction(band:)`：本轮实测发现那个归一化矩形是**上下颠倒**的
    /// （`yStart = (1 - maxY) * h` 把"顶部一条"取成了"底部一条"），
    /// 拿它当位置判据会把带量到窗口另一头去（实测：顶部带首尾差 0.884，那个函数算出来的"顶部"只有 0.071）。
    /// 这条登记在 BACKLOG 80，修它要重算所有用过 `band:` 的旧结论，不在本轮范围内。
    /// 这里只用**同一份缓冲区**直接比行，不经过那个映射，所以它不依赖任何朝向假设。
    static func bandHeadTailDiff(_ band: CGImage?, _ full: CGImage?) -> (head: Double, tail: Double) {
        guard let band, let full else { return (-1, -1) }
        let a = raster(band), b = raster(full)
        guard a.width == b.width, a.height > 0, b.height > a.height,
              a.pixels.count == a.width * a.height * 4, b.pixels.count == b.width * b.height * 4 else {
            return (-1, -1)
        }
        func diff(from offset: Int) -> Double {
            var changed = 0, sampled = 0
            var y = 0
            while y < a.height {
                var x = 0
                while x < a.width {
                    let p = (y * a.width + x) * 4
                    let q = ((y + offset) * b.width + x) * 4
                    let d = max(abs(Int(a.pixels[p]) - Int(b.pixels[q])),
                                max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[q + 1])),
                                    abs(Int(a.pixels[p + 2]) - Int(b.pixels[q + 2]))))
                    if d > 8 { changed += 1 }
                    sampled += 1
                    x += 7
                }
                y += 7
            }
            return Double(changed) / Double(max(sampled, 1))
        }
        return (diff(from: 0), diff(from: b.height - a.height))
    }

    /// 合成一对位图：`a` 全黑，`b` 只在指定行/列带里是亮的（200,200,200）。
    /// 两条测试共用（R58 的方向真值表、R60 的网格行序），所以它必须是**静态**的：
    /// 各自复制一份，就会有一份跟着实现变旧。
    private static func syntheticPair(width: Int, height: Int,
                                      differingRows: Range<Int>? = nil,
                                      differingColumns: Range<Int>? = nil) -> (Bitmap, Bitmap) {
        let a = [UInt8](repeating: 0, count: width * height * 4)
        var b = [UInt8](repeating: 0, count: width * height * 4)
        for y in 0..<height {
            for x in 0..<width {
                let inRows = differingRows.map { $0.contains(y) } ?? true
                let inCols = differingColumns.map { $0.contains(x) } ?? true
                guard inRows && inCols else { continue }
                let p = (y * width + x) * 4
                b[p] = 200; b[p + 1] = 200; b[p + 2] = 200; b[p + 3] = 255
            }
        }
        return (Bitmap(pixels: a, width: width, height: height),
                Bitmap(pixels: b, width: width, height: height))
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
    ///
    /// 这一行 R58 修过一次，修的是**方向**：原来写的是
    /// `yStart=(1-maxY)*h, yEnd=(1-minY)*h`，注释理由是"CGBitmapContext 的缓冲区第 0 行是底边"。
    /// 那个理由**是错的**（R57 实测）：带那一帧与整窗那一帧的第 0–95 行逐像素相同（0.000）、
    /// 与末尾 96 行差 0.954 ⇒ 这条通道里缓冲区第 0 行就是**画面顶边**，
    /// 于是旧映射把"顶部一条"取成了"底部一条"，7 处调用量了五轮镜像位置（BACKLOG 80）。
    /// 现在由 `testBandRectMapsToTheEndItClaims` 用合成位图把四个方向钉住 ——
    /// 光改映射不够：那个函数在**关于中线对称**的矩形上永远看不出问题，
    /// 而那正是旧代码里两条调用点（详情区、列表中部）的形状。
    /// `band = nil` 就是整窗。
    private static func changedFraction(_ a: Bitmap, _ b: Bitmap, band: CGRect?) -> Double {
        guard !a.pixels.isEmpty, a.pixels.count == b.pixels.count, a.width == b.width, a.height == b.height,
              a.width > 0, a.height > 0 else { return 0 }
        let xStart, xEnd, yStart, yEnd: Int
        if let band {
            xStart = max(0, Int(band.minX * CGFloat(a.width)))
            xEnd = min(a.width, Int(band.maxX * CGFloat(a.width)))
            yStart = max(0, Int(band.minY * CGFloat(a.height)))
            yEnd = min(a.height, Int(band.maxY * CGFloat(a.height)))
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

    /// 竖着堆**原始像素尺寸**的几帧（R59）。给带捕获那一卷用。
    ///
    /// 为什么另写一个而不是复用 `writeStrip`：那个按 `width/2` 画，是为了把整窗（1520×1346px）
    /// 压成能一眼扫完的六列。可带捕获那一卷本来就只有 96px 高 —— 再除二是 48px，
    /// 而横幅那条只有 76px：**要看的中间态被缩到看不清**，"每轮都要真实看图"就变成看色块。
    /// 所以带卷用原始尺寸竖排（1520×96 一帧，十帧 1520×960，仍然能看）。
    @discardableResult
    private func writeStack(_ name: String, _ frames: [CGImage]) -> URL? {
        guard let first = frames.first, frames.count > 1 else { return nil }
        let fw = first.width, fh = first.height
        let gap = Self.stackGap
        let canvas = CGRect(x: 0, y: 0, width: CGFloat(fw),
                            height: CGFloat((fh + gap) * frames.count))
        guard let space = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(data: nil, width: Int(canvas.width), height: Int(canvas.height),
                                      bitsPerComponent: 8, bytesPerRow: 0, space: space,
                                      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
        context.setFillColor(CGColor(red: 0.05, green: 0.05, blue: 0.06, alpha: 1))
        context.fill(canvas)
        for (index, frame) in frames.enumerated() {
            // 第 0 帧画在**最上面**：这条带是窗口顶部，倒过来排会让人以为动画是从下往上长的。
            let rect = CGRect(x: 0, y: canvas.height - CGFloat(index + 1) * CGFloat(fh + gap),
                              width: CGFloat(fw), height: CGFloat(fh))
            context.draw(frame, in: rect)
        }
        guard let out = context.makeImage() else { return nil }
        let url = outDir.appendingPathComponent("\(name)-stack.png")
        guard let data = NSBitmapImageRep(cgImage: out).representation(using: .png, properties: [:]) else { return nil }
        do { try data.write(to: url); return url } catch { return nil }
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
        Self.stripCommentLines(source)
    }

    /// 去掉整行注释。静态：按族扫描的判据本体要用它，而注释里写的例子（比如
    /// `MotionModifiers` 文档里那句 `.transition(.opacity)`）不是声明，算进去就是守卫的假阳性。
    private static func stripCommentLines(_ source: String) -> String {
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
    /// 每一帧**抓帧本身**花了多少毫秒（`cacheDisplay` 那一段，不含等 runloop 的时间）。
    ///
    /// 为什么要有这一列（R55 / BACKLOG 77）：判据一直在报"事件段内最粗 Nms 一帧 ⇒ 今天分辨不了"，
    /// 但 N 里有多少是**抓帧器自己**、有多少是"runloop 这段时间没醒"，从来没被分开过。
    /// 不分开的后果不是难看，是**修错东西**：如果 N 全是 `cacheDisplay` 的像素成本，
    /// 该做的是把捕获区域缩小或按 1× 拍；如果 N 是 runloop 没醒，那做什么都没用了。
    var grabMilliseconds: [Double] = []
    var ticks = 0
    var finished = false
    let limit: Int
    weak var view: NSView?
    /// 只抓这一块（R57 / BACKLOG 77 路 a）。`nil` = 整个视图。
    /// 默认 `nil` 而不是必填：那四处探针（扫光、对照臂…）量的是**整窗**的东西，
    /// 强行给它们一个带等于把它们的视野偷换掉。
    let rect: NSRect?

    init(view: NSView, limit: Int, rect: NSRect? = nil) {
        self.view = view
        self.limit = limit
        self.rect = rect
        super.init()
    }

    func tick() {
        ticks += 1
        let began = DispatchTime.now()
        if let view {
            let target = rect ?? view.bounds
            if let rep = view.bitmapImageRepForCachingDisplay(in: target) {
                view.cacheDisplay(in: target, to: rep)
                if let cg = rep.cgImage {
                    frames.append(cg)
                    stamps.append(ProcessInfo.processInfo.systemUptime)
                }
            }
        }
        grabMilliseconds.append(Double(DispatchTime.now().uptimeNanoseconds - began.uptimeNanoseconds) / 1_000_000)
        if ticks >= limit { finished = true }
    }

    /// 抓帧成本的中位数（ms）。空数组返回 −1：宁可读出"没量"，也不许把 0 当成"抓帧不花钱"。
    /// 走 `MotionFilmstripTests.median`：面积那条判据（`testGrabCostScalesWithCapturedArea`）
    /// 用的是同一个中位数实现，两份各写一遍迟早会算出两个"中位"。
    var medianGrabMilliseconds: Double { MotionFilmstripTests.median(grabMilliseconds) }

    var worstGrabMilliseconds: Double { grabMilliseconds.max() ?? -1 }
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
    /// **抓这一卷的时候，这个进程是不是激活的 App。**
    /// `NSTableView` 的行动画只在激活的 App 里跑：实测同一份代码在
    /// `NSApp.isActive == true` 时读到 11 对在变，`false` 时只有 1 对（总变化量一模一样，
    /// 只是不再分摊到几帧）。而 `swift test` 起的裸进程**能不能拿到激活态是不稳定的**
    /// —— 本机同一天里两种都出现过（CI 那台 runner 拿到过：开 3 帧 / 关 1 帧）。
    /// 所以这条判据必须把前提写进判据本身：拿不到激活态就报 not-run，
    /// 不许把"环境没给到前提"读成"产品没动"。
    private(set) var wasActive = false

    /// R17：把"触发那一下"从插一行换成**移一行**（末行提到最前）。
    /// 复用同一套窗口 / 激活 / 预卷逻辑，只换那一行 —— 两臂共用同一个起点
    /// （`texts` 每次都重置），所以读到的差别只可能来自移动本身。
    /// 这里刻意照抄产品那一套：`moveRow` 没有 `withAnimation:`，
    /// 动不动由 `NSAnimationContext.allowsImplicitAnimation` 决定（见 `QuickPickController`）。
    var appliesMoveInsteadOfInsert = false

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
        NSApp.setActivationPolicy(.regular)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))
        let activateDeadline = Date().addingTimeInterval(1.5)
        while !NSApp.isActive, Date() < activateDeadline {
            NSApp.activate(ignoringOtherApps: true)
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        wasActive = NSApp.isActive
        print("NATIVE_PROBE_STATE visible=\(window.isVisible) key=\(window.isKeyWindow) active=\(NSApp.isActive)")

        let grabber = Grabber(view: scroll, limit: 24)
        let prerollDeadline = Date().addingTimeInterval(0.15)
        while grabber.ticks < 3, Date() < prerollDeadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        // 先改模型、再告诉表格动了哪一行：`insertRows` / `moveRow` 当场就会回读 `numberOfRows` 与新内容。
        if appliesMoveInsteadOfInsert {
            let from = texts.count - 1
            let moved = texts.removeLast()
            texts.insert(moved, at: 0)
            // R50 之前这里还有一行 `texts = texts.map { "\($0)·已挪" }`，
            // 也就是**宣布了一次移动，却把六行的文案都改了**。
            // 那有两个后果：① 两臂的像素差里混进了"文字变了"而不是"位置变了"，
            // 峰值被抬高，而抬高的那部分与动画无关；② 产品那条分支根本不 rename
            // （`QuickPickController.rebuildRows` 的移动分支只 `moveRow`，文案变化走 `plan.reloads`）。
            // 探针与产品的调用序列必须逐行可对照，否则"看不见动画"这个结论
            // 可能只是"探针改了什么别的东西"。位置本身变了 ⇒ 每个下标上的内容就变了，
            // 不需要 rename 也有像素可读。
            NSAnimationContext.runAnimationGroup { context in
                context.allowsImplicitAnimation = !animation.isEmpty
                table.beginUpdates()
                table.moveRow(at: from, to: 0)
                table.endUpdates()
            }
        } else {
            texts.insert("刚插进来的一行：它该淡入而不是把别人挤一下就算完", at: 2)
            table.insertRows(at: IndexSet(integer: 2), withAnimation: animation)
        }
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
        NSApp.setActivationPolicy(.regular)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))
        let activateDeadline = Date().addingTimeInterval(1.5)
        while !NSApp.isActive, Date() < activateDeadline {
            NSApp.activate(ignoringOtherApps: true)
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        wasActive = NSApp.isActive
        print("NATIVE_PROBE_STATE visible=\(window.isVisible) key=\(window.isKeyWindow) active=\(NSApp.isActive)")
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
    func record() -> [CGImage] { record(motionClass: .layout) }

    func record(motionClass: MotionFilmstripTests.MotionClass) -> [CGImage] {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 220),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let root: AnyView = motionClass == .layout
            ? AnyView(TickCounterView())
            : AnyView(GradientTickView())
        let host = NSHostingView(rootView: root)
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

// MARK: - 淡入时钟的夹具与探针（R66 / BACKLOG 100）

/// 白底 + 一块盖满视口的黑，用**插入/移除 + `.transition(.opacity)` + `withAnimation`**
/// 反复淡入淡出 —— 与提示条出现时同一套机制。
///
/// 为什么需要一个测试自己的夹具，而不是直接拿产品横幅当证人（这是本轮的要点）：
/// 产品横幅是**被告**。runner 上它读不出过程（`MOTION_CUT_CONTROL notice-banner … 落定残余=0.025`，
/// run 38696695788 与 38698142859 那两步 `motion suite exit: 1` 就是它），本机读得出（0.974）。
/// 要分清"这台机器今天看不见淡入的过程"和"产品的淡入坏了"，得有一个与被告无关、
/// 而机制相同的证人。
///
/// 时长**写死在测试里**（150ms）而不读 `MotionCatalog`：读产品的话，哪天有人把 `bannerIn`
/// 改成 0.01s，探针跟着一起变短，于是永远"能分辨" —— 证词被被告牵着走。
/// 底色/遮罩用字面 `Color.white`/`Color.black` 而不是 `Color.primary` 一类语义色：
/// 这条尺量的是电平，语义色会跟着系统外观翻面，把"暗黑模式"读成"淡入没做完"。
@MainActor
private struct FadeClockView: View {
    static let declaredDurationMilliseconds: Double = 150
    /// 每次翻转的间隔：比声明时长长，保证两头都有真正的静置帧可以当端点。
    static let period: TimeInterval = 0.25

    @State private var shown = false

    var body: some View {
        ZStack {
            Color.white
            if shown {
                Rectangle()
                    .fill(Color.black)
                    .transition(.opacity)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.white)
        .onReceive(Timer.publish(every: Self.period, on: .main, in: .common).autoconnect()) { _ in
            withAnimation(.easeInOut(duration: Self.declaredDurationMilliseconds / 1000)) {
                shown.toggle()
            }
        }
    }
}

/// 抓一段 `FadeClockView`，逐帧报出平均亮度。
@MainActor
private final class FadeClockProbe {
    struct Run {
        let frames: [CGImage]
        let levels: [Double]
        let samplingMilliseconds: Int
    }

    func record() -> Run {
        _ = NSApplication.shared
        // 窗口 320×180，但**只抓左上角 190×24 那一条**（R68 / BACKLOG 104）。
        //
        // 为什么这件事是这一轮的正事：证人必须采得**不比它作证的判据粗**，否则它那句
        // "我也看不见过程"说的只是它自己的分辨率。上一轮 runner 上的实物是
        // 证人 ≈80ms / 判据 35ms —— 而那 80ms 里几乎全是抓帧成本：
        // 判据抓的是 760×48pt 那条带（36,480pt²），证人抓的是整张 320×180pt（57,600pt²），
        // **比被告还贵 1.6 倍**（R55/R57 那条"面积决定采样粗细"第一次咬到我自己）。
        // 190×24 = 4,560pt² ⇒ 稳定是那条带的 **1/8**，与 backing scale 无关（两边同乘 scale²）：
        // "证人合格"从此不靠运气，而是结构上就采得比判据细。
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 320, height: 180),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: FadeClockView())
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.25))
        let grabber = Grabber(view: host, limit: 400,
                              rect: NSRect(x: 0, y: 0, width: 190, height: 24))
        let deadline = Date().addingTimeInterval(2.0)
        while !grabber.finished, Date() < deadline {
            // 0.02 而不是对照臂那个 0.05：这里要分辨的过程只有 150ms，
            // 每 50ms 抓一次的话，斜坡最多落两帧，"这台机器能不能看见过程"就永远在阈值上抖。
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
            grabber.tick()
        }
        let levels = grabber.frames.map { MotionFilmstripTests.meanLevel($0) }
        return Run(frames: grabber.frames, levels: levels,
                   samplingMilliseconds: MotionFilmstripTests.sampleIntervalMilliseconds(grabber.stamps))
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
