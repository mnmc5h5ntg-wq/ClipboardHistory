import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R450：已完成任务项的文字弱化。
///
/// 像素那一半在 `UICaptureTests.testCheckedTasksDimTheirText`：两条逐字相同的任务项，
/// 勾选行在亮档更亮、暗档更暗（差 ≥20）。这里钉的是帧上读不出的两件事：
/// ① 只有 `.checked` 才弱化；② 属性串里两行的文字色确实不同，而 `☑`/`☐` 标记还在。
@MainActor
final class TaskItemPresentationTests: XCTestCase {
    func testOnlyCheckedTasksDimTheirText() {
        XCTAssertTrue(TaskItemPresentation.dimsText(.checked))
        XCTAssertFalse(TaskItemPresentation.dimsText(.unchecked))
        XCTAssertFalse(TaskItemPresentation.dimsText(nil))
    }

    func testCheckedRunColorDiffersFromUnchecked() {
        let document = MarkdownParser.parse("甲\n\n- [x] 乙\n- [ ] 乙")
        let storage = MarkdownPresentation.attributedString(for: document)
        let text = storage.string as NSString
        let first = text.range(of: "乙")
        let second = text.range(of: "乙", options: [], range: NSRange(location: first.location + first.length,
                                                                    length: text.length - first.location - first.length))
        XCTAssertNotEqual(first.location, NSNotFound)
        XCTAssertNotEqual(second.location, NSNotFound)
        guard first.location != NSNotFound, second.location != NSNotFound else { return }
        let checkedColor = storage.attribute(.foregroundColor, at: first.location, effectiveRange: nil) as? NSColor
        let uncheckedColor = storage.attribute(.foregroundColor, at: second.location, effectiveRange: nil) as? NSColor
        XCTAssertNotNil(checkedColor)
        XCTAssertNotNil(uncheckedColor)
        guard let checkedColor, let uncheckedColor else { return }
        XCTAssertFalse(checkedColor.isEqual(uncheckedColor),
                       "勾选/未勾选两行的正文颜色相同 ⇒ 完成态只落在标记上")
    }

    func testTaskMarkersAndVisibleTextAreUnchanged() {
        let document = MarkdownParser.parse("- [x] 乙\n- [ ] 乙")
        let storage = MarkdownPresentation.attributedString(for: document)
        XCTAssertTrue(storage.string.contains("☑"), "完成标记被弱化逻辑吃掉了")
        XCTAssertTrue(storage.string.contains("☐"), "未完成标记被弱化逻辑吃掉了")
        XCTAssertEqual(document.visibleText, "乙\n乙", "可见文字契约不该把标记或颜色算进内容")
    }
}
