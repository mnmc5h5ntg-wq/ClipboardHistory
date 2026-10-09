import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 B-1 / 账本 R2-04：`saveSnapshot` 以前每次保存都**重写每一个图片文件**，
/// 磁盘 IO 与库里的图片数成正比（500 条带图的库，每复制一次就重写几百个文件），
/// 而且连续保存时旧的 work item 不会被取消。
///
/// 判据用 **inode**：图片是 `.atomic` 写的（临时文件 + rename），所以"被重写过"必然换 inode，
/// 而 mtime 在同一秒内可能看不出差别。每条用例都附带一个阳性对照 ——
/// `history.json` 必须**每次**都换 inode，否则"图片没被重写"可能只是整次保存根本没跑。
@MainActor
final class ImageWriteAmortizationTests: XCTestCase {
    private var root: URL!

    private var imagesDirectory: URL {
        root.appendingPathComponent("images", isDirectory: true)
    }

    private var historyURL: URL {
        root.appendingPathComponent("history.json")
    }

    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory
            .appendingPathComponent("图片写入摊销-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: root)
    }

    private func inode(of url: URL) throws -> UInt64 {
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        guard let number = attributes[.systemFileNumber] as? NSNumber else {
            XCTFail("拿不到 \(url.lastPathComponent) 的 inode")
            return 0
        }
        return number.uint64Value
    }

    private func imageFiles() throws -> [URL] {
        try FileManager.default.contentsOfDirectory(at: imagesDirectory, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "png" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    private func twoImageEntries() throws -> [ClipboardEntry] {
        let teal = try makeStoredImage(color: .systemTeal, size: NSSize(width: 40, height: 30))
        let orange = try makeStoredImage(color: .systemOrange, size: NSSize(width: 20, height: 20))
        return [
            makeClipboardEntry(content: .image(teal), timestamp: Date(timeIntervalSince1970: 2), sourceUTIs: ["public.png"]),
            makeClipboardEntry(content: .image(orange), timestamp: Date(timeIntervalSince1970: 1), sourceUTIs: ["public.png"])
        ]
    }

    func testRepeatedSavesLeaveUnchangedImageFilesAlone() throws {
        let entries = try twoImageEntries()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save(entries)
        persistence.flushPendingSaves()

        let files = try imageFiles()
        XCTAssertEqual(files.count, 2, "两张图都应当已落盘，否则后面的比较没有意义")
        let imageInodesBefore = try files.map { try inode(of: $0) }
        let historyInodeBefore = try inode(of: historyURL)

        // 同样的内容再存两次：一张图都不该被重写。
        try persistence.save(entries)
        persistence.flushPendingSaves()
        try persistence.save(entries)
        persistence.flushPendingSaves()

        XCTAssertEqual(try files.map { try inode(of: $0) }, imageInodesBefore,
                       "未变化的图片文件被重写了：磁盘 IO 仍与图片数线性")
        // 阳性对照：保存确实跑了（history.json 每次都重写）。
        XCTAssertNotEqual(try inode(of: historyURL), historyInodeBefore,
                          "history.json 没有换 inode ⇒ 保存根本没执行，上面那条'图片没重写'是假绿")

        // 内容也不能因为跳过写入而读不回来。
        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.count, 2)
        XCTAssertEqual(reloaded.filter { if case .image = $0.content { return true }; return false }.count, 2,
                       "跳过重写之后，图片必须仍然能从磁盘读回来")
    }

    func testChangedImageIsRewrittenWhileTheOtherIsNot() throws {
        let entries = try twoImageEntries()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save(entries)
        persistence.flushPendingSaves()

        // 按条目 id 定位文件，**不要**按目录列举的下标：文件名是 UUID，排序与条目顺序无关。
        // 第一版就是这么写的，单独跑过、进全量套件就红（UUID 顺序变了），是典型的随机化 flake。
        func imageFile(for entry: ClipboardEntry) -> URL {
            imagesDirectory.appendingPathComponent("\(entry.id.uuidString)-image.png")
        }
        let changedFile = imageFile(for: entries[0])
        let untouchedFile = imageFile(for: entries[1])
        XCTAssertTrue(FileManager.default.fileExists(atPath: changedFile.path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: untouchedFile.path))
        let changedInodeBefore = try inode(of: changedFile)
        let untouchedInodeBefore = try inode(of: untouchedFile)

        // 把第一条换成尺寸不同的图（PNG 长度必然不同）：它必须被重写，另一张不许动。
        let bigger = try makeStoredImage(color: .systemPurple, size: NSSize(width: 90, height: 70))
        var changed = entries
        changed[0] = makeClipboardEntry(
            id: entries[0].id,
            content: .image(bigger),
            timestamp: entries[0].timestamp,
            sourceUTIs: ["public.png"]
        )
        try persistence.save(changed)
        persistence.flushPendingSaves()

        XCTAssertNotEqual(try inode(of: changedFile), changedInodeBefore, "换了内容的图片没有被重写")
        XCTAssertEqual(try inode(of: untouchedFile), untouchedInodeBefore, "没变的图片被连带重写了")
    }

    func testImageFileDeletedExternallyIsWrittenAgain() throws {
        let entries = try twoImageEntries()
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save(entries)
        persistence.flushPendingSaves()

        let files = try imageFiles()
        try FileManager.default.removeItem(at: files[0])

        try persistence.save(entries)
        persistence.flushPendingSaves()

        XCTAssertTrue(FileManager.default.fileExists(atPath: files[0].path),
                      "外部删掉的图片必须在下次保存时补回来，否则存档会指着不存在的文件")
        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.filter { if case .image = $0.content { return true }; return false }.count, 2)
    }

    func testSupersededSaveStillLeavesTheLatestSnapshotOnDisk() throws {
        let persistence = FileHistoryPersistence(rootDirectory: root)
        let first = makeClipboardEntry(content: .text("第一条"), timestamp: Date(timeIntervalSince1970: 1))
        try persistence.save([first])

        // 不 flush 就再存一次：去抖会取消还没开始的那一次，
        // 但落盘的必须是**最新**的整库快照，绝不能是"两次都没写"。
        let second = makeClipboardEntry(content: .text("第二条"), timestamp: Date(timeIntervalSince1970: 2))
        try persistence.save([second, first])
        persistence.flushPendingSaves()

        let reloaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(reloaded.map(\.content), [.text("第二条"), .text("第一条")],
                       "去抖不能把最新一次保存也丢掉")
    }
}
