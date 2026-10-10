import XCTest
@testable import ClipboardHistoryApp

/// C-4 的产品侧那一半：运行时启动冒烟测试要把 app 真启一次，而**绝不**碰用户的真存档。
/// 隔离靠一个环境变量，所以这个文件钉住它真的被听进去了 ——
/// 没有这条判据，冒烟脚本可能一路写到 `~/Library/Application Support/时间剪史/` 而没人发现
/// （D-002 的边界：那是用户的数据，不是测试的临时目录）。
@MainActor
final class Round3LaunchIsolationTests: XCTestCase {
    private let key = FileHistoryPersistence.dataDirectoryEnvironmentKey

    private func withEnvironment<T>(_ value: String?, body: () throws -> T) rethrows -> T {
        if let value {
            setenv(key, value, 1)
        } else {
            unsetenv(key)
        }
        defer { unsetenv(key) }
        return try body()
    }

    func testOverrideIsHonouredAndFallsBackToTheRealDirectory() throws {
        let temporary = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("smoke-isolation-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: temporary) }

        withEnvironment(temporary.path) {
            XCTAssertEqual(FileHistoryPersistence.defaultRootDirectory().resolvingSymlinksInPath(),
                           temporary.resolvingSymlinksInPath(),
                           "设了 CLIPBOARD_HISTORY_DATA_DIR 却没有生效：冒烟测试会写到用户的真存档上")
        }

        // 不设的时候必须**回到原样**：这个开关不许影响正常用户
        let fallback = withEnvironment(nil) { FileHistoryPersistence.defaultRootDirectory() }
        XCTAssertTrue(fallback.path.hasSuffix("时间剪史"),
                      "没设环境变量时根目录不再是产品目录：\(fallback.path)")
        XCTAssertFalse(fallback.path.contains(NSTemporaryDirectory()),
                       "默认根目录跑到了临时区：那等于正常启动也不写存档了")
    }

    func testTildeAndEmptyValuesDoNotBreakTheOverride() throws {
        // 空串必须当作"没设"：CI 里 `ENV=""` 是常事，把它当成"存档写到 ''"会直接写坏路径
        withEnvironment("") {
            XCTAssertTrue(FileHistoryPersistence.defaultRootDirectory().path.hasSuffix("时间剪史"))
        }
        // `~` 要展开，否则存档会落在一个字面叫 "~" 的目录里
        withEnvironment("~/../tmp/smoke-tilde-check") {
            let resolved = FileHistoryPersistence.defaultRootDirectory().path
            XCTAssertFalse(resolved.hasPrefix("~/"), "波浪号没展开：\(resolved)")
        }
    }

    func testPersistenceActuallyWritesUnderTheOverride() throws {
        let root = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("smoke-write-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }

        try withEnvironment(root.path) {
            let persistence = FileHistoryPersistence(rootDirectory: FileHistoryPersistence.defaultRootDirectory())
            let entry = ClipboardEntry(content: .text("冒烟"), timestamp: Date(timeIntervalSince1970: 3),
                                       thumbnail: nil, sourceURL: nil, sourceUTIs: [])
            try persistence.save([entry])
            persistence.flushPendingSaves()
            let archive = root.appendingPathComponent("history.json")
            XCTAssertTrue(FileManager.default.fileExists(atPath: archive.path),
                          "存档没写进隔离目录：那冒烟测试读到的就是别的东西")
            XCTAssertEqual(persistence.load().first?.content, .text("冒烟"))
        }
    }
}
