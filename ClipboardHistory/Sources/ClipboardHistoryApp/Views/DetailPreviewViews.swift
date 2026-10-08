import Quartz
import SwiftUI

struct QuickLookPreview: NSViewRepresentable {
    let url: URL

    func makeNSView(context: Context) -> QuickLookPreviewContainerView {
        QuickLookPreviewContainerView()
    }

    func updateNSView(_ nsView: QuickLookPreviewContainerView, context: Context) {
        nsView.update(url: url)
    }

    static func dismantleNSView(_ nsView: QuickLookPreviewContainerView, coordinator: ()) {
        nsView.dismantle()
    }
}

enum QuickLookPreviewLoadDecision: Equatable {
    case skip
    case load(requiresFreshView: Bool)
}

struct QuickLookPreviewLifecycle {
    private(set) var loadedURL: URL?
    private(set) var requiresFreshView = false

    mutating func decision(for url: URL) -> QuickLookPreviewLoadDecision {
        if loadedURL == url {
            return .skip
        }

        return .load(requiresFreshView: requiresFreshView || loadedURL != nil)
    }

    mutating func markLoaded(_ url: URL) {
        loadedURL = url
        requiresFreshView = false
    }

    mutating func markDetached() {
        loadedURL = nil
        requiresFreshView = true
    }
}

final class QuickLookPreviewContainerView: NSView {
    private var previewView: QLPreviewView?
    private var previewConstraints: [NSLayoutConstraint] = []
    private var requestedURL: URL?
    private var lifecycle = QuickLookPreviewLifecycle()
    private var isDismantled = false
    private var loadGeneration = 0

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
    }

    func update(url: URL) {
        guard !isDismantled else { return }
        requestedURL = url
        schedulePendingPreview()
    }

    func dismantle() {
        isDismantled = true
        loadGeneration += 1
        requestedURL = nil
        lifecycle.markDetached()
        discardPreviewView()
    }

    override func viewWillMove(toWindow newWindow: NSWindow?) {
        super.viewWillMove(toWindow: newWindow)

        guard newWindow == nil, !isDismantled else { return }
        loadGeneration += 1
        lifecycle.markDetached()
        discardPreviewView()
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()

        guard !isDismantled else { return }
        if window == nil {
            loadGeneration += 1
            lifecycle.markDetached()
            discardPreviewView()
        } else {
            schedulePendingPreview()
        }
    }

    private func schedulePendingPreview() {
        guard window != nil, let requestedURL else { return }
        loadGeneration += 1
        let generation = loadGeneration

        DispatchQueue.main.async { [weak self] in
            self?.applyPendingPreview(generation: generation, requestedURL: requestedURL)
        }
    }

    private func applyPendingPreview(generation: Int, requestedURL: URL) {
        guard !isDismantled,
              generation == loadGeneration,
              window != nil,
              self.requestedURL == requestedURL,
              let previewView = ensurePreviewView(),
              previewView.superview === self else {
            return
        }

        switch lifecycle.decision(for: requestedURL) {
        case .skip:
            return
        case .load(let requiresFreshView):
            if requiresFreshView {
                discardPreviewView()
            }
            guard let previewView = ensurePreviewView() else { return }
            guard generation == loadGeneration,
                  window != nil,
                  previewView.superview === self else {
                return
            }
            previewView.previewItem = requestedURL as QLPreviewItem
            lifecycle.markLoaded(requestedURL)
        }
    }

    private func discardPreviewView() {
        if previewView?.previewItem != nil {
            previewView?.previewItem = nil
        }
        NSLayoutConstraint.deactivate(previewConstraints)
        previewConstraints = []
        previewView?.removeFromSuperview()
        previewView = nil
    }

    private func ensurePreviewView() -> QLPreviewView? {
        guard window != nil, !isDismantled else { return nil }
        if let previewView {
            return previewView
        }

        let view = Self.makePreviewView()
        previewView = view
        install(view)
        return view
    }

    private func install(_ previewView: QLPreviewView) {
        previewView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(previewView)
        previewConstraints = [
            previewView.leadingAnchor.constraint(equalTo: leadingAnchor),
            previewView.trailingAnchor.constraint(equalTo: trailingAnchor),
            previewView.topAnchor.constraint(equalTo: topAnchor),
            previewView.bottomAnchor.constraint(equalTo: bottomAnchor)
        ]
        NSLayoutConstraint.activate(previewConstraints)
    }

    private static func makePreviewView() -> QLPreviewView {
        let view = QLPreviewView()
        view.autostarts = true
        return view
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
            // 宽高既取不到、又没有缩略图可参考时，旧写法会画一个 16:9 的黑色播放器
            // —— 看起来像"视频坏了"，实际是我们读不到信息（审计 R-41）。
            switch VideoPreviewPlan.resolve(preview: preview) {
            case .player(let ratio):
                VideoPreview(url: preview.url, aspectRatio: ratio)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            case .informationUnavailable:
                videoInfoUnavailableView(preview.url)
            }
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
        ChineseSelectableTextView(text: content, font: .monospacedSystemFont(ofSize: 13, weight: .regular))
    }

    private func videoInfoUnavailableView(_ url: URL) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "questionable")
                .font(.system(size: 32))
                .foregroundStyle(.secondary)
            Text("无法读取这段视频的分辨率信息")
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
            Button("在 Finder 中显示") {
                NSWorkspace.shared.activateFileViewerSelecting([url])
            }
            .controlSize(.small)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
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
