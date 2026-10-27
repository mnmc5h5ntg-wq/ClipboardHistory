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
            if counts.isEmpty {
                // 空态必须说"为什么是空的"，而不是画一片灰格子。
                // 一片灰格子读起来像"我这半年一次都没复制"，而事实是"这里还没开始记"。
                StateLine(kind: .empty, message: "还没有可统计的记录 —— 复制几条之后这里会长出一张日历。")
                    .transition(MotionCatalog.transition(for: .contentFade))
            } else {
                // 汇总行**只在这臂存在**（见 `header` 的注释），所以它被搬进 `else` 里：
                // 空态那一臂如果还留着 `header`，那是一格零高度的占位，
                // 而外层 `VStack(spacing: 10)` 照样会为它付 10pt —— 卡片里就会多出一条
                // 看不见的顶部留白（R101 之前标题在这一格里，那 10pt 是有主的）。
                header
                VStack(alignment: .leading, spacing: 10) {
                    gridSection
                    footer
                }
                .transition(MotionCatalog.transition(for: .contentFade))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        // **第一条复制那一下**是这张图最该被看见的一次变化：空态整块换成日历。
        // 键是 `counts.isEmpty` 而不是 `counts` —— 后者每次复制都换实例，
        // 但"从空到有"只发生一次；用字典本身当键会让之后每一次计数都去驱动一次
        // 空↔网格的交换（那个交换此时是空操作，但事务是真的，白付）。
        // 两臂都挂 `.transition`：只挂一臂是 R5 的 A2 那一族（"声明了但只演一半"）。
        .animation(MotionCatalog.animation(for: .contentFade), value: counts.isEmpty)
    }

    // MARK: - 头部

    /// 汇总行（**标题不在这儿了** —— R101 / BACKLOG 131）。
    ///
    /// 「每日复制」搬到了 `DailyCopyStatsSection`，作为**卡片之上**的分区标题：这扇窗口其余四屏
    /// （通用 / 快捷键 / 隐私 / 数据）的语法都是"标题裸在页面上 + 内容在 `GroupBox` 里"，
    /// 而这条语法由判据 `CARD_ABOVE`（卡片顶之上恰好 1 段墨）钉着。标题留在组件里的那一版
    /// 会把这一屏变成全窗口唯一"标题在卡片内"的一屏 —— 那一版的红与帧都记在 Round 101 §2。
    ///
    /// 汇总行**只在有数据时出现**：阶段一的帧里它是"最近 26 周共 0 次 · 日均 0.0 次 · 连续 0 天"，
    /// 压在"还没有可统计的记录"上面 —— 同一屏两条互相矛盾的表达，
    /// 而且第二条（空态那句）才是用户需要知道的。零不是信息，"还没开始记"才是（U-30 缺陷 5）。
    private var header: some View {
        Group {
            if let line = DailyCopyHeatPolicy.summaryLine(for: summary,
                                                          hasRecords: !counts.isEmpty) {
                summaryText(line)
                    .transition(MotionCatalog.transition(for: .contentFade))
            }
        }
    }

    /// R419：汇总行的数字以前是硬换 —— 同一张图里的格子已经按档在演，读数却跳。
    /// 14+ 走系统的数字滚动（999→1000 连位数变化也能演）；12/13 没有这个 API，保持原样。
    /// 键是**整句**而不是某一个数：一行里有三个会变的数（总数 / 日均 / 连续），
    /// 拆成三条动画只会让它们各自起事务、互相错拍。
    @ViewBuilder
    private func summaryText(_ line: String) -> some View {
        let base = Text(line)
            .font(.system(size: VisualFont.meta))
            .foregroundStyle(.secondary)
        if #available(macOS 14, *) {
            base
                .contentTransition(.numericText())
                .animation(MotionCatalog.animation(for: .contentFade), value: line)
        } else {
            base
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
                        // **刻度不是装饰**（R27 / U-49 / D-086）：这三处（月份 / 星期 / 图例"少·多"）
                        // 以前都是 `.tertiary`，实测 **亮 1.88 : 1、暗 2.27 : 1** —— 与 R21 判为
                        // "看不见"的那两颗控件（清除 × 1.86、展开箭头 1.88）是同一组数。
                        // 区别只有一个：那两颗能点，这三处**要读**。没有月份与星期，
                        // 这张网格根本读不出"哪一天"；没有"少/多"，颜色深浅没有标尺。
                        // 所以它们必须在说明文字那一档（`.secondary`，实测 4.0），
                        // 而不是最淡的一档。判据 `testCaptionTextStaysOnTheSecondaryTier`。
                        .foregroundStyle(.secondary)
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
                    .foregroundStyle(.secondary)
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
            DailyCopyHeatmapCell(
                cell: cell,
                isHovered: hovered?.dayKey == cell.dayKey,
                calendar: calendar
            ) { inside in
                // 事务挂在**变更点**上，而不是靠下游一条 `.animation(value:)`：
                // 描边（可插值的透明度）与页脚（字符串）由同一个 `hovered` 驱动，
                // 挂在这里两者一起进事务，而格子那一条才是真的被插值的那半。
                withAnimation(MotionCatalog.animation(for: .hover)) {
                    hovered = inside ? cell : (hovered?.dayKey == cell.dayKey ? nil : hovered)
                }
            }
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
            //
            // 这一行**刻意没有动效**，而且阶段一这里原本有一条假的：
            // `.animation(.hover, value: hovered?.dayKey ?? "")` 挂在一个 `Text` 上，
            // 而它变的是**字符串内容** —— 字符串不可插值，所以那条声明一次也没演过（U-30 缺陷 2）。
            // 要做"换字有过程"只能 `.id(text).transition(.opacity)` 那一套，
            // 而它在 macOS 12/13 上会先空一帧再淡入（`MotionModifiers` 那条同一族），
            // 比硬换更糟。tooltip 与无障碍标签已经把同一句话说第二遍了，
            // 这一行换字是"读数变了"，不是"状态变了"——原生系统里状态栏读数也是硬换。
            Text(footerDetail)
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .font(.system(size: VisualFont.meta))
        .foregroundStyle(.secondary)
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

/// 热图的一格（R45 从 `DailyCopyHeatmapView.cellView` 的 else 分支抽出来）。
///
/// 抽它的理由不是"文件长"，是**这件事以前只能靠注释**：
/// `VisualHeat.hoverStroke` 那里写着"发丝线在深色格子上会消失，所以描边要重一档"，
/// 而悬停那一圈**从来没有被画出来对过账** —— 因为 `hovered` 是宿主的 `@State`，
/// 而 R14 实测三条"合成 hover"的路全断（CGEvent 被窗口服务器丢弃、
/// 直接喂 `mouseEntered` 不回调、`sendEvent` 崩；数据在
/// `.scratch/motion-audit-2/spike_hover_channel.md`，结论抄在
/// `PressFeedbackTests` 那条梯子判据的开头）。
/// 把"画法"收进一个以 `isHovered` 为入参的视图之后：
/// **触发**那一半仍然只能人眼验（人工批次 22），**表达**这一半第一次可离线渲染、可逐档量、可看。
///
/// 产品走的还是同一条路 —— `cellView` 的 else 分支现在只是把 `hovered` 折成
/// `isHovered` 再交给这里，`heatmap-populated` 那两张帧判的就是它
/// （`HeatmapHoverEvidenceTests` 里有一条源码守卫钉住"网格确实经过这里"）。
struct DailyCopyHeatmapCell: View {
    let cell: DailyCopyHeatPolicy.Cell
    let isHovered: Bool
    /// tooltip 文案由 policy 现算，**不从外面传字符串**：
    /// 传进来就等于允许调用方（包括夹具）替产品决定"这一格该说什么" ——
    /// R43 那条"夹具不许手写回执文案"判据抓的是同一件事。
    let calendar: Calendar
    let onHover: (Bool) -> Void

    var body: some View {
        VisualShape.rounded(VisualRadius.heatCell)
            .fill(cell.count == 0
                  ? Color.primary.opacity(VisualHeat.empty)
                  : Color.accentColor.opacity(VisualHeat.opacity(bucket: cell.bucket)))
            .frame(width: VisualHeat.cell, height: VisualHeat.cell)
            // 当天那一格从浅到深是这张图**唯一一条实时通道**：用户复制一下，
            // 右下角就该有反应。没有这一条的话它是硬切，读起来像"数字被换掉了"
            // 而不是"我又多复制了一次"（阶段一自检 88 分扣在的就是这里，U-30）。
            // 键取 `bucket` 而不是 `count`：深浅本来就是按档走的，
            // 12 → 13 次若仍在同一档，画面**不该**动 —— 拿 count 当键会让每次复制
            // 都起一次事务去插值一个不会变的值（白付，而且让"变了"这件事失去意义）。
            .animation(MotionCatalog.animation(for: .contentFade), value: cell.bucket)
            .overlay(
                // 悬停那一圈只在悬停时出现：常驻描边会让 126 个格子同时开口说话，
                // 而这张图的信息全在**深浅**上。
                // 透明度走 `VisualHeat.hoverRingOpacity`：让"这一圈有多重"是一个有名字的数，
                // 而不是调用点上一个裸字面量（R45：它第一次被逐档量之前，
                // 那个裸数凭什么这么定，盘面上没有任何记录。R300 又量了一次：
                // 0.55 时这一圈在最响的一臂上改 75.50/255，而最重的一次数据变化只改 37.33 ⇒
                // 交互比数据响，于是它被降到 0.30（推导与两条界一起写在令牌那段的注释里）。
                //
                // **R308：`strokeBorder` → `stroke` + `padding(-hoverRingGap)`。**
                // 前者把描边画在形状**里面**，于是"鼠标划过"这件事会改掉那一格外圈的
                // **数据像素**（深浅就是这张图的全部信息），而且环的响度跟着档位变：
                // 现读同一颗尺，最响的一臂（亮档 2x 空格）41.42、最安静的一臂
                // （bucket4）18.87 —— 同一个动作的响度差 2.19 倍，且**最响的地方正是没有数据的那一格**。
                // 搬到格子外面的留白之后，环画在窗口底色上：数据像素一个都不动，
                // 响度也不再随档位变（剩下的离散只来自外观与像素密度，不来自数据）。
                VisualShape.rounded(VisualRadius.heatCell + VisualHeat.hoverRingGap)
                    .stroke(Color.primary.opacity(VisualHeat.hoverRingOpacity(isHovered: isHovered)),
                            lineWidth: VisualHeat.hoverStroke)
                    .padding(-VisualHeat.hoverRingGap)
            )
            .contentShape(Rectangle())
            .onHover(perform: onHover)
            .accessibilityElement()
            // 走 `helpLabel` 而不是裸 `.help(`：仓库里有一条判据
            // （`AccessibilityLabelHygieneTests`）要求悬浮提示必须同时上无障碍标签，
            // 否则 VoiceOver 用户只有鼠标悬停才拿得到这句话。它第一次跑就把这里抓出来了。
            .helpLabel(DailyCopyHeatPolicy.tooltip(cell: cell, calendar: calendar))
    }
}

private extension Array {
    /// 网格标签那几处会按行号取元素；越界必须是"没有"，不是崩溃。
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
