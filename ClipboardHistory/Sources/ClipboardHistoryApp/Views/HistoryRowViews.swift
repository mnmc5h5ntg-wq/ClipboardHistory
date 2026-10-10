import SwiftUI

/// 侧栏里的一行（第三轮审计 D-1 之后）。
///
/// 这一行现在活在建好的 `List(selection:)` 里，所以职责收窄成三件事：
/// 星标、把手（唯一的拖出入口）、文本列。**选中态与选中高亮不再由这里画** ——
/// 以前它是"行自己的 Button + 自绘圆角底色"，配合 `List` 会出现两套选中语言
/// （系统给整行画蓝底，我们又叠一层 `primary.opacity`），而且键盘/VO 的选中语义只能信系统那一份。
///
/// 也不再挂整行的 `.onDrag`：那正是缺陷 D-1（拖出会话在每个阈值处抢先，列表拖选整片失效）。
/// 拖出只从把手发起，判据在 `EntryDragGate.prepareForDrag`。
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

            RowDragHandle(entry: entry)

            RowTextColumn(entry: entry)
        }
        .padding(.vertical, 6)
        .contentShape(Rectangle())
        // 双击用 `onTapGesture(count: 2)`，**不是** `simultaneousGesture(TapGesture(count: 2))`：
        // 换成 `List(selection:)` 之后行里没有自己的 Button 了，没有兄弟手势时 simultaneousGesture
        // 在离屏宿主里实测收不到第二击（探针 copyFired=0），而 onTapGesture 会。
        // 单击选中仍然立刻生效 —— 那是 NSTableView 在 mouseDown 里做的，不与这个手势竞争。
        // （以前这里用 simultaneousGesture 是为了绕开"Button 单击要等双击间隔"；那个前提已经不成立，
        // 见 D-028 与本次 D-1 的取舍。）
        .onTapGesture(count: 2) {
            guard RowDoubleTap.shouldCopy(modifiers: NSEvent.modifierFlags) else { return }
            copyAction()
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

/// 把手的提示语。独立成一个类型是为了让"没有载荷就不许承诺"这件事可测
/// （`RowDragHandle` 本身是 private，测试够不到它的静态方法）。
enum RowDragHandleHelp {
    /// 没有载荷的条目不挂拖出（`EntryDragGate` 会判 false），那就不该给一句承诺落空的提示。
    static func helpText(for content: ClipboardEntryContent) -> String {
        EntryDragGate.prepareForDrag(origin: .handle, content: content)
            ? "按住这里拖到别的应用，即可导出这一条"
            : ""
    }
}

/// 拖出的**唯一**入口：行首的缩略图/图标那一列。
/// 放在这里而不是整行，是 D-1 的修法本身 —— 见 `EntryDragGate`。
private struct RowDragHandle: View {
    let entry: HistoryStore.Entry

    /// 提示语为空时**整个修饰符都不挂**：`.help("")` 在 macOS 上会弹出一个空气泡，
    /// 而没载荷的行本来就没有拖出 affordance，什么都不说才对。
    var body: some View {
        let help = RowDragHandleHelp.helpText(for: entry.content)
        if help.isEmpty {
            RowLeadingVisual(entry: entry)
                .frame(width: 30)
        } else {
            RowLeadingVisual(entry: entry)
                .frame(width: 30)
                .modifier(EntryDragModifier(content: entry.content))
                .helpLabel(help)
        }
    }
}

struct HistoryRow: View {
    let entry: HistoryStore.Entry

    var body: some View {
        HStack(spacing: 8) {
            RowLeadingVisual(entry: entry)
            RowTextColumn(entry: entry)
        }
    }
}

/// 行首的视觉（缩略图优先，没有缩略图才画符号）。它同时是拖出的把手。
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
