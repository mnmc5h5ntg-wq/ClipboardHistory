import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 不覆盖管线：这里是 `HistoryRowMatchHighlight` 的纯函数契约（切分位置、只标来源名不标时间），
/// 管线级证人在 `UICaptureTests.testSidebarSearchRowsShowWhyTheyMatched`（同一帧里数黄像素落在哪条文字带）。
final class HistoryRowMatchHighlightTests: XCTestCase {
    private func highlightedRuns(_ attributed: AttributedString) -> [String] {
        attributed.runs.compactMap { run in
            run.backgroundColor == nil ? nil : String(attributed[run.range].characters)
        }
    }

    func testHighlightsEveryVisibleMatch() {
        let attributed = HistoryRowMatchHighlight.highlighted(
            "这是一段用于视觉验收的普通文本记录", query: "视觉验收")
        XCTAssertEqual(String(attributed.characters), "这是一段用于视觉验收的普通文本记录",
                       "高亮不许改动可见文字")
        XCTAssertEqual(highlightedRuns(attributed), ["视觉验收"],
                       "命中片段必须是查询那一段，且只标一次")
    }

    func testEmptyQueryLeavesTextPlain() {
        let attributed = HistoryRowMatchHighlight.highlighted("这是一段文本", query: "")
        XCTAssertEqual(String(attributed.characters), "这是一段文本")
        XCTAssertEqual(highlightedRuns(attributed), [], "空查询不许退化成全文高亮")
    }

    func testNoMatchLeavesTextPlain() {
        let attributed = HistoryRowMatchHighlight.highlighted("这是一段文本", query: "不存在的词")
        XCTAssertEqual(String(attributed.characters), "这是一段文本")
        XCTAssertEqual(highlightedRuns(attributed), [])
    }

    func testCaseInsensitiveHighlightMatchesTheFilter() {
        let attributed = HistoryRowMatchHighlight.highlighted("来自 Safari 的文本", query: "SAFARI")
        XCTAssertEqual(highlightedRuns(attributed), ["Safari"],
                       "过滤是大小写不敏感的，高亮必须同一套语义")
    }

    func testSourceLineHighlightsOnlyTheAppName() {
        let attributed = HistoryRowMatchHighlight.sourceLine(
            time: "12:34", sourceAppName: "Safari", query: "Safari")
        XCTAssertEqual(String(attributed.characters), "12:34 · 来自 Safari")
        XCTAssertEqual(highlightedRuns(attributed), ["Safari"],
                       "来源行只标 App 名；时间不是搜索字段，不许跟着亮")
    }

    func testSourceLineNeverHighlightsTheTime() {
        let attributed = HistoryRowMatchHighlight.sourceLine(
            time: "12:34", sourceAppName: "Safari", query: "12:34")
        XCTAssertEqual(String(attributed.characters), "12:34 · 来自 Safari")
        XCTAssertEqual(highlightedRuns(attributed), [],
                       "查询只出现在时间上时不许标 —— 时间不参与过滤")
    }

    func testSourceLineWithoutANameKeepsTheTimeOnly() {
        let attributed = HistoryRowMatchHighlight.sourceLine(
            time: "12:34", sourceAppName: "   ", query: "12")
        XCTAssertEqual(String(attributed.characters), "12:34")
        XCTAssertEqual(highlightedRuns(attributed), [])
    }
}
