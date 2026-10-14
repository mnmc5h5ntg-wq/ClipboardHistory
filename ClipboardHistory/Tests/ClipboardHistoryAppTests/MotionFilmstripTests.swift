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

    /// 从触发到"落定"要几帧这件事，由 `settledAtFrame(_:band:)` 回答（R2）——
    /// 它返回**帧号**，调用方乘以实测采样间隔得到毫秒，于是判据表达的是时间而不是帧数。
    /// 这里以前是一个"预卷之后还有几帧在动"的计数器：它的两个上限（`>1`、`≤6`）都是帧数，
    /// 而一帧是 31ms 还是 90ms 取决于抓帧耗时，所以同一条判据在两种时钟下一个松一个紧。

    static func peak(_ fractions: [Double]) -> Double { fractions.max() ?? 0 }

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

    // MARK: - 采样率感知（R2：判据表达的是时间，不是帧号）

    /// 这段过渡在这把尺下**最多**能被切成几帧。
    /// 抓帧是同步 `cacheDisplay`，间隔由抓取耗时决定：本机实测在 31–90ms 之间漂，
    /// 而声明的过渡只有 150–160ms —— 所以"过渡帧数 ≥3"这种写法量的其实是抓帧耗时。
    static func resolvableFrames(durationMilliseconds: Double, sampleMilliseconds: Int) -> Int {
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
        print("MOTION_BLANK frames=\(frames.count) 峰值=\(String(format: "%.4f", fractions.max() ?? 0)) 过渡帧数=\(span)")
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
                print("MOTION_NOT_RUN=clock-not-warm \(scenario.name)：触发那一刻采样还是冷的"
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
                print("MOTION_NOT_RUN=premise-not-visible \(scenario.name)：首尾两帧逐像素相同 ⇒ "
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
            print("MOTION \(scenario.name) frames=\(frames.count) "
                + "声明=\(Int(scenario.declaredDurationMilliseconds))ms 整卷中位=\(interval)ms "
                + "事件内最粗=\(worstInRun.map { String(format: "%.0f", $0) } ?? "无")ms "
                + "变化段时长=\(elapsed.map { String(format: "%.0f", $0) } ?? "无")ms 过渡帧数=\(span) "
                + "时刻ms=[\(gaps.map(String.init).joined(separator: " "))] "
                + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
            writeStrip(scenario.name, frames)
            guard let elapsed, let worstInRun else {
                notRun.append(scenario.name)
                print("MOTION_NOT_RUN=no-changed-run \(scenario.name)：读不出「变化段」的时长 ⇒ 既不判红也不判绿")
                continue
            }
            switch Self.judgeMotion(elapsedMilliseconds: elapsed,
                                    worstIntervalMilliseconds: worstInRun,
                                    declaredDurationMilliseconds: scenario.declaredDurationMilliseconds,
                                    changedFrames: span) {
            case .clockTooCoarse:
                notRun.append(scenario.name)
                print("MOTION_NOT_RUN=clock-coarse-in-window \(scenario.name)：事件那一段最粗 \(String(format: "%.0f", worstInRun))ms "
                    + "一帧、整段过渡只有 \(Int(scenario.declaredDurationMilliseconds))ms（门槛 0.3×声明）⇒ "
                    + "这把尺在过渡正在演的那一段切不出「过程」这个概念，既不判红也不判绿")
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
        print("MOTION_SUMMARY " + rows.map { "\($0.name)=\($0.span)" }.joined(separator: " "))
        print("MOTION_RESOLVE_SUMMARY judged=\(judged)/\(rows.count) not-run=\(notRun.isEmpty ? "-" : notRun.joined(separator: ","))")
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
        print("MOTION_HEAT_RUNS 开A [\(runs(onFilmA.motionStamps, onA))] 开B [\(runs(onFilmB.motionStamps, onB))]"
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
        print("MOTION_HEAT_FADE_A/B 预热 时长=\(ms(elapsedWarm))ms 帧数=\(Self.transitionFrameCount(Self.deltas(warmup.motionFrames)))"
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
            print("MOTION_NOT_RUN=fade-channel-duty-cycle heat-first-record："
                + "同一条产品路径连抓两遍，一遍算看得见（\(ms(a))ms）、一遍算看不见（\(ms(b))ms）⇒ "
                + "这条通道的占空比不是 100%，今天既不能说看得见也不能说看不见")
        case .clockTooCoarse(let worstA, let worstB):
            // 这一格**不红**，而且它连"看不见"都不许说：钟在过程中间停过，
            // 时长读数就没有资格参与判定（R48 的靶就是把这一格从"看不见"里分出来）。
            print("MOTION_NOT_RUN=clock-coarse-in-window heat-first-record："
                + "峰值那一段内部最粗的一次采样是 \(ms(worstA)) / \(ms(worstB))ms，"
                + "而这条过渡声明 \(Int(scenario.declaredDurationMilliseconds))ms ⇒ "
                + "今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT）")
        case .visibleToThisRuler:
            XCTFail("两遍都说「还在变」覆盖的时长比对照臂长出一个采样间隔以上 ⇒ 这把尺现在**看得见**这条淡入 ⇒ "
                    + "把 `heatFirstRecord()` 放回 `Scenario.all()` 当真判据，别留这条当免责")
        case .notVisibleToThisRuler:
            print("MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay heat-first-record："
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
    private func region(in code: String, named declaration: String) -> String {
        let lines = code.components(separatedBy: "\n")
        guard let start = lines.firstIndex(where: { $0.contains(declaration) }) else {
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
        print("MOTION_AB \(scenario.name) 曲线关闭 采样≈\(Self.sampleIntervalMilliseconds(film.motionStamps))ms 过渡帧数=\(span) "
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
        print("MOTION_CUT \(scenario.name) 带内过渡帧数=\(Self.transitionFrameCount(fractions)) "
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
            print("MOTION_NOT_RUN=clock-too-coarse control=notice-banner 采样≈\(interval)ms "
                + "声明=\(Int(banner.declaredDurationMilliseconds))ms ⇒ 过渡的一半落在同一帧里")
            throw XCTSkip("MOTION_NOT_RUN=clock-too-coarse：阳性对照无从判定。它一缺席，"
                + "上面那条「行没在动」就没有分辨率证据 ⇒ 报 skip 并说明，不报绿也不报红")
        }
        let fadingResidual = Self.settleResidualRatio(fading.motionFrames, after: mid)
        print("MOTION_CUT_CONTROL notice-banner 采样≈\(interval)ms 中点帧=\(mid) "
            + "落定残余=\(String(format: "%.3f", fadingResidual))")
        XCTAssertGreaterThan(fadingResidual, 0.15,
                             "连横幅淡入都读不出残余 ⇒ 这把尺子在这个维度上没有分辨率，上面那条绿是空的")

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
            print("MOTION_NOT_RUN=clock-too-coarse detail-kind-change 采样≈\(interval)ms "
                + "声明=\(Int(scenario.declaredDurationMilliseconds))ms ⇒ 取不到过渡中点")
            throw XCTSkip("MOTION_NOT_RUN=clock-too-coarse：这一半无从判定，既不判红也不判绿")
        }
        let crossfade = Self.settleResidualRatio(kindChange.motionFrames, after: mid, band: band)
        let kindFractions = Self.deltas(kindChange.motionFrames, band: band)
        print("MOTION_DETAIL kind-change 采样≈\(interval)ms 中点帧=\(mid) "
            + "带内过渡帧数=\(Self.transitionFrameCount(kindFractions)) "
            + "落定残余=\(String(format: "%.3f", crossfade))")
        XCTAssertGreaterThan(crossfade, 0.15,
                             "换类型时详情区一帧到位 ⇒ 那条 `.transition` 没接上线（或又被谁摘掉了）")

        // 否定那一半从触发帧起算：文本→文本"不该演"，越早取越严格（第 1 帧就该是最终态）。
        let sameKind = record(Scenario.detailSameKind())
        let snap = Self.settleResidualRatio(sameKind.motionFrames, after: 1, band: band)
        let sameFractions = Self.deltas(sameKind.motionFrames, band: band)
        print("MOTION_DETAIL same-kind 带内过渡帧数=\(Self.transitionFrameCount(sameFractions)) "
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
        print("MOTION_DETAIL_AB empty-to-content 开 帧数=\(onSpan) 峰值=\(String(format: "%.3f", Self.peak(on)))"
            + " 冷闸=\(onFilm.clockIsWarm)  关 帧数=\(offSpan) 峰值=\(String(format: "%.3f", Self.peak(off)))"
            + " 采样≈\(Self.sampleIntervalMilliseconds(onFilm.motionStamps))ms")
        XCTAssertGreaterThan(Self.peak(on), Self.minimumVisibleChange,
                             "两臂什么都没变 ⇒ 触发没让图长出来，这条 A/B 没有对照物（是探针坏了，不是动效坏了）")
        XCTAssertTrue(onFilm.clockIsWarm && offFilm.clockIsWarm,
                      "有一臂是在冷采样下抓的 ⇒ 两臂相同不能算尺子的极限，这条结论今天不成立")
        if onSpan == offSpan, abs(Self.peak(on) - Self.peak(off)) < 0.02 {
            print("MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content："
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
    func testSlidingRoleSettlesWithinItsBudget() throws {
        try skipUnlessEnabledAndCapable()
        let band = CGRect(x: 0.05, y: 0.02, width: 0.90, height: 0.20)   // 横幅那一条
        let scenario = Scenario.noticeBanner()
        let film = record(scenario)
        let interval = Self.sampleIntervalMilliseconds(film.motionStamps)
        guard Self.premisePictureChanged(film.motionFrames, band: band) else {
            print("MOTION_NOT_RUN=premise-not-visible banner-in 带内触发前后逐像素相同 ⇒ 这次变更在画面里不存在")
            throw XCTSkip("MOTION_NOT_RUN=premise-not-visible：落定态与起始态相同，落定时长无从谈起")
        }
        guard let settled = Self.settledAtFrame(film.motionFrames, band: band) else {
            let steps = Self.deltas(film.motionFrames, band: band)
            print("MOTION_NOT_RUN=no-visible-change banner-in 帧数=\(film.motionFrames.count) 采样≈\(interval)ms "
                + "峰值相邻差=\(String(format: "%.4f", steps.max() ?? -1)) "
                + "带内逐帧相邻差=\(steps.map { String(format: "%.3f", $0) })"
                + " ⇒ 这一带从头到尾没变过（没触发，或者没框到）")
            throw XCTSkip("MOTION_NOT_RUN=no-visible-change：这条判据今天没有对照物")
        }
        let duration = scenario.declaredDurationMilliseconds
        let settledMilliseconds = Double(settled) * Double(max(interval, 1))
        print("MOTION_SETTLE banner-in 到位帧=\(settled) 采样≈\(interval)ms ⇒ 实测落定≈\(Int(settledMilliseconds))ms"
            + "（声明 \(Int(duration))ms）")
        // "有过程"那一半只在时钟切得出至少 3 帧时才判：否则一次正确的过渡本来就会在两帧内到位。
        if Self.resolvableFrames(durationMilliseconds: duration, sampleMilliseconds: interval) >= 3 {
            XCTAssertGreaterThanOrEqual(settled, 2,
                                        "触发后的第 \(settled) 帧就已经是最终态 ⇒ 这条位移档没有过程")
        } else {
            print("MOTION_NOT_RUN=clock-too-coarse settle-process 采样≈\(interval)ms 声明=\(Int(duration))ms"
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
        print("MOTION_NATIVE row-move 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated)))"
            + " 采样≈\(animatedInterval)ms")
        print("MOTION_NATIVE row-move 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant)))"
            + " 采样≈\(instantInterval)ms")
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
        let verdict = Self.nativeMoveVerdict(animatedSpan: animatedSpan, animatedPeak: Self.peak(animated),
                                             instantSpan: instantSpan, instantPeak: Self.peak(instant))
        let verdictLabel: String = {
            switch verdict {
            case .animated: return "动了"
            case .notAnimated: return "瞬移"
            case .samplingMissed: return "采样错过"
            }
        }()
        print("MOTION_NATIVE_MOVE 判定=\(verdictLabel) 峰值容差="
            + String(format: "%.3f", Self.nativeMovePeakTolerance)
            + "（同一卷的 insert 读数在上一行：insert 能看见多帧 ⇒ 通道不瞎）")
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
            print("MOTION_NOT_RUN=native-move-sampling-missed row-move："
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
        print("MOTION_SEQUENCE 选中没变 帧数=\(sameSpan) 峰值=\(String(format: "%.3f", Self.peak(sameRow)))")
        print("MOTION_SEQUENCE 选中变了 帧数=\(movedSpan) 峰值=\(String(format: "%.3f", Self.peak(moved)))")
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
        print("MOTION_SHIMMER 扫 帧数=\(runningFrames.count) 变化帧对=\(Self.transitionFrameCount(running)) 峰值=\(String(format: "%.3f", Self.peak(running))) 采样≈\(interval)ms")
        print("MOTION_SHIMMER 停 变化帧对=\(Self.transitionFrameCount(stopped)) 峰值=\(String(format: "%.3f", Self.peak(stopped)))")
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
        if !wasActive { print("MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画") }
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
            print("MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion 对照臂峰值=\(String(format: "%.4f", Self.peak(control))) 帧数=\(frames.count)")
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
        print("MOTION_CONTROL 计数方块 帧数=\(frames.count) 峰值=\(String(format: "%.3f", Self.peak(fractions))) 变化帧对=\(Self.transitionFrameCount(fractions))")
        let gradient = StateTickProbe().record(motionClass: .gradient)
        let gradientFractions = Self.deltas(gradient)
        print("MOTION_CONTROL 渐变端点 帧数=\(gradient.count) 峰值=\(String(format: "%.3f", Self.peak(gradientFractions))) 变化帧对=\(Self.transitionFrameCount(gradientFractions))")
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

        init(name: String, size: NSSize,
             prepare: (@MainActor (HistoryStore) -> Void)? = nil,
             declaredDurationMilliseconds: Double = 0,
             root: (@MainActor (HistoryStore) -> AnyView)? = nil,
             storeFactory: (@MainActor () -> HistoryStore)? = nil,
             _ trigger: @escaping @MainActor (HistoryStore) -> Void) {
            self.name = name
            self.size = size
            self.prepare = prepare
            self.declaredDurationMilliseconds = declaredDurationMilliseconds
            self.root = root
            self.storeFactory = storeFactory
            self.trigger = trigger
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
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .bannerOut) * 1000) { store in
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
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .bannerIn) * 1000) { store in
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
    }

    private func record(_ scenario: Scenario) -> Film {
        let store = scenario.storeFactory?() ?? makeStore()
        scenario.prepare?(store)
        return recordFrames(scenario, store: store)
    }

    private func recordFrames(_ scenario: Scenario, store: HistoryStore) -> Film {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: scenario.size.width, height: scenario.size.height),
                              styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: scenario.root?(store) ?? AnyView(ContentView(historyStore: store)))
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
        return Film(frames: grabber.frames, stamps: grabber.stamps,
                    triggerFrame: triggerFrame, clockIsWarm: clockIsWarm)
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
