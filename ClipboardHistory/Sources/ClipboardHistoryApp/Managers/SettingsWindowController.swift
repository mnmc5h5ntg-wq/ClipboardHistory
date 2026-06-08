import AppKit
import SwiftUI

@MainActor
final class SettingsWindowController {
    private let showMainWindowHotKeySettings: HotKeySettings
    private let repeatCopyHotKeySettings: HotKeySettings
    private let loginItemSettings: LoginItemSettings
    private var windowController: NSWindowController?

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
        self.loginItemSettings = loginItemSettings
    }

    func show() {
        let controller = makeWindowControllerIfNeeded()
        controller.showWindow(nil)
        controller.window?.center()
        NSApplication.shared.activate(ignoringOtherApps: true)
    }

    private func makeWindowControllerIfNeeded() -> NSWindowController {
        if let windowController {
            return windowController
        }

        let hostingController = NSHostingController(
            rootView: SettingsView(
                showMainWindowHotKeySettings: showMainWindowHotKeySettings,
                repeatCopyHotKeySettings: repeatCopyHotKeySettings,
                loginItemSettings: loginItemSettings
            )
        )
        let window = NSWindow(contentViewController: hostingController)
        window.title = "设置"
        window.styleMask = [.titled, .closable, .miniaturizable]
        window.isReleasedWhenClosed = false
        window.setContentSize(NSSize(width: 520, height: 330))
        window.minSize = NSSize(width: 520, height: 330)

        let controller = NSWindowController(window: window)
        windowController = controller
        return controller
    }
}
