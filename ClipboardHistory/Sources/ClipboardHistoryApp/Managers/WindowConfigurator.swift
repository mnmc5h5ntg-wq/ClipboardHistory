import AppKit
import SwiftUI

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
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = [.managed, .fullScreenNone]
            window.setContentSize(NSSize(width: 750, height: 480))
            window.minSize = NSSize(width: 600, height: 400)
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
        func windowShouldClose(_ sender: NSWindow) -> Bool {
            LifecycleDebugLogger.log("windowShouldClose called title='\(sender.title)'")
            LifecycleDebugLogger.logAppState("before windowShouldClose")
            NSApplication.shared.hide(nil)
            LifecycleDebugLogger.logAppState("after windowShouldClose hide app")
            return false
        }

        func windowWillClose(_ notification: Notification) {
            LifecycleDebugLogger.log("windowWillClose called")
            LifecycleDebugLogger.logAppState("windowWillClose")
        }
    }
}
