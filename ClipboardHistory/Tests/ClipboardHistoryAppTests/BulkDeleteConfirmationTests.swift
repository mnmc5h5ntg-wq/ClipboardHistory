import XCTest
@testable import ClipboardHistoryApp

/// R517 / BACKLOG 619：批量删除必须先确认；取消/零选区都不删。
/// 纯策略用 fake confirmer 验收；另有一条源码接线守卫，确保侧栏真的走了这条策略。
@MainActor
final class BulkDeleteConfirmationTests: XCTestCase {
    private final class Recorder: DestructiveConfirming {
        struct Call: Equatable {
            let title: String
            let message: String
            let confirmTitle: String
            let cancelTitle: String
        }
        var calls: [Call] = []
        var answer = false
        func confirm(title: String, message: String,
                     confirmTitle: String, cancelTitle: String) -> Bool {
            calls.append(Call(title: title, message: message,
                              confirmTitle: confirmTitle, cancelTitle: cancelTitle))
            return answer
        }
    }

    func testCancelDoesNotConfirmAndNamesTheCount() {
        let recorder = Recorder()
        recorder.answer = false
        XCTAssertFalse(BulkDeleteConfirmation.confirm(count: 3, using: recorder))
        XCTAssertEqual(recorder.calls.count, 1)
        XCTAssertEqual(recorder.calls[0].title, "删除所选记录")
        XCTAssertTrue(recorder.calls[0].message.contains("3 条"),
                      "确认框必须说清将删几条：\(recorder.calls[0].message)")
        XCTAssertEqual(recorder.calls[0].confirmTitle, "删除")
        XCTAssertEqual(recorder.calls[0].cancelTitle, "取消")
    }

    func testOnlyAnExplicitConfirmReturnsTrue() {
        let recorder = Recorder()
        recorder.answer = true
        XCTAssertTrue(BulkDeleteConfirmation.confirm(count: 2, using: recorder))
        XCTAssertEqual(recorder.calls.count, 1)
    }

    func testZeroSelectionNeverAsksAndNeverDeletes() {
        let recorder = Recorder()
        recorder.answer = true
        XCTAssertFalse(BulkDeleteConfirmation.confirm(count: 0, using: recorder))
        XCTAssertEqual(recorder.calls.count, 0, "空选区不该弹确认框")
    }

    func testTheSidebarAsksBeforeTheBulkDelete() throws {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("../../Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
        let source = try String(contentsOf: url, encoding: .utf8)
        XCTAssertTrue(source.contains("BulkDeleteConfirmation.confirm("),
                      "侧栏的批量删除没有走确认策略")
        XCTAssertTrue(source.contains("using: SystemDestructiveConfirming()"),
                      "侧栏没有用系统确认框")
        XCTAssertEqual(source.components(separatedBy: "historyStore.perform(.deleteSelection)").count - 1, 1,
                       "删除调用必须只有一处，且在确认之后")
    }
}
