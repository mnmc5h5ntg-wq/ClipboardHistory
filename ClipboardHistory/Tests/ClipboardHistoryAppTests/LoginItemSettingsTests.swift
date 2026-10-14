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

    // MARK: - R39：macOS 12 那条 AppleScript 路径以前**静默失败**

    /// 真值表：写完读回。四格都要，因为"没生效"有两个方向（该在的不在 / 该没的还在），
    /// 而只测一个方向的话，把比较写成 `if !applied { throw }` 这种半只眼的实现不会红。
    func testVerifyAppliedTruthTable() {
        XCTAssertNoThrow(try SystemLoginItemManager.verifyApplied(enabled: true) { true })
        XCTAssertNoThrow(try SystemLoginItemManager.verifyApplied(enabled: false) { false })
        XCTAssertThrowsError(try SystemLoginItemManager.verifyApplied(enabled: true) { false }) { error in
            guard case LoginItemSettings.Error.loginItemNotApplied = error else {
                return XCTFail("要的是 loginItemNotApplied，实际 \(error)")
            }
        }
        XCTAssertThrowsError(try SystemLoginItemManager.verifyApplied(enabled: false) { true }) { error in
            guard case LoginItemSettings.Error.loginItemNotApplied = error else {
                return XCTFail("删除没生效也要报同一个错，实际 \(error)")
            }
        }
    }

    /// 管线级（产品入口 = `LoginItemSettings.setEnabled`）：
    /// 底层"脚本没报错但也没生效"时，用户必须看到那句回执，而且开关不许停在"看起来开了"。
    /// 这一格是 R39 的真正动机：修之前 macOS 12 上这条路径**一个字节都不说**，
    /// 用户看到的是开关自己弹回去。
    func testSilentAppleScriptFailureSurfacesTheReceipt() {
        let manager = FakeLoginItemManager(isSupported: true, isEnabled: false)
        manager.error = LoginItemSettings.Error.loginItemNotApplied
        let settings = LoginItemSettings(manager: manager)

        settings.setEnabled(true)

        XCTAssertEqual(settings.isEnabled, false,
                       "失败时开关必须停在 off —— 停在 on 就是在撒谎")
        XCTAssertEqual(settings.message, "开机启动开启失败，请稍后重试。",
                       "以前这条路径什么都不说 ⇒ 那句「按了没反应」只能靠用户自己猜")
    }

    /// 那句回执**必须被画出来**：视图里它是 `if let message = loginItemSettings.message`，
    /// 所以只要 message 非空就该有字。这条由帧判（`settings-general-login-failed`），
    /// 这里只钉"夹具确实把 message 造出来了"—— 否则帧判的是 nil，绿得毫无意义。
    func testCaptureFixtureActuallyProducesTheReceipt() throws {
        let manager = FakeLoginItemManager(isSupported: true, isEnabled: false)
        manager.error = LoginItemSettings.Error.loginItemNotApplied
        let settings = LoginItemSettings(manager: manager)
        settings.setEnabled(true)
        XCTAssertNotNil(settings.message)
    }
}
