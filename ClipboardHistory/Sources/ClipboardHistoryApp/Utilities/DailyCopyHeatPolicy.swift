import Foundation

/// 每日复制热图的**全部判定**（新功能 / 目标模式阶段一）。
///
/// 为什么是一族纯函数而不是"视图里算"：日键、分档、周网格、月标签放哪、汇总说哪几个数 ——
/// 这五件事决定这张图读起来是"我的复制节奏"还是"一堆彩色方块"。
/// 它们必须能在**不开窗口、不碰磁盘**的情况下被断言
///（AGENTS.md：新特性先建 `*Policy` / `*Planner`，视图与 Store 只留薄胶水）。
///
/// 这里刻意**没有任何静态可变状态**：网格与标签是"扫一遍算出来"的，
/// 一旦把"上一枚标签在哪一列"塞进 static，两条测试的先后顺序就会改变结果 ——
/// 那种判据红的时候没人知道是不是上一行留下的。
///
/// 口径（写在这里，视图与文案不许各说一套）：
/// 一格 = 一个**本地日**；计数 = 当天被采集侧接受的复制事件数。
/// 同一内容连着复制 5 次算 5 次（它确实复制了 5 次）；
/// 暂停采集与被排除的 App 不算 —— 那条判断在 `CapturePolicy`，不在这里。
enum DailyCopyHeatPolicy {

    // MARK: - 日键

    /// 日键格式 `2026-03-12`。刻意用 ISO 风格而不是本地化串 —— 它是字典的键，
    /// 要能稳定往返，不能跟着系统语言变。同时它**字典序 = 时间序**，所以下面几处
    /// 直接比字符串就是比日期。
    static let dayKeyFormat = "yyyy-MM-dd"

    static func dayKey(for date: Date, calendar: Calendar = Calendar.current) -> String {
        makeFormatter(format: dayKeyFormat, calendar: calendar).string(from: date)
    }

    static func date(forDayKey key: String, calendar: Calendar = Calendar.current) -> Date? {
        makeFormatter(format: dayKeyFormat, calendar: calendar).date(from: key)
    }

    /// 一串事件时刻 → 每日条数。
    static func counts(dates: [Date], calendar: Calendar = Calendar.current) -> [String: Int] {
        var result: [String: Int] = [:]
        for date in dates {
            result[dayKey(for: date, calendar: calendar), default: 0] += 1
        }
        return result
    }

    /// `template` 传 nil 时按 `format` 原样当 pattern 用。
    ///
    /// 为什么两条路都要：日键与月标签要**字面量**（`yyyy-MM-dd`、`M'月'`），
    /// 走模板会被本地化引擎把字面量吃掉；而"完整那天"要的是**跟着系统语言走**的日期，
    /// 只有模板能给（写死 `yyyy年M月d日` 在英文环境下会输出 "2026年3月12日" 那种混血串）。
    private static func makeFormatter(format: String,
                                      calendar: Calendar,
                                      template: String? = nil) -> DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        if let template {
            formatter.locale = calendar.locale
            formatter.setLocalizedDateFormatFromTemplate(template)
        } else {
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.dateFormat = format
            formatter.timeZone = calendar.timeZone
        }
        return formatter
    }

    // MARK: - 分档

    /// 五档（0 = 没有记录，1…4 由浅到深）。
    ///
    /// **档位是相对用户自己的数据算的，不是绝对阈值**：绝对阈值（比如"≥26 算最深"）
    /// 会让轻度用户的整张图都是灰的（读不出任何节奏），让重度用户的整张图都是深的
    ///（同样读不出）。代价必须写清楚：**同一格的颜色会随窗口内其他天的数据变**，
    /// 所以它是"相对强度"，图例那一行只能说"少 → 多"，不许标具体数字。
    static func bucketEdges(positiveCounts: [Int]) -> [Int] {
        let sorted = positiveCounts.sorted()
        guard let last = sorted.last, last > 0 else { return [] }
        var edges: [Int] = []
        for fraction in [0.25, 0.5, 0.75] {
            let index = min(sorted.count - 1, max(0, Int((Double(sorted.count) * fraction).rounded(.down))))
            let edge = sorted[index]
            if edge > 0, !edges.contains(edge) { edges.append(edge) }
        }
        return edges
    }

    static func bucket(count: Int, edges: [Int]) -> Int {
        guard count > 0 else { return 0 }
        return min(4, 1 + edges.filter { count >= $0 }.count)
    }

    // MARK: - 网格

    struct Cell: Equatable {
        let dayKey: String?
        let date: Date?
        /// 这一格在"今天"之后 ⇒ 不许画成"那天我一次都没复制"。
        let isFuture: Bool
        let count: Int
        let bucket: Int

        static let placeholder = Cell(dayKey: nil, date: nil, isFuture: false, count: 0, bucket: 0)
    }

    struct Week: Equatable {
        let cells: [Cell]
        /// 这一列顶部要不要写月份名。
        let monthLabel: String?
    }

    /// 可见窗口默认多少周。
    ///
    /// 26 周 ≈ 半年：设置页右栏在最小窗口下约 412pt 可用，
    /// 26 × (11 + 3) + 18 ≈ 382pt 仍然放得下，不需要横向滚动
    ///（而"要横向滚动的图"基本等于没人看）。
    /// 第一版取 18 周是按 720pt 窗口估的，离屏帧实测右边空出一大片 ——
    /// 一张只用了半栏的日历读起来像没画完。
    static let defaultWindowWeeks = 26
    /// 两枚月标签之间至少隔几列（挨着写会糊成"1月2月3月"一条带子，比不写更糟）。
    static let minimumGapBetweenMonthLabels = 4

    /// 排成"列 = 周、行 = 星期几"的网格，**最后一列含今天**。
    ///
    /// 行的起点跟着 `calendar.firstWeekday` 走（中文环境默认周一）——
    /// 写死周日会让中文用户第一列凭空缺一天。
    static func weeks(counts: [String: Int],
                      endingOn today: Date,
                      weeks window: Int = DailyCopyHeatPolicy.defaultWindowWeeks,
                      calendar: Calendar = Calendar.current) -> [Week] {
        guard window > 0 else { return [] }
        let edges = bucketEdges(positiveCounts: Array(counts.values).filter { $0 > 0 })
        let startOfTodayWeek = calendar.dateInterval(of: .weekOfYear, for: today)?.start ?? today
        guard let gridStart = calendar.date(byAdding: .weekOfYear, value: -(window - 1), to: startOfTodayWeek)
        else { return [] }
        let endOfTodayWeek = calendar.date(byAdding: .day, value: 6, to: startOfTodayWeek) ?? today

        var days: [Date] = []
        var cursor = gridStart
        while cursor <= endOfTodayWeek {
            days.append(cursor)
            guard let next = calendar.date(byAdding: .day, value: 1, to: cursor) else { break }
            cursor = next
        }
        let todayKey = dayKey(for: today, calendar: calendar)

        var columns: [[Cell]] = []
        var index = 0
        while index < days.count {
            var column: [Cell] = []
            for offset in 0..<7 {
                guard index + offset < days.count else { break }
                let date = days[index + offset]
                let key = dayKey(for: date, calendar: calendar)
                let count = counts[key] ?? 0
                column.append(Cell(dayKey: key,
                                   date: date,
                                   isFuture: key > todayKey,
                                   count: count,
                                   bucket: bucket(count: count, edges: edges)))
            }
            while column.count < 7 { column.append(.placeholder) }
            columns.append(column)
            index += 7
        }

        // 第二遍只干一件事：决定哪几列顶部写月份。分开写是因为它需要"上一枚标签在哪一列"，
        // 而这个状态必须是**局部的**。
        var result: [Week] = []
        var lastLabelledColumn = -10
        var lastLabelledMonth = -1
        for (columnIndex, column) in columns.enumerated() {
            var label: String?
            // 标签跟着"这一列里第一个还在窗口内的日子"——最后一列的后半截是未来，
            // 用它定月份会把标签推到不存在的月份上。
            if let anchor = column.first(where: { !$0.isFuture && $0.date != nil })?.date {
                let month = calendar.component(.month, from: anchor)
                // 第一列不写：它常常是上个月的尾巴，凭空多一枚标签会显得图没对齐。
                if columnIndex > 0, month != lastLabelledMonth,
                   columnIndex - lastLabelledColumn >= minimumGapBetweenMonthLabels {
                    label = monthLabel(for: anchor, calendar: calendar)
                    lastLabelledMonth = month
                    lastLabelledColumn = columnIndex
                }
            }
            result.append(Week(cells: column, monthLabel: label))
        }
        return result
    }

    // MARK: - 文案

    static func tooltip(cell: Cell, calendar: Calendar = Calendar.current) -> String {
        guard let date = cell.date, !cell.isFuture else { return "" }
        let day = fullDayString(for: date, calendar: calendar)
        return cell.count == 0 ? "\(day) · 没有记录" : "\(day) · 复制 \(cell.count) 次"
    }

    /// 月标签：`M'月'` 是**字面量**，不走本地化模板。
    ///
    /// 两个理由：① 全称月份在窄列里会溢出（英文 "March" 一整词），把网格推歪；
    /// ② 模板会把非字段字母吃掉，"月" 这个字面量传进去会直接消失。
    /// 界面本身是中文的，所以这里不需要跟着系统语言变。
    static func monthLabel(for date: Date, calendar: Calendar) -> String {
        makeFormatter(format: "M'月'", calendar: calendar).string(from: date)
    }

    /// 完整那天（tooltip 与底部详情用）：`2026年3月12日 周四`。
    ///
    /// 为什么自己拼而不是走本地化模板：模板 `yyyyMMMMdEEEE` 在 en_US 下实测吐过
    /// "2025 M11 17, Mon" —— 月份被当成 "M11" 这种半截字段。而这张图的界面语言本来就是中文
    /// （和 `monthLabel` 同一个理由），"年月日" 是字面量、星期几取日历的符号表，
    /// 两边都对且**不会随系统语言漂**。
    static func fullDayString(for date: Date, calendar: Calendar) -> String {
        let parts = calendar.dateComponents([.year, .month, .day, .weekday], from: date)
        let symbols = calendar.shortWeekdaySymbols
        let index = (parts.weekday ?? 1) - 1
        let weekday = symbols.indices.contains(index) ? symbols[index] : ""
        return "\(parts.year ?? 0)年\(parts.month ?? 0)月\(parts.day ?? 0)日 \(weekday)"
    }

    // MARK: - 汇总

    struct Summary: Equatable {
        let total: Int
        let daysWithRecords: Int
        /// 平均每个**在窗口内的日子**多少次（含 0 的那些天）——
        /// 只除"有记录的天数"会把轻度用户说成"日均 8 次"，那是另一种自欺。
        let averagePerDay: Double
        let busiestDayKey: String?
        let busiestCount: Int
        let currentStreak: Int
    }

    static func summary(counts: [String: Int],
                        weeks grid: [Week],
                        today: Date,
                        calendar: Calendar = Calendar.current) -> Summary {
        let realCells = grid.flatMap(\.cells).filter { !$0.isFuture && $0.dayKey != nil }
        let total = realCells.reduce(0) { $0 + $1.count }
        let busiest = realCells.max { lhs, rhs in
            if lhs.count != rhs.count { return lhs.count < rhs.count }
            return (lhs.dayKey ?? "") > (rhs.dayKey ?? "")   // 并列时取更早的那天（键更小）
        }
        return Summary(
            total: total,
            daysWithRecords: realCells.filter { $0.count > 0 }.count,
            averagePerDay: realCells.isEmpty ? 0 : Double(total) / Double(realCells.count),
            busiestDayKey: busiest?.dayKey,
            busiestCount: busiest?.count ?? 0,
            currentStreak: streak(counts: counts, today: today, calendar: calendar)
        )
    }

    /// 连续天数。**今天还没复制不算断**：从昨天往回数。
    /// 否则每天凌晨到下午这段时间，一条跑了一个月的连续记录会当场显示 0，
    /// 而那既不是事实也不是任何人能改变的事。
    static func streak(counts: [String: Int], today: Date, calendar: Calendar = Calendar.current) -> Int {
        func hasRecord(_ date: Date) -> Bool { (counts[dayKey(for: date, calendar: calendar)] ?? 0) > 0 }
        var cursor = today
        if !hasRecord(cursor) {
            guard let yesterday = calendar.date(byAdding: .day, value: -1, to: today), hasRecord(yesterday)
            else { return 0 }
            cursor = yesterday
        }
        var streak = 0
        while hasRecord(cursor) {
            streak += 1
            guard let previous = calendar.date(byAdding: .day, value: -1, to: cursor) else { break }
            cursor = previous
        }
        return streak
    }
}
