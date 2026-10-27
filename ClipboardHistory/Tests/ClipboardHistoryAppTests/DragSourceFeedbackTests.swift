// R427：拖拽源反馈 —— onDrag 登记、行内容降透明度、鼠标松开发起清零。
// 像素正/负两臂在 UICaptureHarness 的 row-favorite-off / row-drag-source-active。
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class DragSourceFeedbackTests: XCTestCase {

    func testStateTracksTheDraggingEntryAndClearsOnMouseUp() {
        var state = DragSourceFeedbackState()
        let first = UUID()
        let second = UUID()
        XCTAssertFalse(state.isDragging(first))
        state.begin(first)
        XCTAssertTrue(state.isDragging(first))
        XCTAssertFalse(state.isDragging(second))
        state.tick(mouseButtons: 1)
        XCTAssertTrue(state.isDragging(first), "鼠标仍按着，不能清")
        state.tick(mouseButtons: 0)
        XCTAssertFalse(state.isDragging(first), "松开鼠标必须清掉拖拽源")
        state.begin(second)
        XCTAssertTrue(state.isDragging(second))
        state.end()
        XCTAssertFalse(state.isDragging(second))
    }

    func testControllerPublishesBeginAndEnd() {
        let controller = DragSourceFeedback()
        let id = UUID()
        controller.begin(id)
        XCTAssertTrue(controller.state.isDragging(id))
        controller.end()
        XCTAssertFalse(controller.state.isDragging(id))
    }

    func testOnDragRegistersTheSourceAndTheRowConsumesIt() throws {
        let drag = codeOnly(try productSource(named: "Utilities/EntryDrag.swift"))
        XCTAssertTrue(drag.contains("DragSourceFeedback.shared.beginAfterDelay(entryID)"),
                      "onDrag 没有登记拖拽源 ⇒ 行永远不会变暗")
        XCTAssertTrue(drag.contains("content.onDrag {"),
                      "登记不在 onDrag 里 ⇒ 拖起来之前就会暗")

        let row = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        XCTAssertTrue(row.contains("EntryDragModifier(entryID: entry.id, content: entry.content)"),
                      "行没有把 entry.id 交给拖拽 modifier")
        XCTAssertTrue(row.contains("draggingEntryIDForCapture"),
                      "行没有读取证键 ⇒ 帧里画不出拖拽源态")
        XCTAssertTrue(row.contains("DragSourceFeedback.dimOpacity"),
                      "行没有用统一的降透明度值")

        let feedback = codeOnly(try productSource(named: "Utilities/DragSourceFeedback.swift"))
        XCTAssertTrue(feedback.contains("RunLoop.main.add(timer, forMode: .common)"),
                      "轮询没有挂在 .common 模式 ⇒ 拖拽 tracking 模式下会停")
        XCTAssertTrue(feedback.contains("NSEvent.pressedMouseButtons"),
                      "没有读真实鼠标键 ⇒ 拖拽结束无法判定")
        XCTAssertTrue(feedback.contains("beginAfterDelay"),
                      "没有延迟入口 ⇒ 系统拖拽预览会拍到变暗的行")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "DragSourceFeedbackTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
