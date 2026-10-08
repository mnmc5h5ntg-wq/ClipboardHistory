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

    func testShowMainWindowDoesNotCreateFallbackMainWindow() {
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
