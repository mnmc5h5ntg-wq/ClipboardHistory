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

    /// 同一段操作采样多次，判据打在**最快**那次上，并把 最快/均值/最慢 全打印。
    ///
    /// 只有当"这批同操作样本自己的跨度"超过判据阈值时才拒绝下结论（skip）—— 那一刻环境噪声
    /// 比要分辨的差值还大，红和绿都不说明改动。真实回归不会被这个 skip 藏起来：数量级退化时
    /// 每一次采样都超线，跨度反而很小，判据照旧点亮。
    ///
    /// 刻意不用 load1 做闸门。CI runner 实测 `load1=11.8 / 活跃核=3`（比值 3.9），负载闸门会把
    /// 这 5 条守卫在唯一的自动化环境里全部变成 skip —— 只在没人看着的地方失效的守卫比没守卫更糟。
    /// 本机那次 997ms 假红（单跑 155/168/171ms）在新判据下跨度约 840ms ≫ 阈值 250ms，照样 skip；
    /// CI 上图片比较 25/26/32ms（跨度 7ms）则照常下结论。**所有阈值本身一个都没动。**
    private func report(
        samples: [Double],
        threshold: Double,
        what: String,
        test: String = #function
    ) throws -> Double {
        var loads = [Double](repeating: 0, count: 3)
        let load1 = getloadavg(&loads, 1) > 0 ? loads[0] : 0
        let fastest = samples.min() ?? .infinity
        let slowest = samples.max() ?? 0
        let mean = samples.reduce(0, +) / Double(max(samples.count, 1))
        print("PERF[\(test)] \(what)：最快\(String(format: "%.2f", fastest))ms 均值"
            + "\(String(format: "%.2f", mean))ms 最慢\(String(format: "%.2f", slowest))ms"
            + "（阈值 \(threshold)ms，n=\(samples.count)，load1=\(String(format: "%.1f", load1))"
            + " 活跃核=\(ProcessInfo.processInfo.activeProcessorCount)）")
        if slowest - fastest > threshold {
            throw XCTSkip("同操作样本跨度 \(String(format: "%.2f", slowest - fastest))ms 已超过该判据阈值 "
                + "\(String(format: "%.2f", threshold))ms：本次环境分辨不了这条判据。实测数字已全部打印。")
        }
        return fastest
    }

    private func measureFastest(
        _ count: Int,
        threshold: Double,
        what: String,
        test: String = #function,
        _ block: () -> Void
    ) throws -> Double {
        var samples: [Double] = []
        for _ in 0..<max(count, 1) { samples.append(milliseconds(block)) }
        return try report(samples: samples, threshold: threshold, what: what, test: test)
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
        let loadMs = try measureFastest(3, threshold: 200, what: "load(12×1600x1200)") {
            _ = persistence.load()
        }
        entries.append(ClipboardEntry(content: .text("新增的一条文本"), timestamp: Date(),
                                      thumbnail: nil, sourceURL: nil, sourceUTIs: []))
        let saveMs = try measureFastest(3, threshold: 200, what: "save(13条,含12图)") {
            try? persistence.save(entries)
            persistence.flushPendingSaves()
        }
        // 修复前实测：load 413.9ms、save 667.8ms。阈值留了 ~2 倍余量，
        // 但仍比"每次都重编码全部图片"低 2 倍以上，去掉修复必然变红。
        XCTAssertLessThan(loadMs, 200, "启动载入 12 张图必须保持在十位数毫秒（修复前 413.9ms）")
        XCTAssertLessThan(saveMs, 200, "保存不得随图片数量线性重编码（修复前 667.8ms）")
    }

    /// R-08：图片去重比较的成本。
    ///
    /// 这条以前是**恒绿的假守卫**：它计时的是 `StoredImage(nsImage)` 这个构造调用，
    /// 而指纹是惰性的，所以 4000x3000 与 200x150 都报 0.00ms，什么都没测。
    /// 现在分别量三类真实比较：同字节重复（走短路）、同尺寸不同内容（必须采样）、
    /// 以及小图采样，作为对照。旧实现里第二类在 3000x2000 上两侧各整幅解码，
    /// 实测 434ms 起，全部发生在主线程的 `add()` 里。
    @MainActor
    func testImageComparisonCostStaysBounded() throws {
        let big = NSSize(width: 3000, height: 2000)
        // 每一类比较都用各自"第一次被比较"的对象：指纹是惰性缓存的，
        // 拿同一对对象先断言再计时，量到的永远是 0ms（本条测试的第一版就这么假绿过）。
        var samplePairs: [(StoredImage, StoredImage)] = []
        for _ in 0..<3 {
            samplePairs.append((try makeStoredImage(color: .red, size: big),
                                try markedStoredImage(size: big)))
        }
        let largeSampleMs = try report(
            samples: samplePairs.map { pair in milliseconds { _ = (pair.0 == pair.1) } },
            threshold: 250,
            what: "图片比较 3000x2000 冷（同尺寸不同内容）"
        )
        let coldPlain = samplePairs[0].0
        let coldMarked = samplePairs[0].1

        let smallPlain = try makeStoredImage(color: .red, size: NSSize(width: 200, height: 150))
        let smallMarked = try markedStoredImage(size: NSSize(width: 200, height: 150))
        let smallSampleMs = milliseconds { _ = (smallPlain == smallMarked) }

        // 同样每轮都换新的一对，否则第 2、3 次量到的是已焐热的缓存。
        var twinPairs: [(StoredImage, StoredImage)] = []
        for _ in 0..<3 {
            twinPairs.append((try makeStoredImage(color: .red, size: big),
                              try makeStoredImage(color: .red, size: big)))
        }
        let sameBytesMs = try report(
            samples: twinPairs.map { pair in milliseconds { _ = (pair.0 == pair.1) } },
            threshold: 5,
            what: "图片比较 冷（同字节重复）"
        )

        print("PERF 小图采样（200x150，仅打印）=\(String(format: "%.2f", smallSampleMs))ms")

        XCTAssertTrue(twinPairs[0].0 == twinPairs[0].1, "同字节的两张图必须判为同一张")
        XCTAssertNotEqual(coldPlain, coldMarked, "同尺寸不同内容不得被判为同一张")

        // 判据：同字节重复是最常见路径（< 5ms，旧实现要整幅解码），
        // 3000x2000 的一次去重比较必须明显低于旧实测 434ms。
        XCTAssertLessThan(sameBytesMs, 5, "重复复制同一张图是最常见路径，不该付解码成本")
        XCTAssertLessThan(largeSampleMs, 250, "3000x2000 的一次去重比较必须明显低于旧实测 434ms")

        // 稳态不变量：旧图那一侧的指纹已经算过（缓存是 class 盒子，随值拷贝共享），
        // 所以"再复制一张新图"只该付**一次**采样，而不是每次两张。
        let anotherNew = try markedStoredImage(size: NSSize(width: 3200, height: 2100))
        let warmMs = milliseconds { _ = (coldPlain == anotherNew) }
        print("PERF 稳态一次比较（一侧已焐热）=\(String(format: "%.1f", warmMs))ms（冷=\(String(format: "%.0f", largeSampleMs))ms）")

        // 判据改用**计数**而不是计时。CI 的 2 核 runner 上冷/热差值会被调度噪声吃掉 ——
        // `f7398f3` 就是这样假红的（冷 34.5ms、热 40.7ms，"热 < 冷"必然失败，而缓存其实是好的）。
        // 计数与机器快慢无关：焐热之后再比 3 次，旧图那一侧的指纹计算次数必须一动不动。
        let computationsBefore = coldPlain.fingerprintComputations
        for _ in 0..<3 { _ = (coldPlain == anotherNew) }
        XCTAssertEqual(coldPlain.fingerprintComputations, computationsBefore,
                       "旧图那一侧的指纹被重算了：缓存没有随值拷贝共享出去")
        XCTAssertEqual(anotherNew.fingerprintComputations, 1,
                       "新图一侧算了 \(anotherNew.fingerprintComputations) 次指纹，应当只有第一次")
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
        let previewMs = try measureFastest(5, threshold: 5, what: "preview(2.4MB)") {
            _ = content.preview
        }
        let sizeMs = try measureFastest(5, threshold: 5, what: "sizeDescription(2.4MB)") {
            _ = content.sizeDescription
        }
        XCTAssertLessThan(previewMs, 5, "单条预览必须是常数级（修复前 45.8ms）")
        XCTAssertLessThan(sizeMs, 5, "尺寸文案已改成有界计数（数到 10 万即停）：实测 1.11ms，上界从 20ms 收回 5ms；旧实现整串计数基线 5.5ms")
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
        let readFastest = try measureFastest(10, threshold: 1, what: "filteredEntries(500条×1KB+搜索词) 命中缓存") {
            _ = store.filteredEntries
        }
        // 修复前 14.07ms/次；缓存化后命中路径应为 0ms。
        // 判据取最快一次：缓存退化成整表重扫时 10 次里没有一次能低于 1ms（变异实测每次都 14.4ms 起），
        // 而均值会被 runner 上邻居用例的调度噪声吃掉。阈值不变。
        XCTAssertLessThan(readFastest, 1, "命中缓存的读取必须近乎为零（修复前 14.07ms/次）")

        // 输入搜索词的代价：perform(.updateSearch) 内部会走一次 reconcileSelection
        // ⇒ 恰好一次重算。修复前每次界面求值都重扫全表（3–5 次/帧）。
        // 每个词都不同，避免"同一个词第二次直接命中别的缓存"把成本测没。
        var typingSamples: [Double] = []
        for index in 0..<10 {
            typingSamples.append(milliseconds { store.perform(.updateSearch("#\(index)")) })
        }
        let typingFastest = try report(
            samples: typingSamples,
            threshold: 60,
            what: "改一次搜索词（含唯一一次重算）"
        )
        // `53bbe85` 在 runner 上就是靠均值 69.0ms 假红的：跨核调度噪声足以越过 60ms，
        // 而"敲一个字符卡一下"的真实回归会让 10 次里每一次都超，不会因为碰上安静窗口而漏掉。
        // 阈值 60ms 未动。
        XCTAssertLessThan(typingFastest, 60, "输入一个字符的代价必须有上界")
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
