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

    func testSourceOnlyMatchNamesItsReasonWhileOtherMatchesStayBare() {
        let sourceOnly = entry("合同 终版 v3.pdf", bundleID: "com.apple.finder", name: "访达")
        let titleMatch = entry("访达里的文件", bundleID: "com.apple.finder", name: "访达")
        XCTAssertEqual(QuickPickModel.sourceMatchReason(for: sourceOnly, query: "访达"), "访达",
                       "查询词只命中来源 App 时拿不到理由 ⇒ 行上没有任何可见的命中依据")
        XCTAssertNil(QuickPickModel.sourceMatchReason(for: titleMatch, query: "访达"),
                     "预览里已经看得见「访达」，再补一句来源就是噪音")
        XCTAssertNil(QuickPickModel.sourceMatchReason(for: sourceOnly, query: ""),
                     "没在搜索时不该给每一行加来源后缀")
        XCTAssertNil(QuickPickModel.sourceMatchReason(for: sourceOnly, query: "合同"),
                     "命中的是文件名而不是来源，理由不该写成来源")
        let sourceTitle = QuickPickController.rowTitle(for: sourceOnly, query: "访达")
        XCTAssertTrue(sourceTitle.contains("来自 访达"),
                      "产品行文案里没有命中理由：\(sourceTitle)")
        let unqueried = QuickPickController.rowTitle(for: sourceOnly)
        XCTAssertEqual(unqueried, "合同 终版 v3.pdf",
                       "没有查询词时行文案必须只剩预览（R430：时间改到右侧定宽列）：\(unqueried)")
        XCTAssertFalse(unqueried.contains("来自"),
                       "没有查询词时不该出现来源后缀：\(unqueried)")
        XCTAssertEqual(QuickPickController.rowTime(for: sourceOnly),
                       ClipboardDateFormatters.sidebarTime.string(from: sourceOnly.timestamp),
                       "右侧时间列没有沿用侧栏那一套 formatter ⇒ 同一件时间在浮层里换了一种写法")
        XCTAssertFalse(unqueried.contains(ClipboardDateFormatters.sidebarTime
                                            .string(from: sourceOnly.timestamp)),
                       "时间仍然拼在可截断的标题串里：\(unqueried)")
    }

    /// R430：长标题不许把时间挤出画布。
    ///
    /// 修之前 `rowTitle` 把预览与时间拼成一条 `.byTruncatingTail` 的字符串 ——
    /// `quickpick-list` 第 0/4 行（长文本、密钥）整行都没有时间。现在时间只走右侧列。
    func testRowTimeSurvivesTheLongestTitle() {
        let long = entry(String(repeating: "长标题", count: 40), at: 9)
        let title = QuickPickController.rowTitle(for: long)
        let time = ClipboardDateFormatters.sidebarTime.string(from: long.timestamp)
        XCTAssertFalse(title.contains(time),
                       "时间又回到了标题串里 ⇒ 长标题会把它截掉：\(title)")
        XCTAssertEqual(QuickPickController.rowTime(for: long), time,
                       "右侧时间列拿到的不是这条记录的时间")
        XCTAssertFalse(QuickPickController.rowTime(for: entry("x", at: 9)).isEmpty,
                       "时间列允许为空 ⇒ 短标题行会少一格，右沿重新变参差")
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

    /// 浮层在快捷键回调链上：那里一次崩溃的表现是"按下 ⌃⌥⇧V 应用直接没了"，
    /// 所以这条 UI 路径里不许有力解包。判的是源码形状 —— 它防的是回归，不是新功能。
    func testPanelPathHasNoForceUnwraps() throws {
        let source = codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        XCTAssertFalse(source.contains("contentView!"),
                       "面板构建里力解包 contentView：一次布局时序变化就会让应用在快捷键上崩掉")
        XCTAssertTrue(source.contains("guard let content = panel.contentView"),
                      "安静不显示的那条回退路径不见了")
    }

    // MARK: - 面板真的把候选画出来了（在屏判据，要环境变量才跑）

    /// `show()` 之后那张表里**必须真的有条目**，打字之后必须收窄。
    ///
    /// 为什么单独一条：D-041 说"面板拿不到 key window"，那否掉的是**按键路由**，
    /// 不是"面板建不建得起来、表里有没有行"。而行级更新计划（`QuickPickRowDiff`）
    /// 一旦算错，表现恰恰是"表空了/行数对不上"——纯函数测试看不见（它只测计划），
    /// 而 `testTypingThenDownThenEnterCommitsTheRightEntry` 也看不见（那里 `table` 是 nil，
    /// `rebuildRows()` 直接早退）。这一条走的是**真面板 + 真 NSTableView**。
    ///
    /// 开关：`CLIPBOARD_HISTORY_UI_MOTION=1`（会真的开一个浮层窗口）。
    func testPanelPopulatesItsTableOnShowAndNarrowsOnTyping() throws {
        try XCTSkipUnless(ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_MOTION"] == "1",
                          "会开一个真浮层窗口并抢前台：设 CLIPBOARD_HISTORY_UI_MOTION=1 才跑")
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil))
        for index in 0..<5 {
            // 走采集入口（`ClipboardIntake.Entry`），不是模型那份 `ClipboardEntry`：
            // `store.add` 要的是前者，而这条判据要的就是"从产品入口进"。
            store.add(ClipboardIntake.Entry(
                content: .text("候选 \(index)：一段用来数行的文本"),
                thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
                sourceAppBundleID: "com.apple.Notes", sourceAppName: "备忘录"),
                timestamp: Date())
        }
        let controller = QuickPickController(historyStore: { store }, commit: { _ in })
        controller.show()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        defer { controller.hide() }

        let table = try XCTUnwrap(Self.findTable(ownedBy: controller),
                                  "show() 之后找不到那张 NSTableView ⇒ 面板没建起来，这条判据要红")
        XCTAssertEqual(table.numberOfRows, 5,
                       "面板里的候选数不对：`rebuildRows()` 的插删计划或数据源回读出了问题")

        controller.queryChanged("候选 3")
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        XCTAssertEqual(table.numberOfRows, 1,
                       "打字之后候选没收窄 ⇒ 行级更新计划算错了（AppKit 看到的行数与模型不一致时，表现就是空表）")
        controller.queryChanged("候选")
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        XCTAssertEqual(table.numberOfRows, 5, "删回去时候选必须重新长回来（这一步走的是 insertRows 分支）")
    }

    /// 在**所有窗口**里找那张由这个控制器当数据源的表。
    /// 不去加一个"为了测试把 table 暴露出去"的产品 API：面板已经建出来了，遍历就能看到，
    /// 而读自己造出来的东西不算侵入产品。
    private static func findTable(ownedBy controller: QuickPickController) -> NSTableView? {
        let target = controller as AnyObject
        for window in NSApp.windows {
            guard let content = window.contentView else { continue }
            if let found = walk(content, target: target) { return found }
        }
        return nil
    }

    private static func walk(_ view: NSView, target: AnyObject) -> NSTableView? {
        if let table = view as? NSTableView, (table.dataSource as AnyObject?) === target { return table }
        for sub in view.subviews {
            if let found = walk(sub, target: target) { return found }
        }
        return nil
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
