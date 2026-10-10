import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 §5 功能项 F-1 / F-4 / F-5 的判据。
///
/// 按 `AGENTS.md` 的 DoD：能从产品入口进的就不只测纯函数 —— 下面每个特性都同时有
/// 纯函数真值表和一条走 `HistoryStore` 的管线级用例。
@MainActor
final class Round3FeatureTests: XCTestCase {
    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 5, maxAgeDays: nil)
        )
    }

    private func intake(_ text: String, bundleID: String?, name: String? = nil) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(content: .text(text), thumbnail: nil,
                              sourceUTIs: ["public.utf8-plain-text"],
                              sourceAppBundleID: bundleID, sourceAppName: name ?? bundleID)
    }

    private func cleanKeys() {
        UserDefaults.standard.removeObject(forKey: CapturePolicy.userExcludedKey)
        UserDefaults.standard.removeObject(forKey: "recordingPaused")
        UserDefaults.standard.removeObject(forKey: OCRPolicy.modeKey)
    }

    // MARK: - F-1 按 App 排除

    func testCapturePolicyTruthTable() {
        let excluded: Set<String> = ["com.agilebits.onepassword7"]
        XCTAssertTrue(CapturePolicy.accepts(sourceAppBundleID: nil, paused: false,
                                            isUserInitiated: false, excluded: excluded),
                      "来源读不到时不能挡 —— 那会让历史记录莫名其妙不工作")
        XCTAssertFalse(CapturePolicy.accepts(sourceAppBundleID: "com.agilebits.onepassword7", paused: false,
                                             isUserInitiated: false, excluded: excluded),
                       "被排除 App 的复制不该入库")
        XCTAssertTrue(CapturePolicy.accepts(sourceAppBundleID: "com.agilebits.onepassword7", paused: false,
                                            isUserInitiated: true, excluded: excluded),
                      "用户点名的导入不受排除名单影响")
        XCTAssertFalse(CapturePolicy.accepts(sourceAppBundleID: "com.apple.Notes", paused: true,
                                             isUserInitiated: false, excluded: excluded))
    }

    func testDefaultExclusionListCoversPasswordManagersAndKeychain() {
        let defaults = CapturePolicy.defaultExcludedBundleIDs
        XCTAssertTrue(defaults.contains("com.agilebits.onepassword7"), "1Password 必须在默认名单里")
        XCTAssertTrue(defaults.contains("com.apple.keychainaccess"), "钥匙串访问必须在默认名单里")
        XCTAssertTrue(defaults.contains { $0.lowercased().contains("bitwarden") || $0.lowercased().contains("lastpass") },
                      "主流第三方密码管理器至少要有一个是默认排除的")
    }

    func testExcludedAppCopyIsNotRecordedThroughStore() throws {
        cleanKeys()
        defer { cleanKeys() }
        // 读的是注入的 suite 而不是标准域。往 xctest 进程的 `UserDefaults.standard` 写键
        // 会污染同一次运行里的别的用例，而 `policyDefaults` 的存在就是为了不必这么干 ——
        // 判据本身仍然走产品入口 `HistoryStore.add`，所以"设置页写的那个键被采集侧读到"
        // 这一段仍然是真验过的。
        let suite = "Round3Exclusion-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        defaults.set(CapturePolicy.encodeUserExcluded(["com.evil.notes"]),
                     forKey: CapturePolicy.userExcludedKey)
        let store = makeStore()
        store.policyDefaults = defaults

        store.add(intake("密码管理器里复制的", bundleID: "com.evil.notes"),
                  timestamp: Date(timeIntervalSince1970: 5))
        XCTAssertTrue(store.entries.isEmpty, "用户加的排除项没生效")

        // 默认名单不依赖任何用户配置：装好就该挡住钥匙串。
        store.add(intake("钥匙串里的密码", bundleID: "com.apple.keychainaccess"),
                  timestamp: Date(timeIntervalSince1970: 5.5))
        XCTAssertTrue(store.entries.isEmpty, "默认排除名单没在采集侧生效")

        store.add(intake("普通 App 复制的", bundleID: "com.apple.Notes"),
                  timestamp: Date(timeIntervalSince1970: 6))
        XCTAssertEqual(store.entries.count, 1, "排除不能扩大到普通 App")

        // 用户点名的动作（拖入文件）优先于名单。
        store.add(intake("我自己拖进来的", bundleID: "com.evil.notes"),
                  timestamp: Date(timeIntervalSince1970: 7), isUserInitiated: true)
        XCTAssertEqual(store.entries.count, 2, "显式导入被排除名单挡掉了 —— 那会静默丢用户的东西")
    }

    func testExclusionListEncodingRoundTrip() {
        XCTAssertEqual(CapturePolicy.decodeUserExcluded(CapturePolicy.encodeUserExcluded(
            [" b.com ", "a.com", "b.com", ""])), Set(["a.com", "b.com"]))
        XCTAssertTrue(CapturePolicy.decodeUserExcluded("").isEmpty)
        // 排序后写入 ⇒ 同一集合永远得到同一个串（否则设置页会来回抖）
        XCTAssertEqual(CapturePolicy.encodeUserExcluded(["b.com", "a.com"]),
                       CapturePolicy.encodeUserExcluded(["a.com", "b.com"]))
    }

    // MARK: - F-4 OCR 只索引不落盘

    func testOCRPolicyDecisions() {
        XCTAssertEqual(OCRPolicy.mode(from: UserDefaults(suiteName: UUID().uuidString)!), .persisted,
                       "没写过键时必须与历史行为一致（随历史保存）")
        XCTAssertTrue(OCRPolicy.persistsResult(.persisted))
        XCTAssertFalse(OCRPolicy.persistsResult(.indexOnly))
        XCTAssertTrue(OCRPolicy.shouldSchedule(isEnabled: true, hasImage: true))
        XCTAssertFalse(OCRPolicy.shouldSchedule(isEnabled: false, hasImage: true),
                       "关掉开关后什么都不排（D-3 的判据本体）")
        XCTAssertFalse(OCRPolicy.shouldSchedule(isEnabled: true, hasImage: false))
    }

    func testOCRSearchableTextPrefersEntryThenIndex() {
        let entry = ClipboardEntry(content: .text("x"), timestamp: Date(), thumbnail: nil,
                                   sourceURL: nil, sourceUTIs: [], ocrText: "落盘的那份")
        XCTAssertEqual(OCRPolicy.searchableText(entryOcrText: entry.ocrText, indexValue: "内存那份"),
                       "落盘的那份")
        XCTAssertEqual(OCRPolicy.searchableText(entryOcrText: nil, indexValue: "内存那份"), "内存那份")
        XCTAssertNil(OCRPolicy.searchableText(entryOcrText: nil, indexValue: nil))
    }

    func testImageContentIsTheOCRTargetRule() {
        XCTAssertTrue(ClipboardEntryContent.text("x").isOCRTarget == false)
        XCTAssertTrue(ClipboardEntryContent.file(URL(fileURLWithPath: "/tmp/截图.PNG")).isOCRTarget)
        XCTAssertFalse(ClipboardEntryContent.file(URL(fileURLWithPath: "/tmp/合同.pdf")).isOCRTarget)
        XCTAssertFalse(ClipboardEntryContent.files([URL(fileURLWithPath: "/tmp/a.png")]).isOCRTarget,
                       "多文件条目本轮不做 OCR（没有单一图可解）")
    }

    // MARK: - F-5 固定 + 导出导入

    func testPinnedEntriesStayOnTopAndSurvivePromotion() throws {
        let store = makeStore()
        for index in 1...3 {
            store.add(intake("记录 \(index)", bundleID: "com.apple.Notes"),
                      timestamp: Date(timeIntervalSince1970: TimeInterval(index)))
        }
        let newest = store.entries[0]
        store.perform(.togglePin(newest))
        XCTAssertEqual(store.filteredEntries.first?.id, newest.id, "固定项没有置顶")
        XCTAssertTrue(try XCTUnwrap(store.entries.first { $0.id == newest.id }?.isPinned),
                      "固定动作没有落到条目上")

        // 新的复制进来（会顶到最前）也不能把固定项挤下去
        store.add(intake("更新的记录", bundleID: "com.apple.Notes"),
                  timestamp: Date(timeIntervalSince1970: 99))
        XCTAssertEqual(store.filteredEntries.first?.id, newest.id,
                       "固定项被复用提升挤下去了 —— 常用片段又找不到固定位置了")
        XCTAssertEqual(store.filteredEntries[1].content, .text("更新的记录"))
    }

    func testRetentionNeverEvictsPinned() throws {
        let store = makeStore()   // maxEntries = 5
        for index in 1...4 {
            store.add(intake("老记录 \(index)", bundleID: "com.apple.Notes"),
                      timestamp: Date(timeIntervalSince1970: TimeInterval(index)))
        }
        store.perform(.pinSelection(isPinned: true))     // 当前选中的那条固定住
        let pinnedID = try XCTUnwrap(store.entries.first(where: \.isPinned)?.id)

        // 再灌进超过上限的新记录
        for index in 1...6 {
            store.add(intake("新记录 \(index)", bundleID: "com.apple.Notes"),
                      timestamp: Date(timeIntervalSince1970: 100 + Double(index)))
        }
        XCTAssertTrue(store.entries.contains { $0.id == pinnedID },
                      "固定项被保留策略裁掉了 —— 「固定」就成了假承诺")
    }

    func testArchiveExportImportRoundTripKeepsState() throws {
        let store = makeStore()
        store.add(intake("要带走的文本", bundleID: "com.apple.Safari", name: "Safari"),
                  timestamp: Date(timeIntervalSince1970: 7))
        let only = try XCTUnwrap(store.entries.first)
        store.perform(.togglePin(only))
        store.perform(.toggleFavorite(only))

        let (data, summary) = store.exportArchiveJSON()
        XCTAssertEqual(summary.exportedCount, 1)
        XCTAssertEqual(summary.skippedImageCount, 0)
        XCTAssertTrue(summary.exportedCount <= store.entries.count)
        // 导出内容必须是人读的 JSON，且不含图片字节
        let object = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(try XCTUnwrap(object?["version"] as? Int), ArchiveTransfer.exchangeVersion)
        XCTAssertFalse(String(data: data, encoding: .utf8)!.contains("base64"),
                       "默认导出不该悄悄带上图片数据")

        // 删掉再导回来。注意**不能**用 `.clear`：那是"清空未收藏记录"，
        // 上面刚把这条收藏了，按设计它会留着（`HistoryPrivacyCopy.clearBehavior` 写明了这个行为），
        // 于是判据 `entries.isEmpty` 永远红 —— 那是我用错了动作，不是产品缺陷。
        store.perform(.delete(only))
        XCTAssertTrue(store.entries.isEmpty, "删除没生效，后面的往返判据无从判定")
        let imported = try store.importArchiveJSON(data)
        XCTAssertEqual(imported.importedCount, 1)
        let back = try XCTUnwrap(store.entries.first)
        XCTAssertEqual(back.content, .text("要带走的文本"))
        XCTAssertTrue(back.isFavorite, "收藏状态要在往返里保住")
        XCTAssertTrue(back.isPinned, "固定状态要在往返里保住")
        XCTAssertEqual(back.sourceAppName, "Safari", "来源归因也要带走")

        // 再导一次同样的内容：同 id 视为重复，不产生第二条
        let again = try store.importArchiveJSON(data)
        XCTAssertEqual(again.skippedDuplicateCount, 1)
        XCTAssertEqual(store.entries.count, 1)
    }

    /// F-4 的端到端：识别文本回来之后，「只索引不落盘」到底有没有把文字留在内存里。
    ///
    /// 这一条补的是 D-038 自己记下却没闭合的那半句：以前这段分支只能靠"真跑一次 Vision"
    /// 才执行得到，于是它在仓库里从来没被执行过一次。现在识别器可注入（`HistoryStore.ocrRecognizer`），
    /// 于是 `add` → 后台识别 → 写回分支 → 落盘 / 搜索 整条链从产品入口走一遍。
    /// 断言刻意看**磁盘上的字节**：那才是"不落盘"这句话的意思。
    func testIndexOnlyOCRStaysSearchableButLeavesTheArchiveClean() async throws {
        let suiteName = "Round3F4-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let root = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("Round3F4-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }

        let persistence = FileHistoryPersistence(rootDirectory: root)
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: persistence,
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 20, maxAgeDays: nil)
        )
        store.policyDefaults = defaults
        store.ocrRecognizer = { _ in "截图里的口令 zebra-42" }

        // 先确认"什么都不落盘"这条不是空转：没有识别结果时磁盘上当然也没有文字。
        OCRPolicy.setMode(.indexOnly, defaults: defaults)
        let firstImage = try makeStoredImage(color: .systemTeal, size: NSSize(width: 60, height: 24))
        store.add(ClipboardIntake.Entry(content: .image(firstImage), thumbnail: firstImage,
                                        sourceUTIs: ["public.png"],
                                        sourceAppBundleID: "com.apple.Screenshot",
                                        sourceAppName: "截图"),
                  timestamp: Date(timeIntervalSince1970: 10))
        try await awaitOCR(store, text: "zebra-42")

        let archiveURL = root.appendingPathComponent("history.json")
        let bytes = try Data(contentsOf: archiveURL)
        let archive = String(decoding: bytes, as: UTF8.self)
        XCTAssertFalse(archive.contains("zebra-42"),
                       "只索引模式下识别文本仍然写进了 history.json")
        XCTAssertFalse(archive.contains("ocrText"),
                       "条目上仍然带着 ocrText 字段：说明写回分支看的是模式之外的东西")
        // 同一份文字必须仍然搜得到 —— 否则"不落盘"就变成"把功能关掉了"
        store.perform(.updateSearch("zebra-42"))
        XCTAssertEqual(store.filteredEntries.count, 1,
                       "只索引模式下搜不到：内存索引没接上，等于 OCR 白跑一次")
        XCTAssertNil(store.entries.first?.ocrText)

        // 正向对照：切成落盘模式后同样的路径必须把文字写进条目与存档。
        // 没有这半条，上面那句"档案里没有"可以靠"OCR 根本没跑"糊过去。
        OCRPolicy.setMode(.persisted, defaults: defaults)
        let secondImage = try makeStoredImage(color: .systemOrange, size: NSSize(width: 60, height: 24))
        store.perform(.updateSearch(""))
        store.add(ClipboardIntake.Entry(content: .image(secondImage), thumbnail: secondImage,
                                        sourceUTIs: ["public.png"],
                                        sourceAppBundleID: "com.apple.Screenshot",
                                        sourceAppName: "截图"),
                  timestamp: Date(timeIntervalSince1970: 20))
        try await awaitOCR(store, text: "zebra-42", expectingWrittenIntoEntry: true)

        persistence.flushPendingSaves()
        let after = String(decoding: try Data(contentsOf: archiveURL), as: UTF8.self)
        XCTAssertTrue(after.contains("zebra-42"),
                      "落盘模式下识别文本没进存档：那这条正向对照是空的")
        XCTAssertTrue(store.entries.contains { $0.ocrText?.contains("zebra-42") == true })
    }

    /// 等后台识别回到主线程写完回。轮询而不是固定 sleep：
    /// 固定等待在这类测试里只有两种结局 —— 要么偶发失败，要么把断言写成"永远成立"。
    private func awaitOCR(_ store: HistoryStore, text: String,
                          expectingWrittenIntoEntry: Bool = false) async throws {
        let predicate: () -> Bool = {
            store.perform(.updateSearch(text))
            let searchable = !store.filteredEntries.isEmpty
            store.perform(.updateSearch(""))
            guard searchable else { return false }
            // 落盘模式还要等"条目对象自己带上 ocrText"；只索引模式下这条永远不成立，
            // 所以它必须是参数而不是无条件断言。
            // （第一版我在这里加了 `shortPreview.contains("截图")`，把**来源 App 名**当成了
            //  预览文本 —— 图片条目的预览是"图片"，于是这条等待永远不满足。）
            if expectingWrittenIntoEntry {
                return store.entries.contains { $0.ocrText?.contains(text) == true }
            }
            return true
        }
        for _ in 0..<40 {
            if predicate() { return }
            try await Task.sleep(nanoseconds: 50_000_000)
        }
        // 只索引模式下条目永远不带 ocrText，所以那里等的是"搜索能命中"（内存索引），
        // 两种模式都靠同一个轮询走到稳定态。
        XCTAssertTrue(predicate(), "2 秒内 OCR 的写回没发生（识别器没被调用？还是分支被跳过了？）")
    }

    func testExportWarningTextSaysWhatIsMissing() {
        let text = ArchiveTransfer.exportWarningText(
            summary: ArchiveTransfer.Summary(exportedCount: 3, skippedImageCount: 2))
        XCTAssertTrue(text.contains("3"), text)
        XCTAssertTrue(text.contains("2"), text)
        XCTAssertTrue(text.contains("敏感") || text.contains("密码"), "导出前必须提醒内容敏感：" + text)
    }

    // MARK: - 接线守卫（UI 上真有这些入口）

    func testSettingsPanesExposeTheNewControls() throws {
        let settings = codeOnly(try productSource(named: "Views/SettingsView.swift"))
        XCTAssertTrue(settings.contains("不记录这些 App 的复制"), "隐私页没有按 App 排除")
        XCTAssertTrue(settings.contains("只索引不落盘"), "隐私页没有 OCR 存放方式")
        XCTAssertTrue(settings.contains("导出历史…"), "数据页没有导出")
        XCTAssertTrue(settings.contains("导入历史…"), "数据页没有导入")
        XCTAssertTrue(settings.contains("NSSavePanel"), "导出没走保存面板")
        XCTAssertTrue(settings.contains("NSOpenPanel"), "导入没走打开面板")

        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("pinSelection"), "表头没有固定/取消固定的批量入口")

        // 「固定」在界面上必须有两处：行上的状态徽标 + 单条记录的动作入口。
        // 只提供批量按钮是不够的 —— 表头那排按钮只在多选（selectedCount > 1）时出现，
        // 只选一条时它不在，"固定这一条"就没有任何入口（§5 F-5 要求可达，不是要求有字段）。
        let row = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        // 判"徽标被画在行上"要看**使用处**：`RowPinnedBadge` 的类型定义一直留在文件里，
        // 只 contains 类型名的话，把那一行从 HStack 删掉守卫照样绿（变异实测过，见账本）。
        XCTAssertTrue(row.contains("RowPinnedBadge(isPinned: entry.isPinned)"),
                      "行里没有把条目的固定状态画成徽标")
        let pill = codeOnly(try productSource(named: "Views/GlassControls.swift"))
        // 判据写成"有一颗按钮的动作接的是 pinAction"而不是"文件里出现过 pinAction 这个词"：
        // 后者把按钮整块删掉照样绿（声明还在），那是字符串守卫的典型假绿。
        XCTAssertTrue(pill.contains("action: pinAction"), "详情浮层没有真的画上固定按钮：单条记录无法固定")
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("isPinned: entry.isPinned"), "浮层的固定状态没接条目")
        XCTAssertTrue(detail.contains(".togglePin(entry)"), "浮层的固定按钮没接动作")

        // "实心 pin 才表示已固定"这条事实钉在纯函数上：字面量因此只允许出现在
        // `PinTogglePresentation` 一处，视图里各处引用它（D-034 之后 HistoryRowViews 里
        // 已经不该再有 SF Symbol 字面量了）。
        XCTAssertEqual(PinTogglePresentation.symbolName(isPinned: true), "pin.fill")
        XCTAssertEqual(PinTogglePresentation.symbolName(isPinned: false), "pin")
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
