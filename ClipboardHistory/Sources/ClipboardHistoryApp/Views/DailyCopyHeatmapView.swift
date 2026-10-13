import SwiftUI

/// 每日复制热图（GitHub 贡献图那种"列 = 周、行 = 星期几"的方块日历）。
///
/// 全部判定（日键、分档、网格、月标签、汇总、tooltip 文案）都在
/// `DailyCopyHeatPolicy` 里，几何与色阶都在 `VisualHeat` 里 ——
/// 这个文件只负责把它们画出来。理由与仓库里每一张"图"一样：
/// 判据要能在不开窗口的情况下断言，而审美决定必须有唯一作者。
struct DailyCopyHeatmapView: View {
    /// 日键 → 条数。视图不持有任何计数逻辑。
    let counts: [String: Int]
    /// "今天"。生产里是 `Date()`，测试里注入固定时刻 ——
    /// 不注入的话这张图每天自己变，判据就成了日历彩票。
    let today: Date
    let calendar: Calendar

    /// 悬停中的那一格。`nil` = 没有，此时底部那行说汇总。
    @State private var hovered: DailyCopyHeatPolicy.Cell?

    init(counts: [String: Int],
         today: Date = Date(),
         calendar: Calendar = Calendar.current) {
        self.counts = counts
        self.today = today
        self.calendar = calendar
    }

    private var grid: [DailyCopyHeatPolicy.Week] {
        DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, calendar: calendar)
    }

    private var summary: DailyCopyHeatPolicy.Summary {
        DailyCopyHeatPolicy.summary(counts: counts, weeks: grid, today: today, calendar: calendar)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header

            if counts.isEmpty {
                // 空态必须说"为什么是空的"，而不是画一片灰格子。
                // 一片灰格子读起来像"我这半年一次都没复制"，而事实是"这里还没开始记"。
                StateLine(kind: .empty, message: "还没有可统计的记录 —— 复制几条之后这里会长出一张日历。")
            } else {
                gridSection
                footer
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - 头部

    private var header: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text("每日复制")
                .font(.system(size: VisualFont.title, weight: .semibold))
            Text("最近 \(DailyCopyHeatPolicy.defaultWindowWeeks) 周共 \(summary.total) 次 · "
                 + "日均 \(String(format: "%.1f", summary.averagePerDay)) 次 · "
                 + "连续 \(summary.currentStreak) 天")
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - 网格

    private var gridSection: some View {
        VStack(alignment: .leading, spacing: 2) {
            // 月标签单独一行：它的宽度必然大于一格，塞进列里会把格子挤开。
            monthLabelRow

            HStack(alignment: .top, spacing: VisualHeat.spacing) {
                weekdayLabels
                HStack(spacing: VisualHeat.spacing) {
                    ForEach(Array(grid.enumerated()), id: \.offset) { _, week in
                        VStack(spacing: VisualHeat.spacing) {
                            ForEach(Array(week.cells.enumerated()), id: \.offset) { _, cell in
                                cellView(cell)
                            }
                        }
                    }
                }
            }
        }
    }

    /// 月标签那一行。
    ///
    /// 为什么用 `offset` 而不是 `HStack` + 固定宽格子：标签的宽度必然大于一格
    ///（"11月" 约 22pt vs 格宽 11pt），塞进等宽槽里会被折成两行 ——
    /// 离屏帧实测就是这样：`11/月`、`1/2/月` 各占两行，把整张图往下顶了一格。
    /// 叠在一条固定高度的带上、按列宽偏移，才是这种"刻度行"的正确画法。
    private var monthLabelRow: some View {
        ZStack(alignment: .topLeading) {
            Color.clear.frame(height: 14)
            ForEach(Array(grid.enumerated()), id: \.offset) { index, week in
                if let label = week.monthLabel {
                    Text(label)
                        .font(.system(size: VisualFont.meta))
                        .foregroundStyle(.tertiary)
                        .fixedSize()
                        .offset(x: weekdayLabelWidth + CGFloat(index) * (VisualHeat.cell + VisualHeat.spacing))
                }
            }
        }
    }

    /// 星期标签。取偶数行（一/三/五/日）—— 四枚是"能读出这是星期几的网格"的最少数量，
    /// 七枚会把左侧标签列撑得比图还宽。
    private var weekdayLabels: some View {
        VStack(spacing: VisualHeat.spacing) {
            ForEach(0..<7, id: \.self) { row in
                Text(rowLabel(row))
                    .font(.system(size: VisualFont.meta))
                    .foregroundStyle(.tertiary)
                    .frame(width: weekdayLabelWidth, height: VisualHeat.cell, alignment: .trailing)
            }
        }
    }

    private func rowLabel(_ row: Int) -> String {
        guard row % 2 == 0,
              let date = grid.first?.cells[safe: row]?.date else { return "" }
        // 标签跟着 `calendar` 走：中文环境是"一/三/五"，英文环境是 "S/T/F"。
        // 写死中文会让切了系统语言的用户看到一张对不上号的日历。
        let symbols = calendar.veryShortWeekdaySymbols
        let index = calendar.component(.weekday, from: date) - 1
        guard index >= 0, index < symbols.count else { return "" }
        return symbols[index]
    }

    private var weekdayLabelWidth: CGFloat { 18 }

    // MARK: - 单格

    @ViewBuilder
    private func cellView(_ cell: DailyCopyHeatPolicy.Cell) -> some View {
        if cell.dayKey == nil || cell.isFuture {
            // 未来与窗口外：**不画**。画成灰格等于宣称"那天你一次都没复制"，
            // 而那天根本还没到 —— 这是这张图最容易撒的一个谎。
            Color.clear.frame(width: VisualHeat.cell, height: VisualHeat.cell)
        } else {
            let isHovered = hovered?.dayKey == cell.dayKey
            VisualShape.rounded(VisualRadius.heatCell)
                .fill(cell.count == 0
                      ? Color.primary.opacity(VisualHeat.empty)
                      : Color.accentColor.opacity(VisualHeat.opacity(bucket: cell.bucket)))
                .frame(width: VisualHeat.cell, height: VisualHeat.cell)
                .overlay(
                    // 悬停那一圈只在悬停时出现：常驻描边会让 126 个格子同时开口说话，
                    // 而这张图的信息全在**深浅**上。
                    VisualShape.rounded(VisualRadius.heatCell)
                        .strokeBorder(Color.primary.opacity(isHovered ? 0.55 : 0),
                                      lineWidth: VisualHeat.hoverStroke)
                )
                .contentShape(Rectangle())
                .onHover { inside in
                    hovered = inside ? cell : (hovered?.dayKey == cell.dayKey ? nil : hovered)
                }
                .accessibilityElement()
                // 走 `helpLabel` 而不是裸 `.help(`：仓库里有一条判据
                // （`AccessibilityLabelHygieneTests`）要求悬浮提示必须同时上无障碍标签，
                // 否则 VoiceOver 用户只有鼠标悬停才拿得到这句话。它第一次跑就把这里抓出来了。
                .helpLabel(DailyCopyHeatPolicy.tooltip(cell: cell, calendar: calendar))
        }
    }

    // MARK: - 底部：图例 + 悬停详情

    private var footer: some View {
        HStack(spacing: 8) {
            Text("少")
            ForEach(0..<VisualHeat.ladder.count, id: \.self) { index in
                VisualShape.rounded(VisualRadius.heatCell)
                    .fill(Color.accentColor.opacity(VisualHeat.ladder[index]))
                    .frame(width: VisualHeat.cell - 3, height: VisualHeat.cell - 3)
            }
            Text("多")
                .padding(.trailing, 4)

            // 悬停详情。没悬停时退回"最忙的一天"——这一行不能空着，
            // 空着的时候它下面就是大片空白，读起来像界面坏了。
            Text(footerDetail)
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)
                .frame(maxWidth: .infinity, alignment: .leading)
                .animation(MotionCatalog.animation(for: .hover), value: hovered?.dayKey ?? "")
        }
        .font(.system(size: VisualFont.meta))
        .foregroundStyle(.tertiary)
    }

    private var footerDetail: String {
        if let hovered, !hovered.isFuture {
            return DailyCopyHeatPolicy.tooltip(cell: hovered, calendar: calendar)
        }
        guard let key = summary.busiestDayKey, summary.busiestCount > 0,
              let date = DailyCopyHeatPolicy.date(forDayKey: key, calendar: calendar) else {
            return "这段时间没有记录"
        }
        let day = DailyCopyHeatPolicy.fullDayString(for: date, calendar: calendar)
        return "最忙的一天：\(day) · \(summary.busiestCount) 次"
    }
}

private extension Array {
    /// 网格标签那几处会按行号取元素；越界必须是"没有"，不是崩溃。
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
