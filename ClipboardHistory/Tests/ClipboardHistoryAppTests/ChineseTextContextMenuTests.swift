import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class ChineseTextContextMenuTests: XCTestCase {
    func testReadOnlyMenuUsesChineseSelectionItemsOnly() {
        let menu = ChineseTextContextMenu.makeReadOnlyMenu()

        XCTAssertEqual(menu.visibleTitles, ["复制", "全选", "查找…"])
        XCTAssertFalse(menu.visibleTitles.contains("剪切"))
        XCTAssertFalse(menu.visibleTitles.contains("粘贴"))
        XCTAssertFalse(menu.visibleTitles.contains("Services"))
        XCTAssertFalse(menu.visibleTitles.contains("Show All Tabs"))
        XCTAssertFalse(menu.allowsContextMenuPlugIns)
    }

    @MainActor
    func testSearchTextFieldDisablesContextMenuWithoutReplacingStandardFieldEditor() {
        let textField = ChineseMenuTextField()
        let event = rightClickEvent()

        XCTAssertNil(textField.menu(for: event))
        XCTAssertNil(textField.cell?.fieldEditor(for: textField))
    }

    @MainActor
    func testSelectableTextViewUsesCustomChineseMenuAndVisibleSelectionStyle() {
        let textView = ChineseSelectableNSTextView()
        let event = rightClickEvent()

        textView.string = "预览文本"

        XCTAssertEqual(textView.string, "预览文本")
        XCTAssertNotNil(textView.textStorage)
        XCTAssertEqual(textView.menu(for: event)?.visibleTitles, ["复制", "全选", "查找…"])
        XCTAssertFalse(textView.menu(for: event)?.visibleTitles.contains("Services") ?? true)
        XCTAssertFalse(textView.menu(for: event)?.allowsContextMenuPlugIns ?? true)
        XCTAssertEqual(
            textView.selectedTextAttributes[.backgroundColor] as? NSColor,
            NSColor.selectedTextBackgroundColor
        )
        XCTAssertEqual(
            textView.selectedTextAttributes[.foregroundColor] as? NSColor,
            NSColor.selectedTextColor
        )
    }

    private func rightClickEvent() -> NSEvent {
        NSEvent.mouseEvent(
            with: .rightMouseDown,
            location: .zero,
            modifierFlags: [],
            timestamp: 0,
            windowNumber: 0,
            context: nil,
            eventNumber: 0,
            clickCount: 1,
            pressure: 1
        )!
    }
}

private extension NSMenu {
    var visibleTitles: [String] {
        items
            .filter { !$0.isSeparatorItem }
            .map(\.title)
    }
}
