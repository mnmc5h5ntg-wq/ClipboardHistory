import SwiftUI
import AppKit

enum SettingsViewLayout {
    static let windowContentSize = CGSize(width: 720, height: 540)
    static let minimumWindowSize = CGSize(width: 640, height: 440)
    static let sidebarWidth: CGFloat = 148
    static let clearButtonTitle = "清空"
}

enum SettingsCategory: String, CaseIterable, Identifiable {
    case shortcuts
    case general
    case privacy
    case recommendations
    case data

    var id: String { rawValue }

    var title: String {
        switch self {
        case .shortcuts: return "快捷键"
        case .general: return "通用"
        case .privacy: return "隐私"
        case .recommendations: return "推荐"
        case .data: return "数据"
        }
    }

    var icon: String {
        switch self {
        case .shortcuts: return "command"
        case .general: return "gearshape"
        case .privacy: return "hand.raised"
        case .recommendations: return "sparkles"
        case .data: return "folder"
        }
    }
}

struct SettingsView: View {
    @ObservedObject private var showMainWindowHotKeySettings: HotKeySettings
    private let feedbackStore: RecommendationFeedbackStore
    @ObservedObject private var repeatCopyHotKeySettings: HotKeySettings
    @ObservedObject private var loginItemSettings: LoginItemSettings
    @State private var showMainWindowShortcut: HotKeyShortcut
    @State private var repeatCopyShortcut: HotKeyShortcut
    @State private var launchAtLogin: Bool
    @State private var showClearHistoryConfirmation = false
    @State private var exportMessage: String?
    @State private var showExportAlert = false
    @ObservedObject private var contextPreferences: ContextPreferenceSettings
    @ObservedObject private var weightsStore: RecommendationWeightsStore
    private let clearHistoryAction: (() -> Void)?
    @State private var selectedCategory: SettingsCategory?

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        weightsStore: RecommendationWeightsStore = RecommendationWeightsStore(),
        feedbackStore: RecommendationFeedbackStore = RecommendationFeedbackStore(),
        clearHistoryAction: (() -> Void)? = nil,
        initialCategory: SettingsCategory? = .shortcuts
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
        self.loginItemSettings = loginItemSettings
        self.contextPreferences = contextPreferences
        self.weightsStore = weightsStore
        self.feedbackStore = feedbackStore
        self.clearHistoryAction = clearHistoryAction
        _showMainWindowShortcut = State(initialValue: showMainWindowHotKeySettings.shortcut)
        _repeatCopyShortcut = State(initialValue: repeatCopyHotKeySettings.shortcut)
        _launchAtLogin = State(initialValue: loginItemSettings.isEnabled)
        // 默认值与改动前的字面量初值一致：调用方不传就是"快捷键"页。
        // 存在的唯一理由：离屏窗口的无障碍树不会被 SwiftUI 建立，
        // 视觉验收没法用点击切分类，只能让初值可注入（见 AGENT_UI_AUDIT.md）。
        _selectedCategory = State(initialValue: initialCategory)
    }

    private func exportFeedbackData() {
        // 失败必须可见：旧实现写盘失败也返回 URL，界面照样显示"已导出"。
        do {
            let url = try feedbackStore.exportToFile()
            exportMessage = "已导出：\(url.lastPathComponent)"
            NSWorkspace.shared.activateFileViewerSelecting([url])
        } catch RecommendationFeedbackStore.ExportError.noData {
            exportMessage = "暂无反馈数据可导出"
        } catch {
            exportMessage = "导出失败：\(error.localizedDescription)"
        }
        showExportAlert = true
    }

    var body: some View {
        settingsContent
            .frame(minWidth: SettingsViewLayout.minimumWindowSize.width,
                   minHeight: SettingsViewLayout.minimumWindowSize.height)
            .onAppear {
                loginItemSettings.refresh()
                launchAtLogin = loginItemSettings.isEnabled
            }
            .onChange(of: showMainWindowShortcut) { newValue in
                saveShowMainWindowShortcut(newValue)
            }
            .onChange(of: showMainWindowHotKeySettings.shortcut) { newValue in
                showMainWindowShortcut = newValue
            }
            .onChange(of: repeatCopyShortcut) { newValue in
                saveRepeatCopyShortcut(newValue)
            }
            .onChange(of: repeatCopyHotKeySettings.shortcut) { newValue in
                repeatCopyShortcut = newValue
            }
            .onChange(of: launchAtLogin) { newValue in
                saveLaunchAtLogin(newValue)
            }
            .onChange(of: loginItemSettings.isEnabled) { newValue in
                launchAtLogin = newValue
            }
            .alert("清空未收藏记录", isPresented: $showClearHistoryConfirmation) {
                Button("取消", role: .cancel) {}
                Button("清空", role: .destructive) {
                    clearHistoryAction?()
                }
            } message: {
                Text("收藏记录会保留，其余历史会被清空。")
            }
    }

    @ViewBuilder
    private var settingsContent: some View {
        if #available(macOS 13, *) {
            NavigationSplitView {
                SettingsSidebarView(selectedCategory: $selectedCategory)
                    .navigationSplitViewColumnWidth(min: SettingsViewLayout.sidebarWidth,
                                                      ideal: SettingsViewLayout.sidebarWidth,
                                                      max: 180)
            } detail: {
                detailScrollView
            }
        } else {
            CompatibleSplitView(
                sidebarMinWidth: SettingsViewLayout.sidebarWidth,
                sidebarIdealWidth: SettingsViewLayout.sidebarWidth
            ) {
                SettingsSidebarView(selectedCategory: $selectedCategory)
            } detail: {
                detailScrollView
            }
        }
    }

    private var detailScrollView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                switch selectedCategory {
                case .shortcuts:
                    shortcutsSection
                case .general:
                    generalSection
                case .privacy:
                    privacySection
                case .recommendations:
                    recommendationsSection
                case .data:
                    dataSection
                case .none:
                    EmptyView()
                }
            }
            .padding(24)
        }
    }

    // MARK: - Shortcuts Section

    private var shortcutsSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("快捷键")
                .font(.headline)

            GroupBox {
                VStack(spacing: 12) {
                    HotKeySettingsRow(
                        settings: showMainWindowHotKeySettings,
                        shortcut: $showMainWindowShortcut
                    )

                    Divider()

                    HotKeySettingsRow(
                        settings: repeatCopyHotKeySettings,
                        shortcut: $repeatCopyShortcut
                    )
                }
            }
        }
    }

    // MARK: - General Section

    private var generalSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("通用")
                .font(.headline)

            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Toggle("开机启动", isOn: $launchAtLogin)
                        .disabled(!loginItemSettings.isSupported)

                    if let message = loginItemSettings.message {
                        Text(message)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 4)
            }
            // 清空历史只在「数据」页出现一次：同一个破坏性按钮在两个分类里
            // 各放一份，用户无法判断是不是两件事，两份实现还会各自漂移。
        }
    }

    // MARK: - Privacy Section

    private var privacySection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("隐私")
                .font(.headline)

            GroupBox {
                VStack(alignment: .leading, spacing: 12) {
                    Text("上下文权限")
                        .font(.subheadline)
                    Text("启用后可提供更准确的推荐。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    VStack(alignment: .leading, spacing: 6) {
                        Toggle("窗口标题", isOn: Binding(
                            get: { contextPreferences.canReadWindowTitle },
                            set: { contextPreferences.canReadWindowTitle = $0 }
                        ))

                        Toggle("浏览器域名", isOn: Binding(
                            get: { contextPreferences.canReadBrowserDomain },
                            set: { contextPreferences.canReadBrowserDomain = $0 }
                        ))

                        Toggle("Finder 目录", isOn: Binding(
                            get: { contextPreferences.canReadFinderDirectory },
                            set: { contextPreferences.canReadFinderDirectory = $0 }
                        ))

                        Toggle("Finder 选中文件", isOn: Binding(
                            get: { contextPreferences.canReadFinderSelection },
                            set: { contextPreferences.canReadFinderSelection = $0 }
                        ))
                    }

                    Divider()

                    Toggle("推荐过滤", isOn: Binding(
                        get: { contextPreferences.canFilterSensitiveContent },
                        set: { contextPreferences.canFilterSensitiveContent = $0 }
                    ))
                    Text("过滤敏感内容（密钥、令牌、密码等），防止其进入推荐。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 4)
            }

            // 这些文案早就写好了（`HistoryPrivacyCopy`，还有单测守着不重复、不为空），
            // 但一直没接进界面：隐私承诺只有写在代码里才算数吗？（审计 R-14）
            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Text("数据与保留")
                        .font(.subheadline)

                    ForEach(Array(HistoryPrivacyCopy.settingsBullets.enumerated()), id: \.offset) { _, line in
                        Text(line)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 4)
            }
        }
    }

    // MARK: - Recommendations Section

    private var recommendationsSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("推荐")
                .font(.headline)

            RecommendationWeightsView(store: weightsStore)

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("推荐反馈数据")
                    .font(.subheadline)

                HStack {
                    Button("导出反馈数据") {
                        exportFeedbackData()
                    }
                    .buttonStyle(.bordered)

                    if let message = exportMessage {
                        Text(message)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .alert("导出反馈数据", isPresented: $showExportAlert) {
                Button("好的", role: .cancel) {}
            } message: {
                Text(exportMessage ?? "")
            }
        }
    }

    // MARK: - Data Section

    private var dataSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("数据")
                .font(.headline)

            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Text("历史记录存储")
                        .font(.subheadline)
                    Text("剪贴板历史保存在本地，不会上传到任何服务器。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 4)
            }

            Divider()

            HStack(alignment: .center, spacing: 12) {
                VStack(alignment: .leading, spacing: 3) {
                    Text("清空未收藏记录")
                        .font(.subheadline)
                    Text("收藏记录会保留。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button(SettingsViewLayout.clearButtonTitle, role: .destructive) {
                    showClearHistoryConfirmation = true
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                .disabled(clearHistoryAction == nil)
            }
        }
    }

    // MARK: - Actions

    private func saveShowMainWindowShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != showMainWindowHotKeySettings.shortcut else { return }
        if !showMainWindowHotKeySettings.save(shortcut) {
            showMainWindowShortcut = showMainWindowHotKeySettings.shortcut
        }
    }

    private func saveRepeatCopyShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != repeatCopyHotKeySettings.shortcut else { return }
        if !repeatCopyHotKeySettings.save(shortcut) {
            repeatCopyShortcut = repeatCopyHotKeySettings.shortcut
        }
    }

    private func saveLaunchAtLogin(_ enabled: Bool) {
        guard enabled != loginItemSettings.isEnabled else { return }
        loginItemSettings.setEnabled(enabled)
    }
}

// MARK: - HotKey Row

private struct HotKeySettingsRow: View {
    @ObservedObject var settings: HotKeySettings
    @Binding var shortcut: HotKeyShortcut

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(settings.action.title)
                    Text(settings.action.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Spacer(minLength: 24)

                HotKeyRecorderView(
                    shortcut: $shortcut,
                    onInvalidShortcut: {
                        settings.recordInvalidShortcut()
                    }
                )
                .frame(width: 128, height: 28)

                Button("恢复默认") {
                    settings.reset()
                    shortcut = settings.shortcut
                }
            }

            if let message = settings.message {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }
}

// MARK: - Unified Settings Sidebar (matches main window hover style)

private struct SettingsSidebarView: View {
    @Binding var selectedCategory: SettingsCategory?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(SettingsCategory.allCases) { category in
                SettingsSidebarRow(
                    category: category,
                    isSelected: selectedCategory == category,
                    action: { selectedCategory = category }
                )
            }
            Spacer()
        }
        .padding(.top, 8)
    }
}

private struct SettingsSidebarRow: View {
    let category: SettingsCategory
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false

    private var backgroundOpacity: Double {
        if isSelected { return 0.16 }
        return isHovered ? 0.045 : 0
    }

    var body: some View {
        Button(action: action) {
            Label(category.title, systemImage: category.icon)
                // 不显式上色的话，未选中行的 SF Symbol 会按系统弱化色渲染，
                // 在浅色主题下几乎看不见（离屏渲染验收时发现的真实缺陷）
                .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor) : AnyShapeStyle(.primary))
                // 这里**刻意保持** `.hierarchical`。审计第二轮 1.9 说侧栏图标"outline 与 filled 混用、
                // 未选中的比选中的轻"，看起来像缺陷；本轮把这件事量成了数字（`OffscreenSymbolInkProbeTests`）：
                // 在这一帧里未选中四行的图标列墨水是 0.0000，而把同一个图标的颜色换成固定的 `Color.black`
                // 就能画到 0.175–0.402 —— 也就是说不可见来自**离屏管线对语义色的解析**，不是产品。
                // 结论：既不能按这帧判缺陷，也不能为了讨好这一帧把 `.primary` 换成固定色
                // （那会在真实深浅色切换时把颜色写死）。哪一层导致的没有定论，探针每次视觉审计会重量一遍。
                // 以前这里写的是"真机不可能长这样"的推断，现在换成测量。
                .symbolRenderingMode(.hierarchical)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .contentShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
        }
        .buttonStyle(.plain)
        .background(
            RoundedRectangle(cornerRadius: 9, style: .continuous)
                .fill(isSelected ? Color.accentColor.opacity(backgroundOpacity) : Color.primary.opacity(backgroundOpacity))
        )
        .font(.system(size: 13, weight: isSelected ? .semibold : .regular))
        .padding(.horizontal, 6)
        .animation(.easeInOut(duration: 0.11), value: isHovered)
        .animation(.easeInOut(duration: 0.11), value: isSelected)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Cross-version Split View (macOS 12 compatible, replaces HSplitView)

private struct CompatibleSplitView<Sidebar: View, Detail: View>: NSViewRepresentable {
    @ViewBuilder let sidebar: () -> Sidebar
    @ViewBuilder let detail: () -> Detail
    private let sidebarMinWidth: CGFloat
    private let sidebarIdealWidth: CGFloat

    init(
        sidebarMinWidth: CGFloat = 148,
        sidebarIdealWidth: CGFloat = 148,
        @ViewBuilder sidebar: @escaping () -> Sidebar,
        @ViewBuilder detail: @escaping () -> Detail
    ) {
        self.sidebarMinWidth = sidebarMinWidth
        self.sidebarIdealWidth = sidebarIdealWidth
        self.sidebar = sidebar
        self.detail = detail
    }

    func makeNSView(context: Context) -> NSSplitView {
        let splitView = NSSplitView()
        splitView.isVertical = true
        splitView.dividerStyle = .thin
        

        let sidebarNSView = NSHostingView(rootView: sidebar())
        sidebarNSView.translatesAutoresizingMaskIntoConstraints = false
        sidebarNSView.setContentHuggingPriority(.defaultHigh, for: .horizontal)

        let detailNSView = NSHostingView(rootView: detail())
        detailNSView.translatesAutoresizingMaskIntoConstraints = false

        splitView.addArrangedSubview(sidebarNSView)
        splitView.addArrangedSubview(detailNSView)

        // 只保留一条等宽约束：旧写法同时激活 ">= min" 与 "== ideal"，
        // 前者永远被后者吃掉，还让分栏看起来能拖却拖不动（审计 R-25）。
        sidebarNSView.widthAnchor.constraint(equalToConstant: sidebarIdealWidth).isActive = true

        return splitView
    }

    func updateNSView(_ splitView: NSSplitView, context: Context) {
        if let sidebarNSView = splitView.arrangedSubviews.first as? NSHostingView<Sidebar> {
            sidebarNSView.rootView = sidebar()
        }
        if let detailNSView = splitView.arrangedSubviews.last as? NSHostingView<Detail> {
            detailNSView.rootView = detail()
        }
    }
}
