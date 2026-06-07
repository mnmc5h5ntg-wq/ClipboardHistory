import AppKit

@MainActor
final class MenuBarController: NSObject {
    private var statusItem: NSStatusItem?
    private weak var manager: ClipboardManager?

    func configure(manager: ClipboardManager) {
        LifecycleDebugLogger.log("MenuBarController.configure called")
        self.manager = manager

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

        let titleItem = NSMenuItem(title: "时间剪史", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        menu.addItem(NSMenuItem(title: "显示主窗口", action: #selector(showMainWindowFromMenu), keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: "设置…", action: #selector(showSettingsFromMenu), keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: "刷新历史", action: #selector(refreshHistoryFromMenu), keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: "清空历史…", action: #selector(confirmAndClearHistoryFromMenu), keyEquivalent: ""))
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "退出时间剪史", action: #selector(quitFromMenu), keyEquivalent: "q"))

        menu.items.forEach { $0.target = self }
        LifecycleDebugLogger.log("menu bound itemCount=\(menu.items.count)")
        return menu
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

    func showMainWindow() {
        LifecycleDebugLogger.log("MenuBarController.showMainWindow called")
        WindowManager.showMainWindow(menuBarController: self)
    }

    func restoreMainWindowIfNeeded(reason: String) {
        WindowManager.restoreMainWindowIfNeeded(reason: reason, menuBarController: self)
    }

    func refreshHistory() {
        LifecycleDebugLogger.log("MenuBarController.refreshHistory called")
        manager?.refreshHistory()
    }

    func confirmAndClearHistory() {
        LifecycleDebugLogger.log("MenuBarController.confirmAndClearHistory called")
        let alert = NSAlert()
        alert.messageText = "清空全部记录"
        alert.informativeText = "确定要清空所有剪贴板记录吗？此操作不可撤销。"
        alert.alertStyle = .warning
        alert.addButton(withTitle: "清空")
        alert.addButton(withTitle: "取消")

        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            manager?.clearAll()
        }
    }

    func quit() {
        LifecycleDebugLogger.log("MenuBarController.quit called")
        NSApplication.shared.terminate(nil)
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

    @objc private func showMainWindowFromMenu() {
        showMainWindow()
    }

    @objc private func showSettingsFromMenu() {
        (NSApplication.shared.delegate as? AppDelegate)?.showSettings()
    }

    @objc private func refreshHistoryFromMenu() {
        refreshHistory()
    }

    @objc private func confirmAndClearHistoryFromMenu() {
        confirmAndClearHistory()
    }

    @objc private func quitFromMenu() {
        quit()
    }
}
