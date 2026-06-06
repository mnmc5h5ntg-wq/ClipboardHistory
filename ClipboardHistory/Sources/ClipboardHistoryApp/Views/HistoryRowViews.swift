import SwiftUI

struct HistoryRowButton: View {
    let entry: ClipboardManager.Entry
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
    let entry: ClipboardManager.Entry

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
        }
    }
}

private struct FileNameText: View {
    let url: URL

    private var baseName: String {
        let fileName = url.lastPathComponent
        let fileExtension = url.pathExtension
        guard !fileExtension.isEmpty else { return fileName }
        return String(fileName.dropLast(fileExtension.count + 1))
    }

    private var fileExtension: String {
        url.pathExtension
    }

    var body: some View {
        HStack(spacing: 0) {
            Text(baseName.isEmpty ? url.lastPathComponent : baseName)
                .lineLimit(1)
                .truncationMode(.middle)
                .layoutPriority(0)

            if !fileExtension.isEmpty {
                Text(".\(fileExtension)")
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)
                    .layoutPriority(1)
            }
        }
    }
}
