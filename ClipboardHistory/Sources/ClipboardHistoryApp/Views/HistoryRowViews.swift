import SwiftUI

struct HistoryRowButton: View {
    let entry: HistoryStore.Entry
    let selected: Bool
    let action: () -> Void
    @State private var isHovered = false

    private var backgroundOpacity: Double {
        if selected { return 0.16 }
        return isHovered ? 0.045 : 0
    }

    var body: some View {
        Button(action: action) {
            HistoryRow(entry: entry)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 9, style: .continuous)
                        .fill(selected ? Color.accentColor.opacity(backgroundOpacity) : Color.primary.opacity(backgroundOpacity))
                )
                .contentShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
        }
        .buttonStyle(.plain)
        // 行以前不暴露 selected 态：VoiceOver 用户听不出自己选中了哪一条（审计第二轮 1.11 / R2-02）。
        .accessibilityAddTraits(selected ? .isSelected : [])
        .animation(.easeInOut(duration: 0.11), value: isHovered)
        .animation(.easeInOut(duration: 0.11), value: selected)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

struct HistoryRow: View {
    let entry: HistoryStore.Entry

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "star.fill")
                .font(.system(size: 10, weight: .semibold))
                .foregroundStyle(entry.isFavorite ? .yellow : .clear)
                .frame(width: 14, height: 14)
                // 未收藏时这颗星是 .clear（完全隐形），既不该占视觉位置也不该被朗读；
                // 已收藏时它是这一行唯一的收藏线索，必须能被 VoiceOver 读到（审计 R-54）。
                .accessibilityHidden(!entry.isFavorite)
                .helpLabel("已收藏")

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
                    // 复制时间是行内唯一的时间信息，tertiary 在暗色下实测 2.2:1，读不出来
                    .font(.system(size: 10)).foregroundStyle(.secondary)
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
