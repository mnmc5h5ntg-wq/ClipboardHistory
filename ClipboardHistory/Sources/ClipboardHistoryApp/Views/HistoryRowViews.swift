import SwiftUI

/// 侧栏里的一行（第三轮审计 D-1，最终形态见账本 D-034）。
///
/// 这一行活在 `List(selection:)` 里，所以职责收窄成三件事：星标、行首视觉列、文本列。
/// **选中态与选中高亮不再由这里画** —— 以前它是"行自己的 Button + 自绘圆角底色"，
/// 配合 `List` 会出现两套选中语言（系统给整行画蓝底，我们又叠一层 `primary.opacity`），
/// 而且键盘/VO 的选中语义只能信系统那一份。
///
/// 拖出挂在**整行**上（`EntryDragModifier`）。这不是回到 D-1 之前的样子：那时的问题是
/// "整行拖出"与"整行拖选"抢同一次按下；而 `List` 会把行内任何一处 `.onDrag` 提升成整行拖拽源，
/// 所以"只让行首把手可拖"在系统列表里做不到。取舍是留拖出、去拖选（D-034）。
struct HistoryRowButton: View {
    let entry: HistoryStore.Entry
    /// 双击这一行 = 复制这条（与详情区浮层的"再次复制"同一个动作，见 `copyAction` 的接线处）。
    let copyAction: () -> Void
    /// 点行首星标 = 收藏/取消收藏。
    let favoriteAction: () -> Void
    /// R456：侧栏当前的搜索词。只用来给**行里可见的文字**标命中片段；
    /// 空串表示没有搜索，所有行原样（不编高亮）。默认值留给直接构造行的夹具。
    var searchQuery: String = ""
    @State private var isHovered = false
    @Environment(\.hoveredEntryIDForCapture) private var hoveredEntryIDForCapture
    @ObservedObject private var dragSourceFeedback = DragSourceFeedback.shared
    @Environment(\.draggingEntryIDForCapture) private var draggingEntryIDForCapture
    @Environment(\.colorScheme) private var colorScheme
    private var isHoveredForDrawing: Bool {
        isHovered || hoveredEntryIDForCapture == entry.id
    }
    /// R427：这一条正在被拖出去 ⇒ 内容退到背景里，告诉用户"手里的东西就是它"。
    private var isDraggingForDrawing: Bool {
        dragSourceFeedback.state.isDragging(entry.id) || draggingEntryIDForCapture == entry.id
    }

    var body: some View {
        HStack(spacing: 6) {
            // 星标刻意放在选中区之外：它是行的兄弟控件，点它不该改变选中（D-028 实测过归属）。
            RowFavoriteButton(isFavorite: entry.isFavorite, action: favoriteAction)

            RowLeadingVisual(entry: entry)
                .frame(width: 30)

            RowPinnedBadge(isPinned: entry.isPinned)

            RowTextColumn(entry: entry, searchQuery: searchQuery)
        }
        // R427：正在拖出去的那一条退到背景里（只降内容，不动行底/悬停底）。
        .opacity(isDraggingForDrawing ? DragSourceFeedback.dimOpacity : 1)
        .padding(.vertical, 6)
        .background(
            VisualShape.rounded(VisualRadius.panel)
                .fill(Color.primary.opacity(
                    isHoveredForDrawing
                        ? HoverInk.opacity(level: VisualFill.hover, dark: colorScheme == .dark)
                        : 0
                ))
        )
        .contentShape(Rectangle())
        // 双击必须用 `simultaneousGesture(TapGesture(count: 2))`，**不能**用 `.onTapGesture(count: 2)`。
        // 用户真机反馈：换成 onTapGesture 之后"点一行到显示已选中"有可感知的延迟 ——
        // `count: 2` 的 tap 识别器要等一个双击间隔才能确定"这只是一次单击"，
        // 而 `List` 的选中走的正是这一套行内点击识别，于是高亮被整体推迟了一个双击间隔。
        // `simultaneousGesture` 不参与"谁赢"的仲裁：行的选中照常立刻发生，第二击仍然触发复制
        // （这是 D-028 当时在真实侧栏容器里验证过的形状）。
        // 我当初换成 onTapGesture 是为了迁就一条**离屏孤立宿主**里收不到第二击的探针 ——
        // 那是夹具不代表真实容器，拿产品行为去迁就它是要写进账本的错误（D-036）。
        .simultaneousGesture(
            TapGesture(count: 2).onEnded {
                guard RowDoubleTap.shouldCopy(modifiers: NSEvent.modifierFlags) else { return }
                copyAction()
            }
        )
        // 有载荷才挂（判据 `EntryDragGate.offersDrag`）：多文件条目、网页链接、空文本不提供拖出。
        .modifier(EntryDragModifier(entryID: entry.id, content: entry.content))
        // 提示语为空时整个 modifier 都不挂：`.help("")` 在 macOS 上会弹出一个空气泡。
        .modifier(RowDragHelpModifier(content: entry.content))
        .animation(MotionCatalog.animation(for: .hover), value: isHoveredForDrawing)
        .onHover { hovering in isHovered = hovering }
    }
}

/// 拖出提示的文案与接线。**公开是为了让"没有载荷就不许承诺"这件事可测。**
enum RowDragHelp {
    static func text(for content: ClipboardEntryContent) -> String {
        EntryDragGate.offersDrag(for: content)
            ? "拖动这一行可导出到别的应用"
            : ""
    }
}

private struct RowDragHelpModifier: ViewModifier {
    let content: ClipboardEntryContent

    @ViewBuilder
    func body(content: Content) -> some View {
        let help = RowDragHelp.text(for: self.content)
        if help.isEmpty {
            content
        } else {
            // `helpLabel` 同时给 `.help` 与 `accessibilityLabel`：只给悬浮提示的话 VoiceOver 读不到。
            content.helpLabel(help)
        }
    }
}

/// 行首的收藏星标。以前它只是"已收藏"的指示器（未收藏时整颗是 `.clear`，等于不存在），
/// 现在它是真正的控件：未收藏时也要看得见、点得到，否则用户不知道有这个东西。
///
/// **为什么不是 `private`**（R229 / BACKLOG 251）：`VisualFill.controlHover` 存在的理由
/// 全在这颗 20pt 圆上（"6% 铺在整行读得出来，铺在图标上等于没有"），而这一档从来没有一张帧 ——
/// 合成 hover 的三条路 R14 实测全断。把它留出文件边界，配合 `EnvironmentValues.hoveredForCapture`
/// 取证通道，这一档第一次能被离线渲染、逐档量、被眼睛看。抽取/放开的先例是 R45 的
/// `DailyCopyHeatmapCell`（"抽它的理由不是文件长，是这件事以前只能靠注释"）。
/// 产品路径仍然只由 `onHover` 驱动，这个可见性变化不改任何行为。
struct RowFavoriteButton: View {
    let isFavorite: Bool
    let action: () -> Void
    @State private var isHovered = false
    /// 取证通道（R263 / BACKLOG 291 的 `HistoryRowViews.swift` 那一行）：**产品永远不写这颗键**，
    /// 只有夹具写。它补的是"两半只接了一半"——`.pressedStyle` 那一层（药丸填充）早就经
    /// `PressableStyle` 读得到键，而**字形墨**这一半（下面 `tint` 的 0.55 → 0.78）当时还直读
    /// 裸 `isHovered` ⇒ 离屏渲染里 `.onHover` 恒 false，那一抬在帧里根本不存在，
    /// 于是"量不到"被记成"这一位没问题"（R90 那一族）。
    @Environment(\.hoveredForCapture) private var hoveredForCapture

    private var isHoveredForDrawing: Bool { isHovered || (hoveredForCapture ?? false) }

    var body: some View {
        Button(action: action) {
            Image(systemName: FavoriteTogglePresentation.symbolName(isFavorite: isFavorite))
                .font(.system(size: VisualFont.meta, weight: .regular))
                .foregroundStyle(tint)
                // 行里这颗星**也会换符号**（star ↔ star.fill），而它就在用户点的那一行上：
                // 上一轮只给详情浮层那颗胶囊接了过渡，行内这一处是漏的（M5 的原文是
                // "收藏 / pin 切换"，不限一处）。
                // ⚠️ 它在一个 `List` 行里 —— 行**位置**的过渡已实测跑不出来（D-055），
                // 行**内部**的符号过渡能不能跑，由 `MotionFilmstripTests` 的星标带判据量，
                // 不靠推测。
                .symbolMotion(symbol: FavoriteTogglePresentation.symbolName(isFavorite: isFavorite),
                              replacesSymbol: true,
                              bounceValue: isFavorite ? 1 : 0)
                .frame(width: 20, height: 20)
                .contentShape(Rectangle())
        }
        // 悬停档抬到"控件"那一档（R20）：这颗星是 20×20 的圆里装一个 11pt 的字形，
        // 默认那一档（`VisualFill.hover`=0.06）是给"一整行"那种大面积定的，
        // 铺在 20pt 圆上等于没有（`VisualFill.controlHover` 那条注释说的就是这件事，
        // R15 只在三处落实了它 —— 判据数的是"三处"，所以剩下的位点一直不在视野里）。
        // **不加 `labelPadding`**：它的 label 已经有 20×20 的 frame，高亮本来就比笔画大一圈；
        // 再垫 4pt 会把整行的文字列往右推 8pt（侧栏宽度是定的），那是版式不是反馈。
        .pressedStyle(in: Circle(), hoverLevel: VisualFill.controlHover)
        .helpLabel(FavoriteTogglePresentation.helpText(isFavorite: isFavorite))
        .accessibilityLabel(FavoriteTogglePresentation.helpText(isFavorite: isFavorite))
        .animation(MotionCatalog.animation(for: .hover), value: isHoveredForDrawing)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    /// 未收藏时不能是 `.clear`（看不见就没人会去点），也不能太抢眼（一行里它是配角）。
    /// 0.55 这个值是量出来的：0.28 时星标与行底的对比度只有亮色 1.76:1 / 暗色 2.17:1，
    /// 达不到"可交互控件至少 3:1"这一条；提到 0.55 后两边都过 3:1，悬停再抬到 0.78。
    /// R263：那两句"量出来的"第一次有了会红的判据（`testFavoriteGlyphInkClearsTheInteractiveFloor`
    /// 从**帧**里读静置与悬停两态的字形墨），而这一抬以前只活在注释里 —— 读裸 `isHovered`
    /// 意味着离屏帧里 0.78 那一档从来不存在。
    private var tint: AnyShapeStyle {
        if isFavorite { return AnyShapeStyle(FavoriteTogglePresentation.favoriteColor) }
        return AnyShapeStyle(Color.primary.opacity(isHoveredForDrawing ? 0.78 : 0.55))
    }
}

/// 行首的固定徽标（§5 F-5）。
///
/// 位置刻意做成一个**恒定占位**的 12pt 槽：未固定时什么都不画，固定时画 `pin.fill`。
/// 不占位的话固定/取消固定会让整列文本横向平移 18pt —— 用户点一下"固定"，看到的是所有行
/// 一起抖，这比看不见徽标更糟。`row-pinned-on` / `row-pinned-off` 两帧就是"文本起点没动"的证据。
///
/// 对比度沿用收藏那颗星量出来的值（0.55 是"可看见"下限、0.78 是"可交互"值）：这一版取 0.78，
/// 因为"已固定"是这一行存在的理由（它会跳到列表顶部），不该比一个空闲控件更难看见。
private struct RowPinnedBadge: View {
    let isPinned: Bool

    var body: some View {
        Group {
            if isPinned {
                Image(systemName: PinTogglePresentation.symbolName(isPinned: true))
                    .font(.system(size: VisualGlyph.badge, weight: .semibold))
                    .foregroundStyle(Color.primary.opacity(0.78))
                    // R160：这枚徽标**以前什么都不说**。它不是控件（点它没有反应），
                    // 但它是这一行唯一"自己会变"的东西 —— 用户点过「固定」之后，某天看见行首多了一枚图钉，
                    // 手边没有任何一句话告诉他"这条不会被新记录顶下去、也不会被保留策略删掉"。
                    // 悬浮提示是这件事的唯一原生通道（help tag 不占布局、不抢焦点、与两档配色和减弱动态无关），
                    // 文案回答"它为什么在这儿"而不是"这是一个图钉"（后者用户已经看得见）。
                    // 用 `.helpLabel` 而不是裸 `.help`：前者同时给 `.help` 与 `accessibilityLabel`，
                    // 只给悬浮提示的话 VoiceOver 读不到 —— 这一条由
                    // `AccessibilityLabelHygieneTests.testViewsNeverUseBareHelpWithoutAccessibilityLabel` 钉住
                    // （本轮第一版写的是裸 `.help`，被它当场红掉，改的是我的写法，不是那道守卫）。
                    .helpLabel("已固定：不会被新记录顶出历史，也不会被保留策略清理")
                    // 徽标是"从无到有"，所以给淡入而不是弹跳：槽位宽度恒定（见上面注释），
                    // 淡入不会让任何一行横向抖。
                    .transition(MotionCatalog.transition(for: .contentFade))
            } else {
                Color.clear
            }
        }
        .frame(width: 12, height: 14)
        .animation(MotionCatalog.animation(for: .contentFade), value: isPinned)
    }
}

/// 行首的视觉列（缩略图优先，没有缩略图才画符号）。
/// D-1 期间它曾叫"把手"并独占拖出入口 —— 那个设计被真机否掉了（`List` 会把行内 `.onDrag`
/// 提升成整行拖拽源），现在拖出挂在整行上，见 `HistoryRowButton` 与账本 D-034。
///
/// 它以前外面还包着一层 `HistoryRow`（行首视觉列 + 文本列的"旧组合入口"），
/// 注释写着"保留给夹具与详情以外的调用点复用"，而实测**产品与测试都没有一个调用点**：
/// 那句理由是编的，层本身是死的（R1 删除，判据见 `VisualTokenTests.testNoDeadSurfaceInViews`）。
private struct RowLeadingVisual: View {
    let entry: HistoryStore.Entry

    var body: some View {
        switch entry.content {
        case .text:
            // R431：同 `ThumbnailSymbol` —— 相对环境的 `.secondary` 在这一列会被解析成
            // 与行底同色的白/黑（暗档整枚图标看不见），改用绝对的动态 label 色。
            Image(systemName: "doc.text")
                .font(.system(size: VisualFont.row))
                .foregroundStyle(Color(nsColor: .secondaryLabelColor))
                .frame(width: 16)
        case .image(let stored):
            ThumbnailImage(nsImage: stored.nsImage)
        case .file:
            if let thumb = entry.thumbnail {
                ThumbnailImage(nsImage: thumb.nsImage)
            } else {
                ThumbnailSymbol(systemName: "doc")
            }
        case .files:
            if let thumb = entry.thumbnail {
                ThumbnailImage(nsImage: thumb.nsImage)
            } else {
                ThumbnailSymbol(systemName: "doc.on.doc")
            }
        }
    }
}

/// 标题 + 复制时间两行。
private struct RowTextColumn: View {
    let entry: HistoryStore.Entry
    /// R456：命中高亮只落在可见文字上 —— 标题/文件名按搜索词标，来源行只标 App 名。
    let searchQuery: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            switch entry.content {
            case .file(let url):
                FileNameText(url: url, searchQuery: searchQuery)
                    .font(.system(size: VisualFont.row))
            case .files(let urls):
                MultiFileTitle(urls: urls, searchQuery: searchQuery)
                    .font(.system(size: VisualFont.row))
            default:
                Text(HistoryRowMatchHighlight.highlighted(entry.shortPreview, query: searchQuery))
                    .font(.system(size: VisualFont.row))
                    .lineLimit(2)
                    .truncationMode(.tail)
            }
            // R444：时间行补「· 来自 <来源 App>」—— 主列表第一次有来源（此前只有详情头部有）。
            // 时间在前、来源在后：行宽不够时先截断来源，时间不丢；来源 nil 时只显示时间。
            // R456：搜索命中的 App 名带高亮；时间不参与匹配，所以不标时间。
            Text(HistoryRowMatchHighlight.sourceLine(
                time: ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp),
                sourceAppName: entry.sourceAppName,
                query: searchQuery))
                // tertiary 在暗色下实测 2.2:1，读不出来；字号 10pt 低于 HIG 的正文下限
                // （审计第二轮 1.2 / 账本 R2-13），所以这一行是 11pt secondary。
                .font(.system(size: VisualFont.meta)).foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.tail)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct FileNameText: View {
    let url: URL
    var searchQuery: String = ""

    private var fileNameParts: EntryPresentation.FileNameParts {
        EntryPresentation.fileNameParts(for: url)
    }

    var body: some View {
        HStack(spacing: 0) {
            Text(HistoryRowMatchHighlight.highlighted(fileNameParts.displayBaseName,
                                                      query: searchQuery))
                .lineLimit(1)
                .truncationMode(.middle)
                .layoutPriority(0)

            if !fileNameParts.fileExtension.isEmpty {
                Text(HistoryRowMatchHighlight.highlighted(".\(fileNameParts.fileExtension)",
                                                          query: searchQuery))
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)
                    .layoutPriority(1)
            }
        }
    }
}

private struct MultiFileTitle: View {
    let urls: [URL]
    var searchQuery: String = ""

    var body: some View {
        if let firstURL = urls.first {
            HStack(spacing: 0) {
                FileNameText(url: firstURL, searchQuery: searchQuery)
                    .layoutPriority(0)
                Text(" 等 \(urls.count) 个")
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)
            }
        } else {
            Text("多个文件")
        }
    }
}
