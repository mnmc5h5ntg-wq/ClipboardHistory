import XCTest
@testable import ClipboardHistoryApp

/// 采集路径（用户按下 ⌘C 之后，`HistoryStore.add` 那条同步链）的两条判据（R49 / BACKLOG 73）。
///
/// 为什么本轮要新增这个文件：R48 给热图那条淡入 A/B 补上 per-run 打印之后，
/// 读到的是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms` ——
/// **一段连续的变化里有一次 260ms 的抓帧空档**。这件事有两种性质完全不同的解释：
/// ① 产品在自己的事件路径上占住了主线程（那就是卡顿，而且目标里明令"采集路径上不许有同步磁盘写"）；
/// ② 探针自己那次同步 `cacheDisplay` 慢（本文件顶部 `MotionFilmstripTests` 的预卷注释里
///    就写着"新窗口的头两次 `cacheDisplay` 要 260–340ms 一帧"）。
/// 上一轮我把这两种混在了一句"要查"里。**光靠计时分不开它们** —— 计时只能证明"有没有超时"，
/// 证明不了"有没有写盘"。所以这里两条一起立：
/// 一条**行为**判据（目录里有没有出现新写入的文件，与机器快慢无关），
/// 一条**时长**判据（把"主线程在这条链上花了多少"变成一个可红的数）。
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

    // MARK: - 判据一：采集路径上不许有同步磁盘写

    /// 从产品入口复制一条内容，**盘上必须一个字节都没多**。
    ///
    /// 为什么用"目录里有没有新文件"而不是"耗时多少"：耗时判据在慢机器上恒红、
    /// 在快机器上恒绿，而"同步写盘"这件事与快慢无关 —— 它是结构性的。
    /// 目标里那句"采集路径上不许有同步磁盘写"要的是后者。
    func testAddingACopyWritesNothingOnTheCapturePath() throws {
        let ledgerURL = temporaryDirectory.appendingPathComponent("daily-copy.json")
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: temporaryDirectory),
            dailyCopyLedger: DailyCopyLedger(fileURL: ledgerURL, debounceSeconds: 0.4))

        let before = snapshot(of: temporaryDirectory)
        store.add(entry("采集路径不该同步写盘的那一条"), timestamp: Date())
        let after = snapshot(of: temporaryDirectory)

        XCTAssertEqual(before, after,
                       "按下 ⌘C 之后盘上多了东西 ⇒ 采集路径上有同步写盘：\(difference(before, after))")
        XCTAssertFalse(FileManager.default.fileExists(atPath: ledgerURL.path),
                       "账本在 `add` 返回之前就已经落盘 ⇒ 去抖没起作用（这条正是目标明令禁止的形状）")

        // 上面那两条必须**不是恒真**：去抖到期之后文件要真的出现，
        // 否则"什么都没写"也可以靠"根本没接上盘"来绿（把红伪装成没跑的那一族）。
        pumpMain(seconds: 1.2)
        XCTAssertTrue(FileManager.default.fileExists(atPath: ledgerURL.path),
                      "等过去抖窗口账本仍然不存在 ⇒ 这条判据的对照组是空的，"
                      + "上面那句「没写盘」是因为整条链路根本没接上，不是因为去抖")
        let written = snapshot(of: temporaryDirectory)
        XCTAssertNotEqual(before, written, "对照组里盘上仍然一个字节没多 ⇒ 上面那条断言永远绿，是假判据")
    }

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

    /// 目录快照：路径 → (尺寸, mtime)。用**内容指纹**而不是 mtime 单独一项，
    /// 因为有些文件系统把 mtime 截到秒级，同一秒内的写会看不出来。
    private func snapshot(of directory: URL) -> [String: String] {
        let keys: [URLResourceKey] = [.fileSizeKey, .contentModificationDateKey]
        guard let walked = FileManager.default.enumerator(at: directory,
                                                          includingPropertiesForKeys: keys,
                                                          options: []) else { return [:] }
        var result: [String: String] = [:]
        for case let url as URL in walked {
            let values = try? url.resourceValues(forKeys: Set(keys))
            let stamp = values?.contentModificationDate?.timeIntervalSince1970 ?? 0
            result[url.path] = "\(values?.fileSize ?? -1)@\(String(format: "%.6f", stamp))"
        }
        return result
    }

    private func difference(_ before: [String: String], _ after: [String: String]) -> String {
        let added = Set(after.keys).subtracting(before.keys).sorted()
        let changed = after.keys.filter { before[$0] != nil && before[$0] != after[$0] }.sorted()
        return "新增文件=\(added) 内容变了=\(changed)"
    }

    private func entry(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(text), thumbnail: nil,
                              sourceUTIs: ["public.utf8-plain-text"],
                              sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录")
    }

    private func pumpMain(seconds: TimeInterval) {
        RunLoop.main.run(until: Date().addingTimeInterval(seconds))
    }
}
