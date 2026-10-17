import AppKit
import Combine

@MainActor
final class MenuBarController: NSObject, NSMenuDelegate {
    typealias CommandHandler = (AppCommand) -> Void

    /// 菜单栏那颗图标在**两棵表面上必须是同一个符号**（R110 / BACKLOG 164）。
    ///
    /// macOS 13+ 走 `MenuBarExtra(_, systemImage:)`，12 走下面 `makeStatusBarIcon()`
    /// 里的 `NSImage(systemSymbolName:)`。以前 13+ 用 SF Symbol `clipboard`、
    /// 12 用一段手写 `NSBezierPath`（body 10×13.5、clip 5.6×2.8、三条 1.6pt 的线），
    /// 于是"同一个入口在两台机器上长得不一样"，而且 12 上那颗**不是系统素材**
    /// —— 与相邻菜单栏图标的笔画粗细/圆角/视觉重心都对不上。
    /// 名字只在这里写一次，两个调用点都引用它；一致性由
    /// `MotionFilmstripTests.testMenuBarGlyphIsOneSymbolAcrossBothSurfaces` 钉
    /// （源码两格 + 运行时逐像素那一格）。
    static let statusSymbolName = "clipboard"

    /// 165 的那根线：菜单开着时，异步刷新落地要有人重填。
    /// 只留一份 ⇒ 重复 attach 会顶掉旧的（不攒订阅）。
    private var refreshBridge: AnyCancellable?

        private var statusItem: NSStatusItem?
    private var commandHandler: CommandHandler?
    private var pasteHandler: ((HistoryStore.Entry) -> Void)?
    weak var historyStore: HistoryStore?

    func configure(
        commandHandler: @escaping CommandHandler,
        historyStore: HistoryStore? = nil,
        pasteHandler: ((HistoryStore.Entry) -> Void)? = nil
    ) {
        LifecycleDebugLogger.log("MenuBarController.configure called")
        self.commandHandler = commandHandler
        self.historyStore = historyStore
        self.pasteHandler = pasteHandler

        if #available(macOS 13, *) {
            LifecycleDebugLogger.log("MenuBarController.configure skipped NSStatusItem on macOS 13+")
            logStatusItemState(context: "MenuBarController.configure macOS 13+")
            return
        }

        installStatusItemIfNeeded()
        logStatusItemState(context: "after MenuBarController.configure")
    }

    private func installStatusItemIfNeeded() {
        LifecycleDebugLogger.log("installStatusItemIfNeeded called statusItem nil=\(statusItem == nil)")
        guard statusItem == nil else {
            logStatusItemState(context: "installStatusItemIfNeeded existing")
            return
        }

        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        let image = makeStatusBarIcon()
        item.button?.image = image
        item.button?.imagePosition = .imageOnly
        item.button?.toolTip = "时间剪史"
        item.menu = makeMenu()
        statusItem = item
        LifecycleDebugLogger.log("NSStatusItem created")
        logStatusItemState(context: "after installStatusItemIfNeeded")
    }

    private func makeMenu() -> NSMenu {
        LifecycleDebugLogger.log("makeMenu called")
        let menu = NSMenu()
        menu.delegate = self
        // 165：`populate` 是同步的，而 `menuWillOpen` 里发起的刷新是异步的 ⇒
        // 只在这两处填，菜单会一直挂着「正在整理推荐…」。把"算完了"接回这张菜单。
        attachLiveRefresh(to: menu, store: historyStore)
        populate(menu)
        LifecycleDebugLogger.log("menu bound itemCount=\(menu.items.count)")
        return menu
    }

    func menuWillOpen(_ menu: NSMenu) {
        historyStore?.refreshPredictions()
        populate(menu)
    }

    /// 不是 private：审计第二轮 09-08 指出"菜单内容只能靠 `menuLabel` 单测间接覆盖，`populate` 本身没有测试"。
    /// 放宽到 internal 让 `MenuBarPopulationTests` 能直接喂一个 store 进来看菜单项，
    /// 而不是把整套逻辑复制进测试。行为本身没变。
    func populate(_ menu: NSMenu) {
        menu.removeAllItems()

        let titleItem = NSMenuItem(title: "时间剪史", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        // 猜你要粘贴
        if let store = historyStore, !store.predictionSuggestionEntries.isEmpty {
            menu.addItem(.separator())
            let headerItem = NSMenuItem(title: "猜你要粘贴", action: nil, keyEquivalent: "")
            headerItem.isEnabled = false
            headerItem.attributedTitle = NSAttributedString(
                string: "猜你要粘贴",
                // 10pt + tertiary 低于 HIG 对菜单文字的下限，且菜单里本该最多用到 .secondary
                // （审计第二轮 1.2 / R2-13）。与 macOS 13 的 MenuBarRecommendationsView 保持同一套字号。
                attributes: [.font: NSFont.systemFont(ofSize: VisualFont.meta, weight: .semibold),
                             .foregroundColor: NSColor.secondaryLabelColor]
            )
            menu.addItem(headerItem)

            for entry in store.predictionSuggestionEntries.prefix(3) {
                let reason = store.predictionReasonByEntryID[entry.id] ?? ""
                let item = NSMenuItem(
                    title: "",
                    action: #selector(selectRecommendationFromMenu(_:)),
                    keyEquivalent: ""
                )
                item.representedObject = entry.id
                let title = NSMutableAttributedString(string: EntryPresentation.menuLabel(for: entry), attributes: [
                    .font: NSFont.systemFont(ofSize: VisualFont.body)
                ])
                if !reason.isEmpty {
                    title.append(NSAttributedString(string: "\n\(reason)", attributes: [
                        .font: NSFont.systemFont(ofSize: VisualFont.meta),
                        .foregroundColor: NSColor.secondaryLabelColor
                    ]))
                }
                item.attributedTitle = title
                menu.addItem(item)
            }

            // "都不是我想要的" 按钮
            menu.addItem(.separator())
            let dismissItem = NSMenuItem(
                title: "都不是我想要的",
                action: #selector(dismissAllRecommendationsFromMenu),
                keyEquivalent: ""
            )
            dismissItem.attributedTitle = NSAttributedString(
                string: "都不是我想要的",
                attributes: [.foregroundColor: NSColor.systemBlue]
            )
            menu.addItem(dismissItem)
        } else if let store = historyStore {
            // 没有推荐时也要说一句话：旧实现在这种情况下整段静默消失，用户分不清
            // "算过了没有结果"和"这块坏了"（审计第二轮 R2-09 / 1.8）。
            // 但"还在算"与"算完确实没有"是两回事 —— 菜单是同步构建的，而刷新是异步的，
            // 不区分就会在每次打开时先误报一句"暂无推荐"。
            // 与 macOS 13 的 MenuBarRecommendationsView 用同一套文案与同一档字号。
            let placeholder = store.isRefreshingPredictions ? "正在整理推荐…" : "暂无推荐"
            menu.addItem(.separator())
            let emptyItem = NSMenuItem(title: placeholder, action: nil, keyEquivalent: "")
            emptyItem.isEnabled = false
            emptyItem.attributedTitle = NSAttributedString(
                string: placeholder,
                attributes: [.font: NSFont.systemFont(ofSize: VisualFont.meta),
                             .foregroundColor: NSColor.secondaryLabelColor]
            )
            menu.addItem(emptyItem)
        }

        menu.addItem(.separator())
        AppCommandCatalog.menuBarCommands.filter { $0 != .quit }.forEach { command in
            menu.addItem(menuItem(for: command))
        }
        menu.addItem(.separator())
        menu.addItem(menuItem(for: .quit))

        menu.items.forEach { $0.target = self }
    }

    private func menuItem(for command: AppCommand) -> NSMenuItem {
        let item = NSMenuItem(
            title: command.title,
            action: selector(for: command),
            keyEquivalent: command.keyEquivalent
        )
        item.keyEquivalentModifierMask = command.keyModifiers
        return item
    }

    @objc private func selectRecommendationFromMenu(_ sender: NSMenuItem) {
        guard let entryID = sender.representedObject as? UUID else { return }
        guard let entry = historyStore?.entries.first(where: { $0.id == entryID }) else { return }
        historyStore?.perform(.recordRecommendationAccepted(entryID))
        pasteHandler?(entry)
    }

    private func selector(for command: AppCommand) -> Selector {
        switch command {
        case .showMainWindow:
            return #selector(showMainWindowFromMenu)
        case .showSettings:
            return #selector(showSettingsFromMenu)
        case .refreshHistory:
            return #selector(refreshHistoryFromMenu)
        case .clearHistory:
            return #selector(confirmAndClearHistoryFromMenu)
        case .showQuickPick:
            // 菜单项与全局快捷键共用同一个 `AppCommand.showQuickPick`，
            // 于是两条入口是同一段代码 —— 不开第二条粘贴/显示路径。
            return #selector(quickPickFromMenu)
        case .dismissAllRecommendations:
            return #selector(dismissAllRecommendationsFromMenu)
        case .quit:
            return #selector(quitFromMenu)
        }
    }

    /// 状态项那张图。**不是 private**：macOS 12 那棵分支在本机（13+）永远不会执行，
    /// 帧要拍到这颗图标只能由夹具直接来要这张图 —— 与 `populate` 同一条先例
    /// （审计第二轮 09-08：拿不到的表面不是"不能判"，是要给判据留一个入口）。
    /// 这张图**不经过** `NSStatusItem`，所以材质、圆角、点击高亮仍然拍不到，
    /// 拍得到的是素材本身（笔画、留白、是否出框）。
    func makeStatusBarIcon() -> NSImage {
        // 首选系统符号：与 13+ 的 `MenuBarExtra` 同一个 symbolName ⇒ 同一个素材、
        // 同一套笔画权重（与相邻菜单栏图标对齐），模板渲染由系统按明暗档染色。
        if let symbol = NSImage(systemSymbolName: Self.statusSymbolName,
                               accessibilityDescription: "时间剪史") {
            symbol.isTemplate = true
            // 沿用这棵树一直占的那一格 18×18：改尺寸会把"换素材"变成"改几何"，
            // 两件事要能分开归因（帧里的墨包围盒会替我盯着有没有出框）。
            symbol.size = NSSize(width: 18, height: 18)
            return symbol
        }
        // 只有系统符号拿不到时才走（deployment target 是 12，SF Symbols 在 11+ 就有；
        // 这一支是"别把菜单栏留空"的兜底，不是第二条设计）。
        return Self.drawnFallbackIcon()
    }

    /// 兜底那颗手画的剪贴板。**默认路径不画它**（上面拿到符号就直接返回）。
    private static func drawnFallbackIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size, flipped: false) { rect in
            NSColor.black.setStroke()
            NSColor.black.setFill()

            // Clipboard body
            let bodyRect = NSRect(x: 4, y: 2, width: 10, height: 13.5)
            let bodyPath = NSBezierPath(roundedRect: bodyRect, xRadius: 2, yRadius: 2)
            bodyPath.lineWidth = 1.6
            bodyPath.stroke()

            // Clip at top
            let clipRect = NSRect(x: 6.2, y: 14, width: 5.6, height: 2.8)
            let clipPath = NSBezierPath(roundedRect: clipRect, xRadius: 1.3, yRadius: 1.3)
            clipPath.lineWidth = 1.6
            clipPath.stroke()

            // Text lines
            let lineWidth: CGFloat = 1.3
            let lineLeft: CGFloat = 6.2
            let lineRight: CGFloat = 11.8
            for y in stride(from: 11.5, through: 4, by: -3.5) {
                let line = NSBezierPath()
                line.move(to: NSPoint(x: lineLeft, y: y))
                line.line(to: NSPoint(x: lineRight, y: y))
                line.lineWidth = lineWidth
                line.stroke()
            }

            return true
        }
        image.isTemplate = true
        image.accessibilityDescription = "时间剪史"
        return image
    }

    /// 把「刷新落地」接到这张菜单上（BACKLOG 165）。
    ///
    /// **不是 private**：macOS 12 那棵分支在本机（13+）永远不执行，判据只能自己造一张
    /// `NSMenu` 喂进来问同一件事 —— 与 `populate` / `makeStatusBarIcon` 同一条先例。
    /// 接法选「订阅刷新收尾」而不是 `menuNeedsUpdate:`：后者只在**要显示之前**触发，
    /// 而 165 要修的正是"菜单已经开着、结果后到"那一格（`menuWillOpen` 已经覆盖了
    /// "下次打开是新的"，再加一条 menuNeedsUpdate 等于把同一个洞补两遍）。
    func attachLiveRefresh(to menu: NSMenu, store: HistoryStore?) {
        guard let store = store else { refreshBridge = nil; return }
        // 只跟「还算不算完」这一件事：`true` 那一趟什么都不做，落回 `false` 才重填。
        // `removeDuplicates()` 是为了"同一代里被写两次"不重填两遍。
        //
        // **为什么必须 `receive(on: .main)` 而不是在 sink 里直接填**（R111 实测出来的那一格）：
        // `HistoryStore` 收尾是在同一个 `MainActor.run` 里**先**置 `isRefreshingPredictions = false`、
        // **后**才写 `predictionSuggestionEntries`（`HistoryStore.swift:252-260`），
        // 而 `@Published` 的 sink 是同步的 ⇒ 直接填会读到"算完了但候选还是空"，
        // 菜单会从「正在整理推荐…」当场翻成「暂无推荐」—— 那是**另一种**假话，比挂着更坏。
        // 换到下一拍主线程，那三行写都落完了才重填。
        refreshBridge = store.$isRefreshingPredictions
            .removeDuplicates()
            .receive(on: DispatchQueue.main)
            .sink { [weak self, weak menu, weak store] refreshing in
                guard let self = self, let menu = menu, let store = store else { return }
                guard !refreshing, store.isRefreshingPredictions == false else { return }
                self.populate(menu)
            }
    }

    func logStatusItemState(context: String) {
        LifecycleDebugLogger.log(
            "StatusItem state context='\(context)' " +
            "exists=\(statusItem != nil) " +
            "buttonExists=\(statusItem?.button != nil) " +
            "menuExists=\(statusItem?.menu != nil) " +
            "menuItems=\(statusItem?.menu?.items.count ?? 0)"
        )
    }

    private func perform(_ command: AppCommand) {
        LifecycleDebugLogger.log("MenuBarController.perform command=\(command.title)")
        commandHandler?(command)
    }

    @objc private func quickPickFromMenu() {
        perform(.showQuickPick)   // 与其它菜单项同一条 dispatch（含日志），不开第二条路
    }

    @objc private func showMainWindowFromMenu() {
        perform(.showMainWindow)
    }

    @objc private func showSettingsFromMenu() {
        perform(.showSettings)
    }

    @objc private func refreshHistoryFromMenu() {
        perform(.refreshHistory)
    }

    @objc private func confirmAndClearHistoryFromMenu() {
        perform(.clearHistory)
    }

    @objc private func dismissAllRecommendationsFromMenu() {
        perform(.dismissAllRecommendations)
    }

    @objc private func quitFromMenu() {
        perform(.quit)
    }

}
