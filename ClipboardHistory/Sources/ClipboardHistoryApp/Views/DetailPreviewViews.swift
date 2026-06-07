import Quartz
import SwiftUI

struct QuickLookPreview: NSViewRepresentable {
    let url: URL

    func makeNSView(context: Context) -> QLPreviewView {
        let view = QLPreviewView()
        view.autostarts = true
        return view
    }

    func updateNSView(_ nsView: QLPreviewView, context: Context) {
        nsView.previewItem = url as QLPreviewItem
    }
}

struct DetailFileView: View {
    let url: URL
    let thumbnail: StoredImage?
    private let preview: FilePreview

    init(url: URL, thumbnail: StoredImage?) {
        self.url = url
        self.thumbnail = thumbnail
        self.preview = FilePreviewLoader.load(url: url, thumbnail: thumbnail)
    }

    var body: some View {
        switch preview.content {
        case .image(let nsImage):
            ImagePreviewView(nsImage: nsImage)
        case .text(let content):
            textPreview(content)
        case .quickLook:
            QuickLookPreview(url: preview.url)
        case .fallback:
            fallbackView(preview)
        }
    }

    private func textPreview(_ content: String) -> some View {
        ScrollView([.vertical, .horizontal]) {
            Text(content)
                .font(.system(size: 13, design: .monospaced))
                .foregroundStyle(.primary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(20)
                .textSelection(.enabled)
        }
    }

    private func fallbackView(_ preview: FilePreview) -> some View {
        VStack(spacing: 16) {
            if let thumb = preview.thumbnail {
                Image(nsImage: thumb.nsImage)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 128, height: 128)
            } else {
                Image(systemName: "doc.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(.quaternary)
            }
            Text(preview.url.lastPathComponent)
                .font(.system(size: 14))
            Text(preview.url.path)
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .textSelection(.enabled)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
