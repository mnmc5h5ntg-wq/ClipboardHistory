// R415：QuickPick 搜索框的焦点边界接线（产品默认由真实第一响应者供，捕获键只给夹具）。
import XCTest
@testable import ClipboardHistoryApp

final class QuickPickSearchFocusTests: XCTestCase {

    func testFocusStateIsWiredIntoTheSearchBackdrop() throws {
        let source = codeOnly(try productSourceText(named: "Managers/QuickPickController.swift"))
        XCTAssertTrue(source.contains("var onFocusChange: ((Bool) -> Void)?"),
                      "字段没有焦点出口 ⇒ 面板打开后焦点边界永远不亮")
        XCTAssertTrue(source.contains("field.onFocusChange = {"),
                      "字段的焦点出口没有接到 backdrop ⇒ 边界永远收不到真正的焦点")
        XCTAssertTrue(source.contains("focusedForCapture"),
                      "backdrop 没有焦点取证键 ⇒ 焦点帧不存在")
        XCTAssertTrue(source.contains("(focusedForCapture ?? focused) || (hoveredForCapture ?? hovered)"),
                      "焦点没有进入 backdrop 的绘制前置条件")
        XCTAssertTrue(source.contains("if panel.makeFirstResponder(field)"),
                      "没有先证明字段真的拿到第一响应者 ⇒ 会画一个假焦点承诺")
        XCTAssertTrue(source.contains("searchBackdrop?.focused = true"),
                      "show() 没有点亮焦点")
        XCTAssertTrue(source.contains("searchBackdrop?.focused = false"),
                      "hide() 没有收回焦点")
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
        throw NSError(domain: "QuickPickSearchFocusTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
