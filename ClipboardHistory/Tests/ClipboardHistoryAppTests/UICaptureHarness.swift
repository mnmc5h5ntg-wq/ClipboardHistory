import AppKit
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 离屏渲染真实视图，产出 PNG 供肉眼审计 —— 不依赖屏幕录制授权，
/// 也不受"后台窗口动画时间线冻结"影响（那两类都会给出假空白帧）。
///
/// 用法：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`
/// 未设置该环境变量时整个套件 skip，不拖慢普通测试。
///
/// 三条防"假证据"的规矩（都来自踩过的坑）：
/// 1. 每帧都量化"未被绘制的像素比例"并打印。`cacheDisplay` 不会画 AppKit
///    滚动视图/分栏的底，未合成前暗色帧会呈现"白底 + 透明"，肉眼看就是
///    "详情区空白"的假缺陷。现在统一铺一层真实窗口底色再写 PNG。
/// 2. 比例超过 95% 直接判失败：那意味着整帧基本没画出来，不能当验收证据。
/// 3. 拍暗色时把 NSApp.appearance 一起改掉。只注入 `colorScheme` 的话，
///    List 这类 AppKit 承载控件仍按 aqua 取色，会拍出"深底黑字"的假不可读帧。
@MainActor
final class UICaptureTests: XCTestCase {
    /// 夹具时间戳的固定参考时刻（账本 R2-19）。
    ///
    /// 以前这里用 `Date()`：行里显示的时间会随真实时钟走，于是**跨分钟连拍两次，
    /// 时钟字符串自己就在变像素** —— 逐帧对比里混进一层与代码无关的差异
    /// （11pt 字号那轮 row 帧 3.3–13% 的差异里就有它）。固定之后，两帧的差异才只反映代码改动。
    static let referenceDate = Date(timeIntervalSince1970: 1_760_000_000)

    private enum CaptureError: Error {
        case noBitmap
        case noPNG
    }

    private var outputDirectory: URL? {
        guard let path = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"], !path.isEmpty else {
            return nil
        }
        let url = URL(fileURLWithPath: path, isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    func testCaptureKeyViews() throws {
        guard let directory = outputDirectory else {
            throw XCTSkip("未设置 CLIPBOARD_HISTORY_UI_SHOTS，跳过离屏渲染")
        }
        var report: [(name: String, transparent: Double)] = []
        for appearance in [NSAppearance.Name.aqua, .darkAqua] {
            let tag = appearance == .darkAqua ? "dark" : "light"
            for fixture in fixtures(appearance: appearance) {
                let file = directory.appendingPathComponent(
                    "\(fixture.name)-\(Int(fixture.size.width))x\(Int(fixture.size.height))-\(tag).png"
                )
                let transparent = try render(fixture, appearance: appearance, to: file)
                report.append((file.lastPathComponent, transparent))
            }
        }

        print("CAPTURED \(report.count) -> \(directory.path)")
        for item in report {
            print("  \(item.name)  transparent=\(String(format: "%.1f", item.transparent * 100))%")
        }

        for item in report where item.transparent > 0.95 {
            XCTFail("\(item.name) 有 \(Int(item.transparent * 100))% 像素未被绘制，判定为捕获失效，不能作为视觉验收证据")
        }
    }

    // MARK: - 夹具（用闭包延迟求值：否则四个 detail 拍到的都是"最后一次选中"）

    struct Fixture {
        let name: String
        let size: NSSize
        /// 布局完成之后、按快门之前跑一次。给"内容要等一次异步刷新才落定"的视图用：
        /// 不 settle 就只能拍到刷新途中的那一帧，而那一帧是不是最终态取决于机器快慢。
        let settle: (() -> Void)?
        let build: () -> AnyView

        init(_ name: String, _ size: NSSize, settle: (() -> Void)? = nil, _ build: @escaping () -> AnyView) {
            self.name = name
            self.size = size
            self.settle = settle
            self.build = build
        }
    }

    private func fixtures(appearance: NSAppearance.Name) -> [Fixture] {
        let store = makePopulatedStore()
        let empty = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let searching = makePopulatedStore()
        searching.perform(.updateSearch("不存在的词"))

        var results: [Fixture] = [
            Fixture("content-with-history", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-min", NSSize(width: 600, height: 440)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-wide", NSSize(width: 1100, height: 800)) { AnyView(ContentView(historyStore: store)) },
            Fixture("content-empty", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: empty)) },
            Fixture("content-no-results", NSSize(width: 750, height: 560)) { AnyView(ContentView(historyStore: searching)) },
        ]

        // 菜单栏面板的内容层。以前这里一直标 NOT-RUN（D-019：整块 NSMenu 离屏画不出材质表面，
        // 97.7% 像素未绘制，会被本文件第 2 条规矩拦下 —— 那层判断本身没错）。
        // 但真正上线的是 macOS 13+ 的 SwiftUI `MenuBarExtra`，它的内容就是一个普通 View
        // （`MenuBarRecommendationsView`），可以和其他夹具一样离屏渲染：字号、层级、间距、
        // 空态文案、脱敏标签都拍得到；**拍不到的仍然是系统菜单的材质与圆角**（那层由系统画）。
        // 可复现性：reason 文案会带"当前在<App 名>"，取自 `effectiveFrontmostApp()`；
        // 测试进程从不 `startMonitoring()` ⇒ `lastFrontmostBundleID` 恒为 nil ⇒ 走"第一条记录的来源 App"，
        // 由夹具固定（Safari），所以这些帧仍可做逐字节比对。
        if #available(macOS 13, *) {
            let recommendationStore = makePopulatedStore()
            recommendationStore.refreshPredictions()
            waitUntil("菜单栏面板需要候选") { !recommendationStore.predictionSuggestionEntries.isEmpty }
            results.append(Fixture("menubar-recommendations", NSSize(width: 320, height: 320), settle: {
                self.waitUntil("推荐刷新要收尾") { !recommendationStore.isRefreshingPredictions }
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: recommendationStore,
                    appDelegate: AppDelegate(historyStore: recommendationStore)
                )))
            })

            // 刷新途中的那一帧：视图 `onAppear` 自己会发起一次刷新，所以不 settle，
            // 并在快门前一瞬**断言它仍在途中** —— 否则这帧的名字就在说谎，
            // 而"名字说正在算、画面上却写着暂无推荐"这种错用肉眼比对很难发现。
            let refreshingStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
            )
            results.append(Fixture("menubar-refreshing", NSSize(width: 320, height: 120), settle: {
                XCTAssertTrue(refreshingStore.isRefreshingPredictions,
                              "这一帧叫「正在整理推荐」，拍的时候刷新必须仍在途中")
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: refreshingStore,
                    appDelegate: AppDelegate(historyStore: refreshingStore)
                )))
            })

            // 算完确实没有推荐：settle 到刷新收尾，必须说"暂无推荐"而不是整段消失。
            let emptyMenuBarStore = HistoryStore(
                clipboardWriter: TestClipboardWriter(),
                persistence: RecordingHistoryPersistence(),
                retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
            )
            results.append(Fixture("menubar-empty", NSSize(width: 320, height: 120), settle: {
                self.waitUntil("空库的预测刷新要收尾") { !emptyMenuBarStore.isRefreshingPredictions }
                XCTAssertTrue(emptyMenuBarStore.predictionSuggestionEntries.isEmpty,
                              "空库不该有候选，否则这帧拍的不是空态")
            }) {
                AnyView(self.menuBarFrame(MenuBarRecommendationsView(
                    historyStore: emptyMenuBarStore,
                    appDelegate: AppDelegate(historyStore: emptyMenuBarStore)
                )))
            })
        }

        // 侧栏脱离分栏器单独拍：实测 NavigationSplitView 的 sidebar 列在离屏
        // cacheDisplay 下不跟随强制暗色（同一帧里详情列是白字、侧栏列是黑字），
        // 所以 content-* 帧只能用来核对几何与布局，颜色验收看 sidebar-*。
        let multiSelected = makePopulatedStore()
        multiSelected.perform(.selectOnly(multiSelected.entries[0]))
        multiSelected.perform(.toggleSelection(multiSelected.entries[1]))
        multiSelected.perform(.toggleSelection(multiSelected.entries[2]))
        let favorited = makePopulatedStore()
        favorited.perform(.toggleFavorite(favorited.entries[0]))
        favorited.perform(.updateFilter(.favorites))

        results.append(Fixture("sidebar-history", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: store)))
        })
        results.append(Fixture("sidebar-multi-select", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: multiSelected)))
        })
        results.append(Fixture("sidebar-favorites", NSSize(width: 300, height: 520)) {
            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: favorited)))
        })
        results.append(Fixture("sidebar-no-results", NSSize(width: 300, height: 520)) {            AnyView(self.sidebarFrame(HistorySidebarView(historyStore: searching)))
        })

        for entry in store.entries.prefix(4) {            let captured = entry
            results.append(Fixture("row-\(rowKind(captured))", NSSize(width: 300, height: 74)) {
                AnyView(self.rowFrame(HistoryRowButton(
                    entry: captured, copyAction: {}, favoriteAction: {}
                )))
            })
        }

        // 行首星标两个状态各拍一张。以前这颗星在未收藏时是 `.clear`（等于这个控件不存在），
        // 现在它是真按钮，两种状态都必须看得见 —— 这条帧就是那件事的证据。
        let starTarget = store.entries[0]
        let starOn = starTarget.updating(timestamp: starTarget.timestamp, isFavorite: true)
        let starOff = starTarget.updating(timestamp: starTarget.timestamp, isFavorite: false)
        results.append(Fixture("row-favorite-on", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starOn, copyAction: {}, favoriteAction: {}
            )))
        })
        results.append(Fixture("row-favorite-off", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starOff, copyAction: {}, favoriteAction: {}
            )))
        })

        results.append(Fixture("row-pinned-on", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starTarget.updating(isPinned: true), copyAction: {}, favoriteAction: {}
            )))
        })
        results.append(Fixture("row-pinned-off", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: starTarget.updating(isPinned: false), copyAction: {}, favoriteAction: {}
            )))
        })

        // 图片**文件**条目带缩略图的一行（用户报的缺陷：详情区看得到图，列表里只有文档符号）。
        // 这条帧存在的意义是：行首视觉列"有缩略图就用图"这件事从此有像素可查，
        // 不再只能靠真机眼睛看。PDF/多文件那两条仍然没有缩略图，保持文档符号是对的。
        let fileThumb = try! makeStoredImage(color: .systemIndigo, size: NSSize(width: 200, height: 150))
        let fileWithThumb = ClipboardEntry(
            content: .file(URL(fileURLWithPath: "/Users/tester/Desktop/board-icon-fullbleed.png")),
            timestamp: Self.referenceDate.addingTimeInterval(-60),
            thumbnail: fileThumb,
            sourceURL: URL(fileURLWithPath: "/Users/tester/Desktop/board-icon-fullbleed.png"),
            sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        )
        results.append(Fixture("row-file-thumb", NSSize(width: 300, height: 74)) {
            AnyView(self.rowFrame(HistoryRowButton(
                entry: fileWithThumb, copyAction: {}, favoriteAction: {}
            )))
        })

        // 每个详情都用"重建同一份数据 + 按序号选中"，因为重建会生成新的 UUID
        for (index, entry) in store.entries.prefix(4).enumerated() {
            let kind = rowKind(entry)
            results.append(Fixture("detail-\(index)-\(kind)", NSSize(width: 720, height: 520)) {
                let target = self.makePopulatedStore(selectingIndex: index)
                return AnyView(DetailView(historyStore: target))
            })
        }

        // 一颗浮层药丸一张帧。以前两张挤在 200pt 高的框里（四颗按钮 + 分隔线 + padding 实际
        // 需要 ~187pt，加上 32pt padding 就被裁掉了），加了固定按钮后更放不下 ——
        // 被裁的帧会让人误判"按钮少了"，所以一种状态一帧，高度按内容给足。
        // 搜索命中高亮 + 可读行长（审计 §4 U-4）。
        // 这一帧存在的意义是把两件事变成像素：正文列被限制在一个可读宽度内、
        // 以及当前搜索词在正文里真的被涂了底色。判据在 `Round3DetailTypographyTests` 里，
        // 它先钉住夹具前提（确有这条含"视觉验收"的条目，且设了搜索词之后它仍是选中项）。
        results.append(Fixture("detail-text-highlight", NSSize(width: 720, height: 520)) {
            let target = self.makePopulatedStore(selectingIndex: nil)
            if let hit = target.entries.first(where: { $0.shortPreview.contains("视觉验收") }) {
                target.perform(.selectOnly(hit))
                target.perform(.updateSearch("视觉"))
            }
            return AnyView(DetailView(historyStore: target))
        })

        results.append(Fixture("glass-pill", NSSize(width: 120, height: 232)) {
            AnyView(
                GlassPill(isFavorite: false, favoriteAction: {},
                          isPinned: false, pinAction: {},
                          copyAction: {}, deleteAction: {})
                    .padding(16)
                    .frame(width: 120, height: 232)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        results.append(Fixture("glass-pill-states", NSSize(width: 120, height: 232)) {
            AnyView(
                GlassPill(isFavorite: true, favoriteAction: {},
                          isPinned: true, pinAction: {},
                          copyAction: {}, deleteAction: {})
                    .padding(16)
                    .frame(width: 120, height: 232)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        results.append(Fixture("search-field", NSSize(width: 320, height: 96)) {
            AnyView(
                VStack(spacing: 8) {
                    SearchField(text: .constant(""))
                    SearchField(text: .constant("搜索内容"))
                }
                .padding(12)
                .frame(width: 320, height: 96)
                .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        results.append(Fixture("empty-state", NSSize(width: 320, height: 160)) {
            AnyView(
                EmptyStateView(systemName: "doc.on.clipboard", title: "选择一条记录查看详情")
                    .frame(width: 320, height: 160)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        let weightsStore = store.weightsStore
        results.append(Fixture("weights", NSSize(width: 520, height: 560)) {
            AnyView(
                RecommendationWeightsView(store: weightsStore)
                    .padding(20)
                    .frame(width: 520, height: 560)
                    .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        // 设置页：5 个分类逐个拍。分类是 SettingsView 的私有 @State，
        // 离屏窗口又不会建无障碍树（试过：BFS 只能走到根节点），
        // 所以用 initialCategory 注入，而不是靠"点一下"。
        for category in SettingsCategory.allCases {
            results.append(Fixture("settings-\(category.rawValue)", NSSize(width: 720, height: 540)) {
                AnyView(self.makeSettingsView(store: store, initialCategory: category))
            })
        }
        results.append(Fixture("settings-min", NSSize(width: 640, height: 440)) {
            AnyView(self.makeSettingsView(store: store))
        })

        // R-13/R-02 的提示条：既拍组件本身，也拍它插进 ContentView 之后
        // 会不会把 NavigationSplitView 的布局挤坏。
        let pasteFailureText = "系统未授权本 App 控制「System Events」，无法自动粘贴。请在「系统设置 → 隐私与安全性 → 自动化」里允许后重试；记录本身已复制到剪贴板，可手动粘贴。"
        let noticeStore = makePopulatedStore()
        noticeStore.reportPasteFailure(pasteFailureText)
        results.append(Fixture("content-with-notice", NSSize(width: 750, height: 560)) {
            AnyView(ContentView(historyStore: noticeStore))
        })
        results.append(Fixture("notice-banner", NSSize(width: 560, height: 170)) {
            AnyView(
                VStack(spacing: 12) {
                    NoticeBanner(message: "主存档无法读取，已从备份恢复 12 条记录；损坏原件保留为 history.corrupt-1.json。",
                                 tone: .warning, onDismiss: {})
                    NoticeBanner(message: pasteFailureText, tone: .error, onDismiss: {})
                }
                .padding(12)
                .frame(width: 560, height: 170)
                .background(Color(nsColor: .windowBackgroundColor))
            )
        })

        return results
    }

    private func sidebarFrame<V: View>(_ view: V) -> some View {
        view
            .frame(width: 300, height: 520, alignment: .top)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 单行夹具的外框。拍的是 `HistoryRowButton`（带星标与悬停底色的那一层）而不是裸内容，
    /// 这样行上新增的可点控件会真的进帧。
    private func rowFrame<V: View>(_ view: V) -> some View {
        view
            .frame(width: 300, height: 74, alignment: .leading)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 菜单栏面板的离屏外框。真实面板由系统给宽度和材质，这里只固定宽度并铺一层窗口底色，
    /// 让内容层的排版与对比度可测；材质本身不在这帧的责任范围内。
    private func menuBarFrame<V: View>(_ view: V) -> some View {
        view
            .padding(.vertical, 6)
            .frame(width: 320, alignment: .topLeading)
            .background(Color(nsColor: .windowBackgroundColor))
    }

    /// 等异步预测落地。超时是**失败**而不是"那就拍没候选的帧"：
    /// 后者会让"有推荐"这一帧在退化时静默变成"暂无推荐"，像素仍然合法、缺陷却被吞掉。
    private func waitUntil(_ description: String, timeout: TimeInterval = 5.0, condition: @MainActor () -> Bool) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立，这一帧不能拍")
    }

    private func makeSettingsView(store: HistoryStore, initialCategory: SettingsCategory? = .shortcuts) -> some View {
        SettingsView(
            showMainWindowHotKeySettings: HotKeySettings(action: .showMainWindow),
            repeatCopyHotKeySettings: HotKeySettings(action: .repeatCopy),
            loginItemSettings: LoginItemSettings(manager: FakeLoginItemManager(isSupported: true, isEnabled: false)),
            contextPreferences: ContextPreferenceSettings(),
            weightsStore: store.weightsStore,
            feedbackStore: store.feedbackStore,
            clearHistoryAction: {},
            initialCategory: initialCategory
        )
    }

    private func rowKind(_ entry: ClipboardEntry) -> String {
        switch entry.content {
        case .text: return "text"
        case .image: return "image"
        case .file: return "file"
        case .files: return "files"
        }
    }

    /// internal 是刻意的：`detail-text-highlight` 这类夹具的**前提**需要被另一套用例断言
    /// （夹具里到底有没有那条含"视觉验收"的正文、设了搜索词之后选中项有没有换人）。
    /// 前提不成立时帧是白的或量的不是命中 —— 那种帧看着像证据，其实什么都没说。
    func makePopulatedStore(selectingIndex index: Int? = nil) -> HistoryStore {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
        let image = try! makeStoredImage(color: .systemTeal, size: NSSize(width: 240, height: 140))
        store.add(ClipboardIntake.Entry(
            content: .text("这是一段用于视觉验收的普通文本记录，包含足够长度以便观察截断与换行表现 abcdefghijklmnop"),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
        ), timestamp: Self.referenceDate.addingTimeInterval(-30))
        store.add(ClipboardIntake.Entry(
            content: .image(image), thumbnail: image, sourceUTIs: ["public.png"],
            sourceAppBundleID: "com.apple.Preview", sourceAppName: "预览"
        ), timestamp: Self.referenceDate.addingTimeInterval(-120))
        store.add(ClipboardIntake.Entry(
            content: .file(URL(fileURLWithPath: "/Users/tester/Desktop/合同 终版 v3.pdf")),
            thumbnail: nil, sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        ), timestamp: Self.referenceDate.addingTimeInterval(-300))
        store.add(ClipboardIntake.Entry(
            content: .files([
                URL(fileURLWithPath: "/Users/tester/Downloads/IMG_0201.HEIC"),
                URL(fileURLWithPath: "/Users/tester/Downloads/IMG_0202.HEIC"),
                URL(fileURLWithPath: "/Users/tester/Downloads/说明.md"),
            ]),
            thumbnail: nil, sourceUTIs: ["public.file-url"],
            sourceAppBundleID: "com.apple.finder", sourceAppName: "访达"
        ), timestamp: Self.referenceDate.addingTimeInterval(-600))
        store.add(ClipboardIntake.Entry(
            content: .text("ghp_" + String(repeating: "A", count: 36)),
            thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Terminal", sourceAppName: "终端"
        ), timestamp: Self.referenceDate.addingTimeInterval(-900))
        if let index, index < store.entries.count {
            store.perform(.selectOnly(store.entries[index]))
        }
        return store
    }

    // MARK: - 渲染

    private func render(
        _ fixture: Fixture,
        appearance: NSAppearance.Name,
        to file: URL
    ) throws -> Double {
        let size = fixture.size
        // 放进真实（离屏）窗口：裸 NSHostingView 没有 window 时 SwiftUI 的
        // GeometryReader / maxWidth 会退化，整块内容被压到左下角。
        _ = NSApplication.shared
        // 必须同时改"进程外观"：List 这类由 AppKit 承载的控件，其嵌套 hosting view
        // 解析颜色时看的是 NSApp.effectiveAppearance，而不是我们注入的 colorScheme。
        // 只注入 colorScheme 会拍出"深色底 + 黑色列表文字"的假不可读帧。
        let previousApplicationAppearance = NSApp.appearance
        NSApp.appearance = NSAppearance(named: appearance)
        defer { NSApp.appearance = previousApplicationAppearance }

        let window = NSWindow(
            contentRect: NSRect(origin: .zero, size: size),
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.appearance = NSAppearance(named: appearance)
        window.titlebarAppearsTransparent = true
        // 暗色必须同时注入 SwiftUI 的 colorScheme：只设 window.appearance 时
        // 子树仍可能按浅色解析（第一版捕获就把设置页拍成"半明半暗"的假帧）。
        let themed = fixture.build().environment(\.colorScheme, appearance == .darkAqua ? .dark : .light)
        let host = NSHostingView(rootView: themed)
        host.frame = NSRect(origin: .zero, size: size)
        host.autoresizingMask = [.width, .height]
        window.contentView = host
        window.setContentSize(size)
        window.layoutIfNeeded()
        host.layoutSubtreeIfNeeded()

        // 内容要等一次异步刷新才落定的夹具在这里 settle（会转 runloop）。
        // 放在"关 caret"之前：转完 runloop 可能装出新的 field editor，必须让后面的静默与重排照常生效。
        fixture.settle?()

        // 拍帧前先把插入点 caret 清掉：field editor 的光标是**闪烁**的，
        // 同一份代码连拍两次会因此出现最大 251 的通道差（实测：亮色 content 帧 x≈262 处
        // 一条约 100 像素高的竖线时有时无，30/58 帧都受这层噪声影响）。
        // 噪声在，"改动前后逐帧对比"就没有判别力 —— 所以先让窗口交出第一响应者，
        // 再递归把子树里所有 NSTextView 的插入点关掉。
        window.makeFirstResponder(nil)
        Self.silenceCarets(in: host)
        host.layoutSubtreeIfNeeded()

        guard let contentView = window.contentView else {
            throw XCTSkip("窗口没有 contentView（\(file.lastPathComponent)）")
        }
        let bounds = contentView.bounds
        // 不要手工改 rep.size：bitmapImageRepForCachingDisplay 已按 backing scale 建好尺寸，
        // 改它会让内容只画进 1/4 画面（我第一次拍到的"大片空白"就是这个假象）。
        guard let rep = contentView.bitmapImageRepForCachingDisplay(in: bounds) else {
            throw XCTSkip("无法创建位图缓存（\(file.lastPathComponent)）")
        }
        // 关键：cacheDisplay 期间必须把 appearance 设为"当前绘制外观"，
        // 否则只有 window 自身变暗、SwiftUI 子树仍按 aqua 解析颜色，
        // 会拍出"半明半暗"的假帧（第一次拍设置页就踩到了）。
        if #available(macOS 11.0, *) {
            window.appearance?.performAsCurrentDrawingAppearance {
                contentView.cacheDisplay(in: bounds, to: rep)
            }
        } else {
            NSAppearance.current = window.appearance
            contentView.cacheDisplay(in: bounds, to: rep)
            NSAppearance.current = nil
        }

        let (data, transparent) = try flattenedPNG(from: rep, appearance: appearance)
        try data.write(to: file)
        return transparent
    }

    /// 递归关掉子树里所有文本视图的插入点（含 `NSTextField` 的 field editor）。
    /// 只 `makeFirstResponder(nil)` 不够：SwiftUI 包着的 `NSTextField` 可能已经装好了 field editor，
    /// 而闪烁由定时器驱动，两次拍摄落在闪/不闪的两拍上就会出现整条竖线的差异。
    /// 注意 `shouldDrawInsertionPoint` 是只读的，所以用"把插入点画成透明"这一条路径。
    private static func silenceCarets(in view: NSView) {
        if let textView = view as? NSTextView {
            textView.insertionPointColor = .clear
            textView.needsDisplay = true
        }
        if let textField = view as? NSTextField, let editor = textField.currentEditor() as? NSTextView {
            editor.insertionPointColor = .clear
            editor.needsDisplay = true
        }
        view.subviews.forEach { silenceCarets(in: $0) }
    }

    /// 量出"没被画出来的像素"比例，并把帧铺到真实窗口底色上。
    /// 不铺底的话，暗色帧里未绘制的区域会被看图器合成成白色，
    /// 于是"白底 + 白字"的详情区看起来像整块空白（真实假缺陷来源）。
    private func flattenedPNG(from rep: NSBitmapImageRep, appearance: NSAppearance.Name) throws -> (Data, Double) {
        guard let source = rep.cgImage else { throw CaptureError.noBitmap }
        let width = source.width
        let height = source.height
        let rect = CGRect(x: 0, y: 0, width: width, height: height)
        let space = CGColorSpace(name: CGColorSpace.sRGB) ?? CGColorSpaceCreateDeviceRGB()
        let contextInfo = CGImageAlphaInfo.premultipliedLast.rawValue

        func makeContext() -> CGContext? {
            CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                      bytesPerRow: width * 4, space: space, bitmapInfo: contextInfo)
        }

        // 1) 探针：只画内容，空着的地方 alpha 仍是 0
        var transparentFraction = 0.0
        if let probe = makeContext() {
            probe.draw(source, in: rect)
            if let base = probe.data {
                let bytes = base.bindMemory(to: UInt8.self, capacity: width * height * 4)
                var clear = 0
                var total = 0
                var y = 0
                while y < height {
                    var x = 0
                    let row = y * width * 4
                    while x < width {
                        total += 1
                        if bytes[row + x * 4 + 3] < 8 { clear += 1 }
                        x += 1
                    }
                    y += 1
                }
                transparentFraction = Double(clear) / Double(max(total, 1))
            }
        }

        // 2) 合成：铺一层该外观下的窗口底色
        guard let out = makeContext() else { throw CaptureError.noBitmap }
        out.setFillColor(windowBackgroundColor(for: appearance))
        out.fill(rect)
        out.draw(source, in: rect)
        guard let flat = out.makeImage() else { throw CaptureError.noBitmap }
        guard let data = NSBitmapImageRep(cgImage: flat).representation(using: .png, properties: [:]) else {
            throw CaptureError.noPNG
        }
        return (data, transparentFraction)
    }

    private func windowBackgroundColor(for appearance: NSAppearance.Name) -> CGColor {
        var resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
        if #available(macOS 11.0, *) {
            NSAppearance(named: appearance)?.performAsCurrentDrawingAppearance {
                resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
            }
        } else {
            let previous = NSAppearance.current
            NSAppearance.current = NSAppearance(named: appearance)
            resolved = NSColor.windowBackgroundColor.usingColorSpace(.sRGB) ?? .windowBackgroundColor
            NSAppearance.current = previous
        }
        return resolved.cgColor
    }
}
