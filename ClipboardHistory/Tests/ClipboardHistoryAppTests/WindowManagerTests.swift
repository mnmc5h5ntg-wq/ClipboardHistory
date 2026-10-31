import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class WindowManagerTests: XCTestCase {
    func testAppContentWindowRequiresStableMainWindowIdentifier() {
        let window = NSWindow()
        window.identifier = WindowManager.mainWindowIdentifier

        XCTAssertTrue(WindowManager.isAppContentWindow(window))
    }

    func testAppContentWindowRejectsWindowWithoutMainIdentifier() {
        let window = NSWindow()
        window.identifier = NSUserInterfaceItemIdentifier("OtherWindow")

        XCTAssertFalse(WindowManager.isAppContentWindow(window))
    }

    func testAppContentWindowRejectsPanelsEvenWithMainIdentifier() {
        let panel = NSPanel()
        panel.identifier = WindowManager.mainWindowIdentifier

        XCTAssertFalse(WindowManager.isAppContentWindow(panel))
    }

    /// R522：没有装工厂时不许凭空造窗口（WindowManager 不认识视图层）。
    /// 产品那条「无窗口就创建唯一一个」的路由 `MainWindowCreationTests` 从 AppDelegate 入口测。
    func testShowMainWindowDoesNotCreateWithoutAnInstalledFactory() {
        WindowManager.uninstallMainWindowFactoryForTesting()
        let existingMainWindowCount = NSApplication.shared.windows.filter {
            WindowManager.isAppContentWindow($0)
        }.count

        WindowManager.showMainWindow()

        let currentMainWindowCount = NSApplication.shared.windows.filter {
            WindowManager.isAppContentWindow($0)
        }.count
        XCTAssertEqual(currentMainWindowCount, existingMainWindowCount)
    }
}
