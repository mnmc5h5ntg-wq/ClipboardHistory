import AppKit

@MainActor
final class MenuBarController: NSObject, NSMenuDelegate {
    typealias CommandHandler = (AppCommand) -> Void
    typealias EntryProvider = () -> [HistoryStore.Entry]
    typealias EntryHandler = (HistoryStore.Entry) -> Void

    private var statusItem: NSStatusItem?
    private var commandHandler: CommandHandler?
    private var entriesProvider: EntryProvider = { [] }
    private var entryHandler: EntryHandler?

    func configure(
        commandHandler: @escaping CommandHandler,
        entriesProvider: @escaping EntryProvider = { [] },
        entryHandler: EntryHandler? = nil
    ) {
        LifecycleDebugLogger.log("MenuBarController.configure called")
        self.commandHandler = commandHandler
        self.entriesProvider = entriesProvider
        self.entryHandler = entryHandler

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
        populate(menu)
    }

    private func populate(_ menu: NSMenu) {
        menu.removeAllItems()

        let titleItem = NSMenuItem(title: "时间剪史", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        QuickCopyMenu.sections(entries: entriesProvider()).forEach { section in
            addEntrySection(section, to: menu)
        }

        AppCommandCatalog.menuBarCommands.filter { $0 != .quit }.forEach { command in
            menu.addItem(menuItem(for: command))
        }
        menu.addItem(.separator())
        menu.addItem(menuItem(for: .quit))

        menu.items.forEach { $0.target = self }
    }

    private func addEntrySection(_ section: QuickCopyMenuSection, to menu: NSMenu) {
        menu.addItem(.separator())
        let sectionItem = NSMenuItem(title: section.title, action: nil, keyEquivalent: "")
        sectionItem.isEnabled = false
        menu.addItem(sectionItem)

        section.entries.forEach { entry in
            let item = NSMenuItem(
                title: EntryPresentation.privateMenuTitle(for: entry),
                action: #selector(copyHistoryEntryFromMenu(_:)),
                keyEquivalent: ""
            )
            item.representedObject = entry.id.uuidString
            item.image = NSImage(
                systemSymbolName: EntryPresentation.menuSymbol(for: entry),
                accessibilityDescription: nil
            )
            menu.addItem(item)
        }
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
        case .quit:
            return #selector(quitFromMenu)
        }
    }

    private func makeStatusBarIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        image.lockFocus()

        NSColor.black.setStroke()

        let bodyRect = NSRect(x: 4.5, y: 2.5, width: 9, height: 12)
        let bodyPath = NSBezierPath(roundedRect: bodyRect, xRadius: 1.8, yRadius: 1.8)
        bodyPath.lineWidth = 1.8
        bodyPath.stroke()

        let clipRect = NSRect(x: 6.5, y: 13, width: 5, height: 3)
        let clipPath = NSBezierPath(roundedRect: clipRect, xRadius: 1.3, yRadius: 1.3)
        clipPath.lineWidth = 1.8
        clipPath.stroke()

        let lineWidth: CGFloat = 1.4
        for y in [10.5, 7.5, 4.5] {
            let line = NSBezierPath()
            line.move(to: NSPoint(x: 6.7, y: y))
            line.line(to: NSPoint(x: 11.3, y: y))
            line.lineWidth = lineWidth
            line.stroke()
        }

        image.unlockFocus()
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

    @objc private func quitFromMenu() {
        perform(.quit)
    }

    @objc private func copyHistoryEntryFromMenu(_ sender: NSMenuItem) {
        guard let idString = sender.representedObject as? String,
              let id = UUID(uuidString: idString) else { return }
        guard let entry = entriesProvider().first(where: { $0.id == id }) else { return }
        entryHandler?(entry)
    }
}
