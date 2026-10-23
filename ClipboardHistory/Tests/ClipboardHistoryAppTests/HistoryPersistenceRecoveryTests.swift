import Foundation
import XCTest
@testable import ClipboardHistoryApp

/// R-02 回归守卫：存档损坏不得导致历史库与图片文件被连带删除。
///
/// 对应审计缺陷 P-06（已复现）：旧实现把"文件存在但解析失败"折叠成空历史，
/// 于是下一次复制触发保存时，`removeUnusedImages` 会把所有旧图片删掉，
/// 并且覆盖写让原本还可手工抢救的残余内容彻底消失。
@MainActor
final class HistoryPersistenceRecoveryTests: XCTestCase {
    private func imageEntry(_ image: StoredImage, at date: Date) -> ClipboardEntry {
        ClipboardEntry(
            content: .image(image),
            timestamp: date,
            thumbnail: image,
            sourceURL: nil,
            sourceUTIs: ["public.png"]
        )
    }

    func testFirstRunHasNoFilesAndNoRecoveryNotice() throws {
        let root = try makeTemporaryDirectory()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        XCTAssertEqual(persistence.load(), [])
        XCTAssertNil(persistence.recoveryNotice, "首次运行不该报「恢复」提示")
    }

    func testSaveWritesRollingBackupWithOwnerOnlyPermissions() throws {
        let root = try makeTemporaryDirectory()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save([.init(
            content: .text("hello"),
            timestamp: Date(timeIntervalSince1970: 1),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: []
        )])
        persistence.flushPendingSaves()

        let historyURL = root.appendingPathComponent("history.json")
        let backupURL = FileHistoryPersistence.backupURL(for: historyURL)
        XCTAssertTrue(FileManager.default.fileExists(atPath: backupURL.path), "应存在滚动备份")
        XCTAssertEqual(permissions(of: backupURL), 0o600)
        let historyText = try String(contentsOf: historyURL, encoding: .utf8)
        let backupText = try String(contentsOf: backupURL, encoding: .utf8)
        XCTAssertEqual(historyText, backupText, "备份应与刚写入的主存档一致")
    }

    /// 主路径：history.json 半截损坏，但滚动备份完好 ⇒ 从备份恢复，图片一张都不能少。
    func testCorruptHistoryRecoversFromBackupAndKeepsEveryImage() throws {
        let root = try makeTemporaryDirectory()
        let images = root.appendingPathComponent("images", isDirectory: true)
        let image = try makeStoredImage()
        let first = imageEntry(image, at: Date(timeIntervalSince1970: 1))
        let second = imageEntry(image, at: Date(timeIntervalSince1970: 2))

        let seeding = FileHistoryPersistence(rootDirectory: root)
        try seeding.save([first, second])
        seeding.flushPendingSaves()
        let seededImages = try FileManager.default.contentsOfDirectory(atPath: images.path)
        XCTAssertEqual(Set(seededImages).count, 2, "夹具应有两张图片文件")

        // 模拟崩溃/断电留下的半截 JSON
        let historyURL = root.appendingPathComponent("history.json")
        let partial = "{\"version\":1,\"entries\":[{\"id\":\""
        try Data(partial.utf8).write(to: historyURL)

        let persistence = FileHistoryPersistence(rootDirectory: root)
        let recovered = persistence.load()
        XCTAssertEqual(recovered.count, 2, "应从备份恢复两条记录")
        XCTAssertNotNil(persistence.recoveryNotice)
        XCTAssertTrue(persistence.recoveryNotice?.contains("备份") == true)

        // 真实使用路径：用户复制一条新内容 ⇒ 触发保存
        let writer = TestClipboardWriter()
        let store = HistoryStore(
            intake: ClipboardIntake(pasteboard: .general),
            clipboardWriter: writer,
            persistence: persistence,
            retentionPolicy: .default
        )
        store.add(
            ClipboardIntake.Entry(content: .text("新的复制"), thumbnail: nil, sourceUTIs: []),
            timestamp: Date()
        )
        store.flushPendingPersistence()

        let survivingImages = try FileManager.default.contentsOfDirectory(atPath: images.path)
        XCTAssertEqual(Set(survivingImages), Set(seededImages), "P-06 修复验证：图片文件不得被连带删除")
        let stored = try String(contentsOf: historyURL, encoding: .utf8)
        XCTAssertTrue(stored.contains("新的复制"))
        XCTAssertTrue(stored.contains("id"), "恢复后的记录应仍在新存档里")
    }

    /// 兜底路径：主存档损坏、备份也没有 ⇒ 以空历史启动，但
    /// ① 原件被保全成 history.corrupt-*.json（不删不改），
    /// ② 损坏文本里仍能读出的图片文件名不得被清理掉。
    func testCorruptHistoryWithoutBackupPreservesOriginalAndReferencedImages() throws {
        let root = try makeTemporaryDirectory()
        let images = root.appendingPathComponent("images", isDirectory: true)
        try FileManager.default.createDirectory(at: images, withIntermediateDirectories: true)

        let keptName = UUID().uuidString + "-image.png"
        let orphanName = UUID().uuidString + "-image.png"
        let image = try makeStoredImage()
        let png = try XCTUnwrap(image.pngData())
        try png.write(to: images.appendingPathComponent(keptName))
        try png.write(to: images.appendingPathComponent(orphanName))

        let corruptBody = """
        {"version":1,"entries":[{"id":"\(UUID().uuidString)","timestamp":"2026-06-01T00:00:00Z",\
        "contentKind":"image","imageFileName":"\(keptName)","sourceUTIs":[]},
        """
        let historyURL = root.appendingPathComponent("history.json")
        try Data(corruptBody.utf8).write(to: historyURL)
        // 备份也坏掉
        try Data("not json at all".utf8).write(
            to: FileHistoryPersistence.backupURL(for: historyURL)
        )

        let persistence = FileHistoryPersistence(rootDirectory: root)
        XCTAssertEqual(persistence.load(), [])
        XCTAssertNotNil(persistence.recoveryNotice)
        // R319 / BACKLOG 374：这一格原来只在"两次载入落在同一秒"时才成立 ——
        // `preserveCorruptFile` 的名字是**秒**粒度、同名不覆盖，于是同一秒返回 nil
        // （恢复提示只能说"未知位置"），跨秒界就多写一份逐字节相同的副本（红）。
        // R318 的四件套就是跨了秒界那一次：同版两跑 935 例一次红一次绿、独跑 12 次全绿。
        // 一条断言的结果跟着挂钟走，它报的就不是产品，是运气。
        //
        // 所以现在**故意跨过秒界**再载入一次（等条件，不是固定 sleep 撞运气 —— 见账本 R267 那一族），
        // 然后要求"恰好一份 + 与原件逐字节相同 + 提示里有真文件名"。
        // 修之前这两条都会红（第二份 / 未知位置），修之后它们才叫证据。**不许**降成 `>= 1`。
        let crossed = Date()
        while Date().timeIntervalSince(crossed) < 1.05 {
            Thread.sleep(forTimeInterval: 0.05)
        }
        XCTAssertEqual(persistence.load(), [], "第二次载入仍要以空历史启动（原件没被修好）")
        let secondNotice = try XCTUnwrap(persistence.recoveryNotice)
        XCTAssertFalse(secondNotice.contains("未知位置"),
                       "第二次载入也要交回真实的保全文件名 ⇒ 幂等之后不许把已有副本报成 nil")
        let preserved = try FileManager.default.contentsOfDirectory(atPath: root.path)
            .filter { $0.hasPrefix("history.corrupt-") }
        XCTAssertEqual(preserved.count, 1,
                       "原件必须被保全**恰好一份**：跨过秒界的第二次载入不许再抄一份相同的副本")

        let store = HistoryStore(
            intake: ClipboardIntake(pasteboard: .general),
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: .default
        )
        store.add(
            ClipboardIntake.Entry(content: .text("一条新复制"), thumbnail: nil, sourceUTIs: []),
            timestamp: Date()
        )
        store.flushPendingPersistence()

        let survivors = Set(try FileManager.default.contentsOfDirectory(atPath: images.path))
        XCTAssertTrue(survivors.contains(keptName), "损坏文本里被引用的图片必须保住")
        XCTAssertFalse(survivors.contains(orphanName), "未被引用的孤儿图片仍应清理（保留既有语义）")

        // 上面已经跨过秒界做过第二次载入并数过"恰好一份"；这里再确认**正常保存那一条路径**
        // 也不会追加 corrupt 副本，并且那一份确实是原件的逐字节拷贝（可手工抢救的前提）。
        let preservedAfterSave = try FileManager.default.contentsOfDirectory(atPath: root.path)
            .filter { $0.hasPrefix("history.corrupt-") }
        XCTAssertEqual(preservedAfterSave, preserved,
                       "恢复之后的一次正常保存不许再产生 corrupt 副本")
        let preservedURL = root.appendingPathComponent(preserved[0])
        XCTAssertEqual(try Data(contentsOf: preservedURL), Data(corruptBody.utf8),
                       "保全副本必须与损坏原件逐字节相同（可手工抢救的前提）")
        let preservedText = try String(contentsOf: preservedURL, encoding: .utf8)
        XCTAssertTrue(preservedText.contains(keptName), "保全副本应包含原始（可手工抢救的）内容")
    }

    private func permissions(of url: URL) -> Int {
        let attributes = try? FileManager.default.attributesOfItem(atPath: url.path)
        return Int(truncating: (attributes?[.posixPermissions] as? NSNumber) ?? NSNumber(value: 0))
    }
}
