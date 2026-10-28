import XCTest
@testable import ClipboardHistoryApp

/// R444：主列表行的时间行 = `时间 · 来自 <来源 App>`（时间在前；来源 nil 只显示时间）。
///
/// 像素那一半在 `UICaptureTests.testHistoryRowsShowTheirSourceAppName`：
/// `sidebar-history` 第一行（Safari）与 `sidebar-no-source` 第一行同一段正文/时间，
/// 只差来源字段 ⇒ 时间行的墨宽差就是来源那一段的宽度。
final class HistoryRowSourceLineTests: XCTestCase {
    func testSourceIsAppendedAfterTheTime() {
        let line = HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: "Safari")
        XCTAssertEqual(line, "10月9日 16:52 · 来自 Safari")
        XCTAssertTrue(line.hasPrefix("10月9日 16:52"), "时间不在最前面 ⇒ 行宽不够时会先丢时间")
        XCTAssertTrue(line.hasSuffix("来自 Safari"))
    }

    func testMissingOrBlankSourceShowsOnlyTheTime() {
        XCTAssertEqual(HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: nil),
                       "10月9日 16:52")
        XCTAssertEqual(HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: ""),
                       "10月9日 16:52")
        XCTAssertEqual(HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: "  "),
                       "10月9日 16:52")
        XCTAssertEqual(HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: " 访达 "),
                       "10月9日 16:52 · 来自 访达", "来源两端的空白没有归一")
    }

    func testLongSourceStaysInTheStringAndIsLeftToTheLineTruncation() {
        let long = String(repeating: "很长的应用名", count: 8)
        let line = HistoryRowSourceLine.text(time: "10月9日 16:52", sourceAppName: long)
        XCTAssertTrue(line.contains(long), "策略层先截断来源 ⇒ 行里无法再按行宽决定截断点")
        XCTAssertTrue(line.hasPrefix("10月9日 16:52"))
    }
}
