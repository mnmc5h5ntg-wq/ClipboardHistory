import AppKit
import SwiftUI

extension Notification.Name {
    static let mainWindowDidHide = Notification.Name("ClipboardHistoryMainWindowDidHide")
}

enum WindowChromeLayout {
    static let trafficLightLeading: CGFloat = 21
    static let trafficLightMinimumBottomInset: CGFloat = 6
    static let trafficLightTrailingGap: CGFloat = 8
    static let trafficLightTopInset: CGFloat = 19

    static func trafficLightOrigin(titlebarHeight: CGFloat, buttonHeight: CGFloat) -> NSPoint {
        NSPoint(
            x: trafficLightLeading,
            y: max(
                titlebarHeight - buttonHeight - trafficLightTopInset,
                trafficLightMinimumBottomInset
            )
        )
    }
}

/// 透明标题栏 + 禁用原生全屏 + 跨版本窗口尺寸设置
struct WindowConfigurator: NSViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeNSView(context: Context) -> NSView {
        let view = ConfigurationHostView()
        view.configureWindow = { [coordinator = context.coordinator] window in
            LifecycleDebugLogger.log("WindowConfigurator found window")
            window.identifier = WindowManager.mainWindowIdentifier
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = [.managed, .fullScreenNone]
            window.setContentSize(NSSize(width: 750, height: 560))
            window.minSize = NSSize(width: 600, height: 440)
            coordinator.configure(window: window)
            window.delegate = coordinator
            if let zoomButton = window.standardWindowButton(.zoomButton) {
                zoomButton.isEnabled = false
                zoomButton.toolTip = "时间剪史暂不支持全屏显示"
            }
            LifecycleDebugLogger.logAppState("after WindowConfigurator setup")
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}

    private final class ConfigurationHostView: NSView {
        var configureWindow: ((NSWindow) -> Void)?
        private weak var configuredWindow: NSWindow?

        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            configureAttachedWindowIfNeeded()
        }

        override func viewDidMoveToSuperview() {
            super.viewDidMoveToSuperview()
            configureAttachedWindowIfNeeded()
        }

        override func layout() {
            super.layout()
            configureAttachedWindowIfNeeded()
        }

        private func configureAttachedWindowIfNeeded() {
            guard let window, configuredWindow !== window else { return }
            configuredWindow = window
            configureWindow?(window)
        }
    }

    @MainActor
    final class Coordinator: NSObject, NSWindowDelegate {
        private weak var configuredWindow: NSWindow?

        func configure(window: NSWindow) {
            configuredWindow = window
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            // Aggressive follow-up: SwiftUI may recreate the toggle across several frames
            for delay in [0.0, 0.02, 0.08, 0.2, 0.5, 1.0] {
                DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
                    guard let self, let window = self.configuredWindow else { return }
                    self.removeSidebarToolbarButton(from: window)
                }
            }
        }

        func windowDidBecomeKey(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
        }

        func windowDidBecomeMain(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
        }

        func windowDidResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
        }

        func windowDidEndLiveResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            removeSidebarToolbarButton(from: window)
        }

        func windowDidMove(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
        }

        func windowShouldClose(_ sender: NSWindow) -> Bool {
            LifecycleDebugLogger.log("windowShouldClose called title='\(sender.title)'")
            LifecycleDebugLogger.logAppState("before windowShouldClose")
            // 最小化到 Dock，macOS 12 上最可靠的窗口保持方案
            sender.orderOut(nil)
            NotificationCenter.default.post(name: .mainWindowDidHide, object: sender)
            LifecycleDebugLogger.logAppState("after windowShouldClose miniaturize")
            return false
        }

        func windowWillClose(_ notification: Notification) {
            LifecycleDebugLogger.log("[RED-BTN] windowWillClose FIRED — THIS MEANS WINDOW IS BEING DESTROYED DESPITE return false!")
            if let w = notification.object as? NSWindow {
                LifecycleDebugLogger.log("[RED-BTN] windowWillClose title='\(w.title)' isVisible=\(w.isVisible)")
            }
            LifecycleDebugLogger.logAppState("windowWillClose")
        }


        private func alignTrafficLights(in window: NSWindow) {
            guard let closeButton = window.standardWindowButton(.closeButton),
                  let minimizeButton = window.standardWindowButton(.miniaturizeButton),
                  let zoomButton = window.standardWindowButton(.zoomButton),
                  let titlebarContainer = closeButton.superview else {
                return
            }

            let buttonOrigin = WindowChromeLayout.trafficLightOrigin(
                titlebarHeight: titlebarContainer.bounds.height,
                buttonHeight: closeButton.frame.height
            )
            closeButton.setFrameOrigin(buttonOrigin)
            minimizeButton.setFrameOrigin(
                NSPoint(
                    x: buttonOrigin.x + closeButton.frame.width + WindowChromeLayout.trafficLightTrailingGap,
                    y: buttonOrigin.y
                )
            )
            zoomButton.setFrameOrigin(
                NSPoint(
                    x: buttonOrigin.x + (closeButton.frame.width + WindowChromeLayout.trafficLightTrailingGap) * 2,
                    y: buttonOrigin.y
                )
            )
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

            var fields = [
                item.itemIdentifier.rawValue,
                item.label,
                item.paletteLabel,
                item.toolTip ?? ""
            ]
            if let action = item.action {
                fields.append(NSStringFromSelector(action))
            }
            if let view = item.view {
                fields.append(view.accessibilityLabel() ?? "")
                fields.append(accessibilityAndActionText(in: view))
            }
            let normalizedFields = fields.map(\.localizedLowercase)

            return normalizedFields.contains { field in
                field.contains("sidebar")
                    || field.contains("togglesidebar")
                    || field.contains("边栏")
                    || field.contains("侧边栏")
            }
        }

        private func accessibilityAndActionText(in view: NSView) -> String {
            var parts: [String] = [
                view.identifier?.rawValue ?? "",
                view.accessibilityLabel() ?? "",
                view.accessibilityIdentifier()
            ]

            if let control = view as? NSControl {
                parts.append(control.action.map { NSStringFromSelector($0) } ?? "")
                parts.append(control.toolTip ?? "")
            }

            for subview in view.subviews {
                parts.append(accessibilityAndActionText(in: subview))
            }

            return parts.joined(separator: " ")
        }
    }
}
