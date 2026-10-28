import XCTest
@testable import ClipboardHistoryApp

/// R469：跨年时间标注的纯策略 —— 参照是**当前列表最新一条**，不是挂钟。
///
/// 像素/字符串那一半在 `UICaptureTests.testCrossYearTimesCarryTheYear`：
/// 浮层两条只差一年的记录，旧行必须带「2025年」、新行保持紧凑。
/// 这里钉三件事：同年不加、跨年加、没有参照（直接构造的行夹具）不加。
final class TimestampYearPolicyTests: XCTestCase {
    private let calendar = Calendar(identifier: .gregorian)

    private func date(year: Int, month: Int = 6, day: Int = 15) -> Date {
        calendar.date(from: DateComponents(year: year, month: month, day: day))!
    }

    func testSameYearStaysCompact() {
        XCTAssertFalse(TimestampYearPolicy.showsYear(for: date(year: 2025),
                                                     relativeTo: date(year: 2025, month: 12, day: 31),
                                                     calendar: calendar))
    }

    func testDifferentYearAddsYear() {
        XCTAssertTrue(TimestampYearPolicy.showsYear(for: date(year: 2025),
                                                    relativeTo: date(year: 2026),
                                                    calendar: calendar))
        XCTAssertTrue(TimestampYearPolicy.showsYear(for: date(year: 2027),
                                                    relativeTo: date(year: 2026),
                                                    calendar: calendar))
    }

    func testNoReferenceKeepsCompact() {
        XCTAssertFalse(TimestampYearPolicy.showsYear(for: date(year: 2025),
                                                     relativeTo: nil,
                                                     calendar: calendar))
    }

    func testFormatterUsesYearOnlyAcrossTheBoundary() {
        let old = date(year: 2025), new = date(year: 2026)
        let compact = ClipboardDateFormatters.sidebarTime(for: old, reference: old)
        let withYear = ClipboardDateFormatters.sidebarTime(for: old, reference: new)
        XCTAssertFalse(compact.contains("年"), compact)
        XCTAssertTrue(withYear.contains("2025年"), withYear)
        XCTAssertEqual(ClipboardDateFormatters.sidebarTime(for: new, reference: new),
                       compact, "同一条时间在同一年参照下必须逐字相等")
    }
}
