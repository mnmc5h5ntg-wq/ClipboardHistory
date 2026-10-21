import Combine
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

    // MARK: - R10：写盘失败必须**自己**上屏（BACKLOG 14）

    /// 阶段一那条 `lastWriteError` 是"计算属性读加锁盒子"：值不丢，但**没有东西为它发布** ⇒
    /// 写盘失败之后如果用户不再复制，那一行永远不上屏；重启之后永远是 `nil`。
    /// 也就是"防静默失败"只做成了一半。这条判据问的正是没做完的那一半：
    /// **不再复制第二次**，失败也要看得见，而且要有发布出去的那一下。
    func testWriteFailureBecomesVisibleWithoutAnotherCopy() throws {
        let directory = temporaryDirectory
        let blocker = directory.appendingPathComponent("blocked")
        FileManager.default.createFile(atPath: blocker.path, contents: Data())
        // `blocked` 是个**文件** ⇒ 它的下面建不出目录 ⇒ 写盘必失败（不需要权限技巧，跨机器成立）
        let ledger = DailyCopyLedger(fileURL: blocker.appendingPathComponent("daily-copy.json"),
                                     debounceSeconds: 0.05)
        XCTAssertNil(ledger.lastWriteError)

        var publishes = 0
        let sink = ledger.objectWillChange.sink { _ in publishes += 1 }
        ledger.recordCopy(at: ledger.today)
        let afterCopy = publishes

        // **等条件，不等挂钟**（R267 / runner run 39557244740 现读）：这一格原来只
        // `pumpMain(seconds: 0.8)`，而产品的写盘在 `saveQueue(qos: .utility)` 上、
        // 可见性回主线程还要再等 `debounce + grace` —— 本机 0.8s 够，runner 负载高时
        // .utility 队列被压后 ⇒ 两条断言同时红（`lastWriteError=nil`、`publishes=1`），
        // 红的是"还没到时候"，不是"产品没做"。固定睡眠是这种假红的温床（281/304 同一族）。
        // 现在等到条件成立或 10s 上限；**断言一条没放宽**，超时仍然红，而且把等了多久打出来。
        let started = Date()
        let deadline = 10.0
        while Date().timeIntervalSince(started) < deadline
                && (ledger.lastWriteError == nil || publishes <= afterCopy) {
            RunLoop.main.run(mode: .default, before: Date().addingTimeInterval(0.05))
        }
        let waitedMs = Int(Date().timeIntervalSince(started) * 1000)
        CaptureReadings.emit("LEDGER_WRITE_ERROR_VISIBLE waited_ms=" + String(waitedMs)
                             + " publishes=" + String(publishes) + " 复制后基线=" + String(afterCopy)
                             + " 有错误=" + String(ledger.lastWriteError != nil)
                             + " 上限_ms=10000")

        XCTAssertNotNil(ledger.lastWriteError,
                        "写盘失败没有上屏 ⇒ 又回到「只防了一半」的那版（等了 " + String(waitedMs)
                        + " ms，上限 10000 ms）")
        XCTAssertGreaterThan(publishes, afterCopy,
                             "值变了但一次也没发布 ⇒ 观察它的设置页不会重绘，用户看不到这一行（等了 "
                             + String(waitedMs) + " ms）")
        sink.cancel()   // 订阅必须活过 pump：提前解订阅会让上面那条只能靠运气绿
    }

    /// 退出路径上没有"下一次去抖到期"了，所以 flush 必须自己同步一次。
    func testFlushReportsAFailedWrite() throws {
        let directory = temporaryDirectory
        let blocker = directory.appendingPathComponent("blocked2")
        FileManager.default.createFile(atPath: blocker.path, contents: Data())
        // 去抖设得比测试还长 ⇒ 这一条**只能**靠 flush 自己同步，不可能被去抖项顺手做到
        let ledger = DailyCopyLedger(fileURL: blocker.appendingPathComponent("daily-copy.json"),
                                     debounceSeconds: 60)
        ledger.recordCopy(at: ledger.today)
        XCTAssertNil(ledger.lastWriteError, "还没到截止点就报失败 ⇒ 那是假警报")
        ledger.flushPendingSaves()
        XCTAssertNotNil(ledger.lastWriteError,
                        "flush 写失败之后仍然一言不发 ⇒ 退出时丢计数这件事没人知道")
    }

    /// 反向的那一半：**没失败的时候不许说话**。
    /// `@Published` 是"每次赋值都发"，不看值相不相等 ⇒ 少了那句比较，
    /// 每复制一条都会让设置页为一条并不存在的错误重排一次（比静默更吵的那种坏法）。
    func testASuccessfulWriteDoesNotRepublish() throws {
        let ledger = DailyCopyLedger(fileURL: temporaryDirectory.appendingPathComponent("ok/daily-copy.json"),
                                     debounceSeconds: 0.05)
        var publishes = 0
        let sink = ledger.objectWillChange.sink { _ in publishes += 1 }
        ledger.recordCopy(at: ledger.today)
        let afterCopy = publishes
        pumpMain(seconds: 0.8)
        XCTAssertNil(ledger.lastWriteError)
        XCTAssertEqual(publishes, afterCopy,
                       "写成功也发了一次变更 ⇒ 那个「只在值变了才同步」的比较被拿掉了")
        sink.cancel()
    }

    /// 恢复也要说话：路径变可写之后下一次成功写盘要把那行撤掉。
    /// 不测这一半的话，"曾经失败过"会变成一条永久横幅，而那比静默失败更吵。
    func testASuccessfulWriteClearsTheFailure() throws {
        let directory = temporaryDirectory
        let gate = directory.appendingPathComponent("gate")
        FileManager.default.createFile(atPath: gate.path, contents: Data())
        let ledger = DailyCopyLedger(fileURL: gate.appendingPathComponent("sub/daily-copy.json"),
                                     debounceSeconds: 0.05)
        ledger.recordCopy(at: ledger.today)
        pumpMain(seconds: 0.8)
        XCTAssertNotNil(ledger.lastWriteError, "前提：先让它真的失败一次")

        try FileManager.default.removeItem(at: gate)   // 障碍清掉 ⇒ 同一条路径现在写得进去
        ledger.recordCopy(at: ledger.today)
        pumpMain(seconds: 0.8)
        XCTAssertNil(ledger.lastWriteError, "已经恢复还在报失败 ⇒ 这条提示从此变成噪声")
    }

    /// 主队列的"看一眼"要靠 runloop 跑，`Thread.sleep` 会**堵死**主线程 ⇒ 那一格永远不响。
    /// 这条 helper 本身就是判据的一部分：用错等待方式的测试会绿着什么都没测到。
    private func pumpMain(seconds: TimeInterval) {
        let deadline = Date().addingTimeInterval(seconds)
        while Date() < deadline {
            RunLoop.main.run(mode: .default, before: deadline)
        }
    }

    // MARK: - R9：动效必须"被供电"，不许只是声明

    /// 阶段一自检抓到的两条，都在这里钉住（U-30 缺陷 2 + BACKLOG 15）：
    /// ① 描边与页脚由同一个 `hovered` 驱动，而事务当时挂在**页脚的字符串**上 ——
    ///    字符串不可插值，所以那条 `.animation` 一次也没演过，而真正可插值的描边在事务外；
    /// ② 空态 ↔ 网格整块交换没有过渡。
    ///
    /// 写法上的要求（R5 A7 / R7 M15 / R8 M21 三课）：**按函数体取区域**，
    /// 整文件 `contains` 会被同族的另一处命中白拿 —— 这个文件现在有 4 处 `.animation(`
    /// 与 3 处 `.transition(`，任何"文件里有 withAnimation 就算过"的写法都没有判别力。
    func testHeatmapMotionIsDrivenNotJustClaimed() throws {
        let view = codeOnly(try productSource(named: "Views/DailyCopyHeatmapView.swift"))

        // ① 悬停：变更点自己开事务。
        //    R45 之后"格子怎么画"搬进了 `DailyCopyHeatmapCell`，所以这里读**两个**区域：
        //    事务仍在调用点（`cellView` 把 `hovered` 折成 `isHovered` 时开），
        //    而按值动画跟着画法走。守卫跟着代码搬，不是把守卫放宽 ——
        //    两条断言一条都没删，只是各自指回自己现在的主人。
        let cell = region(in: view, named: "func cellView")
        XCTAssertTrue(cell.contains("withAnimation(MotionCatalog.animation(for: .hover))"),
                      "描边是 `hovered` 驱动的透明度，可插值；变更点不开事务 ⇒ 它硬生硬灭（阶段一那条假动画的成因）")
        let cellDrawing = region(in: view, named: "struct DailyCopyHeatmapCell")
        XCTAssertTrue(cellDrawing.contains("value: cell.bucket)"),
                      "当天那格的深浅必须由 bucket 驱动：没有这一条，复制一下之后图上是硬切")
        XCTAssertFalse(cellDrawing.contains("value: cell.count)"),
                       "键不许用 count：同一档内 12→13 次画面**不该**动，拿 count 当键会让每次复制都白起一次事务")

        // ② 页脚：那条"声明了但空转"的动画必须已经撤掉，而不是被挪到别处。
        let footer = region(in: view, named: "var footer")
        XCTAssertFalse(footer.contains(".animation("),
                      "页脚换的是字符串，不可插值 ⇒ 这里挂 `.animation` 就是那条永远不演的假声明（撤掉它并写明理由，别留着当装饰）")
        XCTAssertFalse(view.contains("value: hovered"),
                       "以 `hovered` 为键的按值动画：字符串换了它也不会插值，留着只会让人以为这里有动效")

        // ③ 空态 ↔ 网格：两臂都要有过渡，且容器上要有能驱动它们的键。
        let body = region(in: view, named: "var body")
        XCTAssertEqual(transitionCount(in: body), 2,
                       "空态臂与网格块臂必须**两臂都有**过渡：只挂一臂是 R5 的 A2 那一族（'声明了但只演一半'）")
        XCTAssertTrue(body.contains("value: counts.isEmpty)"),
                      "两臂的过渡没有按值驱动 ⇒ 第一条复制那一下仍然是硬换")
        // 汇总行是随 `counts.isEmpty` 一起出现/消失的那一条，它也得在事务里。
        XCTAssertEqual(transitionCount(in: region(in: view, named: "var header")), 1,
                       "有记录之后汇总行是硬蹦出来的：它和空态的消失是同一件事，该一起淡")
    }

    /// 汇总那一行的**可见性**是决定，不是排版：空屏不许同时说"共 0 次"和"还没有记录"。
    func testHeatmapSummaryLineTruthTable() {
        let summary = DailyCopyHeatPolicy.Summary(total: 1322, daysWithRecords: 126,
                                                  averagePerDay: 7.4, busiestDayKey: "2025-11-17",
                                                  busiestCount: 18, currentStreak: 126)
        XCTAssertNil(DailyCopyHeatPolicy.summaryLine(for: summary, hasRecords: false),
                     "没记录时这一行必须整条不出现 —— 零不是信息，'还没开始记'才是")
        guard let line = DailyCopyHeatPolicy.summaryLine(for: summary, hasRecords: true) else {
            return XCTFail("有记录时这一行必须出现")
        }
        XCTAssertTrue(line.contains("26 周"), "窗口周数要来自 `defaultWindowWeeks`，写死会让改窗口时漏改")
        XCTAssertTrue(line.contains("1322 次") && line.contains("7.4 次") && line.contains("126 天"),
                      "三个数少一个，这句话就退化成装饰")
    }

    /// 决定归作者：文案与可见性都在策略里，视图只负责画。
    /// 反过来也钉住 —— 视图里不许再拼一份这句话，否则改策略时视图那份会静默留在原地。
    func testHeatmapSummaryDecisionIsAuthoredByThePolicy() throws {
        let view = codeOnly(try productSource(named: "Views/DailyCopyHeatmapView.swift"))
        XCTAssertTrue(view.contains("DailyCopyHeatPolicy.summaryLine("),
                      "视图没走策略 ⇒ 这条决定回到了排版里，真值表管不到它")
        XCTAssertFalse(view.contains("周共"), "视图里不许再拼汇总文案（作者是 `DailyCopyHeatPolicy.summaryLine`）")
    }

    // MARK: - 工具

    /// 取某个成员（`func` 或 `var`）的**函数体**：从声明行开始，按花括号配平到闭合。
    /// 为什么不用"行号区间"或"到下一个 MARK 为止"：那两种写法都会随排版漂移，
    /// 而守卫一旦随排版漂移，它就变成了"今天恰好还在管"的那种东西。
    ///
    /// 取不到 ⇒ **当场 XCTFail** 并返回一个不可能匹配任何 needle 的哨兵串。
    /// 这里不能"安静返回空串"：空串会让下面所有 `XCTAssertFalse(contains:)` 全绿，
    /// 于是"把那个成员删了"被读成"修好了" —— 把红伪装成没跑，仓库里记过不止一次。
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

    private func transitionCount(in region: String) -> Int {
        region.components(separatedBy: "\n").filter { $0.contains(".transition(") }.count
    }

    /// 区域助手自己是**尺子**，所以它自己也要被量一次：
    /// 取到了不许把整份文件当区域（那等于把"整文件 contains"的弱点原封不动搬进来），
    /// 也取不到时不许安静（上一段的理由）。
    func testHeatmapRegionHelperIsATruthTable() throws {
        let view = codeOnly(try productSource(named: "Views/DailyCopyHeatmapView.swift"))
        let cell = region(in: view, named: "func cellView")
        XCTAssertTrue(cell.contains("DailyCopyHeatmapCell("), "区域助手取不到 cellView 的内容")
        XCTAssertFalse(cell.contains("private var footer"),
                       "区域把下一个成员也吞了 ⇒ 它其实是整文件，'按区域判'的判别力是假的")
        // R45 新增的一格：画法搬进 `DailyCopyHeatmapCell` 之后，
        // `onHover` 与按值动画都在**那个结构体**里，而调用点区域里不该再有它们。
        // 这一格管的是"守卫有没有跟着代码搬"：搬错了地方，上一条判据会红成"动画丢了"，
        // 而实际只是指错了区域 —— 那是一次假红，比漏检更浪费轮次。
        let cellDrawing = region(in: view, named: "struct DailyCopyHeatmapCell")
        XCTAssertTrue(cellDrawing.contains("onHover"), "格子区域取不到画法 ⇒ R45 之后守卫指错了主人")
        XCTAssertFalse(cell.contains("onHover"),
                       "调用点区域里不该再有画法：若有，说明 `cellView` 自己又画了一份，两份会分叉")
        // 同名成员的两个区域：文件里现在有两个 `var body`（视图的与单格的）。
        // 区域助手取的是**第一个**，所以这里必须钉住取到的是哪一个 ——
        // 取错了，③ 那三条按值/过渡断言量的就是单格而不是整块交换，而它看着是全绿的。
        let body = region(in: view, named: "var body")
        XCTAssertTrue(body.contains("value: counts.isEmpty)"),
                      "`var body` 取到的必须是视图的 body（整块交换在那里）")
        XCTAssertFalse(body.contains("strokeBorder"),
                       "`var body` 取到的是单格而不是视图 ⇒ 同名成员让区域指错了主人")
        let footer = region(in: view, named: "var footer")
        XCTAssertFalse(footer.contains("func cellView"), "同上：footer 区域不许把 cellView 也圈进来")
        // 取不到的那一路：哨兵串必须**不含**任何真实 needle，否则"找不到"会被读成"这里没有动画声明"。
        let missing = "\u{0}REGION-NOT-FOUND\u{0}"
        XCTAssertFalse(missing.contains(".animation("),
                       "哨兵串若含 needle，取不到区域会让按值动画的断言全绿")
        XCTAssertEqual(transitionCount(in: missing), 0)
    }

    /// 「这张图怎么读」必须**跟着图一起出现**，而且必须写在观察账本的那一层里。
    /// 两条各挡一种回归：摘掉闸门 ⇒ 空屏又在教人读一张不在这里的图；
    /// 把说明搬回 `SettingsView.statsSection` ⇒ 它读的是开页快照，用户复制第一条之后说明永远不出现。
    func testHeatmapReadingGuideFollowsTheChart() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        let occurrences = settings.components(separatedBy: "这张图怎么读").count - 1
        XCTAssertEqual(occurrences, 1, "同一句标题出现两次 = 两份会各自漂移的文案（U-30 去重那条同一族）")

        // needle 里**不带访问修饰符**：R11 因为胶片探针要宿主这个视图，把它从 `private struct`
        // 放开成 `struct` —— 那不是这条判据关心的事（它管的是"说明与图同源、同层"）。
        // 把 `private` 写进 needle 等于让一条视觉判据去锁一个访问级别，
        // 结果就是"产品没坏、守卫先红"。这种红也要记（它教的是 needle 的宽度）。
        guard let sectionStart = settings.range(of: "struct DailyCopyStatsSection")?.lowerBound,
              let guideAt = settings.range(of: "这张图怎么读")?.lowerBound else {
            return XCTFail("找不到 `DailyCopyStatsSection` 或那段说明 ⇒ 守卫看不到被守卫的东西")
        }
        XCTAssertGreaterThan(guideAt, sectionStart,
                             "说明不在观察账本的那一层里 ⇒ 它的可见性条件不会随第一条复制更新")

        // `SettingsView` 里有好几个 `var body`（主视图、`ReceiptLine`、这一段…），
        // 所以先把**结构体本身**圈出来，再在里面找它自己的 body ——
        // 直接按 `var body` 取会取到文件里第一个，那条判据就变成"恰好管着某个别的东西"。
        let section = region(in: settings, named: "struct DailyCopyStatsSection")
        let guideRegion = region(in: section, named: "var body")
        XCTAssertTrue(guideRegion.contains("if !ledger.counts.isEmpty"),
                      "没有闸门 ⇒ 空账本那一屏会同时说\"还没有记录\"和\"怎么读这张图\"")
        XCTAssertTrue(guideRegion.contains("Divider()"),
                      "分隔线要一起收进闸门里，否则空屏上会留一条悬空横线")
    }

    /// 说明块（分隔线 + 「这张图怎么读」）的过渡与驱动键必须**成对**出现。
    ///
    /// 说清楚这条判据管到哪：它管的是**结构**（有过渡、有驱动、键不是恒真）。
    /// 这条淡入到底演没演，胶片探针**量不到** ——
    /// `MotionFilmstripTests/testHeatmapFadeIsNotVisibleToThisRuler` 实测
    /// 开着目录与关掉目录两臂读数完全相同（帧数 1 / 峰值 0.225），
    /// 因为 `cacheDisplay` 抓的是模型树，纯 opacity 淡入活在 presentation 层。
    /// 所以这一条的状态是「源码已接、产物未量」，不许当成"已验证"，也不许当成"没做"。
    func testStatsGuideTransitionIsPairedWithADriver() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        let body = region(in: region(in: settings, named: "struct DailyCopyStatsSection"), named: "var body")
        XCTAssertTrue(body.contains(".transition(MotionCatalog.transition(for: .contentFade))"),
                      "说明块没有过渡 ⇒ 它是整块硬蹦出来的（R9 抓到的那一族）")
        XCTAssertTrue(body.contains("value: ledger.counts.isEmpty)"),
                      "有过渡但没有驱动键 ⇒ 又是一条'代码里有、屏幕上没有'（R9 撤掉页脚那条的同一族）")
    }

    // MARK: - 工具（原有）

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
