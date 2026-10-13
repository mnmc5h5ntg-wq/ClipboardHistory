import AppKit
import SwiftUI

struct DetailView: View {
    @ObservedObject var historyStore: HistoryStore
    /// 窗口装饰的实测几何。详情区是 `.ignoresSafeArea(edges: .top)` 铺到窗口顶的，
    /// 所以它必须自己躲开左上角那三个按钮 —— 侧栏开着时看不出问题，一收起侧栏就压上了。
    @ObservedObject private var chrome: WindowChromeMetrics = .shared

    /// 详情区是"看"的地方，所以 Markdown 默认给渲染结果；那颗「原文」控件负责另一头。
    ///
    /// 它是**视图态**，不进 store、不进存档：换一条记录带着它走没问题，
    /// 但它绝不改 `HistoryStore` 里的任何一个字（C-5：Store 只减不加）。
    @State private var markdownMode: MarkdownPreviewMode
    /// 复制失败那一档的视图态（R5）。与 `copyConfirmed` 同族：不进 store、不进存档，
    /// 只负责"这一下按下去，界面上有一件事发生过"。
    @State private var copyFailed: Bool = false

    /// 「已复制」回执（M7）。复制成功以前没有任何反馈，只有行位置变化 ——
    /// 那是可用性缺口，不只是美观问题。
    @State private var copyConfirmed = false
    @State private var copyResetTask: Task<Void, Never>?

    init(historyStore: HistoryStore, initialMarkdownMode: MarkdownPreviewMode = .rendered) {
        self.historyStore = historyStore
        // 私有 @State 用注入参数的老手法（和 `SettingsView.initialCategory` 同一套）：
        // 离屏窗口建不出无障碍树，"点一下那颗控件"在夹具里做不到，
        // 而**没有夹具的两种状态就等于没有验收**。默认值不变，产品路径一行都没多。
        _markdownMode = State(initialValue: initialMarkdownMode)
    }

    var body: some View {
        // `Group` 是为了让下面那条 `.animation(value:)` 有地方挂：`body` 直接以 if/else 开头时，
        // 修饰符没有可依附的表达式（编译器报的是"instance member 'animation' cannot be used on type 'View'"）。
        // Group 不引入布局与尺寸变化。
        Group {
        if let entry = historyStore.selectedEntry {
            // R16：这一臂以前**没有**过渡，而下面那条 `.animation` 管的是"有没有选中"这个布尔 ——
            // 于是"空 ↔ 内容"只有半边在演，另一半是一帧硬切。
            // 更糟的是方向：删掉最后一条时内容**瞬间消失**，空态再从全透明淡进来，
            // 整块详情区空白约 160ms。那正是 D-055 砍掉 M4"整块淡入"的理由
            //（"淡入只能从全透明开始 ⇒ 一帧空白"）—— 当初那条反对的恰好是这里剩下的这个形状。
            // 两臂都挂同一档 ⇒ 才是真的交叉淡：旧的一直在，直到新的完全显形。
            // 注意这**不是**把 M4 翻回来：M4 反对的是"换选（A→B）整块淡"，
            // 那条仍然由下面按 `DetailPreviewKind` 供电的软交接管着（同类之间不演）。
            selectedEntryView(entry)
                .transition(MotionCatalog.transition(for: .contentFade))
        } else {
            EmptyStateView(
                systemName: "doc.on.clipboard",
                title: "选择一条记录查看详情",
                spacing: 16,
                imageSize: VisualGlyph.emptyPane,
                titleSize: VisualFont.body
            )
                .transition(MotionCatalog.transition(for: .contentFade))
        }
        }
        // 上面那条 `.transition` 以前**没有供电**：整块 `body` 上没有任何 `.animation(value:)`，
        // 唯一那条挂在 `selectedEntryView` 内部（键是"视图类型身份"），而 `entry == nil` 时
        // 那棵子树已经不存在了。于是"删完最后一条 / 选中一条空"这两次整块换人是一帧跳变，
        // 而代码里留着一行不会执行的过渡 —— 仓库对这一族的判据是"不执行的声明比没有更坏"。
        // 键只取"有没有选中"这一个布尔：换选（A→B）不该演，那是读字，不是找变化。
        .animation(MotionCatalog.animation(for: .contentFade),
                   value: historyStore.selectedEntry == nil)
    }

    private func selectedEntryView(_ entry: HistoryStore.Entry) -> some View {
        VStack(spacing: 0) {
            header(for: entry)
            Divider()
            preview(for: entry)
                .transition(MotionCatalog.transition(for: .contentFade))
        }
        // 详情区换页的两条规则，都是量出来的（动效审计 M4，账本 U-20 / D-055）：
        //
        // ① **换类型才软交接**。`.transition` 只在"这一支被插入/移除"时执行，
        //    所以文本→文本只是换字符串（不演），文本→图片是整块界面被换掉（交叉淡入）。
        //    这条区分是有依据的：同一类内容之间，用户要读的是**字**；换了类型，
        //    需要被解释的是"你看到的这块东西整个变了"。
        // ② 为什么是**交叉**淡入而不是"淡入新内容"：淡入只能从全透明开始，
        //    于是每次换选都有一帧空白详情；方向键连翻（key repeat ~30/s）时
        //    这一帧空白每按一次重来一遍，整块永远到不了不透明 —— 比不动画更差。
        //    交叉淡入没有那一帧：旧的一直在，直到新的完全显形。
        //    第一版实现的正是"整块淡入"，砍掉它的理由是上面那两条，**不是**"它没跑"——
        //    我一开始以为它没跑（本仓库那把整窗尺量出来是一帧跳变），
        //    报告 §13.5 的场景 A 用小区域亮度重量了一遍：亮度 0.423 → 0.007 再用 8 帧爬回去，
        //    动画确实在跑。同一次调用里"先裸赋值再 withAnimation"不会被合并掉。
        //    （尺子看不见 ≠ 事情没发生；这条已经写进 `MotionFilmstripTests` 的分带判据。）
        .animation(MotionCatalog.animation(for: .contentFade),
                   value: DetailPreviewKind(entry: entry, markdownMode: markdownMode))
        .onChange(of: entry.id) { _ in
            // 上一条留下的「已复制」回执必须收掉（否则"已复制"挂在另一条记录上，那是说谎）。
            clearCopyConfirmation(animated: false)
        }
        .onDisappear { copyResetTask?.cancel() }
        .ignoresSafeArea(edges: .top)
        .overlay(alignment: .bottomTrailing) {
            GlassPill(
                isFavorite: entry.isFavorite,
                favoriteAction: { historyStore.perform(.toggleFavorite(entry)) },
                isPinned: entry.isPinned,
                pinAction: { historyStore.perform(.togglePin(entry)) },
                copyConfirmed: copyConfirmed,
                copyFailed: copyFailed,
                copyAction: {
                    historyStore.perform(.copyAndPromote(entry))
                    confirmCopy()
                },
                deleteAction: { historyStore.perform(.delete(entry)) }
            )
            .padding(12)
        }
    }

    /// 复制回执。**成功与失败都要说话**（R5 补了失败那一半）：
    /// `copyAndPromote` 失败时会置 `clipboardWriteErrorMessage`，以前这里 `guard` 直接 return ——
    /// "不撒谎"做到了，"说实话"没做：图标回到原样、界面一句话都没说。
    /// （原注释声称"并弹顶部横幅"，实测**不成立**：全仓唯一那条横幅来自自动粘贴失败
    /// `ApplicationShell` 的 `pasteFailureNotice`，是另一条链路；而在这之前
    /// `clipboardWriteErrorMessage` 没有任何显示消费者，只有一个 guard 读取点。）
    /// （成功路径上 `writeToClipboard` 会把这条错误清成 nil，所以 nil 就是"这次成了"。）
    private func confirmCopy() {
        guard historyStore.clipboardWriteErrorMessage == nil else {
            showCopyFailure()
            return
        }
        copyResetTask?.cancel()
        withAnimation(MotionCatalog.animation(for: .emphasis)) { copyConfirmed = true }
        // 读屏用户拿不到那颗勾（MC-13）：播报的是同一句话，不是把视觉回执换个写法。
        VoiceOverReceipt.announce("已复制到剪贴板")
        copyResetTask = Task { @MainActor in
            // 1.1 秒：够读完"已复制"，又不至于让一颗勾长期占着按钮。
            try? await Task.sleep(nanoseconds: 1_100_000_000)
            guard !Task.isCancelled else { return }
            clearCopyConfirmation(animated: true)
        }
    }

    /// 失败位：与成功回执同一档（`.emphasis`）、同一个 1.1 秒、同一颗按钮，只是图标与人话换了。
    /// 读屏那一边**不许播"已复制"**（那正是这条要防的谎），改播失败；12/13 没有播报 API，
    /// 那一档只剩图标与 help 文案变化 —— 缺口照实写，不许当成已交付。
    private func showCopyFailure() {
        copyResetTask?.cancel()
        copyResetTask = nil
        copyConfirmed = false
        withAnimation(MotionCatalog.animation(for: .emphasis)) { copyFailed = true }
        VoiceOverReceipt.announce("复制失败，没能写进剪贴板")
        copyResetTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: 1_100_000_000)
            guard !Task.isCancelled else { return }
            withAnimation(MotionCatalog.animation(for: .emphasis)) { copyFailed = false }
        }
    }

    private func clearCopyConfirmation(animated: Bool) {
        copyResetTask?.cancel()
        copyResetTask = nil
        copyFailed = false
        guard copyConfirmed else { return }
        if animated {
            withAnimation(MotionCatalog.animation(for: .emphasis)) { copyConfirmed = false }
        } else {
            copyConfirmed = false
        }
    }

    private func header(for entry: HistoryStore.Entry) -> some View {
        // U-4：两行居中 meta → 一条左对齐，并且和正文**共用同一个可读列**。
        // 居中元信息的问题不是"不好看"，是它把时间、大小这类次要信息抬到了和正文同一视觉层级，
        // 而读者要先判断"这两行属于谁"；来源 App 以前干脆没在详情里露出（B-2 已经把它持久化了）。
        HStack(spacing: 0) {
            Spacer(minLength: 0)
            HStack(spacing: 8) {
                Text(DetailTypography.metaText(
                    copiedAt: ClipboardDateFormatters.detailTimestamp.string(from: entry.timestamp),
                    size: entry.content.sizeDescription,
                    sourceAppName: entry.sourceAppName
                ))
                .font(.system(size: DetailTypography.metaFontSize))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)

                Spacer(minLength: 8)

                // 控件只在"这条内容真的有两种看法"时出现。给一条图片或者纯文本
                // 摆一颗「原文」按钮，是让用户去点一个什么都不会发生的东西。
                if offersMarkdownRendering(for: entry) {
                    MarkdownModeButton(title: MarkdownPreviewMode.controlTitle(for: markdownMode)) {
                        markdownMode = markdownMode.toggled()
                    }
                }
            }
            // 左缘对齐靠的是"同一个列宽 + 同一个 gutter"，不是靠肉眼调 padding。
            // `columnWidth` 里的 gutter 与正文 `textContainerInset` 是同一个常数（见 DetailTypography）。
            .padding(.horizontal, DetailTypography.containerGutter)
            .frame(maxWidth: .infinity, alignment: .leading)
            .frame(maxWidth: DetailTypography.columnWidth())
            Spacer(minLength: 0)
        }
        // 顶部留白不是审美值，是**窗口装饰的实测几何**：这一行文字必须从交通灯带下方开始，
        // 否则侧栏一收起（详情列成了最左列）就会和关闭/最小化按钮叠在一起。
        // 数值由 `WindowChromeMetrics` 在每次重新摆放按钮时发布。
        .padding(.top, chrome.detailContentTopInset)
        .padding(.bottom, 10)
        .background(VisualMaterial.glass)
    }

    /// 这条记录到底有没有"渲染 / 原文"之分。
    ///
    /// 文件按**扩展名**判定（那是作者写下的意图，没有歧义）；文本条目按**内容信号**判定，
    /// 要两类以上不同语法同时出现才给入口（`MarkdownParsingPolicy.offersRendering` 记了阈值与理由：
    /// 单看一类的话 Python/Shell 的 `# 注释` 会被当成标题）。
    /// 两边默认都是渲染态 —— 但这一层只改**看法**：存档、搜索、"再次复制"走的仍是原始字节，
    /// 而顶部这颗控件就是退回原始字节的那一步。
    private func offersMarkdownRendering(for entry: HistoryStore.Entry) -> Bool {
        MarkdownRenderingAffordance.offers(for: entry.content)
    }

    /// 「原文 / 渲染」那颗控件。
    ///
    /// 放在头部那一行的右端而不是浮在正文上：正文区已经有一条 GlassPill（收藏/固定/复制/删除），
    /// 再叠一颗浮层就是两块会抢焦点的玻璃；而这一行本来就是"次要信息"的住处。
    /// 标题说"点下去会变成什么"，不说"现在是什么"（`MarkdownPreviewMode.controlTitle`）。
    private struct MarkdownModeButton: View {
        let title: String
        let action: () -> Void
        @State private var isHovered = false

        var body: some View {
            Button(action: action) {
                Text(title)
                    .font(.system(size: DetailTypography.metaFontSize))
                    // 动作不用弱化色：`.secondary` 在亮色帧上实测 4.10:1，够"次要信息"用，
                    // 不够一个**要点的东西**用（WCAG 1.4.3 对小字要求 4.5:1）。
                    // 这一档是全 App 的次要文字问题，单独记在 backlog，不在这里顺手改。
                    .foregroundStyle(.primary)
                    .padding(.horizontal, 6)
                    // 刻意**不加纵向 padding**：这颗控件的高度必须与 11pt 的 meta 文字同高，
                    // 否则"这条记录有没有第二种看法"会顺带改变头部高度，
                    // 换选一条 .md 与一条普通文本时下面的列表整块上下跳
                    // （实测过：加了 2pt 纵向 padding 之后，22/82 帧因为几何移动而变）。
                    // 悬停底色因此贴着字形那一行 —— 它本来就是个安静的行内动作，不是按钮区。
                    .background {
                        VisualShape.rounded(VisualRadius.chip)
                            .fill(.primary.opacity(isHovered ? VisualFill.hover : 0))
                    }
                    .contentShape(VisualShape.rounded(VisualRadius.chip))
            }
            .pressedStyle(in: VisualShape.rounded(VisualRadius.chip))
            .fixedSize()
            .helpLabel(MarkdownPreviewMode.controlHelp)
            .onHover { hovering in
                withAnimation(MotionCatalog.animation(for: .hover)) {
                    isHovered = hovering
                }
            }
        }
    }

    @ViewBuilder
    private func preview(for entry: HistoryStore.Entry) -> some View {
        switch entry.content {
        case .text(let text):
            // 正文限一个可读列（U-4）：以前它无限宽，700pt 的详情区一行能排 100+ 字符，
            // 而且带一条横向滚动条 —— 读长文本要来回扫视和横向滚动。
            // 列宽由字体推进推出来（68ch），字号一改列宽自己跟着改。
            if MarkdownRenderingAffordance.renders(text: text, in: markdownMode) {
                ChineseSelectableAttributedTextView(source: text,
                                                    highlightQuery: historyStore.searchText)
                    .frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)
                    .frame(maxWidth: .infinity, alignment: .center)
            } else {
                ChineseSelectableTextView(
                    text: text,
                    font: DetailTypography.bodyFont,
                    highlightQuery: historyStore.searchText
                )
                .frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)
                .frame(maxWidth: .infinity, alignment: .center)
            }
        case .image(let stored):
            ImagePreviewView(nsImage: stored.nsImage)
        case .file(let url):
            DetailFileView(url: url, thumbnail: entry.thumbnail, markdownMode: markdownMode)
        case .files(let urls):
            MultiFileDetailView(urls: urls, markdownMode: markdownMode)
        }
    }
}

private struct MultiFileDetailView: View {
    let urls: [URL]
    /// 与详情头部同一份视图态：多文件里展开的每条 `.md` 跟着一起切换。
    let markdownMode: MarkdownPreviewMode
    @State private var expandedURL: URL?

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 0, pinnedViews: []) {
                ForEach(Array(urls.enumerated()), id: \.offset) { _, url in
                    VStack(spacing: 0) {
                        MultiFileRow(
                            url: url,
                            isExpanded: expandedURL == url,
                            symbol: symbol(for: url),
                            action: { toggle(url) }
                        )

                        CollapsibleFilePreview(url: url, isExpanded: expandedURL == url) {
                            DetailFileView(url: url, thumbnail: nil, markdownMode: markdownMode)
                        }
                    }
                    .clipped()
                    .animation(MultiFilePreviewLayout.animation, value: expandedURL)

                    Divider()
                        .padding(.leading, 48)
                }
            }
            .padding(.vertical, 8)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func toggle(_ url: URL) {
        withAnimation(MultiFilePreviewLayout.animation) {
            expandedURL = expandedURL == url ? nil : url
        }
    }

    private func symbol(for url: URL) -> String {
        let fileExtension = url.pathExtension.lowercased()
        if FileTypeSupport.imageExtensions.contains(fileExtension) {
            return "photo"
        }
        if FileTypeSupport.videoExtensions.contains(fileExtension) {
            return "play.rectangle"
        }
        if FileTypeSupport.textExtensions.contains(fileExtension) {
            return "doc.text"
        }
        return "doc"
    }
}

enum MultiFilePreviewLayout {
    static let minimumPreviewHeight: CGFloat = 120
    static let fallbackPreviewHeight: CGFloat = 260
    static let fallbackCompactPreviewHeight: CGFloat = 190
    static let maximumPreviewHeight: CGFloat = 420
    static let previewOuterHorizontalPadding: CGFloat = 40
    static let previewInnerPadding: CGFloat = 40
    static let textLineHeight: CGFloat = 17
    static let textSampleLimit = 32_000
    static let collapsedScale: CGFloat = 0.97
    static let animationDuration = 0.22

    static var animation: Animation {
        animation(reduceMotion: MotionCatalog.motionShouldBeReduced)
    }

    /// 纯函数版：`accessibilityDisplayShouldReduceMotion` 是系统全局状态，测试改不了，
    /// 所以把判断留在这里、把取值做成参数，才有办法被断言（审计 UI 量化检查 5）。
    static func animation(reduceMotion: Bool) -> Animation {
        // 「减弱动态效果」开启时，展开/收起与高度变化直接跳到终态。
        // 只掐会改变位置或尺寸的动画；0.11–0.14s 的颜色/透明度渐变保留，
        // 那类不是前庭刺激源，去掉只会让界面显得迟钝。
        if reduceMotion { return .linear(duration: 0) }
        if #available(macOS 14, *) {
            return .snappy(duration: animationDuration, extraBounce: 0)
        }
        return .interactiveSpring(response: animationDuration, dampingFraction: 0.88, blendDuration: 0.02)
    }

    /// 收起态的缩放同样属于"会动的"那一类：减弱动态时保持原尺寸。
    static func collapsedScale(reduceMotion: Bool) -> CGFloat {
        reduceMotion ? 1 : collapsedScale
    }

    static func preferredHeight(for url: URL, availableWidth: CGFloat) -> CGFloat {
        let fileExtension = url.pathExtension.lowercased()

        if FileTypeSupport.textExtensions.contains(fileExtension),
           let textHeight = preferredTextHeight(for: url, availableWidth: availableWidth) {
            return clamp(textHeight)
        }

        if FileTypeSupport.imageExtensions.contains(fileExtension),
           let imageHeight = preferredImageHeight(for: url, availableWidth: availableWidth) {
            return clamp(imageHeight)
        }

        if FileTypeSupport.videoExtensions.contains(fileExtension) {
            return preferredVideoHeight(for: url, availableWidth: availableWidth)
        }

        if FileTypeSupport.documentExtensions.contains(fileExtension) {
            return clamp(fallbackPreviewHeight)
        }

        return clamp(fallbackCompactPreviewHeight)
    }

    private static func preferredTextHeight(for url: URL, availableWidth: CGFloat) -> CGFloat? {
        guard let handle = try? FileHandle(forReadingFrom: url) else { return nil }
        defer { try? handle.close() }

        guard let data = try? handle.read(upToCount: textSampleLimit),
              !data.isEmpty,
              let text = String(data: data, encoding: .utf8) else {
            return nil
        }

        let textWidth = max(
            availableWidth - previewOuterHorizontalPadding - previewInnerPadding,
            120
        )
        let charactersPerLine = max(Int(textWidth / 7.6), 16)
        let wrappedLineCount = text.components(separatedBy: .newlines).reduce(0) { total, line in
            total + max(Int(ceil(Double(line.count) / Double(charactersPerLine))), 1)
        }
        let fileSize = (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? NSNumber)?.doubleValue ?? Double(data.count)
        let sampleCoverage = min(max(fileSize / Double(max(data.count, 1)), 1), 3)
        let estimatedLineCount = min(CGFloat(wrappedLineCount) * CGFloat(sampleCoverage), 24)

        return estimatedLineCount * textLineHeight + previewInnerPadding
    }

    private static func preferredImageHeight(for url: URL, availableWidth: CGFloat) -> CGFloat? {
        // 旧写法 `NSImage(contentsOf:)` 会把整张图解码进内存，仅仅为了拿宽高。
        guard let size = ImageProperties.pixelSize(of: url), size.width > 0, size.height > 0 else { return nil }

        let widthLimit = max(availableWidth - previewOuterHorizontalPadding - previewInnerPadding, 100)
        let displayWidth = min(widthLimit, size.width)
        return displayWidth * (size.height / size.width) + previewInnerPadding
    }

    private static func preferredVideoHeight(for url: URL, availableWidth: CGFloat) -> CGFloat {
        let aspectRatio = VideoAspectRatioResolver.aspectRatio(for: url)
            ?? VideoAspectRatioResolver.fallbackAspectRatio
        let widthLimit = max(availableWidth - previewOuterHorizontalPadding, 140)
        let controlsAndPadding: CGFloat = 76
        return clamp(widthLimit / max(aspectRatio, 0.1) + controlsAndPadding)
    }

    private static func clamp(_ height: CGFloat) -> CGFloat {
        min(max(height, minimumPreviewHeight), maximumPreviewHeight)
    }
}

private struct CollapsibleFilePreview<Content: View>: View {
    let url: URL
    let isExpanded: Bool
    @ViewBuilder let content: () -> Content
    @State private var targetHeight = MultiFilePreviewLayout.fallbackPreviewHeight
    @State private var keepsContentMounted = false
    @State private var mountGeneration = 0
    @State private var availableWidth: CGFloat = 0

    var body: some View {
        VStack(spacing: 0) {
            widthReader

            if isExpanded || keepsContentMounted {
                content()
                    .frame(maxWidth: .infinity)
                    .frame(height: targetHeight, alignment: .top)
                    .clipShape(VisualShape.rounded(VisualRadius.card))
                    .clipped()
                    .scaleEffect(
                        isExpanded ? 1 : MultiFilePreviewLayout.collapsedScale(
                            reduceMotion: MotionCatalog.motionShouldBeReduced
                        ),
                        anchor: .top
                    )
                    .frame(height: isExpanded ? targetHeight : 0, alignment: .top)
                    .clipped()
                    .allowsHitTesting(isExpanded)
                    .padding(.horizontal, 20)
                    .padding(.bottom, isExpanded ? 12 : 0)
            }
        }
        .animation(MultiFilePreviewLayout.animation, value: isExpanded)
        .animation(MultiFilePreviewLayout.animation, value: targetHeight)
        .onAppear {
            keepsContentMounted = isExpanded
        }
        .onChange(of: isExpanded) { expanded in
            mountGeneration += 1
            let generation = mountGeneration
            if expanded {
                keepsContentMounted = true
                recalculateTargetHeight()
            } else {
                DispatchQueue.main.asyncAfter(deadline: .now() + MultiFilePreviewLayout.animationDuration) {
                    if generation == mountGeneration, !isExpanded {
                        keepsContentMounted = false
                    }
                }
            }
        }
    }

    private var widthReader: some View {
        GeometryReader { proxy in
            Color.clear
                .preference(key: PreviewWidthPreferenceKey.self, value: proxy.size.width)
        }
        .frame(height: 0)
        .onPreferenceChange(PreviewWidthPreferenceKey.self) { width in
            guard width.isFinite, width > 0 else { return }
            availableWidth = width
            recalculateTargetHeight()
        }
    }

    private func recalculateTargetHeight() {
        guard isExpanded || keepsContentMounted, availableWidth > 0 else { return }
        targetHeight = MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: availableWidth)
    }
}

private struct PreviewWidthPreferenceKey: PreferenceKey {
    static let defaultValue: CGFloat = 0

    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = max(value, nextValue())
    }
}

private struct MultiFileRow: View {
    let url: URL
    let isExpanded: Bool
    let symbol: String
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                // 一个符号 + 旋转，而不是 `chevron.down` ↔ `chevron.right` 换名字（R6 / 审计 B-P2）。
                // 换名字是**一帧硬换**，而它旁边的内容正在用 0.22s 展开 —— 箭头先落地、内容还在路上，
                // 读起来就是"对不上"。旋转挂在**同一条**揭示曲线上，两者天然同步
                // （`MultiFilePreviewLayout.animation` 自己已经管 reduce-motion）。
                Image(systemName: "chevron.right")
                    .font(.system(size: VisualGlyph.badge, weight: .semibold))
                    // 静置至少 `.secondary`（R21）：这一颗是**整行唯一的"我可以展开"的记号**，
                    // 而 `.tertiary` 在详情区那块纯白底上实测 **亮 1.88 / 暗 2.27**（地板 3.0），
                    // 同一行旁边那个 `.secondary` 的类型图标是 3.95 / 5.9 ——
                    // 也就是说"能点"这件事一直比"这是什么类型"更弱，方向正好反了。
                    // 它同时还踩着 `VisualGlyph.badge` 的 10pt 下限，两样都弱就叠成了"看不见"。
                    .foregroundStyle(VisualInk.control)
                    .rotationEffect(.degrees(isExpanded ? 90 : 0))
                    .animation(MultiFilePreviewLayout.animation, value: isExpanded)
                    .frame(width: 12)

                Image(systemName: symbol)
                    .font(.system(size: VisualGlyph.rowIcon))
                    .foregroundStyle(.secondary)
                    .frame(width: 18)

                VStack(alignment: .leading, spacing: 2) {
                    Text(url.lastPathComponent)
                        .font(.system(size: VisualFont.body))
                        .lineLimit(1)
                        .truncationMode(.middle)
                    // 只显示上一级目录名（"…/Downloads"），不再把完整绝对路径
                    // 摊在界面上：屏幕共享/截屏时这是泄露点（审计 R-43）
                    Text(url.parentDirectoryLabel)
                        .font(.system(size: VisualFont.meta))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background {
                VisualShape.rounded(VisualRadius.card)
                    .fill(.primary.opacity(isHovered ? VisualFill.hover : 0))
            }
            .overlay {
                VisualShape.rounded(VisualRadius.card)
                    .strokeBorder(.primary.opacity(isHovered ? VisualTint.hoverStroke : 0),
                                  lineWidth: VisualHairline.rule)
            }
            .contentShape(VisualShape.rounded(VisualRadius.card))
        }
        // 整行类：`scales: false`。行的主反馈是选中与底色，缩放一条铺满的行会读成"布局抖了一下"。
        .pressedStyle(in: VisualShape.rounded(VisualRadius.card), scales: false)
        .padding(.horizontal, 20)
        .padding(.vertical, 3)
        .onHover { hovering in
            withAnimation(MotionCatalog.animation(for: .hover)) {
                isHovered = hovering
            }
        }
    }
}
