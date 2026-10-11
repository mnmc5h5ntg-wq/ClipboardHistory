import AppKit
import SwiftUI

struct DetailView: View {
    @ObservedObject var historyStore: HistoryStore

    /// 详情区是"看"的地方，所以 Markdown 默认给渲染结果；那颗「原文」控件负责另一头。
    ///
    /// 它是**视图态**，不进 store、不进存档：换一条记录带着它走没问题，
    /// 但它绝不改 `HistoryStore` 里的任何一个字（C-5：Store 只减不加）。
    @State private var markdownMode: MarkdownPreviewMode

    init(historyStore: HistoryStore, initialMarkdownMode: MarkdownPreviewMode = .rendered) {
        self.historyStore = historyStore
        // 私有 @State 用注入参数的老手法（和 `SettingsView.initialCategory` 同一套）：
        // 离屏窗口建不出无障碍树，"点一下那颗控件"在夹具里做不到，
        // 而**没有夹具的两种状态就等于没有验收**。默认值不变，产品路径一行都没多。
        _markdownMode = State(initialValue: initialMarkdownMode)
    }

    var body: some View {
        if let entry = historyStore.selectedEntry {
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

    private func selectedEntryView(_ entry: HistoryStore.Entry) -> some View {
        VStack(spacing: 0) {
            header(for: entry)
            Divider()
            preview(for: entry)
        }
        .ignoresSafeArea(edges: .top)
        .overlay(alignment: .bottomTrailing) {
            GlassPill(
                isFavorite: entry.isFavorite,
                favoriteAction: { historyStore.perform(.toggleFavorite(entry)) },
                isPinned: entry.isPinned,
                pinAction: { historyStore.perform(.togglePin(entry)) },
                copyAction: { historyStore.perform(.copyAndPromote(entry)) },
                deleteAction: { historyStore.perform(.delete(entry)) }
            )
            .padding(12)
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
        .padding(.vertical, 10)
        .background(.ultraThinMaterial)
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
                    .padding(.vertical, 2)
                    .background {
                        RoundedRectangle(cornerRadius: 5, style: .continuous)
                            .fill(.primary.opacity(isHovered ? 0.07 : 0))
                    }
                    .contentShape(RoundedRectangle(cornerRadius: 5, style: .continuous))
            }
            .buttonStyle(.plain)
            .fixedSize()
            .helpLabel(MarkdownPreviewMode.controlHelp)
            .onHover { hovering in
                withAnimation(.easeInOut(duration: 0.14)) {
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
        animation(reduceMotion: NSWorkspace.shared.accessibilityDisplayShouldReduceMotion)
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
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                    .clipped()
                    .scaleEffect(
                        isExpanded ? 1 : MultiFilePreviewLayout.collapsedScale(
                            reduceMotion: NSWorkspace.shared.accessibilityDisplayShouldReduceMotion
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
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(.tertiary)
                    .frame(width: 12)

                Image(systemName: symbol)
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                    .frame(width: 18)

                VStack(alignment: .leading, spacing: 2) {
                    Text(url.lastPathComponent)
                        .font(.system(size: 13))
                        .lineLimit(1)
                        .truncationMode(.middle)
                    // 只显示上一级目录名（"…/Downloads"），不再把完整绝对路径
                    // 摊在界面上：屏幕共享/截屏时这是泄露点（审计 R-43）
                    Text(url.parentDirectoryLabel)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(.primary.opacity(isHovered ? 0.06 : 0))
            }
            .overlay {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .strokeBorder(.primary.opacity(isHovered ? 0.07 : 0), lineWidth: 0.7)
            }
            .contentShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 20)
        .padding(.vertical, 3)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.14)) {
                isHovered = hovering
            }
        }
    }
}
