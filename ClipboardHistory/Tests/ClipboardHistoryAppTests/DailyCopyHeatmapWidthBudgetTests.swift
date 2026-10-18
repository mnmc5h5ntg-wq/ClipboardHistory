// 不覆盖管线：这一卷测的是**热图网格的宽度预算**（产品令牌 `VisualHeat`、`weekdayLabelWidth`、
// `DailyCopyHeatPolicy.defaultWindowWeeks` 与捕获夹具那条 430pt 组件帧之间的关系）。
// 它是 R166 量出的那条 118pt 空白带（BACKLOG 197）里"能不能靠多排一周来填"这半条的**唯一可复查答案**。
// 管线级的判据在别处，这里指过去而不是重抄一份：
//   · 组件真画得下 —— `UICaptureTests` 的 `heatmap-populated` 夹具带 `contentMustFit: true`（画不下会红）；
//   · 相邻深浅分得开 —— 热图梯子那一卷（R52 / BACKLOG 71）；
//   · 悬停描边几何 —— `HeatmapHoverEvidenceTests`（R15 / R45）。
import XCTest
@testable import ClipboardHistoryApp

/// R169 / BACKLOG 197：把"26 周是不是本来就这么多"从印象换成数。
///
/// 本轮量到的结论（写在这里，因为它推翻了我自己上一轮写进注释的理由）：
/// 组件帧可用宽 = 430 − 2×16 = **398pt**，而 26 周的网格宽 = 18 + 26×11 + 25×3 = **379pt** ⇒ 余量 **19pt**；
/// 一周占 `cell + spacing` = 14pt ⇒ **多一周放得下（393pt），多两周顶破（407pt）**。
/// 所以"加周数"这条修法只能削掉 14pt，剩下 ~104pt 的带不是周数能填的；
/// 而"放大格子"那条动的是**高度**（一列 7 格），也就是 R31/R39/R104 一路判下来的垂直节奏。
/// 两半都不是"本来就这么多"，也两半都不便宜 ⇒ 197 保持开着，等最小窗口那一档的实测读数（新开 200）。
@MainActor
final class DailyCopyHeatmapWidthBudgetTests: XCTestCase {

    /// 网格宽 = 星期标签列 + N 格 + (N−1) 条间距。
    /// 与产品摆的那条 `offset(x: weekdayLabelWidth + index * (cell + spacing))` 必须同式 ——
    /// 分叉由 `testGridWidthFormulaMatchesTheProductOffsets` 钉住。
    private func gridWidth(weeks: Int) -> CGFloat {
        let label = try! productWeekdayLabelWidth()
        return label + CGFloat(weeks) * VisualHeat.cell + CGFloat(max(weeks - 1, 0)) * VisualHeat.spacing
    }

    /// 从产品视图源码读 `weekdayLabelWidth` 的**值**（它是 private，而判据要的是同一个数）。
    /// 读不到就红，不许在这里另写一个 18（那等于把"抄来的常量"再抄一遍）。
    private func productWeekdayLabelWidth() throws -> CGFloat {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift")
        let text = try String(contentsOf: url, encoding: .utf8)
        guard let hit = text.range(of: "weekdayLabelWidth: CGFloat \\{ \\d+ \\}", options: .regularExpression) else {
            XCTFail("读不到 `weekdayLabelWidth` 的定义形状 ⇒ 这条预算判据没有对象了（写法变了就去改这里，别放宽）")
            return -1
        }
        let digits = String(text[hit].filter { $0.isNumber })
        let value = CGFloat(Int(digits) ?? -1)
        XCTAssertGreaterThan(value, 0, "标签列宽解析成 \(digits) ⇒ 尺子读不到对象")
        return value
    }

    /// 从**夹具自己那几行**读组件帧宽与 padding，不写死 430/16：
    /// 写死的数字会在别人改夹具之后继续替旧决定作证。
    private func fixtureNumbers() throws -> (width: CGFloat, padding: CGFloat) {
        let harness = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let source = try String(contentsOf: harness, encoding: .utf8)
        guard let start = source.range(of: "Fixture(\"heatmap-populated\"") else {
            XCTFail("夹具 `heatmap-populated` 不见了 ⇒ 这条宽度预算没有对照对象（不许静默给绿）")
            return (0, 0)
        }
        let window = String(source[start.upperBound...].prefix(600))
        guard let widthHit = window.range(of: "width: \\d+", options: .regularExpression),
              let padHit = window.range(of: "\\.padding\\(\\d+\\)", options: .regularExpression) else {
            XCTFail("从夹具那几行读不出 width / padding ⇒ 尺子读不到对象：\(window.prefix(90))")
            return (0, 0)
        }
        let width = CGFloat(Int(String(window[widthHit].filter { $0.isNumber })) ?? 0)
        let padding = CGFloat(Int(String(window[padHit].filter { $0.isNumber })) ?? 0)
        XCTAssertGreaterThan(width, 0, "组件帧宽读成 0 ⇒ 后面全是在跟 0 比")
        XCTAssertGreaterThan(padding, 0, "padding 读成 0 ⇒ 可用宽被高估，预算假绿")
        return (width, padding)
    }

    func testComponentFrameAvailableWidthIsWhatTheFixtureItselfSays() throws {
        let numbers = try fixtureNumbers()
        XCTAssertEqual(numbers.width - 2 * numbers.padding, 398, accuracy: 0.001,
                       "组件帧可用宽不再是 398pt（读到 宽\(numbers.width) / padding \(numbers.padding)）"
                       + " ⇒ 下面那两条边界的理由要重读，别把 197 的账当还成立")
    }

    func testOneMoreWeekFitsAndTwoMoreDoesNot() throws {
        let numbers = try fixtureNumbers()
        let available = numbers.width - 2 * numbers.padding
        let used = gridWidth(weeks: DailyCopyHeatPolicy.defaultWindowWeeks)
        let plusOne = gridWidth(weeks: DailyCopyHeatPolicy.defaultWindowWeeks + 1)
        let plusTwo = gridWidth(weeks: DailyCopyHeatPolicy.defaultWindowWeeks + 2)
        XCTAssertLessThanOrEqual(used, available,
                                 "默认 \(DailyCopyHeatPolicy.defaultWindowWeeks) 周（\(used)pt）已顶破组件帧可用宽 \(available)pt"
                                 + " ⇒ 与 `contentMustFit` 一起红，先把窗口周数降下来")
        // 承重在这两条**边界**上，不在"周数是不是 26"上。
        XCTAssertLessThanOrEqual(plusOne, available,
                                 "多一周放不下（\(plusOne)pt > \(available)pt）⇒ 『加周数』这条修法已被组件帧否掉，"
                                 + "197 只剩『放大格子会动垂直节奏』那一条候选，别再留两条")
        XCTAssertGreaterThan(plusTwo, available,
                             "多两周仍然放得下（\(plusTwo)pt ≤ \(available)pt）⇒ 上限不是组件帧而是别的容器，"
                             + "这条判据问错了对象，要换成最小窗口那一档的实测（BACKLOG 200）")
        XCTAssertEqual(available - used, 19, accuracy: 0.001,
                       "余量变了（实到 \(available - used)pt，一周占 \(VisualHeat.cell + VisualHeat.spacing)pt）"
                       + " ⇒ 上面两条边界的理由已经换人，重新量了再写账")
    }

    /// 算式只准有一份：产品按偏移摆列，判据若把间距数成 N 条，两边会各说各话。
    func testGridWidthFormulaMatchesTheProductOffsets() throws {
        let label = try productWeekdayLabelWidth()
        let fromProductOffset = label
            + CGFloat(DailyCopyHeatPolicy.defaultWindowWeeks - 1) * (VisualHeat.cell + VisualHeat.spacing)
            + VisualHeat.cell
        XCTAssertEqual(gridWidth(weeks: DailyCopyHeatPolicy.defaultWindowWeeks), fromProductOffset,
                       accuracy: 0.001,
                       "两条算式分叉 ⇒ 判据量的不是产品画的那张图（去 `DailyCopyHeatmapView.monthLabelRow` 对齐写法）")
    }

    /// 令牌不许被测试自己重写：预算成立的前提是这几个数住在产品定义处。
    func testBudgetReadsTheProductTokens() throws {
        XCTAssertEqual(VisualHeat.spacing, 3, accuracy: 0.001,
                       "间距令牌变了 ⇒ 一周占的 14pt 与上面两条边界都要重算")
        XCTAssertEqual(VisualHeat.cell, 11, accuracy: 0.001,
                       "格宽令牌变了 ⇒ 197 那条『放大格子会动高度/节奏』的理由要重新量")
        XCTAssertGreaterThan(DailyCopyHeatPolicy.defaultWindowWeeks, 0)
    }
}
