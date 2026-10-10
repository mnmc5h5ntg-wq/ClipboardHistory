import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 第三轮审计 D-1 的最终形态（修法③ + D-034 的取舍）：侧栏是 `List(selection:)`，
/// 拖出挂在整行上，**拖选这条路径整个不存在**。
///
/// 这里钉三层，缺一层都会留下"看着像修好了"的空间：
/// ① **store 侧**：`List` 汇报上来的集合怎么落成权威状态（含"不可见 id 必须丢掉"）；
/// ② **判据侧**：哪些条目提供拖出（没有载荷就不许给一个拖起来没反应的入口）；
/// ③ **接线侧**：视图真的走系统 `List`，手工方向键没有偷偷长回来，
///    而被放弃的拖选手势也没有留下半套死码。
///
/// ②原本还包含"行体永远不许开拖出会话"——那是"把手才拖出"的设计，
/// 真机验证 `List` 会把行内任何 `.onDrag` 提升成整行拖拽源，分工做不到，故 D-034 改取舍。
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

    // MARK: - ② 判据侧：什么条目提供拖出

    func testOffersDragOnlyWhenSomethingWouldActuallyBeCarriedOut() {
        XCTAssertTrue(EntryDragGate.offersDrag(for: .text("可拖的文本")))
        XCTAssertTrue(EntryDragGate.offersDrag(for: .file(URL(fileURLWithPath: "/tmp/a.png"))))
        // "拖起来什么都没发生"比"没有拖出入口"更糟（R2-05 的原始理由）。
        XCTAssertFalse(EntryDragGate.offersDrag(for: .text("")))
        XCTAssertFalse(EntryDragGate.offersDrag(for: .file(URL(string: "https://example.com")!)))
        // 第三轮 §4 U-2 改了这里的多文件那一行：以前多文件条目**不**提供拖出
        // （一次拖多个 item 需要 NSView 级 dragging session，而 `onDrag` 只给一个 provider，
        // 于是"拖 3 个只落地 1 个"）。现在 provider 里带的是 `NSFilenamesPboardType` 那份
        // **路径数组**，三个路径真的都在里面 —— 字节级的核对见
        // `EntryDragPlannerTests.testMultipleFileEntriesCarryEveryPath`。
        XCTAssertTrue(EntryDragGate.offersDrag(for: .files([
            URL(fileURLWithPath: "/tmp/a.png"), URL(fileURLWithPath: "/tmp/b.png"),
        ])), "多文件条目已经能带出全部路径，这里还拒绝承诺拖拽 = 能力被埋着")
        XCTAssertFalse(EntryDragGate.offersDrag(for: .files([])),
                       "空列表仍然不许许空愿：这条不变")
    }

    /// 提示语不许对没有载荷的条目许空愿（空 `.help` 在 macOS 上还会弹一个空气泡）。
    func testDragHelpTextMatchesTheAffordance() {
        XCTAssertFalse(RowDragHelp.text(for: .files([URL(fileURLWithPath: "/tmp/a")])).isEmpty,
                       "§4 U-2 之后多文件条目是有载荷的，提示语必须跟着承诺")
        XCTAssertTrue(RowDragHelp.text(for: .files([])).isEmpty, "空列表还是不该有提示")
        XCTAssertFalse(RowDragHelp.text(for: .text("x")).isEmpty)
    }

    // MARK: - ③ 接线侧

    /// 视图必须真的换成系统列表；纯函数与 store 动作都对、视图没换 = 缺陷还在。
    func testSidebarIsWiredToTheSystemList() throws {
        let source = codeOnly(try sidebarSource())
        XCTAssertTrue(source.contains("List(selection: selectionBinding)"),
                      "侧栏还在用自绘的 ScrollView/LazyVStack —— D-1 的争用没有解决")
        XCTAssertFalse(source.contains("LazyVStack"), "旧的自绘列表容器还留着，两套选中语言会同时存在")
        // 键盘与滚动交给系统 List：手工接的方向键必须一起撤掉，否则两套实现同时改选中状态。
        XCTAssertFalse(source.contains(".onMoveCommand"),
                       "系统 List 已经负责方向键，手工那条路径会与之争用")
        XCTAssertFalse(source.contains("ScrollViewReader"))
        // 但 D-030 那一圈整块蓝框的抑制必须留着（换成 List 之后环一样会画在列表外）。
        XCTAssertTrue(source.contains(".sidebarFocusRingHidden()"),
                      "整块列表的焦点环抑制被移除了：鼠标点一下就会出现用户报过的那圈蓝框")
    }

    /// 拖选这条路径必须**整个不存在**（D-034 的取舍）。留着半套最坏：
    /// 一个永远抢不过表格拖拽会话的手势，会让人以为拖选还能用。
    func testNoCompetingDragSelectGestureRemains() throws {
        let sidebar = codeOnly(try sidebarSource())
        XCTAssertFalse(sidebar.contains("DragGesture"),
                       "侧栏还挂着一个拖选手势 —— 它在 `List` 里永远抢不过行拖拽会话，是死码")
        XCTAssertFalse(sidebar.contains("dragSelectRange"),
                       "store 的拖选动作已删，视图里不该再有引用")
        XCTAssertFalse(sidebar.contains("rowFrames"),
                       "行位置表只服务于拖选，留着就是没人读的账")
        let store = codeOnly(try productSource(named: "Managers/HistoryStore.swift"))
        XCTAssertFalse(store.contains("dragSelectRange"),
                       "`dragSelectRange` 这个动作还在 store 里 —— 要么接回一条真实路径，要么删干净")
    }

    /// 拖出入口恰好一处，且在行上（`List` 会把行内 `.onDrag` 提升成整行拖拽源，
    /// "只让行首可拖"在系统列表里做不到 —— 见 D-034 与用户真机反馈）。
    func testDragAffordanceIsExactlyOneAndLivesOnTheRow() throws {
        let source = codeOnly(try productSource(named: "Views/HistoryRowViews.swift"))
        XCTAssertEqual(source.components(separatedBy: "EntryDragModifier(content:").count - 1, 1,
                       "拖出入口应当恰好一处；多一处就意味着又出现两个候选")
        XCTAssertTrue(source.contains("RowLeadingVisual"), "行首视觉列不见了")
        XCTAssertFalse(source.contains("RowDragHandle"),
                       "旧的把手层还在 —— 那个设计已被真机否掉，别让它悄悄回来")
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
        XCTAssertTrue(source.contains("TapGesture(count: 2).onEnded"),
                      "行上没有双击手势了：双击复制这条交互等于不存在")
        XCTAssertTrue(source.contains(".simultaneousGesture("),
                      "双击必须走 simultaneousGesture，见下面那条反向守卫")
        // 这条反向守卫是用户真机反馈换来的（D-036）：`.onTapGesture(count: 2)` 里
        // count:2 的识别器要等一个双击间隔才放行单击，而 `List` 的选中正走同一套行内点击识别
        // ⇒「点一行到显示已选中」出现可感知延迟。
        XCTAssertFalse(source.contains(".onTapGesture(count: 2)"),
                       "行上的双击又换回 onTapGesture(count: 2) 了 —— 那会让选中延迟一个双击间隔")
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
