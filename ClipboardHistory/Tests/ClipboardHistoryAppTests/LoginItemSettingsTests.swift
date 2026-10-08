import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class LoginItemSettingsTests: XCTestCase {
    func testSetEnabledUpdatesStateWhenManagerSucceeds() {
        let manager = FakeLoginItemManager(isSupported: true, isEnabled: false)
        let settings = LoginItemSettings(manager: manager)

        settings.setEnabled(true)

        XCTAssertEqual(settings.isEnabled, true)
        XCTAssertNil(settings.message)
        XCTAssertEqual(manager.requestedStates, [true])
    }

    func testSetEnabledRestoresManagerStateAndShowsMessageWhenManagerFails() {
        let manager = FakeLoginItemManager(isSupported: true, isEnabled: false)
        manager.error = NSError(domain: "LoginItemSettingsTests", code: 1)
        let settings = LoginItemSettings(manager: manager)

        settings.setEnabled(true)

        XCTAssertEqual(settings.isEnabled, false)
        XCTAssertEqual(settings.message, "开机启动开启失败，请稍后重试。")
    }

    func testUnsupportedManagerDisablesSettingWithMessage() {
        let settings = LoginItemSettings(
            manager: FakeLoginItemManager(isSupported: false, isEnabled: false)
        )

        XCTAssertFalse(settings.isSupported)
        XCTAssertFalse(settings.isEnabled)
        XCTAssertEqual(settings.message, "当前系统不支持从应用内设置开机启动。")
    }
}
