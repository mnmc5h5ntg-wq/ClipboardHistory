import SwiftUI
import AppKit

enum SettingsViewLayout {
    static let windowContentSize = CGSize(width: 720, height: 540)
    static let minimumWindowSize = CGSize(width: 640, height: 440)
    static let sidebarWidth: CGFloat = 148
    /// 说明段与**它所解释的那一颗控件**之间的间距（R33 / U-55）。
    ///
    /// 3 而不是沿用组间的 8：8 之下"开关—它的说明"与"说明—下一颗开关"等距，
    /// 归属只能靠读句子猜（通用页就是这么错的：讲 OCR 的那句被挂到了 RTF 开关下面）。
    /// 3 是"明显是一组"与"两行字挤成一坨"之间的那一档：说明用的是 11pt `.caption`，
    /// 它的行框自带降部留白，再往下收到 1–2 就看不出是两行了。
    /// 判据不在这条常量上，在帧上：`testSettingsCaptionSitsCloserToItsOwnToggle`
    /// 量的是"说明段离上面那颗开关比离下面那颗更近"。
    static let captionGap: CGFloat = 3
    /// 卡片内容**上下**各补的留白（R95 / U-2xx）。
    ///
    /// 缺陷是量出来的，不是看出来的：`GroupBox { VStack(spacing: 12) { 行; Divider(); 行 } }`
    /// 里那 12pt 只长在**孩子之间**，于是同一张卡片有两种留白 ——
    /// 分隔线两侧各 14.5 / 15.0pt，而卡片自己的上下边缘只有 7.5 / 6.5pt（帧上逐行量的，
    /// 亮暗两档同一组数）。最后一行是四行说明的那一行时，它的末行离卡片底只有 6.5pt，
    /// 读起来像"卡片装不下内容"。
    ///
    /// 7 不是抄来的常数：目标是让卡片四边的留白等于它自己内部已经有的那一档（14.5pt），
    /// 而 GroupBox 自带 ~7pt ⇒ 再补 7 落在 14.5 / 13.5，与内侧那一档差 ≤1pt。
    /// 判据在帧上：`testSettingsCardVerticalRhythmIsOneNumber`。
    static let cardEdgeInset: CGFloat = 7
    /// 开关/单选控件的说明文字与**控件标签**共用一条文字轴。
    ///
    /// 旧形状：说明段是 `VStack` 里独立的 `Text`，于是它从左沿（复选框的左沿）起排，
    /// 而标签从复选框右侧起排 —— `settings-general` 帧量到标签左 **200.0pt**、
    /// 说明左 **179.0pt**，差 **21.0pt**，同一组"开关—说明"的左边读成两条轴。
    /// 21 = 系统复选框 14pt + 复选框与标签的间距 7pt（帧上量的，不是抄的）。
    /// 判据在帧上：`testSettingsHelperTextSharesTheToggleLabelAxis` 读标签行与说明行的最左墨。
    static let helperAxisIndent: CGFloat = 21
    static let clearButtonTitle = "清空"
}

extension View {
    /// 给一张卡片的内容补上**上下**留白，让卡片四边的留白与它自己分隔线两侧的留白是同一档。
    ///
    /// 为什么是一条扩展而不是五处 `.padding(.vertical, 7)`：这条判据要能被源码守卫数出来
    /// ——「有几张卡片」与「有几处补了留白」必须相等，而 `padding(.vertical, 7)` 这个词
    /// 在文件里还长在别的地方（卡片内部的小节就有一处），数它会数错。
    func settingsCardInset() -> some View {
        padding(.vertical, SettingsViewLayout.cardEdgeInset)
    }

    /// 说明文字与它解释的那颗开关/单选控件共用一条文字轴（见 `SettingsViewLayout.helperAxisIndent`）。
    func settingsHelperAxis() -> some View {
        padding(.leading, SettingsViewLayout.helperAxisIndent)
    }
}

/// R472：设置里的路径是**逐字符读**的值（`~/Library/...`），用比例字体时 `i/l/1` 与斜杠的
/// 步进不齐。拆出 "~/" 之后的整段路径用等宽字体；前缀（"保存位置："）保持正文的说明字体。
enum SettingsPathPresentation {
    static func split(_ text: String) -> (prefix: String, path: String?) {
        guard let range = text.range(of: "~/") else { return (text, nil) }
        return (String(text[..<range.lowerBound]), String(text[range.lowerBound...]))
    }

    /// 判据读的就是这一枚字体：`isFixedPitch` 是字体自己的结构量，不是抄一个字号。
    static var pathFont: NSFont {
        .monospacedSystemFont(ofSize: VisualFont.meta, weight: .regular)
    }
}

struct SettingsPathText: View {
    let text: String

    var body: some View {
        let parts = SettingsPathPresentation.split(text)
        if let path = parts.path {
            return Text(parts.prefix) + Text(path).font(Font(SettingsPathPresentation.pathFont))
        }
        return Text(text)
    }
}

enum SettingsCategory: String, CaseIterable, Identifiable {
    case shortcuts
    case general
    case privacy
    case recommendations
    case data
    /// 每日复制热图（新功能 / 阶段一）。放在最后：它是"回头看"的一页，
    /// 不是任何人的第一次进入点。
    case stats
    /// R442：关于页 —— 应用名/版本/build/定位/版权的唯一落点。
    /// 放在最后：介绍自己不是任何人的第一次进入点（与统计同一条排序理由）。
    case about

    var id: String { rawValue }

    var title: String {
        switch self {
        case .shortcuts: return "快捷键"
        case .general: return "通用"
        case .privacy: return "隐私"
        case .recommendations: return "推荐"
        case .data: return "数据"
        case .stats: return "统计"
        case .about: return "关于"
        }
    }

    var icon: String {
        switch self {
        case .shortcuts: return "command"
        case .general: return "gearshape"
        case .privacy: return "hand.raised"
        case .recommendations: return "wand.and.stars"
        case .data: return "folder"
        // 描线系（与其余五枚同一套语言，D-8 那条判据管的就是这个）：
        // `chart.bar` 而不是 `chart.bar.fill`。
        case .stats: return "chart.bar"
        case .about: return "info.circle"
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
    /// 「清空未收藏」之后的那一句"清掉了多少条"（R6 / 审计 B-P1-2）。
    ///
    /// 为什么不复用 `archiveMessage`：那条长在「导出与导入」那一节里（`SettingsView.swift:523`），
    /// 用户按的是下面那颗红色按钮，回执却出现在**上面另一节**——那是"回执离动作有 40pt 远"，
    /// 而这一句要回答的是"我刚刚那一下到底收到没有"。
    @State private var clearReceipt: String?
    @AppStorage(CapturePolicy.userExcludedKey) private var excludedBundleIDsRaw = ""
    /// 富文本保真开关（§5 F-2）。默认关：打开等于每条文本记录多存 2 份表示，
    /// 存档体积翻几倍，而 RTF 里还常带着来源元数据。
    @AppStorage(RichTextPolicy.enabledKey) private var preserveRichText = false
    @State private var newExcludedBundleID = ""
    /// R384：登录项回执的颜色要看外观（系统红在暗档的离屏帧里只有 2.87:1，低于说明文字档）。
    @Environment(\.colorScheme) private var colorScheme
    @AppStorage(OCRPolicy.modeKey) private var ocrModeRaw = OCRPolicy.StorageMode.persisted.rawValue
    @State private var exportMessage: String?
    /// 「按 App 排除」名单增删的回执（R8 / 审计 B-P2）。
    /// `encodeUserExcluded` 会去重 + 排序，所以"加了没变"有三种不同原因，
    /// 而以前**一种都看不出来**：输入框清空、列表没长，用户读到的是"我加的那条去哪了"。
    @State private var exclusionReceipt: String?
    // R43 / BACKLOG 62：这里原来还有一个 `@State private var showExportAlert = false`，
    // 与下面那条 `.alert` 一起被删掉 —— 「导出反馈数据」的结果过去**同时**走模态与行内两条通道，
    // 而仓库里其余三处回执（清空历史 / 导出导入存档 / 排除名单）都是行内。删的是**多出来的那一条**。
    @ObservedObject private var contextPreferences: ContextPreferenceSettings
    @ObservedObject private var weightsStore: RecommendationWeightsStore
    /// 清空历史。返回**回执文案**（`nil` = 没有可清空的东西 / 注入方没给）。
    /// 以前它是 `() -> Void`：按完确认之后红色按钮还在原位、还能再点，
    /// 整个界面上没有任何一处说"清掉了 N 条"（R6 / 审计 B-P1-2）。
    /// 每日复制统计的账本。`nil` = 不接（测试与离屏夹具的默认），此时那一页说"统计不可用"。
    private let dailyCopyLedger: DailyCopyLedger?
    private let clearHistoryAction: (() -> String?)?
    /// 历史的导出 / 导入（第三轮审计 §5 F-5）。和 `clearHistoryAction` 一样由窗口控制器注入，
    /// 因为 `SettingsView` 在两个窗口里都会重建，不该直接持有 store。
    private let exportHistoryAction: ((URL) -> String?)?
    private let importHistoryAction: ((URL) -> String?)?
    @State private var selectedCategoryState: SettingsCategory?
    /// R442：关于页的版本/build 注入缝（产品路径读真实 bundle）。
    @Environment(\.settingsSidebarVersionForCapture) private var aboutVersionOverride
    @Environment(\.settingsAboutBuildForCapture) private var aboutBuildOverride
    /// R486：数据页导出/导入两颗按钮的图标缝（产品默认 nil ⇒ 画图标）。
    @Environment(\.settingsDataActionIconsForCapture) private var dataActionIconsForCapture
    private var dataActionIconsVisible: Bool { dataActionIconsForCapture ?? true }
    /// R489：默认排除项尾部「默认」标记的负向帧缝（产品默认 nil ⇒ 画）。
    @Environment(\.settingsDefaultExcludedBadgeForCapture) private var defaultExcludedBadgeForCapture
    private var defaultExcludedBadgeVisible: Bool { defaultExcludedBadgeForCapture ?? true }
    /// R492：开机启动失败回执图标的负向帧缝（产品默认 nil ⇒ 画）。
    @Environment(\.loginFailureIconForCapture) private var loginFailureIconForCapture
    private var loginFailureIconVisible: Bool { loginFailureIconForCapture ?? true }
    /// R498：RTF 说明段断行形态的负向帧缝（产品默认 nil ⇒ 用不断开「文本。」的写法）。
    @Environment(\.settingsRtfHelperCopyForCapture) private var rtfHelperCopyForCapture
    /// R495：通用页说明文字的负向帧缝（产品默认 nil ⇒ 11pt `meta` 下限）。
    @Environment(\.settingsHelperFontForCapture) private var settingsHelperFontForCapture
    private var settingsHelperFont: Font {
        (settingsHelperFontForCapture ?? true)
            ? .system(size: VisualFont.meta)
            : .system(size: 10)
    }
    /// R395：只读的分类绑定缝。产品路径永远是 nil；测试用它驱动真实的分类切换。
    private let categoryOverride: Binding<SettingsCategory?>?

    private var loginFailureStyle: AnyShapeStyle {
        AnyShapeStyle(colorScheme == .dark
            ? Color(red: 1.0, green: 0.48, blue: 0.44)
            : Color.red)
    }

    private var selectedCategory: SettingsCategory? {
        categoryOverride?.wrappedValue ?? selectedCategoryState
    }

    private var selectedCategoryBinding: Binding<SettingsCategory?> {
        categoryOverride ?? $selectedCategoryState
    }

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
        dailyCopyLedger: DailyCopyLedger? = nil,
        clearHistoryAction: (() -> String?)? = nil,
        exportHistoryAction: ((URL) -> String?)? = nil,
        importHistoryAction: ((URL) -> String?)? = nil,
        initialCategory: SettingsCategory? = .shortcuts,
        categoryOverride: Binding<SettingsCategory?>? = nil
    ) {
        self.categoryOverride = categoryOverride
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
        self.dailyCopyLedger = dailyCopyLedger
        _showMainWindowShortcut = State(initialValue: showMainWindowHotKeySettings.shortcut)
        _repeatCopyShortcut = State(initialValue: repeatCopyHotKeySettings.shortcut)
        _quickPickShortcut = State(initialValue: quickPickHotKeySettings.shortcut)
        _launchAtLogin = State(initialValue: loginItemSettings.isEnabled)
        // 默认值与改动前的字面量初值一致：调用方不传就是"快捷键"页。
        // 存在的唯一理由：离屏窗口的无障碍树不会被 SwiftUI 建立，
        // 视觉验收没法用点击切分类，只能让初值可注入（见 AGENT_UI_AUDIT.md）。
        _selectedCategoryState = State(initialValue: initialCategory)
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
        //
        // R43 / BACKLOG 62：这一条回执原来**同时**走两条通道（行内 `ReceiptLine` + 模态 `.alert`），
        // 而失败那一支是 `error.localizedDescription` 直出 —— `ExportError` 不是 `LocalizedError`，
        // 于是界面会写 "The operation couldn't be completed. (…)"。那是 R41 的 U-67 在另一个出口上复现。
        // 现在：措辞由 `FeedbackExportReceipt` 决定（纯函数、有真值表），原文进日志，
        // **只说一次**（行内，与清空历史 / 导出导入存档 / 排除名单那三处同一套语言）。
        do {
            let url = try feedbackStore.exportToFile()
            exportMessage = FeedbackExportReceipt.success(fileName: url.lastPathComponent)
            NSWorkspace.shared.activateFileViewerSelecting([url])
        } catch let error {
            LifecycleDebugLogger.log("SettingsView feedback export failed error=\(error)")
            exportMessage = FeedbackExportReceipt.failure(error)
        }
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
                    clearReceipt = clearHistoryAction?()
                    // 一次不可撤销的删除，回执最该给的是**看不见屏幕的人**：
                    // 视觉侧那一句在按钮正下方淡入，语音侧走同一条文案（R6）。
                    if let clearReceipt { VoiceOverReceipt.announce(clearReceipt) }
                }
            } message: {
                Text("收藏记录会保留，其余历史会被清空。")
            }
    }

    @ViewBuilder
    private var settingsContent: some View {
        Group {
            if #available(macOS 13, *) {
                NavigationSplitView {
                    SettingsSidebarView(selectedCategory: selectedCategoryBinding)
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
                    SettingsSidebarView(selectedCategory: selectedCategoryBinding)
                } detail: {
                    detailScrollView
                }
            }
        }
    }

    private var detailScrollView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 下面这棵 switch 的分支会随分类整个换掉 ⇒ 给它一次淡入（动效审计 M1 的
                // 可行版本之一：普通容器上的 `.transition` 是工作的，`List` 行上不是）。
                // 刻意**不**做横向推入：那是网页的形状，macOS 系统设置换分类时不推。
                Group {
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
                    case .stats:
                        statsSection
                    case .about:
                        aboutSection
                    case .none:
                        EmptyView()
                    }
                }
                .id(selectedCategory)
                .transition(MotionCatalog.transition(for: .contentFade))
            }
            .padding(24)
        }
        .animation(MotionCatalog.animation(for: .contentFade), value: selectedCategory)
    }

    // MARK: - Shortcuts Section

    /// R476：三行快捷键两两对账。冲突不是"设置没保存"——两组键都真的注册过，
    /// 但系统只会把热键递给其中一个，因此界面必须说清另一组按下去不会响。
    private var shortcutConflicts: [ShortcutConflictPolicy.Conflict] {
        ShortcutConflictPolicy.conflicts([
            (name: "呼出主窗口", shortcut: showMainWindowShortcut),
            (name: "再次复制", shortcut: repeatCopyShortcut),
            (name: "快速选择并粘贴", shortcut: quickPickShortcut),
        ])
    }

    private var shortcutsSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("快捷键", category: .shortcuts)

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
                .settingsCardInset()
            }

            // R476：冲突提示放在卡片外、页标题那一列 —— 它说的是"这三行之间的关系"，
            // 不属于某一行，塞进任一行的说明里都会被读成那一行自己的问题。
            ForEach(Array(shortcutConflicts.enumerated()), id: \.offset) { _, conflict in
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(Color(nsColor: .systemOrange))
                    Text("「\(conflict.firstName)」与「\(conflict.secondName)」都设为 \(conflict.shortcut)"
                         + " —— 同一组键只会触发其中一个，请改开一个。")
                        .foregroundStyle(.primary)
                }
                .font(.caption)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("shortcutConflictWarning")
            }
        }
    }

    // MARK: - General Section

    private var generalSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("通用", category: .general)

            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        // R396：不支持时整颗 Toggle（含标签）被系统额外压暗，标签实测
                        // 亮 1.76 / 暗 2.13:1，低于禁用标签地板 2.2。把标签移出被禁用的
                        // 控件，复选框仍禁用；标签在支持时仍可直接点。
                        HStack(spacing: 6) {
                            Toggle("开机启动", isOn: $launchAtLogin)
                                .labelsHidden()
                                .toggleStyle(.checkbox)
                                .disabled(!loginItemSettings.isSupported)
                            Text("开机启动")
                                .foregroundStyle(loginItemSettings.isSupported
                                                 ? AnyShapeStyle(.primary)
                                                 : AnyShapeStyle(.secondary))
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    if loginItemSettings.isSupported { launchAtLogin.toggle() }
                                }
                                .accessibilityHidden(true)
                        }
                        // 这条回执讲的是**开机启动**这一颗（`loginItemSettings` 的失败原因），
                        // 原来它排在整组最后：中间隔着三个开关与两段说明，
                        // 读起来像在解释上面那段富文本。R33 把它挪回自己那颗下面。
                        // R39：这里原来写的是"帧里量不到（夹具下 `message == nil`）⇒ 只进账本不进判据"。
                        // 现在两张夹具把 message 造出来了（`settings-general-login-unsupported` /
                        // `-failed`），于是这条有像素判据：说明档探针两条 +
                        // `testDisabledToggleAndFailureReceiptAreVisible` 的跨帧差值对照。
                        if let message = loginItemSettings.message {
                            // R492：失败回执只有红字，没有错误图标；横幅/回执都有图标，
                            // 这一行补一枚警示三角，正常的不支持说明不加。
                            HStack(spacing: 4) {
                                if loginItemSettings.lastActionFailed, loginFailureIconVisible {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .font(.system(size: VisualGlyph.badge, weight: .semibold))
                                        .foregroundStyle(loginFailureStyle)
                                }
                                Text(message)
                                    .font(settingsHelperFont)
                                    // R384：失败回执用错误色，与「本机不支持」的静态说明分开
                                    // （快捷键页的非法录制回执也是红字；同一套状态语言）。
                                    // 判据是坐标无关的：失败帧里有红色文字像素、说明帧里没有。
                                    .foregroundStyle(loginItemSettings.lastActionFailed
                                                     ? loginFailureStyle
                                                     : AnyShapeStyle(.secondary))
                            }
                            .settingsHelperAxis()
                        }
                    }

                    // 下面两项是「通用」真正该管的**全局行为开关**（第三轮审计 D-3）：
                    // 这一页以前被 U-6 的去重删到只剩一个开关，整页 90% 空白 ——
                    // 修法不是再塞一个没用的东西，而是把"随时能一键停用/降敏感度"的两件事放这儿。
                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        Toggle("暂停记录剪贴板（暂时不想被记录时）", isOn: $recordingPaused)
                        Text("暂停时仍在推进系统剪贴板的变更计数，所以恢复后不会补记一条暂停期间的旧内容；已入库的历史不受影响。")
                            .font(settingsHelperFont)
                            .foregroundStyle(.secondary)
                            .settingsHelperAxis()
                    }

                    // R33 / U-55：这两组原来写成"两个开关连着、两段说明连着"，
                    // 于是屏上的阅读顺序变成
                    // 「识别截图文字 → 保留富文本 → RTF 的代价 → 关闭后不再对新入库的图片做文字识别」，
                    // 那句讲的是 **OCR** 的说明被挂到了 RTF 开关下面（亮暗两档帧里都看得很清楚）。
                    // 改法是把说明段与它解释的那一颗开关编成一组，组内间距也比组间小 ——
                    // 只重排不收紧间距的话，说明段与上下两颗开关**等距**，归属还是靠猜。
                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        Toggle("识别截图文字用于搜索", isOn: ocrSearchEnabled)
                        Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                            .font(settingsHelperFont)
                            .foregroundStyle(.secondary)
                            .settingsHelperAxis()
                    }

                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        Toggle("保留富文本格式（RTF / HTML）", isOn: $preserveRichText)
                        // R498：640pt 最小窗下最后一行只剩「本。」（孤字行，末行墨宽 ~18pt）。
                        // 用 U+00A0 把「文本。」绑成一个不断开的单元，末行回到三字宽；
                        // 这不是改文案，读者看到的仍是同一句话。
                        Text(rtfHelperCopyForCapture == false
                             ? "打开后从 Word、Pages、邮件里复制的文字会连格式一起存，粘回去保留加粗与链接。"
                               + "代价是历史存档明显变大（单条最多 384KB），默认关闭；"
                               + "导出与导入只带纯文本。"
                             : "打开后从 Word、Pages、邮件里复制的文字会连格式一起存，粘回去保留加粗与链接。"
                               + "代价是历史存档明显变大（单条最多 384KB），默认关闭；"
                               + "导出与导入只带纯文\u{00A0}本。")
                            .font(.system(size: VisualFont.meta))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .settingsHelperAxis()
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .settingsCardInset()
            }
            // 清空历史只在「数据」页出现一次：同一个破坏性按钮在两个分类里
            // 各放一份，用户无法判断是不是两件事，两份实现还会各自漂移。
        }
    }

    // MARK: - Privacy Section

    private var privacySection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("隐私", category: .privacy)

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
                        .settingsHelperAxis()

                    Divider()

                    // MARK: 按 App 排除（第三轮审计 §5 F-1：密码管理器/钥匙串一类内容不该入库）
                    VStack(alignment: .leading, spacing: 6) {
                        Text("不记录这些 App 的复制")
                            .font(.subheadline)
                        // R14 的帧审查抓到的一条：这句里的 `**…**` 是**当字面量画出来的**
                        // —— 设置页的 `Text` 走的是普通字符串，不解析 Markdown（详情区那条
                        // Markdown 渲染管线是内容用的，不是 chrome 用的）。
                        // 改法是把强调去掉而不是接上渲染器：这一页别的地方都不加粗，
                        // 为一句话引入一条排版通道不值。
                        Text("默认已包含密码管理器与系统钥匙串。这里添加的是你额外要排除的；"
                             + "排除只作用于自动采集 —— 你主动拖进历史的内容仍然会入库。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        // R432：默认名单从「默认排除：com.…」的纯文本流改成
                        // 图标 + 应用名 + bundle ID 的行（用户认不出裸 ID 是哪个 App）。
                        ForEach(Array(CapturePolicy.defaultExcludedBundleIDs.sorted()), id: \.self) { id in
                            // R489：默认项没有「移除」，尾部补一个「默认」身份标记，
                            // 让"为什么这一行不能删"在界面上有答案。
                            HStack(spacing: 6) {
                                ExcludedAppRow(bundleID: id)
                                if defaultExcludedBadgeVisible {
                                    Text("默认")
                                        .font(.system(size: VisualFont.meta))
                                        .foregroundStyle(.secondary)
                                        .fixedSize(horizontal: true, vertical: false)
                                        .accessibilityLabel("默认排除项，不可移除")
                                }
                            }
                        }
                        ForEach(Array(CapturePolicy.decodeUserExcluded(excludedBundleIDsRaw)).sorted(), id: \.self) { id in
                            HStack {
                                ExcludedAppRow(bundleID: id)
                                Button("移除") {
                                    let result = ExcludedAppListPolicy.remove(id, from: excludedBundleIDsRaw)
                                    excludedBundleIDsRaw = result.raw
                                    exclusionReceipt = result.receipt
                                }
                                // R13：`.borderless` 换成有按压/悬停的一档（同一轮把三处一起收，
                                // 见 `PressableStyle` 里 `isHovered: false` 那条）。
                                // 这是一颗**破坏性**按钮，"按到了"最不该省。
                                // R403：同一句也适用于颜色 —— 它原来和普通行文本一样黑，
                                // 而全 App 的破坏性动作（批量删除/清空）都是错误红。
                                // 用 R399 压过 runner 的一对红，避免暗档掉回 3:1 以下。
                                .foregroundStyle(colorScheme == .dark
                                                 ? AnyShapeStyle(Color(red: 1.0, green: 0.62, blue: 0.58))
                                                 : AnyShapeStyle(Color(red: 0.72, green: 0.0, blue: 0.0)))
                                .pressedStyle(in: VisualShape.rounded(VisualRadius.control),
                                              hoverLevel: VisualFill.controlHover,
                                              labelPadding: 4)
                            }
                            // 行会真的消失：这里不是 `List`（`List` 的行过渡在 macOS 上
                            // 四种写法都跑不出来，账本 M1 / D-055），是普通 `VStack`，
                            // 所以过渡**能**演 —— 前提是别只挂一臂（R5 的 A2 那一族）。
                            .transition(MotionCatalog.transition(for: .contentFade))
                        }
                        HStack {
                            TextField("com.example.app", text: $newExcludedBundleID)
                                .textFieldStyle(.roundedBorder)
                                .frame(maxWidth: 260)
                            Button("添加") {
                                let result = ExcludedAppListPolicy.add(newExcludedBundleID,
                                                                      to: excludedBundleIDsRaw)
                                excludedBundleIDsRaw = result.raw
                                exclusionReceipt = result.receipt
                                // 只有真的加进去才清空输入框：
                                // 没加成的时候把词留着，用户可以照着回执改。
                                if case .added = result.outcome { newExcludedBundleID = "" }
                            }
                            // R402：空输入按下去只会得到一条"没加成"的回执 —— 那颗按钮
                            // 在最该不可点的时刻是可点的。空白/纯空格输入下直接禁用。
                            .disabled(newExcludedBundleID
                                .trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                        if let exclusionReceipt {
                            ReceiptLine(text: exclusionReceipt) { self.exclusionReceipt = nil }
                        }
                    }
                    // 名单变长/变短要有过程，且**两臂共用这一条驱动**（键是那份持久化字符串，
                    // 它只在增删时变 ⇒ 不是恒真键，见 `MotionDriverTests`）。
                    .animation(MotionCatalog.animation(for: .contentFade),
                               value: excludedBundleIDsRaw)
                    // R42 / BACKLOG 53：**这条驱动原来推不到回执**。键只有那份字符串，
                    // 于是"重复添加 / 输入不合法"这两种名单没变的情况下，`ReceiptLine` 里那句
                    // `.transition(.contentFade)` 仍然不演 —— 回执是瞬间弹出来的。
                    // 为什么是**再加一条**而不是把键换成元组：Swift 的元组不 conform `Equatable`
                    // （`(String, Bool)` 直接编译失败，本轮实测），而为一个动画键新造一个结构体
                    // 不值得 —— 两条 `.animation` 各看各的键，读起来也更接近"谁该被推动"。
                    .animation(MotionCatalog.animation(for: .contentFade),
                               value: exclusionReceipt == nil)

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
                            .settingsHelperAxis()
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .settingsCardInset()
            }

            // 这些文案早就写好了（`HistoryPrivacyCopy`，还有单测守着不重复、不为空），
            // 但一直没接进界面：隐私承诺只有写在代码里才算数吗？（审计 R-14）
            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Text("数据与保留")
                        .font(.subheadline)

                    ForEach(Array(HistoryPrivacyCopy.settingsBullets.enumerated()), id: \.offset) { _, line in
                        SettingsPathText(text: line)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .settingsCardInset()
            }
        }
    }

    // MARK: - Recommendations Section

    private var recommendationsSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("推荐", category: .recommendations)

            RecommendationWeightsView(store: weightsStore)

            // R99 / BACKLOG 142：这一段以前是"卡片外一条裸 `Divider()` + 标题 + 按钮"，
            // 与上面那张卡片之间没有任何容器关系 —— 同一句"这些是并列的段落"在这一屏
            // 用了两种语言说（卡片里的段落有材质、卡片外的没有）。
            // 实测出处：`testSettingsCardVerticalRhythmIsOneNumber` 的 `CARD_BELOW` 那一格，
            // 推荐屏 1040 那一档读到卡片之下 2 段墨（885.0..895.0pt 标题、911.5..923.5pt 按钮），
            // 而其余九屏两档全是 0 段 ⇒ 这不是"另一种合法排版"，是这一屏独有的形状。
            // 收成第二张卡片，与「隐私」那一屏的两张卡片同一套（`settings-privacy-tall`
            // 实测卡片段=2）。**只动容器**：按钮、回执通道、动画键一行没改。
            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Text("推荐反馈数据")
                        .font(.subheadline)

                    HStack {
                        Button("导出反馈数据") {
                            exportFeedbackData()
                        }
                        .buttonStyle(.bordered)

                        if let message = exportMessage {
                            ReceiptLine(text: message) { self.exportMessage = nil }
                        }
                    }
                    // R42 / BACKLOG 53：**这一条回执以前没有驱动**。`ReceiptLine` 自己挂着
                    // `.transition(.contentFade)`（:976），而它的父容器一个 `.animation` 都没有 ⇒
                    // 那句声明等于零：回执是**瞬间**出现、**瞬间**消失的，读起来像界面闪了一下怪东西。
                    // 键取"有没有回执"这一个布尔，与 `clearReceipt` 那条同一套写法（见 :659 的注释）：
                    // 连续两次导出换文案不该再演一次，从无到有才需要被看见。
                    .animation(MotionCatalog.animation(for: .contentFade), value: exportMessage == nil)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                // 上面那一格 `.frame(maxWidth: .infinity)` 是必须的，不是排版洁癖：
                // 不加它，`GroupBox` 会按内容收缩，这张卡片在 720pt 宽的窗口里只画出
                // **250pt 宽的一小块**（本轮 1040 那一档的帧实测就是这样，一眼看得见）。
                // 而卡片尺要求的"横贯过去的一段卡片材质"也就读不到了 ⇒ 它会安静地
                // 变成"这张卡片不存在"，第二屏外的裸内容照样漏网。
                .settingsCardInset()
            }
                // R43 / BACKLOG 62：这里原来是 `.alert("导出反馈数据", isPresented: $showExportAlert)`，
                // 与上面那条行内 `ReceiptLine` 说同一句话 ⇒ 一次导出被说两遍，其中一遍还是模态打断。
                // 删的是模态那一条，行内保留（与清空历史 / 导出导入存档 / 排除名单同一套语言）。
        }
    }

    // MARK: - Data Section

    // MARK: - About Section (R442)

    private var aboutVersionLine: String {
        AboutPresentation.resolvedVersionLine(shortVersionOverride: aboutVersionOverride,
                                              buildOverride: aboutBuildOverride)
    }

    /// 关于页：应用名、版本/build、一句定位、版权。版本与 build 都只做展示，读不到不编占位。
    /// 这一页是设置里唯一"介绍自己"的地方 —— 侧栏底部那行只有应用名 + 版本。
    private var aboutSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("关于", category: .about)
            GroupBox {
                VStack(alignment: .leading, spacing: 12) {
                    Text(AboutPresentation.appName)
                        .font(.title3)
                        .fontWeight(.semibold)
                    Text(aboutVersionLine)
                        .font(.system(size: VisualFont.body))
                        .foregroundStyle(.secondary)
                    Text(AboutPresentation.tagline)
                        .font(.system(size: VisualFont.body))
                        .foregroundStyle(.secondary)
                    Text(AboutPresentation.copyright)
                        .font(.system(size: VisualFont.meta))
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .settingsCardInset()
            }
        }
    }

    /// 「统计」这一页（新功能 / 阶段一；R101 起这一屏也守"卡片"那套语言，见 BACKLOG 131）。
    @ViewBuilder
    private var statsSection: some View {
        // 分区标题与卡片**都由 `DailyCopyStatsSection` 自己摆**：胶片探针驱动的就是那一层
        // （`MotionFilmstripTests` 的 `heat-first-record`），标题如果留在这一侧，
        // 探针看到的就是一副没有头的骨架 —— 那一族在仓库里记过（第二轮 N-1 的守卫绕开 adapter）。
        if let dailyCopyLedger {
            DailyCopyStatsSection(ledger: dailyCopyLedger)
        } else {
            // 拿不到账本时不许画一张全灰的图冒充"你这半年什么都没复制"。
            StateLine(kind: .error, message: "统计不可用：没有拿到按日账本。")
        }
    }

    /// 「这张图怎么读」那段说明**不在这里**：它挂在 `DailyCopyStatsSection` 里，
    /// 因为只有那一层观察账本 ⇒ 见下面那段注释。
    private var dataSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SettingsPageTitle("数据", category: .data)

            // R92 / 分组语言对账（本机量出来的，见 .scratch/motion-audit-2/r92_data_readings.log）：
            // 同一个设置窗口里五种分区用了四套分组语法 ——
            //   通用 1 张卡片 / 卡片外 0 条线 / 卡片内 0 条线
            //   快捷键 1 张卡片 / 外 0 / 内 2（156pt、214pt）
            //   隐私 1 张卡片 / 外 0 / 内 3（45pt、262pt、328pt）
            //   统计 0 张卡片 / 外 1（271pt）
            //   **数据 1 张卡片 / 外 2（173pt、282pt）/ 内 0**  ← 本轮改的就是这一行
            // "卡片外面还有一条压在背景上的分隔线"只有这一屏有，而它那张卡片只圈住了
            // 两段说明文字（106..158pt），另外两段整段裸在外面 ⇒ 同一句"这三段是并列的"
            // 在这一屏用了两种语言说。向多数（快捷键 / 隐私那套 `GroupBox + VStack(spacing:12)
            // + 内部 Divider()`）靠拢。**只动容器**：三段自己的动画键、回执通道、禁用逻辑一行没改。
            GroupBox {
                VStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("历史记录存储")
                            .font(.subheadline)
                        Text("剪贴板历史保存在本地，不会上传到任何服务器。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        // R473：数据页是用户找"存在哪"的地方，路径不该只藏在隐私卡里。
                        SettingsPathText(text: "保存位置：~/Library/Application Support/时间剪史/")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    // R96：这一格 `.padding(.vertical, 4)` 被删掉了 —— 它是**三段里只有第一段有**的
                    // 一份内边距，于是同一张卡片里出现 18.0 与 14.5 两种留白
                    // （`testSettingsCardVerticalRhythmIsOneNumber` 把对象从一张卡扩到每张卡之后
                    // 第一次照出来的一条红：`settings-data 边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`）。
                    // 上一轮我把它当"卡片内部讲的是另一件事"留下了，那句话现在被自己的读数推翻：
                    // 它讲的就是同一件事（行与分隔线之间的距离），却只有一段有。

                    Divider()

                    // MARK: 导出 / 导入（第三轮审计 §5 F-5：以前用户没有任何方式把历史带走）
                    VStack(alignment: .leading, spacing: 8) {
                        Text("导出与导入")
                            .font(.subheadline)
                        Text("导出的是自包含 JSON：默认不含图片，内容是完整的剪贴板原文（可能含账号、验证码、私人对话），请当作敏感文件保管。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        HStack(spacing: 10) {
                            // R486：同一组里清空已有垃圾桶图标，导出/导入却还是纯文字 ——
                            // 三颗动作的图标语言分裂。补系统箭头符号，标签一字不改。
                            Button { exportHistory() } label: {
                                if dataActionIconsVisible {
                                    Label("导出历史…", systemImage: "square.and.arrow.up")
                                } else {
                                    Text("导出历史…")
                                }
                            }
                            .disabled(exportHistoryAction == nil)
                            Button { importHistory() } label: {
                                if dataActionIconsVisible {
                                    Label("导入历史…", systemImage: "square.and.arrow.down")
                                } else {
                                    Text("导入历史…")
                                }
                            }
                            .disabled(importHistoryAction == nil)
                        }
                        if let archiveMessage {
                            ReceiptLine(text: archiveMessage) { self.archiveMessage = nil }
                        }
                    }
                    // R42 / BACKLOG 53：同上，这一条也没有驱动（导出/导入历史那两条回执）。
                    // 键同样是"有没有回执"，不是消息内容：连续两次导入换文案不该再演一次。
                    .animation(MotionCatalog.animation(for: .contentFade), value: archiveMessage == nil)

                    Divider()

                    VStack(alignment: .leading, spacing: 6) {
                        HStack(alignment: .center, spacing: 12) {
                            VStack(alignment: .leading, spacing: 3) {
                                Text("清空未收藏记录")
                                    .font(.subheadline)
                                Text("收藏记录会保留。")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            Button(role: .destructive) {
                                showClearHistoryConfirmation = true
                            } label: {
                                Label(SettingsViewLayout.clearButtonTitle, systemImage: "trash")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.red)
                            .disabled(clearHistoryAction == nil)
                        }
                        if let clearReceipt {
                            // 图标 + 一句数字。刻意不用绿色"成功"强调：这是一次**不可撤销的删除**，
                            // 要的是"告诉你删了多少"，不是庆祝（第三轮 U-5 那句"状态语言统一"）。
                            HStack(spacing: 6) {
                                Image(systemName: "checkmark.circle")
                                    .font(.system(size: VisualGlyph.badge))
                                Text(clearReceipt)
                                    .font(.system(size: VisualFont.meta))
                            }
                            .foregroundStyle(.secondary)
                            .transition(MotionCatalog.transition(for: .contentFade))
                        }
                    }
                    // 键只取"有没有回执"这一个布尔：换文案（连续清两次）不该再演一次，
                    // 那读起来像在抢注意力；从无到有才需要被看见。
                    .animation(MotionCatalog.animation(for: .contentFade), value: clearReceipt == nil)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .settingsCardInset()
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

/// 录制态在**整行**上的那一层（R412）。
///
/// 为什么不是只靠录音器自己那圈描边：那一圈只圈住 128×28 的按钮，而这一行真正要读的是
/// 「哪个动作正在吃键」—— 标题与说明在按钮左边，常被眼睛先扫到。三行快捷键里只看按钮，
/// 得先找到那圈蓝再回头读标题；行级描边把「这一行」和「正在听」绑在同一处。
///
/// 为什么是**描边**而不是整行底色（R412 首拍）：底色会把行内文字之间的留白也涂成墨，
/// 卡片节奏尺读到的段落间距从 14.5 掉到 0.0（`testSettingsCardVerticalRhythmIsOneNumber`）——
/// 那条尺量的是布局，不应被一个状态底色改写。描边只落在行边界上，行内留白与行距原样。
///
/// 为什么只纵向外扩 2pt：横向一扩就把卡片左沿的第一墨列从 5 拉到 3
///（`testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox` 当场读 3.0）；
/// 纵向再多会把行距吃掉超过 4.5pt。纵向 2pt 既避开字形，又留在节奏尺的容差内。
///
/// **R413 更正**：runner 1x 上纵向 −2 仍把行距从 14 压到 10/9（节奏尺 15/10/9 红），
/// 而整页录制帧的邻行只是**1 级底色差**（邻行强调 0）不是描边泄漏。所以描边改成
/// **纵向不外扩**（与行内容同边）：行距原样，邻行隔离由“任意变化”改判“强调色”。
/// R412 的 `SCROLL_REVEAL`/`RECORDER_ROW_EDGE` 两条 runner 红就是这两件事。
///
/// 值仍然是模型值：静置恒 0（静置帧逐像素不变），录制时非 0；减弱动态只是不淡入，
/// 描边照样在（状态不许押在动画上，沿用 `HotKeyRecorderEmphasis` 的同一条规矩）。
enum SettingsRowEmphasis {
    /// 描边不透明度。静置恒 0：这一帧逐像素等于不存在，静置帧基线不动。
    static func recordingStrokeOpacity(isRecording: Bool) -> Double {
        isRecording ? 0.9 : 0
    }

    /// 与录音器自己那圈同宽（`VisualStroke.highlight`）：两边是同一句话的两种范围。
    static func recordingStrokeWidth(isRecording: Bool) -> CGFloat {
        isRecording ? VisualStroke.highlight : 0
    }
}

/// **R412 起从 `private` 放开到 internal**：唯一原因是判据要搭一行**与产品同一棵**的组件帧
/// （真实的 `HotKeyRecorderButton` → 回调 → 行描边）。产品调用点不经过这条可见性变化。
struct HotKeySettingsRow: View {
    @ObservedObject var settings: HotKeySettings
    @Binding var shortcut: HotKeyShortcut
    @State private var isRecording = false
    /// R493：「恢复默认」按钮图标的负向帧缝（产品默认 nil ⇒ 画）。
    @Environment(\.settingsResetButtonIconsForCapture) private var resetButtonIconsForCapture
    private var resetButtonIconsVisible: Bool { resetButtonIconsForCapture ?? true }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(settings.action.title)
                    Text(settings.action.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        // R28：这里原来是 `.lineLimit(1)`。三行说明里前两行放得下，第三行放不下，
                        // 于是**被截断的恰好是信息量最大的那一条**：`HotKeyAction.quickPick.description`
                        // 后半句写的是"默认 ⌃⌥⇧V —— 刻意不是 ⌘⇧V（那是浏览器和编辑器里的粘贴并匹配样式，
                        // 全局抢走会让它们失灵）"，而屏幕上只剩
                        // "在任意应用里呼出浮层，打字筛选后回车直接粘回原应用。…"。
                        // 那句话是审计 §5 F-3 的取舍说明，写进文案就是为了让人看见，结果一个字都没露。
                        //
                        // 三个选项里选了换行：
                        // ① 缩短文案 —— 把要交代的理由删了来迁就一个布局常数，那是为过夹具改产品；
                        // ② `.help()` 折进悬停提示 —— 说明文字的可发现性本来就靠"看得见"，
                        //    而 R24/R27 刚立下的规矩正是"要读的信息不许藏得更深"；
                        // ③ 换行 —— 与**同一个窗口里**其它说明段同一种语言：通用页那段
                        //    "打开后从 Word、Pages…"（:330）本来就是三行，`.fixedSize` 让它长高。
                        //    也就是说这个窗口里同一种文字原本有两套规矩，而被切掉的正好是没套用的是那一套。
                        // 代价：第三行长高，三行不再等高。系统设置里等高从来不是规矩，读得完才是。
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Spacer(minLength: 24)

                HotKeyRecorderView(
                    shortcut: $shortcut,
                    onInvalidShortcut: {
                        settings.recordInvalidShortcut()
                    },
                    onRecordingChange: { isRecording = $0 }
                )
                .frame(width: 128, height: 28)

                HStack(spacing: 0) {
                    Button {
                        settings.reset()
                        shortcut = settings.shortcut
                    } label: {
                        if resetButtonIconsVisible {
                            Label("恢复默认", systemImage: "arrow.counterclockwise")
                        } else {
                            Text("恢复默认")
                        }
                    }
                // R383：快捷键已是默认值时这颗按钮点了不产生任何变化 —— 与 R382 的权重页同一条规矩，
                // 禁用态是它唯一诚实的呈现。判据读的是**整页两态**渲染出的按钮标签墨
                // （`testShortcutResetButtonsAreDisabledWhenShortcutsAreDefault`）。
                .disabled(shortcut == settings.action.defaultShortcut)
                // R388：与权重页同一支样式（标签色过渡，禁用停在可读的 secondary）。
                .buttonStyle(ResetDefaultButtonStyle())
                }
            }
            // 描边**与行内容同边**：横向不扩（一扩就把卡片左沿第一墨列从 5 拉到 3），
            // 纵向也不外扩（R412 的 −2 在 runner 1x 把行距压成 10/9，节奏尺红）。
            .background(
                VisualShape.rounded(VisualRadius.panel)
                    .strokeBorder(Color.accentColor.opacity(
                        SettingsRowEmphasis.recordingStrokeOpacity(isRecording: isRecording)),
                                  lineWidth: SettingsRowEmphasis.recordingStrokeWidth(isRecording: isRecording))
            )
            .animation(MotionCatalog.animation(for: .emphasis), value: isRecording)

            if let message = settings.message {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }
}

// MARK: - Unified Settings Sidebar (matches main window hover style)

/// 捕获夹具用的选中滑移中间态（R414）：产品路径永远是 nil。
struct SettingsSelectionPreview: Equatable {
    let from: SettingsCategory
    let to: SettingsCategory
    let progress: Double
}

private struct SettingsSelectionPreviewKey: EnvironmentKey {
    static let defaultValue: SettingsSelectionPreview? = nil
}

extension EnvironmentValues {
    var settingsSelectionPreview: SettingsSelectionPreview? {
        get { self[SettingsSelectionPreviewKey.self] }
        set { self[SettingsSelectionPreviewKey.self] = newValue }
    }
}

/// 设置侧栏那颗选中胶囊的**几何**（R414）。
///
/// 为什么要有纯计划：中间态要能被夹具**确定地**画一次（与 R411/R412 的取证键同一手法），
/// 而"两行之间走到 0.5"是一个数，不该只存在于 SwiftUI 的插值器里。
/// 真实产品路径仍由 `.animation(value: selectedCategory)` 驱动；夹具只在 progress 处取一帧。
enum SettingsSidebarSelectionPlan {
    /// 行 frame 是整个 `SettingsSidebarRow`（含左右各 6pt 外边距）；旧的行内选中底色
    /// 画在按钮内容框上，等价于行 frame 左右各内缩 6pt。胶囊用同一个矩形，静置帧才逐像素不变。
    static func capsuleRect(rowFrame: CGRect, horizontalInset: CGFloat = 6) -> CGRect {
        CGRect(x: rowFrame.minX + horizontalInset,
               y: rowFrame.minY,
               width: max(0, rowFrame.width - horizontalInset * 2),
               height: max(0, rowFrame.height))
    }

    static func interpolatedCapsuleRect(from: CGRect, to: CGRect, progress: Double) -> CGRect {
        let t = CGFloat(min(1, max(0, progress)))
        return CGRect(x: from.minX + (to.minX - from.minX) * t,
                      y: from.minY + (to.minY - from.minY) * t,
                      width: from.width + (to.width - from.width) * t,
                      height: from.height + (to.height - from.height) * t)
    }
}

private struct SettingsSidebarRowFramesKey: PreferenceKey {
    static let defaultValue: [SettingsCategory: CGRect] = [:]
    static func reduce(value: inout [SettingsCategory: CGRect],
                       nextValue: () -> [SettingsCategory: CGRect]) {
        value.merge(nextValue(), uniquingKeysWith: { $1 })
    }
}

/// 设置窗口左列。
///
/// **R102 起从 `private` 放开到 internal**，唯一原因是判据那边要能拿它搭**与产品同一棵容器树**的
/// 参照臂（BACKLOG 150：runner 上"这扇窗口的卡片没有材质层"，而裸 `GroupBox` 有 ⇒ 成因在容器；
/// 要把容器一层一层加回去二分，就必须用真的那一层，不能用一个长得像的替身）。
/// 这不是产品 API 的扩张：`internal` 只在 `ClipboardHistoryApp` 模块与其测试目标里可见，
/// 对 app 的外部使用者没有任何变化。
struct SettingsSidebarView: View {
    @Binding var selectedCategory: SettingsCategory?
    @Environment(\.settingsSelectionPreview) private var selectionPreview
    @Environment(\.settingsSidebarVersionForCapture) private var versionForCapture
    @Environment(\.settingsSidebarFooterForCapture) private var footerForCapture
    /// R504：设置侧栏身份头的负向帧缝（产品默认 nil ⇒ 画）。
    @Environment(\.settingsSidebarIdentityForCapture) private var settingsSidebarIdentityForCapture
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var rowFrames: [SettingsCategory: CGRect] = [:]

    private var shouldReduce: Bool { reduceMotion || MotionCatalog.motionShouldBeReduced }

    private var footerText: String {
        SettingsSidebarFooterPolicy.resolvedVersionText(override: versionForCapture)
    }

    private var capsuleRect: CGRect? {
        if let preview = selectionPreview,
           let from = rowFrames[preview.from],
           let to = rowFrames[preview.to] {
            return SettingsSidebarSelectionPlan.interpolatedCapsuleRect(
                from: SettingsSidebarSelectionPlan.capsuleRect(rowFrame: from),
                to: SettingsSidebarSelectionPlan.capsuleRect(rowFrame: to),
                progress: preview.progress)
        }
        guard let selectedCategory, let frame = rowFrames[selectedCategory] else { return nil }
        return SettingsSidebarSelectionPlan.capsuleRect(rowFrame: frame)
    }

    var body: some View {
        ZStack(alignment: .topLeading) {
            // 选中胶囊只有**一颗**：它从旧行滑到新行，而不是每行各自淡入淡出。
            // 颜色/矩形与旧的行内选中底一致，静置帧逐像素不变；过程由 `.selection` 驱动。
            if let rect = capsuleRect {
                VisualShape.rounded(VisualRadius.panel)
                    .fill(Color.accentColor.opacity(SelectedInk.opacity(dark: colorScheme == .dark)))
                    .frame(width: rect.width, height: rect.height)
                    .offset(x: rect.minX, y: rect.minY)
                    .allowsHitTesting(false)
            }
            VStack(alignment: .leading, spacing: 0) {
                // R504：主侧栏标题有身份头（时钟图标 + 应用名），设置侧栏只有分类行；
                // 补同一枚身份头，两扇窗口的侧栏顶都有"我在哪"的锚点。
                if settingsSidebarIdentityForCapture ?? true {
                    HStack(spacing: 8) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: VisualFont.title, weight: .semibold))
                            .foregroundStyle(.secondary)
                            .accessibilityHidden(true)
                        Text("时间剪史")
                            .font(.system(size: VisualFont.title, weight: .semibold))
                            .foregroundStyle(.secondary)
                        Spacer()
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 10)
                    .padding(.bottom, 6)
                }
                ForEach(SettingsCategory.allCases) { category in
                    SettingsSidebarRow(
                        category: category,
                        isSelected: selectedCategory == category,
                        action: { selectedCategory = category }
                    )
                    .background(
                        GeometryReader { proxy in
                            Color.clear.preference(
                                key: SettingsSidebarRowFramesKey.self,
                                value: [category: proxy.frame(in: .named("settingsSidebar"))])
                        }
                    )
                }
                // R426：版本行跟在导航行之后（不放到窗口下沿）—— 最小窗里侧栏内容的
                // 理想高度比窗口高，锚到窗口底会把这一行裁在框外；放在行后则在任何高度都可见。
                if footerForCapture != false {
                    SettingsSidebarFooter(text: footerText)
                }
                Spacer()
            }
            .padding(.top, 8)
        }
        .coordinateSpace(name: "settingsSidebar")
        .onPreferenceChange(SettingsSidebarRowFramesKey.self) { rowFrames = $0 }
        .animation(MotionCatalog.animation(for: .selection, reduceMotion: shouldReduce),
                   value: selectedCategory)
    }
}

struct SettingsSidebarRow: View {
    let category: SettingsCategory
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false
    /// 色档自己问（`PressedLabel` / `FilterSegmentButton` / `MarkdownModeButton` 同一条规矩）。
    @Environment(\.colorScheme) private var colorScheme
    /// **取证通道**（R231 / BACKLOG 258）：`EnvironmentValues.hoveredForCapture` 只有捕获夹具会写，
    /// 产品路径上永远是 `nil` ⇒ 真实指针那条 `.onHover` 的路一字未动。
    /// 摘掉 `private` 不是为好看：这一族判据要看渲染出来的画面，而夹具引用不到 `private` 类型
    /// （先例是 `SegmentedFilterPicker` / `GlassPill`，它们本来就是 internal）。
    @Environment(\.hoveredForCapture) private var hoveredForCapture
    /// **画法与动画必须问同一句话**（R275 / D-249 那一族在第二个文件里的复发）：
    /// 下面 `backgroundOpacity` 早就接了取证键，而 `.animation(for: .hover, value:)` 一直直读裸
    /// `isHovered` ⇒ 离屏渲染里 `.onHover` 恒 false，那条淡入的**触发条件**在帧里从来不存在
    /// —— 墨落下了，但没有过程，于是"这一档到底是不是淡进来的"没有任何读数能回答。
    /// 真实指针那条路一字未动：`isHovered` 仍然由 `.onHover` 供。
    private var isHoveredForDrawing: Bool { isHovered || (hoveredForCapture ?? false) }

    private var backgroundOpacity: Double {
        // R414：选中底已经搬到**一颗**滑动胶囊（`SettingsSidebarView`）；这里再画一层会把
        // 静置帧的选中行叠深，也会让"谁在滑"变成两层各演各的。选中行只保留悬停以外的样式。
        guard !isSelected else { return 0 }
        // R231 / BACKLOG 256 的原话是：`selected` 那一格**不接**悬停那条共享换算 —— 它是选中态
        // 不是悬停态，抬量长在悬停上会把"选中的那一行"和"指针所在的那一行"糊成同一档。
        // R260 更正：这条前提被后来的抬量挪走了。亮档下面两级抬到 0.12 / 0.15 之后，
        // 糊成一档的换成了**按下与选中**（0.16 − 0.15 = 0.01 = 2.55/255 < 地板 4/255），
        // 所以选中现在走自己的换算 `SelectedInk`（暗档仍等于令牌原值）。
        guard isHoveredForDrawing else { return 0 }
        return HoverInk.opacity(level: VisualFill.hover, dark: colorScheme == .dark)
    }

    var body: some View {
        Button(action: action) {
            // **R381**：图标与文字分开上色。外观由 `NavigationSplitView` 侧栏材质承载时，
            // `.primary` 在亮档被 vibrancy 解析成白色（本机整页帧：图标 255/255/255 压在 251 的底上，
            // 对比 4/255 ⇒ 等于看不见；同一份 `.primary` 在单行组件帧里是黑的）。
            // `Color(nsColor: .labelColor)` 是**动态系统色**（随外观翻转，不是写死的灰），
            // 它不进 vibrancy 的重映射：亮档现读 76、暗档 232。R443 把**文字**也跟到同一个
            // 动态色：R457/471 的暗档侧栏盲区就是文字那一处（图标 R381 早已修好，文字仍 `.primary`
            // ⇒ 暗档 2x 的离屏帧里整列黑字黑底）。选中仍走 accent。
            Label {
                Text(category.title)
            } icon: {
                Image(systemName: category.icon)
                    .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)
                                                : AnyShapeStyle(Color(nsColor: .labelColor)))
            }
            .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)
                                        : AnyShapeStyle(Color(nsColor: .labelColor)))
                // R122：这里从 `.hierarchical` 换成 `.monochrome`，理由不是审美，是逐行读数。
                // 上一轮装好的永久仪器（`SIDEBAR_ICON_ROW` / `SIDEBAR_ICON_BY_SYMBOL`）在同一批帧上量到：
                //   dark 有墨行=78 无墨行=0 **反侧行=22**，而反侧的两枚恰好是 `wand.and.stars`（推荐）
                //   与 `chart.bar`（统计）—— 同一条 `.primary`、同一档外观、同一列里，
                //   四枚符号解析成亮墨（271–353 px），这两枚解析成 0 亮墨。
                // ⇒ 上面那段注释里"不可见来自离屏管线对语义色的解析，不是产品"这条结论**被这组数推翻了一半**：
                //   如果坏的是"语义色解析"，六枚符号应该一起坏；按符号分开的只能是符号自己的调色板。
                //   `wand.and.stars` / `chart.bar` 正是六枚里仅有的两枚**多色符号**，`.hierarchical`
                //   会保留符号自带的多色调色板（那套色里没有"随深浅色翻转"的语义色），`.monochrome` 才把
                //   整枚符号交回 `.primary`。所以改的是**渲染模式**，不是颜色 —— 原来那条"不许把 .primary
                //   换成固定色"的顾虑仍然成立，这一行也没有换颜色。
                // 判据与验收：`SIDEBAR_ICON_COVERAGE` 的 `反侧行` 必须归 0（本轮同时把它从"只报数"升成会红），
                // 并且要看帧 —— 只有离屏读数说"归 0"是不够的，见 AGENT_UI_AUDIT 第 124 轮。
                .symbolRenderingMode(.monochrome)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .contentShape(VisualShape.rounded(VisualRadius.panel))
        }
        .pressedStyle(in: VisualShape.rounded(VisualRadius.panel), scales: false)
        .background(
            VisualShape.rounded(VisualRadius.panel)
                .fill(Color.primary.opacity(backgroundOpacity))
        )
        .font(.system(size: VisualFont.body, weight: isSelected ? .semibold : .regular))
        .padding(.horizontal, 6)
        .animation(MotionCatalog.animation(for: .hover), value: isHoveredForDrawing)
        .animation(MotionCatalog.animation(for: .selection), value: isSelected)
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

/// 一行可以**自己关掉**的结果文案（R8 / 审计 B-P4 的那半条）。
///
/// 审计的原话是"突然出现、永不清空"。两半分开处理：
/// - "突然" ⇒ 淡入（走目录，reduce-motion 由 `MotionCatalog` 统一退化）；
/// - "永不清空" ⇒ 给一个 × 让用户自己收掉。
/// **刻意不做自动消失**：这三条都是"你刚做的那件事的结果"（导出路径、导入条数、排除增删），
/// 1.1 秒后自己没掉等于把信息拿走 —— 复制成功那种**瞬时回执**才适合自动收回（见 R5 的 A4）。
/// 热图那一节单独观察账本。
///
/// 为什么要这一层：`SettingsView` 不观察 `DailyCopyLedger`（它不是 store 的一部分），
/// 直接把 `ledger.counts` 传下去会得到一张**开页时快照**的图 ——
/// 用户边复制边看着设置页时它不动，那比不画更让人怀疑数据是假的。
/// 统计页那一块。**内部可见而不是 `private`**：胶片探针要在真窗口里驱动它
/// （`MotionFilmstripTests` 的 `heat-first-record` 场景），
/// 而探针一旦自己复制一份"长得很像"的宿主视图，它测的就是替身不是产品 ——
/// 那一族在仓库里记过（第二轮 N-1 的守卫绕开 adapter 直调 engine）。
struct DailyCopyStatsSection: View {
    @ObservedObject var ledger: DailyCopyLedger

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // R101 / BACKLOG 131：这一屏以前是整扇设置窗口里**唯一没有卡片**的一屏 ——
            // 通用 / 快捷键 / 隐私 / 数据 都是"分区标题裸在页面上 + 内容在 `GroupBox` 里"，
            // 而只有这一屏把热图、图例、说明段整块铺在页面底上，中间那条 `Divider()`
            // 压在背景上（R92 逐屏量过：统计 0 张卡片 / 外 1 条线）。
            // **为什么这条值得单独改**：那三条卡片判据（竖向节奏 R95、卡片外几段墨 R99、
            // 横向内缩 R100）的前提都是"这一屏有卡片材质"，没有卡片的屏对它们是
            // `CARD_RHYTHM_DECLINED` —— 于是"这一屏不受这扇窗口的规矩管"这件事**读不出来**，
            // 它一直"通过"。补上卡片之后它第一次被同一颗尺子量到。
            // 标题为什么在**卡片之上**而不是卡片里面：见 `DailyCopyHeatmapView.header` 的注释
            // （整块包进卡片那一版会让这一屏变成全窗口唯一"标题在卡片内"的一屏，
            // 而它自己那条 `CARD_ABOVE` 红当场把这件事报了回来）。
            SettingsPageTitle("每日复制", category: .stats, font: .system(size: VisualFont.title, weight: .semibold))
            GroupBox {
                VStack(alignment: .leading, spacing: 12) {
                    // `today` 也来自账本：见 `DailyCopyLedger.today` 的注释 ——
                    // 一个时刻有两个来源，跨午夜与注入时钟时都会分叉。
                    DailyCopyHeatmapView(counts: ledger.counts, today: ledger.today)
                    if let error = ledger.lastWriteError {
                        // 写盘失败只影响"下次打开还在不在"，不影响这一屏 —— 但必须说出来，
                        // 否则它会悄悄停在几天前，而那正是统计类界面最坏的坏法。
                        Text("统计写入失败：\(error)")
                            .font(.system(size: VisualFont.meta))
                            .foregroundStyle(.secondary)
                    }

                    // 「这张图怎么读」**跟着图一起出现**（R9，离屏帧实测）：空账本那一屏原来是
                    // "还没有可统计的记录 —— 复制几条之后这里会长出一张日历" + 分隔线 +
                    // 五行"一列是一周，一行是一个星期几…" —— 教用户读一张**不在这里**的图，
                    // 与阶段一那条"共 0 次"是同一族（两条互相矛盾的表达同时说话，U-30 缺陷 5）。
                    //
                    // 为什么写在这一层而不是 `SettingsView.statsSection`：**只有这一层观察账本**。
                    // 挂在 `SettingsView.body` 上读到的是"开页那一刻的快照条件"，
                    // 用户复制第一条之后它不会重算 ⇒ 图长出来了、说明却永远不出现（新的一种"变了但界面不说"）。
                    if !ledger.counts.isEmpty {
                        VStack(alignment: .leading, spacing: 16) {
                            Divider()
                            readingGuide
                        }
                        .transition(MotionCatalog.transition(for: .contentFade))
                    }
                }
                // 留白必须落在**材质之内**：`.settingsCardInset()` 是 `padding(.vertical, 7)`，
                // 挂在 `GroupBox` 外面就等于给卡片外面加了一段空隙，而材质自己那 7pt 一分没多。
                // 这不是风格问题 —— 节奏尺当场量出来了：挂外面这一版 `边距=7.0/7.0`，
                // 而其余五张卡片都是 `14.5/14.0`（= GroupBox 自带的 7 + 这 7）。
                // 与 `RecommendationWeightsView` / 快捷键 / 隐私 那五处同一写法。
                .settingsCardInset()
            }
        }
        // 这一条驱动的是**本层那个 if**（说明块 + 分隔线），不是组件内部的两臂 ——
        // 组件自己那条在 `DailyCopyHeatmapView.body` 里，各层驱动各层的子树，
        // 参数都出自 `MotionCatalog`，所以"只有一个作者"这条仍然成立。
        //
        // R11 的实测结论写在这儿，别再被下一次审查误读成"这条没供电"：
        // 胶片探针量到的是**一帧到位**（`heat-first-record`：0.004 / 0.027 / 0.220 / 0.000…），
        // 但把 `animationsEnabled` 关掉再量是**同一个读数** ⇒ 这把尺看不见纯 opacity 的淡入淡出
        // （`cacheDisplay` 抓的是模型树，与 `MOTION_NATIVE` 那条同一族根因）。
        // 所以这条淡入目前的状态是**"源码已接、产物未量"**，不是"已验证"，也不是"没做"。
        // 判据 `testHeatmapFadeIsNotVisibleToThisRuler` 会盯着这件事：
        // 尺子哪天看得见了，它会红，逼着把场景放回真判据里。
        .animation(MotionCatalog.animation(for: .contentFade), value: ledger.counts.isEmpty)
    }

    private var readingGuide: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("这张图怎么读")
                .font(.subheadline)
            Text("一列是一周，一行是一个星期几，右下角是今天。颜色深浅说的是那几天里你复制了多少次，"
                 + "深浅按你自己这段时间的数据算 —— 所以它是「我这阵子忙不忙」的刻度，"
                 + "不是「一天多少次」的刻度。鼠标停在任意一格上会写出那一天。")
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            Text("计数在复制发生的那一刻就记下了：删掉记录、清空历史都不会改写它，"
                 + "所以它比历史列表本身长（保留两年）。暂停采集与被排除的 App 不计数。")
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

/// 一行回执 + 一颗收起的 ×。
///
/// internal 的唯一理由：帧夹具要宿主**产品自己的**这一行（R14）。它以前只由
/// `exportMessage` / `archiveMessage` / `exclusionReceipt` 这些 `@State` 点亮，
/// 而那三个状态在离屏渲染里没人能推 —— 于是这颗 × 与这行字**从来没有进过帧基线**，
/// R13 改它样式时是"源码已接、产物未量"。与 `DailyCopyStatsSection`（R11）同一手法、同一理由：
/// 没有夹具的状态等于没有验收，而宿主替身视图测的是替身。
///
/// **调用点的约定（R42 / D-101 / BACKLOG 63）**：这一行自己挂着 `.transition(.contentFade)`，
/// 而 SwiftUI 只在**外层事务被动画化**时才演它 ⇒ 每个调用点的容器必须带一条
/// `.animation(MotionCatalog.animation(for: .contentFade), value: <决定它出现/消失的那个状态> == nil)`。
/// 这条由 `MotionDriverTests.testEveryReceiptLineCallSiteIsDriven` 按调用点判（不是按文件判 ——
/// 本文件有 9 条动画键，文件级守卫抓不到这里任何一处死声明）。
/// 已知边界：判据只认 `.animation(value:)` 这一族，**用 `withAnimation` 供电会被判成没电**；
/// 要么补上那一种解析，要么把这条约定做成会红的判据 —— 见 BACKLOG 63，别把它当口头规矩。
struct ReceiptLine: View {
    let text: String
    let dismiss: () -> Void

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            Text(text)
                .font(.system(size: VisualFont.meta))
                .foregroundStyle(.secondary)
                .textSelection(.enabled)
                .fixedSize(horizontal: false, vertical: true)
            Button(action: dismiss) {
                Image(systemName: "xmark.circle")
                    .font(.system(size: VisualGlyph.badge))
            }
            .pressedStyle(in: VisualShape.rounded(VisualRadius.control),
                          hoverLevel: VisualFill.controlHover,
                          labelPadding: 4)
            .helpLabel("收起这条提示")
        }
        .transition(MotionCatalog.transition(for: .contentFade))
    }
}


/// R479：设置页标题与侧栏共用同一枚图标 —— 换页后标题不再只是一行字。
struct SettingsPageTitle: View {
    let title: String
    let category: SettingsCategory
    var font: Font = .headline
    @Environment(\.settingsPageTitleIconForCapture) private var pageTitleIconForCapture

    init(_ title: String, category: SettingsCategory, font: Font = .headline) {
        self.title = title
        self.category = category
        self.font = font
    }

    var body: some View {
        HStack(spacing: 8) {
            if pageTitleIconForCapture ?? true {
                Image(systemName: category.icon)
                    .font(font)
                    .foregroundStyle(.secondary)
                    .accessibilityHidden(true)
            }
            Text(title)
                .font(font)
        }
    }
}

/// R479：设置页标题图标的负向帧缝（产品默认 nil ⇒ 画图标）。
struct SettingsPageTitleIconForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsPageTitleIconForCapture: Bool? {
        get { self[SettingsPageTitleIconForCaptureKey.self] }
        set { self[SettingsPageTitleIconForCaptureKey.self] = newValue }
    }
}

/// R486：数据页导出/导入按钮图标的负向帧缝（产品默认 nil ⇒ 画图标）。
struct SettingsDataActionIconsForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsDataActionIconsForCapture: Bool? {
        get { self[SettingsDataActionIconsForCaptureKey.self] }
        set { self[SettingsDataActionIconsForCaptureKey.self] = newValue }
    }
}

/// R489：默认排除项「默认」标记的负向帧缝（产品默认 nil ⇒ 画）。
struct SettingsDefaultExcludedBadgeForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsDefaultExcludedBadgeForCapture: Bool? {
        get { self[SettingsDefaultExcludedBadgeForCaptureKey.self] }
        set { self[SettingsDefaultExcludedBadgeForCaptureKey.self] = newValue }
    }
}

/// R492：开机启动失败回执图标的负向帧缝（产品默认 nil ⇒ 画）。
struct LoginFailureIconForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var loginFailureIconForCapture: Bool? {
        get { self[LoginFailureIconForCaptureKey.self] }
        set { self[LoginFailureIconForCaptureKey.self] = newValue }
    }
}

/// R495：通用页说明字号的负向帧缝（产品默认 nil ⇒ 11pt `meta`）。
struct SettingsHelperFontForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsHelperFontForCapture: Bool? {
        get { self[SettingsHelperFontForCaptureKey.self] }
        set { self[SettingsHelperFontForCaptureKey.self] = newValue }
    }
}

/// R493：「恢复默认」按钮图标的负向帧缝（产品默认 nil ⇒ 画）。
struct SettingsResetButtonIconsForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsResetButtonIconsForCapture: Bool? {
        get { self[SettingsResetButtonIconsForCaptureKey.self] }
        set { self[SettingsResetButtonIconsForCaptureKey.self] = newValue }
    }
}

/// R498：RTF 说明段断行形态的负向帧缝（产品默认 nil ⇒ 用不断开「文本。」的写法）。
struct SettingsRtfHelperCopyForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsRtfHelperCopyForCapture: Bool? {
        get { self[SettingsRtfHelperCopyForCaptureKey.self] }
        set { self[SettingsRtfHelperCopyForCaptureKey.self] = newValue }
    }
}

/// R504：设置侧栏身份头的负向帧缝（产品默认 nil ⇒ 画）。
struct SettingsSidebarIdentityForCaptureKey: EnvironmentKey {
    static let defaultValue: Bool? = nil
}

extension EnvironmentValues {
    var settingsSidebarIdentityForCapture: Bool? {
        get { self[SettingsSidebarIdentityForCaptureKey.self] }
        set { self[SettingsSidebarIdentityForCaptureKey.self] = newValue }
    }
}
