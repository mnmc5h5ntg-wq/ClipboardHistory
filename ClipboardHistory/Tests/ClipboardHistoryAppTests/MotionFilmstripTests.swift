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
    /// 循环证人（同一种画法 + 同一种时钟，由测试自己驱动）的一卷形状，**每进程一次**。
    /// 与 `fadeClockCache` 同一个理由：同一台机器上每条臂问的是同一句话，问两遍会给出两个答案。
    ///
    /// R82 把它拆成**两颗证人**（`coarse` = 每 50ms 一拍、高对比；`rateMatched` = 与产品同一档
    /// 节拍、同一组对比度），因为这两颗问的是两句不同的话，见 `loopAdjudication` 的注释。
    nonisolated(unsafe) static var loopWitnessCache: [MotionClass: LoopShape] = [:]
    /// 骨架扫光**产品自己那一卷**（R84）。缓存的理由与上面两颗证人同一句话，但这一条更硬：
    /// "亮带在不在跑"（coverage）与"亮带是不是整组一条"（位置）现在读的是**同一卷胶片** ——
    /// 各抓各的话，两句话来自两次不同的采样相位，互相既不能印证也不能互相拆台。
    fileprivate nonisolated(unsafe) static var shimmerFilmCache: GrabbedFilm?
    /// 粗节拍那颗证人用**位置那把尺**读出来的判定（R84）。与上面两颗 `LoopShape` 分开缓存，
    /// 因为它们回答的是两句不同的话（"有没有在变" vs "看不看得见一条亮带在哪儿"）。
    fileprivate nonisolated(unsafe) static var bandWitnessCache: BandReading?

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

    /// 实例侧的同名转发。Swift 不允许实例方法不加限定地调静态成员（编译期就挡），
    /// 而 44 处读数散在两种语境里 —— 与其到处写 `Self.emit`，不如让两条语境共用一个名字。
    private func emit(_ line: String) { Self.emit(line) }

    /// 打一行读数，**并且**把它记进文件通道。所有 `MOTION_*` 行都必须走这里
    /// （`testMotionReadingsUseTheFileChannel` 钉着这条规矩）。
    /// 打一行读数，**并且**把它记进文件通道。所有 `MOTION_*` 行都必须走这里
    /// （`testMotionReadingsUseTheFileChannel` 钉着这条规矩）。
    ///
    /// R302 / BACKLOG 358：这里原来**自己实现**了一遍两条腿（stdout 一条、FileHandle 追加一条，
    /// 再加一颗共享布尔做首次整份重写），和 `CaptureReadings` 里那份是同一件事写了两遍。
    /// 问题不是重复十行代码，是**只有一份被锤过**：R79 / BACKLOG 112 在 CI 日志里抓到过
    /// 「两个线程同时看见没开过 ⇒ 两边都做整份重写 ⇒ 后写的把前一份整卷抹掉」，解法是按 URL 记首次、
    /// 进程内一把锁、**一整行一次 write** —— 这三样当时只长在 `CaptureReadings` 那一侧，
    /// 而这份没锁的版本每天在写 44 条动效读数。现在只剩一层壳：通道语义（含「文件坏了不许把
    /// 判据变红、但必须被看见」）由 `CaptureReadings` 单独负责，本文件也因此能进
    /// 「零裸 stdout」的名册（`UICaptureTests.testCaptureReadingsUseTheFileChannel`）。
    static func emit(_ line: String) {
        CaptureReadings.emit(line, to: readingsURL)
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

    /// **跨臂比"看到几帧过程"必须用同一条绝对线**（R191 / BACKLOG 212）。
    ///
    /// 上面那个的门槛是各自峰值 × `stepFloorRatio` —— 本文件在 R59 就已经为分栏对比写过这条批评
    /// （`sharedMovingFloor` 的注释："两块各自归一化 ⇒ 峰值大的那块被一条更高的绝对线先判停…量的是墨量，不是时间"），
    /// 但 ④ 那条"带 vs 整窗"的跨臂比较一直用的是**各自归一化**的计数。runner 上它 14 跑红 3 次，
    /// 而分布显示翻脸的是整窗那一臂（3 或 4），带那一臂恒 3 —— 也就是说这条判据在比两把不同的尺。
    /// 现在把线交给调用方：同一颗 `sharedMovingFloor` 套在两臂上，比的才是同一个量。
    static func transitionFrameCount(_ fractions: [Double], sharedFloor: Double) -> Int {
        fractions.filter { $0 >= sharedFloor }.count
    }

    /// 这一对臂**能不能**共用一条线 —— 判据是"较小那一臂的峰值是否在这条线之上"（R192 / BACKLOG 216）。
    ///
    /// 为什么需要它：`sharedMovingFloor` 取的是**较大**峰值 × `stepFloorRatio`。两臂幅度相当时这条线
    /// 对两边都公平；幅度差很多时，较小那一臂的峰值整臂低于这条线 ⇒ 它读 **0 帧**，于是"同一条线下两臂相同"
    /// 其实读的是"两臂都落定了" —— 那不是把 A/B 判成相同，是把小臂判成不存在。
    /// 本机实测（`/tmp/r192_base_motion.log`，同一份帧数据两臂对照）给的形状：
    /// row-star `0.268/0.268`、detail-empty-to-content `0.051/0.051`、row-insert `0.043/0.052`
    /// ⇒ 较小臂都在线上，共用线成立；而 `MOTION_SEQUENCE` 两臂 `0.027/0.234` ⇒ 那条线是 0.0351，
    /// 小臂的**峰值**都不够 ⇒ 从 11 帧掉到 0 帧，判据当场红，红的却不是产品。
    /// 这条函数没有新阈值：线本身（`sharedMovingFloor`）就是判据，所以"安不安全"是量出来的，不是拍的。
    static func sharedLineIsSound(_ regions: [[Double]]) -> Bool {
        guard let lo = regions.map({ peak($0) }).min() else { return false }
        return lo >= sharedMovingFloor(regions)
    }

    /// 两把尺（同一条线 / 各自归一化）对同一对臂的**合读法** —— 措辞由数字生成（R192）。
    ///
    /// 为什么单独一个纯函数：212 那一族的原罪是"一把尺的输出被写成产品结论"。这里把两把尺的回答
    /// 并成一句话，就能被合成真值表钉住（见 `testCrossArmRulerAgreementIsATruthTable`），
    /// 而"矛盾"那一格必须**指名**它是矛盾、而不是替其中一把尺背书。
    /// **不覆盖管线**：钉的是尺子的话术；真卷那两条是
    /// `testSystemSymbolEffectsAreOutOfThisRulersReach` 与 `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`。
    static func armAgreementReading(sameUnderShared: Bool, sameUnderPerArm: Bool, sound: Bool) -> String {
        switch (sameUnderShared, sameUnderPerArm) {
        case (true, true):
            return "两把尺都说两臂相同 ⇒ 「源码已接、产物未量」这条免责可以记"
        case (false, false):
            return "两把尺都说两臂有别 ⇒ 这把尺看得见这条动效，本条必须升级成硬判据（不许留免责）"
        case (true, false), (false, true):
            return sound
                ? "两把尺矛盾，而共用线是安全的 ⇒ 差别只在一把尺上出现，先读两臂逐帧形状再动判据"
                : "两把尺矛盾，且共用线**不安全**（较小臂的峰值低于这条线 ⇒ 那一臂读 0 帧）"
                    + "⇒ 这是幅度不对称把小臂判成不存在，不是这条 A/B 真的可见（BACKLOG 217）"
        }
    }

    /// ④ 那条跨臂比较必须用**同一条绝对线**（R191 / BACKLOG 212）—— 扫形状，不跑结果。
    ///
    /// 为什么不能只靠"跑一遍看红"：把线换回各自归一化，在本机**照样绿**（本机带臂峰值天然大，
    /// 两臂 8 ≥ 3 两种口径都成立）；它只在 runner 那种两臂计数接近的形状下才露馅（14 跑红 3 次）。
    /// 所以"退回旧口径"这件事只能由接线扫描钉住，并由变异臂 M709 证明这条钉子有牙。
    /// 扫描前先滤掉本方法自己的行：整文件计数会命中"我正在数的那个串"（R100 那一族自指）。
    func testBandProcessComparisonUsesOneSharedLine() throws {
        let text = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        let scan = text.split(separator: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .filter { !$0.contains("separatedBy:") && !$0.contains("contains(") }
            .joined(separator: "\n")
        let uses = scan.components(separatedBy: "sharedFloor: sharedMoving").count - 1
        XCTAssertEqual(uses, 1,
                       "同一条线应当只在一处被喂给两臂计数（读到 \(uses) 次）⇒ 0 次就是退回各自归一化，多次是重复实现")
        XCTAssertEqual(scan.components(separatedBy: "XCTAssertGreaterThanOrEqual(bandShared, fullShared").count - 1, 1,
                       "同线口径的那条断言必须恰好一处（多了是重复实现，少了是这条比较被摘掉）")
        XCTAssertFalse(scan.contains("XCTAssertGreaterThanOrEqual(max(motionFrames(bandFirst)"),
                     "旧那条『各自归一化的计数跨臂比』又回来了 —— 它在两臂计数接近的机器上会把判据变成掷硬币（BACKLOG 212）")
        XCTAssertTrue(scan.contains("旧口径（各自归一化）带="),
                      "旧口径必须与新口径一起打印，否则换判据口径这件事在日志里没有证人（R146 那一课）")
    }

    /// 一臂的"过程"折算成**这一次运行自己量到的采样间隔的倍数**（R193 / BACKLOG 217）。
    ///
    /// 为什么需要它：三处 AppKit 行 A/B（插行 / 移行 / 插行后紧跟写选中）判的是
    /// `transitionFrameCount ≥ 3` 与 `≤ 1` —— 那是**帧对个数**，它有两个洞：
    /// ① 散着变也算数（第 1、8、20 帧各抖一下 = 3 帧），可"演了一段"要求的是**连续**；
    /// ② 一帧多长由抓帧耗时决定（R2 实测同一份代码本机跑过 2/3/2），所以"3 帧"在 6ms 与 50ms
    ///    的时钟下不是同一个要求。
    /// 217 说这两处欠的是时间轴。这里给的就是那条轴，但**不压毫秒数**：
    /// 单位取本次实测的中位间隔 ⇒ 6ms 的机器与 50ms 的机器用的是同一条线（把毫秒写死会把两档
    /// 用一把尺管住，那是 R74 那一族）。`nil` = 这一臂根本没有连续段（峰值低于绝对地板）⇒ 无从判定。
    static func armProcessInIntervals(stamps: [TimeInterval], fractions: [Double])
        -> (intervals: Double, run: ChangedRun)? {
        guard let run = contiguousChangedRun(stamps: stamps, fractions: fractions) else { return nil }
        let interval = Double(sampleIntervalMilliseconds(stamps))
        guard interval > 0 else { return nil }
        return (run.elapsedMilliseconds / interval, run)
    }

    /// `armProcessInIntervals` 的打印形状 —— 读不到打「无」，不许打空串（R100 那一课：
    /// 形状形容词不许落在缺席读数上，而缺席要有缺席的样子）。
    ///
    /// 帧数与连续段**并排打**，因为本轮的真卷读数就是这两个数对不上：
    /// `row-insert 开 帧数=9 … 过程=1.4个间隔 时长10ms 帧对1` —— 九帧是**散着抖**出来的，
    /// 不是一段一直在演的过程。合读法把这件事说成一句话，免得读日志的人只看见那个 9。
    static func processReading(_ value: (intervals: Double, run: ChangedRun)?, span: Int) -> String {
        guard let v = value else { return "无连续段(整卷峰值低于绝对地板) 帧数=\(span)" }
        return String(format: "%.1f个间隔 时长%.0fms 段内最粗%.0fms 帧对%d 帧数=%d ⇒ %@",
                      v.intervals, v.run.elapsedMilliseconds, v.run.worstIntervalMilliseconds,
                      v.run.endFrame - v.run.startFrame + 1, span,
                      processReadingVerdict(span: span, intervals: v.intervals))
    }

    /// "这一臂到底演了一段，还是只是被数到几帧"（R193 / BACKLOG 217）—— 措辞由两个数生成。
    ///
    /// 2.0 个间隔这个界**不是新阈值**：它就是 `minimumTransitionFrames`(3) 在时间轴上的等价形状
    /// —— 三帧**连续**在演，段长必然是"首帧到第四帧"= 2 个间隔。所以这条只在"帧数够、连续段不够"
    /// 时说话，说的还是原来那条判据自己的要求。
    static func processReadingVerdict(span: Int, intervals: Double) -> String {
        if span < minimumTransitionFrames { return "帧数本来就不够 \(minimumTransitionFrames) ⇒ 这一臂判'没在演'" }
        if intervals < 2.0 { return "散点撑绿：帧数 \(span) 够，但含峰值那段只跨 \(String(format: "%.1f", intervals)) 个间隔 ⇒ 这几帧不是一段过程（217）" }
        return "有一段一直在演的过程（连续段 \(String(format: "%.1f", intervals)) 个间隔）"
    }

    /// 两处"两臂相同吗"的比较必须**两把尺都说相同**（R192 / BACKLOG 216）—— 扫形状，不跑结果。
    ///
    /// 为什么不能只靠"跑一遍看红"：本机两臂峰值实测相等（`0.268/0.268`、`0.051/0.051`），
    /// 旧口径与新口径给同一个数 ⇒ 退回旧口径在这台机器上**照样绿**。它只在两臂幅度不等时露馅，
    /// 而幅度不等正是 runner 那一侧的形状。所以这条只能由接线扫描钉住，由 M712…M716 证明有牙。
    func testCrossArmSamenessComparisonsUseBothRulers() throws {
        let text = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        let stripped = text.split(separator: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        /// 按**方法体**切片读（R100 那一课：整文件 contains 会命中引用它的注释与别的用例）。
        /// 真值表那条也在调 `armAgreementReading`，全文件计数会把"接线"与"措辞用例"缝成一个数；
        /// 而本方法自己的行里就写着那些 needle —— R192 第一版就是这么红的（自指命中）。
        let parts = stripped.split(separator: "\n    func ")
        let thisMethod = "testCrossArmSamenessComparisonsUseBothRulers"
        let code = parts.filter { !$0.hasPrefix(thisMethod) }.joined(separator: "\n    func ")
        func body(_ name: String) -> String {
            parts.first(where: { $0.hasPrefix(name) }).map(String.init) ?? ""
        }
        for method in ["testSystemSymbolEffectsAreOutOfThisRulersReach",
                       "testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind"] {
            let section = body(method)
            XCTAssertFalse(section.isEmpty,
                           "\(method)：找不到这个方法体 ⇒ 它被改名或删掉了；计数判据在空串上恒真是假绿（R140 那一族）")
            // 分母先数：两臂各喂一次线，缺一次就是有一臂退回各自归一化。
            let feeds = section.components(separatedBy: "sharedFloor: shared" + "Line").count - 1
            XCTAssertEqual(feeds, 2,
                           "\(method)：同一条线应当喂给**两臂**各一次（读到 \(feeds) 次）")
            XCTAssertTrue(section.contains("sharedMovingFloor([on, " + "off])"),
                          "\(method)：线必须由两臂一起导出，不是拿一臂的峰值自己乘自己")
            XCTAssertTrue(section.contains("armAgreementReading(sameUnder" + "Shared:"),
                          "\(method)：两把尺的回答必须合成一句合读法打进日志，否则读日志的人只能信一把尺")
            XCTAssertTrue(section.contains(" ⇒ \\(agreement"),
                          "\(method)：合读法要打进那一行的日志里 —— 只算不印，两把尺的关系就只剩在测试代码里，"
                            + "读 runner 的人看不到（R146 那一课）")
            XCTAssertTrue(section.contains("旧口径（各自归一化）" + "开="),
                          "\(method)：旧口径要和新口径一起打印（R146 那一课：换判据口径要有证人）")
        }
        XCTAssertFalse(code.contains("XCTAssertEqual(Self.transitionFrameCount(on), "
                                   + "Self.transitionFrameCount(off)"),
                     "row-star 那条『各自归一化的计数跨臂比』又回来了 —— 它是 212 那一族（BACKLOG 216）")
        XCTAssertFalse(code.contains("if onSpan == offSpan,"),
                       "detail 那条免责分支又只问一把尺了 —— 单把尺说『相同』就记『产物未量』，"
                         + "而那把尺的线是自己峰值决定的（BACKLOG 216）")
        // 承重的是**两条**判据，不是一条读数：只数计数会把"摘掉一条硬断言"放过去。
        XCTAssertEqual(code.components(separatedBy: "XCTAssertTrue(onShared == offShared && onPerArm == offPerArm")
                         .count - 1, 1,
                       "row-star 那条『两把尺都说相同才不红』的硬判据必须恰好一处（0 = 被摘掉或退回单把尺，2 = 重复实现）")
        XCTAssertEqual(code.components(separatedBy: "onSpanShared == offSpanShared").count - 1, 2,
                       "detail 的合读法与免责分支各用一次同一条线的比较（少一次就是有一处只问一把尺）")
    }

    /// `sharedLineIsSound` / `armAgreementReading` 的真值表（R192，合成用例）。
    ///
    /// 为什么要有这一条：216 的原提案是"把同一条线**推广**到剩下的跨臂比较"。我先在真卷上量了一遍，
    /// 结果是反例 —— `MOTION_SEQUENCE` 两臂峰值 0.027 / 0.234，共用线 0.0351 比小臂的峰值还高，
    /// 那一臂从 11 帧掉到 **0 帧**。所以"共用一条线"不是无条件更对：它把幅度小的那一臂判成不存在。
    /// 这条真值表钉的就是这条适用域，免得下一轮把那一族"修"成一条会红的假判据。
    /// **不覆盖管线**：这里的数组是人造的，钉的是尺子的适用域与措辞；
    /// 真卷那两条是 `testSystemSymbolEffectsAreOutOfThisRulersReach` 与
    /// `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`。
    func testCrossArmRulerAgreementIsATruthTable() throws {
        // (a) 反例形状（本机 MOTION_SEQUENCE 实测 0.027 / 0.234）：共用线吃掉了小臂。
        let small: [Double] = [0.000, 0.027, 0.025, 0.023, 0.021, 0.019,
                               0.017, 0.015, 0.013, 0.011, 0.009, 0.007]
        let big: [Double] = [0.000, 0.234, 0.001]
        let line = Self.sharedMovingFloor([small, big])
        XCTAssertEqual(line, 0.234 * Self.stepFloorRatio, accuracy: 1e-12,
                       "共享线必须由**较大**那个峰值导出")
        XCTAssertEqual(Self.transitionFrameCount(small), 11, "旧口径：小臂扛自己的线 ⇒ 11 帧在动")
        XCTAssertEqual(Self.transitionFrameCount(small, sharedFloor: line), 0,
                       "同一条线下小臂读 0 ⇒ 这就是 216 不许推广到幅度不对称那一族的成因")
        XCTAssertFalse(Self.sharedLineIsSound([small, big]),
                       "小臂峰值 0.027 低于线 0.0351 ⇒ 必须判成『共用线不安全』")

        // (b) 安全形状（本机 detail 实测 0.051 / 0.051）：两臂都在线上 ⇒ 共用线可以当主尺。
        let a: [Double] = [0.000, 0.051, 0.020]
        let b: [Double] = [0.000, 0.051, 0.018]
        XCTAssertTrue(Self.sharedLineIsSound([a, b]), "两臂峰值相等 ⇒ 共用线安全")
        XCTAssertEqual(Self.transitionFrameCount(a, sharedFloor: Self.sharedMovingFloor([a, b])),
                       Self.transitionFrameCount(b, sharedFloor: Self.sharedMovingFloor([a, b])),
                       "安全形状下新口径应当给同一个数")

        // (c) 边界：小臂峰值**正好等于**线 ⇒ 算安全（`>=`，不是" strictly 高于"）。
        let edgeLow: [Double] = [0.000, 0.15]
        let edgeHigh: [Double] = [0.000, 1.0]
        XCTAssertTrue(Self.sharedLineIsSound([edgeLow, edgeHigh]),
                      "0.15 == 1.0 × 0.15 ⇒ 这一臂还有最后一帧在线上的边界，判成不安全就是多砍一格")

        // (d) 合读法四格：措辞只能由两把尺的回答生成，矛盾那格不许替任何一把尺背书。
        XCTAssertTrue(Self.armAgreementReading(sameUnderShared: true, sameUnderPerArm: true, sound: true)
                        .contains("两把尺都说两臂相同"))
        XCTAssertTrue(Self.armAgreementReading(sameUnderShared: false, sameUnderPerArm: false, sound: true)
                        .contains("升级成硬判据"))
        let contradictedUnsafe = Self.armAgreementReading(sameUnderShared: false,
                                                          sameUnderPerArm: true, sound: false)
        XCTAssertTrue(contradictedUnsafe.contains("幅度不对称"),
                      "不安全 + 矛盾 ⇒ 必须先说清这是小臂被线吃掉（217），不是产品有差别：\(contradictedUnsafe)")
        XCTAssertFalse(contradictedUnsafe.contains("看得见"),
                       "矛盾那格不许写出『这把尺看得见』——那是拿一把尺的产物当产品结论（212 那一课）")
        XCTAssertTrue(Self.armAgreementReading(sameUnderShared: true, sameUnderPerArm: false, sound: true)
                        .contains("先读两臂逐帧形状"))
    }

    /// `armProcessInIntervals` 的真值表（R193 / BACKLOG 217，合成用例）。
    ///
    /// 这条钉的是 217 的**立论本身**：同样"数到 3 帧在变"，连续演与散着抖在帧数尺上同形，
    /// 在时间轴尺上差三倍。没有这一格，下一轮把三处判据搬到时间轴时就没有人管得住"搬了个寂寞"。
    /// **不覆盖管线**：数组与时刻都是人造的，钉的是尺子；真卷那三处是
    /// `testNativeRowAnimationIsVisibleToTheRuler`、`testNativeRowMoveIsVisibleToTheRuler`、
    /// `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt`。
    func testContiguousProcessDiffersFromScatteredChanges() throws {
        let stamps: [TimeInterval] = [0.000, 0.010, 0.020, 0.030, 0.040, 0.050]
        // (a) 连续演三段：第 1→4 帧一直在变 ⇒ 时长 = stamps[4] − stamps[1] = 30ms = 3 个间隔。
        let contiguous: [Double] = [0.00, 0.30, 0.20, 0.10, 0.00, 0.00]
        // (b) 散着抖三下：变化量之和与峰值形状与 (a) 同量级，但**不连续**。
        let scattered: [Double] = [0.00, 0.30, 0.00, 0.25, 0.00, 0.20]
        XCTAssertEqual(Self.transitionFrameCount(contiguous), Self.transitionFrameCount(scattered),
            "前提：帧数这把尺分不开这两种形状（分得开就不需要 217 了）")
        let a = Self.armProcessInIntervals(stamps: stamps, fractions: contiguous)
        let b = Self.armProcessInIntervals(stamps: stamps, fractions: scattered)
        XCTAssertNotNil(a, "连续段必须读得出来")
        XCTAssertNotNil(b)
        XCTAssertEqual(a?.intervals ?? 0, 3.0, accuracy: 0.01,
                       "连续三帧的过程必须读成 3 个间隔（时长 = 段首到段尾后一帧）")
        XCTAssertEqual(b?.intervals ?? 0, 1.0, accuracy: 0.01,
                       "散着抖 ⇒ 含峰值的那一段只有一帧 ⇒ 1 个间隔，不许把三次抖动加成一个过程")
        XCTAssertGreaterThan((a?.intervals ?? 0) - (b?.intervals ?? 0), 1.5,
                             "时间轴必须把这两种形状分开，分不开就是这颗尺白造了")
        // (c) 段内有空档：时长被停顿撑大 ⇒ `worstIntervalMilliseconds` 必须把这件事报出来。
        let gappedStamps: [TimeInterval] = [0.000, 0.010, 0.011, 0.310, 0.320, 0.330]
        let gapped: [Double] = [0.00, 0.30, 0.20, 0.10, 0.00, 0.00]
        let g = Self.armProcessInIntervals(stamps: gappedStamps, fractions: gapped)
        XCTAssertEqual(g?.intervals ?? 0, 31.0, accuracy: 0.5,
                       "中位间隔 10ms、段内一次 299ms 空档 ⇒ 折算 31 个间隔（310ms ÷ 10ms），这条读数本身就是可疑的形状")
        XCTAssertGreaterThan(g?.run.worstIntervalMilliseconds ?? 0, 250.0,
                             "段内最粗采样必须抓到那次空档（R48 那一课：时长不是被过程撑出来的）")
        // (d) 整卷没动 ⇒ nil，不许读成"0 个间隔 = 一帧到位"。
        XCTAssertNil(Self.armProcessInIntervals(stamps: stamps, fractions: [0, 0.001, 0.001, 0, 0, 0]),
                     "峰值低于绝对地板时不许返回一个数 —— 那会把'没量到'说成'瞬移'")

        // (e) 合读法三态：本轮真卷落在**散点撑绿**那一格（`row-insert 开 帧数=9 / 连续段 1.4 个间隔`）。
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 1.4).contains("散点撑绿"),
                      "帧数够而连续段不够 ⇒ 必须说'散点撑绿'，不许只报那个 9")
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 2.0).contains("一直在演"))
        XCTAssertTrue(Self.processReadingVerdict(span: 2, intervals: 1.0).contains("帧数本来就不够"),
                      "帧数本来就不够那一臂 ⇒ 不许被读成'散点撑绿'（那是另一种病）")
        XCTAssertTrue(Self.processReading(nil, span: 0).contains("无连续段"),
                      "缺席要打「无连续段」并带上帧数，不许打空串（R100）")

        // (e) 合读法三态：本轮真卷落在**散点撑绿**那一格（`row-insert 开 帧数=9 / 连续段 1.4 个间隔`）。
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 1.4).contains("散点撑绿"),
                      "帧数够而连续段不够 ⇒ 必须说'散点撑绿'，不许只报那个 9")
        XCTAssertTrue(Self.processReadingVerdict(span: 9, intervals: 2.0).contains("一直在演"))
        XCTAssertTrue(Self.processReadingVerdict(span: 2, intervals: 1.0).contains("帧数本来就不够"),
                      "帧数本来就不够那一臂 ⇒ 不许被读成'散点撑绿'（那是另一种病）")
        XCTAssertTrue(Self.processReading(nil, span: 0).contains("无连续段"),
                      "缺席要打「无连续段」并带上帧数，不许打空串（R100）")
    }

    /// 三处 AppKit 行 A/B 必须把时间轴打进日志（R193 / BACKLOG 217）—— 扫形状。
    ///
    /// 为什么这一轮只钉"打印"不钉"判定"：那三处在本机 `NATIVE_PROBE_STATE … active=false` ⇒ 判定腿 skip，
    /// 本机拿不到分布（只有读数）。按"单次读数不配给产品签字"（R83/R87 那一族），
    /// 先把两臂的时长与折算倍数送到 runner 上跑一跑，判据换形留到下一轮拿着分布做。
    func testNativeRowAbSitesPrintTheTimeAxis() throws {
        let text = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        let stripped = text.split(separator: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        let parts = stripped.split(separator: "\n    func ")
        let thisMethod = "testNativeRowAbSitesPrintTheTimeAxis"
        let code = parts.filter { !$0.hasPrefix(thisMethod) }.joined(separator: "\n    func ")
        XCTAssertEqual(code.components(separatedBy: "Self.armProcessInIntervals").count - 1, 10,
                       "三处站点各两臂（6 次）+ 真值表那四组形状（4 次）⇒ 恰好 10 次调用（定义行不带 `Self.`，不会被算进来）")
        for method in ["testNativeRowAnimationIsVisibleToTheRuler",
                       "testNativeRowMoveIsVisibleToTheRuler",
                       "testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt"] {
            let section = parts.first(where: { $0.hasPrefix(method) }).map(String.init) ?? ""
            XCTAssertFalse(section.isEmpty, "\(method)：找不到方法体 ⇒ 改名或删掉了，空串上的计数是假绿")
            XCTAssertEqual(section.components(separatedBy: "Self.armProcessInIntervals").count - 1, 2,
                           "\(method)：这一处必须给**两臂**各量一次连续段（读到 \(section.components(separatedBy: "Self.armProcessInIntervals").count - 1) 次）"
                             + " ⇒ 少一次就是有一臂还只看帧数")
            XCTAssertTrue(section.contains("过程="),
                          "\(method)：两臂的连续段时长与折算倍数必须打进日志 —— 不印出来，runner 那一跑就没有读数，"
                            + "下一轮换判据时又变成拿本机单次读数签字")
            // 刀 M723 揭示的洞：`contains("过程=")` 会被**另一臂**那一行喂饱 ——
            // 摘掉开臂的打印，关臂那行还在，判据照样绿。要数次数，次数=出口数（R85 那一课）。
            let printed = section.components(separatedBy: "Self.processReading(").count - 1
            XCTAssertEqual(printed, 2,
                           "\(method)：两臂各要打印一次时间轴（读到 \(printed) 次）⇒ 少一次就是有一臂的读数没送到 runner")
        }
        XCTAssertFalse(code.contains("let sameRow = Self.deltas(probe.recordProductSequence"),
                       "序列那处又用`recordProductSequence`的返回值直接算差分了 ⇒ 拿不到**这一臂自己**的时刻，"
                         + "第二臂的 `lastStamps` 会把第一臂的时间轴顶掉（R91：对照自己也要防量错对象）")
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
    ///
    /// **R82 / BACKLOG 110：`clockIntervalMilliseconds` 现在必须是事件那一段的稳健统计量（P75），
    /// 不再是"最粗那一次"。** 那条线原来站在一个单样本上，于是同一份代码、同一台机器，
    /// 事件内最粗 61ms 与 81ms 的两遍读数会一个判、一个 not-run（线是 0.5×160=80ms），
    /// 而中位数一直是 50–51ms —— **判的是采样相位，不是产品**。
    /// 最粗那一次仍然打出来当读数（一次真实的抓帧停顿就该在那里露头，R48 的 260ms 就是），
    /// 只是不再单独决定判定。
    /// 既不判红也不判绿（把尺子的盲区写成产品缺陷，和写成"已交付"一样是假证据）。
    static func judgeMotion(elapsedMilliseconds: Double,
                           clockIntervalMilliseconds: Double,
                           declaredDurationMilliseconds: Double,
                           changedFrames: Int) -> MotionVerdict {
        guard declaredDurationMilliseconds > 0, clockIntervalMilliseconds > 0 else { return .clockTooCoarse }
        let duration = declaredDurationMilliseconds
        if clockIntervalMilliseconds <= 0.3 * duration {
            return elapsedMilliseconds >= 0.4 * duration ? .transition : .jump
        }
        if clockIntervalMilliseconds <= 0.5 * duration {
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

    /// 事件那一段（第一个还在变的帧 → 最后一个还在变的帧之后一帧）里**每一次采样的间隔**（ms）。
    ///
    /// R82 / BACKLOG 110：这里原来只往外交一个**最大值**，而判据拿它当"这把尺切不切得出过程"。
    /// 一个单样本统计做闸门，就会把一臂在"判到 / 判不到"之间翻脸 —— 本机实测三遍
    /// （`.scratch/motion-audit-2/r78_motion_flip.log`）：`detail-kind-change` 的
    /// 事件内最粗在 **61ms 与 81ms 之间跳**，而那条线是 `0.5×声明 = 80ms` ⇒
    /// 同一份代码、同一台机器，一臂红一臂 not-run，而中位数一直是 50–51ms。
    /// 现在把整段交出去，由调用方取**分位数**；最大值仍然打出来当读数（它是有用的：
    /// 一次真实的停顿会在那里露头），只是不再单独决定判定。
    /// 返回 `[]` = 整段没有可见变化 ⇒ 无从判定。
    static func intervalsInsideChangedRun(stamps: [TimeInterval], fractions: [Double]) -> [Double] {
        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return [] }
        let moving = fractions.indices.filter { fractions[$0] >= peak * stepFloorRatio }
        guard let first = moving.first, let last = moving.last, last + 1 < stamps.count else { return [] }
        var gaps: [Double] = []
        for index in (first + 1)...(last + 1) {
            gaps.append((stamps[index] - stamps[index - 1]) * 1000)
        }
        return gaps
    }

    /// 一段采样间隔的**分位数**（0…1）。取法刻意保守：`index = round(q × (n−1))`，
    /// 样本少于 2 个时返回最大值（那时无所谓分位数，只有一个数）。
    static func percentileMilliseconds(_ gaps: [Double], _ q: Double) -> Double {
        guard !gaps.isEmpty else { return -1 }
        let sorted = gaps.sorted()
        if sorted.count == 1 { return sorted[0] }
        let index = min(sorted.count - 1, max(0, Int((q * Double(sorted.count - 1)).rounded())))
        return sorted[index]
    }

    /// 事件那一段里**最粗的一次采样**（ms）—— 保留成读数，不再当判据的闸门（见上）。
    static func worstIntervalInsideChangedRun(stamps: [TimeInterval], fractions: [Double]) -> Double? {
        let gaps = intervalsInsideChangedRun(stamps: stamps, fractions: fractions)
        return gaps.isEmpty ? nil : gaps.max()
    }

    // MARK: - 常驻循环的形状（R82 / BACKLOG 113）

    /// 一卷"该一直在动"的读数（骨架扫光那一族）。
    ///
    /// 为什么需要它（而不是继续用 `transitionFrameCount ≥ 3`）：那条判据数的是**帧对个数**，
    /// 而个数跟着采样密度走 —— R80 的 CI 上 runner 读到 `变化帧对=2 / 帧数=23 / 采样≈115ms`，
    /// 本机是 `23 / 48 / 53ms`，**峰值两边都是 0.015**。也就是说个数这一列量的是"这台机器
    /// 多久拍一张"，不是"这条循环有没有在跑"。R47 对淡入做过同一件事（把帧数换成时长轴），
    /// 这一条是那次的下半场。
    ///
    /// `coverage` 是**时间**之比，因此与帧数无关：
    /// 从第一个还在变的帧对，到最后一个还在变的帧对，覆盖了整卷时长的几成。
    /// 一条真循环 ⇒ 从头到尾都在变 ⇒ coverage ≈ 1；
    /// 一次跳变（或"时钟整卷只醒了两回"）⇒ coverage ≈ 一个采样 ÷ 整卷 ≈ 4%。
    /// 中间不需要知道一圈多长、也不需要知道多久一拍。
    struct LoopShape: Equatable {
        let pairs: Int
        let changingPairs: Int
        let peak: Double
        let coverage: Double
        let recordedMilliseconds: Double

        var verdict: LoopVerdict {
            if peak < Self.minPeak { return .notMoving }
            return coverage >= Self.minCoverage ? .looping : .oneShot
        }

        /// "这一卷到底拍没拍到东西在动"的绝对地板。**它必须等于 `MotionFilmstripTests.minimumVisibleChange`** ——
        /// 为什么住在结构体里而不是直接引用那条常量：嵌套类型**不继承**外层类的 `@MainActor`
        /// （`FadeClockReading` 的注释记着同一件事），而两个数一旦能各自漂移，
        /// "峰值够高但 coverage 不够"与"峰值不够"这两支就会互相冒名。
        /// 这一条由 `testTheLoopShapeClassifierIsATruthTable` 里的相等断言钉住（不许只写在注释里）。
        static let minPeak: Double = 0.005

        /// "一直在动"的地板。取 0.5 而不是更高：本机实测 coverage 是 **0.98**，
        /// 而一次跳变在 22 帧对上是 **0.05** —— 中间有二十倍的空间，0.5 不在刀尖上。
        /// 它**不许**为了哪台机器过线而移动（R80 对焦点那条轴立的同一条规矩）。
        static let minCoverage = 0.5
    }

    /// 一卷胶片的**前提** —— 与"这一卷里有没有东西在动"完全无关的两件事：
    /// 时刻与帧一对一（`GrabbedFilm` 之后理论上不该再失败，留着是因为它是 U-155 的墓碑），
    /// 以及这卷**真的抓了这么久**。
    ///
    /// 为什么不复用 `LoopShape.recordedMilliseconds`（R82 的第一版就是那么写的，代价是一朵 CI 假红）：
    /// 那个数在 guard 分支里被归零，而 guard 分支恰恰在"整卷什么都没变"的时候走 ——
    /// runner 那一遍产品峰值 0.000 ⇒ `recordedMilliseconds=0` ⇒ "卷长不对"。
    /// **卷长是录像的性质，不是运动的性质**：一条静止 2.5 秒的卷仍然是 2.5 秒。
    /// 挂错对象的后果不是"多一行红"，是把一台机器的"看不见运动"改写成"探针坏了"，
    /// 于是下一轮会有人去查探针（U-139 / U-155 同一族：结论尺的输出不能当它自己的前提）。
    struct FilmPremise: Equatable {
        let paired: Bool
        let spanMilliseconds: Double
    }

    static func filmPremise(frames: Int, stamps: [TimeInterval]) -> FilmPremise {
        let paired = stamps.count == frames && frames > 1
        let span = stamps.count > 1
            ? max(0, ((stamps.last ?? 0) - (stamps.first ?? 0)) * 1000) : 0
        return FilmPremise(paired: paired, spanMilliseconds: span)
    }

    enum LoopVerdict: Equatable {
        /// 整卷没拍到任何可见变化 ⇒ 无从判定（探针或通道的问题，不是产品的）。
        case notMoving
        /// 变化覆盖了整卷的一半以上 ⇒ 它在一直演。
        case looping
        /// 只在少数几个帧对上变过 ⇒ 一次跳变 / 时钟没在跑。
        case oneShot
    }

    /// 处置读的是**两颗证人 × 产品形状**（R82 现场补的那一半）。
    ///
    /// 为什么一颗不够：`GradientTickView` 原来只有一档 —— 每 50ms 一拍、亮带抬到 0.45。
    /// 拿它当唯一证人，`.productRed` 那句就说大了：产品那一档是 **30Hz、抬 0.12**，
    /// "这台机器带得动一个 20Hz 循环"并不蕴含"带得动 30Hz 的这一档"（R68 立的是
    /// **证人必须与判据问同一句话**，这里问的是"这台机器带不带得动产品那一档节拍的常驻循环"）。
    /// 所以：
    /// * `coarse`（20Hz、高对比）只守**最硬的那一支** —— 连这种画法、这种对比度都一拍都拍不到，
    ///   说明尺或通道坏了，谁都不能签字（`witnessDead`，红）。它在 R81 的 CI 上是能跑的：
    ///   `MOTION_CONTROL 渐变端点 帧数=21 峰值=0.029 变化帧对=13`。
    /// * `rateMatched`（30Hz、0.06/0.18，与产品同数字）决定 **产品红 vs 环境不行** 那一分界。
    enum LoopAdjudication: Equatable {
        /// 产品在动 ⇒ 判绿。
        case ok
        /// 与产品**同一档节拍、同一组对比度**的证人在一直动，而产品那份没动 ⇒ **产品红**。
        /// 两颗之间只剩"视图归谁"这一个差别，推给环境没有依据了。
        case productRed
        /// 等节拍证人也没能一直动 ⇒ 这台机器今天带不动产品那一档的常驻循环 ⇒ 点名 not-run，不判产品。
        case notRunEnvironment
        /// 连高对比的粗节拍证人整卷都没拍到任何变化 ⇒ 证人自己坏了，必须红
        /// （否则上面那一支"环境"永远有人签字）。
        case witnessDead
        /// R87：**coverage 这把尺说"没在动"，而位置那把尺在同一份卷子上量到亮带走过了整幅**。
        /// 两者支撑的样本数差一个量级（runner 三遍、同一份产品代码：可用帧 11 / 12 / 12，
        /// 而变化帧对只有 2 / 2 / 1），所以这一格**不许**判产品红，也不许判绿 ——
        /// 它是"这把尺今天吃采样网格"，点名成一条有名字的未覆盖
        /// （`loop-coverage-contradicted-by-travel`）。
        case notRunRulerBlind
    }

    /// 亮带**走过多少 pt** —— 位置那把尺给的、不吃采样网格的运动证据（R87）。
    ///
    /// 为什么需要第三种证据：coverage 数的是"相邻帧对的差有没有跨过台阶"，
    /// 而在一台 ~100ms 采样的机器上，2.5 秒一卷只有 22 对，亮带 30Hz 走完整幅时
    /// **相邻两帧常常长得一样**（要走完一根条才跨一次台阶）⇒ 它的支撑是 1–2 个样本。
    /// 位置尺问的是另一个问题："这一帧亮斑在第几列"，只要一根条上有可用帧就能答，
    /// 于是同一卷上它有 11–12 个样本。三遍 runner 读数：
    /// coverage 0.522 / 0.842 / **0.032**，而行程 109pt / 134pt / **134pt** ——
    /// 前者能在同一份代码上翻 26 倍并把产品判红（run 38811457259），后者说"亮带一路走完了整幅"。
    enum TravelEvidence: Equatable {
        /// 亮带走过 `sweepTravelFloorPoints` ⇒ 它**在动**，这是位置证据。
        case sweeping
        /// 有足够可用帧、但亮带没走过（钉在一处）⇒ 这是"没在动"的位置证据，可以签字判红。
        case notSweeping
        /// 可用帧不够 ⇒ 这一格今天没有读数，不许拿它替谁签字。
        case unreadable
    }

    /// 位置读数 → 行程证据。**只看帧数与行程两个量，不看 `verdict`**：
    /// `.notJudged` 同时盖住"散布分不开"与"没走过"两种情况，
    /// 拿它当"没在动"会把前者误判成后者（R84 真值表里那三格就是为此存在的）。
    static func travelEvidence(_ reading: BandReading) -> TravelEvidence {
        guard reading.framesUsed >= minimumBandFrames else { return .unreadable }
        return reading.travelPoints >= sweepTravelFloorPoints ? .sweeping : .notSweeping
    }

    static func loopAdjudication(product: LoopVerdict,
                                 rateWitness: LoopVerdict,
                                 coarseWitness: LoopVerdict,
                                 travel: TravelEvidence = .unreadable) -> LoopAdjudication {
        if product == .looping { return .ok }
        if coarseWitness == .notMoving { return .witnessDead }
        // R87：先问"有没有一份**样本更多**的尺在说反话"。行程说亮带走完了整幅，
        // 那 coverage 的低读数就是这把尺自己的分辨率问题 —— 判红等于让一把 1–2 样本的尺
        // 去否决一把 11–12 样本的尺（BACKLOG 110 那一族：单样本统计会在判到/判不到之间翻脸）。
        if travel == .sweeping { return .notRunRulerBlind }
        return rateWitness == .looping ? .productRed : .notRunEnvironment
    }

    /// 一列帧对差 + 时刻 → 循环形状。纯函数：合成数据就能钉（`testTheLoopShapeClassifierIsATruthTable`）。
    static func loopShape(fractions: [Double], stamps: [TimeInterval]) -> LoopShape {
        // 先取到局部量再进 guard：`peak` 如果只在 `guard let` 之后绑定，
        // 那 else 分支里写 `peak` 会**命中同名的静态方法** `peak(_:)`（Swift 允许把方法当值传，
        // 于是编译期报的是"参数类型不匹配"，而人看到的是一行没写错的字）—— R82 现场踩的。
        let maximum = fractions.max() ?? 0
        guard maximum > 0, fractions.count > 1, stamps.count == fractions.count + 1 else {
            // 峰值这里**返回 0**，不返回 `maximum`：前提出错（时刻与读数对不上、只有一帧、整卷空白）
            // 时 coverage 是 0，而如果峰值仍然报出真实值，`verdict` 就会把"尺没法算"说成
            // "只动了一下"（`.oneShot`）—— 那是把尺自己的故障冒充成产品的行为，
            // 处置上会从"点名 not-run"错翻成"判产品红"或反之。返回 0 ⇒ `.notMoving` = 没量到。
            return LoopShape(pairs: max(0, fractions.count), changingPairs: 0, peak: 0,
                             coverage: 0, recordedMilliseconds: 0)
        }
        let floor = maximum * stepFloorRatio
        let moving = fractions.indices.filter { fractions[$0] >= floor }
        let first = moving.first ?? 0, last = moving.last ?? 0
        let total = (stamps[fractions.count] - stamps[0]) * 1000
        let covered = total > 0 ? max(0, (stamps[last + 1] - stamps[first]) * 1000) / total : 0
        return LoopShape(pairs: fractions.count, changingPairs: moving.count, peak: maximum,
                         coverage: covered, recordedMilliseconds: total)
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

    // MARK: - R77 / BACKLOG 107：两态相减的尺子必须读四通道

    /// 针脚全部**拼出来**。这条守卫要扫的文件里就包括它自己所在的那个文件：
    /// 把 `+ 2]` 原样写进源码，守卫就会在"定义自己针脚"的那一行上命中自己 ——
    /// 那一族在本仓库栽过两次（R53 的 `region()`、R72 的名单扫描）。
    private static let thirdChannelNeedles = ["+ " + "2]", "green" + "Component", "blue" + "Component"]
    private static let fourthChannelNeedles = ["+ " + "3]", "alpha" + "Component"]
    /// "两态"的判据（R78 换掉了写法）：**签名里收两份位图**，而不是"函数体里出现过某种减法写法"。
    ///
    /// 为什么换：R77 那一版扫的是减法针脚（`) - Int(`、`- pb.`），于是它**漏掉了
    /// `UICaptureHarness.alphaBandDelta`** —— 那把尺先把两态各自约成"每列带内最大 alpha"，
    /// 再写 `abs(maxA - maxB) > floor`，减法长得不一样，但它判的确实是两态。
    /// 名册少一条 = "两态相减必须读两根轴"这句话对那条判据根本不成立（U-138）。
    /// 签名是**形状**，写法是**风格**：风格会为了可读性改写，形状不会。
    private static let bitmapParameterTypes = ["NSBitmapImageRep", "Bitmap", "[UInt8]", "CGImage"]

    /// 参数表里出现两份位图 ⇒ 这是一条两态尺子。
    static func takesTwoBitmaps(header: String) -> Bool {
        guard let open = header.firstIndex(of: "(") else { return false }
        var depth = 0
        var close = header.endIndex
        var cursor = open
        while cursor < header.endIndex {
            let character = header[cursor]
            if character == "(" { depth += 1 }
            else if character == ")" {
                depth -= 1
                if depth == 0 { close = cursor; break }
            }
            cursor = header.index(after: cursor)
        }
        let parameters = String(header[header.index(after: open)..<close])
        // 先数长写法，再把它从串里挖掉，才数短写法 ——
        // 否则 `NSBitmapImageRep` 会被同时数成 "NSBitmapImageRep" **和** "Bitmap"，
        // 一个只收一张图的函数（`meanAlpha(_ rep: NSBitmapImageRep, rect:)`）就冒充两态尺。
        // 这一格是实测撞出来的：第一版这么写，`meanAlpha` 与 `meanLuma` 双双被点成盲区尺。
        let longForm = bitmapParameterTypes[0]
        let longCount = countOccurrences(parameters, longForm)
        let withoutLong = parameters.replacingOccurrences(of: longForm, with: " ")
        var seen = longCount
        for type in bitmapParameterTypes.dropFirst() { seen += countOccurrences(withoutLong, type) }
        return seen >= 2
    }

    /// 数一个短串在长串里出现几次（不重叠计数）。
    static func countOccurrences(_ haystack: String, _ needle: String) -> Int {
        guard !needle.isEmpty else { return 0 }
        var count = 0
        var search = haystack.startIndex
        while let range = haystack.range(of: needle, range: search..<haystack.endIndex) {
            count += 1
            search = range.upperBound
        }
        return count
    }
    /// alpha 这根轴"**参与了判定**"的形状：同一个表达式里既写着它、又拿它跟地板比大小。
    /// 只留一句 `let alphaDelta = abs(...)` 而不拿来判，是**读了不用**。
    /// 这一格不是洁癖：M407 那一刀把 `if delta > 6 || alphaDelta > 6` 里的后半截删掉，
    /// 而 `let alphaDelta` 那行还留着 ⇒ 只查"函数体里有没有出现过 + 3]"的守卫**照样绿**（实测 ESCAPED）。
    /// 判据必须打在"用没用"上，不能打在"有没有"上。
    private static let axisMarker = "alp" + "ha"
    private static let comparisonMarker = " > "

    /// 一把尺子的两根盲区，分开数（方向不同，代价也不同）：
    /// · `luminanceOnly` = 读亮度、做两态减法，可 alpha 那根轴根本没进判定 ⇒ "暗墨在淡"会被读成"没动"（假绿）；
    /// · `alphaOnly`      = 读 alpha、做两态减法，可亮度那根根本没读 ⇒ "颜色在变而不透明"会被读成"没动"
    ///   （R76 那两条 `paintedXRange` / `alphaLiftProfile` 就是这个方向，它们是**故意**的，见豁免名单）。
    /// 返回的名字前缀文件名的 `#`：两个文件各有一份 `rgbFraction`，不许互相顶包。
    static func blindDeltaRulers(named file: String, code: String) -> (luminanceOnly: [String], alphaOnly: [String]) {
        let lines = code.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .map { Self.strippingTrailingComment($0) }
        var luminanceOnly: [String] = []
        var alphaOnly: [String] = []
        var index = 0
        while index < lines.count {
            guard let name = Self.memberFunctionName(lines[index]) else { index += 1; continue }
            // 签名可以折行（`alphaBandDelta` 那一条就是两行）：一路收到出现 `{` 为止，
            // 否则参数表被截在第一行上，"收了两份位图"这条形状判据会对折行的签名失效 ——
            // 而"对折行的签名失效"正是那种永远没人发现的失效：它只在**排版**改变时才坏。
            var headerEnd = index
            var header = lines[index]
            while !header.contains("{"), headerEnd + 1 < lines.count, headerEnd - index < 8 {
                headerEnd += 1
                header += "\n" + lines[headerEnd]
            }
            var body: [String] = []
            var cursor = headerEnd + 1
            while cursor < lines.count, lines[cursor] != "    }" {
                body.append(lines[cursor])
                cursor += 1
            }
            let text = body.joined(separator: "\n")
            let readsThird = thirdChannelNeedles.contains { text.contains($0) }
            let readsFourth = fourthChannelNeedles.contains { text.contains($0) }
            // 两态尺子 = 签名收两份位图 **且** 函数体里真的有一道地板比较。
            // 后一半是拦误伤的：`syntheticPair` 也收两份位图、也碰 `p + 2]`，
            // 但它是**造图的**，不判任何东西 ⇒ 没有阈值（第一版没有这一半，它就被点成了盲区）。
            let hasThreshold = text.contains(" > ") || text.contains(">= ")
            let isTwoState = takesTwoBitmaps(header: header) && hasThreshold
            // alpha 有没有进判定：只看"同一行里既有它、又跟地板比大小"的那几行（注释已经剥掉）。
            // **"用了"而不是"读了"**：同一行里既有那一根轴、又跟别的东西比了大小。
            // **大小写不敏感（R80）**：R80 新写的那把尺里那一行是 `if deltaAlpha > move`
            // —— 轴的名字在驼峰中间，小写needle就看不见它，于是**真读了 alpha 的尺被判成盲区**。
            // 这是 U-138（"检测器认写法不认形状"）的反方向版本：写法不该决定语义。
            // 这一格由正对照 I 钉住（把 `alpha` 换成 `Alpha` 必须仍然算"用了"）。
            let alphaInVerdict = body.contains { $0.lowercased().contains(axisMarker)
                && $0.contains(comparisonMarker) }
            if isTwoState, readsThird, !alphaInVerdict { luminanceOnly.append(file + "#" + name) }
            if isTwoState, readsFourth, !readsThird { alphaOnly.append(file + "#" + name) }
            index = cursor + 1
        }
        return (luminanceOnly, alphaOnly)
    }

    /// 一把尺子被**调用**了几次（声明那一处不算）。
    /// 名册里每一条都必须 ≥1：登记一把没人用的尺子，等于给一条已经不存在的判据发豁免
    /// （R78 实测：`paintedXRange` 零调用点，而 R77 的名册不但收了它，还在理由里替它编了调用者）。
    static func callSites(named ruler: String, in code: String) -> Int {
        let occurrences = countOccurrences(code, ruler + "(")
        let declarations = countOccurrences(code, "func " + ruler + "(")
        return max(0, occurrences - declarations)
    }

    /// 去掉**行尾**注释（`… code // 说明`）。整行注释在上一层已经滤掉，而这一半才是 M407 那一刀钻过去的洞：
    /// 变异行写成 `if delta > 6 { changed += 1 }  // R77 变异：又不读 alpha 了`，
    /// 于是"同一行里既有 alpha 又有 `>`"被**注释**凑齐了 ⇒ 守卫把一把真的瞎掉的尺子判成"两根轴都读"。
    /// 已知偏差：不识别字符串里的 `//`（URL 那样子会被截断），方向是**保守**的 ——
    /// 少读文本只会让一条尺子更容易被判成盲区（多一个红），不会让盲区蒙混过关。
    private static func strippingTrailingComment(_ line: String) -> String {
        guard let slash = line.range(of: "//") else { return line }
        return String(line[line.startIndex..<slash.lowerBound])
    }

    /// 给正对照用的合成尺子。
    ///
    /// 源码里**一个完整针脚都不许出现**：所有通道写法都从 `*ChannelNeedles` 里取，运行时才拼成形状。
    /// 这不是形式 —— 上一版把这些字面量直接写进判据的函数体里，守卫扫自己那份文件时
    /// 就把那条判据自己点成了盲区（M407 之后重写的那一版就是为了这个）。
    static func syntheticRulerSource(readingAlpha: Bool) -> String {
        let third = thirdChannelNeedles[0]
        let fourth = fourthChannelNeedles[0]
        var lines: [String] = [
            "    static func ruler(_ a: Bitmap, _ b: Bitmap) -> Double {",
            "        var changed = 0",
            "        let rgb = abs(Int(a.pixels[p]) - Int(b.pixels[q]))",
            "        let luma = abs(Int(a.pixels[p" + third + ") - Int(b.pixels[q" + third + ")))",
        ]
        if readingAlpha {
            lines.append("        let alpha = abs(Int(a.pixels[p" + fourth + ") - Int(b.pixels[q" + fourth + ")))")
            lines.append("        if rgb > 8 || luma > 8 || alpha > 8 { changed += 1 }")
        } else {
            lines.append("        if rgb > 8 || luma > 8 { changed += 1 }")
        }
        lines.append("        return Double(changed)")
        lines.append("    }")
        return lines.joined(separator: "\n") + "\n"
    }

    /// 认得出"这是一个 4 空格缩进的成员函数头"，并取出函数名。
    /// 更深缩进的（函数里嵌的 `func diff(from:)`）不算新成员 —— 它属于外面那条的函数体，
    /// 否则一条尺子会被拆成两截，针脚扫在错的那一截上。
    private static func memberFunctionName(_ line: String) -> String? {
        guard line.hasPrefix("    ") else { return nil }
        let rest = String(line.dropFirst(4))
        guard rest.contains("func ") else { return nil }
        for prefix in ["func ", "private func ", "static func ", "private static func ",
                       "static private func ", "nonisolated static func ", "final func "] where rest.hasPrefix(prefix) {
            guard let open = rest.firstIndex(of: "(") else { return nil }
            let head = rest[prefix.endIndex..<open]
            return head.isEmpty ? nil : String(head)
        }
        return nil
    }

    /// 今天**允许**只读一根轴的两态尺子，按方向分名册，各自带一条"为什么可以"。
    /// 放宽必须带理由（R75 那一课）：只有名字没有理由的名单等于把守卫撤了，只是撤得比较难看。
    static func luminanceOnlyExemptions() -> [(qualifiedName: String, reason: String)] {
        [
            (qualifiedName: "PressFeedbackTests.swift#rgbFraction",
             reason: "单轴报告尺。它的存在就是为了把亮度那一根**单独**报出来，配对的那条叫 alphaFraction，"
                    + "真正做判断的是同文件里的 changedFraction（已经是并集）。"
                    + "给它补 alpha 就等于把两根轴重新混成一个数 —— 那正是本轮要拆开的东西。"),
            (qualifiedName: "PressInteractionProbeTests.swift#rgbFraction",
             reason: "同上：这一族文件里 `axisLine` 用它打『亮度差=』那一列，"
                    + "与 alphaFraction、changedFraction 三条一起构成一次读数的三根轴。"
                    + "它不参与任何判据的取值，只参与读数。"),
            (qualifiedName: "PressFeedbackTests.swift#meanChannelDelta",
             reason: "均值差尺（梯子判据用它量『两档之间平均差多少 /255』）。它的盲区会以**红**的形式暴露："
                    + "只在 alpha 上动的一档读成 0 ⇒ 判据红着说『这一档不存在』，而不是绿着说『它没动』。"
                    + "R77 在同一条判据里加了 alpha差 那一列把这个前提变成读数，并加了一条断言让豁免自己作废："
                    + "本机实测 12 步（row/control/field × 亮/暗）全部 alpha差=0.00/255 而均值差 6.97–15.85，"
                    + "⇒ 这一族夹具确实铺的是实底。哪一步出现『均值差低于地板而 alpha差>8』，"
                    + "`testFillLaddersAreVisibleOnBothControlClasses` 就会红，这条豁免必须撤。"),
                (qualifiedName: "UICaptureHarness.swift#bandChanged",
         reason: "R242 新建的两态变化尺（BACKLOG 277 第一步）：数的是「idle↔lit 之间变了多少颗」，"
                + "为把 modechip 悬停那格从**绝对颗数地板**换掉——同一次 CI 里 runner 读 229 颗、本机读 1281 颗，"
                + "而对比度比值两边同为 1.36 ⇒ 那颗地板量的是那台机器的底平不平涂，不是反馈有没有。"
                + "alpha 那一根已经写进判定（`max(lumaDelta, alphaDelta) >= delta`），但这批 PNG 落盘时 alpha 恒 255"
                + "（R76/U-132 同族：内存里带 alpha、落盘那张不带）⇒ 这根轴今天**没有对象**，有效轴就是亮度。"
                + "代价与其余各条登记同族：「只改透明度不改颜色」的悬停层它读成没动 ⇒ 归 BACKLOG 108。"),
            (qualifiedName: "UICaptureHarness.swift#changedXSpan",
             reason: "R289 新建的两态**几何**尺（多文件详情区那条右轴的判据用它量悬停药丸铺到哪儿）。"
                    + "它按灰阶差 ≥2 找变化像素，交出的是 x 跨度与颗数 —— 判定用的是边的位置而不是边的深浅，"
                    + "补 alpha 那根轴换不出任何一个 x。通道事实与 `bandChanged` 同一条："
                    + "这批 PNG 落盘时 alpha 恒 255（R76/U-132：内存里带 alpha、落盘那张不带）⇒ 这根轴今天没有对象。"
                    + "代价照其余登记写明：「只改透明度、不改颜色」且合成后 RGB 完全相同的一层，它读成没动 ⇒ 归 BACKLOG 108。"),
]
    }

    /// 反方向：只读 alpha 的两态尺子。这一半不是本轮新发现的 —— R67/R76 那两条尺子是**故意**这么写的，
    /// 因为那条通道上"被点亮的墨"在亮度那一根上量不到（U-132 的同族，方向相反）。
    /// 记进名册的理由是：它今天成立，但它把"只在亮度上变"的效果判成"没变"，
    /// 这一半由 BACKLOG **108** 接着量（本轮先把方向钉住，不一次改完）。
    static func alphaOnlyExemptions() -> [(qualifiedName: String, reason: String)] {
        [
            (qualifiedName: "UICaptureHarness.swift#alphaBandDelta",
             reason: "R67 为『灰带必须与选中药丸同宽』新建：按列取带内最大 alpha 之差。"
                    + "R78 才被抓进名册 —— R77 那版把『两态』扫成减法针脚，而它写的是 "
                    + "abs(maxA - maxB) > floor，写法不一样就漏了（U-138：检测器认写法不认形状）。"
                    + "它只读 alpha 是有理由的：那层墨在亮度那一根上量不到（U-132 同族），"
                    + "代价是『只改颜色不改透明度』的效果它读成没变 ⇒ 归 BACKLOG 108。"),
            (qualifiedName: "UICaptureHarness.swift#alphaLiftProfile",
             reason: "与 alphaBandDelta 同一条通道的逐行轮廓尺（R67 为药丸圆角新建）："
                    + "那把尺给总范围、这把给轮廓，圆角与上下内缩只在逐行形状上看得见。"
                    + "同一根轴、同一个代价：轮廓只在 alpha 上取，亮度那一半不参与判定 ⇒ 归 BACKLOG 108。"),
            (qualifiedName: "PressFeedbackTests.swift#alphaFraction",
             reason: "单轴报告尺（R77 新建）：与 rgbFraction 成对，只为把『这一下动在哪根轴上』打进读数。"
                    + "它不做任何判断，判断在同一条文件里的 changedFraction（并集）。"),
            (qualifiedName: "PressInteractionProbeTests.swift#alphaFraction",
             reason: "同上，在在屏交互探针那份文件里：`axisLine` 的 alpha 那一列由它给，"
                    + "而 `heldDelta > 0.0002` 那个闸门读的是并集。"),
            (qualifiedName: "PressFeedbackTests.swift#meanAlphaDelta",
             reason: "R77 新建的那一列（FILL_STEP 行里的 alpha差）。"
                    + "它的任务恰恰是**替 meanChannelDelta 看着 alpha 这根轴**，所以自己只读一根。"),
        ]
    }

    /// 被扫的四个文件 = 捕获/动效那三把两态尺的住处 + 帧捕获卷自己。
    static func axisGuardFiles() -> [String] {
        ["MotionFilmstripTests.swift", "PressFeedbackTests.swift",
         "PressInteractionProbeTests.swift", "UICaptureHarness.swift"]
    }

    /// 守卫：任何**两态相减**的尺子必须两根轴都读，或者说明为什么只读一根（两个方向都要说）。
    ///
    /// 这一条钉的不是"今天对不对"（今天由 `testTheAxisRulerSeparatesAlphaFromLuminance` 钉），
    /// 而是"下一把新尺子不许再瞎"：R77 之前这四份文件里有三把只读亮度的两态尺
    /// （`axisPair`/`changedFraction`×3、`bandHeadTailDiff`、`PressInteractionProbeTests.changedFraction`），
    /// 它们把"暗墨在透明度上淡入"读成 0 —— 而这条通道今天已被证明**真的会**只在 alpha 上出东西
    /// （R76 / U-132：浮层焦点那一档）。
    ///
    /// 三条判据形状各拦一种失效：
    /// · 名册**双向相等** ⇒ 新盲区要红（M407/M410）、过期登记也要红（M409）；
    /// · 每条豁免必须带 ≥60 字的理由 ⇒ 名单不许退化成"有名字就行"（M408）；
    /// · "用了"而不是"读了" ⇒ `let alphaDelta = abs(...)` 挂在函数里却不参与判定，也算盲区（M407 教的）。
    func testEveryTwoStateRulerReadsBothAxes() throws {
        var luminanceOnly: [String] = []
        var alphaOnly: [String] = []
        var scanned: [(file: String, code: String)] = []
        for file in Self.axisGuardFiles() {
            let source = try testSource(named: file)
            scanned.append((file, source))
            // 找不到文件的那一支由 `testSource` 自己红（"守卫找不到被守卫的东西时必须红"）。
            let found = Self.blindDeltaRulers(named: file, code: source)
            luminanceOnly += found.luminanceOnly
            alphaOnly += found.alphaOnly
        }
        let registeredLuma = Self.luminanceOnlyExemptions()
        let registeredAlpha = Self.alphaOnlyExemptions()
        emit("AXIS_GUARD 两态尺只读亮度=" + (luminanceOnly.isEmpty ? "-" : luminanceOnly.joined(separator: ","))
            + " 只读alpha=" + (alphaOnly.isEmpty ? "-" : alphaOnly.joined(separator: ","))
            + " 名册=" + String(registeredLuma.count) + "/" + String(registeredAlpha.count))

        XCTAssertEqual(Set(luminanceOnly), Set(registeredLuma.map { $0.qualifiedName }),
                       "有把两态相减的尺子读了亮度却不拿 alpha 参与判定。新出现的一条 ⇒ 要么按 `axisPair` "
                           + "的形状补上并集，要么带理由登记；名单里剩着一条已经不存在的 ⇒ 也要红"
                           + "（过期名单比没名单更坏）。扫到=\(luminanceOnly.sorted()) "
                           + "名册=\(registeredLuma.map { $0.qualifiedName }.sorted())")
        XCTAssertEqual(Set(alphaOnly), Set(registeredAlpha.map { $0.qualifiedName }),
                       "有把两态相减的尺子只读 alpha ⇒ 它会把『只改颜色不改透明度』的效果判成没动。"
                           + "要么补亮度那一根，要么带理由登记（并归 BACKLOG 108）；"
                           + "过期登记同样红。扫到=\(alphaOnly.sorted()) "
                           + "名册=\(registeredAlpha.map { $0.qualifiedName }.sorted())")

        // R78 / U-137：名册里每一条尺子必须**真的有人调**。
        // 为什么这一格非有不可：R77 收进名册的 `paintedXRange` 全仓零调用点（只有它自己的声明），
        // 而我的理由里还写着"R67/R76 那两条判据用它…" —— 一条死尺占着豁免位，
        // 等于让"全部盲区都数过了"这句话变成假的，而且比漏登记更难看，因为它看起来是数过的。
        var deadRulers: [String] = []
        for entry in registeredLuma + registeredAlpha {
            let ruler = String(entry.qualifiedName.split(separator: "#").last ?? "")
            let calls = scanned.reduce(0) { $0 + Self.callSites(named: ruler, in: $1.code) }
            if calls == 0 { deadRulers.append(entry.qualifiedName) }
        }
        emit("AXIS_GUARD 名册里零调用点的尺=" + (deadRulers.isEmpty ? "-" : deadRulers.joined(separator: ",")))
        XCTAssertTrue(deadRulers.isEmpty,
                      "豁免名册里有一条尺子今天没有任何调用点 ⇒ 要么把死尺删掉（R63 那一课："
                          + "'代码没有作者'的处置是删代码，不是补判据），要么把它接回一条真判据。"
                          + "零调用点的豁免位会让'盲区都数过了'这句话变成假的。死尺=\(deadRulers.sorted())")

        // 每条豁免都得有理由，而且理由不能短到是一句"见注释"。
        for entry in registeredLuma + registeredAlpha {
            XCTAssertGreaterThanOrEqual(entry.reason.count, 60,
                                        "\(entry.qualifiedName) 的豁免理由只有 \(entry.reason.count) 个字符："
                                            + "放宽守卫要写清它为什么今天无害、以及什么情况下必须撤")
        }
        // 做判断的那把尺子永远不许进任何一个名册：它就是这条守卫存在的理由。
        for name in (registeredLuma + registeredAlpha).map({ $0.qualifiedName }) {
            XCTAssertFalse(name.hasSuffix("#changedFraction"),
                           "有人把 changedFraction 登记成'故意只读一根轴'⇒ 这条守卫从此拦不住任何一条判据")
            XCTAssertFalse(name.hasSuffix("#axisPair"),
                           "同上：`axisPair` 是这条卷的母尺，它不进名册也不许进")
        }

        // 正对照 A：一把只读亮度的合成尺子必须被点名（不点名的守卫是空转的装饰）。
        XCTAssertEqual(Self.blindDeltaRulers(named: "Synthetic.swift",
                                             code: Self.syntheticRulerSource(readingAlpha: false)).luminanceOnly,
                       ["Synthetic.swift#ruler"],
                       "只读亮度的合成尺子没被点名 ⇒ 上面那些断言都不算数")
        // 正对照 B：同一把尺子把 alpha 拿进判定之后必须**不再**被点名（否则它是"什么都红"，同样没用）。
        let fixed = Self.blindDeltaRulers(named: "Synthetic.swift",
                                          code: Self.syntheticRulerSource(readingAlpha: true))
        XCTAssertTrue(fixed.luminanceOnly.isEmpty && fixed.alphaOnly.isEmpty,
                      "补上第四根通道、并且拿它参与判定的合成尺子仍然被点名 ⇒ 针脚认的不是'用没用 alpha'，"
                          + "而是别的东西（这条守卫会误伤，接下来就没人敢用它）")
        // 正对照 C：读了却没用 —— 这一格就是 M407 那一刀的形状。
        // 只把 `let alpha = abs(...)` 放进去、判定里不用它，必须仍然算盲区：
        // "函数里出现过 + 3]"不等于"alpha 参与了结论"。
        let deadRead = Self.syntheticRulerSource(readingAlpha: false)
            .replacingOccurrences(of: "        if rgb",
                                  with: "        let alphaUnused = 0" + "\n        if rgb")
        XCTAssertTrue(deadRead.contains("alpha"), "合成用例得真的带上那行空读，否则这一格没内容")
        XCTAssertEqual(Self.blindDeltaRulers(named: "Synthetic.swift", code: deadRead).luminanceOnly,
                       ["Synthetic.swift#ruler"],
                       "一把读了 alpha 却不拿它判定的尺子被判成'两根轴都读'⇒ 这条守卫能被空转的读数糊弄过去")
        // 正对照 D：M407 那一刀真正的形状 —— 判定里没有 alpha，可**行尾注释**里提了一句，
        // 而那一行本来就带一个 `>`。上一版守卫就是在这里绿的（U-135）：
        // 它扫的是"行"，于是 `if delta > 6 { … }  // 又不读 alpha 了` 被当成"alpha 参与了判定"。
        let blindLine = "        if rgb > 8 || luma > 8 { changed += 1 }"
        let trapLine = blindLine + "  // 这一行尾巴上提了一句 alpha，而它不参与判定"
        let commentTrap = Self.syntheticRulerSource(readingAlpha: false)
            .replacingOccurrences(of: blindLine, with: trapLine)
        XCTAssertTrue(commentTrap.contains("alpha"), "合成用例得真的带上那句注释，不然这一格是空的")
        XCTAssertEqual(Self.blindDeltaRulers(named: "Synthetic.swift", code: commentTrap).luminanceOnly,
                       ["Synthetic.swift#ruler"],
                       "行尾注释里提一句 alpha 就把守卫喂掉了 ⇒ 扫之前没把注释剥掉")
        // 正对照 E：守卫不许命中自己。
        XCTAssertFalse(luminanceOnly.contains { $0.contains("testEveryTwoStateRulerReadsBothAxes") },
                       "守卫扫到了自己：针脚的拼法被写成了会被自己命中的形式")
        XCTAssertFalse(alphaOnly.contains { $0.contains("syntheticRulerSource") },
                       "合成尺子的生成器自己成了被扫到的盲区 ⇒ 针脚写在了生成器的源码里而不是运行时拼出来")
        // 正对照 F：调用点计数器自己必须分得清"声明"与"使用"（U-137 那一格的全部依据就是它）。
        let declaredOnly = Self.syntheticRulerSource(readingAlpha: true)
        XCTAssertEqual(Self.callSites(named: "ruler", in: declaredOnly), 0,
                       "只有声明、没有调用却被数成'有人用'⇒ 上面那条死尺判据是空转的")
        XCTAssertEqual(Self.callSites(named: "ruler", in: declaredOnly + "        let x = ruler(a, b)\n"), 1,
                       "加了一次真实调用却仍数 0 ⇒ 那条判据会把每条活尺都报成死尺")
        // 正对照 G：折行的签名也必须被认成两态尺（R78 换检测器就是因为 `alphaBandDelta` 折了两行）。
        let wrappedHeader = "    static func wrapped(_ a: Bitmap, _ aRows: Range<Int>,\n"
            + "                               _ b: Bitmap, _ bRows: Range<Int>, floor: Int) -> Int {\n"
            + "        var hit = 0\n"
            + "        if abs(Int(pa) - Int(pb)) > floor { hit += 1 }\n"
            + "        return hit\n    }\n"
        XCTAssertTrue(Self.takesTwoBitmaps(header: wrappedHeader),
                      "折行的签名没被认成两态尺 ⇒ 名册会随**排版**变化而漏条目（R77 就是这么漏掉 alphaBandDelta 的）")
        // 正对照 H：只收**一张**图的电平尺不许被认成两态尺。这一格是 R78 自己踩的坑：
        // `NSBitmapImageRep` 里含子串 `Bitmap`，长写法不先挖掉就会把单参函数数成两态
        // （第一版因此把 `meanAlpha` / `meanLuma` 双双点成盲区尺 —— 误伤会让下一个人关掉这条守卫）。
        XCTAssertFalse(Self.takesTwoBitmaps(
            header: "    static func meanAlpha(_ rep: NSBitmapImageRep, rect: CGRect) -> Double {"),
            "单张图的电平尺被数成两态尺 ⇒ 长写法没先从串里挖掉")
        XCTAssertTrue(Self.takesTwoBitmaps(
            header: "    static func meanDelta(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Double {"),
            "真的两态签名反而没被认出来 ⇒ 这一格与上面那格一起才说明数的是**参数个数**")
        // 正对照 I（R80）：**轴的名字写在驼峰中间**也必须算"用了 alpha"。
        // 这一格是 R80 自己被这条守卫点名的那次：新写的那把尺里参与判定的一行是
        // `if deltaAlpha > move { move = deltaAlpha }` —— 语义上 alpha 进了结论，
        // 字面上小写 needle 看不见它，于是守卫把**真读了两根轴的尺**判成盲区。
        // U-138 说的是"检测器认写法不认形状"会**漏**；这是同一枚硬币的另一面：认写法也会**误伤**，
        // 而误伤的后果比漏更糟 —— 下一个人会去改名而不是去读轴，守卫就变成拼写检查器。
        let camel = Self.syntheticRulerSource(readingAlpha: true)
            .replacingOccurrences(of: "let alpha = abs(", with: "let deltaAlpha = abs(")
            .replacingOccurrences(of: "|| alpha > 8", with: "|| deltaAlpha > 8")
        XCTAssertTrue(camel.contains("deltaAlpha >"), "合成用例没换上驼峰写法 ⇒ 这一格没内容")
        XCTAssertFalse(camel.contains("alpha > 8"), "换写法没换干净：还留着全小写那一行，这一格就没测到东西")
        let camelFound = Self.blindDeltaRulers(named: "Synthetic.swift", code: camel)
        XCTAssertTrue(camelFound.luminanceOnly.isEmpty && camelFound.alphaOnly.isEmpty,
                      "把 alpha 写成驼峰中间的一段（`deltaAlpha`）就被判成只读亮度 ⇒ 这条守卫认拼写不认语义，"
                          + "它会把人教成改名而不是补轴。盲区=\(camelFound.luminanceOnly)")
    }

    /// 读一份**测试**文件的源码（`productSource(named:)` 走的是 Sources/ 那棵树，这里要的是 Tests/）。
    private func testSource(named file: String) throws -> String {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Tests/ClipboardHistoryAppTests/" + file)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "MotionFilmstripTests", code: 2, userInfo: [
            NSLocalizedDescriptionKey: "找不到 Tests/ClipboardHistoryAppTests/\(file)：守卫找不到被守卫的东西时必须红",
        ])
    }

    /// 两态相减那把尺子的**分轴真值表**（R77 / BACKLOG 107）。
    ///
    /// 纯数据、不开窗口 ⇒ CI 每轮都跑。它要钉的是三件事，每件都会单独坏：
    /// ① **暗墨在透明度上淡入 = 亮度轴读 0**（`blind` 那一格）。
    ///    这不是假想：R76 的 U-132 就是在同一条捕获通道上量到的 —— 两张 PNG 去掉 alpha
    ///    逐像素相同。`raster` 用 `premultipliedLast` 画进零初始化缓冲区，墨越暗，
    ///    它的 RGB 越接近 0，于是"0→0"在亮度轴上永远读不出东西。
    ///    这一格断言的是 `rgb == 0` 而 `either == 1`：**盲区必须被量出来**，
    ///    不然这条判据就只是在给旧读数背书。
    /// ② **加轴不许把亮度轴换掉**（`colorOnly` 那一格：纯颜色变化、alpha 钉住，
    ///    必须仍然读成"变了"）。这一格拦的是"把 `rgb` 那一轴删了只留 alpha"那种改法。
    /// ③ **并集不是两数取大**（`splitAxes` 那一格：左半只动 alpha、右半只动 RGB
    ///    ⇒ `rgb=0.5 alpha=0.5 either=1.0`）。拦的是把 `either` 简化成 `max(rgb, alpha)` ——
    ///    那个写法在"两轴各动一半"时把变化量低估一半，而它看起来一模一样、也照样绿。
    ///
    /// 另外三格是尺子自己的地板与极性：两根轴**共用**同一个 8/255 门槛（否则两个数不可比），
    /// 相同的图必须读 0，a/b 对调必须给同一组数（"变暗"不许被当成"没变"）。
    func testTheAxisRulerSeparatesAlphaFromLuminance() {
        func read(_ pair: (Bitmap, Bitmap)) -> AxisPair { Self.axisPair(pair.0, pair.1, band: nil) }

        // ① 亮墨出现：两轴同时动（预乘缓冲区里 (0,0,0,0) → (200,200,200,255)）。
        let bright = read(Self.syntheticPair(width: 28, height: 28))
        XCTAssertEqual(bright.rgb, 1.0, accuracy: 1e-9, "亮墨出现，亮度轴必须读满")
        XCTAssertEqual(bright.alpha, 1.0, accuracy: 1e-9)
        XCTAssertEqual(bright.either, 1.0, accuracy: 1e-9)

        // ② 暗墨在 alpha 上淡入：RGB 一直是 0，只有透明度动了 ⇒ 亮度轴是瞎的。
        let blind = read(Self.syntheticPair(width: 28, height: 28,
                                            ink: (0, 0, 0, 255)))
        XCTAssertEqual(blind.rgb, 0.0, accuracy: 1e-9,
                       "这一格钉的是『亮度轴看不见暗墨的透明度』这个事实。它要是变成非 0，"
                       + "说明缓冲区不再是预乘零初始化 —— 那 R76/R77 记下的所有 alpha 结论都要重读")
        XCTAssertEqual(blind.alpha, 1.0, accuracy: 1e-9, "alpha 轴必须把这一下看成整幅变了")
        XCTAssertEqual(blind.either, 1.0, accuracy: 1e-9,
                       "并集那一轴必须看得见 ⇒ 『没动』这个结论现在要求两轴同时静")

        // ③ 颜色在动、alpha 钉住：加轴不许把原来那一根换掉。
        let colorOnly = read(Self.syntheticPair(width: 28, height: 28,
                                                base: (0, 0, 0, 255),
                                                ink: (200, 200, 200, 255)))
        XCTAssertEqual(colorOnly.rgb, 1.0, accuracy: 1e-9)
        XCTAssertEqual(colorOnly.alpha, 0.0, accuracy: 1e-9, "alpha 没动就不许读数")
        XCTAssertEqual(colorOnly.either, 1.0, accuracy: 1e-9)

        // ④ 相同的图必须读 0 —— 上面三个 1.0 与这里的 0 是一对，缺一个就没有"读数"这回事。
        let same = read(Self.syntheticPair(width: 28, height: 28, ink: (0, 0, 0, 0)))
        XCTAssertEqual(same, AxisPair(rgb: 0, alpha: 0, either: 0), "尺子在两张相同的图上读出了变化")

        // ⑤ 两轴共用同一道地板：8/255 不算变，9/255 算。
        //    两根轴若各用各的门槛，`亮度峰值` 与 `alpha峰值` 这两列就不可比，
        //    而"这一臂只在 alpha 上动"那句结论完全建立在这句可比上。
        let atFloor = read(Self.syntheticPair(width: 28, height: 28, ink: (0, 0, 0, 8)))
        let overFloor = read(Self.syntheticPair(width: 28, height: 28, ink: (0, 0, 0, 9)))
        XCTAssertEqual(atFloor.alpha, 0.0, accuracy: 1e-9, "地板取的是『严格大于 8』，这一格必须正好落在门外")
        XCTAssertEqual(overFloor.alpha, 1.0, accuracy: 1e-9)
        let rgbAtFloor = read(Self.syntheticPair(width: 28, height: 28, ink: (8, 8, 8, 0)))
        let rgbOverFloor = read(Self.syntheticPair(width: 28, height: 28, ink: (9, 9, 9, 0)))
        XCTAssertEqual(rgbAtFloor.rgb, 0.0, accuracy: 1e-9, "亮度轴的地板必须和 alpha 轴是同一道")
        XCTAssertEqual(rgbOverFloor.rgb, 1.0, accuracy: 1e-9)

        // ⑥ 极性：**变暗**与**变淡**必须给同一组数。
        //    故意用一支"从亮掉到暗"的图：signed 的实现（`b − a > 8`）在这一支上读 0、
        //    反过来读 1.0，而 abs 的实现两边都是 1.0。拿两张都亮的图比是对称的，抓不到它。
        let dimming = Self.syntheticPair(width: 28, height: 28,
                                         base: (200, 200, 200, 255),
                                         ink: (20, 20, 20, 90))
        let forward = read(dimming)
        let backward = read((dimming.1, dimming.0))
        XCTAssertEqual(backward, forward,
                       "把 a/b 对调就读出别的数 ⇒ 这把尺是 signed 的，'淡出'那一臂会读出另一个答案")
        XCTAssertGreaterThan(forward.rgb, 0, "这一格还得真的量到东西：两个 0 相等不算极性检查")

        // ⑦ 并集 ≠ 两数取大（`splitAxes`：左半只动 alpha，右半只动 RGB）。
        //    28 宽 ⇒ 每 7 个像素采一个正好落在左 2 / 右 2，0.5 是个精确数而不是近似。
        let split = read(Self.syntheticPair(width: 28, height: 28, base: (100, 100, 100, 255)) { x, _ in
            x < 14 ? (100, 100, 100, 0) : (200, 200, 200, 255)
        })
        XCTAssertEqual(split.rgb, 0.5, accuracy: 1e-9, "右半只动 RGB ⇒ 亮度轴读到一半")
        XCTAssertEqual(split.alpha, 0.5, accuracy: 1e-9, "左半只动 alpha ⇒ alpha 轴读到另一半")
        XCTAssertEqual(split.either, 1.0, accuracy: 1e-9,
                       "并集必须是 1.0：『任一轴动过就算这像素变了』。谁把 either 写成 max(rgb, alpha)，"
                       + "这一格就红（那个写法在这里只给 0.5，把变化量低估一半）")
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

    /// 造一卷「**从左到右一根一根亮起来**」的合成帧（R326 的采样粒度证人）。
    ///
    /// 为什么不能复用上面那份纯色帧：纯色帧每一步都让**全部**像素变，于是粗采样与细采样
    /// 读出的峰值都是 1.0 —— 那正好是我要证伪的那个 confound 的反例，用它当证人等于没有证人。
    /// 这里每一步只亮一部分列，峰值才会随采样粒度走（粗的一卷每步亮得多 ⇒ 峰值大），
    /// 而首末差与并集只认"两端各是什么画面"，与中间采了几次无关。
    ///
    /// 尺寸取 70 不是随手来的：那两条尺都按 stride 7 采样，70 让 10 列各被采到一个像素，
    /// "亮 35 列" 恰好等于 "50% 的采样像素" —— 证人要的数能手算。
    static func syntheticRevealFilm(revealedColumns: [Int], width: Int = 70,
                                    height: Int = 70, ink: UInt8 = 200) -> [CGImage] {
        revealedColumns.map { revealed in
            var pixels = [UInt8](repeating: 0, count: width * height * 4)
            // 底是**不透明黑**而不是全透明：窗口抓帧的 alpha 整幅都是 255，
            // 透明的底会让"墨量差"那一颗尺只看 alpha 通道就顶到 1.0（200 与 120 读不出差别），
            // 于是它看不见自己本该看见的那一格 —— 夹具要像被量的东西，不像最容易构造的东西。
            for index in stride(from: 3, to: pixels.count, by: 4) { pixels[index] = 255 }
            for y in 0..<height {
                for x in 0..<width where x < revealed {
                    let p = (y * width + x) * 4
                    pixels[p] = ink; pixels[p + 1] = ink; pixels[p + 2] = ink
                }
            }
            let space = CGColorSpace(name: CGColorSpace.sRGB)!
            let context = CGContext(data: &pixels, width: width, height: height, bitsPerComponent: 8,
                                    bytesPerRow: width * 4, space: space,
                                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
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
                                            clockIntervalMilliseconds: worst,
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
                                        clockIntervalMilliseconds: jumpWorst,
                                        declaredDurationMilliseconds: 160,
                                        changedFrames: 1), .jump,
                       "45ms 的变化段对 160ms 的声明 ⇒ 必须判成跳变，否则这条判据没有判别力")
        // 门槛之下：63ms 的变化段（160ms 声明、时钟 45ms）仍然算没演完。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 63, clockIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 1), .jump)
        // 边界：s = 0.3d 时真过渡的最坏读数 d−2s 正好等于 0.4d ⇒ 判据在边界上仍然自洽
        //（"真过渡必过、跳变必红"这两个要求同时成立的那个点）。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 64, clockIntervalMilliseconds: 48,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .transition)
        XCTAssertNotEqual(Self.judgeMotion(elapsedMilliseconds: 48, clockIntervalMilliseconds: 48,
                                           declaredDurationMilliseconds: 160, changedFrames: 1), .transition,
                         "跳变的最坏读数（=s）不许过线")
        // MARK: R8 —— 三档。CI 实测把这条逼出来的：runner 事件内 ~55ms 一帧，
        // 三个场景全掉进中间档，`judged` 从 3/3 掉到 **0/3**，新加的覆盖率闸门如实报红。
        // 中间档（0.3d < s ≤ 0.5d）：跳变 1 帧、过渡至少 2 帧 ⇒ 帧数在这里够用。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 110, clockIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .transition,
                       "CI 那档时钟必须仍然判得出东西，否则覆盖率闸门会长期红着")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 55, clockIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 1), .jump,
                       "中间档里的一帧跳变仍然要红")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 110, clockIntervalMilliseconds: 55,
                                        declaredDurationMilliseconds: 160, changedFrames: 0), .jump,
                       "变化帧数读成 0 却报绿 ⇒ 中间档没有地板")
        // 细时钟档：只看时长，帧数不参与 ⇒ 相位翻脸抓不住它
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 135, clockIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 2), .transition,
                       "细时钟下 2 帧也判绿：这一档看的是时长不是帧数")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 45, clockIntervalMilliseconds: 45,
                                        declaredDurationMilliseconds: 160, changedFrames: 2), .jump,
                       "时长不够就红，哪怕帧数到了 2")
        // 太粗档（s > 0.5d）⇒ 无从判定，既不判红也不判绿。
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 200, clockIntervalMilliseconds: 100,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .clockTooCoarse,
                       "事件那一段 100ms 一帧、整段过渡只有 160ms ⇒ 是尺子看不见，不是产品没动")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 999, clockIntervalMilliseconds: 0,
                                        declaredDurationMilliseconds: 160, changedFrames: 3), .clockTooCoarse,
                       "时钟没测到 ⇒ 不能当成「无限细」往下判")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 999, clockIntervalMilliseconds: 30,
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
        // 结论行打在断言之前（R53 那一课），并且**两根轴各报一个数**：
        // 这一条是 `minimumVisibleChange` 的变异捕手，而它要证的"什么都没动"从今天起
        // 必须在亮度轴和 alpha 轴上同时成立 —— 只报一根轴的话，另一根上的抖动
        // 永远不会被看见（R76 的 U-132：那次差别只在 alpha）。
        // 老的三个字段名原样保留：账本与 CI 存档里引用过 `MOTION_BLANK 峰值=0.0000`
        // （D-0xx 那一族），换个字段名就等于把历史读数作废。
        let axis = Self.axisSummaryLine(frames)
        emit("MOTION_BLANK frames=\(frames.count) 峰值=\(String(format: "%.4f", fractions.max() ?? 0)) "
            + "过渡帧数=\(span) " + axis)
        XCTAssertEqual(span, 0, "什么都没发生却量到了过渡 ⇒ 尺子在把重绘噪声读成动画（两轴读数：" + axis + "）")
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

    /// R82 / BACKLOG 113：循环那条判据的形状尺（`loopShape`）与三支处置的真值表。
    ///
    /// 这一整格是**合成数据**，不开窗口 ⇒ CI 每轮都跑。它要钉的正是"真实那一臂今天判成什么"
    /// 之外的那件事：判据的形状不许跟着采样密度翻脸（R80 的 runner 与本机就是两组这样的数）。
    func testTheLoopShapeClassifierIsATruthTable() throws {
        // 漂移钉子：结构体里那条地板与外层那条必须是同一个数（见 `LoopShape.minPeak` 的注释）。
        XCTAssertEqual(LoopShape.minPeak, Self.minimumVisibleChange,
                       "循环尺的峰值地板与全卷那条地板分家了 ⇒ 两支处置会互相冒名："
                           + "『没拍到变化』与『拍到但没一直动』的界线只能有一处")
        func stamps(every ms: Double, count: Int) -> [TimeInterval] {
            (0..<count).map { index in TimeInterval(Double(index) * ms / 1000.0) }
        }
        // ① 均匀在变 ⇒ looping，coverage ≈ 1
        let loop = Self.loopShape(fractions: [Double](repeating: 0.02, count: 20),
                                  stamps: stamps(every: 50, count: 21))
        XCTAssertEqual(loop.verdict, .looping)
        XCTAssertGreaterThan(loop.coverage, 0.9, "整卷都在变，coverage 应该接近 1")
        // ② 只有一个帧对在变 ⇒ oneShot
        var jump = [Double](repeating: 0.0, count: 20)
        jump[5] = 0.02
        let jumped = Self.loopShape(fractions: jump, stamps: stamps(every: 50, count: 21))
        XCTAssertEqual(jumped.changingPairs, 1)
        XCTAssertEqual(jumped.verdict, .oneShot,
                       "一次跳变的 coverage 就是一个采样 ÷ 整卷 ≈ \(String(format: "%.3f", jumped.coverage)) ⇒ 不许算循环")
        XCTAssertLessThan(jumped.coverage, 0.2)
        // ③ **同一段物理循环、两种采样密度 ⇒ 判定必须一样，而旧那把"数帧对"的尺必须给出两个数**
        //    这一格是整轮的性质所在：它钉的不是"今天对不对"，是"这把尺跟不跟着网格走"。
        let fine = Self.loopShape(fractions: [Double](repeating: 0.02, count: 20),
                                  stamps: stamps(every: 50, count: 21))
        let coarseFractions = [Double](repeating: 0.02, count: 9)
        let coarse = Self.loopShape(fractions: coarseFractions, stamps: stamps(every: 115, count: 10))
        XCTAssertEqual(fine.verdict, coarse.verdict,
                       "50ms 与 115ms 两种采样下，同一种『一直在变』被判成了两样 ⇒ 判据吃的还是帧数")
        // 第一版这里写的是"coverage 允许差一点"（`abs(差) > 0`），那是句废话断言：
        // 两档采样下两个数**都正好是 1.0**，于是它红在自己的空转上。
        // 换成真正要钉的性质：**coverage 是时间之比，因此与帧数无关**。
        XCTAssertEqual(fine.coverage, coarse.coverage, accuracy: 0.05,
                       "同一种『一直在变』在 50ms 与 115ms 两种采样下 coverage 差开了 ⇒ 这个量还是跟着网格走")
        XCTAssertNotEqual(Self.transitionFrameCount([Double](repeating: 0.02, count: 20)),
                          Self.transitionFrameCount(coarseFractions),
                          "旧那把尺在两档采样上必须给出**不同**的个数 —— 这一格钉的是『换尺的理由』本身："
                              + "R80 的 CI 上本机 23 对、runner 2 对，而两边峰值都是 0.015")
        // ④ 整卷没拍到任何东西 ⇒ notMoving（既不是产品没循环，也不是环境，是"没量到"）
        let dead = Self.loopShape(fractions: [Double](repeating: 0.0, count: 20),
                                  stamps: stamps(every: 50, count: 21))
        XCTAssertEqual(dead.verdict, .notMoving)
        // ⑤ 两头各留一段静止：coverage 的分母是**整卷**，不是"变化段的长度"
        var head = [Double](repeating: 0.0, count: 20)
        for index in 0..<3 { head[index] = 0.02 }
        var tail = [Double](repeating: 0.0, count: 20)
        for index in 17..<20 { tail[index] = 0.02 }
        let headShape = Self.loopShape(fractions: head, stamps: stamps(every: 50, count: 21))
        let tailShape = Self.loopShape(fractions: tail, stamps: stamps(every: 50, count: 21))
        XCTAssertEqual(headShape.coverage, tailShape.coverage, accuracy: 0.02,
                       "同样三对在变，摆在卷首与卷尾读出两个 coverage ⇒ 分母不是整卷时长（那是位置偏差，不是形状）")
        XCTAssertLessThan(headShape.coverage, LoopShape.minCoverage,
                          "只演了开头三对就该判『没一直动』；它现在 coverage=\(String(format: "%.3f", headShape.coverage))")
        // ⑥ 处置的三支 + 证人坏掉那一支
        // ⑥ **时刻与读数对不上**（本轮自己犯过的错，见 U-155：探针把时刻存在自己身上，
        //    后一卷覆盖前一卷）⇒ 整卷算"没量到"，不许算"只动了一下"。
        //    这一格钉两件事：①`stamps.count == fractions.count + 1` 这条**结构等式**
        //    （少一根算不出，多一根就是别卷的）；②处置方向 —— "没量到"点名 not-run，
        //    "只动了一下"判产品红，两者不能靠一个残缺的形状互相冒名。
        let mismatched = Self.loopShape(fractions: [Double](repeating: 0.02, count: 20),
                                        stamps: stamps(every: 50, count: 20))
        XCTAssertEqual(mismatched.verdict, .notMoving,
                       "少一根时刻就算不出 coverage，此时若仍然把峰值报出去，判定会写成 `.oneShot` ⇒ "
                           + "尺自己的前提故障被冒充成『产品只动了一下』。这一格现在读到 "
                           + "coverage=\(String(format: "%.3f", mismatched.coverage)) 峰值=\(String(format: "%.4f", mismatched.peak))")
        XCTAssertEqual(Self.loopAdjudication(product: mismatched.verdict, rateWitness: .looping,
                                             coarseWitness: .looping), .productRed,
                       "形状尺红的方向也要有对照：前提故障被判成 `notMoving` 之后，"
                           + "产品这一侧仍然是红（不是被赦免）—— 这一格钉的是『它没有悄悄变绿』")
        //    等式是双向的：**多一根**时刻同样算"没量到"（那多半是别的一卷的尾巴）。
        let extraStamp = Self.loopShape(fractions: [Double](repeating: 0.02, count: 20),
                                        stamps: stamps(every: 50, count: 22))
        XCTAssertEqual(extraStamp.verdict, .notMoving,
                       "时刻比帧对多一根也被放行 ⇒ 结构等式退回了『大概对得上』，"
                           + "而 U-155 那一族恰恰是两卷长度差不多的时候最不容易发现")
        // ⑧ **前提尺与结论尺必须各量各的**（R83 修的那条假红，见 `FilmPremise`）：
        //    一卷"整帧都没变"的胶片仍然有卷长。R82 把卷长挂在 `LoopShape.recordedMilliseconds` 上，
        //    而那个数在峰值 0 时被 guard 归零 ⇒ runner 上"看不见运动"被改写成"探针坏了"。
        let still = Self.filmPremise(frames: 21, stamps: stamps(every: 50, count: 21))
        XCTAssertTrue(still.paired, "21 帧配 21 根时刻就是成对（时刻与帧是一对，不是帧对+1）")
        XCTAssertEqual(still.spanMilliseconds, 1000, accuracy: 0.001,
                       "整卷没动也必须报出 1000ms —— 卷长是录像的性质，不是运动的性质。"
                           + "现在读到 \(still.spanMilliseconds)：说明前提又挂回结论尺的输出上了")
        // 峰值 0 的那一卷：结论尺说"记录时长 0"，前提尺说"1000ms"。两个数**必须**不同，
        // 这一格钉的就是"它们量的是两件事"。
        let deadShape = Self.loopShape(fractions: [Double](repeating: 0.0, count: 20),
                                       stamps: stamps(every: 50, count: 21))
        XCTAssertEqual(deadShape.recordedMilliseconds, 0, accuracy: 0.001,
                       "guard 分支把记录时长归零是**已知行为**（这一格是上面那条对照的另一半）")
        XCTAssertNotEqual(still.spanMilliseconds, deadShape.recordedMilliseconds,
                          "前提尺与结论尺给出同一个数 ⇒ 它们又变成同一把尺了，R82 那朵假红的形状会回来")
        let shortFilm = Self.filmPremise(frames: 21, stamps: stamps(every: 25, count: 21))
        XCTAssertEqual(shortFilm.spanMilliseconds, 500, accuracy: 0.001,
                       "每帧 25ms 的卷只有半秒长 ⇒ 前提必须报出来（探针提前收卷的形状）")
        let unpaired = Self.filmPremise(frames: 21, stamps: stamps(every: 50, count: 20))
        XCTAssertFalse(unpaired.paired, "时刻少一根就是不配对（U-155 的墓碑）")
        // ⑦ 处置：产品形状 × **两颗**证人形状。等节拍那颗决定"产品红 / 环境不行"，
        //    粗节拍那颗只决定"签字的人来没来上班"。
        XCTAssertEqual(Self.loopAdjudication(product: .looping, rateWitness: .notMoving, coarseWitness: .notMoving), .ok,
                       "产品在动就是绿，不需要证人签字（绿不需要借口）")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping, coarseWitness: .looping), .productRed,
                       "与产品同节拍、同对比度、同画法的证人能一直动，而产品那份没动 ⇒ 这句是产品的责任，不许推给环境")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .oneShot, coarseWitness: .looping), .notRunEnvironment,
                       "等节拍证人也只能动一下 ⇒ 这台机器今天带不动那一档节拍的常驻循环，判产品没有依据")
        // 这一格是 R82 把单颗证人换成两颗时**唯一新增**的性质：
        // 等节拍那颗整卷没拍到东西（比如产品的对比度掉到看不见，把证人一起带走了），
        // 也不许翻成 `.productRed` —— 那是拿证人的瞎判产品的罪。粗节拍那颗还在上班，所以也不算空支票。
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .notMoving, coarseWitness: .looping), .notRunEnvironment,
                       "等节拍证人整卷没拍到东西时，不许判产品红：它瞎了不代表产品没动")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping, coarseWitness: .notMoving), .witnessDead,
                       "连高对比、粗节拍那颗都没拍到任何变化时，不许走『环境看不见』那一支 —— 那是一张空支票（R68 那一族）")
        // ⑧ R87：**位置尺的行程**能不能替产品说话。三格一起钉，因为"能不能签"取决于
        //    它是哪一种"没在动"：走过整幅 / 有可用帧但没走过 / 根本没有可用帧。
        //    这一族是读 R86 的 CI 读出来的（run 38811457259）：同一份产品代码、同一台机器类别，
        //    coverage 三遍 0.522 / 0.842 / **0.032**，而行程三遍 109pt / 134pt / **134pt**。
        //    第三遍它把产品判成了红，而位置尺在同一卷上有 12 个可用帧在说"亮带走完了整幅"。
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping,
                                             coarseWitness: .looping, travel: .sweeping), .notRunRulerBlind,
                       "位置尺在同一卷上量到亮带走过了整幅，而 coverage 只靠 1–2 个变化帧对撑着 ⇒ "
                           + "这时判产品红就是让样本少的那把尺否决样本多的那把尺。"
                           + "这一支既不红也不绿：它点名成一条有名字的未覆盖")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping,
                                             coarseWitness: .looping, travel: .notSweeping), .productRed,
                       "位置尺也说亮带**没走过**（有可用帧，行程不够）⇒ 红不许被悄悄放宽："
                           + "两把尺一起说没在动时，『coverage 吃采样网格』这个借口就不成立了")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping,
                                             coarseWitness: .looping, travel: .unreadable), .productRed,
                       "位置尺今天没有读数（可用帧不够）⇒ 不许把它当成『它在动』的免检牌，"
                           + "红仍然由等节拍那颗证人签 —— 新那一格只放行**有证据的**矛盾")
        // 方向钉子（谓词不许恒真）：产品在动就是绿，`travel` 说什么都不能改判；
        // 而"签字的人没来上班"（粗节拍那颗整卷没拍到东西）仍然优先于行程证据 ——
        // 一把坏掉的尺量出"走过 134pt"不是证据。
        XCTAssertEqual(Self.loopAdjudication(product: .looping, rateWitness: .notMoving,
                                             coarseWitness: .notMoving, travel: .notSweeping), .ok,
                       "产品自己一直在动时，行程那一格不许反过来把它判掉 ⇒ 新那一支只在 "
                           + "`product != .looping` 时才有资格说话（绿不需要借口）")
        XCTAssertEqual(Self.loopAdjudication(product: .oneShot, rateWitness: .looping,
                                             coarseWitness: .notMoving, travel: .sweeping), .witnessDead,
                       "粗节拍那颗整卷什么都没拍到 ⇒ 先红在证人，而不是让行程替『尺没坏』背书")
        // `travelEvidence` 自己的三格：它读的是**帧数与行程**，不是 `verdict`。
        XCTAssertEqual(Self.travelEvidence(BandReading(verdict: .oneBand, reason: "对照", framesUsed: 12,
                                                       travelPoints: 134)), .sweeping,
                       "runner 那一卷的真实形状（可用帧 12、行程 134pt）必须读成 sweeping，"
                           + "否则上面那三格全是纸上的")
        XCTAssertEqual(Self.travelEvidence(BandReading(verdict: .notJudged, reason: "对照", framesUsed: 8,
                                                       travelPoints: 4)), .notSweeping,
                       "有可用帧却只走了 4pt ⇒ 这是『没在动』的位置证据，不许被 `.notJudged` 这个"
                           + "笼统的判定吞成『没有读数』（那是另一种坏法，会白放行红）")
        XCTAssertEqual(Self.travelEvidence(BandReading(verdict: .noFrames, reason: "对照", framesUsed: 2,
                                                       travelPoints: 0)), .unreadable,
                       "可用帧不够（<3）就没有行程证据 ⇒ 它不许替任何一方签字")

        // ⑨ 两种 not-run **不许共用一个名字**（R87）：登记表的 `BAD_REASON` 那一格只比名字，
        //    而"机器带不动那一档节拍"与"coverage 这把尺吃采样网格"是两种不同的坏法 ——
        //    借名字等于让新那一种沿用旧那一格的免检牌，登记表从此看不出多了一种病。
        XCTAssertNotEqual(Self.loopStateReason(.notRunEnvironment),
                          Self.loopStateReason(.notRunRulerBlind),
                          "两支 not-run 共用一个理由名 ⇒ 登记表分不清是哪一种坏法（U-162 的反面："
                              + "同一个词在两个判据里含义不同就别统一成一个名字）")
        XCTAssertEqual(Self.loopStateReason(.notRunRulerBlind), "loop-coverage-contradicted-by-travel",
                       "这个名字已经写进 `motion_floor_expectations.json` 的 `loops` 那一节；"
                           + "改了这里不改那里，CI 会红在 BAD_REASON —— 两条都改，或者都别改")
        emit("LOOP_TRUTH_TABLE 均匀=looping 跳变=oneShot 两档采样=同判定 空=notMoving 头尾=同 coverage "
            + "时刻少一根/多一根=notMoving 处置=8 格（含 R87 的行程三格） 前提=静止卷仍有卷长（与结论尺的 0 不同）")
    }

    /// R82：等节拍那颗证人**必须仍然等于产品那几颗数** —— 它写死在测试里（不能被被告牵着改），
    /// 而它的合法性又完全来自"等于产品"。这两件事只能靠一条会红的钉子缝合。
    ///
    /// 这一条不判产品，判的是"证人还有没有资格替产品签字"：产品改了节拍或对比度而证人没跟上，
    /// `.productRed` 那句就退回成"有一台 20Hz 的机器带得动循环"那种弱证词。
    func testTheLoopWitnessStillMirrorsTheProductLoop() throws {
        let witness = GradientTickView.productRate()
        let productStep = SkeletonMotion.fraction(
            secondsPerCycle: MotionCatalog.duration(for: .skeletonSweep))
        XCTAssertNotNil(productStep, "产品的 `fraction(secondsPerCycle:)` 返回 nil ⇒ 扫光那条时钟根本没接上，"
                        + "证人无从镜像，先修产品")
        XCTAssertEqual(witness.tickSeconds, SkeletonMotion.tickInterval, accuracy: 1e-12,
                       "证人的节拍与产品分家了（证人 \(witness.tickSeconds)s / 产品 \(SkeletonMotion.tickInterval)s）⇒ "
                           + "它证的是『这台机器带得动 N Hz』而不是『带得动产品那一档』，`.productRed` 这句就说过头了。"
                           + "要么改证人跟上产品，要么把产品改回这一档 —— 不许只改这条断言的期望值")
        XCTAssertEqual(Double(witness.stepPerTick), Double(productStep ?? 0), accuracy: 1e-12,
                       "证人每拍推进量与产品分家 ⇒ 两台机器读到的『一直在动』不再是同一件事："
                           + "推进量决定每个采样间隔里亮带走多远，那正是 coverage 的分母吃的东西")
        XCTAssertEqual(witness.highlightLift,
                       SkeletonMotion.highlightOpacity - SkeletonMotion.baseOpacity, accuracy: 1e-12,
                       "证人的亮带抬升与产品分家 ⇒ 对比度不同的两颗视图不能互相当反证："
                           + "产品那一份抬 0.12（0.06→0.18），R81 之前那颗证人抬 0.39（0.06→0.45），"
                           + "而同一台 runner 上产品 2 对在变、那颗证人 13 对在变 —— 抬升差 3 倍正是嫌疑之一")
        // 抬升本身还得过产品自己那条地板，否则镜像过来的是个"本来就看不见"的证人。
        XCTAssertGreaterThanOrEqual(witness.highlightLift, SkeletonMotion.minimumHighlightLift,
                                    "镜像过来的抬升低于产品自己声明的最小可见抬升 ⇒ 这颗证人天生就瞎，"
                                        + "它签字的『环境看不见』那一支等于没人签")
        emit("LOOP_WITNESS_MIRROR 节拍=\(String(format: "%.1f", witness.tickSeconds * 1000))ms "
            + "每拍推进=\(String(format: "%.4f", Double(witness.stepPerTick))) "
            + "抬升=\(String(format: "%.2f", witness.highlightLift)) 三项全等于产品 ⇒ 证人还在问同一句话")
        // R84：上面三颗数钉的是"同一档节拍与同一组对比度"，钉不住**同一套画法**。
        // `.productRed` 那句推论写的是"只差视图归谁这一个差别"，而"画法"也是差别之一：
        // 产品换成整组一个形状、证人留在每根条一个形状，那两颗就不再是同一个负载。
        // 这一条没法从像素反推（证人不是被量的对象），所以它是源码级守卫 —— 与
        // `SkeletonMotionTests` 那几条接线守卫同一族，也因此必须自带"谓词不许恒真"那格。
        let product = codeOnly(try productSource(named: "Views/SkeletonShimmer.swift"))
        let witnessFile = codeOnly(try String(contentsOf: URL(fileURLWithPath: #filePath)))
        let drawsOneShapeForTheGroup: (String) -> Bool = { $0.contains("SkeletonBarsShape()") }
        XCTAssertFalse(drawsOneShapeForTheGroup("RoundedRectangle(cornerRadius: 4).fill(gradient)"),
                       "谓词在一句**没有**整组形状的代码上返回了 true ⇒ 它恒真，"
                           + "下面两条守卫就是把注释抄了一遍")
        XCTAssertTrue(drawsOneShapeForTheGroup(product),
                      "产品的骨架不再是整组一个形状 ⇒ 上面那颗证人在镜像一种产品已经不采用的画法，"
                          + "`.productRed` 那句『只剩视图归谁这一个差别』作废（改产品就同时改证人，两边都要动）")
        XCTAssertTrue(drawsOneShapeForTheGroup(region(in: witnessFile, named: "private func skeleton(phase:")),
                      "证人回落到每根条各自的形状，而产品是整组一个 ⇒ 两颗视图的绘制负载不再是同一件事："
                          + "产品红与环境带不动之间只剩的那一个差别又多了两个（形状个数、渐变落在谁的坐标系）")
        // R85 / BACKLOG 118：那两行**状态行**是登记表唯一读的东西。它们被删掉时判据本身照样绿
        // （没人断言自己打过字），红要等到闸门读到"这一族整行没说一句话"才出现 ——
        // 而那已经是下一次 CI 的事了。所以这里就地钉住"两条判据各自还在打状态行"。
        // 名字写在被抽取的那个函数里，守卫自己只出现函数名 ⇒ 不会命中守卫自己（R53 那一课）。
        // 两条出口各自都要打一行：能力闸门 skip 那条，与真判完那条。
        // 为什么数**次数**而不是数"有没有出现过"（M461 第一版就是这么逃掉的）：
        // 只断言"函数体里出现过这个串"时，删掉正常路径那一行仍然绿 —— 剩下 skip 分支那一行
        // 把断言喂饱了。而登记表要的恰恰是"判完的那条路也留了字"，所以这里要的是两行。
        XCTAssertEqual(stateLineCount("MOTION_SHIMMER_STATE", in: witnessFile,
                                      named: "func testSkeletonSweepActuallySweeps("), 2,
                       "循环判据的两条出口（能力闸门 skip / 真判完）不再各自打一行状态 ⇒ "
                           + "登记表那一族今天说没说过话，只剩闸门在下一轮才看得见")
        XCTAssertEqual(stateLineCount("MOTION_SHIMMER_BAND_STATE", in: witnessFile,
                                      named: "func testSkeletonSweepIsOneBand("), 2,
                       "位置判据的两条出口不再各自打一行状态 ⇒ 同上，而且这一族是 R84 才进表的，"
                           + "消失起来最容易无声")
    }

    /// R84：位置那把尺自己的真值表。它判的是"同一帧里三根条的亮斑在同一条竖线上吗"，
    /// 而这句话有四种**都不该判成"整组一条带"**的形状：没有可用帧、亮带根本没走、
    /// 可用帧太少、两个地板之间分不开。少一格，那一格就成了空支票。
    func testTheBandPositionRulerTruthTable() throws {
        let widths = Self.barWidthPoints(viewWidthPoints: 420)
        XCTAssertEqual(widths.count, 3, "条宽是从 `SkeletonMotion.barFractions` 推的，不是这里写的三个数")
        // ① 整组一条带：每帧三根条同绝对中心，而且它一路扫过去。
        XCTAssertEqual(Self.bandReading(frames: [[100, 100, 100], [130, 131, 129], [60, 60, 61]],
                                       widths: widths).verdict, .oneBand,
                       "同绝对中心、有行程的卷子必须判成整组一条带")
        // ② 每根条各扫各的：中心与条宽成正比（R83 手量到的就是这一种，绝对差 170pt）。
        XCTAssertEqual(Self.bandReading(frames: [[88, 181, 134], [50, 110, 75], [20, 40, 30]],
                                       widths: widths).verdict, .fanOut,
                       "中心按条宽各自放大的卷子必须判成各扫各的 —— 这一格是这条判据的反对照")
        // ③ 没有可用帧 ⇒ 不许猜成任何一种画法。
        XCTAssertEqual(Self.bandReading(frames: [], widths: widths).verdict, .noFrames,
                       "0 帧可用时说『整组一条带』或『各扫各的』都是凭空的结论")
        // ④ 正对照失败：三根条的峰值帧帧相同（静止画面也能读成"散布 0pt"）。
        let frozen = Self.bandReading(frames: [[100, 100, 100], [101, 101, 100], [100, 101, 101]],
                                      widths: widths)
        XCTAssertEqual(frozen.verdict, .notJudged,
                       "亮带一步没走 ⇒ 那是没在动，不是『一条带』。这一格拦住的是『散布小就算过』")
        XCTAssertTrue(frozen.reason.contains("正对照"), "④ 的理由必须点名正对照失败，不许和⑤混成一句")
        // ⑤ 可用帧太少。
        let tooFew = Self.bandReading(frames: [[100, 100, 100], [150, 150, 150]], widths: widths)
        XCTAssertEqual(tooFew.verdict, .notJudged, "两帧撑不起『一路扫过去』这句话")
        XCTAssertTrue(tooFew.reason.contains("帧"), "⑤ 的理由要说清缺的是帧数")
        // ⑥ 落在两个地板之间 ⇒ 分不开（比"判错"更诚实的红）。
        let middle = Self.bandReading(frames: [[100, 108, 116], [60, 68, 76], [80, 88, 96]], widths: widths)
        XCTAssertEqual(middle.verdict, .notJudged,
                       "绝对散布 16pt 既不超过一条带的天花板，也不到各扫各的下限 ⇒ 必须说分不开")
        // ⑦ 两个地板不许互相取消：天花板必须明显低于下限，否则上面⑥那一格会被判成其中之一。
        XCTAssertLessThan(Self.oneBandCeilingPoints, Self.fanOutFloorPoints,
                          "地板调到能互相覆盖，这把尺就什么都能判")
        // ⑧ 两把尺必须**反向**：修好之后"绝对"该一致、"归一化"该分家；修之前正好相反。
        //    这一格钉的是"我判的是哪一种画法"，不是"我读到了几个数"。
        let oneBandReading = Self.bandReading(frames: [[100, 100, 100], [130, 131, 129], [60, 60, 61]],
                                              widths: widths)
        let fanOutReading = Self.bandReading(frames: [[88, 181, 134], [50, 110, 75], [20, 40, 30]],
                                            widths: widths)
        XCTAssertGreaterThan(oneBandReading.normalizedSpread, fanOutReading.normalizedSpread,
                             "整组一条带那份的归一化散布必须**大**（同一列在三种条宽上是三个比例）——"
                                 + "如果它比各扫各那份还小，说明两把尺读反了，或者位置放法根本不是这两种之一")
        XCTAssertLessThan(fanOutReading.normalizedSpread, 0.05,
                          "各扫各那份的归一化散布必须接近 0（R83 实测 0.003）⇒ 它才是『每根条自己的单位空间』")
        // ⑨–⑫ 处置那一层：谁能签"这台机器判不了位置"。这四格防的是同一件事 ——
        //     把"环境读不出"与"产品读得出"混成一句话，R82/R83 的 CI 已经为这句话翻过一次面。
        XCTAssertEqual(Self.bandAdjudication(product: .oneBand, witness: .oneBand), .ok,
                       "⑨ 证人读得出、产品判成一条带 ⇒ 判绿")
        XCTAssertEqual(Self.bandAdjudication(product: .fanOut, witness: .oneBand), .productRed,
                       "⑩ 同一台机器上高对比那颗读得出亮带位置，而产品读成各扫各的 ⇒ 红在产品")
        XCTAssertEqual(Self.bandAdjudication(product: .noFrames, witness: .oneBand), .productRed,
                       "⑪ 证人读得出而产品一帧都拍不出 ⇒ 那也是产品的账，不许当成环境问题放行")
        XCTAssertEqual(Self.bandAdjudication(product: .oneBand, witness: .noFrames), .notRunEnvironment,
                       "⑫ 连证人都读不出可用帧时，产品那句『整组一条带』不许当真 —— 没人看见过亮带")
        XCTAssertEqual(Self.bandAdjudication(product: .notJudged, witness: .notJudged), .notRunEnvironment,
                       "⑬ 证人落在『分不开』也不许签字：可判决只有两种画法，其余都是没人看见")
        // ⑭⑮ 循环那一族的处置**只能收窄、不能放大指控**（BACKLOG 119 的形状）：
        //      R82/R83 的 CI 证明那一支会在两轮之间翻面，所以它 false 的时候位置这一族一律不判，
        //      哪怕证人读得出、哪怕产品读成分家 —— 定罪要由一个稳定的读数来签。
        XCTAssertEqual(Self.bandAdjudication(product: .oneBand, witness: .oneBand, loopCapable: false),
                       .notRunEnvironment,
                       "⑭ 循环判不动的时候，位置那句好消息也不许当真（否则同一件事两台机器两个结论）")
        XCTAssertEqual(Self.bandAdjudication(product: .fanOut, witness: .oneBand, loopCapable: false),
                       .notRunEnvironment,
                       "⑮ 同一个方向的另一支：循环判不动时连『红』都不许判 —— 只能不说，不能反过来定罪")
        emit("BAND_TRUTH_TABLE 一条带=\(oneBandReading.verdict.rawValue) 各扫各=\(fanOutReading.verdict.rawValue) "
            + "空=\(Self.bandReading(frames: [], widths: widths).verdict.rawValue) "
            + "静止=\(frozen.verdict.rawValue) 帧少=\(tooFew.verdict.rawValue) 分不开=\(middle.verdict.rawValue) "
            + "处置=ok/红/红/未跑(⑫)/未跑(⑬)/未跑(⑭⑮ loopCapable=false) "
            + "一条带归一化=\(String(format: "%.3f", oneBandReading.normalizedSpread)) "
            + "各扫各归一化=\(String(format: "%.3f", fanOutReading.normalizedSpread)) "
            + "绝对散布=\(String(format: "%.1f", oneBandReading.maxSpreadPoints))/\(String(format: "%.1f", fanOutReading.maxSpreadPoints))pt "
            + "行程=\(String(format: "%.1f", oneBandReading.travelPoints))/\(String(format: "%.1f", fanOutReading.travelPoints))pt ⇒ 15 格")
    }

    /// R82 / BACKLOG 110：分辨率那条闸门改吃 **P75**，一个离群样本不许翻掉它。
    func testTheClockGateUsesARobustStatisticNotTheSingleWorstSample() throws {
        // 本机三遍实测：`detail-kind-change` 的事件内最粗在 61ms 与 81ms 之间跳，
        // 而那条线是 0.5×声明(160ms)=80ms ⇒ 同一份代码在同一台机器上一臂红、一臂 not-run。
        let cleanRun: [Double] = [50, 51, 52, 53]
        let outlierRun: [Double] = [50, 51, 52, 81]
        XCTAssertEqual(Self.percentileMilliseconds(cleanRun, 0.75), 52, accuracy: 0.01)
        XCTAssertEqual(Self.percentileMilliseconds(outlierRun, 0.75), 52, accuracy: 0.01,
                       "多了一个 81ms 的离群样本，P75 不该跟着跳 ⇒ 它才配当闸门")
        XCTAssertGreaterThan(outlierRun.max()!, cleanRun.max()!,
                             "而最大值确实会跳 —— 这一格钉的是『旧闸门为什么会翻脸』")
        // 同一个 elapsed / 同一个声明，两种采样历史必须给同一个判定
        let declared = 160.0
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 198,
                                        clockIntervalMilliseconds: Self.percentileMilliseconds(cleanRun, 0.75),
                                        declaredDurationMilliseconds: declared, changedFrames: 3),
                       Self.judgeMotion(elapsedMilliseconds: 198,
                                        clockIntervalMilliseconds: Self.percentileMilliseconds(outlierRun, 0.75),
                                        declaredDurationMilliseconds: declared, changedFrames: 3),
                       "一次 81ms 的抓帧停顿就把这一臂从『判得出』推到『这台机器看不见』⇒ 判的是时钟，不是产品")
        // 边界仍然成对：P75 真变粗了就必须报 clockTooCoarse（不许把闸门偷偷放宽）
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 198, clockIntervalMilliseconds: 81,
                                        declaredDurationMilliseconds: declared, changedFrames: 3),
                       .clockTooCoarse, "81ms > 0.5×160ms ⇒ 仍然该报『切不出过程』，这条线没被移动")
        XCTAssertEqual(Self.judgeMotion(elapsedMilliseconds: 198, clockIntervalMilliseconds: 80,
                                        declaredDurationMilliseconds: declared, changedFrames: 3), .transition,
                       "正好等于 0.5×声明 的必须还在中间档里判得出（`<=` 被写成 `<` 就红在这里）")
        XCTAssertEqual(Self.percentileMilliseconds([], 0.75), -1, "空样本必须读 −1（没量到不等于 0ms）")
        XCTAssertEqual(Self.percentileMilliseconds([44], 0.75), 44, "只有一个样本时它就是答案")
        emit("CLOCK_GATE_P75 干净=[50 51 52 53] 离群=[50 51 52 81] 两个 P75 相同而最大值差 28ms")
    }

    func testTransitionsAreActuallyRunning() throws {
        try skipUnlessEnabledAndCapable()
        var rows: [(name: String, span: Int)] = []      // 每个场景都进 MOTION_SUMMARY，形状不许因为"看不见"而少一项
        var judged = 0
        var notRun: [String] = []
        // 证人**按需请一次**：拍一条已知 150ms 的淡入要 75 帧 ≈ 2.4s（runner 上更多），
        // 而这一卷只有真读成跳变的那一臂需要它。缓存成卷级的一份，是因为同一台机器上
        // 每条臂问的本来是同一句话 —— 问两遍会给出两个答案，那才是新的抖动源。
        var witness: FadeClockReading?

        // R355 / BACKLOG 429：先把这台机器「减弱动态」的三个来源打出来。
        // runner 上 `empty-state` 从 R348 起只变 1 帧，而开关的任一来源为真就会走归零分支 ——
        // 不打出这几个布尔值，下一轮读 CI 仍只能猜「大概是 reduce」。
        emit("MOTION_REDUCE_SOURCES setting=\(NSWorkspace.shared.accessibilityDisplayShouldReduceMotion) "
            + "voiceOver=\(NSWorkspace.shared.isVoiceOverEnabled) "
            + "catalog=\(MotionCatalog.motionShouldBeReduced) "
            + "override=\(MotionCatalog.overrideReduceMotion.map { $0 ? "true" : "false" } ?? "nil")")

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
            // R82 / BACKLOG 110：这一段交**两个**统计量 —— 最粗那一次只当读数，
            // 决定"这把尺切不切得出过程"的换成 **P75**。理由不是审美，是三次本机读数：
            // `detail-kind-change` 的事件内最粗在 61ms 与 81ms 之间跳，而那条线是 0.5×160=80ms
            // ⇒ 同一份代码在同一台机器上一臂红、一臂 not-run，而中位数一直是 50–51ms。
            // 一个单样本统计当闸门，判的就是采样相位，不是产品。
            let runGaps = Self.intervalsInsideChangedRun(stamps: film.motionStamps, fractions: fractions)
            let worstInRun = runGaps.max()
            let clockInRun = runGaps.isEmpty ? -1 : Self.percentileMilliseconds(runGaps, 0.75)
            // 每个场景都进 MOTION_SUMMARY（哪怕这一条今天判不了）：CI 那一步与它的自测夹具
            // 都按"三个键都在"的形状读，少一个键会让下游把"没测"读成"测了且为 0"。
            rows.append((scenario.name, span))
            // 这一行打在**所有能力闸门之前**（R53 那一课：结论行掉在 skip 之后就等于没跑）。
            // 三个峰值各自的用处：`亮度峰值` 是 R77 之前唯一被读过的那根，`并集峰值` 是现在
            // `fractions`/`过渡帧数` 真正读的那根 —— 两列都留着，才能当场看出这次加轴有没有改读数。
            emit("MOTION_AXIS \(scenario.name) " + Self.axisSummaryLine(frames))
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
                + "事件内P75=\(clockInRun < 0 ? "无" : String(format: "%.0f", clockInRun))ms "
                + "变化段时长=\(elapsed.map { String(format: "%.0f", $0) } ?? "无")ms 过渡帧数=\(span) "
                + "时刻ms=[\(gaps.map(String.init).joined(separator: " "))] "
                + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
            writeStrip(scenario.name, frames)
            guard let elapsed, let worstInRun, clockInRun > 0 else {
                notRun.append(scenario.name)
                emit("MOTION_NOT_RUN=no-changed-run \(scenario.name)：读不出「变化段」的时长 ⇒ 既不判红也不判绿")
                continue
            }
            switch Self.judgeMotion(elapsedMilliseconds: elapsed,
                                    clockIntervalMilliseconds: clockInRun,
                                    declaredDurationMilliseconds: scenario.declaredDurationMilliseconds,
                                    changedFrames: span) {
            case .clockTooCoarse:
                notRun.append(scenario.name)
                emit("MOTION_NOT_RUN=clock-coarse-in-window \(scenario.name)：事件那一段 P75 采样 "
                    + "\(String(format: "%.0f", clockInRun))ms（最粗那一次 \(String(format: "%.0f", worstInRun))ms）、"
                    + "整段过渡只有 \(Int(scenario.declaredDurationMilliseconds))ms（门槛 0.3×声明）⇒ "
                    + "这把尺在过渡正在演的那一段切不出「过程」这个概念，既不判红也不判绿"
                    + Self.grabAttributionLabel(clockIntervalMilliseconds: worstInRun,
                                                worstGrabMilliseconds: film.worstGrabMilliseconds))
            case .jump:
                // R75 / BACKLOG 104 的答案在这一格。一条 `.jump` 是**产品断言**，而它站在一条时长读数上；
                // 变化段只有两帧时，那个"时长"就是一次采样间隔 —— 同一条淡入时钟在 runner 上
                // 两遍给出 32ms（红）与 ≥60ms（绿），`MOTION_SUMMARY notice-banner=2` 两边一样
                // ⇒ 判的是采样相位，不是产品（run 38726667469 vs 38726991211，R74 读）。
                // 谁有资格说"这台机器的通道带不动一条 150ms 的淡入"？只有证人 —— 而 R72 把节拍
                // 换成 0.004 之后它**第一次有资格**：`证人采样≈32ms 可分数段=4 合格=是 判定=拍成跳变`，
                // 两遍都一样。所以这一格从今天起先问证人，再决定是红还是 not-run。
                // **只有红这一支问证人**：绿不需要借口（看见了一段够长的变化，那是正面证据），
                // 而"没看见"必须先确认这台机器看不看得见 —— 缺席的证据不是缺席的证据。
                if witness == nil { witness = fadeClock() }
                let clock = witness!
                let fadeDeclared = Int(FadeClockView.declaredDurationMilliseconds)
                let segments = Self.resolvableFrames(durationMilliseconds: Double(fadeDeclared),
                                                     sampleMilliseconds: clock.samplingMilliseconds)
                let qualifies = clock.qualifies(declaredDurationMilliseconds: fadeDeclared)
                emit("MOTION_JUMP_WITNESS \(scenario.name) 证人采样≈\(clock.samplingMilliseconds)ms "
                    + "声明=\(fadeDeclared)ms 可分数段=\(segments) 合格=\(qualifies ? "是" : "否") "
                    + "判定=\(Self.fadeClockLabel(clock.verdict))（本臂 变化段=\(span) 帧 "
                    + "时长=\(String(format: "%.0f", elapsed))ms 事件内最粗=\(String(format: "%.0f", worstInRun))ms "
                    + "声明=\(Int(scenario.declaredDurationMilliseconds))ms）")
                switch Self.jumpAdjudication(clock: clock.verdict, witnessQualifies: qualifies) {
                case .productRed:
                    judged += 1
                    XCTFail("\(scenario.name)：画面只变了 \(String(format: "%.0f", elapsed))ms 就停了，"
                        + "而声明的过渡是 \(Int(scenario.declaredDurationMilliseconds))ms（事件内最粗采样 "
                        + "\(String(format: "%.0f", worstInRun))ms）⇒ 这是一帧跳变，不是过渡。"
                        + "而证人今天说这台机器**看得见** \(fadeDeclared)ms 的淡入"
                        + "（采样≈\(clock.samplingMilliseconds)ms、中间态 \(clock.intermediate) 帧）⇒ 这句不是环境的借口")
                case .notRunChannel:
                    notRun.append(scenario.name)
                    emit("MOTION_NOT_RUN=witness-snaps-here \(scenario.name)：本臂只变了 "
                        + "\(String(format: "%.0f", elapsed))ms（\(span) 帧），可这台机器把一条**已知** "
                        + "\(fadeDeclared)ms 的淡入也拍成跳变（证人采样≈\(clock.samplingMilliseconds)ms、"
                        + "可分数段=\(segments)、合格=是）⇒ 两帧的『时长』就是一次采样间隔，"
                        + "既不能判产品跳变，也不能判它演了（BACKLOG 77 路 b：让判据不吃帧数，才是解药）")
                case .witnessUnqualified:
                    judged += 1
                    XCTFail("\(scenario.name)：本臂读成一帧跳变，而证人采得不够细，给不了『这台机器看不见』"
                        + "这个签字（证人≈\(clock.samplingMilliseconds)ms、声明 \(fadeDeclared)ms "
                        + "⇒ 只切得出 \(segments) 段，少于『中间态 + 1』那三段的地板）。"
                        + "红着，去把证人降成本 / 加密采样（BACKLOG 104 就是这一格）；"
                        + "把 skip 当解药等于把『我没看清』写成『它没动』")
                case .witnessDead:
                    judged += 1
                    XCTFail("淡入时钟证人自己读不出那条已知淡入的过程（跨度=\(String(format: "%.3f", clock.span)) "
                        + "中间态帧数=\(clock.intermediate) 帧数=\(clock.frames)），而产品这一臂也读不出 ⇒ "
                        + "两条没有一条能证明这把尺看得见淡入。判红而不 skip：坏的是证人，得有人去修它")
                }
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

    /// R355 / BACKLOG 429：**减弱动态下的空态仍然淡** —— runner 上那朵红的本机复现。
    ///
    /// 为什么必须在本机用注入开关跑：这台 Mac 的 reduce-motion 是关的，所以上面那条主卷
    /// 永远走不到 `slideAnimation` 的归零分支；而 runner 从 R348 起就走在那里
    /// （`MOTION_NOT_RUN=witness-snaps-here empty-state`、本臂只变 36ms/1 帧，
    /// 改前 run 40186459168 同一臂是 3 帧）。那一支是**产品事实**：开了「减弱动态效果」的用户
    /// 看到的是内容一帧硬切，不是"这台机器看不见"。注入 `overrideReduceMotion = true` 之后，
    /// 产品读到的就是用户打开那个开关时的那条路径。
    ///
    /// 这条判据的牙：落刀把产品那一行改回 `FilterPillMotion.slideAnimation` ⇒ 本卷必须红（1 帧）；
    /// 还原 ⇒ 必须绿（≥3 帧）。它不读源码，只读这一卷的逐帧变化。
    func testEmptyStateStillFadesWhenMotionIsReduced() throws {
        try skipUnlessEnabledAndCapable()
        let saved = MotionCatalog.overrideReduceMotion
        MotionCatalog.overrideReduceMotion = true
        defer { MotionCatalog.overrideReduceMotion = saved }

        let scenario = Scenario.emptyState()
        let film = record(scenario)
        defer { writeStrip("empty-state-reduce", film.motionFrames) }
        emit("MOTION_REDUCE empty-state 注入=overrideReduceMotion=true "
            + "声明=\(Int(scenario.declaredDurationMilliseconds))ms 帧数=\(film.motionFrames.count)")
        XCTAssertGreaterThan(film.motionFrames.count, 4,
                             "\(scenario.name)：只抓到 \(film.motionFrames.count) 帧，判据没有对照物")
        guard film.clockIsWarm else {
            emit("MOTION_REDUCE_SKIP=clock-not-warm empty-state(reduce)：注入那一卷采样还是冷的 ⇒ 不判产品")
            throw XCTSkip("MOTION_REDUCE_SKIP=clock-not-warm empty-state(reduce)：这一卷的钟没热，量不到过程")
        }
        let fractions = Self.deltas(film.motionFrames)
        let span = Self.transitionFrameCount(fractions)
        let elapsed = Self.changedSpanElapsedMilliseconds(stamps: film.motionStamps, fractions: fractions)
        let runGaps = Self.intervalsInsideChangedRun(stamps: film.motionStamps, fractions: fractions)
        let clockInRun = runGaps.isEmpty ? -1 : Self.percentileMilliseconds(runGaps, 0.75)
        emit("MOTION_REDUCE empty-state 过渡帧数=\(span) "
            + "变化段时长=\(elapsed.map { String(format: "%.0f", $0) } ?? "无")ms "
            + "事件内P75=\(clockInRun < 0 ? "无" : String(format: "%.0f", clockInRun))ms "
            + "逐帧=[\(fractions.map { String(format: "%.3f", $0) }.joined(separator: " "))]")
        guard let elapsed, clockInRun > 0 else {
            throw XCTSkip("MOTION_REDUCE_SKIP=no-changed-run empty-state(reduce)：这一卷里读不出变化段")
        }
        // 判法与主卷**同一颗**（`judgeMotion`）：读时长与事件内 P75，不读帧数。
        let verdict = Self.judgeMotion(elapsedMilliseconds: elapsed,
                                       clockIntervalMilliseconds: clockInRun,
                                       declaredDurationMilliseconds: scenario.declaredDurationMilliseconds,
                                       changedFrames: span)
        guard verdict != .clockTooCoarse else {
            throw XCTSkip("MOTION_REDUCE_SKIP=clock-coarse-in-window empty-state(reduce)：P75=\(String(format: "%.0f", clockInRun))ms")
        }
        XCTAssertEqual(verdict, .transition,
                       "减弱动态效果下空态只变了 \(String(format: "%.0f", elapsed))ms（\(span) 帧，P75="
                       + "\(String(format: "%.0f", clockInRun))ms）⇒ 判成跳变或没在演。"
                       + "R348 用 `slideAnimation` 当驱动，而它在 reduce 下返回 .linear(duration: 0)；"
                       + "runner 从 R348 起就是这样（1 帧/36ms，BACKLOG 429）")
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
        // （本轮还犯过一次可笑的错：我在**还没读到 `clockIntervalMilliseconds` 之前**，
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
                + " ｜A 臂" + Self.grabAttributionLabel(clockIntervalMilliseconds: worstA,
                                                        worstGrabMilliseconds: onFilmA.worstGrabMilliseconds)
                + " ｜B 臂" + Self.grabAttributionLabel(clockIntervalMilliseconds: worstB,
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

    /// 某个成员体内出现了几次这个串。**先取区域再数**，所以守卫自己写下的字面量不算数
    /// （R53 那一课：扫自身源码的守卫，先把守卫自己摘掉）。
    private func stateLineCount(_ marker: String, in code: String, named declaration: String) -> Int {
        region(in: code, named: declaration).components(separatedBy: marker).count - 1
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
    // MARK: - BACKLOG 155：⑤ 那一条判据的两种解释要能被分开（R130）

    /// 「省下的抓帧成本有没有进采样率」这把尺在 runner 上连红三跑（155：
    /// 28.44>25.38 / 32.49>27.46 / 32.16>31.81），而两种解释一直**分不开**，
    /// 因为行内只有比值没有绝对量（① 带那一臂在这台机器上真的更慢；
    /// ② 调度把两臂一起拖住 ⇒ 这条判据在 CI 上量的不是它声称的东西）。
    ///
    /// 这里交出的是那个绝对量本身能做的分解：**间隔 − 抓帧 = 这台机器的调度地板**。
    /// 没有新阈值（155 的下一步只欠读数，不欠一条我猜出来的线）。
    ///
    /// 关键形状：`间隔 < 抓帧` 物理上不该发生（一次采样里必然包含它的抓帧），
    /// 它一旦发生就说明**两个量不是同一卷测的** —— 这里确实会：间隔取
    /// `motionStamps` 相邻帧的中位，抓帧中位取**整卷**（含非运动帧）。
    /// 那种情况下这一行只能报「无从分解」，不许拿它给 ①/② 任何一方定罪。
    enum BandIntervalFacts: Equatable {
        case unpainted
        case notComparable(which: String)
        case decomposable(bandOverhead: Double, fullOverhead: Double, bandFiner: Bool)
    }

    static func bandIntervalFacts(bandInterval: Double, fullInterval: Double,
                                  bandGrab: Double, fullGrab: Double) -> BandIntervalFacts {
        // 「没有两帧」这一格由 `medianInterval` 自己报的哨兵值签 —— 注意它是
        // `.greatestFiniteMagnitude` 而**不是** `infinity`，用 `isInfinite` 判会静默漏掉整格
        // （真值表前两行就是钉这条的）。
        if bandInterval == .greatestFiniteMagnitude || fullInterval == .greatestFiniteMagnitude {
            return .unpainted
        }
        var who: [String] = []
        if bandInterval < bandGrab { who.append("带") }
        if fullInterval < fullGrab { who.append("整窗") }
        if !who.isEmpty { return .notComparable(which: who.joined(separator: "/")) }
        return .decomposable(bandOverhead: bandInterval - bandGrab,
                             fullOverhead: fullInterval - fullGrab,
                             bandFiner: bandInterval <= fullInterval)
    }

    static func bandIntervalFactsText(_ facts: BandIntervalFacts) -> String {
        switch facts {
        case .unpainted: return "无从分解=任何一臂没有两帧"
        case .notComparable(let which):
            return "无从分解=间隔<抓帧（\(which)）⇒ 两个量不是同一卷测的，不给 ①/② 定罪"
        case .decomposable(let bandOverhead, let fullOverhead, let bandFiner):
            return String(format: "带地板=%.2fms 整窗地板=%.2fms 谁细=%@",
                          bandOverhead, fullOverhead, bandFiner ? "带" : "整窗")
        }
    }

    /// 与 171 那把键同形（`arch/macOS major.minor/1x|2x`）：155 要问的是
    /// 「这一臂在哪台机器上判不了」，而跨机器混着读数正是 171 那轮学到的错。
    static func filmstripMachineKey() -> String {
        #if arch(arm64)
        let arch = "arm64"
        #else
        let arch = "x86_64"
        #endif
        let v = ProcessInfo.processInfo.operatingSystemVersion
        let scale = (NSScreen.main?.backingScaleFactor ?? 0) >= 1.75 ? "2x" : "1x"
        return "\(arch)/macOS \(v.majorVersion).\(v.minorVersion)/\(scale)"
    }

    func testBandIntervalFactsRulerIsATruthTable() throws {
        // 每一行都指定「谁细」与「能不能分解」—— 这两件事必须各判各的（同一条红只准认一种病）。
        XCTAssertEqual(.unpainted,
                       Self.bandIntervalFacts(bandInterval: .greatestFiniteMagnitude,
                                              fullInterval: 20, bandGrab: 10, fullGrab: 20),
                       "任何一臂没有两帧 ⇒ 只能记没判，不许当成『带更细』")
        XCTAssertEqual(.unpainted,
                       Self.bandIntervalFacts(bandInterval: 20, fullInterval: .greatestFiniteMagnitude,
                                              bandGrab: 10, fullGrab: 20),
                       "另一臂同样要能单独判出来（两臂共用一个分支就是没判）")
        XCTAssertEqual(.notComparable(which: "带"),
                       Self.bandIntervalFacts(bandInterval: 9, fullInterval: 30, bandGrab: 26, fullGrab: 20),
                       "带的间隔比它的抓帧还短 ⇒ 两个量不同卷，这一行不给任何一方定罪")
        XCTAssertEqual(.notComparable(which: "带/整窗"),
                       Self.bandIntervalFacts(bandInterval: 9, fullInterval: 12, bandGrab: 26, fullGrab: 44),
                       "两臂都不同卷 ⇒ 名字要把两臂都点出来")
        XCTAssertEqual(.decomposable(bandOverhead: 2, fullOverhead: 5, bandFiner: true),
                       Self.bandIntervalFacts(bandInterval: 12, fullInterval: 30, bandGrab: 10, fullGrab: 25))
        XCTAssertEqual(.decomposable(bandOverhead: 20, fullOverhead: 1, bandFiner: false),
                       Self.bandIntervalFacts(bandInterval: 30, fullInterval: 26, bandGrab: 10, fullGrab: 25),
                       "『带更贵』这一格必须能被判出来 —— 155 的红正是这一格，它不能被前一条吞掉")
        // 出口必须互不相同，否则「无从分解」与「带更贵」会共用一个词而读的人分不出来。
        let words = [
            Self.bandIntervalFactsText(.unpainted),
            Self.bandIntervalFactsText(.notComparable(which: "带")),
            Self.bandIntervalFactsText(.decomposable(bandOverhead: 2, fullOverhead: 5, bandFiner: true)),
            Self.bandIntervalFactsText(.decomposable(bandOverhead: 8, fullOverhead: 5, bandFiner: false)),
        ]
        XCTAssertEqual(Set(words).count, words.count, "四条结论词互相重复 ⇒ 读数没有区分力")
    }

    // MARK: - BACKLOG 174：⑤ 需要第三个出口「这台机器判不了」（R133）

    /// ⑤ 原来只有两个出口（通过 / 红），而 runner 上的真相需要第三个。
    ///
    /// 四跑读数：红 `28.44>25.38`、`32.49>27.46`、`32.16>31.81`，绿 `26.72≤38.44`（run `39036587208`）。
    /// 同一次绿跑自己印出的分解：`带地板=21.27ms 整窗地板=23.37ms`，而抓帧只省了 9.63ms
    /// ⇒ **间隔里约八成是调度**，胜负由剩下那两成决定 —— 也就是这条"A 臂比 B 臂细"在那台机器上
    /// 量的不是它声称的东西（155 的 ② 那一读法，第一次由尺自己的数支持，而不是由我的推断支持）。
    ///
    /// 所以这里**不加新阈值**：前提由同一次运行量出来的两个数比出来 ——
    /// 两臂各自地板（`间隔 − 抓帧`）里较小的那个，如果比"抓帧省下的钱"还大，
    /// 那么这一次跑的间隔就不可能由抓帧成本决定，这一跑判不了这件事。
    ///
    /// 「放行地板主导」不会把"根本没省钱"放过去：**省没省钱由 ② 那条判据单独判**
    /// （`bandMedian < fullMedian / bandCaptureSavingFloor`），这里只判"省下的钱有没有进采样率"。
    /// 同一件事只判一次（R83 / U-162），两条判据各自能红。
    enum SamplingRateVerdict: Equatable {
        case unpainted
        case floorDominant(schedulerMilliseconds: Double, savedMilliseconds: Double)
        case finer
        case coarser
    }

    static func samplingRateVerdict(bandInterval: Double, fullInterval: Double,
                                    bandGrab: Double, fullGrab: Double) -> SamplingRateVerdict {
        if bandInterval == .greatestFiniteMagnitude || fullInterval == .greatestFiniteMagnitude {
            return .unpainted
        }
        let saved = fullGrab - bandGrab
        let floor = min(bandInterval - bandGrab, fullInterval - fullGrab)
        if floor > saved { return .floorDominant(schedulerMilliseconds: floor, savedMilliseconds: saved) }
        return bandInterval <= fullInterval ? .finer : .coarser
    }

    static func samplingRateVerdictText(_ verdict: SamplingRateVerdict) -> String {
        switch verdict {
        case .unpainted: return "无从判定=任何一臂读不出相邻帧间隔（探针坏了，不是产品没省到钱）"
        case .floorDominant(let floor, let saved):
            return String(format: "这台机器判不了=调度地板 %.2fms 大于省下的 %.2fms", floor, saved)
        case .finer: return "判到=带更细"
        case .coarser: return "判到=带更粗，且调度地板解释不了"
        }
    }

    /// 两行**真测量**各自落在哪个出口（本机 vs runner）。
    /// 为什么单独一条测试：一条判据的真值表如果全是我编的样本，它就只在样本上成立；
    /// 而这两行是从两次运行里抄回来的数 —— 同一份代码在两台机器上落到不同出口，
    /// 这正是 174 存在的全部理由，值得有它自己的名字（M647 只红在这一条上）。
    func testSamplingRateVerdictMatchesTheTwoRealMeasurements() throws {
        let local = Self.samplingRateVerdict(bandInterval: 9.27, fullInterval: 43.16,
                                             bandGrab: 4.24, fullGrab: 38.17)
        XCTAssertEqual(.finer, local,
                       "本机（run R130 那一跑）：地板 4.99ms 远小于省下的 33.93ms ⇒ ⑤ 照常判")
        let runner = Self.samplingRateVerdict(bandInterval: 26.72, fullInterval: 38.44,
                                              bandGrab: 5.44, fullGrab: 15.07)
        // 十进制字面量相减不保证逐位相等 ⇒ 按带容差的两格判，而不是按整个枚举判相等
        // （`XCTAssertEqual(Double, Double)` 无 accuracy 会把一次正确的测量判成红，U-441）。
        guard case let .floorDominant(runnerFloor, runnerSaved) = runner else {
            return XCTFail("runner（run 39036587208）应当落在『地板主导』，实际是 \(Self.samplingRateVerdictText(runner))")
        }
        XCTAssertEqual(21.28, runnerFloor, accuracy: 0.01)
        XCTAssertEqual(9.63, runnerSaved, accuracy: 0.01)
        XCTAssertNotEqual(local, runner, "同一份代码在两台机器上落到同一个出口 ⇒ 这台机器的差异没被说出来")
    }

    /// 另外三个出口 + 词表互不相同（合成样本，专门用来让"摘掉某一格"能被抓到）。
    func testSamplingRateVerdictIsATruthTable() throws {
        XCTAssertEqual(.coarser,
                       Self.samplingRateVerdict(bandInterval: 20.0, fullInterval: 12.0,
                                                bandGrab: 4.0, fullGrab: 10.0),
                       "带更粗而地板（min(16,2)=2.0）小于省下的 6.0ms ⇒ 必须还能红")
        XCTAssertEqual(.unpainted,
                       Self.samplingRateVerdict(bandInterval: .greatestFiniteMagnitude,
                                                fullInterval: 12.0, bandGrab: 4.0, fullGrab: 10.0))
        XCTAssertEqual(.unpainted,
                       Self.samplingRateVerdict(bandInterval: 12.0,
                                                fullInterval: .greatestFiniteMagnitude,
                                                bandGrab: 4.0, fullGrab: 10.0),
                       "另一臂同样要能单独判出来（U-433 那一族：两臂共用一个分支就是没判）")
        let words = [
            Self.samplingRateVerdictText(.unpainted),
            Self.samplingRateVerdictText(.floorDominant(schedulerMilliseconds: 21.3, savedMilliseconds: 9.6)),
            Self.samplingRateVerdictText(.finer),
            Self.samplingRateVerdictText(.coarser),
        ]
        XCTAssertEqual(Set(words).count, words.count, "四个出口塌成同一个词 ⇒ 读数没有区分力")
    }

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
        emit("MOTION_BAND_SAVING 带中位=\(String(format: "%.2f", bandMedian))ms "
            + "整窗中位=\(String(format: "%.2f", fullMedian))ms 省=\(String(format: "%.2f", fullMedian / max(bandMedian, 0.001)))× "
            + "线=\(Self.bandCaptureSavingFloor)×（严格更便宜；倍数只报不判，R72）")
        XCTAssertGreaterThan(bandMedian, 0, "带那一臂没量到抓帧成本 ⇒ 归因会是 unmeasured，这条对账没有内容")
        XCTAssertLessThan(bandMedian, fullMedian / Self.bandCaptureSavingFloor,
            "带捕获中位 \(String(format: "%.1f", bandMedian))ms 不比整窗 \(String(format: "%.1f", fullMedian))ms 便宜 ⇒ "
                + "`captureRect` 是空操作（两臂成本相同就是这一格的形状）。"
                + "**这里只判方向，不判倍数**：runner 实测 1.70×（26.0 vs 44.4ms）而本机 4× 上下，"
                + "倍数是这台机器的成本结构，不是 rect 有没有生效（R72 / 与 R38 同一条课）。"
                + "该改的是那条建议而不是把地板调低 —— 地板现在停在'方向'这条机器无关的线上")
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
        // 这两个数以前只当断言用、不落读数。R77 把这条尺子从三根通道扩到四根之后，
        // 台账里必须能看见"扩轴前后的同一头差是多少"，否则"没有改坏位置同一性"这句话
        // 只能靠"它绿了"来证明（绿了只说明落在容差里，不说明它没挪）。
        emit("MOTION_BAND_POSITION 同头差=\(String(format: "%.4f", headDiff)) "
            + "另一头差=\(String(format: "%.4f", tailDiff)) 地板=\(String(format: "%.4f", Self.bandMustMatchFullHeadFraction))"
            + "/\(String(format: "%.4f", Self.bandMustDifferFromFullTailFraction))")
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
        //    R191 / BACKLOG 212：这条比较以前用"各自峰值归一化"的计数（`transitionFrameCount(_:)`），
        //    而本文件在 R59 就批评过那种形状（`sharedMovingFloor` 的注释："两块各自归一化 ⇒ 峰值大的那块
        //    被一条更高的绝对线先判停…量的是墨量，不是时间"）。带那一臂只看 48pt 那一条，
        //    每帧变化占比天然比整窗大 ⇒ 它自己的线被抬得更高 ⇒ 两臂比的不是同一个量。
        //    runner 上 14 跑红 3 次、分布显示翻脸的是**整窗那一臂**（3 或 4）而带恒 3 —— 正是这个错形状的形状。
        //    现在：一条绝对线（四臂里最大的峰值 × 同一个比例）套到两臂上；旧口径同时打印，
        //    这样"换口径有没有把真问题藏起来"在日志里看得见（R146：换判据口径要留正对照）。
        let sharedMoving = Self.sharedMovingFloor([
            Self.deltas(bandFirst.motionFrames), Self.deltas(bandSecond.motionFrames),
            Self.deltas(fullFirst.motionFrames), Self.deltas(fullSecond.motionFrames)])
        func sharedCount(_ film: Film) -> Int {
            Self.transitionFrameCount(Self.deltas(film.motionFrames), sharedFloor: sharedMoving)
        }
        let bandShared = max(sharedCount(bandFirst), sharedCount(bandSecond))
        let fullShared = max(sharedCount(fullFirst), sharedCount(fullSecond))
        let bandOld = max(motionFrames(bandFirst), motionFrames(bandSecond))
        let fullOld = max(motionFrames(fullFirst), motionFrames(fullSecond))
        emit("MOTION_BAND_PROCESS 同一条线=\(String(format: "%.4f", sharedMoving)) "
             + "同线口径 带=\(bandShared) 整窗=\(fullShared) "
             + "｜ 旧口径（各自归一化）带=\(bandOld) 整窗=\(fullOld)")
        // 先要"至少看到一帧过程"，再谈两臂比较 —— 否则比较可以在两边都是 0 时成立（M708 实测：
        // 把同线计数改成恒 0，旧的那条 `bandShared ≥ fullShared` 照样绿，因为它退化成 0 ≥ 0）。
        XCTAssertGreaterThanOrEqual(bandShared, 1,
            "同一条绝对线（\(String(format: "%.4f", sharedMoving))）下带那一臂看到 0 帧过渡 ⇒ "
                + "『收窄还能看清过程』这句话没有内容，而两臂比较会退化成 0 ≥ 0 的装饰"
                + "（旧口径同时打印在 MOTION_BAND_PROCESS 里：带=\(bandOld) 整窗=\(fullOld)）")
        XCTAssertGreaterThanOrEqual(bandShared, fullShared,
            "同一条绝对线（\(String(format: "%.4f", sharedMoving))）下，带那一臂看到 \(bandShared) 帧过渡，"
                + "少于整窗那一臂的 \(fullShared) ⇒ 采样变细没换来过程，这一臂仍然只能记 not-run，那这条路就白走了。"
                + "旧口径同时打在 MOTION_BAND_PROCESS 里（带=\(bandOld) 整窗=\(fullOld)），换口径没藏东西")
        // ⑤ 采样必须真的变细（这才是要的目的：让那一臂从 clock-coarse 变成判得到）。
        //    结论行打在闸门**之前**（R53 那条规矩）：这一格在 runner 上会红，
        //    红了之后日志里必须还能看见"到底是哪一个量把两臂分开的"（BACKLOG 155 欠的就是这句）。
        //    断言与读数吃同一颗尺（`bandInterval` / `fullInterval` 就是下面比较的那两个数）。
        let bandInterval = medianInterval(bandSecond)
        let fullInterval = medianInterval(fullSecond)
        let intervalFacts = Self.bandIntervalFacts(bandInterval: bandInterval, fullInterval: fullInterval,
                                                   bandGrab: bandMedian, fullGrab: fullMedian)
        emit("MOTION_BAND_INTERVAL 机器=\(Self.filmstripMachineKey()) "
             + "带间隔=\(String(format: "%.2f", bandInterval))ms "
             + "整窗间隔=\(String(format: "%.2f", fullInterval))ms "
             + "带抓帧=\(String(format: "%.2f", bandMedian))ms "
             + "整窗抓帧=\(String(format: "%.2f", fullMedian))ms ｜ "
             + Self.bandIntervalFactsText(intervalFacts))
        // ⑤′ 三个出口（BACKLOG 174）：判到"更细"、判到"更粗且调度解释不了"、这台机器判不了。
        //     前提不是新阈值，是同一次运行量出来的两个数之比（见 `samplingRateVerdict` 的理由）。
        let samplingVerdict = Self.samplingRateVerdict(bandInterval: bandInterval, fullInterval: fullInterval,
                                                       bandGrab: bandMedian, fullGrab: fullMedian)
        emit("MOTION_BAND_SAMPLING_VERDICT 机器=\(Self.filmstripMachineKey()) "
             + "出口=\(Self.samplingRateVerdictText(samplingVerdict)) "
             + "｜ 省没省钱由 ② 单独判（那里已经报过 \(String(format: "%.2f", fullMedian / max(bandMedian, 0.001)))×），"
             + "这里放行『地板主导』不会把没省钱放过去")
        switch samplingVerdict {
        case .coarser:
            XCTFail("带捕获之后整卷中位间隔反而更粗，而这一跑的调度地板解释不了它（地板 ≤ 省下的钱）"
                + " ⇒ 省下的钱没进采样率，这一臂仍然判不了（\(Self.samplingRateVerdictText(samplingVerdict))）")
        case .unpainted:
            XCTFail("任何一臂读不出相邻帧间隔 ⇒ 这条 A/B 没有对象，是探针坏了而不是产品没省到钱")
        case .floorDominant, .finer:
            break
        }
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
                    + "整卷中位间隔 44–45ms），而登记表仍然要求 dismiss 那一臂判到"
                    + "（notice-banner 从 R75 起按实测放行，理由 witness-snaps-here 带 run 号，见下面那格）"
                    + "⇒ 回到 R52 那种「两台机器都判不到」的形状，只是这次会红在 UNDERCOVERED")
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
        // 登记表与这条守卫必须同向。R75 之后不再要求"两臂都 must_judge=true"，
        // 而是要求一件更准的事：**放宽必须带着证据写在同一份文件里**（登记的理由 + 一个 run 号），
        // 否则这条守卫就是在替一次悄悄发生的降级背书。
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
        func registryBlock(_ arm: String) -> String {
            guard let start = registry.range(of: "\"\(arm)\": {") else { return "" }
            let rest = String(registry[start.upperBound...])
            guard let end = rest.range(of: "\n    },") else { return rest }
            return String(rest[rest.startIndex..<end.lowerBound])
        }
        let dismissBlock = registryBlock("notice-banner-dismiss")
        XCTAssertFalse(dismissBlock.isEmpty, "扫不到 notice-banner-dismiss 的登记块 ⇒ 下面两条是空转的")
        XCTAssertTrue(dismissBlock.contains("\"must_judge\": true"),
                      "登记表里 notice-banner-dismiss 不是 must_judge=true ⇒ 带捕获白做："
                          + "判得到也没人要求它判到，掉回 not-run 时闸门不会红")
        let bannerBlock = registryBlock("notice-banner")
        XCTAssertFalse(bannerBlock.isEmpty, "扫不到 notice-banner 的登记块 ⇒ 上面那格是空转的")
        if bannerBlock.contains("\"must_judge\": false") {
            // R75 的形状：这一臂允许判不到，但**必须**把放行所依据的理由与 run 号写在这同一格里。
            // 理由要在 `allowed_not_run_reasons` 那个**数组里**找，不能整块 `contains` ——
            // M395 实测：把数组里那一项删掉之后，这一臂的 note 仍然写着
            // `MOTION_NOT_RUN=witness-snaps-here notice-banner`（那是在**解释**这条放宽），
            // 于是整块 contains 的写法被说明文字喂饱、当场逃掉。
            // 与 R55 的 M276、R79 的"守卫命中自己写下的名字"同族：**守卫读的是字段，不是散文。**
            let reasons = bannerBlock.components(separatedBy: "\"allowed_not_run_reasons\": [")
                .last?.components(separatedBy: "]").first ?? ""
            XCTAssertFalse(reasons.isEmpty,
                           "扫不到 notice-banner 的 allowed_not_run_reasons ⇒ 下面那条是空转的（正对照）")
            XCTAssertTrue(reasons.contains("\"witness-snaps-here\""),
                          "notice-banner 被放宽成 must_judge=false，却没在理由数组里登记放行它的理由 ⇒ "
                              + "闸门那边会把它当 UNREGISTERED 红掉，这条放宽是空的（登记要能落地）")
            XCTAssertNotNil(bannerBlock.range(of: #"38\d{8}"#, options: .regularExpression),
                            "notice-banner 的放宽没带 run 号 ⇒ 「登记是测量」这句话就退化成一句愿望："
                                + "没有 run 号，下一个人无法去把那条读数再看一遍（BACKLOG 49）")
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

    /// 判"带捕获够便宜"所需的**最小节省倍数**（整窗中位 ÷ 带中位）。R72 从 2 改成 1。
    ///
    /// 为什么改：那个 2 是**本机数**（R55 拟合说 4.8、判据退到 2 已经是一次让步），
    /// 而 R68+R69 那一次 CI 给出了 runner 的实物：
    /// `XCTAssertLessThanOrEqual failed: ("26.036") is greater than ("22.200")`
    /// ⇒ 带 26.0ms、整窗 44.4ms ⇒ **省了 1.70 倍，真实存在，只是不到 2**。
    /// 也就是说这一格在 runner 上量到的是"这台机器的成本结构"，不是"rect 有没有起作用"。
    /// 与它同一条课的是 R38（两台机器的读数不能当另一台机器的地板）—— 这次栽的又是新判据。
    ///
    /// 改到 1 之后**牙没有变少**，因为"rect 是装饰"这一族错由三条更硬的断言拦：
    /// 帧高必须变小、带宽必须等于整宽、首尾差必须装得下变更；再加上这一条"严格更便宜"
    /// （相等就红 ⇒ `captureRect` 变成空操作时两臂成本相同 ⇒ 红）。
    /// 倍数本身仍然每轮打出来（`MOTION_BAND`），趋势看得见 —— 只是不再拿一台机器的数当另一台的地板。
    static let bandCaptureSavingFloor: Double = 1

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
            switch Self.grabAttribution(clockIntervalMilliseconds: interval, worstGrabMilliseconds: grab) {
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
        XCTAssertTrue(Self.grabAttributionLabel(clockIntervalMilliseconds: 260, worstGrabMilliseconds: 255.2)
                        .contains("归因=probe-grab-bound"))
        XCTAssertTrue(Self.grabAttributionLabel(clockIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
                        .contains("归因=grab-dominates"))
        XCTAssertTrue(Self.grabAttributionLabel(clockIntervalMilliseconds: 120, worstGrabMilliseconds: 20)
                        .contains("归因=not-the-grab"))
        XCTAssertTrue(Self.grabAttributionLabel(clockIntervalMilliseconds: 120, worstGrabMilliseconds: -1)
                        .contains("归因=grab-unmeasured"))
        // ⑩ 比例要**打在日志里**：分档是我的判读，`解释=NN%` 才是能复核的数。
        XCTAssertTrue(Self.grabAttributionLabel(clockIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
                        .contains("解释=91%"),
                      "标签里没了比例 ⇒ 读日志的人只能信我的分档，没法自己看 87.9/97")
        // ⑪ 归因不许改 not-run 的**令牌**：`clock-coarse-in-window` 是登记表里的理由，
        //    换掉它会让覆盖率地板报 BAD_REASON（那是我们想要的"新形状"，不是本轮的意图）。
        //    这一格钉的是：归因只能**追加**在结论后面，不能自己再打一个 `MOTION_NOT_RUN=` 前缀
        //    —— 闸门每行只取第一个匹配，多打一个就会把真理由顶掉。
        XCTAssertFalse(Self.grabAttributionLabel(clockIntervalMilliseconds: 97, worstGrabMilliseconds: 87.9)
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
        let printCall = "pr" + "int("   // R302/358：本文件进了名册，被搜的串不许原样出现在自己文本里（R55 的 M276 同族）
        let readingPrefix = "MOTION"
        let positiveControl = ["  " + printCall + quote + readingPrefix + "_X 1)",
                               "  " + printCall + "(String(format: " + quote + readingPrefix + "_Y %@\", a))",
                               "  " + printCall + quote + readingPrefix + " \(name) frames=1)",
                               "  emit(" + quote + readingPrefix + "_Z 1)"]
        let caught = positiveControl.filter { $0.contains(printCall) && $0.contains(quote + readingPrefix) }
        XCTAssertEqual(caught.count, 3,
            "正对照只抓到 \(caught.count)/3 种写法 ⇒ 这条扫描本身是坏的（第 4 条是 emit，必须**不**被抓到），"
                + "下面那句\"没有游离读数\"因此什么都没说")
        let strays = source.components(separatedBy: "\n").filter { line in
            line.contains(printCall) && line.contains(quote + readingPrefix)
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

    /// R75 / BACKLOG 104 的答案：**四臂那条 `.jump` 红**也要过证人这一关（原来只有阳性对照那一条问证人）。
    ///
    /// 为什么这是同一个洞的另一半：`testTransitionsAreActuallyRunning` 的 `.jump` 判的是
    /// "变化段时长 < 0.4×声明"，而一条只拍到两帧的变化段，它的"时长"**就是一次采样间隔**。
    /// runner 上两遍的实物（R74 读，同一份判据代码）：
    ///   run 38726667469 ⇒ `notice-banner=2 帧、时长=32ms、事件内最粗=18ms` ⇒ `.jump` ⇒ **红**
    ///   run 38726991211 ⇒ `notice-banner=2 帧、时长≥60ms` ⇒ `.transition` ⇒ **绿**
    /// 而证人两遍给的是同一句话：`采样≈32ms 可分数段=4 合格=是 判定=拍成跳变`
    /// ⇒ 这台机器的通道带不动一条**已知** 150ms 的淡入。既然阳性对照与产品臂读的是同一条通道，
    /// 那"产品跳变"这句就不能在证人自己 snap 的机器上成立 —— 那是把"我没看清"写成"它没动"。
    ///
    /// 与 `controlJudgment` 的**不对称是刻意的**：只有"读成跳变"这一支需要问证人。
    /// 读到一段够长的变化是正面证据，不需要借口；缺席的证据才要先确认这台机器本来看得见它。
    enum JumpAdjudication: Equatable {
        /// 这台机器看得见那条已知淡入 ⇒ 产品这一臂读成跳变就是产品的事，判红。
        case productRed
        /// 证人（且它合格）在这台机器上把已知淡入也拍成跳变 ⇒ 通道问题，报 not-run。
        case notRunChannel
        /// 证人 snap 了，但它采得不够细 ⇒ 它没资格给"通道看不见"签字 ⇒ 仍然判红（R68 同一条理由）。
        case witnessUnqualified
        /// 证人连自己都读不出 ⇒ 探针坏了，判红并指名探针（不许拿一个坏证人去赦免一条红）。
        case witnessDead
    }

    static func jumpAdjudication(clock: FadeClockVerdict, witnessQualifies: Bool) -> JumpAdjudication {
        switch clock {
        case .resolves: return .productRed
        case .probeDead: return .witnessDead
        case .snaps: return witnessQualifies ? .notRunChannel : .witnessUnqualified
        }
    }

    /// `jumpAdjudication` 的真值表（不开窗口，CI 每轮都跑）。
    ///
    /// 四格里有两格**必须是红**（`witnessUnqualified`、`witnessDead`）：这一轮加的是"证人可以赦免"，
    /// 而一条只会赦免的表等于把红换成 skip —— 那正是 BACKLOG 49 警告的免检牌。
    /// 所以这一族断言钉的是"赦免只有一个形状"，不是"能赦免"。
    func testTheJumpAdjudicationIsATruthTable() {
        XCTAssertEqual(Self.jumpAdjudication(clock: .resolves, witnessQualifies: true), .productRed,
                       "这台机器明明看得见已知淡入，产品臂读成跳变就必须判产品")
        XCTAssertEqual(Self.jumpAdjudication(clock: .resolves, witnessQualifies: false), .productRed,
                       "证人合不合格与『它看得见』这一格无关：判定已经是 resolves")
        XCTAssertEqual(Self.jumpAdjudication(clock: .snaps, witnessQualifies: true), .notRunChannel,
                       "证人合格且 snap ⇒ 这才是『这台机器带不动』，不许继续判产品跳变")
        XCTAssertEqual(Self.jumpAdjudication(clock: .snaps, witnessQualifies: false), .witnessUnqualified,
                       "证人采得比它作证的过渡还粗，就没资格给『看不见』签字（R68 那一课）")
        XCTAssertEqual(Self.jumpAdjudication(clock: .probeDead, witnessQualifies: true), .witnessDead,
                       "证人自己读不出过程 ⇒ 红在探针上，不许拿一个坏证人去赦免一条红")
        XCTAssertEqual(Self.jumpAdjudication(clock: .probeDead, witnessQualifies: false), .witnessDead,
                       "探针坏这一格与采样率无关：合格位不该改变输出")
        XCTAssertNotEqual(Self.jumpAdjudication(clock: .snaps, witnessQualifies: true),
                          Self.jumpAdjudication(clock: .snaps, witnessQualifies: false),
                          "`witnessQualifies` 这根轴没改变输出 ⇒ 它等于没写（与 M377 同一族）")
        XCTAssertNotEqual(Self.jumpAdjudication(clock: .resolves, witnessQualifies: true),
                          Self.jumpAdjudication(clock: .snaps, witnessQualifies: true),
                          "证人的**判定**没参与决定 ⇒ 这条表只是在读合格位")
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
        // 成本与间隔**分开**打（R72）：上一轮我把 81ms 说成"抓帧面积贵"，而那次 CI 证伪了它
        // （面积小 12.6 倍，采样 80 → 81ms）。只有一个数的时候，人总会拿它当原因。
        emit("MOTION_FADE_CLOCK_COST 帧数=\(run.frames.count) 采样≈\(run.samplingMilliseconds)ms "
            + "抓帧中位=\(String(format: "%.1f", run.medianGrabMilliseconds))ms "
            + "抓帧最慢=\(String(format: "%.1f", run.worstGrabMilliseconds))ms 面积=190x24pt "
            + "⇒ 采样−中位 那一段是 runloop 没醒，不是 `cacheDisplay`")
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

    /// R109 / BACKLOG 163：菜单栏那一行"不可能有动画"的理由，今天必须**写在代码里**而不是写在注释里。
    ///
    /// 起因是本轮逐元素重判菜单栏时读到的事实：`MenuBarRecommendationsView.swift:27` 说
    /// "内容会被编译成真的 `NSMenu`（账本 D-055 / M15 实测）"，而 `App.swift` 里
    /// **从来没有出现过 `.menuBarExtraStyle`** —— 那句话依赖的是 SwiftUI 的默认值。
    /// 默认值会被人改，而旁边那条守卫数的是"这个文件里有没有 `animation(`"，
    /// 于是"理由失效"与"守卫变绿"可以同时成立（R74 那一族：只在自家夹具上成立的理由比没做决定更贵）。
    ///
    /// 三格各钉一句话：① 样式被**显式**设成 `.menu`；② 它挂在 `MenuBarExtra(` 那一段里
    /// （不是文件里随便哪一行，否则挪个位置照样绿）；③ 整个 `MenuBarExtra` 在
    /// `if #available(macOS 13, *)` 里 ⇒ 在支持底线 macOS 12 上这棵表面**不存在**，
    /// 那时用户看到的菜单是 `MenuBarController` 那棵 AppKit 的 —— 菜单栏的动效判断因此要按版本分开。
    func testMenuBarSurfaceIdentityIsDeclaredNotInherited() throws {
        let app = codeOnly(try productSource(named: "App.swift"))
        XCTAssertTrue(app.contains("MenuBarExtra("),
                      "App.swift 里找不到 MenuBarExtra ⇒ 这条守卫失去对象，先查表面是不是被挪走了")
        let after = app.components(separatedBy: "MenuBarExtra(").dropFirst().first ?? ""
        let block = String(after.prefix(1600))
        XCTAssertTrue(block.contains(".menuBarExtraStyle(.menu)"),
                      "菜单栏表面的样式不是**显式声明**的 `.menu`（今天它在 "
                          + "MenuBarRecommendationsView 的注释里被当成事实引用）⇒ 要么显式声明，要么把那句理由改掉")
        XCTAssertFalse(block.contains(".menuBarExtraStyle(.window)"),
                       "菜单栏被换成 `.window` 了：那时 SwiftUI 的过渡**会**执行，"
                           + "而 `MenuBarRecommendationsView` 里那句「不会执行」与它的守卫都还绿着")
        let before = app.components(separatedBy: "MenuBarExtra(").first ?? ""
        XCTAssertTrue(before.contains("if #available(macOS 13, *)"),
                      "MenuBarExtra 不再被 macOS 13 的可用性门挡住 ⇒ 台账里「12 上没有这棵表面」那句要重写")
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
        // R192 / BACKLOG 216：下面那句"两臂读数相同 ⇒ 尺子看不见"是**跨臂比**，而 onSpan/offSpan
        // 各自扛着各自峰值导出的线 ⇒ 与 212 同形。同一条线并排加上：这条免责必须**两把尺都说相同**
        // 才成立（只准变严，不准变松；两把尺矛盾时红，并由合读法指名是"幅度不对称"还是"真可见"）。
        let sharedLineDetail = Self.sharedMovingFloor([on, off])
        let onSpanShared = Self.transitionFrameCount(on, sharedFloor: sharedLineDetail)
        let offSpanShared = Self.transitionFrameCount(off, sharedFloor: sharedLineDetail)
        let soundDetail = Self.sharedLineIsSound([on, off])
        let floorDetail = String(format: "%.4f", sharedLineDetail)
        let agreementDetail = Self.armAgreementReading(sameUnderShared: onSpanShared == offSpanShared,
                                                       sameUnderPerArm: onSpan == offSpan,
                                                       sound: soundDetail)
        emit("MOTION_DETAIL_AB empty-to-content 开 帧数=\(onSpanShared)(旧口径\(onSpan))"
            + " 峰值=\(String(format: "%.3f", Self.peak(on)))"
            + " 冷闸=\(onFilm.clockIsWarm)  关 帧数=\(offSpanShared)(旧口径\(offSpan))"
            + " 峰值=\(String(format: "%.3f", Self.peak(off)))"
            + " 同一条线=\(floorDetail) 共用线安全=\(soundDetail)"
            + " ｜ 旧口径（各自归一化）开=\(onSpan) 关=\(offSpan)"
            + " 采样≈\(Self.sampleIntervalMilliseconds(onFilm.motionStamps))ms ⇒ \(agreementDetail)")
        XCTAssertGreaterThan(Self.peak(on), Self.minimumVisibleChange,
                             "两臂什么都没变 ⇒ 触发没让图长出来，这条 A/B 没有对照物（是探针坏了，不是动效坏了）")
        XCTAssertTrue(onFilm.clockIsWarm && offFilm.clockIsWarm,
                      "有一臂是在冷采样下抓的 ⇒ 两臂相同不能算尺子的极限，这条结论今天不成立")
        if onSpan == offSpan && onSpanShared == offSpanShared && abs(Self.peak(on) - Self.peak(off)) < 0.02 {
            emit("MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content："
                + "开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」")
        } else {
            XCTFail("两臂读数不同 ⇒ 这把尺**看得见**这条交叉淡 ⇒ 把本条改成硬判据"
                    + "（开着的过渡帧数必须大于关着的），别留一句免责。"
                    + "先读上一行的合读法：若它说『共用线不安全』⇒ 那是幅度不对称把小臂判成 0 帧"
                    + "（BACKLOG 217），不是这条交叉淡可见。"
                    + " 读数：新口径 开=\(onSpanShared) 关=\(offSpanShared) / 旧口径 开=\(onSpan) 关=\(offSpan)"
                    + " 线=\(floorDetail) 安全=\(soundDetail)")
        }
    }

    /// R322 / 动效主线：**这颗胶囊的横移到底有没有过程** —— 第一次把它放进真窗口逐帧取证，
    /// 并且当场升成硬判据。R323 把带子改成本卷量出来之后，本机读数是
    /// **开臂中间态帧数 3（旧口径 6）/ 关臂 1，峰值 0.277 对 0.939，落定 7 帧 ≈56ms**
    /// （R322 记的是 0.097 对 0.354 —— 带子只盖住半颗胶囊时，峰值被低估近三倍）。
    ///
    /// 为什么这个位点值得单独一格：它是全仓**唯一一条位移档**（`.slider` → `Slide.leading` → 弹簧），
    /// 而账上关于它只有两态证据（`segmented-filter-idle` 那张帧 + `FILTER_PILL_BAND`：
    /// R189 把 `offset` 换成 `.position` 之后，"药丸在第几段"能被像素判）。
    /// **两端都对，不等于中间那段在演** —— 它完全可以瞬移而两态尺一声不响（R16 那一族的正面版）。
    ///
    /// 判法（三条方向都是**先写死再跑**的，跑完才升硬）：
    /// ① 开臂的中间态帧数必须**严格大于**关臂，且**两把尺**（各自归一化的旧口径 + 共用线的新口径）都说大；
    /// ② 开臂峰值必须**小于**关臂 —— 同一次位移，摊到几帧上就比一帧到位矮；
    /// ③ 落定耗时上限 = 声明的两倍再让一个采样间隔（"没跑飞"；上限判据，不是"够长"判据）。
    /// 开臂抓两遍（R47 的 A/A/B）：两遍方向不一致 ⇒ 报 `MOTION_NOT_RUN=pill-slide-aa-inconsistent`
    /// 并 skip —— 前提由同一次运行量出来、说清放掉了什么、交回的是读数，不是覆盖率通道。
    func testFilterPillSlideIsAProcessNotATeleport() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.filterPillSlide()
        let saved = MotionCatalog.animationsEnabled
        let onFilmA = record(scenario)
        let onFilmB = record(scenario)
        MotionCatalog.animationsEnabled = false
        let offFilm = record(scenario)
        MotionCatalog.animationsEnabled = saved
        // 前提①（排在带子之前，R323）：**整幅**首末必须不同。这条与带子无关，拦的是"触发没驱动任何东西"。
        // 少了它，一个 no-op 触发会先撞在 `pill-band-unmeasured` 上、被读成"这台机器看不见"——
        // 那就是把探针坏洗成 skip（M924 那一刀今天正是从这里被抓回红的）。
        XCTAssertTrue(Self.premisePictureChanged(onFilmA.motionFrames, band: nil),
            "触发后整幅画面首末逐像素相同 ⇒ 这次点档什么都没驱动（夹具/探针坏了，不是通道看不见）。"
            + " 帧数=\(onFilmA.motionFrames.count)")
        // 前提②：A/B 开关必须**落进过胶片** —— 关臂得真是 `animationsEnabled == false` 时抓的。
        // 这一条是出口的前置：出口只能放行"开关生效了、胶片仍然分不开"的那种机器，
        // 不许替一把坏开关说话（同一个形状：R70 把门本身变成被量的对象）。
        XCTAssertTrue(onFilmA.animationsEnabledAtRecord && onFilmB.animationsEnabledAtRecord
                        && !offFilm.animationsEnabledAtRecord,
            "A/B 开关没落进胶片（开A=\(onFilmA.animationsEnabledAtRecord)"
            + " 开B=\(onFilmB.animationsEnabledAtRecord) 关=\(offFilm.animationsEnabledAtRecord)）"
            + " ⇒ 两臂其实是同一臂，『有没有过程』这一判据根本没在演")
        // 前提②'（R324）：**三臂必须拍在同一档色档里，而且是尺有对象的那一档**。
        // 这一条对跨臂比较比对单臂更硬：两臂若在不同档位下拍，"开臂中间态比关臂多"量的
        // 就是两种材质而不是动效开关。亮档里轨道与药丸只差 3 级 ⇒ 带子根本框不住胶囊。
        for (arm, film) in [("开A", onFilmA), ("开B", onFilmB), ("关", offFilm)] {
            XCTAssertEqual(Self.pillRampRequiredAppearanceName, film.appearanceNameAtRecord,
                "臂「\(arm)」拍在了\(film.appearanceNameAtRecord)档（这条尺要求"
                + Self.pillRampRequiredAppearanceName + "档）⇒ 三臂不同档或请求没落进胶片，"
                + "跨臂比较不成立（MOTION_GRAB 那行会印出每臂的 色档= 与 请求=）")
        }
        // R323 更正：带子改回**从这一卷量**。R322 那一版写的是 `y 66…92pt`，来源是
        // 组件帧 `/tmp/r321_rv/frames/sidebar-history-300x520-light.png` 逐行扫出来的那一条 ——
        // 那张帧里胶囊确实在 66…92pt，可本卷是**真窗口**（`HistorySidebarView` 直接进帧），
        // 同一颗胶囊量出来在 49…75pt。写死的 66…92 因此只盖住胶囊下缘那 9pt 再加一条分隔线，
        // 结论（开臂中间态比关臂多）没被推翻，但峰值 0.097 是**被低估**的读数，
        // 而斜坡尺要的中心绝不能拿半颗胶囊量（R107 / R108 那一族：尺读的是不是它声称的那个对象）。
        guard let band = measuredPillBand(onFilmA) else {
            emit("MOTION_NOT_RUN=pill-band-unmeasured pill-slide-process 首末帧之间读不出一颗"
                + "'宽度稳定、位置会走'的洞 ⇒ 这一台框不住那颗胶囊，两臂比较不成立（不写产品事实，D-305）")
            throw XCTSkip("MOTION_NOT_RUN=pill-band-unmeasured")
        }
        emit("MOTION_PILL_BAND filter-pill-slide 带=x\(String(format: "%.1f", band.minX * 300))"
            + "…\(String(format: "%.1f", (band.minX + band.width) * 300))pt"
            + " y\(String(format: "%.1f", band.minY * 520))…\(String(format: "%.1f", (band.minY + band.height) * 520))pt"
            + " 来源=本卷首末帧之差(R323 改前=组件帧目测 66…92pt)")

        writeStrip("filter-pill-slide-开A", onFilmA.motionFrames)
        writeStrip("filter-pill-slide-开B", onFilmB.motionFrames)
        writeStrip("filter-pill-slide-关", offFilm.motionFrames)

        let dA = Self.deltas(onFilmA.motionFrames, band: band)
        let dB = Self.deltas(onFilmB.motionFrames, band: band)
        let dOff = Self.deltas(offFilm.motionFrames, band: band)
        let shared = Self.sharedMovingFloor([dA, dB, dOff])
        let sound = Self.sharedLineIsSound([dA, dB, dOff])
        let spanA = Self.transitionFrameCount(dA, sharedFloor: shared)
        let spanB = Self.transitionFrameCount(dB, sharedFloor: shared)
        let spanOff = Self.transitionFrameCount(dOff, sharedFloor: shared)
        let oldA = Self.transitionFrameCount(dA)
        let oldB = Self.transitionFrameCount(dB)
        let oldOff = Self.transitionFrameCount(dOff)
        let interval = Self.sampleIntervalMilliseconds(onFilmA.motionStamps)
        let duration = scenario.declaredDurationMilliseconds
        emit("MOTION_PILL_SLIDE filter-pill-slide 开A 帧数=\(spanA)(旧口径\(oldA))"
            + " 峰值=\(String(format: "%.3f", Self.peak(dA))) 冷闸=\(onFilmA.clockIsWarm)"
            + "  开B 帧数=\(spanB)(旧口径\(oldB)) 峰值=\(String(format: "%.3f", Self.peak(dB)))"
            + " 冷闸=\(onFilmB.clockIsWarm)"
            + "  关 帧数=\(spanOff)(旧口径\(oldOff)) 峰值=\(String(format: "%.3f", Self.peak(dOff)))"
            + " 同一条线=\(String(format: "%.4f", shared)) 共用线安全=\(sound)"
            + " 声明=\(String(format: "%.0f", duration))ms 采样≈\(interval)ms")

        // 前提：这一卷里得**有**一次变化，而且不是在冷采样下抓的。
        XCTAssertGreaterThan(Self.peak(dA), Self.minimumVisibleChange,
            "开臂带内一个像素都没变 ⇒ 触发没让胶囊移动（探针/夹具坏了，不是动效坏了）。"
            + " 峰值=\(String(format: "%.3f", Self.peak(dA))) 地板=\(Self.minimumVisibleChange)")
        XCTAssertTrue(onFilmA.clockIsWarm && onFilmB.clockIsWarm && offFilm.clockIsWarm,
                      "有一臂是在冷采样下抓的 ⇒ 两臂的比较不成立，这条结论今天不判")

        // R323 / runner 交账（RUN=40023610164 与 40023766162，同一朵红）：那一跑**三臂逐帧相同** ——
        //   开A 帧数=1 峰值=0.463 / 开B 帧数=1 峰值=0.463 / 关 帧数=1 峰值=0.463，可分帧=7、冷闸=true。
        // 这句话不能读成"这条位移在那台机器上只占一帧"，因为**开关两臂连一帧差异都没有**：
        // 把 `animationsEnabled` 打开与关上拍出同一卷胶片，说明这段过程根本没进那台机器的画面，
        // 于是"开臂比关臂多 / 比关臂矮"两条判据都没有对照物（R47 的 A/A 同一形状，只是这次跨臂）。
        // 出口的前提在本机是**相反方向**量过的（R161 的规矩）：本机同一卷 开=0.277 对 关=0.939、
        // 帧数 3 对 1 ⇒ 这条出口放掉的是通道，不是产品；产品侧留下一格**有名字的未覆盖**（BACKLOG 376）。
        let armsIdentical = Self.armsAreIdentical(onA: dA, onB: dB, off: dOff)
        // R325 / D-311：出口谓词换成**判据自己用的那两个数**（过渡帧数、峰值）。
        // RUN=40053805112 是这一改的证人：那一跑三臂 帧数=1/1/1、峰值=0.925/0.925/0.925，
        // 而数组别的位置各不相同 ⇒ 上一版"逐字节相同"没响，红砸在产品断言上（读起来像"这条位移是瞬移"）。
        // 本机给的是相反方向的证据（开 3 帧 / 关 1 帧、峰值 0.266 对 0.949）⇒ 这条出口放掉的是通道，不是产品。
        let indistinguishable = Self.armsIndistinguishable(spanA: spanA, spanB: spanB, spanOff: spanOff,
                                                           peakA: Self.peak(dA), peakB: Self.peak(dB),
                                                           peakOff: Self.peak(dOff))
        guard !armsIdentical && !indistinguishable else {
            let resolvableOnThisMachine = Self.resolvableFrames(durationMilliseconds: duration,
                                                                 sampleMilliseconds: interval)
            let which = armsIdentical ? "逐字节相同" : "帧数与峰值全等（数组别处不同）"
            emit("MOTION_NOT_RUN=pill-slide-arms-indistinguishable filter-pill-slide 三臂不可分（\(which)"
                + "：开A 帧数=\(spanA) 峰值=\(String(format: "%.4f", Self.peak(dA)))"
                + " 开B 帧数=\(spanB) 峰值=\(String(format: "%.4f", Self.peak(dB)))"
                + " 关 帧数=\(spanOff) 峰值=\(String(format: "%.4f", Self.peak(dOff)))）"
                + " 采样≈\(interval)ms 可分帧=\(resolvableOnThisMachine)"
                + " ⇒ 这一台的胶片里这段位移只占一帧且开关不可分，『有没有过程』这一半没有对照物")
            throw XCTSkip("MOTION_NOT_RUN=pill-slide-arms-indistinguishable")
        }

        // ③ 落定耗时**上限**（"没跑飞"）—— 这一半与采样粒度无关，任何一台都判。
        //
        // 它只判上限、不判"够长"，理由写在这里免得下一次被读成缺陷：
        // 本机实测（R323 改带之后）`到位帧=7 采样≈8ms ⇒ 落定≈56ms`，而目录声明的是 200ms（`.slider` 的 response）。
        // 临界阻尼弹簧本来就先把绝大部分位移做完再拖尾，尾段那零点几个 pt 落在这把尺的
        // 逐像素相等判据之下 ⇒ "64ms 落定"与"response=200ms"**不矛盾**，
        // 它是这条尺的分辨率，不是产品的时长。真要判"声明 200ms 是不是 200ms"，
        // 需要 4ms 一帧（R2 那一课），而那件事由纯值守卫 `testCurveSecondsComeFromTheDurationTable`
        // 从参数侧钉住，不由这把像素尺冒充。
        let settled = Self.settledAtFrame(onFilmA.motionFrames, band: band)
        if let settled {
            let settledMilliseconds = Double(settled) * Double(max(interval, 1))
            emit("MOTION_PILL_SLIDE_SETTLE filter-pill-slide 到位帧=\(settled)"
                + " 采样≈\(interval)ms ⇒ 实测落定≈\(Int(settledMilliseconds))ms（声明 \(Int(duration))ms）"
                + " 可分帧=\(Self.resolvableFrames(durationMilliseconds: duration, sampleMilliseconds: interval))")
            XCTAssertLessThanOrEqual(settledMilliseconds, duration * 2 + Double(interval),
                "胶囊滑入实测落定 ≈\(Int(settledMilliseconds))ms，远超声明的 \(Int(duration))ms："
                + "曲线跑飞或者有别的东西在重排这一带")
        } else {
            XCTFail("开臂读不出落定帧 ⇒ 这条带从头到尾没变过（没触发，或者没框到）；"
                + "带=x\(band.minX * 300)…\((band.minX + band.width) * 300)pt"
                + " y\(band.minY * 520)…\((band.minY + band.height) * 520)pt")
        }

        // 「有没有过程」这一半只在**这一台的时钟切得出至少 3 帧**时才判（R47 / R2 的同一把尺：
        // 帧数由采样相位决定，而 runner 的采样在本卷里量过 31–90ms 一档）。
        // 放行条件读的是**同一次运行量出来的采样间隔与声明时长**，不是覆盖率通道（R161）。
        let resolvable = Self.resolvableFrames(durationMilliseconds: duration,
                                               sampleMilliseconds: interval)
        guard resolvable >= 3 else {
            emit("MOTION_NOT_RUN=clock-too-coarse pill-slide-process 采样≈\(interval)ms"
                + " 声明=\(Int(duration))ms ⇒ 这一台的时钟切不出 3 帧，「中间态比关臂多」这一半无从判定"
                + "（前提与落定上限照判）。开A 帧数=\(spanA)/旧\(oldA) 关 帧数=\(spanOff)/旧\(oldOff)")
            return
        }
        // A/A 不一致 ⇒ 这条判据今天没有对照物（**不挑一次算数**，R47）。
        let aAgree = (spanA > spanOff) == (spanB > spanOff) && (oldA > oldOff) == (oldB > oldOff)
        guard aAgree else {
            emit("MOTION_NOT_RUN=pill-slide-aa-inconsistent filter-pill-slide"
                + " 开A 帧数=\(spanA)/旧\(oldA) 开B 帧数=\(spanB)/旧\(oldB) 关 帧数=\(spanOff)/旧\(oldOff)"
                + " ⇒ 同一臂两遍方向不一致，判的是进程历史而不是产品")
            throw XCTSkip("MOTION_NOT_RUN=pill-slide-aa-inconsistent：开臂两遍不一致，今天不判")
        }
        // ① 中间态帧数：两把尺都必须说"开着比关着多"。
        XCTAssertGreaterThan(spanA, spanOff,
            "共用线口径下开臂中间态帧数=\(spanA) 不大于关臂 \(spanOff) ⇒ 这条位移是**瞬移**，"
            + "而目录里给它写了 \(String(format: "%.0f", duration))ms 的弹簧：声明与产物不符（R11 那一族）。")
        XCTAssertGreaterThan(oldA, oldOff,
            "旧口径（各自归一化）下开臂=\(oldA) 不大于关臂 \(oldOff) ⇒ 两把尺必须同方向，"
            + "只有一把说多就是其中一把坏了（R192 / BACKLOG 216 同一形状）。")
        // ② 峰值：摊到几帧上，必然比"一帧到位"矮。
        XCTAssertLessThan(Self.peak(dA), Self.peak(dOff),
            "开臂峰值=\(String(format: "%.3f", Self.peak(dA))) 不小于关臂"
            + " \(String(format: "%.3f", Self.peak(dOff))) ⇒ 两臂在同一帧里改了同样多的像素，"
            + "也就是这次变更没有被摊开 —— 声明的位移档没在演。")
        // ④ 时钟切得出来的时候，"两帧就到位"就是没有过程。
        if let settled {
            XCTAssertGreaterThanOrEqual(settled, 2,
                "触发后第 \(settled) 帧就已经是最终态 ⇒ 这条位移档没有过程")
        }
    }

    // MARK: - R323 / 斜坡尺：四颗纯尺 + 一条逐帧判据
    //
    // 这一组纯尺存在的全部理由：R322 那条"有没有过程"用的带子是**在另一张帧上目测**的
    // （组件帧 `sidebar-history-300x520-light`，胶囊在 66…92pt），而这一卷真窗口里逐行量出来的
    // 胶囊行带在 49…75pt —— 同一句"胶囊那一行"指向了两块地方。
    // 结论没被推翻（半颗胶囊仍然读得出"开臂比关臂多"），但那一格的峰值是**被低估**的读数，
    // 而斜坡尺要的是**中心**：中心不能拿半颗胶囊量
    // （R107 / R108 那一族：尺读的是不是它声称的那个对象）。

    /// 色档名（只用于把"这一卷是在哪一档外观下拍的"印进读数）：胶片场景以前不钉外观，
    /// macOS 的"自动"会在白天/夜里换档 —— 同一份判据在两个时刻量的不是同一张画面（R324 现读）。
    /// 一个**请求**的色档 → 名字（`nil` = 这一卷没钉；"其他" = 钉了这把尺不认识的档）。
    static func appearanceName(forRequested requested: NSAppearance.Name?) -> String {
        guard let requested = requested else { return "未钉" }
        if requested == .aqua { return "亮" }
        if requested == .darkAqua { return "暗" }
        return "其他"
    }

    /// 读的是**传进来的那棵树**实际解析到的档位，不是"我请求了哪一档"。
    static func appearanceName(of appearance: NSAppearance) -> String {
        appearanceName(forRequested: appearance.bestMatch(from: [.aqua, .darkAqua]))
    }

    static func appearanceName() -> String {
        appearanceName(of: NSApp.effectiveAppearance)
    }

    /// 斜坡尺 / 过程证人**要求**的色档名（R324 现读，不是审美选择）：
    /// 暗档 轨道−页底 = 22 级、药丸−轨道 = 16 级；亮档三档实测 230 / 230 / 233 —— 只剩 **3** 级，
    /// 低于这把尺的 `delta=8`，于是"那颗会走的洞"在亮档里连一个候选行都读不出来（本机 `候选行=0`）。
    /// 场景请求哪一档写在 `Scenario.filterPillSlide` 里，尺需要哪一档写在这里 ——
    /// **两边各自成文再断言相等**：合抄成一处就没有第二只眼，漂了没人红（R38 的同一课，
    /// 但"要什么"与"给了什么"本来就是两个量，不许共享一份权威）。
    static let pillRampRequiredAppearanceName = "暗"

    /// 从一行里认出"这是一颗场景工厂"（`static func 名字() -> Scenario {`），认不出返回 nil。
    static func scenarioFactoryName(from line: String) -> String? {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        guard trimmed.hasPrefix("static func "), trimmed.hasSuffix("-> Scenario {") else { return nil }
        let head = String(trimmed.dropFirst("static func ".count))
        guard let paren = head.firstIndex(of: "(") else { return nil }
        let name = String(head[..<paren])
        return name.isEmpty ? nil : name
    }

    /// 点名式数一遍：哪些场景工厂**钉了**色档、哪些没钉（R324 的缺席计数，纯函数）。
    ///
    /// 为什么要数而不是"本轮顺手把胶囊那条钉上就完事"：没钉色档这个毛病是**整卷级别**的，
    /// 只修一处就把它当成了个案；而"其余场景要不要钉"在量出来缺席之前不许登记成已判（D-305 的同一课）。
    /// 数法只认工厂签名与它自己那段正文里的 `appearance:`，注释行先剥掉 ——
    /// 台账式注释里满篇都写着 `appearance:`，算进去就是守卫的假阳性（R143 那一族）。
    /// 收尾只认 8 空格那一行 `}`：工厂正文都在 12 空格以上，所以内层闭包的 `}` 不会提前收口。
    static func scenarioPinCensus(code: String) -> (pinned: [String], unpinned: [String]) {
        let lines = code.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
        var pinned: [String] = []
        var unpinned: [String] = []
        var current: String?
        var sawPin = false
        func close() {
            guard let name = current else { return }
            if sawPin { pinned.append(name) } else { unpinned.append(name) }
            current = nil
            sawPin = false
        }
        for line in lines {
            if let name = scenarioFactoryName(from: line) {
                close()
                current = name
                continue
            }
            guard current != nil else { continue }
            if line.contains("appearance:") { sawPin = true }
            if line == "        }" { close() }
        }
        close()
        return (pinned, unpinned)
    }

    /// 纯函数：一个像素的 Rec.709 亮度（与 `UICaptureHarness.ArmRGB.luma` 同一组系数，
    /// 两把尺不许各抄一份系数表 —— R68：证人要与它作证的判据同一颗尺子）。
    static func lumaAt(_ pixels: [UInt8], _ bytesPerRow: Int, _ x: Int, _ y: Int) -> Double {
        let o = y * bytesPerRow + x * 4
        return 0.2126 * Double(pixels[o]) + 0.7152 * Double(pixels[o + 1])
            + 0.0722 * Double(pixels[o + 2])
    }

    /// 纯函数：给定行带里**逐列取中位数**的横向剖面（长度 = xRange.count，索引 0 对 xRange.lowerBound）。
    ///
    /// 为什么是中位数，不是均值也不是最大值：行带正中间穿过两个段的**字**。
    /// 字墨（本机 130…230）比轨道（52）亮得多 —— 按列取均值会把药丸内部那一段抬上去，
    /// 取最大值干脆整条剖面都是字。字只占那一列行高的小三成 ⇒ 中位数仍然落回底上。
    /// （与 `testGlyphInkUsesTenthDecile` 那一族同一件事：锐度对均值过敏。）
    static func columnMedianProfile(pixels: [UInt8], bytesPerRow: Int, yRange: Range<Int>,
                                    xRange: Range<Int>, yStride: Int = 2) -> [Double] {
        guard !xRange.isEmpty, !yRange.isEmpty, yStride > 0 else { return [] }
        var out: [Double] = []
        out.reserveCapacity(xRange.count)
        for x in xRange {
            var col: [Double] = []
            var y = yRange.lowerBound
            while y < yRange.upperBound {
                col.append(lumaAt(pixels, bytesPerRow, x, y))
                y += yStride
            }
            out.append(Self.median(col))
        }
        return out
    }

    /// 纯函数：单行上的"轨道 + 会动的洞"读数（首末两帧一起看）。
    ///
    /// 三道**结构**闸决定"这一行是不是候选"（不成立 ⇒ nil）：
    /// ① 有一段与页底不同档的轨道；② 两臂的左右两半**互为镜像**，由它们量出药丸档与轨道档，
    /// 且轨道里要有一段处在药丸那一档（R333 重基：旧写法是"与页底同档的那一段"，
    /// 那句话把 377 的缺陷画法当成了定义，修法一落地就失去对象 —— 见 `halfLevels` 上面的更正）；
    /// ③ 这个洞在两帧之间**走了**至少 `minMoveFraction` 个轨道宽。
    ///    （R333：② 一旦要求两半互换，③ 就被它**蕴含**了 —— 药丸跨过中线才会让两半换档。
    ///    这条闸留着不删（删守卫是放宽），但它的证人从"静止的一行给 nil"换成了
    ///    "地板本身有牙"：`minMove=0.7` 必须拦、`minMove=0.6` 必须放，见 `MotionPillRampTests`。）
    /// 三道**形状**闸决定"这颗候选是不是那颗胶囊"（成立但形状不对 ⇒ 非 nil，`gate` 点名为什么不对）：
    /// ④ 两帧里洞的宽度必须差不多（`widthToleranceFraction`）—— 胶囊是刚体，字缝不是；
    /// ⑤ 洞必须贴在轨道的**一端**，而两帧贴在**异端**（`edgeFlushFraction`）—— 静止态里药丸占满一整段，
    ///    所以它必然挨着轨道的某一边；列表行里那颗"会走的洞"走在中间，两端都不贴；
    /// ⑥ 洞至少要有一段之宽（`minHoleFraction`）—— 字缝远窄于此。
    ///
    /// 为什么不用"哪些行在变"来定位（R323 自曝的第一版）：换档会**重排整个列表**，
    /// 本机量出来列表那一片（y≈128…520pt）逐行都在变，比胶囊那 26pt 大一个数量级 ⇒
    /// "最长连续变化行带"选到的是列表（读数：行带=126…520pt 那一版）。
    ///
    /// 为什么 ④⑤⑥ 是 R324 补的而不是洁癖：runner 那一跑（RUN=40032708615）用三道结构闸
    /// 量出来的行带是 `346.0…352.0pt 轨道范围=25.0…299.0pt`（6pt 高、一直顶到扫描右界），
    /// 那是列表里的一行，不是胶囊 —— 于是斜坡尺判成"回头"、过程证人判成"峰值相等"，
    /// **一朵尺子红长得和产品缺陷一模一样**。
    /// 为什么 ⑤ 用"贴端"而不是"贴段中心"：段中心要把段的**数量**抄进尺（产品常量），
    /// 而"静止时药丸挨着轨道的一端"是这条位移档自己的语义，不需要知道一共几段。
    static func movingHoleRowReading(pixelsA: [UInt8], pixelsB: [UInt8], bytesPerRow: Int, y: Int,
                                     xRange: Range<Int>, marginWindow: Int, delta: Double,
                                     minTrackPixels: Int, minHolePixels: Int,
                                     maxHoleFraction: Double, minMoveFraction: Double,
                                     minHoleFraction: Double, edgeFlushFraction: Double,
                                     widthToleranceFraction: Double)
        -> (extent: Range<Int>, holeA: Range<Int>, holeB: Range<Int>, margin: Double, gate: String)? {
        guard !xRange.isEmpty, y >= 0, marginWindow > 0 else { return nil }
        let rowA = (0..<xRange.count).map { lumaAt(pixelsA, bytesPerRow, xRange.lowerBound + $0, y) }
        let rowB = (0..<xRange.count).map { lumaAt(pixelsB, bytesPerRow, xRange.lowerBound + $0, y) }
        let window = min(marginWindow, rowA.count)
        let margin = Self.median(Array(rowA[0..<window]))
        guard margin >= 0 else { return nil }
        guard let extA = trackExtent(profile: rowA, margin: margin, delta: delta,
                                     minTrackPixels: minTrackPixels),
              let extB = trackExtent(profile: rowB, margin: margin, delta: delta,
                                     minTrackPixels: minTrackPixels) else { return nil }
        let extent = Range<Int>(uncheckedBounds: (lower: Swift.min(extA.lowerBound, extB.lowerBound),
                                                  upper: Swift.max(extA.upperBound, extB.upperBound)))
        guard extent.count >= minTrackPixels,
              let halvesA = halfLevels(profile: rowA, extent: extent),
              let halvesB = halfLevels(profile: rowB, extent: extent) else { return nil }
        // R333：药丸那一档由**两臂镜像**量出来（为什么不再锚"与页底同档"，见 `halfLevels` 上面那段更正）。
        let levels = settledPillTrackLevels(firstLeft: halvesA.left, firstRight: halvesA.right,
                                            lastLeft: halvesB.left, lastRight: halvesB.right,
                                            delta: delta)
        guard let holeA = pillRun(profile: rowA, pillLevel: levels.pill, trackLevel: levels.track,
                                  delta: delta, extent: extent, minPillPixels: minHolePixels,
                                  mergeInk: true),
              let holeB = pillRun(profile: rowB, pillLevel: levels.pill, trackLevel: levels.track,
                                  delta: delta, extent: extent, minPillPixels: minHolePixels,
                                  mergeInk: true) else { return nil }
        let width = Double(extent.count)
        guard Double(holeA.range.count) / width <= maxHoleFraction,
              Double(holeB.range.count) / width <= maxHoleFraction else { return nil }
        let move = abs(Double(holeB.range.lowerBound + holeB.range.upperBound
                              - holeA.range.lowerBound - holeA.range.upperBound) / 2.0)
        guard move >= minMoveFraction * width else { return nil }
        // 形状闸（R324）：三道都过才叫"过"，第一道不过就点名。
        var gate = "过"
        let wA = Double(holeA.range.count), wB = Double(holeB.range.count)
        let tol = Swift.max(1.0, widthToleranceFraction * Swift.min(wA, wB))
        let narrow = wA / width < minHoleFraction || wB / width < minHoleFraction
        let edge = Swift.max(1.0, edgeFlushFraction * width)
        let aLeft = Double(holeA.range.lowerBound - extent.lowerBound) <= edge
        let aRight = Double(extent.upperBound - holeA.range.upperBound) <= edge
        let bLeft = Double(holeB.range.lowerBound - extent.lowerBound) <= edge
        let bRight = Double(extent.upperBound - holeB.range.upperBound) <= edge
        let oppositeEnds = (aLeft && bRight) || (aRight && bLeft)
        if !levels.mirror {
            gate = "不镜像"
        } else if narrow {
            gate = "洞太窄"
        } else if abs(wA - wB) > tol {
            gate = "宽度不稳"
        } else if !oppositeEnds {
            gate = "不贴两端"
        }
        return (extent, holeA.range, holeB.range, margin, gate)
    }

    /// 纯函数：逐行跑 `movingHoleRowReading`，返回**最长的一段连续"过"行**（px，自上往下），
    /// 并把被拒的候选段一起交回 —— 定位失败时"为什么失败"必须是**读数**，
    /// 不能只留一句"读不出"（R323 那一版在 runner 上找错对象，而账上只看得见一个红）。
    static func movingHoleBand(pixelsA: [UInt8], pixelsB: [UInt8], bytesPerRow: Int, height: Int,
                               xRange: Range<Int>, marginWindow: Int, delta: Double,
                               minTrackPixels: Int, minHolePixels: Int, maxHoleFraction: Double,
                               minMoveFraction: Double, minHoleFraction: Double,
                               edgeFlushFraction: Double, widthToleranceFraction: Double,
                               yStride: Int, minRows: Int) -> (band: Range<Int>?, report: String) {
        guard height > 0, yStride > 0, !xRange.isEmpty else {
            return (nil, "参数不成立(height=\(height) yStride=\(yStride) xRange=\(xRange))")
        }
        var verdicts: [String] = []
        var holeFractions: [Double] = []
        var y = 0
        while y < height {
            if let r = movingHoleRowReading(pixelsA: pixelsA, pixelsB: pixelsB,
                                            bytesPerRow: bytesPerRow, y: y, xRange: xRange,
                                            marginWindow: marginWindow, delta: delta,
                                            minTrackPixels: minTrackPixels,
                                            minHolePixels: minHolePixels,
                                            maxHoleFraction: maxHoleFraction,
                                            minMoveFraction: minMoveFraction,
                                            minHoleFraction: minHoleFraction,
                                            edgeFlushFraction: edgeFlushFraction,
                                            widthToleranceFraction: widthToleranceFraction) {
                verdicts.append(r.gate)
                // R327：被拒的那一段要带**差多少**的数。"洞太窄"这三个字在 R326 之前就是全部信息，
                // 于是"是地板定高了还是对象没框全"两种坏法读不出区别 —— 本轮量到被拒段 23% / 25%
                // 而通过段 49%（差一倍，不是刚过线），这一格直接把 384 的下一步定成"修对象"。
                holeFractions.append(Double(r.holeA.count) / Double(Swift.max(1, r.extent.count)))
            } else {
                verdicts.append("非候选")
                holeFractions.append(-1)
            }
            y += yStride
        }
        // 连续同判定的行段（"非候选"不进报告：它不是候选，没什么可解释的）
        var groups: [(gate: String, from: Int, to: Int, hole: Double)] = []
        var i = 0
        while i < verdicts.count {
            var j = i
            while j + 1 < verdicts.count, verdicts[j + 1] == verdicts[i] { j += 1 }
            if verdicts[i] != "非候选" {
                let slice = holeFractions[i...j].filter { $0 >= 0 }
                groups.append((verdicts[i], i * yStride, Swift.min(height, (j + 1) * yStride),
                               slice.isEmpty ? -1 : Self.median(Array(slice))))
            }
            i = j + 1
        }
        let accepted: [(gate: String, from: Int, to: Int, hole: Double)] =
            groups.filter { $0.gate == "过" && $0.to - $0.from >= minRows }
        let best: (gate: String, from: Int, to: Int, hole: Double)? =
            accepted.max { ($0.to - $0.from) < ($1.to - $1.from) }
        let ranked: [(gate: String, from: Int, to: Int, hole: Double)] =
            groups.sorted { ($0.to - $0.from) > ($1.to - $1.from) }
        var parts: [String] = []
        for g in ranked.prefix(4) {
            // "过了形状闸但高度不够"也必须是读数：否则报告只会说"候选段=无"，
            // 而真相是"候选找到了、被 minRows 掉了" —— 这两种坏的修法相反。
            let label = (g.gate == "过" && g.to - g.from < minRows) ? "过但太短" : g.gate
            var line = "y" + String(g.from) + ".." + String(g.to) + "px 高"
                + String(g.to - g.from) + "px 判=" + label
                + " 洞宽=" + (g.hole < 0 ? "无" : String(format: "%.0f%%", g.hole * 100.0))
            // R328 / BACKLOG 388：**被拒**的那一段要带逐列转储。
            // 为什么只给被拒的：通过段没有待答的问题，给它的转储只会把这一行变长；
            // 而被拒段的那句"洞太窄"在 R327 之前分不出"地板高了"与"对象没框全"，
            // 加了洞宽之后又分不出"那里有几档" —— 384 连着两轮改定义都卡在这个不知道上。
            if g.gate != "过" {
                let row = Swift.max(0, Swift.min(height - 1, (g.from + g.to) / 2))
                let profile = (0..<xRange.count)
                    .map { lumaAt(pixelsA, bytesPerRow, xRange.lowerBound + $0, row) }
                let margin = Self.median(Array(profile.prefix(Swift.max(1, marginWindow))))
                line += " 分档=" + Self.levelHistogram(profile: profile, margin: margin, delta: delta)
            }
            parts.append(line)
        }
        var taken = "无"
        var band: Range<Int>?
        if let b = best {
            taken = "y" + String(b.from) + ".." + String(b.to) + "px"
            band = Range<Int>(uncheckedBounds: (lower: b.from, upper: b.to))
        }
        let joined = parts.isEmpty ? "无" : parts.joined(separator: " | ")
        let candidateRows = verdicts.filter { $0 != "非候选" }.count
        let head = "行=" + String(verdicts.count) + " 候选行=" + String(candidateRows)
            + " 判定分布=" + Dictionary(grouping: verdicts, by: { $0 })
                .map { $0.key + "×" + String($0.value.count) }.sorted().joined(separator: ",")
        return (band, head + " 候选段=" + joined + " 取用=" + taken
            + " " + Self.verticalCoverage(groups: groups, taken: band))
    }

    /// 纯函数：取用带占"这条纵向跨度"的几成（R329 / BACKLOG 388 剩下那半格的出处）。
    ///
    /// 为什么要它：R328 的分档证明了被拒那一段是胶囊下半 + 标签的字，
    /// 于是报告里那三段（过 / 洞太窄 / 过）**首尾相接**，合起来才是那颗胶囊的纵向范围。
    /// 之前只有三段各自的高，"取用带盖住了胶囊的几成"要读者自己去加 ——
    /// 而这一格决定下一轮修什么：盖得住就只需要开一条形状闸，盖不住就得先修带子的纵向定义。
    /// 只合**进了报告的**候选段（"非候选"没资格参与）；取用为空给"纵向覆盖=无"，不许给 0%。
    static func verticalCoverage(groups: [(gate: String, from: Int, to: Int, hole: Double)],
                                 taken: Range<Int>?) -> String {
        guard let taken = taken, taken.upperBound > taken.lowerBound else { return "纵向覆盖=无" }
        var low = taken.lowerBound, high = taken.upperBound
        var moved = true
        while moved {
            moved = false
            for g in groups {
                if g.to == low, g.from < low { low = g.from; moved = true }
                if g.from == high, g.to > high { high = g.to; moved = true }
            }
        }
        let total = high - low
        guard total > 0 else { return "纵向覆盖=无" }
        let pct = Int((Double(taken.count) / Double(total) * 100.0).rounded())
        return "纵向覆盖=" + String(taken.count) + "/" + String(total) + "px=" + String(pct) + "%"
    }

    /// 纯函数：把报告里那一格 `纵向覆盖=A/Bpx=P%` 解析回三个数；读不出（没有这一格、
    /// 或它是"无"、或形状不是三段）一律给 nil。
    ///
    /// 为什么解析要住在尺这一边而不是证人里（R333）：证人原本自己 `split` 完就直接按下标取，
    /// 于是"没有带子"那一发把整卷打成 **SIGTRAP（Index out of range）** —— 崩掉比红坏得多：
    /// 红只损失一格，崩把后面所有格的结论行一起带走（变异表因此读成 NOT_RUN，
    /// 而 NOT_RUN 与"这一环没有证人"在账上是两件事）。格式由打印它的那颗尺负责解析，
    /// 于是"读不出"是返回值里的一个 nil，不是一次下标越界。
    static func verticalCoverageCells(report: String) -> [Int]? {
        guard let cell = report.split(separator: " ").first(where: { $0.hasPrefix("纵向覆盖=") })
        else { return nil }
        let nums = String(cell.dropFirst("纵向覆盖=".count))
            .components(separatedBy: CharacterSet.decimalDigits.inverted)
            .filter { !$0.isEmpty }.compactMap { Int($0) }
        return nums.count == 3 ? nums : nil
    }

    /// 纯函数：剖面上"与页底**不同档**"的第一列到最后一次出现的那一列 = 轨道的横向范围（剖面索引）。
    ///
    /// 为什么范围要**整卷取并**而不是逐帧自算：药丸停在某一段时，亮区只剩轨道的另一半，
    /// 逐帧自算会让范围跟着跳（本机实测：首帧的亮区只有 146…286pt，末帧只有 12…154pt）。
    static func trackExtent(profile: [Double], margin: Double, delta: Double,
                            minTrackPixels: Int) -> Range<Int>? {
        guard !profile.isEmpty, minTrackPixels > 0 else { return nil }
        var first = -1, last = -1
        for (i, value) in profile.enumerated() where abs(value - margin) >= delta {
            if first < 0 { first = i }
            last = i
        }
        guard first >= 0, last - first >= minTrackPixels else { return nil }
        return first..<(last + 1)
    }

    /// 纯函数：把一行的逐列电平按**尺自己那两个数**（`margin` 与 `delta`）分箱，给"第几箱×列数"的清单。
    ///
    /// 为什么要它（R328 / BACKLOG 388）：384 连着两轮改"洞的定义"而读数不变，缺的不是阈值是**对象**——
    /// 那一行里到底住着几级电平，之前只有我拿 /tmp 的临时尺看过一次，而那次没留档。
    /// 为什么分箱用 `delta` 而不是另挑一个量化宽度：自己挑的宽度会把答案变成假设 ——
    /// 第一版我按 8 级一档做 run-length，结果 36 与 40 落进同一箱，而洞/轨道的分界正好是 38，
    /// 于是那格转储把它声称要回答的那一问抹平了（这是"形容词不是读数"的仪器版）。
    /// 用 `floor((v − margin) / delta)` 之后：**第 0 箱就是与页底同档的那一级**、第 2 箱上下是轨道、
    /// 更高的箱是字墨，而这一格不引入任何新常数。形状：`-1×22,0×236,2×119,21×8`（按箱号升序）。
    /// R333 更正：这一句原来写的是"第 0 箱就是判据认的洞"——那是旧定义（药丸=与页底同档）留下的话，
    /// 重基之后洞由两臂定档，第 0 箱只回答"这条剖面扫到页底了没有"。
    /// 空剖面或 delta≤0 给"无"，不许给空串（空串在报告里读起来像被截断）。
    static func levelHistogram(profile: [Double], margin: Double, delta: Double) -> String {
        guard delta > 0, !profile.isEmpty else { return "无" }
        var bins: [Int: Int] = [:]
        for value in profile {
            bins[Int(((value - margin) / delta).rounded(.down)), default: 0] += 1
        }
        return bins.keys.sorted().map { String($0) + "×" + String(bins[$0] ?? 0) }
            .joined(separator: ",")
    }

    // ── R333 / BACKLOG 393 的公开更正：药丸的定义不再锚"与页底同档" ──────────────
    //
    // 上面那段注释（R324 写的）说的是一件**当时真实、但不是产品语义**的事：暗档实测
    // 页底 30 / 轨道 52 / 药丸 36 ⇒ 药丸恰好与页底同档。那句话之所以能用，是因为产品
    // 当时把"选中"画成了轨道上的一个暗洞 —— 也就是 377 在屏幕上判掉的那个缺陷。
    // 换句话说：**这把尺一直把缺陷的画法当成定义**。
    //
    // 所以 391 的修法①（把选中那颗抬到轨道之上）一落地，它就失去对象：本机现读
    // `行=520 候选行=0 判定分布=非候选×520 候选段=无 取用=无`，而斜坡尺与过程证人两格
    // 不是红、是 **skip**（`MOTION_NOT_RUN=pill-ramp-no-band` / `pill-band-unmeasured`）。
    // 那是这仓库最怕的一种绿：产品变了，证人安静地退场。
    //
    // 新的定义（`halfLevels` + `settledPillTrackLevels` + 这一颗 `pillRun`）极性无关：
    // 药丸那一档由两臂的**镜像**背书量出来，而不是由"它等于页底"猜出来。
    // R324 那次试过又放弃的 `staticLevel` 为什么现在又能用：它当时失败在"取没动的列的众数"
    // —— 轨道范围内没有一列不动；而这里不取众数，取的是**两半各自的电平**再要求两臂互换，
    // 恰好绕开了那一格失败。
    /// 纯函数：把轨道范围**左右平分**，各取一档电平（先按列取中位，再对半区取中位）。
    ///
    /// 为什么允许平分：两段的宽度相等是**这条控件的语义**，而它不是被抄进来的常量 ——
    /// `settledPillTrackLevels` 会拿"两臂互为镜像"去验它：如果两半不等宽或药丸没换边，
    /// 镜像就不成立，那一行就被判成"不镜像"而不是被硬框出一条带子。
    static func halfLevels(profile: [Double], extent: Range<Int>) -> (left: Double, right: Double)? {
        guard extent.lowerBound >= 0, extent.upperBound <= profile.count,
              extent.count >= 4 else { return nil }
        let mid = (extent.lowerBound + extent.upperBound) / 2
        let left = Array(profile[extent.lowerBound..<mid])
        let right = Array(profile[mid..<extent.upperBound])
        guard !left.isEmpty, !right.isEmpty else { return nil }
        return (Self.median(left), Self.median(right))
    }

    /// 纯函数：从**两个 settled 臂**量出"哪一档是选中那颗、哪一档是轨道"（R333 / BACKLOG 393）。
    ///
    /// 为什么不再用"与页底同档"当药丸的定义：那句是**照着缺陷画法**写的（R323 立它的时候，
    /// 药丸本来就画在页底那一档）。391 把选中那颗抬到轨道之上之后，轨道范围里再也没有
    /// "与页底同档"的那一段 ⇒ 旧定义当场失去对象（本机现读：行=520 候选行=0，
    /// 而那两格不是红、是 skip —— 一朵尺子瞎掉长得跟"这台机器看不见"一模一样）。
    ///
    /// 新定义**极性无关**：药丸那一档 = 首帧左半的电平，轨道那一档 = 首帧右半的电平，
    /// 而它们必须由另一臂的镜像来背书（臂末的右半 == 臂首的左半、臂末的左半 == 臂首的右半）。
    /// 于是"选中那颗比轨道亮还是暗"是一个**读出来的符号**，不再是一条写死的假设；
    /// 两半不等宽、药丸没换边、或者只有一臂在动，都会让镜像不成立而被点名。
    static func settledPillTrackLevels(firstLeft: Double, firstRight: Double,
                                       lastLeft: Double, lastRight: Double, delta: Double)
        -> (pill: Double, track: Double, separation: Double, mirror: Bool) {
        let mirror = abs(firstLeft - lastRight) < delta && abs(firstRight - lastLeft) < delta
        let pill = (firstLeft + lastRight) / 2.0
        let track = (firstRight + lastLeft) / 2.0
        return (pill, track, pill - track, mirror)
    }

    /// 纯函数：在轨道范围里找出**处在药丸那一档**的最长连续列段。
    ///
    /// `pillLevel` / `trackLevel` 由 `settledPillTrackLevels` 从两臂量出来；
    /// 两档本身分不开（`|pill − track| < delta`）时这一格**没有对象**，直接给 nil ——
    /// 不许退回去猜一个（那是把"洗淡了"读成"看不见"的那条路）。
    static func pillRun(profile: [Double], pillLevel: Double, trackLevel: Double,
                        delta: Double, extent: Range<Int>, minPillPixels: Int,
                        mergeInk: Bool = false)
        -> (range: Range<Int>, pillLuma: Double, trackLuma: Double)? {
        guard extent.lowerBound >= 0, extent.upperBound <= profile.count,
              !extent.isEmpty, minPillPixels > 0,
              abs(pillLevel - trackLevel) >= delta else { return nil }
        // R356 / BACKLOG 384：标签墨不许把胶囊劈成两半。
        // 只并"既不接近药丸档、也不接近轨道档"的列（两边都 ≥ delta）—— 那是字墨；
        // 轨道（离药丸远、离轨道近）仍然断开，所以不会把相隔的两段连起来。
        // 并墨只改"哪一段算洞"，不改电平：pillLuma 仍只由药丸档的列平均（否则均值会被墨拉下去）。
        func isInk(_ value: Double) -> Bool {
            mergeInk && abs(value - pillLevel) >= delta && abs(value - trackLevel) >= delta
        }
        let isPill = extent.map { abs(profile[$0] - pillLevel) < delta || isInk(profile[$0]) }
        var best = (-1, -1)
        var start = -1
        var pillSum = 0.0, pillN = 0, trackSum = 0.0, trackN = 0
        for (i, hit) in isPill.enumerated() {
            let value = profile[extent.lowerBound + i]
            if hit {
                if !isInk(value) {
                    pillSum += value
                    pillN += 1
                }
                if start < 0 { start = i }
            } else {
                trackSum += value
                trackN += 1
                if start >= 0 {
                    if i - start > best.1 - best.0 { best = (start, i) }
                    start = -1
                }
            }
        }
        if start >= 0, isPill.count - start > best.1 - best.0 { best = (start, isPill.count) }
        guard best.1 - best.0 >= minPillPixels, pillN > 0, trackN > 0 else { return nil }
        return (Range<Int>(uncheckedBounds: (lower: extent.lowerBound + best.0,
                                             upper: extent.lowerBound + best.1)),
                pillLuma: pillSum / Double(pillN), trackLuma: trackSum / Double(trackN))
    }

    /// 纯函数：三臂在**判据自己用的那两个数**上是否全等（R325 / 决定 D-311）。
    ///
    /// 为什么不是"数组逐字节相同"：`armsAreIdentical` 是这条出口在 R324 的形状，
    /// 而 RUN=40053805112 证明它**太严**——三臂的过渡帧数（1/1/1）与峰值（0.925/0.925/0.925）全等，
    /// 数组别的位置却因为噪声各不相同 ⇒ 出口不响，红落在"开臂帧数必须大于关臂"这条产品断言上，
    /// 读起来像"这条位移是瞬移"。判据比的就是 (span, peak) 这两个数，
    /// 所以"没有对照物"必须写成这两个数的全等；逐字节相同是它的一个子集（仍然算）。
    static func armsIndistinguishable(spanA: Int, spanB: Int, spanOff: Int,
                                      peakA: Double, peakB: Double, peakOff: Double) -> Bool {
        spanA == spanB && spanB == spanOff && peakA == peakB && peakB == peakOff
    }

    /// 纯函数：中心序列里**既不在起点档、也不在终点档**的样本数（R325）。
    ///
    /// 这条存在的全部理由：runner 那一卷的中心序列是 `80.0, 219.0, 219.0, …` —— 一步跳变，
    /// 而斜坡尺照样判成"单调、最大倒退 0.0pt"。**没有中间样本就没有斜坡可判**，
    /// 那张证是空转出来的（词表默认输入里至少有一颗中间态）。
    /// 方向无关：药丸往左走还是往右走都算，端点按 `tolerance` 让开（抗锯齿与容差同量级）。
    static func intermediateCount(_ centers: [Double], tolerance: Double) -> Int {
        guard let first = centers.first, let last = centers.last else { return 0 }
        let lo = Swift.min(first, last)
        let hi = Swift.max(first, last)
        if hi - lo <= 2 * tolerance { return 0 }
        return centers.filter { $0 > lo + tolerance && $0 < hi - tolerance }.count
    }

    /// 纯函数：三臂的逐帧差数组是否**完全相同** —— 也就是这台机器的胶片里"开"与"关"不可分。
    ///
    /// 这条单独抽出来是因为它是**出口**，而出口最容易变成洗红的水：
    /// "两臂读数一样 = 尺坏/通道看不见"（R47 / BACKLOG 216 同一形状）在这里反过来用 ——
    /// 三臂一样 ⇒ 没有对照物 ⇒ 放行。所以它必须自己有一格正对照：
    /// 只要有任何一臂差一个数，它就不许说"相同"（`MotionPillRampTests.testArmsAreIdenticalRefuses...`）。
    static func armsAreIdentical(onA: [Double], onB: [Double], off: [Double]) -> Bool {
        onA == off && onB == off
    }

    /// 纯函数：把一串亮区中心归成**有名字的一种**斜坡结论。词表就是这一轮的产物，不许意译。
    ///
    /// 四格：`无对象`（任何一帧读不出中心 ⇒ 后面每一格都没有对象）/
    /// `没动`（首末中心之差 < `tolerance`，也就是这一卷里药丸根本没挪）/
    /// `回头`（相邻两帧之间出现 > `tolerance` 的**倒退** —— MC-1 说程序触发的位移不给过冲，
    /// 而"过冲后弹回来"正是它的像素形状）/ `单调`（其余：一路朝一个方向走）。
    ///
    /// 为什么 `tolerance` 用长度而不用"帧数比例"：这条判据要说的是"药丸在轨道上退回去多少"，
    /// 那是个长度量；比例会把倍率与轨道宽度混进来（R58 那一族：像素数不是几何）。
    /// 中心交给调用方换算成 **pt**，所以同一个容差在本机与 runner 上是同一条线。
    static func rampVerdict(_ centers: [Double], tolerance: Double) -> (label: String, detail: String) {
        guard !centers.isEmpty else { return ("无对象", "一个中心都没读到") }
        if let bad = centers.firstIndex(where: { $0 < 0 }) {
            return ("无对象", "第 \(bad) 帧起读不出药丸连续段：\(centers.map { String(format: "%.1f", $0) })")
        }
        let first = centers[0], last = centers[centers.count - 1]
        var worstBack = 0.0
        for i in 1..<centers.count { worstBack = max(worstBack, Double(centers[i - 1] - centers[i])) }
        let travel = Double(last - first)
        let detail = "首=\(String(format: "%.1f", first))pt 末=\(String(format: "%.1f", last))pt"
            + " 位移=\(String(format: "%.1f", travel))pt 最大倒退=\(String(format: "%.1f", worstBack))pt"
            + " 容差=\(String(format: "%.1f", tolerance))pt 帧数=\(centers.count)"
        if abs(travel) < tolerance { return ("没动", detail) }
        if worstBack > tolerance { return ("回头", detail) }
        return ("单调", detail)
    }

    /// 两处调用共用的一颗参数表（写两遍就会漂：R38 那一族，同一个阈值不许有两个权威）。
    private func measuredMovingHoleBand(_ a: Bitmap, _ b: Bitmap, scale: Double)
        -> (band: Range<Int>?, report: String) {
        let xLo = max(0, Int((1.0 * scale).rounded()))
        let xHi = min(a.width, Int((299.0 * scale).rounded()))
        guard xHi - xLo >= 16, a.height == b.height, a.width == b.width else {
            return (nil, "尺寸不成立(w=\(a.width) h=\(a.height) vs w=\(b.width) h=\(b.height))")
        }
        // 三道形状闸的参数都是**比例**，不写 px：2× 与 1× 上同一条 276pt 是两个像素数（R58 那一族）。
        // 0.25 = "至少一段之宽"（两段的控件里一段占 50%，字缝远窄于此）；
        // 0.04 ≈ 11pt@276pt 轨道 —— 药丸停在段里时与轨道端的间隙只有那 2pt 内缩；
        // 0.15 = 刚体允许被抗锯齿吃掉一成宽。
        return Self.movingHoleBand(pixelsA: a.pixels, pixelsB: b.pixels, bytesPerRow: a.width * 4,
                                   height: a.height, xRange: xLo..<xHi,
                                   marginWindow: max(2, Int((6.0 * scale).rounded())),
                                   delta: 8, minTrackPixels: max(8, Int((20.0 * scale).rounded())),
                                   minHolePixels: max(4, Int((12.0 * scale).rounded())),
                                   maxHoleFraction: 0.8, minMoveFraction: 0.1,
                                   minHoleFraction: 0.25, edgeFlushFraction: 0.04,
                                   widthToleranceFraction: 0.15,
                                   yStride: 2, minRows: max(4, Int((6.0 * scale).rounded())))
    }

    /// 从**这一卷**的首末帧量出胶囊所在的归一化带（R323：R322 那条带是在别的帧上目测的）。
    /// 读不出 ⇒ nil，调用方必须写成具名出口，不许拿目测带顶上去。
    private func measuredPillBand(_ film: Film) -> CGRect? {
        guard film.motionFrames.count > 2,
              let head = film.motionFrames.first, let tail = film.motionFrames.last else { return nil }
        let a = Self.raster(head), b = Self.raster(tail)
        guard a.height > 0, a.width > 0 else { return nil }
        let scale = Double(a.height) / 520.0
        let xLo = max(0, Int((1.0 * scale).rounded()))
        let xHi = min(a.width, Int((299.0 * scale).rounded()))
        guard xHi - xLo >= 16 else { return nil }
        let (bandOpt, _) = measuredMovingHoleBand(a, b, scale: scale)
        guard let band = bandOpt else { return nil }
        let xRange = xLo..<xHi
        let profileA = Self.columnMedianProfile(pixels: a.pixels, bytesPerRow: a.width * 4,
                                                yRange: band, xRange: xRange)
        let profileB = Self.columnMedianProfile(pixels: b.pixels, bytesPerRow: b.width * 4,
                                                yRange: band, xRange: xRange)
        let margin = Self.median(Array(profileA[0..<max(2, xRange.count / 40)]))
        let minTrack = max(8, Int((20.0 * scale).rounded()))
        guard margin >= 0,
              let extA = Self.trackExtent(profile: profileA, margin: margin, delta: 8,
                                          minTrackPixels: minTrack),
              let extB = Self.trackExtent(profile: profileB, margin: margin, delta: 8,
                                          minTrackPixels: minTrack) else { return nil }
        // 横向范围取**两帧的并**：药丸停在某一段时，亮区只剩轨道的另一半，
        // 逐帧自算会让带子只盖住半颗胶囊（`trackExtent` 上面记的是同一件事）。
        let extent = Range<Int>(uncheckedBounds: (lower: Swift.min(extA.lowerBound, extB.lowerBound),
                                                  upper: Swift.max(extA.upperBound, extB.upperBound)))
        return CGRect(x: CGFloat(xRange.lowerBound + extent.lowerBound) / CGFloat(a.width),
                      y: CGFloat(band.lowerBound) / CGFloat(a.height),
                      width: CGFloat(extent.count) / CGFloat(a.width),
                      height: CGFloat(band.count) / CGFloat(a.height))
    }

    /// R323 / 产品面：那条位移**走得怎么样** —— 斜坡尺第一次逐帧读药丸中心。
    ///
    /// 上一轮结的是"有没有过程"（@R322 那格：开臂中间态帧数 3 对关臂 1）。到线之后剩下的问题是品质：
    /// MC-1 写着"只有手势跟手的位移才给过冲"，而这颗胶囊是**程序触发**的 ⇒ 它的像素形状必须是
    /// 一路朝一个方向、不回头。以前这句话只有纯值守卫（`damping == 1.0`）在钉，产物侧一次也没被看过。
    ///
    /// 判法：两遍各判一次（同臂两遍都必须给同一个词），词表是 `rampVerdict` 那四格。
    /// `无对象` / `没动` / 分离度不够 是**通道问题**（这一台量不出 ⇒ 具名出口，不写产品事实，D-305 同一形状）；
    /// `回头` 才是产品事实 —— 那意味着曲线里混进了过冲，第一笔该改的就是它。
    func testFilterPillRampIsMonotone() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.filterPillSlide()
        let filmA = record(scenario)
        let filmB = record(scenario)
        // 前提⓪（R324，排在帧数与带子之前）：这一卷**拍在哪一档外观里**必须是这把尺有对象的那一档。
        // 三条各拦不同的坏法，合抄成一条就分不清是谁坏的：
        //   · 场景请求的 == 尺要求的   ⇒ 拦"场景改档改错了"（M931 那一刀的靶）
        //   · 胶片实际解析到的 == 尺要求的 ⇒ 拦"请求没落进胶片"（只改 NSApp / 只改 host 那一族）
        //   · 两遍同一档               ⇒ 拦"第二遍跑到别的档里"（同臂两遍必须比同一个词）
        // 为什么这条是红的、而不是出口：亮档里轨道与药丸只差 3 级（暗档 16–22 级），
        // "带子找不到"在这两种情况下长得一模一样，而只有"档位对了仍然看不见"才是通道极限。
        // 与 R323 给 A/B 开关立的那条前置同一形状：出口不许替一把没生效的请求说话。
        XCTAssertEqual(Self.pillRampRequiredAppearanceName,
                       Self.appearanceName(forRequested: scenario.appearance),
                       "斜坡尺要求的色档是「\(Self.pillRampRequiredAppearanceName)」，而场景请求的是「"
                       + Self.appearanceName(forRequested: scenario.appearance)
                       + "」⇒ 逐行像素尺在没有对象的那一档里跑（亮档分离度只有 3 级）")
        XCTAssertEqual(Self.pillRampRequiredAppearanceName, filmA.appearanceNameAtRecord,
                       "这一卷实际拍在了「\(filmA.appearanceNameAtRecord)」档（请求「"
                       + Self.appearanceName(forRequested: scenario.appearance)
                       + "」没落进胶片）⇒ NSApp / window / host 三处里至少一处没跟上，"
                       + "后面的带子读数与色档无关的那半条结论都作废")
        XCTAssertEqual(filmA.appearanceNameAtRecord, filmB.appearanceNameAtRecord,
                       "同臂两遍拍在不同色档里（A=\(filmA.appearanceNameAtRecord)"
                       + " B=\(filmB.appearanceNameAtRecord)）⇒ 两遍比的不是同一张画面")
        guard filmA.motionFrames.count > 3, filmB.motionFrames.count > 3 else {
            emit("MOTION_NOT_RUN=too-few-frames pill-ramp A=\(filmA.motionFrames.count)"
                + " B=\(filmB.motionFrames.count) ⇒ 斜坡无从逐帧判")
            throw XCTSkip("MOTION_NOT_RUN=too-few-frames：这一卷帧数不足")
        }
        // 前提（与带子无关，R323 同一课）：首末必须真的换了档。
        // no-op 触发不许被读成"这台机器看不见"——它得红在"什么都没驱动"上。
        XCTAssertTrue(Self.premisePictureChanged(filmA.motionFrames, band: nil),
            "触发后整幅画面首末逐像素相同 ⇒ 这次点档什么都没驱动（夹具/探针坏了，不是通道看不见）。"
            + " 帧数=\(filmA.motionFrames.count)")
        // 几何全部由**这一卷自己的帧**量出来：行带 = 首末帧之间那颗"会走的洞"所在的连续行
        // （为什么不用"哪些行在变"：换档重排整个列表，列表那一片比胶囊大一个数量级）；
        // 页底档 = 轨道之外那几列的中位数；轨道范围 = 整卷取并（理由写在 `trackExtent` 上面）。
        let head = Self.raster(filmA.motionFrames[0])
        let tail = Self.raster(filmA.motionFrames[filmA.motionFrames.count - 1])
        guard head.width == tail.width, head.height == tail.height, head.width > 0, head.height > 0 else {
            emit("MOTION_NOT_RUN=pill-ramp-frame-shape 首末帧尺寸不一致 ⇒ 逐行差无从算")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-frame-shape")
        }
        let scale = Double(head.height) / 520.0
        let xRange = max(0, Int((1.0 * scale).rounded()))
            ..< min(head.width, Int((299.0 * scale).rounded()))
        let (bandOpt, bandReport) = measuredMovingHoleBand(head, tail, scale: scale)
        guard let band = bandOpt else {
            emit("MOTION_NOT_RUN=pill-ramp-no-band pill-slide-ramp 首末帧之间没有一段'结构成立、形状也像那颗胶囊'"
                + "的连续行带 ⇒ 这一台看不见胶囊走过（不写产品事实，D-305）。为什么找不到：\(bandReport)")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-band")
        }
        func profile(of image: CGImage) -> [Double] {
            let bmp = Self.raster(image)
            return Self.columnMedianProfile(pixels: bmp.pixels, bytesPerRow: bmp.width * 4,
                                            yRange: band, xRange: xRange)
        }
        let profilesA = filmA.motionFrames.map { profile(of: $0) }
        let profilesB = filmB.motionFrames.map { profile(of: $0) }
        let marginWindow = max(2, xRange.count / 40)
        let margin = Self.median(Array(profilesA[profilesA.count - 1][0..<marginWindow]))
        guard margin >= 0 else {
            emit("MOTION_NOT_RUN=pill-ramp-no-margin 页底那几列一个数都没读到")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-margin")
        }
        var extLo = Int.max, extHi = Int.min
        for values in profilesA {
            guard let e = Self.trackExtent(profile: values, margin: margin, delta: 8,
                                           minTrackPixels: max(8, Int((20.0 * scale).rounded()))) else { continue }
            extLo = min(extLo, e.lowerBound)
            extHi = max(extHi, e.upperBound)
        }
        guard extHi > extLo, extLo != Int.max else {
            emit("MOTION_NOT_RUN=pill-ramp-no-track 页底=\(String(format: "%.1f", margin))"
                + " ⇒ 这一行带里没有一段与页底不同档的轨道，尺找不到对象")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-track")
        }
        let extent = extLo..<extHi
        // R333 / BACKLOG 393：药丸那一档**不再由页底定义**（旧写法把 377 那个缺陷的画法当成了尺的定义，
        // 修法一落地这把尺就安静地 skip 掉 —— 全在 `halfLevels` 上面那段更正里）。
        // 现在两档由**首末两个 settled 臂的镜像**量出来：药丸 = 首帧左半（= 末帧右半），
        // 轨道 = 首帧右半（= 末帧左半）。逐帧的中间态不参与定档，只被这两个数去认。
        let minPillPixels = max(4, Int((12.0 * scale).rounded()))
        let firstHalves = Self.halfLevels(profile: profilesA[0], extent: extent)
        let lastHalves = Self.halfLevels(profile: profilesA[profilesA.count - 1], extent: extent)
        guard let fh = firstHalves, let lh = lastHalves else {
            emit("MOTION_NOT_RUN=pill-ramp-no-halves 轨道范围=\(extent.lowerBound)..\(extent.upperBound)"
                + " 在这台机器上分不出左右半（剖面列数不足 4）⇒ 两档无从量出")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-halves")
        }
        let levels = Self.settledPillTrackLevels(firstLeft: fh.left, firstRight: fh.right,
                                                 lastLeft: lh.left, lastRight: lh.right, delta: 8)
        func centers(_ profiles: [[Double]]) -> [Double] {
            profiles.map { values in
                guard let run = Self.pillRun(profile: values, pillLevel: levels.pill,
                                             trackLevel: levels.track, delta: 8, extent: extent,
                                             minPillPixels: minPillPixels) else { return -1 }
                return Double((run.range.lowerBound + run.range.upperBound) / 2 + xRange.lowerBound) / scale
            }
        }
        let cA = centers(profilesA), cB = centers(profilesB)
        // 分离度前提：轨道档与药丸档必须分得开（本机实测 52 对 36）。分不开就不是"没动"，
        // 是这台机器的材质把那两级洗成了同一档 ⇒ 具名出口，不许把它读成"胶囊不动"。
        let settledRun = Self.pillRun(profile: profilesA[profilesA.count - 1], pillLevel: levels.pill,
                                      trackLevel: levels.track, delta: 8, extent: extent,
                                      minPillPixels: minPillPixels)
        let separation = abs(levels.pill - levels.track)
        let trackWidthPt = Double(extent.count) / scale
        let tolerance = max(2.0, trackWidthPt * 0.02)
        emit("MOTION_PILL_RAMP_GEOM filter-pill-slide 行带=\(String(format: "%.1f", Double(band.lowerBound) / scale))"
            + "…\(String(format: "%.1f", Double(band.upperBound) / scale))pt"
            + " 轨道范围=\(String(format: "%.1f", Double(extent.lowerBound + xRange.lowerBound) / scale))"
            + "…\(String(format: "%.1f", Double(extent.upperBound + xRange.lowerBound) / scale))pt"
            + " 倍率=\(String(format: "%.2f", scale)) 页底=\(String(format: "%.1f", margin))"
            + " 色档=胶片" + filmA.appearanceNameAtRecord + "/机器" + Self.appearanceName()
            + " 轨道=\(String(format: "%.1f", levels.track))"
            + " 药丸=\(String(format: "%.1f", levels.pill))"
            + " 分离=\(String(format: "%.1f", separation)) 镜像=\(levels.mirror ? "是" : "否")"
            + " 末帧药丸宽=\(settledRun.map { $0.range.count } ?? -1)"
            + " 容差=\(String(format: "%.1f", tolerance))pt"
            + " 定位=\(bandReport)")
        // 前提①（R333）：两档必须由**镜像**背书，否则 `levels` 里"哪一档是选中那颗"是猜的。
        // 首末两半没互换 ⇒ 要么这两帧不是两个稳定态（触发没生效），要么轨道不是那颗胶囊；
        // 两种都不是"斜坡走得平不平"的证据，也不许被读成产品缺陷 ⇒ 具名出口（D-305 同一形状）。
        guard levels.mirror else {
            emit("MOTION_NOT_RUN=pill-ramp-no-mirror 首帧左/右=\(String(format: "%.1f", fh.left))"
                + "/\(String(format: "%.1f", fh.right)) 末帧左/右=\(String(format: "%.1f", lh.left))"
                + "/\(String(format: "%.1f", lh.right))（delta=8）"
                + " ⇒ 两臂没互换，药丸档与轨道档没有对照物，逐帧中心不作数")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-mirror")
        }
        guard separation >= 8 else {
            emit("MOTION_NOT_RUN=pill-ramp-low-separation 轨道与药丸两档之差=\(String(format: "%.1f", separation))"
                + " < 8 ⇒ 这一台的通道分不开这两级，斜坡品质无从逐帧判（分离度是量出来的，不是假设）")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-low-separation")
        }
        // R325 / D-311：**退化采样不许升成品质结论**。词表（单调 / 回头 / 没动 / 无对象）默认输入里
        // 至少有一颗中间样本。RUN=40053805112 那一卷的中心序列是 `80.0, 219.0, 219.0, …`——
        // 一步跳变照样被判成"单调、最大倒退 0.0pt"，那张证是空转出来的。
        // 本机给相反方向的证据（中间样本 4 颗，见 MOTION_PILL_RAMP 的 中心= 序列）⇒ 这条出口放掉的是通道。
        let interA = Self.intermediateCount(cA, tolerance: tolerance)
        let interB = Self.intermediateCount(cB, tolerance: tolerance)
        guard interA > 0 && interB > 0 else {
            emit("MOTION_NOT_RUN=pill-ramp-no-intermediate filter-pill-slide 两遍的中间样本 A=\(interA)"
                + " B=\(interB)（容差 \(String(format: "%.1f", tolerance))pt、首末 \(cA.first ?? -1)"
                + "→\(cA.last ?? -1)）⇒ 这一台的采样里这条位移是一步跳变，"
                + "『走得平不平』没有可判的东西（不写产品事实，D-305 同一形状）")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-intermediate")
        }
        let vA = Self.rampVerdict(cA, tolerance: tolerance)
        let vB = Self.rampVerdict(cB, tolerance: tolerance)
        emit("MOTION_PILL_RAMP filter-pill-slide A 判定=\(vA.label) \(vA.detail)"
            + " 中心=" + cA.map { String(format: "%.1f", $0) }.joined(separator: ",")
            + " ｜ B 判定=\(vB.label) \(vB.detail)")
        guard vA.label != "无对象" && vB.label != "无对象" else {
            emit("MOTION_NOT_RUN=pill-ramp-no-object A=\(vA.detail) B=\(vB.detail)"
                + " ⇒ 有帧在轨道范围里读不出药丸连续段，斜坡品质在这一台判不了")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-no-object")
        }
        guard vA.label != "没动" && vB.label != "没动" else {
            emit("MOTION_NOT_RUN=pill-ramp-flat A=\(vA.detail) B=\(vB.detail)"
                + " ⇒ 两遍都读成『药丸没挪』：这一台的采样看不见这条斜坡（不写产品事实，D-305）")
            throw XCTSkip("MOTION_NOT_RUN=pill-ramp-flat")
        }
        // 两遍必须给**同一个词**：不一致就是通道在抖，不挑一次算数（R47）。
        XCTAssertEqual(vA.label, vB.label,
            "同臂两遍的斜坡结论不一致（A=\(vA.label) \(vA.detail) / B=\(vB.label) \(vB.detail)）"
            + " ⇒ 这条判据今天没有对照物")
        // 方向：这一卷是 `.all` → `.favorites`，第二段在右 ⇒ 中心必须往右走。
        XCTAssertLessThan(cA[0], cA[cA.count - 1],
            "首帧中心 \(String(format: "%.1f", cA[0]))pt 不在末帧"
            + " \(String(format: "%.1f", cA[cA.count - 1]))pt 左边 ⇒ 带子或方向错了：\(vA.detail)")
        XCTAssertEqual(vA.label, "单调",
            "药丸的横移读成了「\(vA.label)」：\(vA.detail) ⇒ MC-1 说程序触发的位移不给过冲，"
            + "而『回头』正是过冲的像素形状 —— 这是产品事实，改曲线，不是改这条判据。")
    }

    /// R324 / 缺席计数：这一卷的场景工厂**有几颗钉了色档**，没钉的报名字。
    ///
    /// 本轮的靶是逐行像素尺（胶囊），它已经被 `testFilterPillRampIsMonotone` 的前提⓪钉住了；
    /// 剩下那些工厂今天仍跟着系统的"自动"走 —— 它们的读数（帧数、峰值、比例带）与色档**弱**相关，
    /// 所以本轮不把它们一起钉上（那会在同一笔提交里改动十几条判据的读数而一条也没重测）。
    /// 这条不写"已判不做"，它写的是**数出来的缺席**：名字、颗数、以及"哪一颗必须钉着"那颗棘轮。
    func testFilmScenarioAppearancePinCensusNamesEveryAbsence() throws {
        let text = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        let census = Self.scenarioPinCensus(code: text)
        let total = census.pinned.count + census.unpinned.count
        let unpinnedList = census.unpinned.sorted().joined(separator: ",")
        emit("MOTION_SCENARIO_APPEAR 工厂=\(total) 钉了=\(census.pinned.count)"
            + " 没钉=\(census.unpinned.count)"
            + " 钉了名单=\(census.pinned.sorted().joined(separator: ","))"
            + " 没钉名单=\(unpinnedList.isEmpty ? "无" : unpinnedList)")
        XCTAssertGreaterThanOrEqual(total, 10,
            "只认出 \(total) 颗场景工厂（这台文件里 grep `-> Scenario {` 是十几颗）"
            + " ⇒ 点名器瞎了，下面那句『没钉名单』不能算读数")
        XCTAssertTrue(census.pinned.contains("filterPillSlide"),
            "胶囊那两颗判据（斜坡尺 / 过程证人）用的工厂 `filterPillSlide` 没钉色档"
            + " ⇒ 前提⓪要拦的那件事就在这儿：亮档里轨道与药丸只差 3 级，尺没有对象")
    }

    /// 纯函数：把"同一颗场景在两档色档里的读数"归成四格词表（R325 立，R326 换统计量 / BACKLOG 383、386）。
    ///
    /// 为什么要抽成纯函数而不直接在探针里写 if：不抽出来，这四格词表就只活在一次真机跑里，
    /// 没人能证明"漂"与"敏感"的分界真的在 5% / 25%，也没人能证明"换对象"优先于相对差
    /// （R146 那一族：写死在探针里的分类法等于没有分类法）。
    ///
    /// R326 改的是**收哪几个数**：R325 收的是两臂**峰值**，而峰值是采样通道的量（见
    /// `endpointChangedFraction` 的注释），于是同一个 commit 在本机给"敏感=0"、在 runner 给
    /// "敏感=2" —— 两台机器对同一份代码做出**相反的动作**。现在收三颗通道无关的量：
    /// **首末面积**（哪些像素动了）、**动过的并集**（整卷里动过多少像素，补"动了又回来"）、
    /// **首末墨量差**（同样的面积在暗档里差 170 级、亮档里差 65 级时它要能看见），
    /// 取三者较大的相对差：任何一颗单独都可能恰好看不见，而"选哪一颗"不能由答案决定。
    /// 阈值 5% / 25% 本轮**一个字没动** —— 它们该不该在这儿是 BACKLOG 386 的问题，
    /// 本轮没有资格顺手重标；换统计量之后重测出来的分布才是 386 能拿来定线的数。
    ///
    /// 顺序是承重的：`换对象` 排在相对差之前 —— 一档看得见、另一档看不见时，
    /// 相对差再小也是**前提**翻了脸，那与"数值漂了一点"是修法相反的两件事。
    static func appearanceDependenceVerdict(endpointDark: Double, endpointLight: Double,
                                            unionDark: Double, unionLight: Double,
                                            inkDark: Double, inkLight: Double,
                                            changedDark: Bool, changedLight: Bool) -> String {
        if let flipped = Self.flippedAppearanceWord(changedDark: changedDark, changedLight: changedLight) {
            return flipped
        }
        let rel = Swift.max(Self.relativeDifference(endpointDark, endpointLight),
                            Self.relativeDifference(unionDark, unionLight),
                            Self.relativeDifference(inkDark, inkLight))
        return Self.verdictFromRelativeDifference(rel)
    }

    /// 前提那一格只住一处（R326）：两口径共用。写两遍就会有两根可以各自腐烂的针 ——
    /// 本轮新加 `peakVerdict` 时正是这样把 R325 的 M940 顶成了"锚点命中 2 次"，
    /// 那一格当场报 NOT_RUN（刀没下），所以这不是洁癖，是被抓过的形状。
    static func flippedAppearanceWord(changedDark: Bool, changedLight: Bool) -> String? {
        changedDark != changedLight ? "换对象" : nil
    }

    /// 两条分界也只住一处，理由同上：`敏感` 与 `漂` 的字面量若有两份，
    /// 改一份留下另一份，"这两条线在哪"就又是注释里的分类法了（BACKLOG 386 要的正是能一次改对）。
    static func verdictFromRelativeDifference(_ rel: Double) -> String {
        if rel > 0.25 { return "敏感" }
        if rel > 0.05 { return "漂" }
        return "同"
    }

    /// 相对差：分母取两臂里较大的那个，两臂都是 0 时读 0（空白对照那类不许变 NaN）。
    static func relativeDifference(_ a: Double, _ b: Double) -> Double {
        let denom = Swift.max(a, b, 0.001)
        return Swift.abs(a - b) / denom
    }

    /// R325 / BACKLOG 383：把"12 颗没钉色档"从**缺席计数**变成**逐颗读数**。
    ///
    /// 同一颗场景在暗档与亮档里各拍一卷，比的是**它自己那把尺的读数**，四格分类：
    ///   `换对象` = 一档看得见变化、另一档看不见 ⇒ 这条判据的**前提**随色档翻脸，必须钉；
    ///   `敏感`   = 两边都看得见，但通道无关读数的相对差 > 25% ⇒ 读数随色档走，钉；
    ///   `漂`     = 相对差 5–25% ⇒ 登记，本轮不钉（钉了就要重测那条判据的历史读数）；
    ///   `同`     = 相对差 < 5% ⇒ **有数了**才许写"不依赖色档"，而不是"猜它不依赖"。
    /// 这一格判的是尺，不是产品；它自己不红任何产品事实，除了下面三条通道前提。
    ///
    /// 三条通道前提为什么是红的：
    /// ① 两臂若其实拍在同一档里，"读数相同"就是两卷同一张图的同义反复（R38 / R161 那一族）；
    /// ② 两臂的**帧数或像素尺寸**若不同，"同一个统计量"就是两份不同的画面，比不得；
    /// ③ 峰值那一口径本轮起**只印不判**，但仍要印 —— 它是 R325 那两格结论的出处，
    ///    读者要能看见"换统计量把哪几颗的判定改了"，否则这条更正本身就成了新的一句推测。
    func testFilmScenarioAppearanceDependenceIsMeasuredPerScenario() throws {
        try skipUnlessEnabledAndCapable()
        let subjects = Scenario.unpinnedAppearanceProbe()
        let text = try String(contentsOf: URL(fileURLWithPath: #filePath), encoding: .utf8)
        let census = Self.scenarioPinCensus(code: text)
        let probeNames = subjects.map { $0.factory }.sorted()
        XCTAssertEqual(probeNames, census.unpinned.sorted(),
            "色档 A/B 的对象表与点名器数出来的『没钉名单』不是同一份 ⇒ 探针会静默漏掉某一颗场景"
            + "（漏掉的那颗正是「我们以为量过了」的那颗）")
        var sameCount = 0
        var driftCount = 0
        var sensitiveCount = 0
        var flippedCount = 0
        var peakSame = 0
        var peakDrift = 0
        var peakSensitive = 0
        var peakFlipped = 0
        var verdictMismatch = 0
        var granularityGap = 0
        // 全局方向那一格（R326 实测逼出来的）：墨量差在 11 颗有变化的场景里**每一颗都是亮臂更大**。
        // 那不是 11 条"这条判据随色档走"的证据，那是一条"这颗尺带着一整个色档的系统偏移"的证据 ——
        // 而 25% 那条线当初是在**没有这个偏移的峰值口径**上拍的。所以这一格必须印出来：
        // 它是"本轮不许拿 敏感=8 去钉 8 颗"那句话的读数，不是注释里的推测。
        var ratios: [Double] = []
        var changedBoth = 0
        for subject in subjects {
            let dark = record(subject.scenario.pinned(to: .darkAqua))
            let light = record(subject.scenario.pinned(to: .aqua))
            XCTAssertEqual(dark.appearanceNameAtRecord, "暗",
                "探针说在暗档、胶片实际拍在「\(dark.appearanceNameAtRecord)」⇒ 两臂对照不成立（\(subject.factory)）")
            XCTAssertEqual(light.appearanceNameAtRecord, "亮",
                "探针说在亮档、胶片实际拍在「\(light.appearanceNameAtRecord)」⇒ 两臂对照不成立（\(subject.factory)）")
            // 通道同一性（两件事，别混）：①**画面**必须是同一块 —— 像素尺寸严格相等；
            // ②采样**粒度**要可比 —— 帧数由墙上时钟决定，同一进程里两臂差 1 帧是常态
            //   （本轮实测：`blank` 暗 27 / 亮 28 ⇒ 第一版写成"帧数必须相等"当场红，
            //   那是判据自己变窄，不是通道坏了）。所以这里判的是 25% 的容差，
            //   而它之所以还值得判：三颗通道无关的统计量只要求"过程被采到过"，
            //   一臂塌到零帧就再没什么"通道无关"可言 —— 那用得上，就不能当噪声放行。
            let comparable = Self.samplingComparable(dark.motionFrames.count, light.motionFrames.count)
            XCTAssertEqual(dark.motionFrames.first.map(Self.pixelSizeText) ?? "空",
                           light.motionFrames.first.map(Self.pixelSizeText) ?? "空",
                           "两臂像素尺寸不同 ⇒ 亮的那一臂拍的是另一块画面（\(subject.factory)）")
            if !comparable {
                granularityGap += 1
                emit("MOTION_SCENARIO_AB_NOT_COMPARABLE " + subject.factory
                     + " 帧数暗=" + String(dark.motionFrames.count)
                     + " 帧数亮=" + String(light.motionFrames.count)
                     + " ⇒ 这一颗的两臂采样粒度差到不能比，判定不许当'不依赖色档'的证据（也不红产品事实）")
            }
            let peakDark = Self.peak(Self.deltas(dark.motionFrames, band: nil))
            let peakLight = Self.peak(Self.deltas(light.motionFrames, band: nil))
            let endpointDark = Self.endpointChangedFraction(dark.motionFrames)
            let endpointLight = Self.endpointChangedFraction(light.motionFrames)
            let unionDark = Self.everChangedFraction(dark.motionFrames)
            let unionLight = Self.everChangedFraction(light.motionFrames)
            let inkDark = Self.endpointInkDifference(dark.motionFrames)
            let inkLight = Self.endpointInkDifference(light.motionFrames)
            let changedDark = Self.premisePictureChanged(dark.motionFrames, band: nil)
            let changedLight = Self.premisePictureChanged(light.motionFrames, band: nil)
            if endpointDark > 0, endpointLight > 0 {
                changedBoth += 1
                if inkLight > 0 { ratios.append(inkDark / inkLight) }
            }
            // 分类走纯尺（与证人同一颗尺子，R68）：探针自己 if 一遍，证人就只是在证它自己抄的那份。
            let verdict = Self.appearanceDependenceVerdict(endpointDark: endpointDark,
                                                           endpointLight: endpointLight,
                                                           unionDark: unionDark, unionLight: unionLight,
                                                           inkDark: inkDark, inkLight: inkLight,
                                                           changedDark: changedDark, changedLight: changedLight)
            let peakVerdict = Self.peakVerdict(peakDark: peakDark, peakLight: peakLight,
                                               changedDark: changedDark, changedLight: changedLight)
            if verdict != peakVerdict { verdictMismatch += 1 }
            switch verdict {
            case "换对象": flippedCount += 1
            case "敏感": sensitiveCount += 1
            case "漂": driftCount += 1
            default: sameCount += 1
            }
            switch peakVerdict {
            case "换对象": peakFlipped += 1
            case "敏感": peakSensitive += 1
            case "漂": peakDrift += 1
            default: peakSame += 1
            }
            emit("MOTION_SCENARIO_AB " + subject.factory + " 判定=" + verdict
                 + " 首末暗=" + String(format: "%.4f", endpointDark)
                 + " 首末亮=" + String(format: "%.4f", endpointLight)
                 + " 并集暗=" + String(format: "%.4f", unionDark)
                 + " 并集亮=" + String(format: "%.4f", unionLight)
                 + " 墨暗=" + String(format: "%.4f", inkDark)
                 + " 墨亮=" + String(format: "%.4f", inkLight)
                 + " 暗换档=" + (changedDark ? "是" : "否") + " 亮换档=" + (changedLight ? "是" : "否"))
            // 只印不判的那一口：R325 的结论就是从这颗峰值来的，留着它读者才能对账。
            emit("MOTION_SCENARIO_AB_CHANNEL " + subject.factory
                 + " 峰值口径判定=" + peakVerdict
                 + " 峰值暗=" + String(format: "%.4f", peakDark)
                 + " 峰值亮=" + String(format: "%.4f", peakLight)
                 + " 峰值相对差=" + String(format: "%.1f", Self.relativeDifference(peakDark, peakLight) * 100.0) + "%"
                 + " 帧数=" + String(dark.motionFrames.count))
        }
        // 分母同一性（R326）：`亮臂更大=11/11` 那句是本轮"不拿 敏感=8 去钉 8 颗"的**读数**，
        // 所以它不能只是打出来 —— 打出来的数要有一个它会红的地方。这里钉的是：
        // 凡是两臂面积都读到变化的场景，墨量那颗尺必须也在样本里（少一颗就是尺瞎了一半，
        // 而瞎掉的那一半正好会让"全是同一侧"这句话变成挑出来的样本）。
        XCTAssertEqual(ratios.count, changedBoth,
            "两臂面积都有变化的场景是 \(changedBoth) 颗，而墨量比值只收了 \(ratios.count) 颗 ⇒ "
                + "比值那一格的样本被悄悄缩小了，'亮臂更大=N' 不能代表全部有变化的场景")
        XCTAssertGreaterThan(changedBoth, 1,
            "只有 \(changedBoth) 颗场景在两臂里都读到了画面变化 ⇒ 对象表里全是空胶片，"
                + "A/B 分类没有可判的东西（这条要红，不许让'同=12'那种数糊过去）")
        let sortedRatios = ratios.sorted()
        emit("MOTION_SCENARIO_AB_MAGNITUDE 有变化=" + String(ratios.count)
             + " 亮臂更大=" + String(sortedRatios.filter { $0 < 1.0 }.count)
             + " 暗臂更大=" + String(sortedRatios.filter { $0 > 1.0 }.count)
             + " 比值暗除亮=" + (sortedRatios.isEmpty ? "无"
                 : String(format: "%.2f…%.2f", sortedRatios.first!, sortedRatios.last!))
             + "（全在同一侧 ⇒ 墨量这颗尺带一个色档级系统偏移，5%/25% 在它身上没有出处：BACKLOG 387）")
        emit("MOTION_SCENARIO_AB_SUMMARY 场景=" + String(subjects.count)
             + " 同=" + String(sameCount) + " 漂=" + String(driftCount)
             + " 敏感=" + String(sensitiveCount) + " 换对象=" + String(flippedCount)
             + " 粒度不可比=" + String(granularityGap)
             + "（口径=首末面积∪动过并集∪首末墨量 取较大者，一颗不许替另一颗说话；钉档判据：换对象/敏感 ⇒ 该钉，漂 ⇒ 登记不钉）")
        emit("MOTION_SCENARIO_AB_SUMMARY_CHANNEL 峰值口径 同=" + String(peakSame)
             + " 漂=" + String(peakDrift) + " 敏感=" + String(peakSensitive)
             + " 换对象=" + String(peakFlipped)
             + " 与通道无关口径判定不同=" + String(verdictMismatch)
             + "（这一格只印不判：峰值随采样通道走，R326 / 本机 0.2598 对 runner 0.7208）")
    }

    /// R326：R325 那一版口径（比峰值）保留成**只印不判**的对照，好让读者看见换了统计量之后
    /// 哪几颗的判定改了。它不再决定"要不要钉"，所以它不该被当成第二把尺子引用 ——
    /// 分界与前提两格都复用同一颗纯函数（`verdictFromRelativeDifference` / `flippedAppearanceWord`），
    /// 这样"敏感"这条线在文件里只有一个字面量：两份线就能被各自改一次而没人发现。
    static func peakVerdict(peakDark: Double, peakLight: Double,
                            changedDark: Bool, changedLight: Bool) -> String {
        if let flipped = Self.flippedAppearanceWord(changedDark: changedDark, changedLight: changedLight) {
            return flipped
        }
        return Self.verdictFromRelativeDifference(Self.relativeDifference(peakDark, peakLight))
    }

    /// 一张帧的像素尺寸文本（通道同一性那条断言用它比"两臂拍的是不是同一块画面"）。
    static func pixelSizeText(_ image: CGImage) -> String {
        "\(image.width)×\(image.height)"
    }

    /// 两臂的**采样粒度**是否可比（R326）。写成纯函数是因为这条容差必须能被证伪：
    /// 差 1 帧要放行（时钟抖动，本机实测），一臂塌到 3 帧要拦住（那卷根本没拍到过程）。
    /// 形状：允许 25% 的相对差，另外再给 1 帧的绝对豁免 —— 没有后者，7 帧对 8 帧这种
    /// 小样本会被相对差判死，而那是同一种拍法。
    static func samplingComparable(_ a: Int, _ b: Int) -> Bool {
        let gap = Swift.abs(a - b)
        let denom = Swift.max(a, b, 1)
        return gap <= 1 || Double(gap) / Double(denom) <= 0.25
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
        let onPerArm = Self.transitionFrameCount(on)
        let offPerArm = Self.transitionFrameCount(off)
        // R192 / BACKLOG 216：本条问的是"两臂**相同**吗"，而两臂各自的计数是**两把不同的线**
        // ⇒ 与 212 同形（峰值大的那臂被一条更高的线先判停）。现在同一条线为主、旧口径并列，
        // 而且**两把尺都必须说"相同"**这条免责才成立 —— 只准变严，不准变松。
        let sharedLineSymbol = Self.sharedMovingFloor([on, off])
        let onShared = Self.transitionFrameCount(on, sharedFloor: sharedLineSymbol)
        let offShared = Self.transitionFrameCount(off, sharedFloor: sharedLineSymbol)
        let soundSymbol = Self.sharedLineIsSound([on, off])
        let floorSymbol = String(format: "%.4f", sharedLineSymbol)
        let peakSymbol = String(format: "%.3f", Self.peak(on)) + "/" + String(format: "%.3f", Self.peak(off))
        let agreementSymbol = Self.armAgreementReading(sameUnderShared: onShared == offShared,
                                                      sameUnderPerArm: onPerArm == offPerArm,
                                                      sound: soundSymbol)
        emit("MOTION_SYMBOL row-star 同一条线=\(floorSymbol) 共用线安全=\(soundSymbol) 峰值=\(peakSymbol)"
             + " 新口径 开=\(onShared) 关=\(offShared)"
             + " ｜ 旧口径（各自归一化）开=\(onPerArm) 关=\(offPerArm)"
             + " ⇒ \(agreementSymbol)")
        XCTAssertGreaterThan(Self.peak(on), Self.minimumVisibleChange,
                             "带里什么都没变 ⇒ 我连星标在哪都没框到，这条'测不到'的结论本身不成立")
        XCTAssertTrue(onShared == offShared && onPerArm == offPerArm,
                      "两把尺里至少一把说两臂有别 ⇒ 这条『量不到』的边界可能要撤。先读上一行的合读法："
                        + "它说『共用线不安全』⇒ 那是幅度不对称把小臂判成 0 帧（BACKLOG 217），不是产品有差别；"
                        + "两把尺都说有别 ⇒ 尺子真的看得见，把本条改成真判据，"
                        + "并把 `AGENT_UI_AUDIT` 里那条'量不到'的边界撤掉。"
                        + " 读数：新口径 开=\(onShared) 关=\(offShared) / 旧口径 开=\(onPerArm) 关=\(offPerArm)"
                        + " 线=\(floorSymbol) 峰值=\(peakSymbol) 安全=\(soundSymbol)")
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
        let animatedStamps = probe.lastStamps
        let animatedInterval = Self.sampleIntervalMilliseconds(animatedStamps)
        let instantFilm = probe.record(animation: QuickPickController.rowAnimationOptions(
            reduceMotion: true, animationsEnabled: true))
        let instantStamps = probe.lastStamps
        let instant = Self.deltas(instantFilm, band: band)
        let instantInterval = Self.sampleIntervalMilliseconds(instantStamps)
        let animatedSpan = Self.transitionFrameCount(animated)
        let instantSpan = Self.transitionFrameCount(instant)
        // R193 / BACKLOG 217：帧数只是**对照** —— 这条判定欠的是连续段时长（散着抖三下也够 3 帧，
        // 而一帧多长由抓帧耗时决定）。本轮先把两臂的时间轴送进日志，判据换形等 runner 那份分布。
        let animatedProcess = Self.armProcessInIntervals(stamps: animatedStamps, fractions: animated)
        let instantProcess = Self.armProcessInIntervals(stamps: instantStamps, fractions: instant)
        emit("MOTION_NATIVE row-insert 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated))) 采样≈\(animatedInterval)ms 过程=\(Self.processReading(animatedProcess, span: animatedSpan))")
        emit("MOTION_NATIVE row-insert 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant))) 采样≈\(instantInterval)ms 过程=\(Self.processReading(instantProcess, span: instantSpan))")
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
        let animatedStamps = probe.lastStamps
        let animatedInterval = Self.sampleIntervalMilliseconds(animatedStamps)
        let instantFilm = probe.record(animation: QuickPickController.rowAnimationOptions(
            reduceMotion: true, animationsEnabled: true))
        let instantStamps = probe.lastStamps
        let instant = Self.deltas(instantFilm, band: band)
        let instantInterval = Self.sampleIntervalMilliseconds(instantStamps)
        let animatedSpan = Self.transitionFrameCount(animated)
        let instantSpan = Self.transitionFrameCount(instant)
        // R193 / BACKLOG 217：`nativeMoveVerdict` 吃的两个数都是**各自归一化的帧对个数**，
        // 而 `moveRow` 动不动由 `allowsImplicitAnimation` 决定 ⇒ 三态结论欠的仍是时间轴。
        // 本机这一处 skip（`active=false`）⇒ 本轮只送读数，换判据等 runner 的分布。
        let animatedProcess = Self.armProcessInIntervals(stamps: animatedStamps, fractions: animated)
        let instantProcess = Self.armProcessInIntervals(stamps: instantStamps, fractions: instant)
        emit("MOTION_NATIVE row-move 开 帧数=\(animatedSpan) 峰值=\(String(format: "%.3f", Self.peak(animated)))"
            + " 采样≈\(animatedInterval)ms 过程=\(Self.processReading(animatedProcess, span: animatedSpan))")
        emit("MOTION_NATIVE row-move 关 帧数=\(instantSpan) 峰值=\(String(format: "%.3f", Self.peak(instant)))"
            + " 采样≈\(instantInterval)ms 过程=\(Self.processReading(instantProcess, span: instantSpan))")
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
        // R193 / BACKLOG 217：原来这两句直接把 `recordProductSequence` 的返回值喂给差分算法，
        // 于是**时刻**只剩最后那一臂的（`probe.lastStamps` 被第二臂覆盖）⇒ 想给第一臂量时间轴，
        // 拿到的会是另一臂的钟（R91：对照自己也要防量错对象）。先各存一份，再量。
        let sameFilm = probe.recordProductSequence(selectionChanges: false)
        let sameStamps = probe.lastStamps
        let sameRow = Self.deltas(sameFilm)
        let movedFilm = probe.recordProductSequence(selectionChanges: true)
        let movedStamps = probe.lastStamps
        let moved = Self.deltas(movedFilm)
        let sameSpan = Self.transitionFrameCount(sameRow)
        let movedSpan = Self.transitionFrameCount(moved)
        let sameProcess = Self.armProcessInIntervals(stamps: sameStamps, fractions: sameRow)
        let movedProcess = Self.armProcessInIntervals(stamps: movedStamps, fractions: moved)
        emit("MOTION_SEQUENCE 选中没变 帧数=\(sameSpan) 峰值=\(String(format: "%.3f", Self.peak(sameRow))) 过程=\(Self.processReading(sameProcess, span: sameSpan))")
        emit("MOTION_SEQUENCE 选中变了 帧数=\(movedSpan) 峰值=\(String(format: "%.3f", Self.peak(moved))) 过程=\(Self.processReading(movedProcess, span: movedSpan))")
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
    /// R82 / BACKLOG 113：这条判据不再数帧对。
    ///
    /// 换掉的理由是 R80 的 CI 读数，不是审美：runner 那一遍 `变化帧对=2 / 帧数=23 / 采样≈115ms`，
    /// 本机是 `23 / 48 / 53ms`，而**两边峰值都是 0.015**。
    /// 也就是说"几对在变"这一列量的是这台机器多久拍一张，不是这条循环有没有在跑 ——
    /// 与 R47 把淡入从帧数换成时长轴是同一件事的下半场（BACKLOG 110 说的"判据不许押在采样上"，
    /// 那一族在这里的形状是"押在帧数上"）。
    ///
    /// 现在的判据读 **coverage**（变化覆盖了整卷时长的几成，时间之比 ⇒ 与帧数无关），
    /// 并且带**两颗同画法证人**（`GradientTickView` 的两个参数档），因为 R81 的 CI 把一颗打回了：
    /// 那一遍 runner 上产品读 `变化帧对=2 / 帧数=27 / 峰值=0.015`，而唯一那颗证人（20Hz、亮带抬 0.39）
    /// 读 `帧数=21 峰值=0.029 变化帧对=13` —— 如果就这么判 `.productRed`，那句说过头了：
    /// 两颗之间差着**节拍**（20Hz vs 产品 30Hz）和**对比度**（抬 0.39 vs 抬 0.12），
    /// "这台机器带得动 20Hz 的高对比循环"并不蕴含"带得动产品那一档"。
    /// 所以 R68 那条"证人必须与判据问同一句话"在这里落成一个具体的数：**等节拍**。
    ///
    /// * 等节拍证人（30Hz、抬 0.12，四个数由 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住等于产品）
    ///   决定"产品红 vs 环境不行"那一分界。
    /// * 粗节拍证人（20Hz、抬 0.45）只守最硬那支：它都没拍到任何变化 ⇒ 签字的人没来上班 ⇒ 红。
    ///
    /// `requireObservableMotion(.gradient)` 问的是弱一题（"看不看得见一次渐变变化"），
    /// 那一题 runner 是"看得见"，所以它放行了判据，却拦不住一条**因为采样节拍**而红的判据。
    ///
    /// 处置：产品在跑 ⇒ 绿；等节拍证人在跑而产品没跑 ⇒ **红**；等节拍证人也没跑 ⇒ 点名 not-run；
    /// 连粗节拍证人整卷都没拍到东西 ⇒ 证人坏了，红（否则"环境"这一支永远有人签字）。
    func testSkeletonSweepActuallySweeps() async throws {
        // 能力闸门 skip 之前先打一行状态（R85 / BACKLOG 118）：闸门那一步数的是"这一族今天
        // 到底说没说一句话"，而 skip 恰好是最容易什么都不留下的那条路 —— 没有这一行，
        // "被闸门挡在门外"与"判据坏了没打读数"在日志里长得一模一样。
        do { try skipUnlessEnabledAndCapable() } catch {
            emit("MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate")
            throw error
        }
        let probe = SkeletonProbe()
        // 一卷就是**一对**（帧 + 它们的时刻）。R82 之前这里写的是 `probe.lastStamps`，
        // 而后一卷会把它覆盖掉 —— 见 `GrabbedFilm` 的注释与 U-155。
        // R84：产品这一卷进了缓存，因为"亮带在不在跑"（这一条）与"亮带是不是整组一条"
        // （`testSkeletonSweepIsOneBand`）必须读**同一卷**，各抓各的就不互相印证了。
        let runningFilm = Self.shimmerFilm()
        let stoppedFilm = probe.record(reduceMotion: true)
        let running = Self.deltas(runningFilm.frames)
        let interval = Self.sampleIntervalMilliseconds(runningFilm.stamps)
        let stopped = Self.deltas(stoppedFilm.frames)
        let shape = Self.loopShape(fractions: running, stamps: runningFilm.stamps)
        let stoppedShape = Self.loopShape(fractions: stopped, stamps: stoppedFilm.stamps)
        let rateWitness = Self.loopWitness(.gradientAtProductRate)
        let coarseWitness = Self.loopWitness(.gradient)
        // 结论行在所有闸门之前（R53 那一课：抛出去之后这行就是唯一的痕迹）。
        emit("MOTION_SHIMMER 扫 帧数=\(runningFilm.frames.count) 变化帧对=\(Self.transitionFrameCount(running)) "
            + "峰值=\(String(format: "%.3f", Self.peak(running))) 采样≈\(interval)ms "
            + "coverage=\(String(format: "%.3f", shape.coverage))(地板 \(String(format: "%.2f", LoopShape.minCoverage))) "
            + "记录时长=\(String(format: "%.0f", shape.recordedMilliseconds))ms 判定=\(Self.loopLabel(shape.verdict))")
        emit("MOTION_SHIMMER 停 变化帧对=\(Self.transitionFrameCount(stopped)) "
            + "峰值=\(String(format: "%.3f", Self.peak(stopped))) "
            + "coverage=\(String(format: "%.3f", stoppedShape.coverage))")
        emit("MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=\(rateWitness.pairs) "
            + "在变=\(rateWitness.changingPairs) 峰值=\(String(format: "%.3f", rateWitness.peak)) "
            + "coverage=\(String(format: "%.3f", rateWitness.coverage)) 判定=\(Self.loopLabel(rateWitness.verdict))")
        emit("MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45，只签字'看得见这种画法') 帧对=\(coarseWitness.pairs) "
            + "在变=\(coarseWitness.changingPairs) 峰值=\(String(format: "%.3f", coarseWitness.peak)) "
            + "coverage=\(String(format: "%.3f", coarseWitness.coverage)) 判定=\(Self.loopLabel(coarseWitness.verdict))")
        // 本轮的真实看图：这条扫光**第一次有条带图可看**（以前只有数字与帧数）。
        // 放在所有闸门之前 —— 判据红了也要留下一张能看的。
        writeStrip("skeleton-sweep", Array(runningFilm.frames.prefix(24)))
        emit("MOTION_SHIMMER_STRIP 前 24 帧排成条带（六列）⇒ 眼睛判的是『亮带一路扫过去』，"
            + "这把尺判的是 coverage，两者不许互相替")
        // 这卷**真的抓了这么久**的钉子。R82 的第一版把它挂在 `shape.recordedMilliseconds` 上，
        // 而那个数在"整卷什么都没变"时被 guard 归零 ⇒ R82 的 CI 上 runner 读到峰值 0.000，
        // 于是"这台机器看不见运动"被改写成"探针坏了"（一条假红，本轮修的就是它）。
        // 前提是**录像的性质**，不是运动的性质：一条静止 2.5 秒的卷仍然是 2.5 秒 ⇒ 从时刻本身读。
        let premise = Self.filmPremise(frames: runningFilm.frames.count, stamps: runningFilm.stamps)
        emit("MOTION_SHIMMER_FILM 帧=\(runningFilm.frames.count) 时刻=\(runningFilm.stamps.count) "
            + "配对=\(premise.paired ? "是" : "否") 卷长=\(String(format: "%.0f", premise.spanMilliseconds))ms"
            + "（探针声明 \(String(format: "%.0f", loopFilmSeconds * 1000))ms）"
            + " ｜ 结论尺报的记录时长=\(String(format: "%.0f", shape.recordedMilliseconds))ms"
            + " —— 后者在峰值 0 时**必然**是 0，所以前提不许挂在它身上")
        XCTAssertTrue(premise.paired,
                      "这一卷的时刻条数与帧数不是一对 ⇒ 它吃的不是这一卷的时刻（U-155 那一族）。"
                          + "帧=\(runningFilm.frames.count) 时刻=\(runningFilm.stamps.count)")
        XCTAssertEqual(premise.spanMilliseconds, loopFilmSeconds * 1000, accuracy: loopFilmSeconds * 250,
                       "这一卷只抓了 \(String(format: "%.0f", premise.spanMilliseconds))ms，而探针声明要抓 "
                           + "\(String(format: "%.0f", loopFilmSeconds * 1000))ms ⇒ coverage 的分母不对，"
                           + "判定无论红绿都没有依据（中间有别的东西占住了主线程，或探针提前收卷）")
        let disposition = Self.shimmerDisposition()
        // 状态行排在**所有闸门与 XCTFail 之前**（R53 那一课：抛出去之后这行就是唯一的痕迹），
        // 且它是 `motion_floor_gate.py` 的 `loops` 那一节唯一读的东西 —— 判据的结论可以随机器翻面，
        // 但"今天说没说过这句话"不许翻面（BACKLOG 118）。
        emit("MOTION_SHIMMER_STATE 判定=\(Self.loopStateLabel(disposition)) "
            + "原因=\(Self.loopStateReason(disposition))")
        switch disposition {
        case .ok:
            break
        case .productRed:
            XCTFail("骨架扫光只覆盖了整卷 \(String(format: "%.3f", shape.coverage)) 的时间（\(shape.changingPairs)/\(shape.pairs) 对在变），"
                    + "而**同一颗形状出口、同一条三段渐变、同一档节拍、同一档推进量、同一档对比度、同一种 `Timer.publish` 驱动**，"
                    + "只差『视图归产品还是归测试』的那一颗证人今天覆盖了 "
                    + "\(String(format: "%.3f", rateWitness.coverage)) ⇒ 这台机器带得动产品那一档节拍的常驻循环，"
                    + "是产品这一份没在跑：查 `SkeletonPreviewView` 那条 `Timer.publish`"
                    + "（`SkeletonMotion.tickInterval`）与 `MotionCatalog.duration(for: .skeletonSweep)` 的接线")
        case .notRunEnvironment:
            emit("MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate 产品 coverage=\(String(format: "%.3f", shape.coverage))、"
                + "等节拍证人 coverage=\(String(format: "%.3f", rateWitness.coverage))（30Hz / 抬升 0.12 / 同一种画法）、"
                + "粗节拍证人 coverage=\(String(format: "%.3f", coarseWitness.coverage)) ⇒ "
                + "这台机器今天带不动产品那一档节拍的常驻循环，"
                + "这一条不能推成『产品的扫光没跑』，也不能推成『它跑了』（本机 2× 那一遍 coverage 0.98 才是判它的那台机器）")
        case .notRunRulerBlind:
            // 不红，也不许悄悄当绿：这是一朵**有名字的**未覆盖（登记表 `loops` 那一节读它）。
            emit("MOTION_NOT_RUN=loop-coverage-contradicted-by-travel 产品 coverage="
                + "\(String(format: "%.3f", shape.coverage))（\(shape.changingPairs)/\(shape.pairs) 对在变）、"
                + "等节拍证人 coverage=\(String(format: "%.3f", rateWitness.coverage))、"
                + "粗节拍证人 coverage=\(String(format: "%.3f", coarseWitness.coverage))，"
                + "而**同一卷上位置那把尺量到亮带走过了整幅**（可用帧与行程在 MOTION_SHIMMER_BAND 那一行）⇒ "
                + "两把尺对『亮带在不在走』给出相反答案时，签字的是样本多的那一个："
                + "coverage 在这台机器上只有 1–2 个变化帧对撑着，而位置尺有 11–12 个可用帧。"
                + "这一格既不判产品红、也不判绿 —— 它记的是 coverage 这把尺的分辨率账（BACKLOG 119 / 110）")
        case .witnessDead:
            XCTFail("连**高对比、粗节拍**那颗证人整卷都没拍到任何变化（峰值 \(String(format: "%.4f", coarseWitness.peak))）⇒ "
                    + "给『环境看不见』签字的那个人今天没来上班。这条必须红：否则 .notRunEnvironment 那一支"
                    + "从此是一张空支票（R68 的 M366 同一族）")
        }
        // 减弱动态那一档：必须**真的停住**（这一臂反过来证明上面读到的变化确实是扫光，不是噪声）。
        // 这一条**不**随处置豁免：它要的是"静止"，而"这台机器看不见运动"永远不会伪造出运动来。
        XCTAssertLessThan(Self.peak(stopped), Self.minimumVisibleChange,
                          "减弱动态那一档还在变 ⇒ 常驻动画没被门住（HIG 与 WCAG 2.3.3 要的就是这一条）")
        // 峰值地板：coverage 只在"看得见东西在动"的前提下才有意义，所以它问的是
        // "**这台机器上**这一臂到底有没有东西在动"。R82 的 CI 让这一条红了一次：
        // runner 上产品峰值 0.000、等节拍证人 coverage 0.284、粗节拍证人 1.000 ⇒
        // 处置已经是"这台机器带不动那一档节拍的循环"，而这条地板不管处置，
        // 于是同一件事被报两次，其中一次还把环境说成产品。
        // ⇒ 绝对地板只在**环境已被证明有资格判这一臂**时说话（.ok / .productRed），
        //   其余两支把它换成一行有名字的读数，红由上面那个 switch 负责，不重复判。
        if disposition == .ok || disposition == .productRed {
            XCTAssertGreaterThan(Self.peak(running), Self.minimumVisibleChange,
                                 "该扫的那一档什么都没变 ⇒ 扫光没落地（先看上面那行的帧数与尺寸，0 帧和 0 变化是两种病）")
        } else {
            emit("MOTION_SHIMMER_PEAK_NOT_JUDGED 峰值=\(String(format: "%.4f", Self.peak(running)))"
                + " 地板=\(Self.minimumVisibleChange) 处置=\(disposition) ⇒ 这一臂今天不由绝对地板判："
                + "同一件事上面已经处置过一次（红或点名 not-run），再判一次就是把环境问题改写成产品问题")
        }
    }

    // MARK: - R84 / BACKLOG 117：亮带是整组一条，还是每根条各一条

    /// 骨架的亮带**是不是一条光穿过整组条带** —— 这一条判的是**位置**，不是运动。
    ///
    /// 为什么值得一条独立判据（R83 看图看出来的，`BACKLOG 117`）：原来每根条各自
    /// `RoundedRectangle().fill(渐变).frame(width: 条宽)`，而 `LinearGradient` 的 `UnitPoint`
    /// 按**被填充那个形状**的边界归一化 ⇒ 同一个相位在 176 / 361 / 269pt 三根条上是三个
    /// 绝对位置。画面上那是三条各扫各的亮带，不是一条光扫过一组 —— 而"一条光扫过一组"
    /// 才是这条扫光的全部表达力（整组一个方向、一个节奏，读起来是"这块内容在加载"）。
    /// R83 用 `.scratch/motion-audit-2/r83_band_fanout.py` 手量的：同一帧内三根条的亮斑
    /// **绝对**中心最大差 170pt、**归一化**中心最大只差 0.003。本轮把渐变抬到容器层，
    /// 并把那道手量换成会红的判据。
    ///
    /// 三个闸门，少一个这句话就站不住（顺序也是这个顺序）：
    /// ① **尺子自己的正对照**：两份合成卷子 —— 一份整组一条带、一份每根条各一条带 ——
    ///    这一格分不开的话，下面那句"产品是整组一条带"就是一张空支票（R68 的 M366 同一族）。
    /// ② **真片上的正对照**：可用帧里亮带必须真的走过一段行程（`sweepTravelFloorPoints`）。
    ///    没有这一条，"三根条的峰值都停在同一列"（静止画面、噪声、或者根本没拍到）也会读成
    ///    散布 0pt，而 0pt 恰好是"整组一条带"的读数 —— 内存里那句"有没有变化拦不住带在错地方"
    ///    的反面：位置一致也拦不住根本没在扫。
    /// ③ **谁能签"这台机器判不了位置"**：不签给 coverage 那个处置，签给**同一把尺**去读高对比那颗
    ///    证人（`bandAdjudication`）。理由写在调用点：R82 与 R83 的 CI 在**同一个产品代码**上
    ///    给过相反的两支（证人 coverage 0.284 ⇒ 点名环境，0.837 ⇒ 判产品红），
    ///    那一支自己不稳定，不能拿来当这一支的地板。
    func testSkeletonSweepIsOneBand() async throws {
        do { try skipUnlessEnabledAndCapable() } catch {
            emit("MOTION_SHIMMER_BAND_STATE 判定=skipped 原因=capability-gate")
            throw error
        }
        // ① 尺子自己的正对照（合成卷子，不依赖机器、不依赖产品）。
        let control = Self.bandRulerControl()
        emit("MOTION_SHIMMER_BAND_CONTROL 整组一条带那卷判定=\(control.oneBandVerdict.rawValue) "
            + "每根条各扫那卷判定=\(control.fanOutVerdict.rawValue) "
            + "（两份都是 8 灰阶抬升的亮斑，只有中心位置放法不同）")
        XCTAssertEqual(control.oneBandVerdict, BandReading.Verdict.oneBand,
                       "把『整组一条带』那份合成卷子读成了 \(control.oneBandVerdict.rawValue)"
                           + " ⇒ 这把尺看不见它本该看见的东西，下面那句产品判定不作数")
        XCTAssertEqual(control.fanOutVerdict, BandReading.Verdict.fanOut,
                       "把『每根条各扫各的』那份卷子读成了 \(control.fanOutVerdict.rawValue)"
                           + " ⇒ 这把尺分不开这两种画法，那它也就没资格说产品是哪一种")

        // ② 产品那卷：与运动判据**同一卷**（`shimmerFilm` 缓存），两句话必须互相印证。
        let film = Self.shimmerFilm()
        let scale = Self.bandScale(of: film.frames.first, viewWidthPoints: skeletonViewWidthPoints)
        let measured = Self.bandFrames(film.frames.map(Self.raster), viewWidthPoints: skeletonViewWidthPoints)
        let reading = Self.bandReading(frames: measured.accepted,
                                       widths: Self.barWidthPoints(viewWidthPoints: skeletonViewWidthPoints))
        emit("MOTION_SHIMMER_BAND 帧=\(film.frames.count) 比例=1pt≈\(String(format: "%.2f", scale))px "
            + "可用帧=\(reading.framesUsed) 丢掉=\(measured.rejected) "
            + "同帧绝对中心最大散布=\(String(format: "%.1f", reading.maxSpreadPoints))pt"
            + "（地板：≤\(Self.oneBandCeilingPoints) 判一条带、≥\(Self.fanOutFloorPoints) 判各扫各的） "
            + "归一化散布=\(String(format: "%.3f", reading.normalizedSpread)) "
            + "行程=\(String(format: "%.1f", reading.travelPoints))pt（正对照地板 \(Self.sweepTravelFloorPoints)） "
            + "判定=\(reading.verdict.rawValue) 理由=\(reading.reason)")
        emit("MOTION_SHIMMER_BAND_SAMPLE \(reading.sampleLine)")
        writeStrip("skeleton-band", Array(film.frames.prefix(24)))
        // ③ 位置这把尺的"这台机器有没有资格判"，**不能**由 coverage 那个处置签：
        //    R83 的 CI 刚证明那一支自己会翻面（同一个产品代码、同一类机器，R82 读 0.284 ⇒ 点名环境，
        //    R83 读 0.837 ⇒ 判产品红）。所以这里换一颗只问位置、不问节拍的证人：
        //    高对比那颗（抬 0.45）与产品**同一种画法、同一个几何**，它问的是最弱那一题 ——
        //    "这台机器在这张图上看不出一条亮带的位置吗"。连它都读不出可用帧，产品那 0.12 抬升
        //    的位置就无从判起；它读得出而产品读不出，红就落在产品。
        let witnessReading = Self.bandWitnessReading()
        emit("MOTION_SHIMMER_BAND_WITNESS 粗节拍那颗(抬 0.45、同一种画法、同一把尺) "
            + "可用帧=\(witnessReading.framesUsed) 绝对散布=\(String(format: "%.1f", witnessReading.maxSpreadPoints))pt "
            + "行程=\(String(format: "%.1f", witnessReading.travelPoints))pt 判定=\(witnessReading.verdict.rawValue) "
            + "理由=\(witnessReading.reason)")
        let loopDisposition = Self.shimmerDisposition()
        let bandDisposition = Self.bandAdjudication(product: reading.verdict,
                                                    witness: witnessReading.verdict,
                                                    loopCapable: loopDisposition == .ok)
        let bandReason = Self.bandStateReason(bandDisposition, loop: loopDisposition,
                                              witness: witnessReading.verdict)
        emit("MOTION_SHIMMER_BAND_STATE 判定=\(Self.bandStateLabel(bandDisposition)) 原因=\(bandReason)")
        switch bandDisposition {
        case .ok:
            break   // 产品判成整组一条带，而且这台机器有资格判这件事
        case .productRed:
            XCTFail("骨架的亮带今天不是『一条光穿过整组』（判定=\(reading.verdict.rawValue)："
                               + reading.reason + "）。R84 把渐变填在整组的形状上（`SkeletonBarsShape`）"
                               + "就是为了让三根条共用一个亮带中心；现在同一帧里三根条的亮斑绝对中心差 "
                               + String(format: "%.1f", reading.maxSpreadPoints) + "pt ⇒ 要么渐变又回到了单根条的"
                               + "单位空间（`unitPoints` 被用在条宽上），要么三根条不再是同一个形状里的三根。"
                               + "而同一台机器上那颗**只有对比度更高**的证人用同一把尺读得出亮带位置"
                               + "（" + witnessReading.verdict.rawValue + "），而 coverage 那一族的处置也是 .ok"
                               + "（这台机器判得动产品自己那一档节拍）⇒ 这条红不是环境问题")
        case .notRunEnvironment:
            emit("MOTION_SHIMMER_BAND_NOT_JUDGED 产品判定=\(reading.verdict.rawValue) "
                + "证人判定=\(witnessReading.verdict.rawValue) 证人可用帧=\(witnessReading.framesUsed) "
                + "循环处置=\(loopDisposition) ⇒ 今天不判位置：要么连高对比那颗证人都拍不出可用的亮带位置，"
                + "要么 coverage 那一族在这台机器上还没被证明判得动产品那一档节拍"
                + "（BACKLOG 119：那个处置自己会在两轮之间翻面 ⇒ 它只能收窄断言，不许放大指控）。"
                + "这一格既不能说亮带在整组里扫过去，也不能说它没有。（与峰值地板同落在 118 那个洞里）")
        }
    }

    // MARK: 位置判据的那把尺（纯函数 + 像素测量，都在上面那条判据里用）

    /// 整组一条带的判定上限：同一帧里三根条的亮斑绝对中心差 ≤ 这个数 ⇒ 判"一条带"。
    /// 6pt = 两根条的峰值落在同一个亮带台阶上时允许的最大量化误差（1px @2× = 0.5pt，
    /// 加上渐变本身在半格宽内是平的）。它必须**明显小于** `fanOutFloorPoints`：
    /// 两个地板能互相取消的话，这把尺就什么都能判（内存里那条"阈值要成对"）。
    static let oneBandCeilingPoints: Double = 6
    /// 每根条各扫各的判定下限：≥ 40pt ⇒ 判"各扫各的"。
    /// 实测那一卷的数差是 170pt（R83），而三根条两两之间的条宽差最小那对是 88pt
    /// ⇒ 40pt 既不贴天花板也不贴地板：落在 6…40 之间就是**分不开**，判据老实说分不开。
    static let fanOutFloorPoints: Double = 40
    /// 正对照：可用帧里亮带至少要走这么远。0 行程的"散布 0pt"是静止画面，不是对称。
    static let sweepTravelFloorPoints: Double = 20
    /// 少于这么多可用帧就不判：一帧只能说明"这一瞬间三根条亮在同一条竖线上"，
    /// 而这句话要在好几帧上都成立才叫"一条带扫过去"。
    static let minimumBandFrames: Int = 3
    /// 亮斑相对本条自身中位数的最小偏离（灰阶，两根轴里更强的那根）。
    /// 实测：亮带扫到那根条时峰谷差 23–26，没扫到时 ≈2 ⇒ 门槛 4 不在刀尖上。
    /// 这一格的意义是把"亮带不在这根条里"的那一帧**丢掉并数出来** —— 那种帧的剖面
    /// 是一条单调斜坡，"最偏离中位数的那一列"会退化成条端（R83 手量时踩过的同一个坑）。
    /// **它今天没有独立的牙，这一句是读数而不是礼貌**：变异 M454（只把这格调到 0）本地全绿，
    /// 而 M454b（这一格与下面那格**一起**调到 0）红 ⇒ 今天真正拦住假峰的是条端内边距那一格
    /// （M452 单独拆它就红），这一格是纵深防御。至于"为什么单拆没牙"，本轮**没有量**：
    /// 说得通的机制是无噪声渲染下"条内没有亮带"的剖面是常数、argmax 落在第 0 列，
    /// 于是先被内边距拦住 —— 但那只是解释，不是一条读数，所以记在这里而不是写成结论。
    /// 留着它的条件也写在这里：哪天渲染通道带上噪声（换捕获后端、加抖动），
    /// 常数剖面不再成立，这一格可能变成唯一还拦得住假中点的那一格。
    static let bandAmplitudeFloor: Double = 4
    /// 峰值离本条两端必须至少这么远（点），否则亮带被这条切掉了，读到的不是中心。
    ///
    /// **10pt 是量出来的，不是猜的**：第一版写 4pt，本机那一卷 45 帧里 15 帧可用，
    /// 而最后一帧读出 `[33.0 → 171.5, 191.0, 191.0]`：短条（176pt）在亮带中心已经走出它右端时，
    /// 条内剖面变成单调上升，argmax 贴在右端**里面一点点** —— 圆角让最外那一两列变暗，
    /// 于是 4pt 的门槛恰好拦不住它（差 0.9pt 漏过去），整帧被这一个假数拉到 19.5pt ⇒ "分不开"。
    /// 门槛要大于"圆角 + 一个台阶"能伪装出来的那段距离：亮带半宽是 63pt ⇒ 10pt 既拦得住这种
    /// 贴边假峰，也还没吃掉真正在条内的那些中心（可用帧 15 → 仍然够）。
    static let bandInteriorMarginPoints: Double = 10

    /// 一帧的测量结果 + 判定。纯函数：`frames` 是**已通过前提**的那些帧，
    /// 每帧三根条各自的亮斑绝对中心（点）。
    struct BandReading: Equatable {
        enum Verdict: String {
            case oneBand = "整组一条带"
            case fanOut = "每根条各扫各的"
            case notJudged = "分不开"
            case noFrames = "没有可用帧"
        }
        let verdict: Verdict
        let reason: String
        let framesUsed: Int
        /// 同一帧内三根条绝对中心之差的最大值（点）。取**最大**而不是平均：
        /// 有一帧分家就不是整组一条带。
        let maxSpreadPoints: Double
        /// 同一帧内归一化中心（÷各自条宽）之差的最大值。这一格今天只用来打读数：
        /// 修之前它 ≈0、绝对散布 170pt，修之后应该反过来 —— 两个数一起才说清是哪一种画法。
        let normalizedSpread: Double
        /// 亮带在可用帧里走过的距离（点）：正对照。
        let travelPoints: Double
        let sampleLine: String

        /// 真值表用的构造器（判定由 `bandReading(frames:widths:)` 算，这里只填数）。
        init(verdict: Verdict, reason: String, framesUsed: Int = 0, maxSpreadPoints: Double = 0,
             normalizedSpread: Double = 0, travelPoints: Double = 0, sampleLine: String = "-") {
            self.verdict = verdict
            self.reason = reason
            self.framesUsed = framesUsed
            self.maxSpreadPoints = maxSpreadPoints
            self.normalizedSpread = normalizedSpread
            self.travelPoints = travelPoints
            self.sampleLine = sampleLine
        }
    }

    /// 判定本身。地板全部是参数（默认取上面那些常量），为的是真值表能写出"落在两个地板之间"那一格，
    /// 而不是只能构造恰好越线的输入。
    static func bandReading(frames: [[Double]], widths: [Double],
                            oneBandCeiling: Double = oneBandCeilingPoints,
                            fanOutFloor: Double = fanOutFloorPoints,
                            travelFloor: Double = sweepTravelFloorPoints,
                            minimumFrames: Int = minimumBandFrames) -> BandReading {
        func format(_ value: Double) -> String { String(format: "%.1f", value) }
        guard !frames.isEmpty else {
            return BandReading(verdict: .noFrames,
                               reason: "没有任何一帧同时满足『三根条都拍到亮斑』与『峰值不在条端』"
                                    + " ⇒ 要么这台机器没扫过光，要么条不在 `SkeletonMotion.barRect` 说的那三行上")
        }
        let spreads = frames.map { ($0.max() ?? 0) - ($0.min() ?? 0) }
        let maxSpread = spreads.max() ?? 0
        let norms = frames.map { frame in
            let scaled = zip(frame, widths).map { $0.0 / max($0.1, 0.0001) }
            return (scaled.max() ?? 0) - (scaled.min() ?? 0)
        }
        let maxNorm = norms.max() ?? 0
        // 行程：逐根条看它自己跨帧走过多远，取最强的那根。
        var travel = 0.0
        if frames.count > 1 {
            for column in 0..<(frames.map(\.count).min() ?? 0) {
                let values = frames.compactMap { $0.count > column ? $0[column] : nil }
                travel = max(travel, (values.max() ?? 0) - (values.min() ?? 0))
            }
        }
        let sample = "可用帧首=[\(frames[0].map(format).joined(separator: ", "))] "
            + "末=[\(frames[frames.count - 1].map(format).joined(separator: ", "))]"
        let counted = BandReading(verdict: .notJudged, reason: "", framesUsed: frames.count,
                                  maxSpreadPoints: maxSpread, normalizedSpread: maxNorm,
                                  travelPoints: travel, sampleLine: sample)
        if frames.count < minimumFrames {
            return BandReading(verdict: .notJudged,
                               reason: "只有 \(frames.count) 帧可用，地板是 \(minimumFrames) 帧："
                                    + "一帧上的『同一条竖线』说明不了『一路扫过去』",
                               framesUsed: counted.framesUsed, maxSpreadPoints: maxSpread,
                               normalizedSpread: maxNorm, travelPoints: travel, sampleLine: sample)
        }
        if travel < travelFloor {
            return BandReading(verdict: .notJudged,
                               reason: "正对照失败：亮带在这 \(frames.count) 帧里只走了 \(format(travel))pt，"
                                    + "地板 \(format(travelFloor))pt ⇒ 散布再小也不是『一条带扫过去』，那是没在动",
                               framesUsed: counted.framesUsed, maxSpreadPoints: maxSpread,
                               normalizedSpread: maxNorm, travelPoints: travel, sampleLine: sample)
        }
        if maxSpread <= oneBandCeiling {
            return BandReading(verdict: .oneBand,
                               reason: "每一帧三根条的亮斑都在同一条竖线上（最大差 \(format(maxSpread))pt ≤ "
                                    + "\(format(oneBandCeiling))），且它一路走了 \(format(travel))pt",
                               framesUsed: counted.framesUsed, maxSpreadPoints: maxSpread,
                               normalizedSpread: maxNorm, travelPoints: travel, sampleLine: sample)
        }
        if maxSpread >= fanOutFloor {
            return BandReading(verdict: .fanOut,
                               reason: "同一帧里三根条的亮斑绝对中心差到 \(format(maxSpread))pt ≥ "
                                    + "\(format(fanOutFloor)) ⇒ 那是三条各自单位空间里的亮带",
                               framesUsed: counted.framesUsed, maxSpreadPoints: maxSpread,
                               normalizedSpread: maxNorm, travelPoints: travel, sampleLine: sample)
        }
        return BandReading(verdict: .notJudged,
                           reason: "绝对散布 \(format(maxSpread))pt 落在两个地板之间（≤\(format(oneBandCeiling)) 才判一条带、"
                                + "≥\(format(fanOutFloor)) 才判各扫各的）⇒ 这把尺今天分不开这两种画法",
                           framesUsed: counted.framesUsed, maxSpreadPoints: maxSpread,
                           normalizedSpread: maxNorm, travelPoints: travel, sampleLine: sample)
    }

    /// 三根条各自的宽度（点）—— 归一化那一格用的分母。
    static func barWidthPoints(viewWidthPoints: Double) -> [Double] {
        SkeletonMotion.barFractions.map { Double($0) * viewWidthPoints }
    }

    /// 点 → 像素的比例，从帧本身读（不假设 2×：外接屏与 runner 都是 1×）。
    static func bandScale(of frame: CGImage?, viewWidthPoints: Double) -> Double {
        guard let frame, viewWidthPoints > 0 else { return 0 }
        return Double(frame.width) / viewWidthPoints
    }

    /// 一卷位图 → 通过前提的那些帧（每帧三根条的亮斑绝对中心）+ 被丢掉的帧数。
    /// 丢掉必须**数出来**：一帧都不剩和全是噪声是两种病，而 `bandReading` 只看前者。
    private static func bandFrames(_ bitmaps: [Bitmap], viewWidthPoints: Double) -> (accepted: [[Double]], rejected: Int) {
        var accepted: [[Double]] = []
        var rejected = 0
        for bitmap in bitmaps {
            if let peaks = bandFramePeaks(bitmap, viewWidthPoints: viewWidthPoints) {
                accepted.append(peaks)
            } else {
                rejected += 1
            }
        }
        return (accepted, rejected)
    }

    /// 一帧里三根条各自的亮斑中心。任何一根不合格就整帧作废（宁缺毋滥：
    /// 少一根条的"散布"量的就不是那道扫光了）。
    private static func bandFramePeaks(_ bitmap: Bitmap, viewWidthPoints: Double) -> [Double]? {
        let peaks = barPeaks(bitmap, viewWidthPoints: viewWidthPoints)
        guard peaks.count == SkeletonMotion.barFractions.count else { return nil }
        guard peaks.allSatisfy({ $0.interior && $0.deviation >= bandAmplitudeFloor }) else { return nil }
        return peaks.map(\.peakPoints)
    }

    struct BarPeak: Equatable {
        let peakPoints: Double
        let deviation: Double
        let interior: Bool
    }

    /// 三根条各自的亮斑（`SkeletonMotion.barRect` 说的那三行）。
    private static func barPeaks(_ bitmap: Bitmap, viewWidthPoints: Double) -> [BarPeak] {
        let scale = Double(bitmap.width) / viewWidthPoints
        guard scale >= 1, bitmap.height > 0 else { return [] }
        let group = CGRect(x: 0, y: 0, width: viewWidthPoints, height: groupHeightPoints)
        return SkeletonMotion.barFractions.enumerated().compactMap { index, fraction in
            guard let peak = barPeak(bitmap,
                                     rect: SkeletonMotion.barRect(index: index, fraction: fraction, in: group),
                                     scale: scale) else { return nil }
            return peak
        }
    }

    /// 一根条：沿 x 求列均值，取**离本条自身中位数最远**的那一列当亮斑中心。
    ///
    /// 为什么是中位数而不是最大值：`Color.primary` 在浅色外观下是**黑**的，条带比窗口背景暗，
    /// 亮带则是"更暗"；在深色外观下整个反过来。用"离本条自身的多数派偏离最远"就不必赌方向，
    /// 而这道题要问的本来就不是"哪边亮"，是"亮斑在不在同一列"。
    /// 为什么两根轴都要算：R77 量过"暗墨变透明这一族在预乘 RGB 上就是 0→0"，
    /// 一把只读 RGB 的尺在浅色外观下会看不见这里的亮带 —— 那会把"各扫各的"读成"没有可用帧"，
    /// 也就是把一条会红的判据悄悄变成一条不判的判据。
    private static func barPeak(_ bitmap: Bitmap, rect: CGRect, scale: Double) -> BarPeak? {
        // `rect` 是**点**（`SkeletonMotion.barRect` 在视图坐标系里算的），位图下标是**像素**
        // ⇒ 这里必须乘 `scale`。第一版漏乘了：条被当成只有实际一半宽去采样，
        // 于是整组一条带那种卷子的峰值永远贴在采样窗的右端 ⇒ `interior` 全部失败 ⇒
        // 45 帧全被丢掉、两条合成对照也一起读成"分不开"（三条红同一个根因，本轮实测）。
        let x0 = Int((rect.minX * scale).rounded()), x1 = Int((rect.maxX * scale).rounded())
        let y0 = Int((rect.minY * scale).rounded()), y1 = Int((rect.maxY * scale).rounded())
        guard x1 > x0, y1 > y0, x1 <= bitmap.width, y1 <= bitmap.height else { return nil }
        var rgb: [Double] = []
        var alpha: [Double] = []
        for x in x0..<x1 {
            var sums = (r: 0.0, g: 0.0, b: 0.0, a: 0.0)
            var count = 0
            var y = y0
            while y < y1 {
                let p = (y * bitmap.width + x) * 4
                guard p + 3 < bitmap.pixels.count else { break }
                sums.r += Double(bitmap.pixels[p]); sums.g += Double(bitmap.pixels[p + 1])
                sums.b += Double(bitmap.pixels[p + 2]); sums.a += Double(bitmap.pixels[p + 3])
                count += 1
                y += 1
            }
            guard count > 0 else { return nil }
            rgb.append((sums.r + sums.g + sums.b) / (3.0 * Double(count)))
            alpha.append(sums.a / Double(count))
        }
        guard let peak = outlierPeak(rgb: rgb, alpha: alpha) else { return nil }
        let margin = bandInteriorMarginPoints * scale
        return BarPeak(peakPoints: rect.minX + Double(peak.index) / scale,
                       deviation: peak.deviation,
                       interior: Double(peak.index) >= margin
                           && Double(peak.index) <= Double(rgb.count - 1) - margin)
    }

    /// 两条轴各找一次"离中位数最远"，返回偏离更强的那根。
    /// 幅度用灰阶、两轴共用同一个地板（`bandAmplitudeFloor`）—— 共用门槛才可比（R77 同一句话）。
    private static func outlierPeak(rgb: [Double], alpha: [Double]) -> (index: Int, deviation: Double)? {
        guard rgb.count == alpha.count, rgb.count >= 8 else { return nil }
        var best: (index: Int, deviation: Double)?
        for values in [rgb, alpha] {
            let sorted = values.sorted()
            let median = sorted[sorted.count / 2]
            guard let winner = values.enumerated().max(by: {
                abs($0.element - median) < abs($1.element - median)
            }) else { continue }
            let deviation = abs(winner.element - median)
            if best == nil || deviation > best!.deviation {
                best = (winner.offset, deviation)
            }
        }
        return best
    }

    /// 位置这把尺的处置：谁来签"这台机器今天判不了位置"。
    enum BandAdjudication: Equatable {
        /// 证人读得出亮带位置，产品也判成了整组一条带 ⇒ 判绿。
        case ok
        /// 证人读得出，而产品读不出/判成分家 ⇒ **产品红**（两颗之间只剩对比度这一个差别）。
        case productRed
        /// 连高对比那颗证人都拍不出可用的亮带位置 ⇒ 这台机器判不了这件事 ⇒ 点名，不判产品。
        case notRunEnvironment
    }

    /// 证人"有资格签"= 它自己读出了一个**可判决**的画法（两种之一），而不是 0 可用帧、
    /// 正对照失败或落在两个地板之间。把"分不开"也算成有资格的话，产品那一句"红"就又是空支票。
    static func bandWitnessIsAdmissible(_ verdict: BandReading.Verdict) -> Bool {
        verdict == .oneBand || verdict == .fanOut
    }

    /// `loopCapable` = coverage 那一族今天在这台机器上判得动产品自己那一档节拍（处置是 `.ok`）。
    ///
    /// 为什么这一格只能**收窄**断言、不能放大指控（R84 / BACKLOG 119 的实测教训）：
    /// R82 与 R83 的 CI 在同一份产品代码上给过相反的两支（等节拍证人 coverage 0.284 ⇒ 点名环境，
    /// 0.837 ⇒ 判产品红）。一个自己会在两轮之间翻脸的读数，如果拿来**定罪**产品，
    /// 下一轮就会红着说一件它上一轮否认过的事；而拿来**免罪**（不说）则任何一轮都安全。
    /// ⇒ 所以 `loopCapable == false` 时这一族一律不判，哪怕证人这边读得出。
    /// 本机那一遍的处置是 `.ok`（产品 coverage 0.976-1.000），所以这一格在本机不改变任何结论，
    /// 它拦的是 runner 上那朵假红。
    static func bandAdjudication(product: BandReading.Verdict,
                                 witness: BandReading.Verdict,
                                 loopCapable: Bool = true) -> BandAdjudication {
        guard loopCapable else { return .notRunEnvironment }
        guard bandWitnessIsAdmissible(witness) else { return .notRunEnvironment }
        return product == .oneBand ? .ok : .productRed
    }

    /// 粗节拍那颗证人用**同一把尺**读出来的位置判定（每进程一次，一次 2.5 秒）。
    /// 为什么不复用 `loopWitness(.gradient)` 那个 LoopShape：那颗尺读的是"有没有在变"，
    /// 而这一格要的是"看不看得见一条亮带在哪儿"。两句话在 runner 上会分家
    /// （R82 与 R83 的 coverage 处置正好翻过一次面），所以签字的人必须被问对那一题。
    static func bandWitnessReading() -> BandReading {
        if let cached = bandWitnessCache { return cached }
        let film = StateTickProbe().record(motionClass: .gradient, seconds: loopFilmSeconds)
        let reading = bandReading(frames: bandFrames(film.frames.map(raster),
                                                     viewWidthPoints: skeletonViewWidthPoints).accepted,
                                  widths: barWidthPoints(viewWidthPoints: skeletonViewWidthPoints))
        bandWitnessCache = reading
        return reading
    }

    /// 尺子自己的正对照：两份合成卷子，只有亮斑中心的**放法**不同。
    /// 整组一条带那份 ⇒ 必须判 `oneBand`；每根条各扫各那份 ⇒ 必须判 `fanOut`。
    /// 两份都放同一档抬升（8 灰阶）与同一条行程，所以"分不开"不可能是对比度造成的。
    static func bandRulerControl() -> (oneBandVerdict: BandReading.Verdict,
                                       fanOutVerdict: BandReading.Verdict) {
        let scale = 2.0
        let widths = Self.barWidthPoints(viewWidthPoints: skeletonViewWidthPoints)
        // 亮带中心从 20pt 走到 150pt：三根条都装得下这段（最短那根 176pt），
        // 而"各扫各的"那卷在同样三个相位上的绝对中心差到 90pt 以上。
        let centers: [Double] = [20, 60, 100, 150]
        let oneBand = Self.bandFrames(centers.map { center in
            Self.syntheticSkeletonFrame(peakPoints: [center, center, center], scale: scale)
        }, viewWidthPoints: skeletonViewWidthPoints)
        let fanOut = Self.bandFrames(centers.map { center in
            // 同一个相位在每根条自己的单位空间里 ⇒ 绝对中心 = 比例 × 条宽。
            let fraction = (center - 20) / 130.0 * 0.8 + 0.1
            return Self.syntheticSkeletonFrame(peakPoints: widths.map { $0 * fraction }, scale: scale)
        }, viewWidthPoints: skeletonViewWidthPoints)
        return (Self.bandReading(frames: oneBand.accepted, widths: widths).verdict,
                Self.bandReading(frames: fanOut.accepted, widths: widths).verdict)
    }

    /// 合成一张骨架位图：三根条 + 每根条里一个可指定绝对位置的亮斑（白墨、按 alpha 计）。
    /// 只用来当尺子的正对照，不进任何产品判定。
    private static func syntheticSkeletonFrame(peakPoints: [Double], scale: Double,
                                       viewWidthPoints: Double = skeletonViewWidthPoints) -> Bitmap {
        let width = max(1, Int(viewWidthPoints * scale))
        let height = max(1, Int(groupHeightPoints * scale))
        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        let bandHalf = SkeletonMotion.bandSize * viewWidthPoints / 2
        let lift = SkeletonMotion.highlightOpacity - SkeletonMotion.baseOpacity
        for (index, fraction) in SkeletonMotion.barFractions.enumerated() {
            let rect = SkeletonMotion.barRect(index: index, fraction: fraction,
                                              in: CGRect(x: 0, y: 0, width: viewWidthPoints,
                                                         height: groupHeightPoints))
            let peak = index < peakPoints.count ? peakPoints[index] : viewWidthPoints / 2
            let x0 = Int((rect.minX * scale).rounded()), x1 = Int((rect.maxX * scale).rounded())
            let y0 = Int((rect.minY * scale).rounded()), y1 = Int((rect.maxY * scale).rounded())
            guard x1 > x0, y1 > y0, x1 <= width, y1 <= height else { continue }
            for y in y0..<y1 {
                for x in x0..<x1 {
                    let points = Double(x) / scale
                    // 三角亮斑：中心在最亮，半个带宽处回到底色（与产品那条三段渐变同形）。
                    let falloff = max(0, 1 - abs(points - peak) / max(bandHalf, 0.0001))
                    let ink = min(0.98, SkeletonMotion.baseOpacity + lift * falloff)
                    let value = UInt8((ink * 255).rounded())
                    let p = (y * width + x) * 4
                    pixels[p] = value; pixels[p + 1] = value; pixels[p + 2] = value; pixels[p + 3] = value
                }
            }
        }
        return Bitmap(pixels: pixels, width: width, height: height)
    }

    /// 三根条占的总高度（点）：判据按它决定合成图要多高，也按它检查真片容不容得下整组。
    static var groupHeightPoints: Double {
        Double(SkeletonMotion.barFractions.count) * Double(SkeletonMotion.barHeight)
            + Double(SkeletonMotion.barFractions.count - 1) * Double(SkeletonMotion.barSpacing)
    }

    /// 产品那一卷只抓一次（R84）：运动判据与位置判据必须读同一卷。
    fileprivate static func shimmerFilm() -> GrabbedFilm {
        if let cached = shimmerFilmCache { return cached }
        let film = SkeletonProbe().record(reduceMotion: false)
        shimmerFilmCache = film
        return film
    }

    /// 那一卷的处置（产品在跑 / 产品红 / 环境带不动 / 证人坏了）。
    /// 两条判据共用一个处置，是因为它们共用同一个前提：**这台机器今天看得见这一臂在动**。
    /// 写成一颗函数而不是各自算一遍，是为了不让"coverage 那条"与"位置那条"算出两个答案
    /// （R58 那一课：同一件事两份实现迟早分家）。
    /// 产品那一卷的**行程证据**（R87）：位置尺在同一卷上有 11–12 个可用帧，
    /// 而 coverage 只有 1–2 个变化帧对 —— 两个量对同一件事给出相反答案时，
    /// 签字的必须是样本多的那一个（`loopAdjudication` 里那一格）。
    /// 这里重算一遍位置尺是**有意的**：`shimmerFilm()` 是缓存的同一卷，
    /// 而位置判据那条测试里算出的数与这里必须一模一样（两句话读同一卷，R84 立的规矩）。
    static func shimmerTravel() -> TravelEvidence {
        let film = shimmerFilm()
        let measured = bandFrames(film.frames.map(Self.raster), viewWidthPoints: skeletonViewWidthPoints)
        return travelEvidence(bandReading(frames: measured.accepted,
                                          widths: barWidthPoints(viewWidthPoints: skeletonViewWidthPoints)))
    }

    static func shimmerDisposition() -> LoopAdjudication {
        let film = shimmerFilm()
        return loopAdjudication(product: loopShape(fractions: deltas(film.frames),
                                                   stamps: film.stamps).verdict,
                                rateWitness: loopWitness(.gradientAtProductRate).verdict,
                                coarseWitness: loopWitness(.gradient).verdict,
                                travel: shimmerTravel())
    }

    /// 状态行的两种取值。**名字要稳定**：`motion_floor_expectations.json` 的 `loops` 那一节
    /// 按这些串登记"允许哪几种判不到"，改了名字就是换了一种坏法（`BAD_REASON` 那一格会红）。
    static func loopStateLabel(_ disposition: LoopAdjudication) -> String {
        switch disposition {
        case .ok: return "ok"
        case .productRed: return "productRed"
        case .notRunEnvironment, .notRunRulerBlind: return "notRunEnvironment"
        case .witnessDead: return "witnessDead"
        }
    }

    static func bandStateLabel(_ disposition: BandAdjudication) -> String {
        switch disposition {
        case .ok: return "ok"
        case .productRed: return "productRed"
        case .notRunEnvironment: return "notRunEnvironment"
        }
    }

    /// 循环那一族的点名理由。两支 not-run 各有各的名字：把"证人坏了"与"环境带不动"并成
    /// 一个名字，等于让最严重的那一种坏法（没人签字）借用较轻那一支的免检牌。
    static func loopStateReason(_ disposition: LoopAdjudication) -> String {
        switch disposition {
        case .ok, .productRed: return "-"
        case .notRunEnvironment: return "loop-clock-not-sustainable-at-product-rate"
        // R87：这一支的理由**不许**借用上面那个名字。"机器带不动那一档节拍"与
        // "coverage 这把尺在这台机器上吃采样网格、而位置尺说亮带在走"是两种坏法；
        // 并成一个名字，登记表就分不清哪一格该被修（`BAD_REASON` 那一格会红，是刻意的）。
        case .notRunRulerBlind: return "loop-coverage-contradicted-by-travel"
        case .witnessDead: return "loop-witness-dead"
        }
    }

    /// 位置那一族的点名理由：同样是 not-run，但**是谁不让判**要分开写 ——
    /// `loop-not-capable` 说的是"循环那一族今天判不动，所以这一族闭嘴"（U-172 那条方向性约束），
    /// `band-witness-reads-nothing` 说的是"连高对比那颗证人都读不出亮带在哪儿"。
    static func bandStateReason(_ disposition: BandAdjudication, loop: LoopAdjudication,
                                witness: BandReading.Verdict) -> String {
        switch disposition {
        case .ok, .productRed: return "-"
        case .notRunEnvironment:
            return loop != .ok ? "loop-not-capable" : "band-witness-reads-nothing(\(witness.rawValue))"
        }
    }

    /// 两颗证人的卷子与产品那卷**同一个时长**（`loopFilmSeconds`，文件里那个全局常量）：
    private static func loopWitness(_ klass: MotionClass) -> LoopShape {
        if let cached = loopWitnessCache[klass] { return cached }
        let film = StateTickProbe().record(motionClass: klass, seconds: loopFilmSeconds)
        let shape = loopShape(fractions: deltas(film.frames), stamps: film.stamps)
        loopWitnessCache[klass] = shape
        return shape
    }

    static func loopLabel(_ verdict: LoopVerdict) -> String {
        switch verdict {
        case .notMoving: return "没拍到变化"
        case .looping: return "一直在动"
        case .oneShot: return "只动了一下"
        }
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
        case gradient    // 只动 `LinearGradient` 的端点：`GradientTickView`（20Hz、高对比那一档）
        /// 与骨架扫光**同一档节拍、同一组对比度**的那一颗（R82 / BACKLOG 113）。
        /// 它存在的唯一理由：证人必须与它作证的判据问同一句话（R68），
        /// 而那句里有"多少赫兹"这一项。
        case gradientAtProductRate

        /// 读数与 `MOTION_NOT_RUN=` 的名字都从这里取，别再手写三元表达式
        /// （加一个 case 而忘了改三元，编译器不会响，名字会串到别的臂上）。
        var marker: String {
            switch self {
            case .layout: return "layout"
            case .gradient: return "gradient"
            case .gradientAtProductRate: return "gradient-at-product-rate"
            }
        }
    }

    private func requireObservableMotion(_ klass: MotionClass) async throws {
        let marker = klass.marker
        if let cached = Self.observableCache[klass] {
            try XCTSkipIf(!cached, "MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
            return
        }
        let film = StateTickProbe().record(motionClass: klass)
        let control = Self.deltas(film.frames)
        let observable = Self.peak(control) > Self.minimumVisibleChange
        Self.observableCache[klass] = observable
        if !observable {
            emit("MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion 对照臂峰值=\(String(format: "%.4f", Self.peak(control))) 帧数=\(film.frames.count)")
        }
        try XCTSkipIf(!observable, "MOTION_NOT_RUN=runner-cannot-observe-\(marker)-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品")
    }

    /// 对照臂本身：**已知该动的东西必须动**，而且**两类各问一次**。
    /// 它是 `requireObservableMotion(_:)` 的判据来源，所以它自己只在"连布局位移都看不见"时
    /// 报 skip（那是环境），而不是红；渐变那一臂只报数 —— 它看不见是**事实**，不是失败。
    func testTheRulerSeesAStateDrivenSwiftUIUpdate() async throws {
        try skipUnlessEnabledAndCapable()
        let film = StateTickProbe().record(motionClass: .layout)
        let fractions = Self.deltas(film.frames)
        emit("MOTION_CONTROL 计数方块 帧数=\(film.frames.count) 峰值=\(String(format: "%.3f", Self.peak(fractions))) 变化帧对=\(Self.transitionFrameCount(fractions))")
        let gradient = StateTickProbe().record(motionClass: .gradient)
        let gradientFractions = Self.deltas(gradient.frames)
        emit("MOTION_CONTROL 渐变端点 帧数=\(gradient.frames.count) 峰值=\(String(format: "%.3f", Self.peak(gradientFractions))) 变化帧对=\(Self.transitionFrameCount(gradientFractions))")
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
        /// 这一卷**钉死**在哪一档外观里拍（R324）。`nil` = 不钉，跟着系统的"自动"走。
        ///
        /// 为什么要有这一层，而且它不是风格偏好：以前所有胶片场景都不钉，于是同一份判据
        /// 在本机"自动"色档下**白天与夜里量的不是同一张画面**。R324 现读同一卷 `filter-pill-slide`：
        /// 暗档 页底 30 / 轨道 52 / 药丸 36（两档相差 16–22 级），
        /// 亮档 页底 230 / 轨道 230 / 药丸 233（只差 **3** 级，低于这把尺的 `delta=8`）
        /// ⇒ 亮档里那条"会走的洞"一个候选行都读不出来（`候选行=0`），
        /// 而这不是产品事实，是尺在同一台机器上换了对象。
        /// 判据用的时间戳、帧数、峰值全都与色档无关，唯独**逐行像素尺**与材质档强相关 ——
        /// 所以钉色档的不是审美，是"这一把尺今天量的是哪张图"。
        let appearance: NSAppearance.Name?

        init(name: String, size: NSSize,
             prepare: (@MainActor (HistoryStore) -> Void)? = nil,
             declaredDurationMilliseconds: Double = 0,
             appearance: NSAppearance.Name? = nil,
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
            self.appearance = appearance
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
                     // 侧栏的空态 ↔ 列表那一层现在跟**药丸**同一个动画（R348 起：`FilterPillMotion.slideAnimation`
                     // ⇒ `MotionCatalog.duration(for: .slider)`）。这里以前声明的是 `.contentFade`（160ms）——
                     // 产品早就改成 0.20 了，胶片却还在按 160 摆帧，"改了胶片不动"就是这么来的（BACKLOG 425）。
                     // 声明与接线的一致性由 `FilterPillMotionTests.testEmptyStateFadeSharesThePillRhythm` 钉住。
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .slider) * 1000) { store in
                store.perform(.clear)
            }
        }

        static func searchReflow() -> Scenario {
            Scenario(name: "search-reflow", size: NSSize(width: 380, height: 520)) { store in
                store.perform(.updateSearch("记录 5"))
            }
        }

        /// R322 / 动效主线：侧栏顶部那颗「全部 / 收藏」的**横移**，第一次被放进真窗口逐帧取证。
        ///
        /// 为什么是这一个位点：它是全仓**唯一一条"位移"档**（`.slider` → `Slide.leading` → 弹簧）
        /// 的现场，而账上关于它的证据只有两态 —— `segmented-filter-idle` 那张帧 +
        /// `FILTER_PILL_BAND`（R189 把 `offset` 换成 `.position` 之后，"药丸在第几段"能被像素判）。
        /// **两端都对，不等于中间那段在演**：它完全可以瞬移，而两态尺一声不响。
        /// 这一族仓库里有名字：R11「源码已接、产物未量」、R16「只有一臂在演的过渡等于没有」。
        ///
        /// 为什么这一格**有资格**期待被看见（与热图那条纯 opacity 的淡入相反）：
        /// `cacheDisplay` 抓的是模型树，而这条动效变的是**位置** ——
        /// R288 那格写的正是"环境键的变化过程不进胶片，值变化进"，选中态同一驱动 16 帧渐变当反证。
        /// 也就是说"位移该看得见"是**可被推翻的预测**，不是免责：推翻它就把这条改成具名出口。
        ///
        /// 根视图用**产品那个** `SegmentedFilterPicker`，绑定走产品自己那条动作
        /// （`HistorySidebarView.swift:19-24` 同形：`get: store.filter` / `set: perform(.updateFilter)`）——
        /// 自带一份"长得像"的宿主视图就是在测替身（第二轮 N-1 那一族）。
        /// 根视图用**产品自己的** `HistorySidebarView`（`@ObservedObject var historyStore` 那一层就在它身上）：
        /// 第一版这里放的是裸的 `SegmentedFilterPicker(selection: Binding(get: store.filter, …))`，
        /// 结果两臂峰值都是 **0.000** —— 没有任何一层观察 store，SwiftUI 整棵树不重算，
        /// 胶囊当然不动。那是**探针坏了**，不是产品没动（R161 那一课：绕开被测系统自己的驱动路径，
        /// 会把它伪装成产品缺陷）。绑定链本身与 `HistorySidebarView.swift:19-24` 同形
        /// （`get: historyStore.filter` / `set: perform(.updateFilter)`），本轮没有替它做任何一层。
        ///
        /// 尺寸 300×520 与 `sidebar-history-300x520-*` 夹具同档（`sidebarFrame` 的默认宽）。
        static func filterPillSlide() -> Scenario {
            Scenario(name: "filter-pill-slide", size: NSSize(width: 300, height: 520),
                     prepare: { store in store.perform(.updateFilter(.all)) },
                     declaredDurationMilliseconds: MotionCatalog.duration(for: .slider) * 1000,
                     // R324：这两条判据（斜坡尺 / 过程证人）都是**逐行像素尺**，而亮档里
                     // 轨道与药丸只差 3 级（暗档 16–22 级）⇒ 不钉色档就等于把尺的对象交给时钟。
                     // 钉的是"尺有对象的那一档"，不是"好看的那一档"；理由写在 `Scenario` 的
                     // `appearance` 字段上面（页底/轨道/药丸三档的现读数以那个字段为准）。
                     appearance: .darkAqua,
                     root: { store in
                         AnyView(
                             HistorySidebarView(historyStore: store)
                                 .frame(width: 300, height: 520, alignment: .top)
                                 .background(Color(nsColor: .windowBackgroundColor))
                         )
                     }) { store in
                store.perform(.updateFilter(.favorites))
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

        /// 把同一颗场景改钉到某一档色档里再拍一遍（R325 的色档 A/B 探针专用）。
        ///
        /// 为什么要有这一层而不是在探针里自己拼 `Scenario(...)`：场景有九格参数（含四颗闭包），
        /// 手拼一遍就会在下一格加进 `Scenario` 时**静默漏抄**（R38 那一族：同一个东西不许有两份定义）。
        func pinned(to appearance: NSAppearance.Name?) -> Scenario {
            Scenario(name: name, size: size, prepare: prepare,
                     declaredDurationMilliseconds: declaredDurationMilliseconds,
                     appearance: appearance, root: root, storeFactory: storeFactory,
                     captureRect: captureRect, trigger)
        }

        /// R325 / BACKLOG 383：逐颗量"色档换了，这条判据的读数换不换"的**对象表**。
        ///
        /// 这份名单与 `scenarioPinCensus` 数出来的"没钉名单"**必须由判据自己对账成同一份**
        /// （`testFilmScenarioAppearanceDependenceIsMeasuredPerScenario` 第一条断言就是这件事）：
        /// 手写一遍就会在有人新加场景、或有人把某一颗钉上档之后**静默漏掉一颗**，
        /// 而漏掉的那颗正是"我们以为量过了"的那颗。
        static func unpinnedAppearanceProbe() -> [(factory: String, scenario: Scenario)] {
            [("blank", blank()),
             ("detailEmptyToContent", detailEmptyToContent()),
             ("detailKindChange", detailKindChange()),
             ("detailSameKind", detailSameKind()),
             ("emptyState", emptyState()),
             ("heatFirstRecord", heatFirstRecord()),
             ("listInsertNewRecord", listInsertNewRecord()),
             ("noticeBanner", noticeBanner()),
             ("noticeBannerDismiss", noticeBannerDismiss()),
             ("promotionToTop", promotionToTop()),
             ("searchReflow", searchReflow()),
             ("toggleFavoriteInRow", toggleFavoriteInRow())]
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

        /// 抓这一卷时 `MotionCatalog.animationsEnabled` 落在哪一边（R323）。
        ///
        /// 这条存在的全部理由：新加的「三臂逐帧相同 ⇒ 这台机器的胶片里开关不可分」出口，
        /// 与"A/B 开关根本没生效"在**胶片上长得一模一样**（两者都交出一卷同样的画面）。
        /// 没有这个数，出口就会把一把坏开关读成"这台机器判不了" —— 那是把真红洗成 skip。
        /// M923 那一刀（把 `animationsEnabled = false` 删掉）今天正是被这条抓回来的。
        var animationsEnabledAtRecord: Bool = true

        /// 抓这一卷时**实际解析到**的色档（"亮" / "暗" / "未知" / "未记录"，R324）。
        ///
        /// 与场景请求的那一档分开记，理由和 `animationsEnabledAtRecord` 一模一样：
        /// "我请求了暗档"与"胶片真的拍在暗档里"在两棵不同的树上会长得一样，
        /// 而出口（"这一台的材质把两档洗成同一档"）只许替后者说话，不许替一把没生效的请求说话。
        /// 默认值是 `"未记录"` 而不是 `"暗"`：忘了赋值就一定会红在前提上，不会被读成通过。
        var appearanceNameAtRecord: String = "未记录"

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

        static func classify(clockIntervalMilliseconds: Double,
                             worstGrabMilliseconds: Double) -> GrabAttribution {
            guard worstGrabMilliseconds >= 0, clockIntervalMilliseconds > 0 else { return .unknown }
            let explained = worstGrabMilliseconds / clockIntervalMilliseconds
            let overshoot = clockIntervalMilliseconds - worstGrabMilliseconds
            if overshoot <= allowanceMilliseconds {
                return .probeBound(explainedRatio: explained, overshootMilliseconds: overshoot)
            }
            return explained >= dominatesRatio
                ? .grabDominates(explainedRatio: explained, overshootMilliseconds: overshoot)
                : .outsideTheGrab(explainedRatio: explained, overshootMilliseconds: overshoot)
        }
    }

    static func grabAttribution(clockIntervalMilliseconds: Double,
                                worstGrabMilliseconds: Double) -> GrabAttribution {
        GrabAttribution.classify(clockIntervalMilliseconds: clockIntervalMilliseconds,
                                 worstGrabMilliseconds: worstGrabMilliseconds)
    }

    /// 归因怎么说进日志。**令牌必须是英文**（`probe-grab-bound` / `grab-dominates` / `not-the-grab` /
    /// `grab-unmeasured`）：中文短语里的连词与括号会被下游的 grep 切成两半，而这一行是 CI 那一步要读的东西。
    /// 比例也一起打出来：分档是我给的判读，而 `解释=NN%` 是可复核的数。
    static func grabAttributionLabel(clockIntervalMilliseconds: Double,
                                     worstGrabMilliseconds: Double) -> String {
        func percent(_ ratio: Double) -> String { String(format: "%.0f%%", ratio * 100) }
        func ms(_ value: Double) -> String { String(format: "%.0f", value) }
        switch grabAttribution(clockIntervalMilliseconds: clockIntervalMilliseconds,
                               worstGrabMilliseconds: worstGrabMilliseconds) {
        case .unknown:
            return " 归因=grab-unmeasured（这一卷没量抓帧成本，或间隔≤0 ⇒ 不许把间隔赖给抓帧器，也不许说不是它）"
        case .probeBound(let explained, let over):
            return " 归因=probe-grab-bound（解释=\(percent(explained))：这一卷最慢一次抓帧 \(ms(worstGrabMilliseconds))ms，"
                + "而间隔 \(ms(clockIntervalMilliseconds))ms 只比它多 \(ms(over))ms ⇒ 差值就是一次等 runloop 的时间）"
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
        // R324：场景钉了色档就**三处一起钉**。`UICaptureHarness` 顶上第 3 条规矩记过同一件事：
        // 只注入视图层，AppKit 承载的控件（List / NSScrollView 的底）仍按 aqua 取色，
        // 于是"请求了"与"钉住了"是两回事 —— 而判据信的是后者（见 `Film.appearanceNameAtRecord`）。
        let previousAppAppearance = NSApplication.shared.appearance
        if let requested = scenario.appearance.map({ NSAppearance(named: $0) }) {
            NSApplication.shared.appearance = requested
            window.appearance = requested
            host.appearance = requested
        }
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer {
            NSApplication.shared.appearance = previousAppAppearance
            window.orderOut(nil)
        }
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
        // R324：每一卷都把自己的**实际**色档印出来 —— 逐行像素尺的读数离开这一格就没有解释。
        // （同一台机器 亮档 页底/轨道/药丸 = 230/230/233、暗档 = 30/52/36，差 5 倍的分离度。）
        let resolvedAppearance = Self.appearanceName(of: host.effectiveAppearance)
        emit(String(format: "MOTION_GRAB %@ 帧数=%d 抓帧中位=%.1fms 抓帧最慢=%.1fms "
                     + "视图=%.0f×%.0fpt 像素=%@ 声明=%dms 色档=%@ 请求=%@",
                     scenario.name, grabber.frames.count, grabber.medianGrabMilliseconds,
                     grabber.worstGrabMilliseconds, host.bounds.width, host.bounds.height, pixels,
                     Int(scenario.declaredDurationMilliseconds), resolvedAppearance,
                     Self.appearanceName(forRequested: scenario.appearance)))
        return Film(frames: grabber.frames, stamps: grabber.stamps,
                    triggerFrame: triggerFrame, clockIsWarm: clockIsWarm,
                    animationsEnabledAtRecord: MotionCatalog.animationsEnabled,
                    appearanceNameAtRecord: resolvedAppearance,
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

    /// **首末两态差**（R326）：只比第一帧与最后一帧，中间采了几个样本与它无关。
    ///
    /// 为什么本轮要新造这一颗而不是接着用峰值：`peak(deltas(…))` 是"单步最大变化"，
    /// 它的分母是**那台机器的钟**，不是画面。本机与 runner 在**两臂帧数都是 30** 的条件下，
    /// 同一颗 `noticeBanner` 的峰值读成 0.2598（本机）与 0.7208（runner）—— 2.8 倍，
    /// 而夹具是同一份代码画的 ⇒ 拿它去判"这条判据的读数随不随色档走"，
    /// 量到的是采样粒度。后果不是"数不好看"而是**动作相反**：R325 那份分类在本机是
    /// 敏感=0（ ⇒ 12 颗都不钉），在 runner 是 敏感=2（ ⇒ 那两颗该钉）。
    /// 首末差是端点比较：粗采样与细采样对同一份"从 A 态到 B 态"给出同一个数
    /// （证人：`testAppearanceStatisticsSurviveASamplingChange`）。
    static func endpointChangedFraction(_ frames: [CGImage], band: CGRect? = nil) -> Double {
        guard frames.count > 1, let first = frames.first, let last = frames.last else { return 0 }
        return changedFraction(raster(first), raster(last), band: band)
    }

    /// **动过的并集**（R326）：一整卷里至少变过一次的那些采样像素占比。
    ///
    /// 它补的是首末差看不见的那一格：一段"动了又回来"的过程（抖一下、闪一下）首末差读 0，
    /// 而它在两档色档里可以完全不一样。分母与 `changedFraction` 同一套（同一条 stride-7 采样、
    /// 同一个 band 映射），所以两个相对差可以取较大者一起判 —— 这条同一性由
    /// `testEverChangedUsesTheSameDenominatorAsChangedFraction` 钉住（两帧的胶片必须读出同一个数）。
    static func everChangedFraction(_ frames: [CGImage], band: CGRect? = nil) -> Double {
        guard frames.count > 1 else { return 0 }
        let bitmaps = frames.map(raster)
        guard let first = bitmaps.first, first.width > 0, first.height > 0,
              bitmaps.allSatisfy({ $0.width == first.width && $0.height == first.height
                    && $0.pixels.count == first.pixels.count }) else { return 0 }
        let width = first.width, height = first.height
        let xStart, xEnd, yStart, yEnd: Int
        if let band {
            xStart = max(0, Int(band.minX * CGFloat(width)))
            xEnd = min(width, Int(band.maxX * CGFloat(width)))
            yStart = max(0, Int(band.minY * CGFloat(height)))
            yEnd = min(height, Int(band.maxY * CGFloat(height)))
        } else {
            xStart = 0; xEnd = width; yStart = 0; yEnd = height
        }
        guard xEnd > xStart, yEnd > yStart else { return 0 }
        var sampled = 0
        var everChanged = Set<Int>()
        var y = yStart
        while y < yEnd {
            var x = xStart
            while x < xEnd {
                sampled += 1
                for index in 1..<bitmaps.count {
                    let a = bitmaps[index - 1].pixels, b = bitmaps[index].pixels
                    let p = (y * width + x) * 4
                    let rgb = max(abs(Int(a[p]) - Int(b[p])),
                                 max(abs(Int(a[p + 1]) - Int(b[p + 1])),
                                     abs(Int(a[p + 2]) - Int(b[p + 2]))))
                    let alpha = abs(Int(a[p + 3]) - Int(b[p + 3]))
                    if rgb > 8 || alpha > 8 {
                        everChanged.insert(y * width + x)
                        break
                    }
                }
                x += 7
            }
            y += 7
        }
        return Double(everChanged.count) / Double(max(sampled, 1))
    }

    /// 一卷帧的**单步最大变化**（峰值口径）。R326 起它在色档 A/B 里只印不判，
    /// 但仍然是别的判据在用的量；留成 internal 是为了证人能替"这颗尺随采样粒度走"那句话说话
    /// —— 不能替自己造反例的更正，只是一句新的断言。
    static func peakChangedFraction(_ frames: [CGImage], band: CGRect? = nil) -> Double {
        peak(deltas(frames, band: band))
    }

    /// **首末两态的墨量差**（R326）：端点上每个采样像素"最大通道差"的平均值，归一到 0…1。
    ///
    /// 为什么三颗里还要这一颗：首末差与并数都只回答**哪些像素动过**，它们对"动了多少"是盲的 ——
    /// 同一块面积在暗档里从 30 走到 200（差 170 级），在亮档里从 255 走到 190（差 65 级），
    /// 那两颗尺读出来一模一样，而逐行电平尺（`MOTION_PILL_RAMP_GEOM` 那类）的读数会差好几倍。
    /// 少了这一颗，本轮的修法就只是"把判据换窄到它恰好看不见的那一半"（R326 自查时抓到的）。
    /// 证人：`testEndpointAreaIsBlindToInkMagnitudeButTheVerdictIsNot`。
    static func endpointInkDifference(_ frames: [CGImage], band: CGRect? = nil) -> Double {
        guard frames.count > 1, let first = frames.first, let last = frames.last else { return 0 }
        let a = raster(first), b = raster(last)
        guard a.width == b.width, a.height == b.height, a.width > 0, a.height > 0,
              a.pixels.count == b.pixels.count, a.pixels.count == a.width * a.height * 4 else { return 0 }
        let width = a.width, height = a.height
        let xStart, xEnd, yStart, yEnd: Int
        if let band {
            xStart = max(0, Int(band.minX * CGFloat(width)))
            xEnd = min(width, Int(band.maxX * CGFloat(width)))
            yStart = max(0, Int(band.minY * CGFloat(height)))
            yEnd = min(height, Int(band.maxY * CGFloat(height)))
        } else {
            xStart = 0; xEnd = width; yStart = 0; yEnd = height
        }
        guard xEnd > xStart, yEnd > yStart else { return 0 }
        var total = 0.0
        var sampled = 0
        var y = yStart
        while y < yEnd {
            var x = xStart
            while x < xEnd {
                let p = (y * width + x) * 4
                let rgb = max(abs(Int(a.pixels[p]) - Int(b.pixels[p])),
                              max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[p + 1])),
                                  abs(Int(a.pixels[p + 2]) - Int(b.pixels[p + 2]))))
                let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[p + 3]))
                total += Double(Swift.max(rgb, alpha))
                sampled += 1
                x += 7
            }
            y += 7
        }
        guard sampled > 0 else { return 0 }
        return total / Double(sampled) / 255.0
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
                    let rgb = max(abs(Int(a.pixels[p]) - Int(b.pixels[q])),
                                  max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[q + 1])),
                                      abs(Int(a.pixels[p + 2]) - Int(b.pixels[q + 2]))))
                    // R77 / BACKLOG 107：这一行原来只读前三根通道。这条尺子判的是
                    // "带那一帧与整窗那一帧的**同一头**是不是同一块画面"，而它也是两态相减 ——
                    // 只在 alpha 上不同的两块画面会被它读成"相同"，于是"带挪走了"这件事
                    // 可以安静地通过位置同一性那一格。与 `axisPair` 同一形状：并集才算变。
                    let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[q + 3]))
                    if rgb > 8 || alpha > 8 { changed += 1 }
                    sampled += 1
                    x += 7
                }
                y += 7
            }
            return Double(changed) / Double(max(sampled, 1))
        }
        return (diff(from: 0), diff(from: b.height - a.height))
    }

    /// 合成一对位图：`a` 整幅是 `base`，`b` 只在指定行/列带里是 `ink`（默认 200,200,200,255）。
    /// 两条测试共用（R58 的方向真值表、R60 的网格行序），所以它必须是**静态**的：
    /// 各自复制一份，就会有一份跟着实现变旧。
    ///
    /// R77 加了 `base`/`ink` 两个端点：alpha 轴的真值表要能造"墨不变、只有透明度在动"
    /// 和"颜色在动、alpha 钉住"这两格，而固定 200/255 那两个常数造不出来。
    /// 默认值就是原来写死的那两个数 ⇒ 上面那两条老判据的读数一个都没变。
    private static func syntheticPair(width: Int, height: Int,
                                      differingRows: Range<Int>? = nil,
                                      differingColumns: Range<Int>? = nil,
                                      base: (UInt8, UInt8, UInt8, UInt8) = (0, 0, 0, 0),
                                      ink: (UInt8, UInt8, UInt8, UInt8) = (200, 200, 200, 255)) -> (Bitmap, Bitmap) {
        syntheticPair(width: width, height: height, base: base) { x, y in
            let inRows = differingRows.map { $0.contains(y) } ?? true
            let inCols = differingColumns.map { $0.contains(x) } ?? true
            return inRows && inCols ? ink : nil
        }
    }

    /// 真正干活的那一份：逐像素问 `inkAt` 拿 `b` 的取值（`nil` = 与 `base` 相同）。
    /// 上面那个"行/列带"的前端只是它的一个闭包 —— 采样步长与缓冲区布局只有一份，
    /// 不会因为两处各写一遍就算出两个答案（R58 那一课）。
    private static func syntheticPair(width: Int, height: Int,
                                      base: (UInt8, UInt8, UInt8, UInt8),
                                      inkAt: (Int, Int) -> (UInt8, UInt8, UInt8, UInt8)?) -> (Bitmap, Bitmap) {
        var a = [UInt8](repeating: 0, count: width * height * 4)
        var b = [UInt8](repeating: 0, count: width * height * 4)
        for y in 0..<height {
            for x in 0..<width {
                let p = (y * width + x) * 4
                a[p] = base.0; a[p + 1] = base.1; a[p + 2] = base.2; a[p + 3] = base.3
                let pixel = inkAt(x, y) ?? base
                b[p] = pixel.0; b[p + 1] = pixel.1; b[p + 2] = pixel.2; b[p + 3] = pixel.3
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

    /// 一张位图在 `band` 里、**两根轴各自**有多少采样像素不同（R77 / BACKLOG 107）。
    ///
    /// 为什么一次算三根：R76 那条浮层焦点判据（U-132）实测到的差别**只在 alpha 上** ——
    /// 用 PIL 把两张 PNG `convert("RGB")` 之后逐像素相同，留着 alpha 比才看见动过。
    /// 而 `raster` 是 `premultipliedLast` 画进**零初始化**缓冲区的，于是"暗墨变透明"这一族
    /// 在预乘 RGB 上就是 0→0：墨越暗，RGB 这一轴越读不到它的透明度。
    /// 一把只读 RGB 的尺因此会把"暗墨在淡入"判成"没动"，而这条卷里的"没动"是**结论**
    /// （`transitionFrameCount == 0` ⇒ 写进台账的"这条过渡不存在"）。
    /// 所以这里一次算出 `rgb` / `alpha` / `either`，谁在判"动没动"必须用 `either`，
    /// 两根轴各自的数还要能被打印出来 —— 缺一根轴就没人知道另一根在动。
    private struct AxisPair: Equatable {
        /// 预乘 RGB 那一轴：R77 之前这条尺只有它，历史上所有 `逐帧=[…]` 读数都是这根。
        var rgb: Double
        /// alpha 那一轴：同一套地板（8/255），两根轴共用门槛才可比。
        var alpha: Double
        /// 并集：任一轴过地板就算这一像素变了。**不是** `max(rgb, alpha)` ——
        /// 那个数只会偏小（两轴各动一半像素时它读一半），拿它当"变了多少"会低估。
        var either: Double

        static func format(_ value: Double) -> String { String(format: "%.4f", value) }
    }

    /// 一次算三根轴的那个循环。`changedFraction` 与 `axisSummary` 都必须走这里，
    /// 不许各自再写一份采样步长/阈值（R58 那一课：两份各写一遍迟早算出两个答案）。
    private static func axisPair(_ a: Bitmap, _ b: Bitmap, band: CGRect?) -> AxisPair {
        guard !a.pixels.isEmpty, a.pixels.count == b.pixels.count, a.width == b.width, a.height == b.height,
              a.width > 0, a.height > 0 else { return AxisPair(rgb: 0, alpha: 0, either: 0) }
        let xStart, xEnd, yStart, yEnd: Int
        if let band {
            xStart = max(0, Int(band.minX * CGFloat(a.width)))
            xEnd = min(a.width, Int(band.maxX * CGFloat(a.width)))
            yStart = max(0, Int(band.minY * CGFloat(a.height)))
            yEnd = min(a.height, Int(band.maxY * CGFloat(a.height)))
        } else {
            xStart = 0; xEnd = a.width; yStart = 0; yEnd = a.height
        }
        guard xEnd > xStart, yEnd > yStart else { return AxisPair(rgb: 0, alpha: 0, either: 0) }
        var changedRgb = 0
        var changedAlpha = 0
        var changedEither = 0
        var sampled = 0
        var y = yStart
        while y < yEnd {
            var x = xStart
            while x < xEnd {
                let p = (y * a.width + x) * 4
                let rgb = max(abs(Int(a.pixels[p]) - Int(b.pixels[p])),
                              max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[p + 1])),
                                  abs(Int(a.pixels[p + 2]) - Int(b.pixels[p + 2]))))
                let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[p + 3]))
                if rgb > 8 { changedRgb += 1 }
                if alpha > 8 { changedAlpha += 1 }
                if rgb > 8 || alpha > 8 { changedEither += 1 }
                sampled += 1
                x += 7
            }
            y += 7
        }
        let n = Double(max(sampled, 1))
        return AxisPair(rgb: Double(changedRgb) / n, alpha: Double(changedAlpha) / n,
                        either: Double(changedEither) / n)
    }

    /// 一卷帧在两根轴上的峰值，连"只有 alpha 在动、亮度读不出来"的帧对数，打成一格读数。
    ///
    /// `仅alpha在动=K/N` 才是这一轮要的那个量：它是"旧尺子会漏掉的东西有几帧"。
    /// 今天它大概率是 0（这条通道的窗口是实心的），但 0 必须是**量出来的 0** ——
    /// R76 之前我也一直当它是 0，而那一次的实测读数是"差别只在 alpha"（U-132）。
    static func axisSummaryLine(_ frames: [CGImage], band: CGRect? = nil) -> String {
        let bitmaps = frames.map(raster)
        guard bitmaps.count > 1 else { return "帧对=0 亮度峰值=0.0000 alpha峰值=0.0000 并集峰值=0.0000 仅alpha在动=0/0" }
        var peak = AxisPair(rgb: 0, alpha: 0, either: 0)
        var alphaOnly = 0
        for index in 1..<bitmaps.count {
            let pair = axisPair(bitmaps[index - 1], bitmaps[index], band: band)
            peak.rgb = max(peak.rgb, pair.rgb)
            peak.alpha = max(peak.alpha, pair.alpha)
            peak.either = max(peak.either, pair.either)
            if pair.alpha >= minimumVisibleChange, pair.rgb < minimumVisibleChange { alphaOnly += 1 }
        }
        let pairs = bitmaps.count - 1
        return "帧对=\(pairs) 亮度峰值=\(AxisPair.format(peak.rgb)) "
            + "alpha峰值=\(AxisPair.format(peak.alpha)) 并集峰值=\(AxisPair.format(peak.either)) "
            + "仅alpha在动=\(alphaOnly)/\(pairs)"
    }

    /// 两张位图在 `band` 里有多少采样像素不同。
    ///
    /// **R77 起这一句返回的是并集那一轴**（`axisPair.either`）：动效/静止的结论必须两根轴都不动才成立。
    /// 亮度那一根仍然要能拿到，就在 `axisPair(...).rgb`，别在调用方再写一份循环。
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
        axisPair(a, b, band: band).either
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
        MotionFilmstripTests.emit("NATIVE_PROBE_STATE visible=\(window.isVisible) key=\(window.isKeyWindow) active=\(NSApp.isActive)")

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
        MotionFilmstripTests.emit("NATIVE_PROBE_STATE visible=\(window.isVisible) key=\(window.isKeyWindow) active=\(NSApp.isActive)")
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

// MARK: - 一卷胶片：帧 + 它们的时刻（R82 / U-155）

/// 一卷胶片**连同它的抓帧时刻**一起返回。
///
/// 为什么不让探针把 `lastStamps` 存在自己身上（原来就是这个形状）：两卷连拍时后一卷会覆盖
/// 前一卷的时刻，于是"拿后一卷的时刻算前一卷的形状"这句话**写得出来**，而且写错的时候读起来
/// 完全合理 —— R82 现场：产品那卷的形状吃了静止那卷的时刻，本机读到 coverage=0.000
/// （两卷碰巧不等长），而等长时它读到 0.979，**断言一条都不红**
/// （M443 第一版：把这句话改回 `probe.lastStamps`，四条判据全绿 ⇒ U-155）。
/// 绑成一对之后，错的那句话在类型上拼不出来。
/// （这个文件里**早就有**这个形状：主场景探针的 `Film(frames:stamps:triggerFrame:)`
///   与淡入探针的 `FadeClockProbe.Run` —— 只有这两个手写探针把时刻存在了探针身上。）
private struct GrabbedFilm {
    let frames: [CGImage]
    let stamps: [TimeInterval]
}

/// 常驻循环那三卷的**共同**抓帧时长（产品一卷 + 两颗证人各一卷，R82）。
/// 只有一条性质要保证：**被判的那一段和当反证的那两段必须一样长**。
private let loopFilmSeconds: TimeInterval = 2.5

// MARK: - 骨架扫光探针

/// 骨架探针那张视图的**点宽**（R84）。
/// 位置判据要说"三根条的亮斑在同一条竖线上"，而"竖线"的单位是点 ⇒ 像素必须按这个宽度换算。
/// 它同时是探针开窗的宽度与判据的换算基数，所以只能有一处定义：写两份迟早分家（R58 同一课）。
private let skeletonViewWidthPoints: Double = 420

/// 在离屏窗口里 host 一个 `SkeletonPreviewView`，连抓 30 帧。
///
/// 为什么不通过 `DetailFileView` 走：那条路要真去读一个文件的预览，`MediaLoader` 什么时候回来
/// 由磁盘和 QuickLook 决定 —— 拿它做"这段里有没有连续变化"的判据，红绿会跟着机器状态漂。
/// 这里量的是**这把尺能不能看见渐变位移**；"骨架接在加载分支上"那半条由
/// `SkeletonMotionTests.testSkeletonIsWiredIntoTheDetailLoadingBranch` 钉住。
@MainActor
private final class SkeletonProbe {
    func record(reduceMotion: Bool) -> GrabbedFilm {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140,
                                                  width: CGFloat(skeletonViewWidthPoints), height: 220),
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
        // 与两颗证人**同一个时长**（`loopFilmSeconds`）：产品 2.5 秒、证人 2.0 秒的话，
        // "这台机器带不动循环"就只覆盖了被判的那一段的一部分。
        let deadline = Date().addingTimeInterval(loopFilmSeconds)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            grabber.tick()
        }
        return GrabbedFilm(frames: grabber.frames, stamps: grabber.stamps)
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

    func record() -> GrabbedFilm { record(motionClass: .layout) }

    /// `seconds` = 抓够多久。**证人必须与产品那卷同长**（R82）：产品那卷是 2.5s，
    /// 证人只抓 2.0s 的话，"这台机器带不动循环"就成了"2.0 秒之内带不动"，
    /// 而产品被判的那一段比这更长 —— 窗口不一致的两条曲线不能互相当反证。
    func record(motionClass: MotionFilmstripTests.MotionClass,
                seconds: TimeInterval = 2.0) -> GrabbedFilm {
        _ = NSApplication.shared
        let window = NSWindow(contentRect: NSRect(x: 140, y: 140, width: 420, height: 220),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let root: AnyView
        switch motionClass {
        case .layout: root = AnyView(TickCounterView())
        case .gradient: root = AnyView(GradientTickView())
        case .gradientAtProductRate: root = AnyView(GradientTickView.productRate())
        }
        let host = NSHostingView(rootView: root)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        defer { window.orderOut(nil) }
        RunLoop.main.run(until: Date().addingTimeInterval(0.25))
        let grabber = Grabber(view: host, limit: 400)
        let deadline = Date().addingTimeInterval(seconds)
        while !grabber.finished, Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            grabber.tick()
        }
        return GrabbedFilm(frames: grabber.frames, stamps: grabber.stamps)
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
        /// 一次 `cacheDisplay` 的中位 / 最慢耗时（ms）。R72 起跟着读数一起交出去：
        /// 没有它，"采样 81ms" 这一句里有多少是抓帧、有多少是 runloop 没醒，永远分不开
        /// （R55 那一族 —— 上一轮我就是拿一个数当成了原因）。
        let medianGrabMilliseconds: Double
        let worstGrabMilliseconds: Double
    }

    func record() -> Run {
        _ = NSApplication.shared
        // 窗口 320×180，但**只抓左上角 190×24 那一条**（R68 / BACKLOG 104）。
        //
        // 这一条保留，但**它当时的理由已被 R68+R69 那一次 CI 证伪**（诚实记账，不删）：
        // 我当时写"证人比被告贵 1.6 倍 ⇒ 面积决定它采得粗"。实测：面积从 57,600pt² 降到 4,560pt²
        // （12.6 倍）之后，runner 上证人采样 80ms ⇒ **81ms，一点没变细**。
        // ⇒ 限制采样的不是面积，是循环的睡眠节拍与这台机器的 runloop（见下面那个 0.004）。
        // 面积仍然要小（省时间、也保证证人不会比被告更贵），但它不是这一格的原因。
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
            // 0.004 —— **与它作证的那条判据同一个循环形状**（`record(_:)` 里就是 0.004，见 3996 行）。
            // R68 我写的是 0.02，理由写着"这里要分辨的过程只有 150ms"；
            // 而 R68+R69 那一次 CI 把我的解释证伪了：
            //   面积 57,600pt² → 4,560pt²（小 12.6 倍），runner 采样 80ms → **81ms（一点没变细）**，
            //   同一遍里判据自己 23ms。⇒ 限制证人的不是抓帧面积，是**它的睡眠节拍 + 这台机器的 runloop**，
            //   而我唯一能控制的那一项就是节拍。判据用 0.004，证人也必须用 0.004，
            //   否则"证人看不见"永远可能只是"证人睡得比判据久"（BACKLOG 104 的原始形状）。
            RunLoop.main.run(until: Date().addingTimeInterval(0.004))
            grabber.tick()
        }
        let levels = grabber.frames.map { MotionFilmstripTests.meanLevel($0) }
        // 成本与间隔**分开带出来**（R72）：下一次 runner 的那一遍要能回答
        // "81ms 里有多少是 `cacheDisplay`，有多少是 runloop 没醒" ——
        // 上一轮我答错了（说成面积），因为只有一个数。打印仍归测试类（`emit` 在那边）。
        return Run(frames: grabber.frames, levels: levels,
                   samplingMilliseconds: MotionFilmstripTests.sampleIntervalMilliseconds(grabber.stamps),
                   medianGrabMilliseconds: grabber.medianGrabMilliseconds,
                   worstGrabMilliseconds: grabber.worstGrabMilliseconds)
    }
}

/// 只动 `LinearGradient` 的两个端点，其它一切都不动。
///
/// 四个可调的量（节拍、每拍推进量、底色、亮带）都开成参数，是因为 R82 需要用这颗视图问**两句**
/// 不同的话：默认那一档问"这台机器看不看得见这种画法的变化"，
/// `productRate()` 那一档问"这台机器带不带得动**产品那一档节拍与那一档对比度**的常驻循环"。
/// 默认值就是原来写死的那几个数 ⇒ 老调用点（`requireObservableMotion`、`MOTION_CONTROL`）读数不变。
@MainActor
private struct GradientTickView: View {
    var tickSeconds: TimeInterval = 0.05
    var stepPerTick: CGFloat = 0.05
    var baseOpacity: Double = 0.06
    var highlightOpacity: Double = 0.45

    /// 亮带相对底色的抬升 —— 决定"这把尺看不看得见它"的就是这个量。
    var highlightLift: Double { highlightOpacity - baseOpacity }

    @State private var phase: CGFloat = 0

    var body: some View {
        skeleton(phase: phase)
            .onReceive(Timer.publish(every: tickSeconds, on: .main, in: .common).autoconnect()) { _ in
                phase = SkeletonMotion.advance(phase, by: stepPerTick)
            }
    }

    /// 与骨架扫光**同数字**的那一颗证人。四个数都写死在这里、不读 `SkeletonMotion` /
    /// `MotionCatalog`，理由与 `FadeClockView` 把 150ms 写死是同一条：读产品的常量的话，
    /// 哪天产品把亮带抬升调到看不见，证人跟着一起瞎，于是"环境看不见"那一支永远有人签字。
    /// 写死的代价是**会漂移** ⇒ 由 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住
    /// "这几颗数还等于产品那几颗"（漂移是红的，不是一行注释）。
    static func productRate() -> GradientTickView {
        GradientTickView(tickSeconds: 1.0 / 30.0,
                         stepPerTick: (1.0 / 30.0) / 1.5,
                         baseOpacity: 0.06,
                         highlightOpacity: 0.18)
    }

    /// 与 `SkeletonPreviewView` **同一套画法**（整组一个形状 + 一条容器坐标系的渐变填充），
    /// 只有驱动方式不同：这里是视图自己的 `@State`。
    /// 分成两个视图而不是只测一个，是为了把"驱动方式"和"画法"这两个嫌疑分开 ——
    /// 否则读到不动时，仍然不知道该改时钟还是该改布局。
    ///
    /// R84：产品从"每根条一个 `RoundedRectangle`"换成整组一个 `SkeletonBarsShape`，这里跟着换。
    /// 这句话不是注释体的礼貌 —— 它要是不同步，`.productRed` 那一支的推论（"只差视图归谁这一个差别"）
    /// 当场失效。四个数字由 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住，
    /// **画法**由同一条里的源码守卫钉住：证人不是被量的对象，没法从像素反推它画的是什么。
    private func skeleton(phase: CGFloat) -> some View {
        SkeletonBarsShape().fill(LinearGradient(
            stops: [.init(color: .primary.opacity(baseOpacity), location: 0),
                    .init(color: .primary.opacity(highlightOpacity), location: 0.5),
                    .init(color: .primary.opacity(baseOpacity), location: 1)],
            startPoint: SkeletonMotion.unitPoints(phase: phase).start,
            endPoint: SkeletonMotion.unitPoints(phase: phase).end))
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
