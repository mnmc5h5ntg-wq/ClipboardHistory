import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 B-2 / 账本 R2-07：来源 App 以前只活在内存里 —— `StoredEntry` 根本没有这两个字段，
/// 所以每次重启后归因全丢，推荐权重里的 `appAffinity` 对"载入的历史"恒为 0（等于那一项从没生效过）。
///
/// 这三条用例分别钉住：① 存盘再载入仍然带着来源 App；② **旧存档**（没有这两个键）照样能读，
/// 读成 nil —— 这是"加可选字段、不升 schema 版本"的兼容性前提；③ 隐私文案里说清了会保存来源 App，
/// 免得代码里多存了一样东西而界面上的承诺没跟着变。
@MainActor
final class SourceAppAttributionPersistenceTests: XCTestCase {
    private var root: URL!

    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory
            .appendingPathComponent("来源App持久化-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: root)
    }

    func testSourceAppSurvivesASaveLoadRoundTrip() throws {
        let entry = makeClipboardEntry(
            content: .text("一条带来源的记录"),
            timestamp: Date(timeIntervalSince1970: 1_700_000_000),
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari",
            sourceAppName: "Safari"
        )
        let writer = FileHistoryPersistence(rootDirectory: root)
        try writer.save([entry])
        writer.flushPendingSaves()   // 落盘是异步的，不 flush 就读不到（这条以前漏了，读到 0 条）

        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.count, 1)
        XCTAssertEqual(reloaded.first?.sourceAppBundleID, "com.apple.Safari",
                       "bundle id 没有落盘：重启后 appAffinity 仍然恒为 0")
        XCTAssertEqual(reloaded.first?.sourceAppName, "Safari")
    }

    func testSourceAppSurvivesRoundTripForImageAndFileEntriesToo() throws {
        let image = try makeStoredImage(color: .systemTeal, size: NSSize(width: 12, height: 9))
        let fileURL = URL(fileURLWithPath: "/tmp/来源归因-\(UUID().uuidString).txt")
        let entries = [
            makeClipboardEntry(
                content: .image(image),
                timestamp: Date(timeIntervalSince1970: 3),
                sourceUTIs: ["public.png"],
                sourceAppBundleID: "com.apple.Preview",
                sourceAppName: "预览"
            ),
            makeClipboardEntry(
                content: .file(fileURL),
                timestamp: Date(timeIntervalSince1970: 2),
                sourceUTIs: ["public.file-url"],
                sourceAppBundleID: "com.apple.finder",
                sourceAppName: "Finder"
            )
        ]
        let writer = FileHistoryPersistence(rootDirectory: root)
        try writer.save(entries)
        writer.flushPendingSaves()

        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.map(\.sourceAppBundleID), ["com.apple.Preview", "com.apple.finder"],
                       "图片和文件条目也要带来源：漏一种就等于那类记录永远没有归因")
        XCTAssertEqual(reloaded.map(\.sourceAppName), ["预览", "Finder"])
    }

    func testArchiveWrittenBeforeTheFieldExistedStillLoads() throws {
        // 手写的"旧存档"：没有 sourceAppBundleID / sourceAppName 两个键。
        let json = """
        {
          "version" : 1,
          "entries" : [
            {
              "contentKind" : "text",
              "id" : "\(UUID().uuidString)",
              "sourceUTIs" : [ "public.utf8-plain-text" ],
              "text" : "旧版本写下的一条",
              "timestamp" : "2026-10-09T00:00:00Z"
            }
          ]
        }
        """
        try Data(json.utf8).write(
            to: root.appendingPathComponent("history.json"),
            options: .atomic
        )

        let persistence = FileHistoryPersistence(rootDirectory: root)
        let loaded = persistence.load()
        XCTAssertEqual(loaded.count, 1, "旧存档必须照常可读，不能因为新增字段就整份解不开")
        XCTAssertEqual(loaded.first?.content, .text("旧版本写下的一条"))
        XCTAssertNil(loaded.first?.sourceAppBundleID, "旧存档没有这个信息，读成 nil 而不是编一个")
        XCTAssertNil(persistence.recoveryNotice, "正常旧存档不该触发恢复提示")
    }

    func testPrivacyCopyDisclosesTheSourceApp() {
        XCTAssertTrue(
            HistoryPrivacyCopy.capturedContent.contains("来源 App"),
            "代码里多存了来源 App，设置页的隐私说明必须跟着说；否则界面承诺与落盘内容不一致"
        )
        XCTAssertTrue(
            HistoryPrivacyCopy.settingsBullets.contains(HistoryPrivacyCopy.capturedContent),
            "这条说明必须真的出现在设置页的列表里，不能只是躺在源码里"
        )
    }
}
