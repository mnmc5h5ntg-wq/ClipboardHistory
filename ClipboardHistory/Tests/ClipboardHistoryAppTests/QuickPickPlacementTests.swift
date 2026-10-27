// R421：快速选择面板的落点 —— 纯策略 + 真 NSPanel 的 frame + 源接线。
// 以前面板建在 (0,0) 就再也没动过：那是屏幕左下角，常常压在 Dock 上；
// 窗口位置不进任何内容帧，所以这一格一直没被看过。
import XCTest
@testable import ClipboardHistoryApp

final class QuickPickPlacementTests: XCTestCase {

    func testCentersInsideTheVisibleFrame() {
        // 有菜单栏（y=25）与 Dock 的 1440×830 可见区。
        let origin = QuickPickPlacement.origin(
            panelSize: CGSize(width: 420, height: 300),
            visibleFrame: CGRect(x: 0, y: 25, width: 1440, height: 830))
        XCTAssertEqual(origin.x, 510, accuracy: 0.001)
        XCTAssertEqual(origin.y, 25 + (830 - 300) / 2, accuracy: 0.001)
    }

    func testKeepsTheSecondScreenOffset() {
        let origin = QuickPickPlacement.origin(
            panelSize: CGSize(width: 420, height: 300),
            visibleFrame: CGRect(x: 1600, y: 25, width: 1280, height: 800))
        XCTAssertEqual(origin.x, 1600 + (1280 - 420) / 2, accuracy: 0.001)
        XCTAssertEqual(origin.y, 25 + (800 - 300) / 2, accuracy: 0.001)
    }

    func testSmallRoomAnchorsAtTheVisibleOriginInsteadOfNegative() {
        let origin = QuickPickPlacement.origin(
            panelSize: CGSize(width: 420, height: 300),
            visibleFrame: CGRect(x: 0, y: 0, width: 300, height: 200))
        XCTAssertEqual(origin, .zero,
                       "房间比面板还小时，面板必须从可见原点开始，不许跑到负坐标（菜单栏/Dock 外）")
    }

    func testZeroRoomFallsBackToTheOrigin() {
        XCTAssertEqual(QuickPickPlacement.origin(visibleFrame: .zero), .zero)
    }

    @MainActor
    func testShowPlacesTheRealPanelBeforeOrderingFront() throws {
        let controller = QuickPickController(historyStore: { nil }, commit: { _ in })
        let panel = try XCTUnwrap(controller.windowForCapture(query: ""),
                                  "建不出面板 ⇒ 这一格没有对象")
        let before = panel.frame.origin
        let visible = CGRect(x: 100, y: 50, width: 800, height: 600)
        controller.placePanel(in: visible)
        let expected = QuickPickPlacement.origin(panelSize: panel.frame.size, visibleFrame: visible)
        let after = panel.frame.origin
        let oldX = Int(before.x), oldY = Int(before.y)
        let newX = Int(after.x), newY = Int(after.y)
        let expectedX = Int(expected.x), expectedY = Int(expected.y)
        let visibleW = Int(visible.width), visibleH = Int(visible.height)
        let panelW = Int(panel.frame.width), panelH = Int(panel.frame.height)
        CaptureReadings.emit("PANEL_ORIGIN 旧=(\(oldX),\(oldY)) 新=(\(newX),\(newY)) "
                             + "期望=(\(expectedX),\(expectedY)) 可见=\(visibleW)x\(visibleH) "
                             + "面板=\(panelW)x\(panelH)")
        XCTAssertEqual(after.x, expected.x, accuracy: 0.5,
                       "面板没有落到策略给的 x（旧原点 \(before.x)）⇒ 落点没接上")
        XCTAssertEqual(after.y, expected.y, accuracy: 0.5,
                       "面板没有落到策略给的 y（旧原点 \(before.y)）⇒ 落点没接上")
    }

    func testShowUsesThePlacementBeforeOrderingFront() throws {
        let source = codeOnly(try productSourceText(named: "Managers/QuickPickController.swift"))
        guard let showStart = source.range(of: "func show()"),
              // 不能用 `screenForPresentation` 当结束针：show() 里那一句
              // `screenForPresentation?.visibleFrame` 会先命中，把 if 体截掉。
              let showEnd = source.range(of: "private var screenForPresentation") else {
            return XCTFail("读不到 show() 段 ⇒ 这条接线判据没有对象")
        }
        let show = String(source[showStart.lowerBound..<showEnd.lowerBound])
        XCTAssertTrue(show.contains("screenForPresentation?.visibleFrame"),
                      "show() 没读可见屏幕（菜单栏/Dock 之外）")
        guard let place = show.range(of: "placePanel(in:"),
              let order = show.range(of: "makeKeyAndOrderFront(nil)") else {
            return XCTFail("show() 里读不到 placePanel 或出场的先后 ⇒ 没有对象")
        }
        XCTAssertTrue(place.lowerBound < order.lowerBound,
                      "面板先出场再落点 ⇒ 用户会看到它从 (0,0) 跳一下")
        let screenStart = try XCTUnwrap(source.range(of: "screenForPresentation: NSScreen?"))
        let screenEnd = try XCTUnwrap(source.range(of: "func placePanel", range: screenStart.upperBound..<source.endIndex))
        let screen = String(source[screenStart.lowerBound..<screenEnd.lowerBound])
        XCTAssertTrue(screen.contains("NSEvent.mouseLocation"),
                      "屏幕没有优先取鼠标所在那一块 ⇒ 多屏时会开在另一块屏")
        XCTAssertTrue(screen.contains("NSScreen.main"),
                      "取不到鼠标屏幕时没有退回主屏")
        let placeStart = try XCTUnwrap(source.range(of: "func placePanel"))
        let placeEnd = try XCTUnwrap(source.range(of: "windowForCapture", range: placeStart.upperBound..<source.endIndex))
        let placeBody = String(source[placeStart.lowerBound..<placeEnd.lowerBound])
        XCTAssertTrue(placeBody.contains("QuickPickPlacement.origin(panelSize:"),
                      "placePanel 没有走纯策略 ⇒ 测试与产品会各算一份")
        XCTAssertTrue(placeBody.contains("panel.frame.size"),
                      "placePanel 没有用真实面板尺寸 ⇒ 换尺寸时落点会错")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "QuickPickPlacementTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
