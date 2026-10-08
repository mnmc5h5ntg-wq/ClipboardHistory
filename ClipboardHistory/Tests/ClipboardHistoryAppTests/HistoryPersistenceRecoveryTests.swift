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

        let preserved = try FileManager.default.contentsOfDirectory(atPath: root.path)
            .filter { $0.hasPrefix("history.corrupt-") }
        XCTAssertEqual(preserved.count, 1, "原件必须被保全一份副本")
        let preservedText = try String(
            contentsOf: root.appendingPathComponent(preserved[0]),
            encoding: .utf8
        )
        XCTAssertTrue(preservedText.contains(keptName), "保全副本应包含原始（可手工抢救的）内容")
    }

    private func permissions(of url: URL) -> Int {
        let attributes = try? FileManager.default.attributesOfItem(atPath: url.path)
        return Int(truncating: (attributes?[.posixPermissions] as? NSNumber) ?? NSNumber(value: 0))
    }
}
