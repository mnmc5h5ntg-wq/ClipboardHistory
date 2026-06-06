import SwiftUI

struct DetailView: View {
    @ObservedObject var manager: ClipboardManager

    var body: some View {
        if let entry = manager.selectedEntry {
            selectedEntryView(entry)
        } else {
            EmptyStateView(
                systemName: "doc.on.clipboard",
                title: "选择一条记录查看详情",
                spacing: 16,
                imageSize: 40,
                titleSize: 14
            )
        }
    }

    private func selectedEntryView(_ entry: ClipboardManager.Entry) -> some View {
        VStack(spacing: 0) {
            header(for: entry)
            Divider()
            preview(for: entry)
        }
        .ignoresSafeArea(edges: .top)
        .overlay(alignment: .bottomTrailing) {
            GlassPill(
                copyAction: { manager.copyToClipboardAndBringToTop(entry) },
                deleteAction: { manager.delete(entry) }
            )
            .padding(12)
        }
    }

    private func header(for entry: ClipboardManager.Entry) -> some View {
        HStack {
            Spacer()
            VStack(alignment: .center, spacing: 2) {
                Text("\(ClipboardDateFormatters.detailTimestamp.string(from: entry.timestamp)) 复制")
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                Text(entry.content.sizeDescription)
                    .font(.system(size: 11))
                    .foregroundStyle(.tertiary)
            }
            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial)
    }

    @ViewBuilder
    private func preview(for entry: ClipboardManager.Entry) -> some View {
        switch entry.content {
        case .text(let text):
            ScrollView(.vertical) {
                Text(text)
                    .font(.system(size: 14, design: .monospaced))
                    .foregroundStyle(.primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(20)
                    .textSelection(.enabled)
            }
        case .image(let stored):
            ImagePreviewView(nsImage: stored.nsImage)
        case .file(let url):
            DetailFileView(url: url, thumbnail: entry.thumbnail)
        }
    }
}
