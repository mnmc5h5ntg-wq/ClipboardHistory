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
