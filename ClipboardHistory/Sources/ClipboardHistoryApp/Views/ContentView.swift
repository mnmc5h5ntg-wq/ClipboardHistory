import SwiftUI

struct ContentView: View {
    @ObservedObject var historyStore: HistoryStore

    var body: some View {
        if #available(macOS 13, *) {
            NavigationSplitView {
                HistorySidebarView(historyStore: historyStore)
                    .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 320)
            } detail: {
                DetailView(historyStore: historyStore)
            }
            .removeSidebarToggleIfAvailable()
            .windowBackground()
            .onAppear {
                LifecycleDebugLogger.log("NavigationSplitView appeared")
                LifecycleDebugLogger.logKeyWindowLayout("NavigationSplitView appear")
            }
        } else {
            NavigationView {
                HistorySidebarView(historyStore: historyStore)
                    .frame(minWidth: 220, idealWidth: 260, maxWidth: 320)
                DetailView(historyStore: historyStore)
            }
            .windowBackground()
            .onAppear {
                LifecycleDebugLogger.log("NavigationView appeared")
                LifecycleDebugLogger.logKeyWindowLayout("NavigationView appear")
            }
        }
    }
}

private extension View {
    @ViewBuilder
    func removeSidebarToggleIfAvailable() -> some View {
        if #available(macOS 14, *) {
            toolbar(removing: .sidebarToggle)
        } else {
            self
        }
    }
}
