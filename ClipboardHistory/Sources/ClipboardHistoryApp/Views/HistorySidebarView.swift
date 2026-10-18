import AppKit
import SwiftUI

struct HistorySidebarView: View {
    @ObservedObject var historyStore: HistoryStore
    /// 拖放悬停反馈（虚线框）。
    @State private var isDropTargeted = false

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
                    systemName: "clipboard",
                    title: emptyTitle,
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
        .animation(MotionCatalog.animation(for: .contentFade), value: historyStore.filteredEntries.isEmpty)
    }

    private var header: some View {
        HStack {
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
                Text(countText)
                    .font(.system(size: VisualFont.body, weight: .regular))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
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
        HStack(spacing: 0) {
            Button {
                historyStore.perform(.favoriteSelection)
            } label: {
                Image(systemName: "star")
            }
            .helpLabel("收藏所选记录")

            Button {
                // 固定 = "这条我要长期留着，别被复制顶下去、别被保留策略删掉"（§5 F-5）
                historyStore.perform(.pinSelection(isPinned: true))
            } label: {
                Image(systemName: PinTogglePresentation.actionSymbolName(isPinning: true))
            }
            .helpLabel(PinTogglePresentation.helpText(isPinned: false))

            Button {
                historyStore.perform(.pinSelection(isPinned: false))
            } label: {
                Image(systemName: PinTogglePresentation.actionSymbolName(isPinning: false))
            }
            .helpLabel(PinTogglePresentation.helpText(isPinned: true))

            Button {
                historyStore.perform(.unfavoriteSelection)
            } label: {
                Image(systemName: "star.slash")
            }
            .helpLabel("取消收藏所选记录")

            Button(role: .destructive) {
                historyStore.perform(.deleteSelection)
            } label: {
                Image(systemName: "trash")
            }
            .helpLabel("删除所选记录")
            .foregroundStyle(.red)
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

    private var emptyTitle: String {
        if historyStore.entries.isEmpty {
            return "暂无剪贴板历史"
        }
        if historyStore.filter == .favorites {
            return historyStore.favoriteCount == 0 ? "暂无收藏" : "无匹配结果"
        }
        return "无匹配结果"
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
            ForEach(historyStore.filteredEntries) { entry in
                HistoryRowButton(
                    entry: entry,
                    // 双击行 = 详情区浮层那颗"再次复制"，同一个动作同一个语义（会把这条顶到最前）。
                    copyAction: { historyStore.perform(.copyAndPromote(entry)) },
                    favoriteAction: { historyStore.perform(.toggleFavorite(entry)) }
                )
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
            if isDropTargeted {
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
            }
        }
        .animation(MotionCatalog.animation(for: .dropTarget), value: isDropTargeted)
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
                    in: historyStore.filteredEntries.map(\.id)))
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
            _ = historyStore?.addDroppedFiles(urls: urls)
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
    static func hoverFill(isHovered: Bool, isSelected: Bool) -> Double {
        // 选中的那一段下面就是那颗胶囊，再叠一层悬停底会糊成两块。
        guard isHovered, !isSelected else { return 0 }
        return VisualFill.controlHover
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

private struct SegmentedFilterPicker: View {
    @Binding var selection: HistoryStore.Filter
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

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
            VisualShape.rounded(VisualRadius.control)
                .fill(VisualMaterial.sliderPill)
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
                            FilterPillMotion.hoverFill(isHovered: isHovered, isSelected: isSelected)))
                )
                .contentShape(Rectangle())
        }
        .pressedStyle(in: VisualShape.rounded(VisualRadius.control))
        // 参数从目录拿，不在这里写死 0.14：这一档以前散在四处、分别是 0.11/0.14/0.15/0.18，
        // 没人说得出哪个对（M11）。悬停跟着鼠标 ⇒ 给最短的那一档。
        .animation(MotionCatalog.animation(for: .hover), value: isHovered)
        .animation(MotionCatalog.animation(for: .selection), value: isSelected)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
