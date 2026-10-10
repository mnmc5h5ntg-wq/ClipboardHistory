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

    var body: some View {
        HStack(spacing: 6) {
            // 星标刻意放在选中区之外：它是行的兄弟控件，点它不该改变选中（D-028 实测过归属）。
            RowFavoriteButton(isFavorite: entry.isFavorite, action: favoriteAction)

            RowLeadingVisual(entry: entry)
                .frame(width: 30)

            RowTextColumn(entry: entry)
        }
        .padding(.vertical, 6)
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
        .modifier(EntryDragModifier(content: entry.content))
        // 提示语为空时整个 modifier 都不挂：`.help("")` 在 macOS 上会弹出一个空气泡。
        .modifier(RowDragHelpModifier(content: entry.content))
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
private struct RowFavoriteButton: View {
    let isFavorite: Bool
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            Image(systemName: FavoriteTogglePresentation.symbolName(isFavorite: isFavorite))
                .font(.system(size: 11, weight: .regular))
                .foregroundStyle(tint)
                .frame(width: 20, height: 20)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .helpLabel(FavoriteTogglePresentation.helpText(isFavorite: isFavorite))
        .accessibilityLabel(FavoriteTogglePresentation.helpText(isFavorite: isFavorite))
        .animation(.easeInOut(duration: 0.11), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    /// 未收藏时不能是 `.clear`（看不见就没人会去点），也不能太抢眼（一行里它是配角）。
    /// 0.55 这个值是量出来的：0.28 时星标与行底的对比度只有亮色 1.76:1 / 暗色 2.17:1，
    /// 达不到"可交互控件至少 3:1"这一条；提到 0.55 后两边都过 3:1，悬停再抬到 0.78。
    private var tint: AnyShapeStyle {
        if isFavorite { return AnyShapeStyle(FavoriteTogglePresentation.favoriteColor) }
        return AnyShapeStyle(Color.primary.opacity(isHovered ? 0.78 : 0.55))
    }
}

/// 行内容的旧组合入口（行首视觉列 + 文本列）。侧栏现在直接用 `HistoryRowButton`，
/// 这里保留给夹具与详情以外的调用点复用。
struct HistoryRow: View {
    let entry: HistoryStore.Entry

    var body: some View {
        HStack(spacing: 8) {
            RowLeadingVisual(entry: entry)
            RowTextColumn(entry: entry)
        }
    }
}

/// 行首的视觉列（缩略图优先，没有缩略图才画符号）。
/// D-1 期间它曾叫"把手"并独占拖出入口 —— 那个设计被真机否掉了（`List` 会把行内 `.onDrag`
/// 提升成整行拖拽源），现在拖出挂在整行上，见 `HistoryRowButton` 与账本 D-034。
private struct RowLeadingVisual: View {
    let entry: HistoryStore.Entry

    var body: some View {
        switch entry.content {
        case .text:
            Image(systemName: "doc.text")
                .font(.system(size: 12)).foregroundStyle(.secondary).frame(width: 16)
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

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            switch entry.content {
            case .file(let url):
                FileNameText(url: url)
                    .font(.system(size: 12))
            case .files(let urls):
                MultiFileTitle(urls: urls)
                    .font(.system(size: 12))
            default:
                Text(entry.shortPreview)
                    .font(.system(size: 12))
                    .lineLimit(2)
                    .truncationMode(.tail)
            }
            Text(ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp))
                // 复制时间是行内唯一的时间信息，tertiary 在暗色下实测 2.2:1，读不出来。
                // 字号也从 10pt 提到 11pt：10pt 低于 HIG 的正文下限，而这一行没有别的冗余信息
                // 可以让它更小（审计第二轮 1.2 / 账本 R2-13）。
                .font(.system(size: 11)).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct FileNameText: View {
    let url: URL

    private var fileNameParts: EntryPresentation.FileNameParts {
        EntryPresentation.fileNameParts(for: url)
    }

    var body: some View {
        HStack(spacing: 0) {
            Text(fileNameParts.displayBaseName)
                .lineLimit(1)
                .truncationMode(.middle)
                .layoutPriority(0)

            if !fileNameParts.fileExtension.isEmpty {
                Text(".\(fileNameParts.fileExtension)")
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)
                    .layoutPriority(1)
            }
        }
    }
}

private struct MultiFileTitle: View {
    let urls: [URL]

    var body: some View {
        if let firstURL = urls.first {
            HStack(spacing: 0) {
                FileNameText(url: firstURL)
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
