import AppKit
import SwiftUI

extension Notification.Name {
    static let mainWindowDidHide = Notification.Name("ClipboardHistoryMainWindowDidHide")
}

/// 透明标题栏 + 禁用原生全屏 + 跨版本窗口尺寸设置
struct WindowConfigurator: NSViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            LifecycleDebugLogger.log("WindowConfigurator found window")
            window.identifier = WindowManager.mainWindowIdentifier
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = [.managed, .fullScreenNone]
            window.setContentSize(NSSize(width: 750, height: 480))
            window.minSize = NSSize(width: 600, height: 400)
            context.coordinator.configure(window: window)
            window.delegate = context.coordinator
            if let zoomButton = window.standardWindowButton(.zoomButton) {
                zoomButton.isEnabled = false
                zoomButton.toolTip = "时间剪史暂不支持全屏显示"
            }
            LifecycleDebugLogger.logAppState("after WindowConfigurator setup")
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}

    @MainActor
    final class Coordinator: NSObject, NSWindowDelegate {
        private weak var configuredWindow: NSWindow?

        func configure(window: NSWindow) {
            configuredWindow = window
            removeSidebarToolbarButton(from: window)
            scheduleSidebarToolbarCleanupPasses()
        }

        func windowShouldClose(_ sender: NSWindow) -> Bool {
            LifecycleDebugLogger.log("windowShouldClose called title='\(sender.title)'")
            LifecycleDebugLogger.logAppState("before windowShouldClose")
            NSApplication.shared.hide(nil)
            NotificationCenter.default.post(name: .mainWindowDidHide, object: sender)
            LifecycleDebugLogger.logAppState("after windowShouldClose hide app")
            return false
        }

        func windowWillClose(_ notification: Notification) {
            LifecycleDebugLogger.log("windowWillClose called")
            LifecycleDebugLogger.logAppState("windowWillClose")
        }

        private func scheduleSidebarToolbarCleanupPasses() {
            for delay in [0.1, 0.3, 0.7, 1.2, 2.0, 3.0] {
                Task { @MainActor [weak self] in
                    try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                    guard let self, let window = self.configuredWindow else { return }
                    self.removeSidebarToolbarButton(from: window)
                }
            }
        }

        private func removeSidebarToolbarButton(from window: NSWindow) {
            guard let toolbar = window.toolbar else { return }
            for index in toolbar.items.indices.reversed() {
                let item = toolbar.items[index]
                if isSidebarToolbarItem(item) {
                    toolbar.removeItem(at: index)
                }
            }
        }

        private func isSidebarToolbarItem(_ item: NSToolbarItem) -> Bool {
            if item.action == #selector(NSSplitViewController.toggleSidebar(_:)) {
                return true
            }

            let fields = [
                item.itemIdentifier.rawValue,
                item.label,
                item.paletteLabel,
                item.toolTip ?? "",
                item.action.map { NSStringFromSelector($0) } ?? "",
                item.view?.accessibilityLabel() ?? ""
            ].map(\.localizedLowercase)

            return fields.contains { field in
                field.contains("sidebar")
                    || field.contains("togglesidebar")
                    || field.contains("边栏")
                    || field.contains("侧边栏")
            }
        }
    }
}
