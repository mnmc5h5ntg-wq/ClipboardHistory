// R419：热图汇总行的数字滚动 —— 纯 policy 与源接线。
// 像素在 UICaptureHarness 的 heatmap-summary-before/after；
// 过程在 MotionFilmstripTests 的 heat-summary-number-change 场景里判。
import XCTest
@testable import ClipboardHistoryApp

final class HeatmapSummaryTransitionTests: XCTestCase {

    @MainActor
    func testSummaryLineMovesWhenTheTotalCrossesADigitBoundary() {
        let today = UICaptureTests.heatmapFixtureToday
        let calendar = UICaptureTests.heatmapFixtureCalendar()
        let todayKey = DailyCopyHeatPolicy.dayKey(for: today, calendar: calendar)
        var after = [todayKey: 999]
        if let yesterday = calendar.date(byAdding: .day, value: -1, to: today) {
            after[DailyCopyHeatPolicy.dayKey(for: yesterday, calendar: calendar)] = 1
        }
        func line(_ counts: [String: Int]) -> String {
            let weeks = DailyCopyHeatPolicy.weeks(counts: counts, endingOn: today, calendar: calendar)
            let summary = DailyCopyHeatPolicy.summary(counts: counts, weeks: weeks,
                                                      today: today, calendar: calendar)
            return DailyCopyHeatPolicy.summaryLine(for: summary, hasRecords: !counts.isEmpty) ?? ""
        }
        XCTAssertTrue(line([todayKey: 999]).contains("共 999 次"))
        XCTAssertTrue(line(after).contains("共 1000 次"),
                      "跨位数后总数没有变 ⇒ 这条判据没有对象")
        XCTAssertNotEqual(line([todayKey: 999]), line(after))
    }

    func testSummaryUsesTheNumericTransitionAndItsOwnAnimation() throws {
        let source = codeOnly(try productSourceText(named: "Views/DailyCopyHeatmapView.swift"))
        XCTAssertTrue(source.contains("summaryText(line)"),
                      "header 没有走 summaryText ⇒ 数字还是硬换")
        XCTAssertTrue(source.contains(".contentTransition(.numericText())"),
                      "没有数字滚动 ⇒ 999→1000 会整行跳")
        XCTAssertTrue(source.contains(".animation(MotionCatalog.animation(for: .contentFade), value: line)"),
                      "数字滚动没有事务 ⇒ contentTransition 不会演")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "HeatmapSummaryTransitionTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
