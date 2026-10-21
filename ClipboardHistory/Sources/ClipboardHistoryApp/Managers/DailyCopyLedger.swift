import Foundation

/// 采集侧写一笔复制时用的入口（协议存在只为让测试能塞一个内存替身，
/// 也让 `HistoryStore` 那一侧的胶水不必知道磁盘这件事）。
@MainActor
protocol DailyCopyRecording: AnyObject {
    /// 记一次"当天发生了复制"。**不许在采集路径上做同步磁盘写**（见实现里的注释）。
    func recordCopy(at date: Date)
    /// 账本空着时，用现有历史的时间戳回填一次。
    func backfillIfEmpty(from dates: [Date])
}

/// 每日复制条数的账本（新功能 / 目标模式阶段一）。
///
/// 为什么不直接从 `HistoryStore.entries` 现算：历史有 **500 条上限**（保留策略），
/// 现算出来的"每日条数"会随着旧条目被淘汰而**倒退** —— 上个月那格会自己变浅、
/// 再变灰，最后整列空掉。那不是统计，那是随机数。
/// 所以计数单独落一份**只追加**的小账：删记录、清历史都不会改写你已经复制过多少次的事实。
///
/// 这份数据是可再生的派生品，不是用户内容：
/// ① 它单独一个文件（`daily-copy.json`），回滚 = 删掉它，历史存档一个字节都不动；
/// ② 导出 / 导入 / 隐私擦除都不碰它（真要"连统计一起抹"得单独做一个动作，见 BACKLOG）。
@MainActor
final class DailyCopyLedger: ObservableObject, DailyCopyRecording {
    /// 视图读这个：日键 → 条数。
    @Published private(set) var counts: [String: Int]

    private let fileURL: URL
    private let calendar: Calendar
    private let now: () -> Date
    private let debounceSeconds: TimeInterval
    /// 写盘专用队列（`.utility`：统计落盘不该和用户的复制抢主线程，也不该抢 OCR 的带宽）。
    private let saveQueue = DispatchQueue(label: "daily-copy-ledger.save", qos: .utility)
    private var pendingSave: DispatchWorkItem?
    /// 还没落盘的那份快照。`flushPendingSaves` 靠它**同步**写完 ——
    /// 原来的 `pendingSave.wait()` 会一直等到 `asyncAfter` 的延迟到期，
    /// 也就是说"退出时落盘"会把退出堵住两秒（去抖多久堵多久）。
    private var pendingSnapshot: [String: Int]?
    private let failureBox = WriteFailureBox()

    /// 账本眼里的"今天"。生产里就是 `Date()`；注入时钟时它是那个固定时刻。
    ///
    /// 为什么要暴露它：热图的窗口是"从今天往回数 18 周"。如果视图自己再取一次
    /// `Date()`，那么**注入时钟的夹具**会看到一格都不在窗口里（实测就是这样：
    /// 夹具的计数在三月、视图的今天在十月 ⇒ 整张图全灰）。
    /// 让"今天"只有一个来源，既修掉这个测试盲区，也让"账本与图说的是同一天"
    /// 这件事在跨午夜时不会各算各的。
    var today: Date { now() }

    /// 上一次写盘失败的原因（`nil` = 没失败过 / 已经恢复）。
    ///
    /// 只在"存不下"时非空 —— 静默失败会让这张图悄悄停在几天前。
    ///
    /// **为什么是 `@Published` 而不是直接读盒子**（R10 / BACKLOG 14）：
    /// 阶段一把它做成"计算属性读加锁盒子"，值确实不会丢（盒子在后台队列上被写），
    /// 但**没有任何东西为它发布** ⇒ 写盘失败之后如果用户不再复制，那一行永远不上屏，
    /// 重启之后更是永远 `nil`。也就是"防静默失败"这件事只做成了一半。
    ///
    /// 现在两条都保住：**值仍然只在盒子里**，这个 `@Published` 只是它的主线程镜像，
    /// 由 `scheduleVisibilityCheck()` 在写盘截止点之后同步一次。
    /// 那个通知如果被丢掉（主队列忙、进程要退），最坏结果只是**晚一格显示**，
    /// 而不是静默 —— 这正是原来那条注释要保住的性质。
    @Published private(set) var lastWriteError: String?

    /// 写盘截止点之后"回头看一眼盒子"的那件事。
    ///
    /// 它必须跑在**主队列**上：闭包字面量写在 `@MainActor` 方法里会被推成 MainActor 隔离，
    /// 丢到 `saveQueue` 上就是 `dispatch_assert_queue` SIGTRAP（D-068 第 4 条那次崩溃）。
    private var pendingVisibilityCheck: DispatchWorkItem?

    /// 通知比写盘截止点晚这么多再看：留出去抖项被排到队列后面的时间。
    /// 不是"等够就一定写完"—— 值一直在盒子里，这一条只决定什么时候上屏。
    /// 写盘截止点之后，回主线程看盒子之前再让出来的那一段（秒）。
    ///
    /// R270 / BACKLOG 320：原来是 `private let` —— 于是判据想按这条日程推观察窗口长度，
    /// 只能把 0.15 **抄**进测试里（抄值会腐烂，R94 那条规矩）。改成 `static let`（internal）
    /// 之后测试直接读它：产品里改这个值，`ledger_timing_scan.py` 与那条判据的窗口长度会一起动，
    /// 不需要有人记得去改注释里的数字。
    static let visibilityGrace: TimeInterval = 0.15

    /// 保留多久。两年 = 104 周，够看"去年这时候忙不忙"，又让文件尺寸有界
    ///（一天一个键，最坏 730 条 ≈ 12KB）。
    nonisolated static let retentionDays = 730

    init(fileURL: URL? = nil,
         calendar: Calendar = Calendar.current,
         debounceSeconds: TimeInterval = 2,
         now: @escaping () -> Date = Date.init) {
        let url = fileURL ?? Self.defaultFileURL()
        self.fileURL = url
        self.calendar = calendar
        self.debounceSeconds = debounceSeconds
        self.now = now
        self.counts = Self.load(from: url, calendar: calendar, now: now())
    }

    static func defaultFileURL(calendar: Calendar = Calendar.current) -> URL {
        // 与历史存档同一个根目录 ⇒ 同一个 `CLIPBOARD_HISTORY_DATA_DIR` 隔离开关管住它，
        // 运行时冒烟测试才不会碰用户那份真数据（D-002 的边界）。
        FileHistoryPersistence.defaultRootDirectory().appendingPathComponent("daily-copy.json")
    }

    // MARK: - 写入

    func recordCopy(at date: Date) {
        let key = DailyCopyHeatPolicy.dayKey(for: date, calendar: calendar)
        counts[key, default: 0] += 1
        scheduleSave()
    }

    /// 只在**空账本**时回填。已经记了半年的账不能被 500 条上限的存档倒灌覆盖 ——
    /// 那会把"最近三个月之外"的部分直接抹掉。
    ///
    /// 回填**只改内存、不排写盘**：`HistoryStore.init` 会调它，而"构造期写盘"是这个仓库
    /// 立过规矩的红线（`HistoryPersistenceTests` 里那条 "init 阶段绝不能写盘"，
    /// 起因是第二个实例会在守卫之前覆盖存档 —— D-002）。
    /// 计数留在 `pendingSnapshot` 里，下一次真复制、或退出时的 flush 会把它落下去。
    func backfillIfEmpty(from dates: [Date]) {
        guard counts.isEmpty, !dates.isEmpty else { return }
        counts = DailyCopyHeatPolicy.counts(dates: dates, calendar: calendar)
        counts = Self.pruned(counts: counts, now: now(), calendar: calendar, retentionDays: Self.retentionDays)
        pendingSnapshot = counts
    }

    /// 把待写的东西**同步**落盘。退出路径必须调它：
    /// 去抖窗口里被 SIGTERM 打断会丢掉最后几秒的计数（这条在历史存档上栽过一次，见 D-004）。
    func flushPendingSaves() {
        pendingVisibilityCheck?.cancel()
        pendingVisibilityCheck = nil
        guard let snapshot = pendingSnapshot else { return }
        pendingSave?.cancel()
        pendingSave = nil
        pendingSnapshot = nil
        do {
            try Self.write(snapshot, to: fileURL)
            failureBox.message = nil
        } catch {
            failureBox.message = error.localizedDescription
        }
        // 退出路径上没有"下一次去抖到期"了，所以这里必须自己同步一次镜像 ——
        // 否则那条失败只进了盒子，而屏幕上什么都不会说（D-068 第 8 条记的就是这个洞）。
        syncWriteFailure()
    }

    private func scheduleSave() {
        let snapshot = Self.pruned(counts: counts,
                                   now: now(),
                                   calendar: calendar,
                                   retentionDays: Self.retentionDays)
        pendingSnapshot = snapshot
        pendingSave?.cancel()
        let workItem = Self.makeSaveWorkItem(snapshot: snapshot, url: fileURL, box: failureBox)
        pendingSave = workItem
        saveQueue.asyncAfter(deadline: .now() + debounceSeconds, execute: workItem)
        scheduleVisibilityCheck()
    }

    /// 在写盘截止点之后回主线程看一眼盒子。见 `lastWriteError` 的注释。
    private func scheduleVisibilityCheck() {
        pendingVisibilityCheck?.cancel()
        let item = DispatchWorkItem { [weak self] in self?.syncWriteFailure() }
        pendingVisibilityCheck = item
        DispatchQueue.main.asyncAfter(deadline: .now() + debounceSeconds + Self.visibilityGrace, execute: item)
    }

    /// 盒子 → `@Published` 镜像。**相同就不发变更** ——
    /// 否则每复制一条都会让设置页为同一个（通常为空）的错误重排一次。
    private func syncWriteFailure() {
        pendingVisibilityCheck = nil
        let message = failureBox.message
        if message != lastWriteError {
            lastWriteError = message
        }
    }

    /// 去抖写盘的那个闭包，必须在**非隔离**的上下文里造出来。
    ///
    /// 为什么专门绕一层静态工厂：闭包字面量写在 `@MainActor` 的方法里，就会被推成
    /// MainActor 隔离，而它实际跑在 `saveQueue` 上 —— Swift 会在闭包入口插
    /// `dispatch_assert_queue`，于是**第一次去抖到期就 SIGTRAP**。
    /// 这不是理论问题：本机全量测试就是这么崩的，崩溃栈写着
    /// `closure #1 in DailyCopyLedger.scheduleSave()`，而测试自己全绿
    /// （崩在两个用例之间，`swift test` 只留下"signal code 5"）。
    /// 回归判据见 `DailyCopyHeatmapTests.testDebouncedWriteFiresWithoutMainActorTrap`。
    nonisolated private static func makeSaveWorkItem(snapshot: [String: Int],
                                                     url: URL,
                                                     box: WriteFailureBox) -> DispatchWorkItem {
        DispatchWorkItem {
            do {
                try write(snapshot, to: url)
                box.message = nil
            } catch {
                box.message = error.localizedDescription
            }
        }
    }

    // MARK: - 读写（全部 nonisolated：它们在后台队列上跑，不碰 @Published）

    nonisolated static func write(_ counts: [String: Int], to url: URL) throws {
        let directory = url.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let sorted = counts.keys.sorted().reduce(into: [String: Int]()) { partial, key in
            partial[key] = counts[key]
        }
        let data = try JSONEncoder().encode(sorted)
        // 原子写：先写临时文件再 rename。半截文件会让下次载入判成"损坏"，
        // 而一份只追加的派生数据被半截写毁掉是纯亏。
        try data.write(to: url, options: [.atomic])
    }

    nonisolated static func load(from url: URL, calendar: Calendar, now: Date) -> [String: Int] {
        guard let data = try? Data(contentsOf: url) else { return [:] }
        guard let decoded = try? JSONDecoder().decode([String: Int].self, from: data) else {
            // 损坏 ⇒ **保全原件**再从零开始（与历史存档同一套处置）。
            // 直接覆盖会把"至少还有几天数据"这件事也弄没。
            let backup = url.appendingPathExtension("bak")
            try? FileManager.default.removeItem(at: backup)
            try? FileManager.default.moveItem(at: url, to: backup)
            return [:]
        }
        return pruned(counts: decoded, now: now, calendar: calendar, retentionDays: retentionDays)
    }

    /// 裁掉超出保留窗口的旧日子。载入与每次写盘都做，所以文件尺寸有界。
    nonisolated static func pruned(counts: [String: Int],
                                   now: Date,
                                   calendar: Calendar,
                                   retentionDays: Int) -> [String: Int] {
        guard let cutoff = calendar.date(byAdding: .day, value: -retentionDays, to: now) else { return counts }
        let cutoffKey = DailyCopyHeatPolicy.dayKey(for: cutoff, calendar: calendar)
        return counts.filter { $0.key >= cutoffKey }
    }
}

/// 跨队列传一条错误信息用的小盒子（存在理由见 `lastWriteError`）。
///
/// `@unchecked Sendable` 是**有根据的**：里面只有一个 `String?`，读写都在 `NSLock` 里，
/// 没有不变量需要维护。这类标注一旦需要，就要同时写下"为什么安全"，
/// 否则它就是把并发问题从编译器手里偷走的口子。
private nonisolated final class WriteFailureBox: @unchecked Sendable {
    private let lock = NSLock()
    private var stored: String?

    var message: String? {
        get {
            lock.lock(); defer { lock.unlock() }
            return stored
        }
        set {
            lock.lock(); defer { lock.unlock() }
            stored = newValue
        }
    }
}
