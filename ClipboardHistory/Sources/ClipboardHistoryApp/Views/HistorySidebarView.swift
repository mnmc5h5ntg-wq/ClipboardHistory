import AppKit
import SwiftUI

struct HistorySidebarView: View {
    @ObservedObject var historyStore: HistoryStore
    /// 拖放悬停反馈（虚线框）。
    @State private var isDropTargeted = false
    /// 取证通道：离屏捕获送不进 drag session，只有夹具写这颗键（R408）。
    @Environment(\.dropTargetedForCapture) private var dropTargetedForCapture
    @Environment(\.colorScheme) private var colorScheme
    private var isDropTargetedForDrawing: Bool { isDropTargeted || (dropTargetedForCapture ?? false) }

    /// R515：系统红在 1x 暗档的抗锯齿下核心亮度只剩约 2.37:1（R514 实心化也没清掉这朵红）。
    /// 暗档换成更亮的珊瑚红（核心亮度约 160 ⇒ 1x 约 4.5:1、2x 约 6:1），亮档维持系统红。
    private var destructiveActionInk: Color {
        colorScheme == .dark
            ? Color(red: 1.0, green: 0.53, blue: 0.53)
            : Color.red
    }

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 8) {
                SearchField(
                    text: Binding(
                        get: { historyStore.searchText },
                        set: { historyStore.perform(.updateSearch($0)) }
                    )
                )

                SegmentedFilterPicker(
                    selection: Binding(
                        get: { historyStore.filter },
                        set: { historyStore.perform(.updateFilter($0)) }
                    )
                )
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)

            Divider()
            header

            if historyStore.filteredEntries.isEmpty {
                EmptyStateView(
                    systemName: SearchNoResultsPresentation.iconName(
                        entriesEmpty: historyStore.entries.isEmpty,
                        isFavoritesFilter: historyStore.filter == .favorites,
                        favoriteCount: historyStore.favoriteCount,
                        searchText: historyStore.searchText),
                    title: SearchNoResultsPresentation.title(
                        entriesEmpty: historyStore.entries.isEmpty,
                        isFavoritesFilter: historyStore.filter == .favorites,
                        favoriteCount: historyStore.favoriteCount,
                        searchText: historyStore.searchText),
                    illustration: historyStore.entries.isEmpty,
                    // "无匹配结果"必须给下一步（审计 §4 U-5 的那句"说清发生了什么 + 说清下一步"）：
                    // 用户搜不出东西时，最该出现的不是"这里空着"，而是"把搜索词清掉"。
                    actionTitle: historyStore.searchText.isEmpty ? nil : "清除搜索",
                    action: historyStore.searchText.isEmpty ? nil : { historyStore.perform(.updateSearch("")) }
                )
                .padding(.vertical, 40)
                    // 过渡以前挂在下面那个 `Spacer()` 上（R5 修正）：Spacer 没有可见内容，
                    // 于是"空态淡入"这句话在代码里存在、在屏幕上不存在。挪到 EmptyStateView 本体上。
                    .transition(MotionCatalog.transition(for: .contentFade))
                Spacer()
            } else {
                historyList
            }
        }
        // 空态出现/消失（审计 §3："空态是停，不该演"⇒ 只淡入，不滑不缩）。
        //
        // R348 / BACKLOG 389·424：这一层以前走 `contentFade`（0.16），而同一时刻那颗药丸走 `slider`（0.20）
        // —— 切筛选把列表切空（或切回来）时，内容 0.16 就落定了，药丸还要再走一小段（外加弹簧尾巴）。
        // 两件事是**同一个手势的两半**，必须同一个节奏：这里改成和药丸同一个动画。
        // 只有时长变了，过渡本身仍是 `.opacity`（"空态是停"那条不动）。
        //
        // R355 / BACKLOG 429：**不能**用 `FilterPillMotion.slideAnimation` 来借这个节奏 ——
        // 那是药丸的瞬移快捷方式（reduce 下 `shape.slides == .none` ⇒ 返回 `.linear(duration: 0)`），
        // 对"位置就是内容"的胶囊成立，对内容淡入就是**一帧硬切**：
        // runner 从 R348 起读到的 `MOTION_NOT_RUN=witness-snaps-here empty-state`（本臂只变 36ms/1 帧）
        // 就是它 —— 改前同一臂在 runner 上是 3 帧（run 40186459168 ↔ 2f47243）。
        // 目录里的 `.slider` 动画本身在 reduce 下**不归零**：滑入换成 0.20 的淡入（`curve(for:)` 那条规）。
        .animation(MotionCatalog.animation(for: .slider, reduceMotion: shouldReduce), value: historyStore.filteredEntries.isEmpty)
    }

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    /// 同 `SegmentedFilterPicker.shouldReduce`：系统开关 ∪ VoiceOver。
    private var shouldReduce: Bool { reduceMotion || MotionCatalog.motionShouldBeReduced }
    /// R429：分区头取证键（`false` = 旧形状）；产品路径永远显示。
    @Environment(\.sidebarSectionHeadersForCapture) private var sidebarSectionHeadersForCapture
    /// R494：主侧栏标题图标的负向帧缝（产品默认 nil ⇒ 画）。
    @Environment(\.mainSidebarTitleIconForCapture) private var mainSidebarTitleIconForCapture
    private var sectionHeadersForDrawing: Bool { sidebarSectionHeadersForCapture ?? true }
    private var pinnedEntries: [HistoryStore.Entry] { historyStore.filteredEntries.filter(\.isPinned) }
    private var unpinnedEntries: [HistoryStore.Entry] { historyStore.filteredEntries.filter { !$0.isPinned } }
    private var sectionPlanForDrawing: SidebarSectionPlan {
        SidebarSectionPlan(pinnedCount: sectionHeadersForDrawing ? pinnedEntries.count : 0)
    }

    /// R469：跨年参照 —— 当前过滤结果里最新的一条。取过滤后的集合而不是全量：
    /// 搜索到只剩同一年的记录时，年份不该继续跟着看不见的那些记录走。
    private var newestTimestamp: Date? {
        historyStore.filteredEntries.map(\.timestamp).max()
    }

    @ViewBuilder
    private func historyRow(_ entry: HistoryStore.Entry) -> some View {
        HistoryRowButton(
            entry: entry,
            // 双击行 = 详情区浮层那颗"再次复制"，同一个动作同一个语义（会把这条顶到最前）。
            copyAction: { historyStore.perform(.copyAndPromote(entry)) },
            favoriteAction: { historyStore.perform(.toggleFavorite(entry)) },
            // R456：行里标出命中片段 —— 过滤匹配正文与来源 App 名，列表必须说清"为什么这行在"。
            searchQuery: historyStore.searchText,
            // R469：跨年的那几条时间行带年份。
            timeReference: newestTimestamp
        )
    }

    private var header: some View {
        HStack {
            // R494：设置页标题与侧栏分类都有图标，主窗口这张标题却只有一行字。
            // 补一枚时钟/回溯符号，作为同一个身份锚点；纯装饰，读屏不重复念。
            // R495：批量态标题是「已选 N 条」而不是应用名，时钟图标语义不对；
            // 250pt 最小宽下它还把选中数挤成「已选…」（R493 帧可见完整文案）。
            if historyStore.selectedCount <= 1, mainSidebarTitleIconForCapture ?? true {
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: VisualFont.title, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .accessibilityHidden(true)
            }
            Text(headerTitle)
                .font(.system(size: VisualFont.title, weight: .semibold))
                .foregroundStyle(.secondary)
                .lineLimit(1)

            Spacer()

            if historyStore.selectedCount > 1 {
                // 两臂都要有过渡，否则"进批量"是软交接而"出批量"是一帧硬换
                //（R7 / 审计 B-P3：这条以前整块没有 `.transition`，只有下面那条按值动画）。
                bulkActionButtons
                    .transition(MotionCatalog.transition(for: .contentFade))
            } else {
                countTextLabel
                    .transition(MotionCatalog.transition(for: .contentFade))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .frame(height: 39)
        .animation(MotionCatalog.animation(for: .selection), value: historyStore.selectedCount > 1)
    }



    private var bulkActionButtons: some View {
        // R15：间距从 8 收到 0，交给 `labelPadding` 出。
        // 药丸每边 5pt ⇒ 相邻两颗的高亮正好挨着（系统工具栏就是这个形状），
        // 而字形之间仍然是 10pt 的视觉距离（比原来的 8pt 略松一点，可接受）。
        // 如果留着 spacing 8 再加 padding 5，两颗高亮之间会露出一条 18pt 的空隙，
        // 读起来像"五个孤立的方块"而不是"一排工具"。
        // R513：动词按选区可用性点亮 —— 没有固定项时「取消固定」不该是一个可点的空操作。
        let availability = BulkActionAvailability(selectedEntries: historyStore.selectedEntries)
        return HStack(spacing: 0) {
            Button {
                historyStore.perform(.favoriteSelection)
            } label: {
                Image(systemName: "star")
            }
            .helpLabel("收藏所选记录")
            .disabled(!availability.canFavorite)
            .opacity(availability.canFavorite ? 1 : 0.35)

            Button {
                // 固定 = "这条我要长期留着，别被复制顶下去、别被保留策略删掉"（§5 F-5）
                historyStore.perform(.pinSelection(isPinned: true))
            } label: {
                Image(systemName: PinTogglePresentation.actionSymbolName(isPinning: true))
            }
            .helpLabel(PinTogglePresentation.helpText(isPinned: false))
            .disabled(!availability.canPin)
            .opacity(availability.canPin ? 1 : 0.35)

            Button {
                historyStore.perform(.pinSelection(isPinned: false))
            } label: {
                Image(systemName: PinTogglePresentation.actionSymbolName(isPinning: false))
            }
            .helpLabel(PinTogglePresentation.helpText(isPinned: true))
            .disabled(!availability.canUnpin)
            .opacity(availability.canUnpin ? 1 : 0.35)

            Button {
                historyStore.perform(.unfavoriteSelection)
            } label: {
                Image(systemName: "star.slash")
            }
            .helpLabel("取消收藏所选记录")
            .disabled(!availability.canUnfavorite)
            .opacity(availability.canUnfavorite ? 1 : 0.35)

            // R436：破坏性动作与其余四颗之间补一条发丝分隔 —— 它们原来在
            // `spacing: 0` 的一排里只靠颜色分开，扫视时要先读红才知道哪颗是删除。
            Rectangle()
                .fill(Color.primary.opacity(0.18))
                .frame(width: 1, height: 14)
                .padding(.horizontal, 2)

            Button(role: .destructive) {
                historyStore.perform(.deleteSelection)
            } label: {
                // R514：轮廓 `trash` 在 runner 1x 暗档只读到 2.27:1；实心化补了核心面积，
                // 但系统红本身在 1x 抗锯齿下仍只有 2.37:1（R515 新跑实测）⇒ 暗档用上面那颗
                // 提亮红，1x/2x 都留出 4:1 余量；亮档维持系统红。
                Image(systemName: "trash.fill")
            }
            .helpLabel("删除所选记录")
            .foregroundStyle(destructiveActionInk)
        }
        // R13：这里以前是 `.buttonStyle(.borderless)` —— 全 App 唯一一处绕开 `PressedStyle`
        // 的地方，于是这五颗（含**删除**）既没有按压也没有悬停反馈：点下去只有图标自己动一下，
        // 而"我按到的是哪一颗"要等结果才知道。`.borderless` 不是"更素"，是把反馈拿掉了。
        .pressedStyle(in: VisualShape.rounded(VisualRadius.control),
                      hoverLevel: VisualFill.controlHover,
                      labelPadding: 5)
    }

    private var headerTitle: String {
        if historyStore.selectedCount > 1 {
            return "已选 \(historyStore.selectedCount) 条"
        }
        return "时间剪史"
    }

    private var countText: String {
        switch historyStore.filter {
        case .all:
            return "\(historyStore.filteredEntries.count) 条记录"
        case .favorites:
            return "\(historyStore.filteredEntries.count) 个收藏"
        }
    }

    /// R420：搜索结果计数以前是硬换（同一个头里，列表已经按 0.16 淡，读数却跳）。
    /// 14+ 走系统的数字滚动；12/13 保持原样。键是整句：筛选词与「条记录/个收藏」
    /// 的后缀一起变，拆成两段动画会各自起事务错拍。
    @ViewBuilder
    private var countTextLabel: some View {
        let base = Text(countText)
            .font(.system(size: VisualFont.body, weight: .regular))
            .foregroundStyle(.secondary)
            .lineLimit(1)
        if #available(macOS 14, *) {
            base
                .contentTransition(.numericText())
                .animation(MotionCatalog.animation(for: .contentFade), value: countText)
        } else {
            base
        }
    }

    /// 历史列表（第三轮审计 D-1，最终形态见账本 D-034）。
    ///
    /// 这里**刻意没有**列表级的拖选手势。原本 D-1 的修法③想同时保住"拖出"和"拖选"，
    /// 做法是把 `.onDrag` 只挂在行首把手上；真机验证否掉了它 ——
    /// `List` 底下是 `NSTableView`，SwiftUI 会把行内**任何**一处 `.onDrag` 提升成"整行是拖拽源"，
    /// 于是从行里任意位置按下都会开会话（半透明剪影跟着鼠标走），
    /// 而会话一开始，挂在容器上的 `DragGesture` 就拿不到这串鼠标事件了。
    /// 结论：在 `List` 里"把手才拖出、行体拖选"这个分工做不到。
    /// 取舍是**保留整行拖出、去掉拖选**（macOS 侧栏本来也不做橡皮筋多选，Finder 侧栏同样不做），
    /// 选中交给单击 / shift / ⌘ / 方向键 —— 全部由系统 `List` 负责。
    private var historyList: some View {
        List(selection: selectionBinding) {
            if sectionHeadersForDrawing, !pinnedEntries.isEmpty {
                // R429：固定条目置顶，但以前与普通条目完全同形。给它们一行分区头，
                // 只加一行、不拆分组；无固定条目时仍走原来的单个 ForEach（老帧不变）。
                Section {
                    ForEach(pinnedEntries) { entry in
                        historyRow(entry)
                    }
                } header: {
                    SidebarSectionHeader(title: SidebarSectionPlan.pinnedTitle)
                }
                ForEach(unpinnedEntries) { entry in
                    historyRow(entry)
                }
            } else {
                ForEach(historyStore.filteredEntries) { entry in
                    historyRow(entry)
                }
            }
        }
        // 行的增删/重排**没有**过渡，这里刻意不留 `.transition`（动效审计 M1，账本 U-20 / D-055）。
        //
        // 不是没试，是四种写法都试过并且都量过：`.animation(value:)` 挂在 `List` 上、
        // 挂在 `ForEach` 上、用 `.transaction` 给这棵子树装默认事务、以及把动画事务挂到
        // **变更漏斗**（`HistoryStore.perform` / `add`）上 —— 最后这种在最小复现里也无效
        // （报告 §13.2 的 S1/S5 与本仓库 `MotionFilmstripTests.testListRowsDoNotAnimateAndNothingClaimsTheyDo`
        // 是同一份读数：列表中部那条带 0.283 一帧到位、落定残余 0.000）。
        // `List` 底下是 `NSTableView`，SwiftUI 的行级 transition 拿不到它。
        //
        // 剩下的两条路都要付更大的代价：换 `ScrollView + LazyVStack` 能动画，
        // 但会丢掉 D-034/D-1 花大力气换回来的系统选中与键盘语义；
        // 走 `NSTableView.insertRows(with: .effectFade)` 要自己实现整个侧栏。
        // 报告的结论和本轮的判断一致：**承认侧栏行不动，比把时长加大到"看得见"更正确**，
        // 所以动效留在行内（收藏/固定的符号动效、悬停与选中淡入、复制回执）。
        .listStyle(.sidebar)
        .accessibilityLabel("历史记录列表")
        // 拖入文件入库（审计第二轮 1.5 / R2-05 的另一半：整个应用以前不接受任何拖入）。
        // 落点刻意只在列表区域而不是整窗：详情的文本视图自己接受文字拖放，
        // 窗口级 .onDrop 会抢走它。
        .onDrop(of: DroppedFileImport.acceptedTypeIdentifiers, isTargeted: $isDropTargeted) { providers in
            acceptDroppedFileProviders(providers)
        }
        .overlay {
            if isDropTargetedForDrawing {
                ZStack(alignment: .bottom) {
                VisualShape.rounded(VisualRadius.panel)
                    .strokeBorder(Color.accentColor.opacity(VisualTint.dropTargetStroke),
                                  style: StrokeStyle(lineWidth: VisualStroke.highlight,
                                                     dash: VisualStroke.highlightDash))
                    .allowsHitTesting(false)
                    // 落点框以前是"瞬间出现/瞬间消失"（审计 🟡）。
                    // 淡入 + 一点点缩放是必要的：鼠标悬在窗口边缘时它每帧都在进出，
                    // 没有过渡就会闪。减弱动态时只剩淡入（`shape` 里那条规则）。
                    .transition(MotionCatalog.transition(for: .dropTarget))
                // M8 的后半句："命中文件时列表轻微让位 + **描边发光**"。让位那一半是上面的缩放，
                // 这一半才是"松手就在这里"的那句话 —— 虚线框只说"这里能放"，光说"现在正对着你"。
                // 减弱动态时整圈光都不画：它是一层模糊，而 HIG 的 reduce-motion 清单里明写了
                // "avoid animating into and out of blurs"；虚线框本身仍然淡入，指向性没有丢。
                if MotionCatalog.glows(for: .dropTarget) {
                    VisualShape.rounded(VisualRadius.panel)
                        .strokeBorder(Color.accentColor.opacity(MotionCatalog.dropGlowOpacity),
                                      lineWidth: VisualStroke.glow)
                        .blur(radius: MotionCatalog.dropGlowRadius)
                        .allowsHitTesting(false)
                        .transition(MotionCatalog.transition(for: .contentFade))
                }
                Text("松手加入剪贴板历史")
                    .font(.system(size: VisualFont.meta, weight: .semibold))
                    .foregroundStyle(.primary)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        VisualShape.rounded(VisualRadius.control)
                            .fill(Color(nsColor: .windowBackgroundColor).opacity(0.86))
                    )
                    .padding(.bottom, 18)
                    .allowsHitTesting(false)
                    .transition(MotionCatalog.transition(for: .contentFade))
                }
                .allowsHitTesting(false)
            }
        }
        .animation(MotionCatalog.animation(for: .dropTarget), value: isDropTargetedForDrawing)
        // 系统的 `List` 在自己拿到焦点时也会画一圈焦点环；鼠标点一下不该留下它（D-030 那圈蓝框），
        // 键盘导航要留着，所以只关"效果"不关"可聚焦"。`focusEffectDisabled()` 是 macOS 14+，
        // 12/13 没有对应 API ⇒ 那两版上环会留着，是平台限制不是漏了。
        .sidebarFocusRingHidden()
        // R61 / BACKLOG 61：把当前选中的那一行**滚进视口**。
        // `List(selection:)` 不选中视口外的行（本轮在屏实测：store 有 1 条、表格 `selectedRowIndexes` 是空），
        // 而只要那一行进了视口，SwiftUI 自己就把选中补回来 —— 所以这里只补"揭示"这一步，
        // 不碰选中（作者仍然是 `List`，见 `SelectedRowRevealer` 正文与 D-1 修法③）。
        // 为什么不用 SwiftUI 自己的 `ScrollViewReader`/`scrollTo`：在产品这棵树上它不滚
        // （带/不带 anchor 都试过，胶水确实执行、id 也解析到了），
        // `SelectedRowRevealTests.testSidebarDoesNotClaimTheSwiftUIScrollRoute` 钉住这条结论。
        .background(
            SelectedRowRevealer(
                revealKey: (historyStore.selectedEntry?.id).map { AnyHashable($0) },
                rowIndex: SelectionRevealPlan.rowIndex(
                    of: historyStore.selectedEntry?.id,
                    in: historyStore.filteredEntries.map(\.id))
                    .map { sectionPlanForDrawing.displayRowIndex(forFilteredIndex: $0) })
        )
    }

    /// 选中集合：`List` 是唯一作者，store 只是落状态（D-1 修法③）。
    ///
    /// 以前这里是"行自己的 Button 调 `select(_:)`，再按 `NSEvent.modifierFlags` 手工分成
    /// `selectOnly`/`selectRange`/`toggleSelection`"，方向键另走 `onMoveCommand`。
    /// 换到 `List(selection:)` 之后 shift 扩选、⌘ 加选、方向键移动、滚动跟随、VoiceOver 的
    /// selected 语义全部由系统负责 —— 那四件事正是审计 D-1 说"一次解决"的部分。
    /// store 侧的 `selectOnly`/`selectRange`/`toggleSelection` 仍然留着：
    /// 菜单栏面板、快捷键路径和 store 级语义测试都在用它们（被删掉的只有"拖选"那一条，见 D-034）。
    private var selectionBinding: Binding<Set<HistoryStore.Entry.ID>> {
        Binding(
            get: { historyStore.selectedEntryIDs },
            set: { historyStore.perform(.setSelection($0)) }
        )
    }

    /// 把 provider 里的 file URL 解出来交给 store。解码是异步的，所以这里只回答"我接住了"，
    /// 真正的入库在收集完之后发生；一个 provider 解不出来不影响其余。
    /// 这段胶水需要真实拖放才能验收（账本 R2-05 标为未验证），因此所有可判定的逻辑
    /// 都推到了 `DroppedFileImport.plan` 与 `HistoryStore.addDroppedFiles` 这两处有测试的地方。
    private func acceptDroppedFileProviders(_ providers: [NSItemProvider]) -> Bool {
        let identifier = DroppedFileImport.acceptedTypeIdentifiers[0]
        let wanted = providers.filter { $0.hasItemConformingToTypeIdentifier(identifier) }
        guard !wanted.isEmpty else { return false }
        Task { @MainActor [weak historyStore] in
            var urls: [URL] = []
            for provider in wanted {
                urls.append(contentsOf: await Self.fileURLs(from: provider, identifier: identifier))
            }
            /// ③ 那一格的调用方：`wanted` 是"声称自己是文件"的个数，`urls` 是"真解出来"的个数。
            /// 只传 `urls` 的话，一个都没解出来时 store 看到的是空数组 ⇒ 静默（BACKLOG 224）。
            _ = historyStore?.addDroppedFiles(urls: urls, attemptedCount: wanted.count)
        }
        return true
    }

    /// 单个 provider → 文件 URL 列表。`loadItem` 是回调式的，包一层 continuation 才能顺序收集，
    /// 避免多个回调并发往同一个数组里写。
    private static func fileURLs(from provider: NSItemProvider, identifier: String) async -> [URL] {
        await withCheckedContinuation { continuation in
            provider.loadItem(forTypeIdentifier: identifier) { item, _ in
                var result: [URL] = []
                if let data = item as? Data {
                    if let url = URL(dataRepresentation: data, relativeTo: nil) { result.append(url) }
                } else if let url = item as? URL {
                    result.append(url)
                } else if let nsurl = item as? NSURL {
                    result.append(nsurl as URL)
                }
                continuation.resume(returning: result)
            }
        }
    }
}

// MARK: - Segmented Filter Picker — sliding pill with spring overshoot

/// 筛选 pill 的动效（审计第二轮 1.1 / 1.12 / R2-10）。
///
/// 滑块的过冲弹簧与 hover 放大属于"为动而动"：系统分段控件没有这种弹性，
/// 而且它们以前**不读**系统的「减弱动态效果」开关。抽成纯函数，
/// 一是为了单测两个分支，二是为了让"减少动态时到底退化成什么"写在同一处。
enum FilterPillMotion {
    /// 滑块动效的**参数**（纯值，可测）。`Animation` 本身不便比较，
    /// 所以让视图消费这个值，测试断言这个值 —— 否则"减少动态时到底退化成什么"没有判据。
    struct SlideMotion: Equatable {
        /// true = 瞬移，不做动画。
        let isInstant: Bool
        let response: Double
        /// < 1 表示有过冲（弹簧）；等于 1 表示不过冲。
        let damping: Double
    }

    static func slideMotion(reduceMotion: Bool) -> SlideMotion {
        // 参数不再写死在这里（R12）。以前是 `response 0.38 / damping 0.72`：
        // 0.38 越过目录的 `maximumDuration`，0.72 是欠阻尼 ⇒ 胶囊会**冲过头再弹回来**。
        // 而目录里 `criticalDamping` 那条注释还点名说"正确定义在 `FilterPillMotion`"——
        // MC-1 修的是规矩，这一处实例被漏掉了。修规矩的时候要把用旧值的地方一起扫掉，
        // 否则注释会变成第二个谎言。
        reduceMotion
            ? SlideMotion(isInstant: true, response: 0, damping: MotionCatalog.criticalDamping)
            : SlideMotion(isInstant: false,
                          response: MotionCatalog.duration(for: .slider),
                          damping: MotionCatalog.criticalDamping)
    }

    /// 要不要"真的滑"。目录说这一档在减弱动态时**不滑**（`shape.slides == .none`），
    /// 那就瞬移 —— 这里瞬移不是"把动效清零"，而是**位移本身就是这条动效的全部内容**：
    /// 胶囊的位置就是"你选了哪一段"，把它淡入淡出并不能表达这件事。
    /// （banner 那一档可以换成淡入，是因为它的信息在文字里，不在它从哪儿来。）
    static func slideAnimation(reduceMotion: Bool) -> Animation {
        guard MotionCatalog.shape(for: .slider, reduceMotion: reduceMotion).slides != .none else {
            return .linear(duration: 0)
        }
        return MotionCatalog.animation(for: .slider, reduceMotion: reduceMotion)
    }

    /// hover 放大：减少动态时不放大（1.0 = 原尺寸）。
    static func hoverScale(isHovered: Bool, reduceMotion: Bool) -> CGFloat {
        guard isHovered, !reduceMotion else { return 1.0 }
        return 1.08
    }

    /// hover 底色。**这一档是"替换"那一半，不是装饰**（R12）：
    /// 减弱动态时 `hoverScale` 归 1.0，而这一段以前**只剩缩放这一种悬停表达** ⇒
    /// 开了「减弱动态效果」的用户把鼠标放上去，什么反馈都没有 ——
    /// "reduce 是替换不是删除"这条规矩，在悬停这件事上以前是空的。
    /// 底色不承担物理隐喻，所以它不受 reduce 影响：两臂都给同一个值。
    ///
    /// `dark` 是 R230 加的：这一层**以前两档共用一个数**，而它正是"直接读令牌、不走按钮样式"
    /// 的那一类位点 ⇒ R229 的亮档那一抬落不到它身上。规矩改成问 `HoverInk`（同文件里那条注释）。
    /// 抬量只允许长在"真的要画"这条分支里：未悬停 / 选中那两段必须还是 0，
    /// 否则就是把 0.025 画在了没有悬停的段上（`FilterSegmentButton` 那一段注释记的是同一件事）。
    static func hoverFill(isHovered: Bool, isSelected: Bool, dark: Bool) -> Double {
        // 选中的那一段下面就是那颗胶囊，再叠一层悬停底会糊成两块。
        guard isHovered, !isSelected else { return 0 }
        // R334 / BACKLOG 396：**暗档走胶囊自己那一档**（`VisualFill.pillHover`，比全局的
        // `controlHover` 轻），因为 393 把选中那颗抬到 70 之后，共用 0.08 画出的 66 与它只差 4 级
        // —— 悬停把选中复现了一遍。亮档继续走共享换算：它的空闲 230 与选中 220 之间
        // 只剩 1.099 的距离，放不下"与两边都看得见地不同"的第三档，要修得换一条轴（BACKLOG 399）。
        // 两档不再同源于一个数，所以理由必须留在调用点上，不许只写在令牌里。
        return dark ? VisualFill.pillHover
                    : HoverInk.opacity(level: VisualFill.controlHover, dark: dark)
    }
}

/// 保留"可聚焦"（方向键必须还能用），只关掉系统画的那一圈焦点环。
///
/// `focusEffectDisabled()` 是 macOS 14 才有的 API；本项目部署下限是 12，所以 12/13 上这圈环仍然会画
/// —— 那是平台没有对应开关，不是漏了。守卫见 `SidebarKeyboardNavigationTests`
/// （它同时钉住"还挂着 `.focusable()`"和"环被关掉了"两件事，防止改一个坏另一个）。
fileprivate extension View {
    @ViewBuilder func sidebarFocusRingHidden() -> some View {
        if #available(macOS 14.0, *) {
            self.focusEffectDisabled()
        } else {
            self
        }
    }
}

/// 侧栏顶部那颗「全部 / 收藏」。
///
/// **为什么不是 `private`**（R230 / BACKLOG 251）：要一张"只有这一段被点亮"的帧，
/// 只能把它单独放进夹具 —— 挂在整条侧栏上拍的话，同一枚取证键会同时点亮列表里每一颗星标，
/// 那张帧替证的就不是"悬停的那一层灰"，而是"指针同时出现在八个地方"这种产品里不存在的样子。
/// 表面没换：这颗胶囊自己画底（`VisualMaterial.track` + `selectedSegment`），所以单独放它出来
/// 读到的就是产品里那片底（R24 那条"组件帧必须与产品对齐"判的是同一件事）。
/// 放开可见性的先例是 R45 / R229 的 `RowFavoriteButton`。
struct SegmentedFilterPicker: View {
    @Binding var selection: HistoryStore.Filter
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    /// 色档由**这个视图自己**问，不从调用点传（`FilterSegmentButton` / `PressedLabel` 同一条规矩：
    /// 传进来就等于允许调用方 —— 包括夹具 —— 替产品决定"这一档该多亮"）。
    @Environment(\.colorScheme) private var colorScheme

    /// 两个来源**取或**（R12）。这一段以前只读系统开关，而全仓其他地方读的是
    /// `MotionCatalog.motionShouldBeReduced`（系统开关 ∪ VoiceOver）⇒
    /// 同一个人开着 VoiceOver 时，别处都降级了、只有这颗胶囊还在弹。
    /// 环境那一份不能丢：它是**自动响应**的（中途改设置立刻生效），
    /// 目录那一份要等视图重算 —— 两个都要才既全又活。
    private var shouldReduce: Bool { reduceMotion || MotionCatalog.motionShouldBeReduced }

    var body: some View {
        ZStack {
            VisualShape.rounded(VisualRadius.track)
                .fill(VisualMaterial.track)

            slidingPill

            HStack(spacing: 0) {
                ForEach(HistoryStore.Filter.allCases) { filter in
                    FilterSegmentButton(
                        title: filter.title,
                        isSelected: selection == filter,
                        action: { selection = filter }
                    )
                }
            }
        }
        .frame(height: 26)
        .clipShape(VisualShape.rounded(VisualRadius.track))
    }

    private var slidingPill: some View {
        GeometryReader { geo in
            // R189 / BACKLOG 210：几何交给纯函数算，视图里只留"照着放"这一句。
            //
            // 原来是 `frame(width: w/count - 2)` + `offset(x: idx*(w/count)+1)` —— 那个 `offset` 的基准
            // 是 `GeometryReader` 给子视图的**默认摆放位置**，而这件事实测与"第 idx 段"不一致：
            // 两态对照（`.all` / `.favorites` 各拍一张，同一把尺量亮区中心）读出来是
            // `.all` 的亮区在**右**段、`.favorites` 的亮区在**左**段（`FILTER_PILL_BAND` 24 桶：
            // all=[…,36,255×11] / fav=[245,255×11,36,…]），也就是**镜像**。
            // 改成 `.position`（把中心直接钉在纯函数算出来的那块上）之后，摆放不再依赖任何隐式对齐，
            // 而"药丸在第几段"变成一个能被像素判据打红的数。
            let allCases = HistoryStore.Filter.allCases
            let idx = FilterPillGeometry.segmentIndex(selection, in: allCases)
            let rect = FilterPillGeometry.pillRect(
                in: CGRect(origin: .zero, size: geo.size),
                count: allCases.count,
                index: idx)
            ZStack {
                VisualShape.rounded(VisualRadius.control)
                    .fill(VisualMaterial.selectedSegment)
                // R345 / 399：亮档选中那颗补一根发丝边 —— 身份从"亮度"换到"边界"，亮度频道让给悬停。
                if let w = SegmentEdge.width(dark: colorScheme == .dark),
                   let a = SegmentEdge.alpha(dark: colorScheme == .dark) {
                    VisualShape.rounded(VisualRadius.control)
                        .strokeBorder(Color.primary.opacity(a), lineWidth: w)
                }
                if let lift = SegmentKnob.liftAlpha(dark: colorScheme == .dark) {
                    // **同一颗形状再盖一层**，而不是换一种颜色：抬量必须压在 R333 那枚语义基准之上，
                    // 这样"平台惯例那一枚"与"盖掉轨道漂移的那一点量"是两件事，各自能被刀指着改。
                    VisualShape.rounded(VisualRadius.control)
                        .fill(Color.white.opacity(lift))
                }
            }
            .frame(width: rect.width, height: rect.height)
            .position(x: rect.midX, y: rect.midY)
                .animation(FilterPillMotion.slideAnimation(reduceMotion: shouldReduce), value: selection)
        }
    }
}

private struct FilterSegmentButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    /// 色档由**这个视图自己**问，不从调用点传（`PressedLabel` 同一条规矩：
    /// 传进来就等于允许调用方 —— 包括夹具 —— 替产品决定"这一档该多亮"）。
    @Environment(\.colorScheme) private var colorScheme
    /// 取证通道（R229 的键，R230 接到这一家）。产品路径永远 `nil` ⇒ 这一半行为一字未动。
    @Environment(\.hoveredForCapture) private var hoveredForCapture

    /// **只有底色那一层**跟着取证通道亮，缩放不亮。
    ///
    /// 为什么不一起亮：`hoverScale` 改的是几何，一张"什么都没人指、四段却都放大 8%"的帧
    /// 不是产品里任何一个样子，把它钉进基线就是让基线替一个不存在的状态作证。
    /// 而本轮要量的恰好只有"多出来的那层灰看不看得见"这一半 —— 那半必须是产品画的那半，
    /// 所以汇到同一个 `hoverFill` 调用（R14 那一课）。
    private var isHoveredForFill: Bool { isHovered || (hoveredForCapture ?? false) }

    /// 同 `SegmentedFilterPicker.shouldReduce`：系统开关 ∪ VoiceOver。
    private var shouldReduce: Bool { reduceMotion || MotionCatalog.motionShouldBeReduced }

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: VisualFont.row, weight: isSelected ? .semibold : .regular))
                .scaleEffect(FilterPillMotion.hoverScale(isHovered: isHovered, reduceMotion: shouldReduce))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 5)
                .padding(.horizontal, 10)
                .background(
                    // 减弱动态时缩放归 1.0，这一层就是**唯一**的悬停表达 ——
                    // 以前这一段只剩缩放一种说法，于是"开了减弱动态 = 悬停没有反馈"。
                    VisualShape.rounded(VisualRadius.control)
                        .fill(Color.primary.opacity(
                            FilterPillMotion.hoverFill(isHovered: isHoveredForFill, isSelected: isSelected,
                                                       dark: colorScheme == .dark)))
                )
                .contentShape(Rectangle())
        }
        // **`hoverLevel: 0` 是刻意的**（R230，与 `GlassPillButton` 的 R20 那一处同一件事）：
        // 这一段本来就已经在上面自己画了一层 `controlHover`，而 `pressedStyle` 默认还要再叠一层
        // `VisualFill.hover`=0.06 ⇒ 悬停时实际是 0.06 + 0.08 = 约 0.14，**比"控件"那一档高一倍**，
        // 而且这两层各走各的换算 —— R229 那一抬只落在下面那层上，于是"亮档抬一档"在这里
        // 变成了"两层里的一层抬、另一层不抬"。修法与 R20 一致：悬停交给画它的那一处，
        // 样式只留按压那一档（`isPressed` 分支不受 `hoverLevel` 影响）。
        .pressedStyle(in: VisualShape.rounded(VisualRadius.control), hoverLevel: 0)
        // R194 试过在这里加 `.focusable(true) + @FocusState + 一条 accent 描边`，
        // 探针实测**没有效果**（Tab 链 12 站仍然全是搜索框的字段编辑器，段按钮一站都不是）⇒ 代码删掉，
        // 只留下这条读数与它撑着的缺口：可达性不是加一个修饰符就能买到的，得先弄清 List 宿主怎么排 key-view。
        // 见 `UIInteractionProbeTests.testFilterSegmentsAreReachableAndShowFocus` 与 BACKLOG 220。
        // 参数从目录拿，不在这里写死 0.14：这一档以前散在四处、分别是 0.11/0.14/0.15/0.18，
        // 没人说得出哪个对（M11）。悬停跟着鼠标 ⇒ 给最短的那一档。
        .animation(MotionCatalog.animation(for: .hover), value: isHoveredForFill)
        .animation(MotionCatalog.animation(for: .selection), value: isSelected)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

/// R494：主侧栏标题图标的负向帧缝（产品默认 nil ⇒ 画）。
struct MainSidebarTitleIconForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var mainSidebarTitleIconForCapture: Bool? {
        get { self[MainSidebarTitleIconForCaptureKey.self] }
        set { self[MainSidebarTitleIconForCaptureKey.self] = newValue }
    }
}
