import XCTest
@testable import ClipboardHistoryApp

final class QuickCopyMenuTests: XCTestCase {
    func testSectionsIncludeRecentAndFavoriteEntriesWithLimit() {
        let entries = [
            makeClipboardEntry(content: .text("one"), timestamp: Date(timeIntervalSince1970: 4)),
            makeClipboardEntry(content: .text("two"), timestamp: Date(timeIntervalSince1970: 3), isFavorite: true),
            makeClipboardEntry(content: .text("three"), timestamp: Date(timeIntervalSince1970: 2)),
            makeClipboardEntry(content: .text("four"), timestamp: Date(timeIntervalSince1970: 1), isFavorite: true)
        ]

        let sections = QuickCopyMenu.sections(entries: entries, limit: 2)

        XCTAssertEqual(sections.map(\.title), ["最近复制", "收藏"])
        XCTAssertEqual(sections[0].entries.map(\.content), [.text("one"), .text("two")])
        XCTAssertEqual(sections[1].entries.map(\.content), [.text("two"), .text("four")])
    }

    func testSectionsOmitEmptyGroups() {
        XCTAssertTrue(QuickCopyMenu.sections(entries: []).isEmpty)

        let sections = QuickCopyMenu.sections(entries: [
            makeClipboardEntry(content: .text("one"))
        ])

        XCTAssertEqual(sections.map(\.title), ["最近复制"])
    }
}
