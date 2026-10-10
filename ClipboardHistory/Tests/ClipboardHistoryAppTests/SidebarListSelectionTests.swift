import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 D-1（修法③）：侧栏换成 `List(selection:)`，拖出只从把手发起。
///
/// 这里钉三层，缺一层都会留下"看着像修好了"的空间：
/// ① **store 侧**：`List` 汇报上来的集合怎么落成权威状态（含"不可见 id 必须丢掉"）；
/// ② **判据侧**：`EntryDragGate.prepareForDrag` 的真值表 —— 行体永远不许开拖出会话，
///    那正是 D-1 的形状（整行挂 `onDrag` ⇒ 拖选整片失效）；
/// ③ **接线侧**：视图真的走的是系统 `List(selection:)`，而且没有偷偷把方向键/自绘选中态加回来。
@MainActor
final class SidebarListSelectionTests: XCTestCase {
    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    private func textEntry(_ string: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(string), thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
        )
    }

    // MARK: - ① store 侧：List 汇报的集合

    func testListSelectionBecomesTheStoreSelection() {
        let store = makeStore()
        store.add(textEntry("一"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(textEntry("二"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(textEntry("三"), timestamp: Date(timeIntervalSince1970: 1))
        let visible = store.filteredEntries
        let primaryBefore = try? XCTUnwrap(store.selectedEntry?.id)

        store.perform(.setSelection([visible[0].id, visible[visible.count - 1].id]))

        XCTAssertEqual(store.selectedEntryIDs, Set([visible[0].id, visible[visible.count - 1].id]))
        XCTAssertEqual(store.selectedCount, 2)
        XCTAssertEqual(store.selectedEntry?.id, primaryBefore,
                       "主选中项还在新集合里时不该跳走 —— 详情区会闪成另一条")
    }

    func testListSelectionFallsBackToTheFirstVisibleRowWhenThePrimaryIsGone() throws {
        let store = makeStore()
        store.add(textEntry("一"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(textEntry("二"), timestamp: Date(timeIntervalSince1970: 2))
        store.add(textEntry("三"), timestamp: Date(timeIntervalSince1970: 1))
        let visible = store.filteredEntries
        let primaryBefore = try XCTUnwrap(store.selectedEntry?.id)
        // 这次集合**不含**原来的主选中项（真实的 ⌘ 加选/框选会把锚点排除在外）。
        let ids = Set(visible.map(\.id).filter { $0 != primaryBefore })
        XCTAssertFalse(ids.isEmpty)

        store.perform(.setSelection(ids))

        let expected = visible.first { ids.contains($0.id) }?.id
        XCTAssertEqual(store.selectedEntry?.id, expected,
                       "主选中项没了就按列表顺序取第一条命中项，不能取 Set 里随便一个（Set 没有顺序，详情区会随机跳）")
    }

    func testListSelectionKeepsTheCurrentPrimaryEntryWhenItStaysSelected() {
        let store = makeStore()
        store.add(textEntry("一"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(textEntry("二"), timestamp: Date(timeIntervalSince1970: 2))
        let ids = store.entries.map(\.id)
        store.perform(.selectOnly(store.entries[1]))

        store.perform(.setSelection([ids[0], ids[1]]))

        XCTAssertEqual(store.selectedEntry?.id, ids[1],
                       "shift 扩选时主选中项不该跳走 —— 详情区会闪成另一条")
    }

    func testListSelectionDropsIDsThatAreNotVisible() throws {
        let store = makeStore()
        store.add(textEntry("苹果派"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(textEntry("香蕉"), timestamp: Date(timeIntervalSince1970: 2))
        let bananaID = try XCTUnwrap(
            store.entries.first { $0.shortPreview.contains("香蕉") }?.id
        )
        store.perform(.updateSearch("苹果"))

        // 模拟"列表把已经不在过滤结果里的 id 一起报回来"（过滤与选中竞态的真实形状）。
        store.perform(.setSelection([store.entries[0].id, bananaID]))

        XCTAssertEqual(store.selectedEntryIDs, [store.entries[0].id],
                       "看不见的条目被留在选中集合里 ⇒ 之后的批量收藏/删除会作用在用户看不见的记录上")
        XCTAssertFalse(store.selectedEntryIDs.contains(bananaID))
    }

    func testEmptyListSelectionClearsThePrimaryEntry() {
        let store = makeStore()
        store.add(textEntry("一"), timestamp: Date(timeIntervalSince1970: 1))
        store.perform(.setSelection([]))

        XCTAssertTrue(store.selectedEntryIDs.isEmpty)
        XCTAssertNil(store.selectedEntry)
    }

    // MARK: - ② 判据侧：拖出的分工

    func testDragGateRefusesTheRowBodyEvenWhenPayloadExists() {
        // 这一条就是缺陷 D-1 本体：载荷再满，行体也不许开拖出会话。
        XCTAssertFalse(EntryDragGate.prepareForDrag(origin: .rowBody, content: .text("可拖的文本")),
                       "行体开拖出会话 = 列表的拖选会被系统在每个阈值处抢走")
        XCTAssertFalse(EntryDragGate.prepareForDrag(origin: .rowBody, content: .file(URL(fileURLWithPath: "/tmp/a.png"))))
    }

    func testDragGateAllowsTheHandleOnlyWhenThereIsAPayload() {
        XCTAssertTrue(EntryDragGate.prepareForDrag(origin: .handle, content: .text("可拖的文本")))
        XCTAssertTrue(EntryDragGate.prepareForDrag(origin: .handle, content: .file(URL(fileURLWithPath: "/tmp/a.png"))))
    }

    func testDragGateRefusesTheHandleWhenNothingWouldBeCarriedOut() {
        // "拖起来什么都没发生"比"没有拖出入口"更糟（R2-05 的原始理由），所以载荷为空也要判 false。
        XCTAssertFalse(EntryDragGate.prepareForDrag(origin: .handle, content: .text("")))
        XCTAssertFalse(EntryDragGate.prepareForDrag(origin: .handle, content: .files([
            URL(fileURLWithPath: "/tmp/a.png"), URL(fileURLWithPath: "/tmp/b.png"),
        ])), "多文件拖出需要 NSView 级 dragging session，本轮仍不提供（账本 R2-05 部分完成）")
        XCTAssertFalse(EntryDragGate.prepareForDrag(
            origin: .handle, content: .file(URL(string: "https://example.com")!)))
    }

    // MARK: - ③ 接线侧

    /// 视图必须真的换成系统列表；纯函数与 store 动作都对、视图没换 = 缺陷还在。
    func testSidebarIsWiredToTheSystemList() throws {
        let source = codeOnly(try sidebarSource())
        XCTAssertTrue(source.contains("List(selection: selectionBinding)"),
                      "侧栏还在用自绘的 ScrollView/LazyVStack —— D-1 的争用没有解决")
        XCTAssertFalse(source.contains("LazyVStack"), "旧的自绘列表容器还留着，两套选中语言会同时存在")
        XCTAssertFalse(source.contains(".onDrag"),
                       "拖出入口不该出现在侧栏容器/行上，它只属于把手（见 EntryDragGate）")
        // 键盘与滚动交给系统 List：手工接的方向键必须一起撤掉，否则两套实现同时改选中状态。
        XCTAssertFalse(source.contains(".onMoveCommand"),
                       "系统 List 已经负责方向键，手工那条路径会与之争用")
        XCTAssertFalse(source.contains("ScrollViewReader"))
        // 但 D-030 那一圈整块蓝框的抑制必须留着（换成 List 之后环一样会画在列表外）。
        XCTAssertTrue(source.contains(".sidebarFocusRingHidden()"),
                      "整块列表的焦点环抑制被移除了：鼠标点一下就会出现用户报过的那圈蓝框")
    }

    /// 拖出入口只许有一处，且挂在把手上。
    func testDragAffordanceLivesOnlyOnTheHandle() throws {
        let source = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        XCTAssertEqual(source.components(separatedBy: "EntryDragModifier(content:").count - 1, 1,
                       "拖出入口应当恰好有一处（把手）。多一处就意味着又开始抢列表的拖选")
        XCTAssertTrue(source.contains("RowDragHandle"), "行里找不到把手这一层")
        XCTAssertFalse(source.contains(".onDrag"),
                       "行视图里直接写 `.onDrag` 就绕过了 EntryDragGate 的分工判据")
        // 把手的提示语不能对没有载荷的条目许空愿。
        XCTAssertEqual(RowDragHandleHelp.helpText(for: .files([URL(fileURLWithPath: "/tmp/a")])), "")
        XCTAssertFalse(RowDragHandleHelp.helpText(for: .text("x")).isEmpty)
    }

    /// 源码扫描先把注释行滤掉：**"这里不再挂 `.onDrag`"这样一句解释会被裸关键词扫描当成违规**
    /// （本轮第一次跑就撞上过一次，账本里同类教训是 R-a 那条"锚点撞上注释"）。
    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    /// 接线守卫：行的双击与星标必须还接在这两个动作上。
    /// D-1 把行里的 `Button` 拿掉了，孤立行的合成点击就送不进去（见探针文件里那段说明），
    /// 于是"双击=复制、点星标=收藏"在自动化这一侧只剩下接线可钉 —— 行为本身进手工清单。
    func testRowGesturesAreStillWiredToTheirActions() throws {
        let source = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        XCTAssertTrue(source.contains(".onTapGesture(count: 2)"),
                      "行上没有双击手势了：双击复制这条交互等于不存在")
        XCTAssertTrue(source.contains("RowDoubleTap.shouldCopy(modifiers: NSEvent.modifierFlags)"),
                      "双击没有走带例外名单的判定（shift/⌘ 双击不该写剪贴板）")
        XCTAssertTrue(source.contains("copyAction()"), "双击手势没有接到 copyAction")
        XCTAssertTrue(source.contains("RowFavoriteButton(isFavorite: entry.isFavorite, action: favoriteAction)"),
                      "星标没有接到 favoriteAction")
        // 整个文件里只许有星标这一个 Button：行体再长出一个"选中用的 Button"
        // 就等于同时存在两套选中语言（那是 D-1 之前的形状）。
        XCTAssertEqual(source.components(separatedBy: "Button(action:").count - 1, 1,
                       "行里出现了多于一个 Button —— 选中只能由 List 负责")
    }

    private func sidebarSource() throws -> String {
        try productSource(named: "Views/HistorySidebarView.swift")
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
