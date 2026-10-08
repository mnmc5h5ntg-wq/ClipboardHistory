import XCTest
@testable import ClipboardHistoryApp

final class WindowChromeLayoutTests: XCTestCase {
    func testTrafficLightOriginUsesNativeCornerInset() {
        let origin = WindowChromeLayout.trafficLightOrigin(titlebarHeight: 52, buttonHeight: 14)

        XCTAssertEqual(origin.x, 21)
        XCTAssertEqual(origin.y, 19)
    }

    func testTrafficLightOriginDoesNotStickToWindowCornerBeforeTitlebarSettles() {
        let origin = WindowChromeLayout.trafficLightOrigin(titlebarHeight: 20, buttonHeight: 14)

        XCTAssertEqual(origin.x, 21)
        XCTAssertEqual(origin.y, WindowChromeLayout.trafficLightMinimumBottomInset)
    }
}
