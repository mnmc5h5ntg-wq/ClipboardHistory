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
        case .recommendations: return "wand.and.stars"
        case .data: return "folder"
        }
    }
}

struct SettingsView: View {
    @ObservedObject private var showMainWindowHotKeySettings: HotKeySettings
    private let feedbackStore: RecommendationFeedbackStore
    @ObservedObject private var repeatCopyHotKeySettings: HotKeySettings
    @ObservedObject private var quickPickHotKeySettings: HotKeySettings
    @ObservedObject private var loginItemSettings: LoginItemSettings
    @State private var showMainWindowShortcut: HotKeyShortcut
    @State private var repeatCopyShortcut: HotKeyShortcut
    @State private var quickPickShortcut: HotKeyShortcut
    @State private var launchAtLogin: Bool
    // 这两个键与 `HistoryStore.recordingPausedKey` / `ocrSearchDisabledKey` 是同一对，
    // 写在这里而不引用 store 是因为设置页在两个窗口里都会重建（@AppStorage 自带跨实例同步）。
    @AppStorage("recordingPaused") private var recordingPaused = false
    @AppStorage("ocrSearchDisabled") private var ocrSearchDisabled = false

    /// OCR 开关的界面语义是"启用"，而存储键是"禁用"（默认值取反的必要性见 `HistoryStore`）。
    private var ocrSearchEnabled: Binding<Bool> {
        Binding(get: { !ocrSearchDisabled }, set: { ocrSearchDisabled = !$0 })
    }
    @State private var showClearHistoryConfirmation = false
    @State private var archiveMessage: String?
    @AppStorage(CapturePolicy.userExcludedKey) private var excludedBundleIDsRaw = ""
    /// 富文本保真开关（§5 F-2）。默认关：打开等于每条文本记录多存 2 份表示，
    /// 存档体积翻几倍，而 RTF 里还常带着来源元数据。
    @AppStorage(RichTextPolicy.enabledKey) private var preserveRichText = false
    @State private var newExcludedBundleID = ""
    @AppStorage(OCRPolicy.modeKey) private var ocrModeRaw = OCRPolicy.StorageMode.persisted.rawValue
    @State private var exportMessage: String?
    @State private var showExportAlert = false
    @ObservedObject private var contextPreferences: ContextPreferenceSettings
    @ObservedObject private var weightsStore: RecommendationWeightsStore
    private let clearHistoryAction: (() -> Void)?
    /// 历史的导出 / 导入（第三轮审计 §5 F-5）。和 `clearHistoryAction` 一样由窗口控制器注入，
    /// 因为 `SettingsView` 在两个窗口里都会重建，不该直接持有 store。
    private let exportHistoryAction: ((URL) -> String?)?
    private let importHistoryAction: ((URL) -> String?)?
    @State private var selectedCategory: SettingsCategory?

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        // 有默认值只是为了让旧的测试夹具不必一起改；生产侧（AppDelegate）始终显式传入，
        // 而"确实传了"由 Round3QuickPickTests 的接线守卫钉住。
        quickPickHotKeySettings: HotKeySettings = HotKeySettings(action: .quickPick),
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        weightsStore: RecommendationWeightsStore = RecommendationWeightsStore(),
        feedbackStore: RecommendationFeedbackStore = RecommendationFeedbackStore(),
        clearHistoryAction: (() -> Void)? = nil,
        exportHistoryAction: ((URL) -> String?)? = nil,
        importHistoryAction: ((URL) -> String?)? = nil,
        initialCategory: SettingsCategory? = .shortcuts
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
        self.quickPickHotKeySettings = quickPickHotKeySettings
        self.loginItemSettings = loginItemSettings
        self.contextPreferences = contextPreferences
        self.weightsStore = weightsStore
        self.exportHistoryAction = exportHistoryAction
        self.importHistoryAction = importHistoryAction
        self.feedbackStore = feedbackStore
        self.clearHistoryAction = clearHistoryAction
        _showMainWindowShortcut = State(initialValue: showMainWindowHotKeySettings.shortcut)
        _repeatCopyShortcut = State(initialValue: repeatCopyHotKeySettings.shortcut)
        _quickPickShortcut = State(initialValue: quickPickHotKeySettings.shortcut)
        _launchAtLogin = State(initialValue: loginItemSettings.isEnabled)
        // 默认值与改动前的字面量初值一致：调用方不传就是"快捷键"页。
        // 存在的唯一理由：离屏窗口的无障碍树不会被 SwiftUI 建立，
        // 视觉验收没法用点击切分类，只能让初值可注入（见 AGENT_UI_AUDIT.md）。
        _selectedCategory = State(initialValue: initialCategory)
    }

    private func exportHistory() {
        guard let exportHistoryAction else { return }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "时间剪史-历史.json"
        panel.message = "导出内容包含完整剪贴板原文，请当作敏感文件保管。"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        archiveMessage = exportHistoryAction(url)
    }

    private func importHistory() {
        guard let importHistoryAction else { return }
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [.json]
        panel.message = "导入会把文件里的记录合并进历史（同一条不会重复导入）。"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        archiveMessage = importHistoryAction(url)
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
            .onChange(of: quickPickShortcut) { newValue in
                saveQuickPickShortcut(newValue)
            }
            .onChange(of: quickPickHotKeySettings.shortcut) { newValue in
                quickPickShortcut = newValue
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

                    Divider()

                    HotKeySettingsRow(
                        settings: quickPickHotKeySettings,
                        shortcut: $quickPickShortcut
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

                    // 下面两项是「通用」真正该管的**全局行为开关**（第三轮审计 D-3）：
                    // 这一页以前被 U-6 的去重删到只剩一个开关，整页 90% 空白 ——
                    // 修法不是再塞一个没用的东西，而是把"随时能一键停用/降敏感度"的两件事放这儿。
                    Toggle("暂停记录剪贴板（暂时不想被记录时）", isOn: $recordingPaused)
                    Text("暂停时仍在推进系统剪贴板的变更计数，所以恢复后不会补记一条暂停期间的旧内容；已入库的历史不受影响。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Toggle("识别截图文字用于搜索", isOn: ocrSearchEnabled)
                    Toggle("保留富文本格式（RTF / HTML）", isOn: $preserveRichText)
                    Text("打开后从 Word、Pages、邮件里复制的文字会连格式一起存，粘回去保留加粗与链接。"
                        + "代价是历史存档明显变大（单条最多 384KB），默认关闭；"
                        + "导出与导入只带纯文本。")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

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

                    Divider()

                    // MARK: 按 App 排除（第三轮审计 §5 F-1：密码管理器/钥匙串一类内容不该入库）
                    VStack(alignment: .leading, spacing: 6) {
                        Text("不记录这些 App 的复制")
                            .font(.subheadline)
                        Text("默认已包含密码管理器与系统钥匙串。这里添加的是**你额外**要排除的；"
                             + "排除只作用于自动采集 —— 你主动拖进历史的内容仍然会入库。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ForEach(Array(CapturePolicy.defaultExcludedBundleIDs.sorted()), id: \.self) { id in
                            Text("默认排除：\(id)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        ForEach(Array(CapturePolicy.decodeUserExcluded(excludedBundleIDsRaw)).sorted(), id: \.self) { id in
                            HStack {
                                Text(id)
                                Spacer()
                                Button("移除") {
                                    excludedBundleIDsRaw = CapturePolicy.encodeUserExcluded(
                                        Array(CapturePolicy.decodeUserExcluded(excludedBundleIDsRaw)).filter { $0 != id }
                                    )
                                }
                                .buttonStyle(.borderless)
                            }
                        }
                        HStack {
                            TextField("com.example.app", text: $newExcludedBundleID)
                                .textFieldStyle(.roundedBorder)
                                .frame(maxWidth: 260)
                            Button("添加") {
                                let id = newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines)
                                guard !id.isEmpty else { return }
                                excludedBundleIDsRaw = CapturePolicy.encodeUserExcluded(
                                    Array(CapturePolicy.decodeUserExcluded(excludedBundleIDsRaw)) + [id]
                                )
                                newExcludedBundleID = ""
                            }
                        }
                    }

                    Divider()

                    // MARK: OCR 结果的存放方式（§5 F-4 的"只索引不落盘"）
                    VStack(alignment: .leading, spacing: 6) {
                        Text("截图文字识别结果")
                            .font(.subheadline)
                        Picker("存放方式", selection: $ocrModeRaw) {
                            Text("随历史保存（重启后仍可搜）").tag(OCRPolicy.StorageMode.persisted.rawValue)
                            Text("只索引不落盘（重启后重新识别）").tag(OCRPolicy.StorageMode.indexOnly.rawValue)
                        }
                        .pickerStyle(.radioGroup)
                        .labelsHidden()
                        Text("「只索引不落盘」时，截图里识别出的文字不会写进 history.json；"
                             + "代价是每次启动要重新识别一遍。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
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

            // MARK: 导出 / 导入（第三轮审计 §5 F-5：以前用户没有任何方式把历史带走）
            VStack(alignment: .leading, spacing: 8) {
                Text("导出与导入")
                    .font(.subheadline)
                Text("导出的是自包含 JSON：默认不含图片，内容是完整的剪贴板原文（可能含账号、验证码、私人对话），请当作敏感文件保管。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 10) {
                    Button("导出历史…") { exportHistory() }
                        .disabled(exportHistoryAction == nil)
                    Button("导入历史…") { importHistory() }
                        .disabled(importHistoryAction == nil)
                }
                if let archiveMessage {
                    Text(archiveMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .textSelection(.enabled)
                }
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

    private func saveQuickPickShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != quickPickHotKeySettings.shortcut else { return }
        if !quickPickHotKeySettings.save(shortcut) {
            quickPickShortcut = quickPickHotKeySettings.shortcut
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
