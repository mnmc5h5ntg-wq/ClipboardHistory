import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R435：浮层搜索框的清除按钮（有字才出现）。
@MainActor
final class QuickPickSearchClearButtonTests: XCTestCase {
    func testVisibilityIsATruthTable() {
        XCTAssertFalse(QuickPickController.showsClearButton(text: ""))
        XCTAssertTrue(QuickPickController.showsClearButton(text: "访达"))
        XCTAssertTrue(QuickPickController.showsClearButton(text: " "))
    }

    func testTheRealPanelButtonFollowsTheQuery() throws {
        _ = NSApplication.shared
        let store = UICaptureTests().makePopulatedStore()
        let controller = QuickPickController(historyStore: { store }, commit: { _ in })
        guard let panel = controller.windowForCapture(query: "访达"), let content = panel.contentView else {
            return XCTFail("浮层建不出来 ⇒ 这条判据没有对象")
        }
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        panel.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.15))
        defer { panel.orderOut(nil) }
        let buttons = Self.allSubviews(of: content).compactMap { $0 as? NSButton }
            .filter { $0.identifier?.rawValue == "quickPickClearSearchButton" }
        XCTAssertEqual(buttons.count, 1, "面板里应当恰好有一颗清除按钮，实际 \(buttons.count) 颗")
        guard let button = buttons.first else { return }
        XCTAssertFalse(button.isHidden, "查询非空时清除按钮仍是隐藏的 ⇒ 有字也清不掉")
        button.performClick(nil)
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        XCTAssertTrue(button.isHidden, "点过清除之后按钮没有收起来")
    }

    private static func allSubviews(of view: NSView) -> [NSView] {
        [view] + view.subviews.flatMap { allSubviews(of: $0) }
    }
}
