import XCTest
@testable import ClipboardHistoryApp

/// 采集路径（用户按下 ⌘C 之后，`HistoryStore.add` 那条同步链）的三条判据（R49 立 / R51 重做）。
///
/// 为什么本轮要新增这个文件：R48 给热图那条淡入 A/B 补上 per-run 打印之后，
/// 读到的是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms` ——
/// **一段连续的变化里有一次 260ms 的抓帧空档**。这件事有两种性质完全不同的解释：
/// ① 产品在自己的事件路径上占住了主线程（那就是卡顿，而且目标里明令"采集路径上不许有同步磁盘写"）；
/// ② 探针自己那次同步 `cacheDisplay` 慢（本文件顶部 `MotionFilmstripTests` 的预卷注释里
///    就写着"新窗口的头两次 `cacheDisplay` 要 260–340ms 一帧"）。
/// 上一轮我把这两种混在了一句"要查"里。**光靠计时分不开它们** —— 计时只能证明"有没有超时"，
/// 证明不了"有没有写盘"。所以这里三条一起立：
/// 一条**行为**判据（把写队列堵起来：堵着就不许出现文件，放开就必须出现），
/// 两条**时长**判据（小库与快满的库各一条 —— 这条链的成本随库大小增长，只测小库等于没测）。
/// R51 的实测还给出一个不体面的边界：**时长判据抓不到行为判据抓到的那件事**
/// （M249 把写盘真的搬回主线程，`add` 只涨到 2.54ms，仍然绿），所以三条不能互相替代。
///
/// 不覆盖管线：不适用 —— 本文件全部从产品入口 `HistoryStore.add` 进入，
/// 没有一条只调内部纯函数（`percentile` 那格是尺子自己的真值表，见它的注释）。
@MainActor
final class CapturePathWriteBudgetTests: XCTestCase {

    // `nonisolated(unsafe)`：`setUpWithError` 是 nonisolated 的，而这个属性只有测试方法（主 actor）读写。
    // 不加这个标注的话整个类要在 setUp 里 hop，而 XCTest 的 setUp 不支持 await。
    private nonisolated(unsafe) var temporaryDirectory: URL!

    override func setUpWithError() throws {
        temporaryDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("r49-capture-path-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: temporaryDirectory,
                                                withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: temporaryDirectory)
    }

    // MARK: - R171：落盘轮询那颗纯谓词（把固定 sleep 换掉之后，"等不等"必须自己钉得住）
    //
    // 这两格是上面那三条判据的**前提钉子**，不是第四条判据：行为与时长仍然由 `HistoryStore.add` 那三条作证。

    /// 三种结局互不重叠，而且都是读数不是形容词：
    /// `landed` 数量对上 / `timeout` 到上限还不对（真红，带两端的数）/ `keep-polling` 还要等。
    enum ArchiveReloadWait {
        static let pollInterval: TimeInterval = 0.1
        static let timeout: TimeInterval = 5.0
        static let maxPolls = 60
        static let landed = "landed"
        static let timedOut = "timeout"
        static let keepPolling = "keep-polling"

        static func outcome(seeded: Int, reloaded: Int, elapsed: TimeInterval) -> String {
            if reloaded == seeded { return landed }
            return elapsed >= timeout ? timedOut : keepPolling
        }
    }

    struct ReloadWait {
        let reloaded: Int
        let polls: Int
        let elapsed: TimeInterval
        let outcome: String
    }

    /// 重开库直到快照落地，或到上限。**每一拍都真的重开一次库**（不是读内存里那份缓存），
    /// 所以它测的是"落盘到可读"这件事，不是"睡够了没"。
    static func awaitFlushedSnapshot(matching expected: Int, in directory: URL) -> ReloadWait {
        let start = Date()
        var polls = 0
        var reloaded = 0
        var outcome = ArchiveReloadWait.keepPolling
        while polls < ArchiveReloadWait.maxPolls {
            polls += 1
            let probe = HistoryStore(clipboardWriter: TestClipboardWriter(),
                                     persistence: FileHistoryPersistence(rootDirectory: directory),
                                     dailyCopyLedger: nil)
            reloaded = probe.entries.count
            outcome = ArchiveReloadWait.outcome(seeded: expected, reloaded: reloaded,
                                                elapsed: -start.timeIntervalSinceNow)
            if outcome != ArchiveReloadWait.keepPolling { break }
            Thread.sleep(forTimeInterval: ArchiveReloadWait.pollInterval)
        }
        return ReloadWait(reloaded: reloaded, polls: polls,
                          elapsed: -start.timeIntervalSinceNow, outcome: outcome)
    }

    func testReloadWaitTruthTable() {
        XCTAssertEqual(CapturePathWriteBudgetTests.ArchiveReloadWait
                       .outcome(seeded: 480, reloaded: 480, elapsed: 0.0),
                       CapturePathWriteBudgetTests.ArchiveReloadWait.landed)
        XCTAssertEqual(CapturePathWriteBudgetTests.ArchiveReloadWait
                       .outcome(seeded: 480, reloaded: 459, elapsed: 2.0),
                       CapturePathWriteBudgetTests.ArchiveReloadWait.keepPolling)
        XCTAssertEqual(CapturePathWriteBudgetTests.ArchiveReloadWait
                       .outcome(seeded: 480, reloaded: 459, elapsed: 5.0),
                       CapturePathWriteBudgetTests.ArchiveReloadWait.timedOut,
                       "边界那一拍（elapsed == timeout）必须是 timeout —— 写成 `>` 会永远多等一拍，而多等就是下一次假绿")
        XCTAssertEqual(CapturePathWriteBudgetTests.ArchiveReloadWait
                       .outcome(seeded: 480, reloaded: 500, elapsed: 0.1),
                       CapturePathWriteBudgetTests.ArchiveReloadWait.keepPolling,
                       "读到比预期更多的库不算「落地」：那是读到了别的库（临时目录被复用那一族），必须继续等到超时，不许当通过")
    }

    /// 上限必须存在：没有 `maxPolls`，一颗永不落地的快照会把这一格挂到 CI 超时（比红更坏）。
    func testReloadWaitIsBounded() {
        let total = CapturePathWriteBudgetTests.ArchiveReloadWait.pollInterval
            * TimeInterval(CapturePathWriteBudgetTests.ArchiveReloadWait.maxPolls)
        XCTAssertLessThanOrEqual(total, CapturePathWriteBudgetTests.ArchiveReloadWait.timeout + 1.0,
                                 "轮询总时长 \(total)s 超过 timeout + 1s ⇒ 这条出口会变成挂住")
        XCTAssertGreaterThan(CapturePathWriteBudgetTests.ArchiveReloadWait.timeout, 0.5,
                             "上限小于 0.5s 等于回到固定 sleep：满载时照样读不到刚写完的库")
    }

    // MARK: - 判据一：采集路径上不许有同步磁盘写

    /// 从产品入口复制一条内容，**主线程那一次不许碰盘**。
    ///
    /// 这一条是 R49 写的、R51 重做的。R49 那版是"复制之后整个临时目录一个文件都不许多"，
    /// 它在本机第一次全量跑就红了，而红得**不对**：多出来的那个文件是
    /// `history.json.sb-11faeef9-PWSNBE` —— 原子写的临时文件，由**后台** `saveQueue` 创建。
    /// 也就是说目录快照分不清"主线程同步写"与"后台正在写"，它测的是错的东西
    /// （目标禁的是**同步**磁盘写，后台异步写正是设计要求的形状）。
    ///
    /// 现在的做法是把持久化的写队列**先堵起来**，再复制：
    /// ① 写如果是排在队列后面的 ⇒ `add` 立刻返回，且被堵期间盘上没有 `history.json`；
    /// ② 写如果发生在主线程 ⇒ 它绕不开这个堵，要么当场就出现文件（红），要么直接卡住（超时也是红）。
    /// 放开闸门之后文件必须出现 —— 这一句是对照组：没有它，"没写盘"可以靠"根本没接上盘"来绿。
    func testAddingACopyWritesNothingOnTheMainThread() throws {
        let blocked = DispatchSemaphore(value: 0)
        let queue = DispatchQueue(label: "r51.blocked-save-queue")
        queue.async { blocked.wait() }          // 这个串行队列现在什么都干不了
        let ledgerURL = temporaryDirectory.appendingPathComponent("daily-copy.json")
        let historyURL = temporaryDirectory.appendingPathComponent("history.json")
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: temporaryDirectory, saveQueue: queue),
            dailyCopyLedger: DailyCopyLedger(fileURL: ledgerURL, debounceSeconds: 0.4))

        XCTAssertFalse(FileManager.default.fileExists(atPath: historyURL.path),
                       "构造期就落了盘 ⇒ 这条判据的前提没了（init 不许写盘是 D-002 的边界）")
        // **同一次运行里的空转基线**（R271 / BACKLOG 325）：另一颗没被堵的 store、同一个 `add`。
        // 为什么要它：绝对 ms 地板既抓不住真坏法（M249 把写盘搬回调用线程之后本机只值 2.54ms，
        // 照样绿），又会在负载高的 runner 上把 12.17ms 的正常抖动判成产品缺陷（run 39566666631 现读）。
        // 换成"堵住的 add ≤ K × 同一次运行的空转 add"之后，两个量一起随负载漂，比值不漂。
        let idleDirectory = temporaryDirectory.appendingPathComponent("idle-baseline", isDirectory: true)
        try FileManager.default.createDirectory(at: idleDirectory, withIntermediateDirectories: true)
        let idleStore = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: idleDirectory),
            dailyCopyLedger: DailyCopyLedger(fileURL: idleDirectory.appendingPathComponent("daily-copy.json"),
                                             debounceSeconds: 0.4))
        func timeAdd(_ target: HistoryStore) -> Double {
            let t0 = DispatchTime.now()
            target.add(entry("同一条内容，另一颗没被堵的 store"), timestamp: Date())
            return Double(DispatchTime.now().uptimeNanoseconds - t0.uptimeNanoseconds) / 1_000_000
        }
        let idleSamples = [timeAdd(idleStore), timeAdd(idleStore), timeAdd(idleStore)]
        let idle = idleSamples.sorted()[idleSamples.count / 2]      // 中位数：单颗样本的抖动不算基线
        let start = DispatchTime.now()
        store.add(entry("采集路径不该同步写盘的那一条"), timestamp: Date())
        let elapsed = Double(DispatchTime.now().uptimeNanoseconds - start.uptimeNanoseconds) / 1_000_000

        XCTAssertFalse(FileManager.default.fileExists(atPath: historyURL.path),
                       "写队列还堵着，`history.json` 就已经出现 ⇒ 那次写发生在调用线程上，"
                       + "不是排在后台队列里 ⇒ 目标里那句「采集路径上不许有同步磁盘写」不成立")
        XCTAssertFalse(FileManager.default.fileExists(atPath: ledgerURL.path),
                       "账本在 `add` 返回之前就已经落盘 ⇒ 去抖没起作用")
        print(String(format: "CAPTURE_PATH_BLOCKED add 用时=%.3fms 空转基线=%.3fms 倍率=%.2f 地板倍率=%.2f 绝对值=%@（只印不判）",
                     elapsed, idle, elapsed / max(idle, 0.001), Self.blockedRatioReference,
                     String(format: "%.2fms", Self.blockedQueuePrintOnlyMilliseconds)))
        // 比值**只印不判**（R271 现读把这条判据证伪了）：干净三跑的倍率是 1.13 / 1.05 / 0.96，
        //  而把写盘搬回调用线程那把刀（M831）跑出来的倍率是 0.85 —— 比干净还低。原因与这颗地板自陈的
        // 那句是同一件：库太小，两个量都在亚毫秒，噪声（预热、分配器）比"同步写一次盘"的成本还大。
        // ⇒ 时间这条轴在这里没有分辨力，硬门留在**行为**那一侧（上面两条"盘上有没有出现文件"）。
        // 被禁止的两种自欺：① 把绝对 ms 地板放宽到达标；② 把一条抓不住坏法的比值写成判据（装饰性闸门）。
        blocked.signal()                        // 放开闸门
        let deadline = Date().addingTimeInterval(3.0)
        while !FileManager.default.fileExists(atPath: historyURL.path), Date() < deadline {
            pumpRunLoopStep(seconds: 0.05)
        }
        XCTAssertTrue(FileManager.default.fileExists(atPath: historyURL.path),
                      "放开闸门之后存档仍然没出现 ⇒ 上面那两条「没写盘」是因为根本没接上盘，"
                      + "不是因为有去抖。这条判据就成了一条恒真的空话")
        // 账本走的是"去抖 + 后台队列"，所以它必须**晚一点**才出现；这里只要求它最终出现。
        let ledgerDeadline = Date().addingTimeInterval(3.0)
        while !FileManager.default.fileExists(atPath: ledgerURL.path), Date() < ledgerDeadline {
            pumpRunLoopStep(seconds: 0.05)
        }
        XCTAssertTrue(FileManager.default.fileExists(atPath: ledgerURL.path),
                      "账本始终没落盘 ⇒ 计数只活在内存里，重启就丢（阶段一的可回溯性要求）")
    }

    /// 队列被堵住时 `add` 允许花的时间（ms）。
    /// 本机实测 `CAPTURE_PATH_BLOCKED add 用时=0.48 / 0.49 / 0.53ms` ⇒ 取 10ms（约 20 倍余量，与另两条同一把尺）。
    ///
    /// **这一条的分辨率必须写清楚，否则它会冒充成判据一**：变异 M249 把写盘真的搬回调用线程之后，
    /// 这一条打印出来是 `用时=2.54ms` —— 仍然绿。也就是说在小库上"同步写一次盘"只值 2ms，
    /// 任何按 ms 定的门槛都要么松到抓不住它、要么紧到在 CI 那台机器上恒红（R38 那条规矩）。
    /// 真正在管"不许有同步磁盘写"的是上面那条**行为**判据（盘上有没有出现文件），
    /// 这一条管的是另一件事：不写盘的时候这条链占住主线程多久。
    ///
    /// R271 / 325：这一颗从此**只印不判**（`blockedQueuePrintOnlyMilliseconds`）。判交给下面的比值地板 ——
    /// 理由是现读的：run 39566666631 在 runner 上报 `12.17ms ≥ 10ms`，而同一份 Swift 代码在
    /// e87191a／2073b12 两跑都是绿的 ⇒ 绝对挂钟地板在负载前不是判据，是一朵会翻脸的红。
    /// 放宽它（改成 20ms）是被禁止的修法：那只会把"没有分辨率"和"会假红"两件事都留下。
    ///
    /// 比值地板由本机现读推出来（不是猜的）：空转那次 ~0.0x ms、被堵那次 ~0.5ms，
    /// 而把写盘搬回调用线程的坏法（M249 形状）会把比值抬到两位数 ⇒ 取 25 倍留噪声余量，
    /// 并由刀 M831 证明它抓得住那把旧尺抓不住的东西。
    static let blockedRatioReference: Double = 25
    static let blockedQueuePrintOnlyMilliseconds: Double = 10

    // MARK: - 判据二：主线程在这条链上花的时间必须是个数

    /// 把"复制一条内容占住主线程多久"变成一个**可红**的数。
    ///
    /// 门槛怎么来的：见下面 `budgetMilliseconds` 的注释 —— 从实测分布推导，不是抄来的常数。
    /// 这一条与上一条是两件事：上一条管"有没有写盘"，这一条管"就算不写盘，
    /// 这条链上的其它工作（索引、降采样、发布）有没有把主线程占久到能被用户感觉到"。
    func testAddingACopyKeepsTheMainThreadInsideBudget() throws {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: temporaryDirectory),
            dailyCopyLedger: DailyCopyLedger(fileURL: temporaryDirectory.appendingPathComponent("budget.json"),
                                             debounceSeconds: 60))

        var samples: [Double] = []
        samples.reserveCapacity(Self.sampleCount)
        for index in 0..<Self.sampleCount {
            let start = DispatchTime.now()
            store.add(entry("第 \(index) 条：采集路径耗时样本"), timestamp: Date())
            let end = DispatchTime.now()
            samples.append(Double(end.uptimeNanoseconds - start.uptimeNanoseconds) / 1_000_000)
        }

        let median = Self.percentile(samples, 0.5)
        let p95 = Self.percentile(samples, 0.95)
        let worst = samples.max() ?? 0
        print(String(format: "CAPTURE_PATH_BUDGET n=%d median=%.2fms p95=%.2fms max=%.2fms 门槛=%.0fms",
                     samples.count, median, p95, worst, Self.budgetMilliseconds))

        XCTAssertLessThanOrEqual(median, Self.budgetMilliseconds,
                                 "中位数就超了 ⇒ 这不是偶发抖动，是这条链常态化的主线程成本")
        XCTAssertLessThanOrEqual(p95, Self.budgetMilliseconds * Self.p95Multiplier,
                                 "p95 超到门槛的 \(Self.p95Multiplier) 倍以上 ⇒ 每 20 条里就有 1 条能被感觉到")
        // 样本数要钉在一条**与 `sampleCount` 无关**的地板上。
        // 原来这里写的是 `XCTAssertEqual(samples.count, Self.sampleCount)` —— 那是一句恒真：
        // 把 `sampleCount` 从 40 改成 5，循环与断言一起变，谁都不会红。
        // 地板独立存在才有判别力（真值表第 ⑥ 格给了理由：n 太小时 p95 就是换了名字的最大值）。
        XCTAssertGreaterThanOrEqual(samples.count, Self.minimumSampleCount,
                                    "样本掉到 \(Self.minimumSampleCount) 以下 ⇒ p95 不再是一个分位数")
    }

    /// 存档**快满了**的时候，一次复制在主线程上花多少（R51）。
    ///
    /// 为什么必须单独一条：上面那 40 个样本是在"几条记录"的小库里测的，
    /// 而这条链的主线程成本**随库大小增长**（同一次跑、同一台机器：小库 median 0.55ms
    /// ⇒ 480 条时 2.47ms，差 4.5 倍）。500 条上限那一天才是这条链最贵的时候，
    /// "不许有同步磁盘写"如果只测小库，等于没测。
    ///
    /// **但增长的构成不是我以为的那个**（M253 实测推翻了我先写的一句话）：
    /// 我原本写"这条测的是 `saveSnapshot`（整库 JSON 编码 + 图片规划），因为它在调用线程上跑"。
    /// 变异电池那一次把 `saveSnapshot` 真跑两遍，median 只从 2.43 涨到 2.93ms
    /// ⇒ **整库快照只占约 0.5ms**，也就是 median 的五分之一。剩下那约 1.9ms 在别处
    /// （索引 / 降采样 / 发布 / 视图 diff，本文件没有把它们分开量，那是 BACKLOG 76）。
    /// 所以这条判据红了之后要做的第一件事是**分段量**，不是直接把 `saveSnapshot` 搬出主线程 ——
    /// 搬了它也只能省下两成。
    func testAddingACopyWithANearlyFullArchiveStaysInsideBudget() throws {
        // ① 先造一个接近上限的存档（真写盘，之后重新加载它）。
        let seeding = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: temporaryDirectory),
            dailyCopyLedger: nil)
        for index in 0..<Self.fullArchiveEntries {
            seeding.add(entry("填满存档的第 \(index) 条：这条的存在只为了让快照变大"), timestamp: Date())
        }
        // R171：这里以前是 `pumpMain(seconds: 0.4)` —— 一个**固定 sleep** 去等异步落盘。
        // 满载时它不够（R168 实测红在 459 vs 480，R169 又一跑红到连 `failed` 那行都被 stdout 吞了），
        // 而"等多久"从来不是这条判据要问的事：它要的是"库到底落没落地"。
        // 现在换成**有界轮询**（`ArchiveReloadWait` 那颗纯谓词决定等不等，超时才红，并把第几拍的数打出来）。

        // ② 先把"快照落没落地"轮询到（落地的读数由 `ArchiveReloadWait` 那颗纯谓词判，不是拍脑袋等多久）。
        let wait = Self.awaitFlushedSnapshot(matching: seeding.entries.count, in: temporaryDirectory)
        // ③ 换一个"写队列被堵住"的持久化重新开一个库：此时主线程只剩快照要做。
        let blocked = DispatchSemaphore(value: 0)
        let queue = DispatchQueue(label: "r51.blocked-full-archive-queue")
        queue.async { blocked.wait() }
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: temporaryDirectory, saveQueue: queue),
            dailyCopyLedger: nil)
        XCTAssertEqual(store.entries.count, seeding.entries.count,
                       "重新加载没拿到同一份库 ⇒ 下面测的是空库，白测"
                       + "（轮询 \(wait.polls) 拍 / \(String(format: "%.2f", wait.elapsed))s / "
                       + "最后一拍 reloaded=\(wait.reloaded) 期望=\(seeding.entries.count) / 成因 \(wait.outcome)）")
        // 这一条钉的是**前提**：库真的接近上限。
        // 地板是一个**独立**的绝对数，不是 `fullArchiveEntries - 20`：R51 第一版写的就是后者，
        // 而那是自适应阈值 —— 把 `fullArchiveEntries` 改成 1，地板跟着变成 -19，
        // 这条前提断言恒真，正好把"它要防的那次退化"放过去了（变异 M251 实测，见下）。
        // 同一族在本仓库记过不止一次（`sampleCount` 与 `minimumSampleCount` 必须分开也是这件事）。
        XCTAssertGreaterThanOrEqual(seeding.entries.count, Self.fullArchivePremiseFloor,
                                    "造库没造满 ⇒ 下面那个数不是在测快满的库，是在测空库")

        var samples: [Double] = []
        for index in 0..<Self.sampleCount {
            let start = DispatchTime.now()
            store.add(entry("快满的库里再复制一条：第 \(index) 个样本"), timestamp: Date())
            let end = DispatchTime.now()
            samples.append(Double(end.uptimeNanoseconds - start.uptimeNanoseconds) / 1_000_000)
        }
        blocked.signal()
        let median = Self.percentile(samples, 0.5)
        let p95 = Self.percentile(samples, 0.95)
        print(String(format: "CAPTURE_PATH_FULL_ARCHIVE n=%d 库=%d 条 median=%.2fms p95=%.2fms 门槛=%.0fms",
                     samples.count, seeding.entries.count, median, p95, Self.fullArchiveBudgetMilliseconds))
        XCTAssertGreaterThanOrEqual(samples.count, Self.minimumSampleCount)
        XCTAssertLessThanOrEqual(median, Self.fullArchiveBudgetMilliseconds,
                                 "快满的库里一次复制的中位耗时超过门槛 ⇒ 主线程这条链已经是可感成本。"
                                 + "**先分段量是哪一段**（M253 实测：整库快照只占 median 的约 1/5），"
                                 + "不要直接搬 `saveSnapshot` —— 那是把两成的问题解决成全部的问题")
    }

    /// 造库时塞多少条：故意留一点余量，别让降采样/上限把测试形状改掉。
    static let fullArchiveEntries = 480
    /// 前提地板：**独立于** `fullArchiveEntries` 的绝对数（400 = 500 上限的 80%）。
    /// 为什么不能写成 `fullArchiveEntries - 20`：那样两个数就绑在一起动了，
    /// 把造库数量改成 1 时地板也一起缩到 -19，这条断言永远绿 —— 恒真的前提等于没有前提。
    /// 两个数分开之后，"造库变少"与"判据还在测快满的库"是两件事，前者会红。
    static let fullArchivePremiseFloor = 400
    /// 快满的库里一次复制的中位门槛（ms）。**从实测推导**：
    /// 本机 2026-10-14 在 480 条的库上跑四次 `median=2.34 / 2.43 / 2.47 / 2.49ms`、
    /// `p95=2.56 / 2.64 / 3.39 / 5.91ms` ⇒ 取 20ms（最差 median 的 8 倍、最差 p95 的 3.4 倍）。
    /// p95 的散布比 median 大得多（2.6 到 5.9），所以余量按**最差**那一遍算，不按第一次看到的数。
    /// 为什么余量比小库那条紧：这条测的是**随库大小增长的那一份**（同一次跑里小库 median 0.55ms），
    /// 它才是"复制多了会不会开始卡"的先行指标；留太宽就等于不测。
    static let fullArchiveBudgetMilliseconds: Double = 20

    /// 样本数。为什么不是 5：`p95` 在 n=5 上就是最大值（本仓库记过"p99 在 n=2"这一族）。
    static let sampleCount = 40
    /// 地板：判据成立所需的最少样本，**故意不等于** `sampleCount`。
    /// 留 4 倍余量：40 是取值，20 是"少了就不许下结论"的那条线。
    static let minimumSampleCount = 20

    /// 门槛（ms），**从实测推导**而不是抄一个整数：
    /// 本机 2026-10-14 跑 40 个样本得到 `median=0.59ms p95=1.46ms max=3.08ms`
    /// （原文见 `CAPTURE_PATH_BUDGET` 那行日志）。
    /// 取 10ms = 实测中位的 **17 倍**，同时稳稳落在"人能感觉到卡顿"（约 100ms）之下 ——
    /// 前者给 CI 那台更慢的机器留余量（把地板设在本机读数上等于把"这台机器判不了"写成产品缺陷，
    /// R38 那条规矩），后者保证这条判据红了就是**真有可感知的退化**，不是噪声。
    static let budgetMilliseconds: Double = 10
    /// p95 允许比中位门槛高多少倍（4 ⇒ 40ms，仍在可感知线之下）。
    /// 写成显式的第二个数，是为了让"哪个是常态、哪个是尾巴"在判据里可读；
    /// 合成一个数就分不出"常态变慢"与"偶发抖动"了 —— 实测 max=3.08ms 就是那条尾巴，
    /// 它比中位高 5 倍，却没有超任何门槛，这正是"两个数分开"要保护的形状。
    static let p95Multiplier: Double = 4

    // MARK: - 尺子自己的真值表

    /// `percentile` 是上面那条判据的**尺**，所以它自己也要被量一次。
    ///
    /// 为什么不用 `Collection.sorted()` 下标一行写完就宣称它对：那条判据绿不绿全看这个数，
    /// 而"取第几个"这件事在 n 为偶数、n=1、空表三种形状上最容易悄悄偏。
    func testPercentileIsATruthTable() {
        // ① 偶数个：中间两值取平均（线性插值）。这一格钉的是"不许偏到某一侧"：
        //    写成 `sorted[count / 2]` 会报 30，写成 `(count - 1) / 2` 会报 20 ——
        //    两个都能绿一整天，直到某天门槛落在它们之间。
        XCTAssertEqual(Self.percentile([10, 20, 30, 40], 0.5), 25, accuracy: 0.001)
        // ② 奇数个：正好落在中间。
        XCTAssertEqual(Self.percentile([10, 20, 30], 0.5), 20, accuracy: 0.001)
        // ③ 分位取两端。
        XCTAssertEqual(Self.percentile([5, 7, 9], 0), 5, accuracy: 0.001)
        XCTAssertEqual(Self.percentile([5, 7, 9], 1), 9, accuracy: 0.001)
        // ④ 乱序输入不许影响结果。
        XCTAssertEqual(Self.percentile([30, 10, 20], 0.5), 20, accuracy: 0.001)
        // ⑤ 单样本与空表：空表**不许返回 0**（那会把"没采到"读成"耗时为 0"，
        //    与"把没跑写成跑过"同一族），所以返回 NaN 让调用方的比较必然红。
        XCTAssertEqual(Self.percentile([42], 0.95), 42, accuracy: 0.001)
        XCTAssertTrue(Self.percentile([], 0.5).isNaN,
                      "空样本必须报「无从判定」，不许报 0ms")
        // ⑥ 尾巴只有 1 个样本时，p95 仍然被它牵着走：`[1,2,3,4,100]` 的 p95 是 80.8，
        //    而 100 那一个点就占了里面 80% 的量 ⇒ **样本太少时 p95 只是换了个名字的最大值**。
        //    这一格钉的是"为什么 n 要单独断言"（本机实测 n=40 时 p95=1.46ms、max=3.08ms，
        //    两个数分得开，才是可用的分位数）。
        XCTAssertEqual(Self.percentile([1, 2, 3, 4, 100], 0.95), 80.8, accuracy: 0.01)
    }

    // MARK: - 工具

    /// 线性插值分位数（`quantile` ∈ [0,1]）。空表返回 NaN：宁可让比较红，也不许把 0 当读数。
    static func percentile(_ values: [Double], _ quantile: Double) -> Double {
        guard !values.isEmpty else { return .nan }
        let sorted = values.sorted()
        guard sorted.count > 1 else { return sorted[0] }
        let position = min(max(quantile, 0), 1) * Double(sorted.count - 1)
        let lower = Int(position.rounded(.down))
        let upper = min(lower + 1, sorted.count - 1)
        let fraction = position - Double(lower)
        // 0.5 分位在 n=4 上落在位置 1.5 ⇒ 必须插值，两端的下标取法都会偏。
        // 真值表第 ① 格钉的就是这个形状（25，既不是 20 也不是 30）。
        return sorted[lower] * (1 - fraction) + sorted[upper] * fraction
    }

    private func entry(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(text), thumbnail: nil,
                              sourceUTIs: ["public.utf8-plain-text"],
                              sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录")
    }

    /// 这是**轮询步进**而不是「赌一段挂钟」：两处调用都在 `while 条件, Date() < deadline`
    /// 的循环体里。R268 / 318 把这两种形状起成两个名字，就是为了让 `wait_scan.py` 能按符号分它们 ——
    /// 读散文的守卫不算守卫（D-235 那一族）。
    private func pumpRunLoopStep(seconds: TimeInterval) {
        RunLoop.main.run(until: Date().addingTimeInterval(seconds))
    }
}
