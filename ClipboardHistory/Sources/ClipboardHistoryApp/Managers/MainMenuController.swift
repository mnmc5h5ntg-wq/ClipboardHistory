import AppKit

@MainActor
final class MainMenuController {
    private weak var appDelegate: AppDelegate?

    func configure(appDelegate: AppDelegate) {
        self.appDelegate = appDelegate
        installMainMenuRepeatedly()
    }

    func installMainMenu() {
        guard appDelegate != nil else { return }
        let mainMenu = NSMenu()
        mainMenu.addItem(makeAppMenuItem())
        mainMenu.addItem(makeEditMenuItem())
        mainMenu.addItem(makeWindowMenuItem())
        mainMenu.addItem(makeHelpMenuItem())
        NSApplication.shared.mainMenu = mainMenu
        NSApplication.shared.windowsMenu = nil
    }

    func installMainMenuRepeatedly() {
        for delay in [0.0, 0.1, 0.35, 0.8, 1.5] {
            DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
                self?.installMainMenu()
            }
        }
    }

    private func makeAppMenuItem() -> NSMenuItem {
        let menu = NSMenu(title: "时间剪史")
        menu.addItem(item("关于时间剪史", action: #selector(AppDelegate.showAboutPanel), key: ""))
        menu.addItem(.separator())
        menu.addItem(item(for: .showSettings, action: #selector(AppDelegate.showSettingsFromMenu)))
        menu.addItem(.separator())
        menu.addItem(item("隐藏时间剪史", action: #selector(NSApplication.hide(_:)), key: "h", target: NSApplication.shared))
        menu.addItem(item("隐藏其他应用", action: #selector(NSApplication.hideOtherApplications(_:)), key: "h", modifiers: [.command, .option], target: NSApplication.shared))
        menu.addItem(item("显示全部", action: #selector(NSApplication.unhideAllApplications(_:)), key: "", target: NSApplication.shared))
        menu.addItem(.separator())
        menu.addItem(item(for: .quit, action: #selector(AppDelegate.quitFromMenu)))

        return topLevelItem("时间剪史", submenu: menu)
    }

    private func makeEditMenuItem() -> NSMenuItem {
        let menu = NSMenu(title: "编辑")
        menu.addItem(item("撤销", action: Selector(("undo:")), key: "z", target: nil))
        menu.addItem(item("重做", action: Selector(("redo:")), key: "Z", modifiers: [.command, .shift], target: nil))
        menu.addItem(.separator())
        menu.addItem(item("剪切", action: #selector(NSText.cut(_:)), key: "x", target: nil))
        menu.addItem(item("复制", action: #selector(NSText.copy(_:)), key: "c", target: nil))
        menu.addItem(item("粘贴", action: #selector(NSText.paste(_:)), key: "v", target: nil))
        menu.addItem(item("删除", action: #selector(NSText.delete(_:)), key: "", target: nil))
        menu.addItem(item("全选", action: #selector(NSText.selectAll(_:)), key: "a", target: nil))

        return topLevelItem("编辑", submenu: menu)
    }

    private func makeWindowMenuItem() -> NSMenuItem {
        let menu = NSMenu(title: "窗口")
        menu.addItem(item("最小化", action: #selector(NSWindow.performMiniaturize(_:)), key: "m", target: nil))
        menu.addItem(item("缩放", action: #selector(NSWindow.performZoom(_:)), key: "", target: nil))
        menu.addItem(.separator())
        menu.addItem(item("全部前置", action: #selector(NSApplication.arrangeInFront(_:)), key: "", target: NSApplication.shared))

        return topLevelItem("窗口", submenu: menu)
    }

    private func makeHelpMenuItem() -> NSMenuItem {
        let menu = NSMenu(title: "帮助")
        menu.addItem(item("GitHub 项目主页", action: #selector(AppDelegate.openGitHubRepository), key: ""))
        return topLevelItem("帮助", submenu: menu)
    }

    private func topLevelItem(_ title: String, submenu: NSMenu) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        item.submenu = submenu
        return item
    }

    private func item(
        _ title: String,
        action: Selector?,
        key: String,
        modifiers: NSEvent.ModifierFlags = .command,
        target: AnyObject? = nil
    ) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: key)
        item.keyEquivalentModifierMask = key.isEmpty ? [] : modifiers
        item.target = target ?? appDelegate
        return item
    }

    private func item(for command: AppCommand, action: Selector) -> NSMenuItem {
        item(
            command.title,
            action: action,
            key: command.keyEquivalent,
            modifiers: command.keyModifiers
        )
    }
}
