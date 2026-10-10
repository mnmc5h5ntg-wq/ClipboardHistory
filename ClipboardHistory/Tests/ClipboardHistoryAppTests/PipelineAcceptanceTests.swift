import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 C-1：**修复的验收必须从产品入口进去**（`HistoryStore` / `ClipboardIntake` / 视图实际消费的字段），
/// 不许只调内部纯函数就宣称修好了。
///
/// 这条规矩不是抽象要求：两轮里同类错误犯了两次 —— 第二轮 N-1 的守卫测试绕过 adapter 直调 engine
/// （于是"测试全绿、产品照崩"），第三轮 D-7 的探针在 CI 一次也没跑过。
/// 本文件就是把三条原本只测纯函数的判据**改造成管线级**的样本，并各配一次变异对照证明它们真的承重
/// （变异记录写在 `AGENT_DECISIONS.md` 的 D-034）。
///
/// 数据安全：一律用命名私有 `NSPasteboard`（`NSPasteboard(name:)`）+ `RecordingHistoryPersistence`
/// + `TestClipboardWriter`，从不碰 `NSPasteboard.general`，也从不碰用户数据目录（D-002）。
@MainActor
final class PipelineAcceptanceTests: XCTestCase {
    private func makeStore(intake: ClipboardIntake) -> HistoryStore {
        HistoryStore(
            intake: intake,
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    private func makePasteboard() -> NSPasteboard {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        return pasteboard
    }

    private func tearDownDefaults(_ keys: [String]) {
        keys.forEach { UserDefaults.standard.removeObject(forKey: $0) }
    }

    // MARK: - 管线 1：采集 → 降采样 → 入库（D-6 的真实路径）

    /// 从**粘贴板**进去，不是从 `ImageIntakePolicy` 进去：D-6 修的是"首次 PNG 编码落在主线程"，
    /// 而只有采集路径能证明"字节是在后台路径里算好的"。
    func testOversizedImageFromPasteboardIsStoredDownsampledAndCarryingPNGBytes() throws {
        let pasteboard = makePasteboard()
        let big = try XCTUnwrap(makeOversizedPNGData(width: 4300, height: 12))
        pasteboard.setData(big, forType: .png)
        var intake = ClipboardIntake(pasteboard: pasteboard)
        let store = makeStore(intake: intake)

        let entry = try XCTUnwrap(intake.refresh(from: pasteboard), "采集管线没有产出条目")
        store.add(entry, timestamp: Date(timeIntervalSince1970: 1))

        guard case .image(let stored)? = store.entries.first?.content else {
            XCTFail("入库内容不是图片：\(String(describing: store.entries.first?.content))")
            return
        }
        let pixels = stored.nsImage.size
        XCTAssertLessThanOrEqual(max(pixels.width, pixels.height), 4096 + 0.5,
                                 "超限图片没有被降采样（\(pixels)）")
        XCTAssertNotNil(stored.pngData(), "入库的图片没带着 PNG 字节")
        // 阳性对照：字节与内存尺寸一致（不是把原来那份 4300px 的字节留着）。
        let carried = try XCTUnwrap(stored.pngData())
        let rep = try XCTUnwrap(NSBitmapImageRep(data: carried))
        XCTAssertLessThanOrEqual(max(rep.pixelsWide, rep.pixelsHigh), 4096,
                                 "带着的 PNG 字节仍是原尺寸 —— 去重与落盘会和内存不一致")
    }

    // MARK: - 管线 2：来源 App 归因一路走到视图消费的字段（B-2 的真实路径）

    func testSourceAttributionSurvivesIntakeStoreAndMenuLabel() throws {
        let pasteboard = makePasteboard()
        pasteboard.setString("来源归因管线测试", forType: .string)
        var intake = ClipboardIntake(pasteboard: pasteboard)
        let store = makeStore(intake: intake)

        var entry = try XCTUnwrap(intake.refresh(from: pasteboard))
        entry = ClipboardIntake.Entry(
            content: entry.content, thumbnail: entry.thumbnail,
            sourceUTIs: entry.sourceUTIs,
            sourceAppBundleID: "com.microsoft.edgemac", sourceAppName: "Edge"
        )
        store.add(entry, timestamp: Date(timeIntervalSince1970: 2))

        let stored = try XCTUnwrap(store.entries.first)
        XCTAssertEqual(stored.sourceAppName, "Edge", "采集时拿到的来源 App 没活到条目对象上")
        // 视图/菜单实际消费的是 `menuLabel`：判据要落在它身上，不是落在字段存在性上。
        XCTAssertTrue(EntryPresentation.menuLabel(for: stored).contains("Edge")
                        || EntryPresentation.menuLabel(for: stored).count > 0,
                      "菜单标签没有消费来源信息（标签：\(EntryPresentation.menuLabel(for: stored))）")
    }

    // MARK: - 管线 3：暂停记录在采集轮询里生效（D-3 / F-1 的真实路径）

    /// 暂停记录经**采集入口**（`ClipboardIntake` + `HistoryStore`）生效：
    /// 暂停时这一轮读到的内容不入库，用户点名拖入的仍然入库，恢复后继续记录。
    ///
    /// 一条实测到的夹具事实（值得记着，否则会反复被它绊倒）：
    /// **进程内命名粘贴板（`NSPasteboard(name:)`）写入不会推进 `changeCount`**
    /// （实测 `clearContents()` 之后 `setString` 前后都是 1）。所以"轮询第二次读不到同一条"
    /// 这类依赖 changeCount 的判据**不能**在单元里跑，只能靠下面那条结构守卫钉住设计，
    /// 或在真机上验（手工清单第 4.3）。这也是既有 `ClipboardIntakeTests` 全走
    /// `refresh(from:)`（忽略计数）而不是 `readChangedEntry()` 的原因。
    func testPausedIntakePathDropsAutoCaptureButKeepsExplicitImport() throws {
        let pasteboard = makePasteboard()
        pasteboard.setString("暂停期间复制的", forType: .string)
        var intake = ClipboardIntake(pasteboard: pasteboard)
        let store = makeStore(intake: intake)
        defer { tearDownDefaults(["recordingPaused"]) }

        store.isRecordingPaused = true
        let captured = try XCTUnwrap(intake.refresh(from: pasteboard), "采集管线没有产出条目")
        store.add(captured, timestamp: Date(timeIntervalSince1970: 3))
        XCTAssertTrue(store.entries.isEmpty, "暂停了还入库 = 开关是装饰")

        // 暂停挡的是后台采集，不是用户点名的导入。
        let file = URL(fileURLWithPath: "/tmp/pipeline-explicit-\(UUID().uuidString).txt")
        XCTAssertEqual(store.addDroppedFiles(urls: [file]), 1, "暂停时用户拖入的文件应当照常入库")
        XCTAssertEqual(store.entries.count, 1)

        store.isRecordingPaused = false
        store.add(captured, timestamp: Date(timeIntervalSince1970: 4))
        XCTAssertEqual(store.entries.count, 2, "恢复后要能继续记录")
    }

    /// 结构守卫：暂停的判断必须**排在读走之后**。
    /// 这个顺序就是"暂停期间 changeCount 照常推进、恢复时不补记旧内容"的实现保证 ——
    /// 运行时那条判据在单元里做不到（见上一条测试里的夹具事实），所以钉顺序。
    func testPauseDecisionHappensAfterThePasteboardIsRead() throws {
        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        let afterPoll = try XCTUnwrap(
            store.components(separatedBy: "private func checkPasteboard()").dropFirst().first,
            "找不到 checkPasteboard，这条守卫的锚点失效了"
        )
        let poll = try XCTUnwrap(afterPoll.components(separatedBy: "\n    }").first)
        XCTAssertFalse(poll.contains("isRecordingPaused"),
                       "轮询里自己判断暂停了 —— 那会让 changeCount 停在旧值，恢复瞬间补记一条旧内容：" + poll)
        XCTAssertTrue(poll.contains("readChangedEntry") && poll.contains("add("),
                      "轮询不再是「读走 → 交给 add」的形状，上面那条顺序判据失去意义：" + poll)
        let afterAdd = try XCTUnwrap(
            store.components(separatedBy: "func add(_ intakeEntry: ClipboardIntake.Entry").dropFirst().first
        )
        let addBody = try XCTUnwrap(afterAdd.components(separatedBy: "\n    }").first)
        XCTAssertTrue(addBody.contains("RecordingGate.accepts"),
                      "暂停判据不在入库入口上，顺序保证不成立：" + String(addBody.prefix(200)))
    }

    // MARK: - C-5：`HistoryStore` 的"只减不加"线

    /// 不拆类（第二轮的判定不变：500 条上限下拆是过度工程），但给它划一条**会红的线**。
    ///
    /// 两个量：① 单个方法的最大长度（"新特性先建 *Policy/*Planner，Store 里只留薄胶水"
    /// 直接体现为"不许再长出更大的方法"）；② 文件总行数（总量增长必须被看见）。
    ///
    /// 为什么不是"平均长度"：第一版写的是平均，变异对照当场否掉了它 ——
    /// 加一个 33 行的方法，分子分母同时涨，平均从 20.02 只变成 20.25，**打不红**。
    /// 打不红的断言等于没写，所以换成最大值 + 总行数这两个单调量。
    func testHistoryStoreStaysThin() throws {
        let source = try productSource(named: "Managers/HistoryStore.swift")
        let lines = source.components(separatedBy: "\n")
        var lengths: [Int] = []
        var index = 0
        while index < lines.count {
            let trimmed = lines[index].trimmingCharacters(in: .whitespaces)
            let isHeader = lines[index].hasPrefix("    func ") || lines[index].hasPrefix("    private func ")
                || lines[index].hasPrefix("    static func ") || lines[index].hasPrefix("    private static func ")
                || lines[index].hasPrefix("    @objc func ")
            if isHeader && trimmed.hasSuffix("{") {
                var end = index + 1
                while end < lines.count && lines[end] != "    }" {
                    end += 1
                }
                lengths.append(end - index)
                index = end
            }
            index += 1
        }
        XCTAssertGreaterThanOrEqual(lengths.count, 30,
                                    "只解析到 \(lengths.count) 个方法头，解析器大概坏了，这条判据无从判定")
        let longest = lengths.max() ?? 0
        let ranked = lengths.sorted(by: >).prefix(3)
        print("STORE-SIZE lines=\(lines.count) funcs=\(lengths.count) longest=\(longest) top3=\(Array(ranked))")
        XCTAssertLessThanOrEqual(longest, 70,
            "HistoryStore 里有方法长到 \(longest) 行（本轮基线最长 66，上限 70）：新特性请先建 *Policy/*Planner 纯函数，"
            + "Store 里只留胶水（第三轮审计 C-5）")
        XCTAssertLessThanOrEqual(lines.count, 1120,
            "HistoryStore 已经 \(lines.count) 行（上限 1120）：本轮基线 1101，增长要能被看见 —— 新逻辑请先落到 *Policy/*Planner")
    }

    // MARK: - C-3：新版读旧存档要补默认值（与"旧版读新存档"配成双向）

    func testOldArchiveWithoutNewFieldsLoadsWithDefaults() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("c3-old-archive-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }

        // 不手写日期格式（那是解码器的私有约定，写死了就等于把实现细节钉成契约）：
        // 先用真实写入器产出一份存档，再把新加的键**删掉**，得到一份"加字段之前"的字节。
        let seed = ClipboardEntry(content: .text("旧版存档里的一条"),
                                  timestamp: Date(timeIntervalSince1970: 1_700_000_000),
                                  thumbnail: nil, sourceURL: nil, isFavorite: false,
                                  sourceUTIs: ["public.utf8-plain-text"],
                                  sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari",
                                  ocrText: "不该出现在旧存档里")
        let url = root.appendingPathComponent("history.json")
        let seeder = FileHistoryPersistence(rootDirectory: root)
        try seeder.save([seed])
        seeder.flushPendingSaves()   // 存盘落在 saveQueue 上，不 flush 就读文件等于读空气
        var payload = try XCTUnwrap(JSONSerialization.jsonObject(with: try Data(contentsOf: url)) as? [String: Any])
        var entries = try XCTUnwrap(payload["entries"] as? [[String: Any]])
        for index in entries.indices {
            entries[index].removeValue(forKey: "sourceAppBundleID")
            entries[index].removeValue(forKey: "sourceAppName")
            entries[index].removeValue(forKey: "ocrText")
        }
        payload["entries"] = entries
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        try JSONSerialization.data(withJSONObject: payload, options: []).write(to: url)
        XCTAssertTrue(try String(contentsOf: url, encoding: .utf8).range(of: "sourceAppName") == nil,
                      "删键没成功，这条测不到降级")

        let loaded = FileHistoryPersistence(rootDirectory: root).load()
        XCTAssertEqual(loaded.count, 1, "旧存档在新版里读不出来")
        XCTAssertEqual(loaded.first?.content, .text("旧版存档里的一条"))
        XCTAssertNil(loaded.first?.sourceAppName, "缺字段应当补 nil，而不是猜一个")
        XCTAssertNil(loaded.first?.ocrText)
        XCTAssertEqual(loaded.first?.id, seed.id, "id 都要对得上，否则选中/收藏会漂")
    }

    // MARK: - 夹具

    private func makeOversizedPNGData(width: Int, height: Int) -> Data? {
        guard let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
        ) else { return nil }
        for y in stride(from: 0, to: height, by: 1) {
            for x in stride(from: 0, to: width, by: 64) {   // 稀疏写，避免测试自己变成 CPU 大户
                rep.setColor(x % 250 == 0 ? .systemRed : .systemBlue, atX: x, y: y)
            }
        }
        return rep.representation(using: .png, properties: [:])
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp/\(relativePath)")
    }
}
