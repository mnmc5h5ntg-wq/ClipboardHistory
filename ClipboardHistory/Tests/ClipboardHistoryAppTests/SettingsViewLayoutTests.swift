import XCTest
@testable import ClipboardHistoryApp

final class SettingsViewLayoutTests: XCTestCase {
    func testSettingsClearButtonUsesShortDestructiveLabel() {
        XCTAssertEqual(SettingsViewLayout.clearButtonTitle, "清空")
    }

    func testSettingsWindowDefaultWidthKeepsHotKeyRowsComfortable() {
        XCTAssertGreaterThanOrEqual(SettingsViewLayout.windowContentSize.width, 720)
        XCTAssertGreaterThanOrEqual(SettingsViewLayout.minimumWindowSize.width, 640)
    }
}
