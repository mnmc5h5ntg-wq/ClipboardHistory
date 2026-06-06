import SwiftUI

struct ContentView: View {
    @ObservedObject var manager: ClipboardManager

    var body: some View {
        if #available(macOS 13, *) {
            NavigationSplitView {
                HistorySidebarView(manager: manager)
                    .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 320)
            } detail: {
                DetailView(manager: manager)
            }
            .windowBackground()
            .onAppear {
                LifecycleDebugLogger.log("NavigationSplitView appeared")
                LifecycleDebugLogger.logKeyWindowLayout("NavigationSplitView appear")
            }
        } else {
            NavigationView {
                HistorySidebarView(manager: manager)
                    .frame(minWidth: 220, idealWidth: 260, maxWidth: 320)
                DetailView(manager: manager)
            }
            .windowBackground()
            .onAppear {
                LifecycleDebugLogger.log("NavigationView appeared")
                LifecycleDebugLogger.logKeyWindowLayout("NavigationView appear")
            }
        }
    }
}
