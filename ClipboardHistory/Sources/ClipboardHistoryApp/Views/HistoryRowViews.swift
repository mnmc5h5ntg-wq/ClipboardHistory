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
            }
            VStack(alignment: .leading, spacing: 2) {
                switch entry.content {
                case .file(let url):
                    FileNameText(url: url)
                        .font(.system(size: 12))
                default:
                    Text(entry.shortPreview)
                        .font(.system(size: 12))
                        .lineLimit(2)
                        .truncationMode(.tail)
                }
                Text(ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp))
                    .font(.system(size: 10)).foregroundStyle(.tertiary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            if entry.isFavorite {
                Image(systemName: "star.fill")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(.yellow)
                    .frame(width: 14, height: 14)
                    .help("已收藏")
            }
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
