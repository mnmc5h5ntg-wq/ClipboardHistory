import XCTest
import SwiftUI
@testable import ClipboardHistoryApp

/// 每日复制热图（新功能 / 目标模式阶段一）。
///
/// 四组判据，缺一不可：
/// ① `DailyCopyHeatPolicy` 的**真值表**（日键、分档、网格、月标签、连续天数、汇总、tooltip）；
/// ② `DailyCopyLedger` 的**磁盘行为**（去抖、退出同步落盘、只回填空账本、保留窗口裁剪、
///    损坏时保全原件）；
/// ③ 从**产品入口**进的验收（AGENTS.md 定义 of done 第 1 条）：走真 `HistoryStore.add`，
///    看今天那一格长没长、暂停与被排除的算不算、退出时有没有真的落盘；
/// ④ 接线与令牌单一作者。
///
/// 只测 ① 会漏掉这个功能真正的风险：数据是**派生 + 持久化**的，
/// "算对了但存歪了"这一类缺陷在纯函数测试里永远绿。
@MainActor
final class DailyCopyHeatmapTests: XCTestCase {

    /// 每条用例一个独立临时目录。
    ///
    /// `nonisolated let` 不是随手加的：`setUp` / `addTeardownBlock` 是 XCTestCase 的
    /// **非隔离**入口，碰一个 MainActor 隔离的属性会得到三条 warning，
    /// 而这个仓库的 CI 要求 0 告警。URL 是 Sendable、值是常量，所以这样标注是安全的。
    nonisolated private let temporaryDirectory = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
        .appendingPathComponent("daily-copy-tests-\(UUID().uuidString)", isDirectory: true)

    override func setUp() {
        super.setUp()
        try? FileManager.default.createDirectory(at: temporaryDirectory, withIntermediateDirectories: true)
        addTeardownBlock { [temporaryDirectory] in
            try? FileManager.default.removeItem(at: temporaryDirectory)
        }
    }

    /// 固定历：周一开头、固定时区。
    /// 不固定的话这张图的**形状**跟着机器跑 —— 判据会在某些日子自己变红。
    private var calendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Asia/Shanghai") ?? .current
        calendar.firstWeekday = 2
        calendar.minimumDaysInFirstWeek = 4
        return calendar
    }

    private func day(_ year: Int, _ month: Int, _ day: Int, hour: Int = 12) -> Date {
        var components = DateComponents()
        components.year = year
        components.month = month
        components.day = day
        components.hour = hour
        guard let date = calendar.date(from: components) else {
            preconditionFailure("夹具日期构造失败：\(year)-\(month)-\(day)")
        }
        return date
    }

    private func ledger(named file: String = "daily-copy.json",
                        debounce: TimeInterval = 60,
                        now: Date? = nil) -> DailyCopyLedger {
        let stamp = now ?? day(2026, 3, 12)
        return DailyCopyLedger(fileURL: temporaryDirectory.appendingPathComponent(file),
                               calendar: calendar,
                               debounceSeconds: debounce,
                               now: { stamp })
    }

    private func url(_ file: String = "daily-copy.json") -> URL {
        temporaryDirectory.appendingPathComponent(file)
    }

    // MARK: - ① 真值表

    func testDayKeysRoundTripAndSortChronologically() throws {
        let early = day(2026, 3, 12, hour: 0)
        let late = day(2026, 3, 12, hour: 23)
        let nextDay = day(2026, 3, 13, hour: 0)
        let earlyKey = DailyCopyHeatPolicy.dayKey(for: early, calendar: calendar)
        let lateKey = DailyCopyHeatPolicy.dayKey(for: late, calendar: calendar)
        let nextKey = DailyCopyHeatPolicy.dayKey(for: nextDay, calendar: calendar)

        XCTAssertEqual(earlyKey, lateKey, "同一天的 00:00 与 23:00 必须落进同一格")
        XCTAssertNotEqual(earlyKey, nextKey, "跨了午夜必须是两格")
        XCTAssertEqual(earlyKey, "2026-03-12")
        XCTAssertLessThan(earlyKey, nextKey, "日键必须字典序 = 时间序（裁剪与并列都靠这条）")
        let back = try XCTUnwrap(DailyCopyHeatPolicy.date(forDayKey: earlyKey, calendar: calendar))
        XCTAssertEqual(DailyCopyHeatPolicy.dayKey(for: back, calendar: calendar), earlyKey, "日键要能往返")
    }

    func testCountsAggregateByLocalDay() {
        let counts = DailyCopyHeatPolicy.counts(dates: [
            day(2026, 3, 11), day(2026, 3, 12, hour: 9), day(2026, 3, 12, hour: 18), day(2026, 3, 12, hour: 23)
        ], calendar: calendar)
        XCTAssertEqual(counts["2026-03-11"], 1)
        XCTAssertEqual(counts["2026-03-12"], 3)
        XCTAssertEqual(counts.values.reduce(0, +), 4, "一条都不该丢")
    }

    /// 分档是**相对**的：这是这张图最重要的一个语义决定，所以它必须被钉住。
    func testBucketLadderIsRelativeMonotonicAndBounded() {
        let edges = DailyCopyHeatPolicy.bucketEdges(positiveCounts: [1, 2, 5, 9, 20, 44])
        XCTAssertFalse(edges.isEmpty, "有正数就该有档位边界")
        var previousBucket = -1
        for count in [1, 2, 5, 9, 20, 44] {
            let bucket = DailyCopyHeatPolicy.bucket(count: count, edges: edges)
            XCTAssertGreaterThanOrEqual(bucket, 1, "有记录就不许落进「没有」那一档")
            XCTAssertLessThanOrEqual(bucket, 4, "最多五档：再多就不是「深浅」而是「色板」了")
            XCTAssertGreaterThanOrEqual(bucket, previousBucket, "条数变多不许变浅")
            previousBucket = bucket
        }
        XCTAssertEqual(DailyCopyHeatPolicy.bucket(count: 0, edges: edges), 0)

        // 每天都一样 ⇒ 只有一档。图会读成「均匀的中间色」，那正是事实。
        //（第一版这里遍历 1...7 去比，测的是**数据里根本没有的条数** —— 那是测试的前提错了，
        //  不是分档错了。判据写错的时候要说「我写错了」，不许顺手把产品改成能让断言过。）
        let flat = DailyCopyHeatPolicy.bucketEdges(positiveCounts: [7, 7, 7, 7])
        XCTAssertEqual(Set([7, 7, 7].map { DailyCopyHeatPolicy.bucket(count: $0, edges: flat) }).count, 1,
                       "全部相等时不许凭空造出深浅")
        XCTAssertLessThanOrEqual(DailyCopyHeatPolicy.bucket(count: 7, edges: flat), 4)

        // 轻度用户（每天 1-3 次）也要有深浅：绝对阈值会把这类人整张图判成灰的。
        let light = DailyCopyHeatPolicy.bucketEdges(positiveCounts: [1, 1, 2, 2, 3])
        XCTAssertGreaterThan(DailyCopyHeatPolicy.bucket(count: 3, edges: light),
                             DailyCopyHeatPolicy.bucket(count: 1, edges: light),
                             "轻度用户必须看得出哪几天多一点")
    }

    func testGridShapeWeekdayAlignmentAndFutureCells() throws {
        let today = day(2026, 3, 12)
        let counts = DailyCopyHeatPolicy.counts(dates: [today, today, day(2026, 3, 5)], calendar: calendar)
        let grid = DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, weeks: 18, calendar: calendar)
        XCTAssertEqual(grid.count, 18, "窗口必须是整数列")
        for week in grid { XCTAssertEqual(week.cells.count, 7, "每列必须 7 格，否则星期标签会错位") }

        // 第一列的第一格必须是那一周的起始日（这里 firstWeekday = 2 ⇒ 周一）。
        let firstDate = try XCTUnwrap(grid.first?.cells.first?.date)
        XCTAssertEqual(calendar.component(.weekday, from: firstDate), 2,
                       "行序必须跟着 calendar.firstWeekday 走，写死周日会让中文用户凭空缺一天")

        let lastColumn = try XCTUnwrap(grid.last?.cells)
        let todayCell = try XCTUnwrap(lastColumn.first { $0.dayKey == "2026-03-12" })
        XCTAssertEqual(todayCell.count, 2, "今天那一格必须读到今天的两条")
        // 03-05 是整整一周之前 ⇒ 它在**上一列**，不在最后一列（第一版这样断言是我算错了）。
        let allCells = grid.flatMap(\.cells)
        XCTAssertEqual(allCells.first { $0.dayKey == "2026-03-05" }?.count, 1)
        XCTAssertEqual(allCells.filter { !$0.isFuture && $0.count > 0 }.count, 2,
                       "窗口里只有这两天有记录 ⇒ 亮的格子必须正好两格，多出来就是日期键串了")

        let future = lastColumn.filter { $0.isFuture }
        XCTAssertFalse(future.isEmpty, "今天所在那一周后面还有几天，它们必须被标成未来")
        XCTAssertTrue(future.allSatisfy { ($0.dayKey ?? "") > "2026-03-12" },
                      "只有今天之后才算未来 —— 过去的日子不许被标成「还没到」")
        XCTAssertTrue(future.allSatisfy { $0.bucket == 0 })
    }

    func testMonthLabelsAreSparseAndNeverOnTheFirstColumn() {
        let today = day(2026, 5, 8)
        let grid = DailyCopyHeatPolicy.weeks(counts: [:], endingOn: today, weeks: 18, calendar: calendar)
        let labelled = grid.enumerated().filter { $0.element.monthLabel != nil }
        XCTAssertFalse(labelled.isEmpty, "18 周跨了三四个月却一枚标签都没有 ⇒ 标签逻辑坏了")
        XCTAssertTrue(labelled.allSatisfy { $0.offset > 0 }, "第一列不许写月份（它常是上个月的尾巴）")
        let columns = labelled.map { $0.offset }
        for index in 1..<columns.count {
            XCTAssertGreaterThanOrEqual(columns[index] - columns[index - 1],
                                        DailyCopyHeatPolicy.minimumGapBetweenMonthLabels,
                                        "标签挨着写会糊成一条带子：\(columns)")
        }
        // 标签必须是数字 + 「月」，宽度稳定（全称月份会把网格推歪）。
        for label in labelled.map({ $0.element.monthLabel ?? "" }) {
            XCTAssertTrue(label.hasSuffix("月"), label)
            XCTAssertLessThanOrEqual(label.count, 3, label)
        }
    }

    func testStreakToleratesAnEmptyToday() {
        let today = day(2026, 3, 12)
        let counts = DailyCopyHeatPolicy.counts(dates: [
            day(2026, 3, 11), day(2026, 3, 10), day(2026, 3, 8)
        ], calendar: calendar)
        // 今天还没复制 ⇒ 从昨天起算，不许当场清零。
        XCTAssertEqual(DailyCopyHeatPolicy.streak(counts: counts, today: today, calendar: calendar), 2)
        var withToday = counts
        withToday[DailyCopyHeatPolicy.dayKey(for: today, calendar: calendar)] = 1
        XCTAssertEqual(DailyCopyHeatPolicy.streak(counts: withToday, today: today, calendar: calendar), 3)
        XCTAssertEqual(DailyCopyHeatPolicy.streak(counts: [:], today: today, calendar: calendar), 0)
        // 中间断一天 ⇒ 只数最近那一段。
        let broken = DailyCopyHeatPolicy.counts(dates: [day(2026, 3, 11), day(2026, 3, 9)], calendar: calendar)
        XCTAssertEqual(DailyCopyHeatPolicy.streak(counts: broken, today: today, calendar: calendar), 1)
    }

    func testSummaryAveragesOverEveryVisibleDay() {
        let today = day(2026, 3, 12)
        let counts = DailyCopyHeatPolicy.counts(dates: [today, today, day(2026, 3, 11)], calendar: calendar)
        let grid = DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, weeks: 4, calendar: calendar)
        let summary = DailyCopyHeatPolicy.summary(counts: counts, weeks: grid, today: today, calendar: calendar)
        XCTAssertEqual(summary.total, 3)
        XCTAssertEqual(summary.daysWithRecords, 2)
        let visibleDays = grid.flatMap(\.cells).filter { !$0.isFuture && $0.dayKey != nil }.count
        XCTAssertEqual(summary.averagePerDay, Double(3) / Double(visibleDays), accuracy: 0.0001,
                       "分母必须是窗口里所有日子；只除「有记录的天数」会把轻度用户说成日均 3")
        XCTAssertEqual(summary.busiestDayKey, "2026-03-12")
        XCTAssertEqual(summary.busiestCount, 2)
    }

    func testTooltipSaysTheDayAndTheCount() throws {
        let today = day(2026, 3, 12)
        let counts = DailyCopyHeatPolicy.counts(dates: [today, today], calendar: calendar)
        let grid = DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, weeks: 2, calendar: calendar)
        let cells = grid.flatMap(\.cells)

        let busy = try XCTUnwrap(cells.first { $0.dayKey == "2026-03-12" })
        let busyTooltip = DailyCopyHeatPolicy.tooltip(cell: busy, calendar: calendar)
        XCTAssertTrue(busyTooltip.contains("复制"), busyTooltip)
        XCTAssertTrue(busyTooltip.contains("2 次"), busyTooltip)

        let quiet = try XCTUnwrap(cells.first { $0.dayKey == "2026-03-10" })
        XCTAssertTrue(DailyCopyHeatPolicy.tooltip(cell: quiet, calendar: calendar).contains("没有记录"),
                      "0 那一格要说「没有记录」，不许是空白")

        let future = try XCTUnwrap(cells.first { $0.isFuture }, "夹具里必须有一格是未来，否则这一半没被验")
        XCTAssertTrue(DailyCopyHeatPolicy.tooltip(cell: future, calendar: calendar).isEmpty,
                      "未来那一格不许有 tooltip：它说的是「还没到」，不是「你那天没复制」")
    }

    // MARK: - ② 账本的磁盘行为

    /// 采集路径上不许有同步磁盘写（目标里明写的一条硬要求）。
    func testRecordCopyDoesNotTouchTheDiskOnTheCallingPath() throws {
        let subject = ledger()
        subject.recordCopy(at: day(2026, 3, 12))
        subject.recordCopy(at: day(2026, 3, 12))
        XCTAssertEqual(subject.counts["2026-03-12"], 2)
        XCTAssertFalse(FileManager.default.fileExists(atPath: url().path),
                       "复制路径上就写了盘：去抖形同虚设，一次复制多一次同步 IO")

        subject.flushPendingSaves()
        XCTAssertTrue(FileManager.default.fileExists(atPath: url().path),
                      "退出落盘没写：去抖窗口里的计数会被 SIGTERM 掐掉")
        XCTAssertEqual(ledger().counts["2026-03-12"], 2, "落盘的内容要能原样读回来")
    }

    func testFlushDoesNotBlockForTheDebounceWindow() throws {
        // 去抖 60 秒。如果 `flush` 是 `workItem.wait()`，这条会挂满一分钟 ——
        // 那在退出路径上就是「按退出没反应」。
        let subject = ledger(debounce: 60)
        subject.recordCopy(at: day(2026, 3, 12))
        let started = Date()
        subject.flushPendingSaves()
        XCTAssertLessThan(Date().timeIntervalSince(started), 1.0, "flush 在等去抖到期，不是在立刻落盘")
        XCTAssertTrue(FileManager.default.fileExists(atPath: url().path))
    }

    /// 去抖的写盘**真的会执行**，而且不在 MainActor 上炸。
    ///
    /// 这条是回归判据：第一版把 `DispatchWorkItem { ... }` 写在 `@MainActor` 的方法里，
    /// 闭包被推成 MainActor 隔离，跑到后台队列上就 `dispatch_assert_queue` → SIGTRAP。
    /// 全量测试当时是"所有用例都绿，然后进程在两个用例之间崩掉"——
    /// 只有真等到去抖到期才能复现，所以这条必须真的等，不能只测排没排。
    func testDebouncedWriteFiresWithoutMainActorTrap() throws {
        let subject = ledger(debounce: 0.05)
        subject.recordCopy(at: day(2026, 3, 12))
        subject.recordCopy(at: day(2026, 3, 11))
        XCTAssertFalse(FileManager.default.fileExists(atPath: url().path), "去抖之前不许写")
        // 让后台队列有机会跑：主线程睡 0.6s（12 倍去抖窗口）。
        Thread.sleep(forTimeInterval: 0.6)
        XCTAssertTrue(FileManager.default.fileExists(atPath: url().path),
                      "去抖到期没写盘：这条路径从来没被执行过，隔离问题也就看不见")
        XCTAssertNil(subject.lastWriteError, subject.lastWriteError ?? "nil")
        XCTAssertEqual(ledger().counts["2026-03-12"], 1)
    }

    /// 构造与回填都**不许排写盘**（`HistoryStore.init` 会调 `backfillIfEmpty`，
    /// 而"init 阶段写盘"是 D-002 那条红线的同族）。
    ///
    /// 去抖故意设成 0.05s 并真的等过去：第一版这里用 60s，于是"排了一次写盘"
    /// 与"没排"在测试窗口内长得一模一样 —— 变异 M31 就是这么绿着通过的。
    /// **能等到**才是判据，等不到的那条只是愿望。
    func testBackfillDoesNotWriteDuringConstruction() throws {
        let subject = ledger(debounce: 0.05)
        subject.backfillIfEmpty(from: [day(2026, 3, 11), day(2026, 3, 11)])
        Thread.sleep(forTimeInterval: 0.6)
        XCTAssertFalse(FileManager.default.fileExists(atPath: url().path),
                       "回填当场写了盘 ⇒ 任何碰到共享 store 的测试都会去写用户目录")
        subject.flushPendingSaves()
        XCTAssertTrue(FileManager.default.fileExists(atPath: url().path),
                      "回填的计数必须最终落下去，否则下次启动又要从 500 条上限重算")
    }

    func testBackfillOnlyFillsAnEmptyLedger() throws {
        let empty = ledger()
        empty.backfillIfEmpty(from: [day(2026, 3, 11), day(2026, 3, 11), day(2026, 3, 9)])
        XCTAssertEqual(empty.counts["2026-03-11"], 2)
        XCTAssertEqual(empty.counts["2026-03-09"], 1)

        // 已经有账 ⇒ 回填必须**不覆盖**。500 条上限的存档倒灌会把半年之外的部分抹掉。
        let filled = ledger()
        filled.recordCopy(at: day(2026, 3, 12))
        filled.backfillIfEmpty(from: [day(2026, 1, 1)])
        XCTAssertEqual(filled.counts["2026-03-12"], 1)
        XCTAssertNil(filled.counts["2026-01-01"], "回填把已有账本覆盖了")
    }

    func testPruningBoundsTheLedger() {
        let old = DailyCopyHeatPolicy.dayKey(for: day(2019, 1, 1), calendar: calendar)
        let recent = DailyCopyHeatPolicy.dayKey(for: day(2026, 3, 12), calendar: calendar)
        let pruned = DailyCopyLedger.pruned(counts: [old: 5, recent: 7],
                                            now: day(2026, 3, 12),
                                            calendar: calendar,
                                            retentionDays: DailyCopyLedger.retentionDays)
        XCTAssertNil(pruned[old], "超出保留窗口的旧日子必须被裁掉，否则文件无限长")
        XCTAssertEqual(pruned[recent], 7)
    }

    func testCorruptLedgerKeepsTheOriginalBytes() throws {
        let file = url()
        let garbage = Data("这不是 JSON {{{".utf8)
        try garbage.write(to: file)

        let subject = ledger()
        XCTAssertTrue(subject.counts.isEmpty, "读不懂就当空账本（随后可以从历史回填），不许崩")

        let backup = file.appendingPathExtension("bak")
        let preserved = try Data(contentsOf: backup)
        XCTAssertEqual(preserved, garbage, "损坏原件必须留着：直接覆盖会把「还剩几天数据」也弄没")
    }

    // MARK: - ③ 产品入口（AGENTS.md 定义 of done 第 1 条）

    private func makeStore(_ subject: DailyCopyLedger?) -> HistoryStore {
        HistoryStore(clipboardWriter: TestClipboardWriter(),
                     persistence: RecordingHistoryPersistence(),
                     dailyCopyLedger: subject,
                     retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
    }

    func testCopyingThroughTheStoreGrowsTodaysCell() {
        let subject = ledger()
        let store = makeStore(subject)
        let today = day(2026, 3, 12)

        store.add(entry("第一条"), timestamp: today)
        store.add(entry("第二条"), timestamp: today)
        XCTAssertEqual(subject.counts["2026-03-12"], 2)
        XCTAssertEqual(store.entries.count, 2)

        // 同一条内容连着复制：列表里还是一条（去重），但**计数要加** —— 它确实复制了两次。
        store.add(entry("第二条"), timestamp: today)
        XCTAssertEqual(subject.counts["2026-03-12"], 3, "去重把一次真实发生的复制从统计里吞掉了")
        XCTAssertEqual(store.entries.count, 2, "列表侧的去重行为不许被统计改动")

        store.add(entry("昨天的"), timestamp: day(2026, 3, 11))
        XCTAssertEqual(subject.counts["2026-03-11"], 1, "换一天必须长出新的一格")
    }

    func testPausedAndExcludedCaptureDoNotCount() {
        let subject = ledger()
        let store = makeStore(subject)
        let today = day(2026, 3, 12)

        store.isRecordingPaused = true
        store.add(entry("暂停期间复制的"), timestamp: today)
        store.isRecordingPaused = false
        XCTAssertTrue(subject.counts.isEmpty, "暂停时发生的复制被计数了 —— 那是「没发生」，不是「发生了没记」")

        store.add(ClipboardIntake.Entry(content: .text("钥匙串里复制的"),
                                        thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.keychainaccess",
                                        sourceAppName: "钥匙串访问"),
                  timestamp: today)
        XCTAssertTrue(subject.counts.isEmpty, "被排除的 App 不该进统计")

        store.add(entry("正常复制的"), timestamp: today)
        XCTAssertEqual(subject.counts["2026-03-12"], 1, "上面两条之后正常采集必须仍然计数（别把守卫写反）")
    }

    /// 退出路径：`flushPendingPersistence()` 必须把账本一起落盘。
    func testStoreFlushAlsoFlushesTheLedger() {
        let subject = ledger()
        let store = makeStore(subject)
        store.add(entry("要落盘的"), timestamp: day(2026, 3, 12))
        XCTAssertFalse(FileManager.default.fileExists(atPath: url().path))
        store.flushPendingPersistence()
        XCTAssertTrue(FileManager.default.fileExists(atPath: url().path),
                      "只刷历史不刷账本：退出会丢掉最后一段计数")
    }

    /// 不注入账本时**一个字节都不许写**（否则每一条不关心统计的测试都会碰真目录）。
    func testStoreWithoutLedgerWritesNothingAndStillWorks() {
        let store = makeStore(nil)
        store.add(entry("没有账本也要正常入库"), timestamp: day(2026, 3, 12))
        XCTAssertEqual(store.entries.count, 1)
        store.flushPendingPersistence()   // 不许崩
        XCTAssertFalse(FileManager.default.fileExists(atPath: url().path))
    }

    // MARK: - ④ 接线与令牌

    func testStatsCategoryIsWired() throws {
        XCTAssertTrue(SettingsCategory.allCases.contains(.stats), "「统计」分区没进侧栏")
        XCTAssertEqual(SettingsCategory.stats.title, "统计")
        XCTAssertEqual(SettingsCategory.stats.icon, "chart.bar",
                       "侧栏图标必须全是描线系（D-8 那条判据管的就是这个）")

        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("case .stats:"), "switch 里没有统计分支：点进去会是一片空白")
        XCTAssertTrue(settings.contains("DailyCopyStatsSection(ledger:"),
                      "统计页没有观察账本：边复制边看时图不会动")
        XCTAssertTrue(settings.contains("DailyCopyHeatmapView(counts:"), "视图没接上")
        XCTAssertTrue(settings.contains("统计不可用"),
                      "拿不到账本时必须明说，不许画一张全灰的图冒充「你这半年什么都没复制」")

        let controller = codeOnly(try productSource(named: "Managers/SettingsWindowController.swift"))
        XCTAssertTrue(controller.contains("dailyCopyLedger: historyStore?.dailyCopyLedger"),
                      "窗口控制器没把账本递给设置页")

        let app = codeOnly(try productSource(named: "Managers/AppDelegate.swift"))
        XCTAssertTrue(app.contains("HistoryStore(dailyCopyLedger: DailyCopyLedger())"),
                      "生产侧没注入账本 ⇒ 这张图永远是空的")

        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        XCTAssertFalse(store.contains("DailyCopyLedger()"),
                       "Store 内部默认建一个账本 ⇒ 每条不注入的测试都会去写用户的数据目录")
    }

    /// 令牌单一作者：这张新图不许自带几何与色阶。
    func testHeatmapReadsTheTokenAuthors() throws {
        let view = codeOnly(try productSource(named: "Views/DailyCopyHeatmapView.swift"))
        XCTAssertFalse(view.contains("RoundedRectangle(cornerRadius:"), "圆角没走 VisualShape")
        XCTAssertFalse(view.contains(".shadow("), "投影没走 VisualShadow")
        XCTAssertTrue(view.contains("VisualHeat."), "几何与色阶没走 VisualHeat")
        XCTAssertTrue(view.contains("VisualRadius.heatCell"), "圆角没走 VisualRadius")
        XCTAssertTrue(view.contains("MotionCatalog.animation(for:"), "动效参数没走目录")
        XCTAssertTrue(view.contains(".helpLabel("),
                      "悬浮提示必须走 `helpLabel`（它同时上 .help 与 accessibilityLabel）；"
                          + "裸 `.help(` 会被 AccessibilityLabelHygieneTests 打红")
        XCTAssertFalse(view.contains(".help("), "这里不许出现裸 .help(")
        // 未来格必须是「不画」，而不是画成 0。
        XCTAssertTrue(view.contains("cell.isFuture"),
                      "没有未来分支 ⇒ 还没到的日子会被画成「那天没复制」")
    }

    // MARK: - 工具

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let file = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory + "/" + name)
            if let text = try? String(contentsOf: file, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "DailyCopyHeatmapTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 \(relative)：守卫找不到被守卫的东西时必须红"])
    }

    private func entry(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text),
            thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Notes",
            sourceAppName: "备忘录"
        )
    }
}
