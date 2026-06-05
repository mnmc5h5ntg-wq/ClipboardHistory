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
        .windowResizability(.contentMinSize)
        .defaultSize(width: 750, height: 480)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

/// 透明标题栏 + 禁用全屏
struct WindowConfigurator: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.collectionBehavior = .fullScreenNone
        }
        return view
    }
    func updateNSView(_ nsView: NSView, context: Context) {}
}
