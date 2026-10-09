import SwiftUI

struct HistoryRowButton: View {
    let entry: HistoryStore.Entry
    let selected: Bool
    let action: () -> Void
    /// 双击这一行 = 复制这条（与详情区浮层的"再次复制"同一个动作，见 `copyAction` 的接线处）。
    let copyAction: () -> Void
    /// 点行首星标 = 收藏/取消收藏。
    let favoriteAction: () -> Void
    @State private var isHovered = false

    private var backgroundOpacity: Double {
        if selected { return 0.16 }
        return isHovered ? 0.045 : 0
    }

    var body: some View {
        HStack(spacing: 2) {
            // 星标刻意放在行的 Button **外面**，是兄弟控件而不是嵌套控件：
            // 嵌套 Button 在 macOS 上点击归属不可靠，点星标会顺手把这一行选中。
            RowFavoriteButton(isFavorite: entry.isFavorite, action: favoriteAction)

            Button(action: action) {
                HistoryRow(entry: entry)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            // 用 simultaneousGesture 而不是把行改成裸手势：Button 的单击要**立刻**改选中，
            // 而 `onTapGesture(count: 2)` 与单击手势并列时，系统会等一个双击间隔再放行单击 ——
            // 那会让每次点选都慢半拍。这里第一击照常选中（幂等），第二击触发复制。
            .simultaneousGesture(
                TapGesture(count: 2).onEnded {
                    guard RowDoubleTap.shouldCopy(modifiers: NSEvent.modifierFlags) else { return }
                    copyAction()
                }
            )
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 9, style: .continuous)
                .fill(selected ? Color.accentColor.opacity(backgroundOpacity) : Color.primary.opacity(backgroundOpacity))
        )
        .contentShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
        // 行以前不暴露 selected 态：VoiceOver 用户听不出自己选中了哪一条（审计第二轮 1.11 / R2-02）。
        .accessibilityAddTraits(selected ? .isSelected : [])
        // 拖出这条记录（审计第二轮 1.5 / R2-05）：文本给字符串、图片给 PNG、单个文件给 file URL 引用。
        // 没有可用载荷时（多文件条目、Web URL、空文本）**不挂** onDrag，避免"拖起来什么都没发生"。
        // 真机拖放无法离屏验证，验证等级见账本 R2-05。
        .modifier(EntryDragModifier(content: entry.content))
        .animation(.easeInOut(duration: 0.11), value: isHovered)
        .animation(.easeInOut(duration: 0.11), value: selected)
        .onHover { hovering in
            isHovered = hovering
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
    /// 0.45 这个值是量出来的：0.28 时星标与行底的对比度只有亮色 1.76:1 / 暗色 2.17:1，
    /// 达不到"可交互控件至少 3:1"这一条；提到 0.45 后两边都过 3:1，悬停再抬到 0.7。
    private var tint: AnyShapeStyle {
        if isFavorite { return AnyShapeStyle(FavoriteTogglePresentation.favoriteColor) }
        return AnyShapeStyle(Color.primary.opacity(isHovered ? 0.78 : 0.55))
    }
}

struct HistoryRow: View {
    let entry: HistoryStore.Entry

    var body: some View {
        HStack(spacing: 8) {
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
