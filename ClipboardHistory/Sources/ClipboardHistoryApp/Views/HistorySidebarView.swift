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
                Spacer()
                .transition(MotionCatalog.transition(for: .contentFade))
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
                bulkActionButtons
            } else {
                Text(countText)
                    .font(.system(size: VisualFont.body, weight: .regular))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .frame(height: 39)
        .animation(MotionCatalog.animation(for: .selection), value: historyStore.selectedCount > 1)
    }



    private var bulkActionButtons: some View {
        HStack(spacing: 8) {
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
        .buttonStyle(.borderless)
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
        reduceMotion
            ? SlideMotion(isInstant: true, response: 0, damping: 1)
            : SlideMotion(isInstant: false, response: 0.38, damping: 0.72)
    }

    static func slideAnimation(reduceMotion: Bool) -> Animation {
        let motion = slideMotion(reduceMotion: reduceMotion)
        return motion.isInstant
            ? .linear(duration: 0)
            : .spring(response: motion.response, dampingFraction: motion.damping)
    }

    /// hover 放大：减少动态时不放大（1.0 = 原尺寸）。
    static func hoverScale(isHovered: Bool, reduceMotion: Bool) -> CGFloat {
        guard isHovered, !reduceMotion else { return 1.0 }
        return 1.08
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
            let count = CGFloat(HistoryStore.Filter.allCases.count)
            let idx = CGFloat(HistoryStore.Filter.allCases.firstIndex(of: selection) ?? 0)
            VisualShape.rounded(VisualRadius.control)
                .fill(VisualMaterial.sliderPill)
                .frame(width: geo.size.width / count - 2)
                .padding(.vertical, 1)
                .offset(x: idx * (geo.size.width / count) + 1)
                .animation(FilterPillMotion.slideAnimation(reduceMotion: reduceMotion), value: selection)
        }
    }
}

private struct FilterSegmentButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: VisualFont.row, weight: isSelected ? .semibold : .regular))
                .scaleEffect(FilterPillMotion.hoverScale(isHovered: isHovered, reduceMotion: reduceMotion))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 5)
                .padding(.horizontal, 10)
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
