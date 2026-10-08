import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R-20：`version` 字段以前只写不读，且"一次清掉几十条"这件事没有任何出口。
/// 这里锁住两条行为：更高版本的存档必须只读打开（不能被降级写回），
/// 以及成批按时间过期时必须告诉用户（单条常规过期不打扰）。
@MainActor
final class ArchiveVersionAndRetentionTests: XCTestCase {
    private func textEntry(_ text: String, at date: Date) -> ClipboardEntry {
        ClipboardEntry(content: .text(text), timestamp: date, thumbnail: nil, sourceURL: nil, sourceUTIs: [])
    }

    private func historyURL(in root: URL) -> URL { root.appendingPathComponent("history.json") }

    // MARK: - 版本闸门

    func testArchiveFromNewerVersionIsOpenedReadOnlyAndNeverRewritten() throws {
        let root = try makeTemporaryDirectory()
        let writer = FileHistoryPersistence(rootDirectory: root)
        try writer.save([textEntry("来自未来的一条", at: Date(timeIntervalSince1970: 1))])
        writer.flushPendingSaves()

        let url = historyURL(in: root)
        let original = try String(contentsOf: url, encoding: .utf8)
        let bumped = original.replacingOccurrences(of: "\"version\" : 1", with: "\"version\" : 99")
        XCTAssertNotEqual(bumped, original, "夹具没找到版本行 —— 这条测试本身没在测东西")
        try bumped.write(to: url, atomically: true, encoding: .utf8)

        let reopened = FileHistoryPersistence(rootDirectory: root)
        XCTAssertEqual(reopened.load().count, 1, "更高版本的存档仍应能读到记录")
        XCTAssertTrue(reopened.isArchiveFromNewerVersion)
        XCTAssertTrue(reopened.recoveryNotice?.contains("只读") == true,
                      "必须说明为什么这次不写盘：\(reopened.recoveryNotice ?? "nil")")

        try reopened.save([textEntry("本版本新增的一条", at: Date(timeIntervalSince1970: 2))])
        reopened.flushPendingSaves()

        let after = try String(contentsOf: url, encoding: .utf8)
        XCTAssertTrue(after.contains("\"version\" : 99"), "只读模式绝不能把更高版本的存档覆盖回 v1")
        XCTAssertFalse(after.contains("本版本新增的一条"), "只读期间不得写入新内容")
    }

    func testCurrentVersionArchiveStillWrites() throws {
        let root = try makeTemporaryDirectory()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save([textEntry("第一条", at: Date(timeIntervalSince1970: 1))])
        persistence.flushPendingSaves()

        let reopened = FileHistoryPersistence(rootDirectory: root)
        XCTAssertEqual(reopened.load().count, 1)
        XCTAssertFalse(reopened.isArchiveFromNewerVersion)
        XCTAssertNil(reopened.recoveryNotice)

        try reopened.save([textEntry("第二条", at: Date(timeIntervalSince1970: 2))])
        reopened.flushPendingSaves()
        let after = try String(contentsOf: historyURL(in: root), encoding: .utf8)
        XCTAssertTrue(after.contains("第二条"), "正常版本必须照旧写盘，闸门不能变成常闭")
    }

    // MARK: - 过期报告

    func testMassAgeExpiryTellsTheUser() throws {
        let root = try makeTemporaryDirectory()
        let writer = FileHistoryPersistence(rootDirectory: root)
        let longAgo = Date().addingTimeInterval(-41 * 86_400)
        try writer.save((0..<12).map { textEntry("旧记录 \($0)", at: longAgo.addingTimeInterval(Double($0))) })
        writer.flushPendingSaves()

        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: root),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 500, maxAgeDays: 30)
        )
        XCTAssertEqual(store.entries.count, 0, "41 天的记录按 30 天策略本就该清掉 —— 报告不等于不执行")
        XCTAssertTrue(store.retentionNotice?.contains("12") == true,
                      "一次清掉 12 条要说明数量：\(store.retentionNotice ?? "nil")")
        XCTAssertTrue(store.retentionNotice?.contains("系统时间") == true)
        store.dismissRetentionNotice()
        XCTAssertNil(store.retentionNotice)
    }

    func testRoutineSingleExpiryDoesNotNag() throws {
        let root = try makeTemporaryDirectory()
        let writer = FileHistoryPersistence(rootDirectory: root)
        let now = Date()
        try writer.save([
            textEntry("还新鲜的", at: now.addingTimeInterval(-60)),
            textEntry("也新鲜", at: now.addingTimeInterval(-120)),
            textEntry("刚过期的", at: now.addingTimeInterval(-31 * 86_400)),
        ])
        writer.flushPendingSaves()

        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: FileHistoryPersistence(rootDirectory: root),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 500, maxAgeDays: 30)
        )
        XCTAssertEqual(store.entries.count, 2, "过期那条应被移除")
        XCTAssertNil(store.retentionNotice, "常规的一条一条过期不该弹提示，否则用户会忽略真正的异常")
    }
}
