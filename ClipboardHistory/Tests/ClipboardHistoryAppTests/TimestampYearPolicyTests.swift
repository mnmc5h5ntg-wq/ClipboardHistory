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

    /// R509：详情头的时间戳与列表用同一种日期语言（年月日），不是 ISO 短横线。
    func testDetailTimestampUsesTheSameDateLanguageAsTheList() {
        let at = calendar.date(from: DateComponents(year: 2026, month: 10, day: 30,
                                                    hour: 21, minute: 9, second: 55))!
        let detail = ClipboardDateFormatters.detailTimestamp.string(from: at)
        let list = ClipboardDateFormatters.sidebarTimeWithYear.string(from: at)
        XCTAssertEqual(detail, "2026年10月30日 21:09:55", detail)
        XCTAssertEqual(list, "2026年10月30日 21:09", list)
        XCTAssertFalse(detail.contains("-"), "详情时间戳又回到 ISO 短横线语言：\(detail)")
        XCTAssertFalse(list.contains("-"), "列表时间戳又回到 ISO 短横线语言：\(list)")
    }

    /// R510：详情头沿用列表的年份策略 —— 同年省年、跨年带年，秒始终保留。
    func testDetailTimestampUsesTheYearPolicyLikeTheList() {
        let at = calendar.date(from: DateComponents(year: 2026, month: 10, day: 30,
                                                    hour: 21, minute: 9, second: 55))!
        let sameYear = calendar.date(from: DateComponents(year: 2026, month: 12, day: 1))!
        let nextYear = calendar.date(from: DateComponents(year: 2027, month: 1, day: 1))!
        let compact = ClipboardDateFormatters.detailTimestamp(for: at, reference: sameYear)
        let withYear = ClipboardDateFormatters.detailTimestamp(for: at, reference: nextYear)
        XCTAssertEqual(compact, "10月30日 21:09:55", compact)
        XCTAssertEqual(withYear, "2026年10月30日 21:09:55", withYear)
        XCTAssertFalse(compact.contains("年"), compact)
        XCTAssertTrue(withYear.hasPrefix("2026年"), withYear)
        XCTAssertTrue(compact.contains(":55") && withYear.contains(":55"), "秒必须保留")
    }

    /// R511（615 结案）：最窄一档只留到分钟 —— 秒让位，分钟与来源完整，年份策略不变。
    func testDetailMinuteTimestampDropsSecondsButKeepsTheYearPolicy() {
        let at = calendar.date(from: DateComponents(year: 2026, month: 10, day: 30,
                                                    hour: 21, minute: 9, second: 55))!
        let sameYear = calendar.date(from: DateComponents(year: 2026, month: 12, day: 1))!
        let nextYear = calendar.date(from: DateComponents(year: 2027, month: 1, day: 1))!
        let compact = ClipboardDateFormatters.detailTimestampMinute(for: at, reference: sameYear)
        let withYear = ClipboardDateFormatters.detailTimestampMinute(for: at, reference: nextYear)
        XCTAssertEqual(compact, "10月30日 21:09", compact)
        XCTAssertEqual(withYear, "2026年10月30日 21:09", withYear)
        XCTAssertFalse(compact.contains(":55"), "分钟档不许再带秒：\(compact)")
        XCTAssertFalse(withYear.contains(":55"), "分钟档不许再带秒：\(withYear)")
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
