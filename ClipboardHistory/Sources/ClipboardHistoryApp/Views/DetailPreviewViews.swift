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
    @State private var previewState: MediaLoadingState<FilePreview> = .loading
    @State private var loadingHandle: MediaLoadHandle?

    init(url: URL, thumbnail: StoredImage?) {
        self.url = url
        self.thumbnail = thumbnail
    }

    var body: some View {
        Group {
            switch previewState {
            case .loading:
                loadingView
            case .success(let preview):
                previewView(preview)
            case .failure(let message):
                failureView(message)
            }
        }
        .task(id: url) {
            await loadPreview()
        }
        .onDisappear {
            loadingHandle?.cancel()
            loadingHandle = nil
        }
    }

    @ViewBuilder
    private func previewView(_ preview: FilePreview) -> some View {
        switch preview.content {
        case .image(let nsImage):
            ImagePreviewView(nsImage: nsImage)
        case .text(let content):
            textPreview(content)
        case .video:
            VideoPreview(url: preview.url, aspectRatio: videoAspectRatio(for: preview))
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .quickLook:
            QuickLookPreview(url: preview.url)
        case .fallback:
            fallbackView(preview)
        }
    }

    private var loadingView: some View {
        VStack(spacing: 12) {
            ProgressView()
                .controlSize(.small)
            Text("正在加载预览…")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func failureView(_ message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 36))
                .foregroundStyle(.secondary)
            Text(message)
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
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

    private func videoAspectRatio(for preview: FilePreview) -> CGFloat {
        if let videoAspectRatio = preview.videoAspectRatio,
           videoAspectRatio > 0 {
            return videoAspectRatio
        }
        if let thumbnail {
            let size = thumbnail.nsImage.size
            if size.width > 0, size.height > 0 {
                return size.width / size.height
            }
        }
        return VideoAspectRatioResolver.fallbackAspectRatio
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
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @MainActor
    private func loadPreview() async {
        loadingHandle?.cancel()
        previewState = .loading

        let handle = MediaLoader.loadFilePreviewHandle(url: url, thumbnail: thumbnail)
        loadingHandle = handle
        let result = await handle.value
        guard !Task.isCancelled else { return }
        previewState = result
        loadingHandle = nil
    }
}
