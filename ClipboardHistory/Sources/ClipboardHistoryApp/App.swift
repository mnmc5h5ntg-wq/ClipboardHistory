import SwiftUI
import AppKit

@main
struct ClipboardHistoryApp: App {

    @State private var manager = ClipboardManager()

    var body: some Scene {
        WindowGroup {
            ContentView(manager: manager)
                .frame(minWidth: 600, minHeight: 400)
                .onAppear { manager.startMonitoring() }
                .onDisappear { manager.stopMonitoring() }
                .background(WindowConfigurator())
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

/// 透明标题栏 + 禁用全屏 + 跨版本窗口尺寸设置
struct WindowConfigurator: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = .fullScreenNone
            window.setContentSize(NSSize(width: 750, height: 480))
            window.minSize = NSSize(width: 600, height: 400)
        }
        return view
    }
    func updateNSView(_ nsView: NSView, context: Context) {}
}
