import AppKit

@MainActor
final class MenuBarController: NSObject, NSMenuDelegate {
    typealias CommandHandler = (AppCommand) -> Void

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
        populate(menu)
        LifecycleDebugLogger.log("menu bound itemCount=\(menu.items.count)")
        return menu
    }

    func menuWillOpen(_ menu: NSMenu) {
        historyStore?.refreshPredictions()
        populate(menu)
    }

    private func populate(_ menu: NSMenu) {
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
                attributes: [.font: NSFont.systemFont(ofSize: 11, weight: .semibold),
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
                    .font: NSFont.systemFont(ofSize: 13)
                ])
                if !reason.isEmpty {
                    title.append(NSAttributedString(string: "\n\(reason)", attributes: [
                        .font: NSFont.systemFont(ofSize: 11),
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
        } else if historyStore != nil {
            // 没有推荐时也要说一句话：旧实现在这种情况下整段静默消失，用户分不清
            // "算过了没有结果"和"这块坏了"（审计第二轮 R2-09 / 1.8）。
            // 与 macOS 13 的 MenuBarRecommendationsView 用同一句文案与同一档字号。
            menu.addItem(.separator())
            let emptyItem = NSMenuItem(title: "暂无推荐", action: nil, keyEquivalent: "")
            emptyItem.isEnabled = false
            emptyItem.attributedTitle = NSAttributedString(
                string: "暂无推荐",
                attributes: [.font: NSFont.systemFont(ofSize: 11),
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
        case .dismissAllRecommendations:
            return #selector(dismissAllRecommendationsFromMenu)
        case .quit:
            return #selector(quitFromMenu)
        }
    }

    private func makeStatusBarIcon() -> NSImage {
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
