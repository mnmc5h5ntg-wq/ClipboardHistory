import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 性能预算用例（R-29）。阈值定得比实测宽松，避免机器抖动导致随机失败，
/// 但足以抓住"退回主线程整表重编码"这类数量级回归。
/// 每条都会 print 实测毫秒，便于对比修复前后。
final class PerfBudgetTests: XCTestCase {
    private func milliseconds(_ block: () -> Void) -> Double {
        let start = Date()
        block()
        return Date().timeIntervalSince(start) * 1000
    }

    private func imageEntry(_ image: StoredImage, id: UUID, ageSeconds: TimeInterval) -> ClipboardEntry {
        ClipboardEntry(
            id: id,
            content: .image(image),
            timestamp: Date().addingTimeInterval(-ageSeconds),
            thumbnail: image,
            sourceURL: nil,
            sourceUTIs: ["public.png"]
        )
    }

    /// R-07/R-08：库里已有 12 张图时，保存一条新文本不得再重编码全部图片。
    @MainActor
    func testSavingTextIntoImageHeavyLibraryStaysCheap() throws {
        let root = try makeTemporaryDirectory()
        defer { try? FileManager.default.removeItem(at: root) }
        let image = try makeStoredImage(size: NSSize(width: 1600, height: 1200))
        var entries: [ClipboardEntry] = (0..<12).map {
            imageEntry(image, id: UUID(), ageSeconds: Double($0) + 1)
        }
        let persistence = FileHistoryPersistence(rootDirectory: root)
        try persistence.save(entries)
        persistence.flushPendingSaves()

        // 重新载入（模拟启动），再保存一条纯文本
        let loaded = persistence.load()
        XCTAssertEqual(loaded.count, 12)
        // 取 3 次里的最快值：单次计时在本机抖动可达 ±40%，
        // 而"修复前"的量级差是 3~5 倍，最小值足以把回归挡在门外。
        let loadSamples = (0..<3).map { _ in milliseconds { _ = persistence.load() } }
        entries.append(ClipboardEntry(content: .text("新增的一条文本"), timestamp: Date(),
                                      thumbnail: nil, sourceURL: nil, sourceUTIs: []))
        let saveSamples = (0..<3).map { _ in
            milliseconds {
                try? persistence.save(entries)
                persistence.flushPendingSaves()
            }
        }
        let loadMs = loadSamples.min() ?? .infinity
        let saveMs = saveSamples.min() ?? .infinity
        print("PERF load(12×1600x1200)=\(loadSamples.map { String(format: "%.0f", $0) }.joined(separator: "/"))ms"
            + " save(13条,含12图)=\(saveSamples.map { String(format: "%.0f", $0) }.joined(separator: "/"))ms")
        // 修复前实测：load 413.9ms、save 667.8ms。阈值留了 ~2 倍余量，
        // 但仍比"每次都重编码全部图片"低 2 倍以上，去掉修复必然变红。
        XCTAssertLessThan(loadMs, 200, "启动载入 12 张图必须保持在十位数毫秒（修复前 413.9ms）")
        XCTAssertLessThan(saveMs, 200, "保存不得随图片数量线性重编码（修复前 667.8ms）")
    }

    /// R-08：单张图片的指纹成本应与图片尺寸解耦。
    @MainActor
    func testImageFingerprintIsSampledNotFullSize() throws {
        let large = try makeStoredImage(size: NSSize(width: 4000, height: 3000))
        let small = try makeStoredImage(size: NSSize(width: 200, height: 150))
        let largeMs = milliseconds { _ = StoredImage(large.nsImage) }
        let smallMs = milliseconds { _ = StoredImage(small.nsImage) }
        print("PERF fingerprint 4000x3000=\(String(format: "%.2f", largeMs))ms 200x150=\(String(format: "%.2f", smallMs))ms")
        XCTAssertLessThan(largeMs, max(smallMs * 4, 8), "指纹成本不应随像素数线性增长（审计基线 1200x900 = 7.4ms/张）")
    }

    /// 采样指纹必须仍能区分同尺寸不同内容的图（否则去重会把不同截图合并）。
    @MainActor
    func testSampledFingerprintKeepsDistinctImagesDistinct() throws {
        let plain = try makeStoredImage(size: NSSize(width: 1200, height: 900))
        let withMark = try markedStoredImage(size: NSSize(width: 1200, height: 900))
        XCTAssertNotEqual(plain, withMark, "同尺寸不同内容不得被判为同一张图")
        let sameAgain = try makeStoredImage(size: NSSize(width: 1200, height: 900))
        XCTAssertEqual(plain, sameAgain, "同尺寸同内容必须仍被判为重复")
    }

    /// R-10：大文本的显示文案不得整串扫描。
    func testPreviewOfHugeTextIsBounded() throws {
        let huge = String(repeating: "行内容 line\n", count: 200_000)   // ~2.4MB
        let content = ClipboardEntryContent.text(huge)
        let previewMs = milliseconds { _ = content.preview }
        let sizeMs = milliseconds { _ = content.sizeDescription }
        print("PERF preview(2.4MB)=\(String(format: "%.2f", previewMs))ms sizeDescription=\(String(format: "%.2f", sizeMs))ms")
        XCTAssertLessThan(previewMs, 5, "单条预览必须是常数级（修复前 45.8ms）")
        XCTAssertLessThan(sizeMs, 20, "尺寸文案仍走整串计数（grapheme 计数），暂以 20ms 为上界；基线 5.5ms")
    }

    /// R-09：一次过滤求值不应是全表重复扫描级别的成本。
    @MainActor
    func testFilteredEntriesWithSearchIsBounded() throws {
        var entries: [ClipboardEntry] = []
        for index in 0..<500 {
            entries.append(ClipboardEntry(
                content: .text(String(repeating: "内容", count: 500) + " #\(index)"),
                timestamp: Date().addingTimeInterval(-Double(index)),
                thumbnail: nil, sourceURL: nil, sourceUTIs: []
            ))
        }
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(entriesToLoad: entries),
            retentionPolicy: .default
        )
        store.perform(.updateSearch("#499"))
        var total = 0.0
        for _ in 0..<10 { total += milliseconds { _ = store.filteredEntries } }
        let average = total / 10
        print("PERF filteredEntries(500条×1KB+搜索词)=\(String(format: "%.2f", average))ms/次（审计基线 14.07ms，且一帧会被调用 3–5 次）")
        // 修复前 14.07ms/次；缓存化后命中路径应为 0ms。
        XCTAssertLessThan(average, 1, "命中缓存的读取必须近乎为零（修复前 14.07ms/次）")

        // 输入搜索词的代价：perform(.updateSearch) 内部会走一次 reconcileSelection
        // ⇒ 恰好一次重算。修复前每次界面求值都重扫全表（3–5 次/帧）。
        var typingTotal = 0.0
        for index in 0..<10 {
            typingTotal += milliseconds { store.perform(.updateSearch("#\(index)")) }
        }
        let typingAverage = typingTotal / 10
        print("PERF 改一次搜索词（含唯一一次重算）=\(String(format: "%.2f", typingAverage))ms/次（修复前单次全表扫描就要 14.07ms）")
        XCTAssertLessThan(typingAverage, 60, "输入一个字符的代价必须有上界")
    }

    private func markedStoredImage(size: NSSize) throws -> StoredImage {
        let image = NSImage(size: size)
        image.lockFocus()
        NSColor.red.setFill()
        NSRect(origin: .zero, size: size).fill()
        NSColor.blue.setFill()
        NSRect(x: 10, y: 10, width: 24, height: 24).fill()
        image.unlockFocus()
        let tiff = try XCTUnwrap(image.tiffRepresentation)
        let bitmap = try XCTUnwrap(NSBitmapImageRep(data: tiff))
        let png = try XCTUnwrap(bitmap.representation(using: .png, properties: [:]))
        return try XCTUnwrap(StoredImage(pngData: png))
    }
}

/// 派生缓存的一致性：任何一次写入都必须让 filteredEntries 立刻反映，
/// 否则 R-09 的缓存就是"看起来快、实际会显示旧数据"。
@MainActor
final class FilteredCacheCoherenceTests: XCTestCase {
    private func intake(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(text), thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"])
    }

    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    func testCacheReflectsAddDeleteAndFavoriteImmediately() {
        let store = makeStore()
        store.perform(.updateSearch("kkt"))
        XCTAssertEqual(store.filteredEntries.count, 0)

        store.add(intake("kkt 第一条"), timestamp: Date())
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["kkt 第一条"], "新增后必须立即出现在过滤结果里")

        let added = store.entries[0]
        store.add(intake("无关内容"), timestamp: Date())
        XCTAssertEqual(store.filteredEntries.count, 1, "不匹配搜索词的条目不得混进来")

        store.perform(.toggleFavorite(added))
        store.perform(.updateSearch(""))
        store.perform(.updateFilter(.favorites))
        XCTAssertEqual(store.filteredEntries.map(\.id), [added.id], "收藏筛选必须看到刚收藏的那条")

        let deleted = store.filteredEntries[0]
        store.perform(.delete(deleted))
        XCTAssertEqual(store.filteredEntries.count, 0, "删除后不得仍在过滤结果里")
    }

    func testCacheReflectsSearchAndFilterChanges() {
        let store = makeStore()
        store.add(intake("alpha one"), timestamp: Date())
        store.add(intake("beta two"), timestamp: Date())
        XCTAssertEqual(store.filteredEntries.count, 2)
        store.perform(.updateSearch("beta"))
        XCTAssertEqual(store.filteredEntries.map(\.shortPreview), ["beta two"])
        store.perform(.updateSearch(""))
        store.perform(.updateFilter(.favorites))
        XCTAssertEqual(store.filteredEntries.count, 0)
        store.perform(.updateFilter(.all))
        XCTAssertEqual(store.filteredEntries.count, 2)
    }


}
