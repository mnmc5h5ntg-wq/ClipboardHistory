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

/// 详情预览的加载兜底（审计第二轮 R2-09：`MediaLoader` 不返回时 spinner 会永远转下去）。
/// 纯值类型，方便单测；界面侧只负责计时与改状态。
enum PreviewLoadTimeoutPolicy {
    /// 8 秒：QuickLook/AVFoundation 对网络卷或损坏文件可能长时间不返回，
    /// 而本地正常文件的预览都在 1 秒内出结果，8 秒足够宽又不会让用户干等。
    static let timeoutSeconds: UInt64 = 8

    static let timeoutNanoseconds: UInt64 = timeoutSeconds * 1_000_000_000

    /// 只有"仍是同一次加载"且"还在等"时才允许放弃：
    /// 否则一个陈旧超时会把用户已经切到的下一条预览的结果覆盖掉。
    static func shouldGiveUp(stillWaiting: Bool, isCurrentLoad: Bool) -> Bool {
        stillWaiting && isCurrentLoad
    }

    static func failureMessage(timeoutSeconds: UInt64 = Self.timeoutSeconds) -> String {
        "预览加载超过 \(timeoutSeconds) 秒仍未返回，已停止等待。"
    }
}

/// 详情区的**加载态**那一块（动效审计 M9 / R26）。
///
/// 为什么从 `DetailFileView.loadingView` 提成一个具名视图：这块表面**从来没有进过帧基线**
/// —— 它是异步的，夹具要拍到它就得赌"拍的那一瞬间还没加载完"，
/// 而按墙钟判的夹具每天会给出不同的答案（R22 记过"夹具自检不许判跑测试的那一刻"）。
/// 提出来之后它可以被**确定地**画一次：`detail-loading` 那张帧从此长驻基线，
/// 全 App 唯一那块常驻动效第一次有像素可审。
///
/// 理由不是"扫光更时髦"：spinner 说的是"我在等"，骨架说的是"内容马上来"，
/// 同一段等待里后者把注意力放到即将出现的东西上（报告 §3 那行给的就是这个差别）。
/// 那一句人话留着 —— 报告 §5 红线 2 要的是"只在加载态挂上、离开就停"，
/// 而这块视图正是被 `.loading` 分支独占的，超时 8 秒后换成失败态，循环随之消失。
struct DetailLoadingView: View {
    /// 注入点（与 `SkeletonPreviewView.reduceMotion` 同一个理由）：**帧基线要的是可重复的像素**，
    /// 而扫光的相位由墙钟驱动 —— 不钉住它，同一份代码两次拍出来的帧就不一样，
    /// `frame_baseline` 的 sha 会每天自己变（R18 立的"帧名=帧的尺寸=帧的内容"从此守不住）。
    /// 所以这张帧拍的是**减弱动态那一档**的样子：条带、宽度、间距、那一句人话全都在，
    /// 唯一不在的是带子的位置 —— 而那正是 `testSkeletonSweepActuallySweeps` 用胶片去量的东西。
    /// ⇒ 静止帧管"长什么样"，胶片管"动不动"，两条各判各的，不许互相冒充。
    var reduceMotion: Bool = MotionCatalog.motionShouldBeReduced

    var body: some View {
        // **那一句人话与条带共用一条左轴**（R26 / U-48）。
        //
        // 以前这个 `VStack` 用的是默认的 `.center`：三根条带自己顶到左边缘，
        // 而"正在加载预览…"落在整块面板的水平中线上 —— 同一块 74pt 高的面板里两条对齐轴，
        // 句子读起来不像"这三根条带在说什么"，而像"这块区域有个状态要说"，
        // 于是它的视线权重反而高于本该是主角的条带。骨架说的是"内容马上来"，
        // 那一句就该贴在它指的那块内容上。
        //
        // 判据是像素：`detail-loading` 帧里条带的最左有墨列 与 句子的最左有墨列 必须同轴（≤2pt）。
        VStack(alignment: .leading, spacing: 14) {
            SkeletonPreviewView(reduceMotion: reduceMotion)
                .frame(height: 44)
            Text("正在加载预览…")
                .font(.system(size: StatePresentation.messageFontSize))
                // R398：加载态整块面板也只有这句话；`.secondary` 在亮档实测 2.86:1，
                // 低于 AA 正文线 4.5 ⇒ 走 pane 墨档（与空态同一来源）。
                .foregroundStyle(StatePresentation.paneMessageInkStyle)
            Spacer(minLength: 0)
        }
        // 左右内缩取**详情栏那一条现成的轴**，不是新造一个数：
        // `DetailTypography.containerGutter` 的注释写的就是同一件事
        // —— "meta 行和正文不同左缘"这种缺陷在帧上一眼能看见、在代码里看不出来。
        // 加载块是那块内容的替身，它必须站在同一列上（R26 / U-48，判据是像素：
        // `detail-loading` 里条带与句子的最左有墨列，必须等于 `detail-2-file` 里头部的最左有墨列）。
        .padding(.horizontal, DetailTypography.containerGutter)
        .padding(.top, 24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}

struct DetailFileView: View {
    let url: URL
    let thumbnail: StoredImage?
    /// 详情头部那颗「原文 / 渲染」的当前值。
    /// 由 `DetailView` 传下来而不是在这里自己存一份：多文件展开时每条都走这个视图，
    /// 各存一份就会各切各的 —— 那正是 D-1 那一轮在侧栏上栽过的"两套选中语言"的同族问题。
    let markdownMode: MarkdownPreviewMode
    /// **只给帧基线用的注入点**（R211 / BACKLOG 233）：把预览冻在 `.loading` 那一格，
    /// 于是"头部 + 分隔线 + 骨架"这张**组合**帧可以被确定地拍一次。
    ///
    /// 为什么要有它：`detail-loading` 那张帧画的是 `DetailLoadingView` 一个视图，
    /// 所以它只能回答"这块骨架长什么样"，回答不了"它在真实详情区里长什么样"——
    /// 我看图时正是因此说错过一句"加载时头部消失了"（D-206 记的就是这个机制）。
    /// 而旧写法要拍组合态就得赌"拍的那一瞬间还没加载完"，那是按墙钟判的夹具（R22 禁止）。
    ///
    /// 默认 `false` ⇒ 产品路径一行都不变：真实调用永远照常走 `loadPreview()`。
    /// **注意：这条默认值今天没有守卫**（注释里曾声称有 `DetailPreviewCaptureSeamTests`，那支测试不存在 ⇒ 假话已删）。
    /// 补那格守卫记在 BACKLOG 236；在补上之前，"默认关闭"只有源码可读、没有证人。
    var freezeLoadingForCapture: Bool   // 默认值只有**一处**：init 的参数默认（两处默认会让刀打空）
    @State private var previewState: MediaLoadingState<FilePreview> = .loading
    @State private var loadingHandle: MediaLoadHandle?
    @State private var loadGeneration = 0
    @State private var timeoutTask: Task<Void, Never>?

    init(url: URL, thumbnail: StoredImage?, markdownMode: MarkdownPreviewMode = .rendered,
         freezeLoadingForCapture: Bool = false) {
        self.url = url
        self.thumbnail = thumbnail
        self.markdownMode = markdownMode
        self.freezeLoadingForCapture = freezeLoadingForCapture
    }

    var body: some View {
        Group {
            switch previewState {
            case .loading:
                DetailLoadingView()
                    .transition(MotionCatalog.transition(for: .contentFade))
            case .success(let preview):
                previewView(preview)
                    .transition(MotionCatalog.transition(for: .contentFade))
            case .failure(let message):
                failureView(message)
                    .transition(MotionCatalog.transition(for: .contentFade))
            }
        }
        // 三态之间软交接（R6 / 审计 B-P1-1）。以前这里**一条动画都没有**：
        // 骨架"啪"地换成图片、8 秒后"啪"地换成警告。同一族"声明在、屏幕不在"，
        // 而这一处比详情换类型更该演 —— 用户正盯着这块等它出结果。
        //
        // 键只取**阶段**（0/1/2），不取 `previewState`（`FilePreview` 不是 Equatable，
        // 也压根不该整值比较：图片数据不同不该再演一次），也不取 `url`
        // （换一条记录时阶段会 1→0→1，那是"又在加载"的证据，本身不需要额外过渡）。
        .animation(MotionCatalog.animation(for: .contentFade), value: previewStage)
        .task(id: url) {
            // 夹具那一格：停在 `.loading`，不去取文件（R211 / BACKLOG 233）。
            // 决定本身是纯函数 `MediaLoadingPlan.startsLoad(...)`，证人写在 `MediaLoadingPlanTests`：
            // 默认值 ⇒ 真去加载，只有夹具显式传 true 才冻结。产品路径上这一行等于没有。
            guard MediaLoadingPlan.startsLoad(freezeLoadingForCapture: freezeLoadingForCapture) else { return }
            await loadPreview()
        }
        .onDisappear {
            loadingHandle?.cancel()
            loadingHandle = nil
            timeoutTask?.cancel()
            timeoutTask = nil
        }
    }

    /// 预览处在哪个阶段：0 加载 / 1 成功 / 2 失败。上面那条按值动画的键。
    private var previewStage: Int {
        switch previewState {
        case .loading: return 0
        case .success: return 1
        case .failure: return 2
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

    private func failureView(_ message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: VisualGlyph.state))
                .foregroundStyle(.secondary)
            Text(message)
                .font(.system(size: StatePresentation.messageFontSize))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @ViewBuilder
    private func textPreview(_ content: String) -> some View {
        // Markdown **文件**走渲染（扩展名就是作者的意图，没有歧义所以默认给渲染结果），
        // 并且和详情正文共用同一个可读列：切到「原文」时列宽不动，只有排版变。
        // 其它文本文件保持原来的等宽显示 —— 那是代码和日志，本来就要数着字符看。
        // R335：`.html` / `.htm` 以前落在最后那一支（等宽显示源码）—— 也就是**没有预览**。
        // 现在它与 Markdown 走同一块属性串视图，只是渲染器不同；等宽那一支留给代码与日志。
        let decision = DetailRenderPolicy.decide(fileContent: content, url: url)
        if markdownMode == .rendered, let (renderer, source) = decision.resolved() {
            ChineseSelectableAttributedTextView(source: source, renderer: renderer,
                                                resetKey: url)
                .frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)
                .frame(maxWidth: .infinity, alignment: .center)
        } else {
            // R460：纯文本文件也是正文，按**它自己的 13pt 字体**算 68ch 可读列
            // （U-4 当年漏了这条支路；直接套 14pt 的列会让 13pt 的一行排到 ~83ch）。
            let fileFont = NSFont.monospacedSystemFont(ofSize: 13, weight: .regular)
            ChineseSelectableTextView(text: content,
                                      font: .monospacedSystemFont(ofSize: 13, weight: .regular),
                                      resetKey: url)
                .frame(maxWidth: DetailTypography.columnWidth(font: fileFont), alignment: .leading)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func videoInfoUnavailableView(_ url: URL) -> some View {
        VStack(spacing: 12) {
            // `"questionable"` 不是合法的 SF Symbol 名字，SwiftUI 会画一个**空白图标**
            // （审计第二轮 R2-09 / 1.3）。这类错误编译期不报，所以有一道扫描式守卫：
            // `SystemSymbolValidityTests` 会把产品源码里所有 systemName 字面量拿去问 NSImage。
            Image(systemName: "questionmark.circle")
                .font(.system(size: VisualGlyph.state))
                .foregroundStyle(.secondary)
            Text("无法读取这段视频的分辨率信息")
                .font(.system(size: StatePresentation.messageFontSize))
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
                    .font(.system(size: VisualGlyph.placeholder))
                    .foregroundStyle(.quaternary)
            }
            Text(preview.url.lastPathComponent)
                .font(.system(size: VisualFont.title))
                // R462：长文件名不再从窗格左/右缘跑出去（也不再压右下角浮层）。
                .lineLimit(2)
                .multilineTextAlignment(.center)
                .truncationMode(.middle)
                .padding(.horizontal, 80)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @MainActor
    private func loadPreview() async {
        loadingHandle?.cancel()
        timeoutTask?.cancel()
        previewState = .loading
        loadGeneration += 1
        let generation = loadGeneration

        let handle = MediaLoader.loadFilePreviewHandle(url: url, thumbnail: thumbnail)
        loadingHandle = handle

        // 兜底：MediaLoader 对网络卷/损坏文件可能永远不返回，而旧实现只有一个转不完的 spinner。
        timeoutTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: PreviewLoadTimeoutPolicy.timeoutNanoseconds)
            guard !Task.isCancelled else { return }
            guard PreviewLoadTimeoutPolicy.shouldGiveUp(
                stillWaiting: loadingHandle != nil,
                isCurrentLoad: generation == loadGeneration
            ) else { return }
            loadingHandle?.cancel()
            loadingHandle = nil
            previewState = .failure(PreviewLoadTimeoutPolicy.failureMessage())
        }

        let result = await handle.value
        timeoutTask?.cancel()
        timeoutTask = nil
        guard !Task.isCancelled, generation == loadGeneration else { return }
        previewState = result
        loadingHandle = nil
    }
}
