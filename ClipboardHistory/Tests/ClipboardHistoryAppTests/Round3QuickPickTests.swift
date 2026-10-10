import AppKit
import Carbon.HIToolbox
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 §5 F-3（⌃⌥⇧V 快速选择浮层）的判据。
///
/// spike 的结论（账本 D-041）：在裸二进制与测试进程里 `NSApp.activate(ignoringOtherApps:)` 是空操作，
/// 面板的 `isKeyWindow` 在激活前后都是 false —— 那条路**没有判别力**，所以"真按键能不能进面板"
/// 不能在这里被证明（它由产品里已经跑着的那条同族路径保证：主窗口呼出后能直接打字）。
/// 因此本文件的策略是：把"输入 → 候选 → 移动 → 提交哪一条"整条链做成可以隔着面板驱动的函数，
/// 逐个钉住；把手感（面板出现的位置、打字延迟）留给人手测清单。
@MainActor
final class Round3QuickPickTests: XCTestCase {
    private func entry(_ text: String,
                       bundleID: String? = "com.apple.Notes",
                       name: String? = nil,
                       pinned: Bool = false,
                       at seconds: TimeInterval = 1) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date(timeIntervalSince1970: seconds),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: bundleID,
            sourceAppName: name ?? bundleID,
            isPinned: pinned
        )
    }

    private func keyEvent(_ keyCode: UInt16) -> NSEvent {
        try! XCTUnwrap(NSEvent.keyEvent(with: .keyDown,
                                         location: .zero,
                                         modifierFlags: [],
                                         timestamp: ProcessInfo.processInfo.systemUptime,
                                         windowNumber: 0,
                                         context: nil,
                                         characters: "",
                                         charactersIgnoringModifiers: "",
                                         isARepeat: false,
                                         keyCode: keyCode))
    }

    // MARK: - 模型

    func testFilteringMatchesPreviewSourceAndFileName() {
        let entries = [entry("剪贴板管理器很好用"),
                       entry("plain", bundleID: "com.microsoft.edgemac", name: "Edge"),
                       entry("无关", bundleID: "com.apple.Notes", name: "备忘录")]
        XCTAssertEqual(QuickPickModel.filtered(entries, query: "剪贴板").count, 1)
        XCTAssertEqual(QuickPickModel.filtered(entries, query: "edge").count, 1,
                       "按来源 App 搜要能搜到（大小写不敏感）")
        XCTAssertEqual(QuickPickModel.filtered(entries, query: "   ").count, 3,
                       "只有空格的查询不该把列表筛空")
        XCTAssertEqual(QuickPickModel.filtered(entries, query: "不存在的东西").count, 0)
    }

    func testUnfilteredListingIsCappedButSearchingIsNot() {
        let many = (1...40).map { entry("记录 \($0)", at: TimeInterval($0)) }
        let model = QuickPickModel(all: many)
        XCTAssertEqual(model.visible.count, QuickPickModel.maximumUnfilteredCount,
                       "没有查询词时列一整屏候选，浮层就成了第二个主窗口")
        var searching = model
        searching.setQuery("记录")
        XCTAssertGreaterThan(searching.visible.count, QuickPickModel.maximumUnfilteredCount,
                             "打字之后候选反而更少：这个浮层就没法用来找老记录")
        XCTAssertEqual(searching.visible.count, 40)
    }

    func testMovementClampsAndNeverWraps() {
        let model = QuickPickModel(all: [entry("一", at: 3), entry("二", at: 2), entry("三", at: 1)])
        var moving = model
        XCTAssertEqual(moving.selection?.shortPreview, "一")
        moving.move(delta: 1)
        moving.move(delta: 1)
        XCTAssertEqual(moving.selection?.shortPreview, "三")
        moving.move(delta: 1)
        XCTAssertEqual(moving.index, 2, "到底了还绕回第一条：用户看不出自己绕了一圈")
        moving.move(delta: -99)
        XCTAssertEqual(moving.index, 0, "顶部同理要夹住")
    }

    func testChangingTheQueryResetsTheSelection() {
        // 这是这个浮层最危险的一种错误：留着旧下标，回车提交一条**不含搜索词**的记录。
        var model = QuickPickModel(all: [entry("甲甲甲", at: 3), entry("乙乙乙", at: 2),
                                         entry("丙丙丙", at: 1), entry("丁丁丁", at: 0)])
        model.move(delta: 2)
        XCTAssertEqual(model.index, 2)
        model.setQuery("甲")
        XCTAssertEqual(model.index, 0, "换搜索词后下标没归零")
        XCTAssertEqual(model.selection?.shortPreview, "甲甲甲",
                       "回车会提交一条与搜索词无关的记录")
    }

    func testEmptyListHasNoSelectionAndStaysPut() {
        var model = QuickPickModel(all: [])
        XCTAssertNil(model.selection)
        model.move(delta: 1)
        XCTAssertEqual(model.index, 0, "空列表里移动不该造出一个越界下标")
        model.setQuery("随便")
        XCTAssertNil(model.selection)
    }

    // MARK: - 按键判定

    func testKeyOutcomes() {
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(125)), .move(1))
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(126)), .move(-1))
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(36)), .commit)
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(76)), .commit, "数字键盘回车也要能提交")
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(53)), .dismiss)
        XCTAssertEqual(QuickPickController.outcome(for: keyEvent(9)), .passThrough,
                       "字母键必须交回输入框，否则打字打不出来")
    }

    func testTypingThenDownThenEnterCommitsTheRightEntry() {
        let store = HistoryStore(clipboardWriter: TestClipboardWriter(),
                                 persistence: RecordingHistoryPersistence(),
                                 retentionPolicy: HistoryRetentionPolicy(maxEntries: 20, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text("alpha 候选"), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 3))
        store.add(ClipboardIntake.Entry(content: .text("beta 候选"), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 2))
        store.add(ClipboardIntake.Entry(content: .text("gamma 候选"), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))

        var committed: [ClipboardEntry] = []
        let controller = QuickPickController(historyStore: { store }, commit: { committed.append($0) })
        controller.refreshEntries()
        controller.queryChanged("候选")
        XCTAssertEqual(controller.handle(keyEvent: keyEvent(126)), .move(-1))   // ↑ 已经在上界
        XCTAssertEqual(controller.handle(keyEvent: keyEvent(125)), .move(1))    // ↓ 第二条
        XCTAssertEqual(controller.handle(keyEvent: keyEvent(36)), .commit)
        XCTAssertEqual(committed.count, 1, "回车没有提交")
        XCTAssertEqual(committed.first?.shortPreview, "beta 候选",
                       "移动一下之后回车提交的还是第一条 —— 下标没被表格选中同步")
        XCTAssertFalse(controller.isVisible, "提交后面板必须收起：留着一屏剪贴板内容在屏幕上是暴露面")
    }

    func testEscapeCommitsNothing() {
        let store = HistoryStore(clipboardWriter: TestClipboardWriter(),
                                 persistence: RecordingHistoryPersistence(),
                                 retentionPolicy: HistoryRetentionPolicy(maxEntries: 20, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text("别提交我"), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        var committed: [ClipboardEntry] = []
        let controller = QuickPickController(historyStore: { store }, commit: { committed.append($0) })
        controller.refreshEntries()
        XCTAssertEqual(controller.handle(keyEvent: keyEvent(53)), .dismiss)
        XCTAssertTrue(committed.isEmpty, "Esc 却提交了一条：那比没有浮层更糟")
    }

    func testEnterWithNoMatchesCopiesNothing() {
        let store = HistoryStore(clipboardWriter: TestClipboardWriter(),
                                 persistence: RecordingHistoryPersistence(),
                                 retentionPolicy: HistoryRetentionPolicy(maxEntries: 20, maxAgeDays: nil))
        store.add(ClipboardIntake.Entry(content: .text("唯一一条"), thumbnail: nil,
                                        sourceUTIs: ["public.utf8-plain-text"],
                                        sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                  timestamp: Date(timeIntervalSince1970: 1))
        var committed: [ClipboardEntry] = []
        let controller = QuickPickController(historyStore: { store }, commit: { committed.append($0) })
        controller.refreshEntries()
        controller.queryChanged("没有这个")
        XCTAssertEqual(controller.handle(keyEvent: keyEvent(36)), .commit)
        XCTAssertTrue(committed.isEmpty, "搜不到时回车不许提交任何东西（更不能提交旧的第一条）")
    }

    func testRowTitleFlattensNewlinesMarksPinnedAndNeverBlank() {
        let multiline = entry("第一行\n第二行", at: 5)
        let title = QuickPickController.rowTitle(for: multiline)
        XCTAssertFalse(title.contains("\n"), "行文案里带换行：34pt 的行高会被撑开")
        XCTAssertTrue(title.contains("第一行"))
        XCTAssertTrue(QuickPickController.rowTitle(for: entry("x", pinned: true, at: 6)).hasPrefix("置顶"))
        XCTAssertTrue(QuickPickController.rowTitle(for: entry("   ", at: 7)).contains("（空）"),
                      "空预览也要有个说法，不能画一行只有时间的东西")
    }

    // MARK: - 接线守卫

    func testHotKeyAndMenuAreWired() throws {
        XCTAssertEqual(HotKeyAction.quickPick.hotKeyIdentifier, 3,
                       "快捷键 id 撞了已有动作的话，Carbon 只会注册到一个上")
        XCTAssertEqual(HotKeyAction.allCases.count, 3)
        let shortcut = HotKeyAction.quickPick.defaultShortcut
        XCTAssertEqual(shortcut.keyCode, UInt32(kVK_ANSI_V))
        XCTAssertEqual(shortcut.modifiers, UInt32(controlKey | optionKey | shiftKey),
                       "默认组合键漂了：⌘⇧V 在浏览器/编辑器里是「粘贴并匹配样式」，不能被全局抢走")
        XCTAssertNotEqual(shortcut, HotKeyShortcut(keyCode: UInt32(kVK_ANSI_V),
                                                   modifiers: UInt32(cmdKey | shiftKey)))
        XCTAssertTrue(shortcut.isValid)

        let shell = codeOnly(try productSource(named: "Managers/ApplicationShell.swift"))
        XCTAssertTrue(shell.contains("commit: { [weak self] entry in self?.copyAndPasteEntry(entry) }"),
                      "浮层没接产品里现成的「复制 + 粘回原应用」那条路")
        XCTAssertTrue(shell.contains("case .showQuickPick:"), "菜单命令没有分派到浮层")

        let menu = codeOnly(try productSource(named: "Managers/MenuBarController.swift"))
        XCTAssertTrue(menu.contains("case .showQuickPick:"), "菜单里那一项没有 selector")

        let delegate = codeOnly(try productSource(named: "Managers/AppDelegate.swift"))
        XCTAssertTrue(delegate.contains("quickPickHotKeySettings.start()"),
                      "快捷键设置建了但没注册 = 按下去没有反应")
        XCTAssertTrue(delegate.contains("name: .quickPickHotKeyPressed"), "通知没接")

        let commands = codeOnly(try productSource(named: "Models/AppCommand.swift"))
        XCTAssertTrue(commands.contains(".showQuickPick,"), "菜单栏命令表里没有它")
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
        throw NSError(domain: "Round3QuickPickTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
