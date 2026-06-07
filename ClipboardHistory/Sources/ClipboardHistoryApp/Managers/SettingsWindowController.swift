import AppKit
import SwiftUI

@MainActor
final class SettingsWindowController {
    private let hotKeySettings: HotKeySettings
    private var windowController: NSWindowController?

    init(hotKeySettings: HotKeySettings) {
        self.hotKeySettings = hotKeySettings
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

        let hostingController = NSHostingController(rootView: SettingsView(hotKeySettings: hotKeySettings))
        let window = NSWindow(contentViewController: hostingController)
        window.title = "设置"
        window.styleMask = [.titled, .closable, .miniaturizable]
        window.isReleasedWhenClosed = false
        window.setContentSize(NSSize(width: 500, height: 180))
        window.minSize = NSSize(width: 500, height: 180)

        let controller = NSWindowController(window: window)
        windowController = controller
        return controller
    }
}
