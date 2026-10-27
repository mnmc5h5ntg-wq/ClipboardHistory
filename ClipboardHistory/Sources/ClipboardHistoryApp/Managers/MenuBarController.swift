import AppKit
import Combine
import SwiftUI

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
    /// R418 / BACKLOG 443：12 那颗状态项图标要跟着「暂停记录」换记号。
    /// 菜单栏那颗图不是 SwiftUI 的，`@AppStorage` 不会替它重画 ⇒ 自己订阅 defaults 变化。
    private var pauseBridge: AnyCancellable?

    private var statusItem: NSStatusItem?
    private var commandHandler: CommandHandler?
    private var pasteHandler: ((HistoryStore.Entry) -> Void)?
    private var menuShortcutHints: () -> [AppCommand: String] = { [:] }
    weak var historyStore: HistoryStore?

    func configure(
        commandHandler: @escaping CommandHandler,
        historyStore: HistoryStore? = nil,
        pasteHandler: ((HistoryStore.Entry) -> Void)? = nil,
        menuShortcutHints: @escaping () -> [AppCommand: String] = { [:] }
    ) {
        LifecycleDebugLogger.log("MenuBarController.configure called")
        self.commandHandler = commandHandler
        self.historyStore = historyStore
        self.pasteHandler = pasteHandler
        self.menuShortcutHints = menuShortcutHints

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
        let paused = historyStore?.isRecordingPaused ?? false
        item.button?.image = makeStatusBarIcon(paused: paused)
        item.button?.imagePosition = .imageOnly
        item.button?.toolTip = MenuBarStatusPresentation.accessibilityLabel(paused: paused)
        item.menu = makeMenu()
        statusItem = item
        attachPauseBridgeIfNeeded()
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
            // R235（D-220）：这里原先把这一行的墨**写死**成一颗蓝，墨写死就不参与系统为
            // 选中态准备的换色。实测（MENUBAR_DISMISS_INK，底色用系统语义色当代理）：
            // 静置底上 3.52:1（亮）/5.16:1（暗），而同一棵菜单的正文参照是 21.00/16.67；
            // 选中底上 1.93/2.36，压强调底 1.14/1.24。静置与悬停两种态它都输 ⇒ 墨交回系统。
            // 这一行"我是退出这轮推荐"的身份改由**分隔线 + 它自己在最后一段**承担。
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
            title: MenuShortcutPresentation.title(command.title,
                                                  hint: menuShortcutHints()[command]),
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
    func makeStatusBarIcon(paused: Bool = false) -> NSImage {
        // 首选系统符号：与 13+ 的 `MenuBarExtra` 同一个 symbolName ⇒ 同一个素材、
        // 同一套笔画权重（与相邻菜单栏图标对齐），模板渲染由系统按明暗档染色。
        let base: NSImage
        if let symbol = NSImage(systemSymbolName: Self.statusSymbolName,
                               accessibilityDescription: "时间剪史") {
            symbol.isTemplate = true
            // 沿用这棵树一直占的那一格 18×18：改尺寸会把"换素材"变成"改几何"，
            // 两件事要能分开归因（帧里的墨包围盒会替我盯着有没有出框）。
            symbol.size = NSSize(width: 18, height: 18)
            base = symbol
        } else {
            // 只有系统符号拿不到时才走（deployment target 是 12，SF Symbols 在 11+ 就有；
            // 这一支是"别把菜单栏留空"的兜底，不是第二条设计）。
            base = Self.drawnFallbackIcon()
        }
        // R418：暂停时两棵表面画同一个斜杠 —— 13+ 的 label 与 12 的这张图共用
        // `MenuBarStatusPresentation` 的角度/线宽/文案，不许各写一个记号。
        return paused ? Self.imageAddingPauseSlash(to: base) : base
    }

    /// 在 18×18 的模板图上加一道斜杠（R418）。模板图只有 alpha 有意义：
    /// 黑色只是"这里有不透明像素"，菜单栏会按明暗档重新染色。
    private static func imageAddingPauseSlash(to base: NSImage) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size, flipped: false) { rect in
            base.draw(in: rect)
            let path = NSBezierPath()
            // SwiftUI 的坐标系 y 向下，AppKit 的 y 向上 ⇒ 端点翻转一次；
            // 两棵表面画出来的仍是同一条左上→右下的斜杠。
            path.move(to: NSPoint(x: MenuBarStatusPresentation.slashFrom.x,
                                  y: rect.height - MenuBarStatusPresentation.slashFrom.y))
            path.line(to: NSPoint(x: MenuBarStatusPresentation.slashTo.x,
                                  y: rect.height - MenuBarStatusPresentation.slashTo.y))
            path.lineWidth = MenuBarStatusPresentation.slashLineWidth
            path.lineCapStyle = .round
            NSColor.black.setStroke()
            path.stroke()
            return true
        }
        image.isTemplate = true
        image.size = size
        image.accessibilityDescription = MenuBarStatusPresentation.accessibilityLabel(paused: true)
        return image
    }

    /// 12：订阅默认值变化，把「暂停记录」立刻画进状态项。
    /// 13+ 不走这里（`MenuBarExtra` 的 label 自己读 `@AppStorage`）。
    private func attachPauseBridgeIfNeeded() {
        guard pauseBridge == nil else { return }
        pauseBridge = NotificationCenter.default.publisher(for: UserDefaults.didChangeNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in self?.refreshStatusItemImage() }
    }

    private func refreshStatusItemImage() {
        guard let statusItem else { return }
        let paused = historyStore?.isRecordingPaused ?? false
        statusItem.button?.image = makeStatusBarIcon(paused: paused)
        statusItem.button?.toolTip = MenuBarStatusPresentation.accessibilityLabel(paused: paused)
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

/// 菜单栏那颗图标的暂停状态（R418 / BACKLOG 443）。
///
/// 两棵表面（13+ 的 `MenuBarExtra` label 与 12 的 `NSStatusItem` 图）必须画同一个记号：
/// 斜杠的端点、线宽、无障碍文案只在这里写一次。13+ 的菜单栏标签由系统合成，
/// 离屏只能拍 `MenuBarStatusLabel` 本身（真菜单栏那条通道具名 NOT-RUN，见台账）。
enum MenuBarStatusPresentation {
    /// 斜杠在 18×18 格里的两个端点（SwiftUI 的 y 向下；AppKit 画的时候翻 y）。
    static let slashFrom = CGPoint(x: 3.2, y: 3.2)
    static let slashTo = CGPoint(x: 14.8, y: 14.8)
    static let slashLineWidth: CGFloat = 1.6

    static func accessibilityLabel(paused: Bool) -> String {
        paused ? "时间剪史，已暂停记录" : "时间剪史"
    }
}

/// 13+ 的 `MenuBarExtra` 标签：同一颗 `clipboard` 符号，暂停时多一道斜杠。
///
/// 为什么不是换一颗符号：R110 把「两棵表面同一个入口」立成了守卫；
/// 暂停是**同一颗图标的状态**，不是另一个入口 —— 换符号会让它在菜单栏里变成另一个 App。
/// 符号/斜杠/文案都从产品常量来；`pausedForCapture` 只给夹具，产品读 `@AppStorage`。
struct MenuBarStatusLabel: View {
    @AppStorage("recordingPaused") private var recordingPaused = false
    @Environment(\.pausedForCapture) private var pausedForCapture

    private var paused: Bool { pausedForCapture ?? recordingPaused }

    var body: some View {
        Image(systemName: MenuBarController.statusSymbolName)
            .frame(width: 18, height: 18)
            .overlay {
                if paused {
                    Path { path in
                        path.move(to: MenuBarStatusPresentation.slashFrom)
                        path.addLine(to: MenuBarStatusPresentation.slashTo)
                    }
                    .stroke(.primary,
                            style: StrokeStyle(lineWidth: MenuBarStatusPresentation.slashLineWidth,
                                               lineCap: .round))
                }
            }
            .accessibilityLabel(MenuBarStatusPresentation.accessibilityLabel(paused: paused))
    }
}
