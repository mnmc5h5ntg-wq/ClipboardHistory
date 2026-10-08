import SwiftUI

struct ContentView: View {
    @ObservedObject var historyStore: HistoryStore

    var body: some View {
        if #available(macOS 13, *) {
            splitView
                .removeSidebarToggleToolbarItem()
                .windowBackground()
                .onAppear {
                    LifecycleDebugLogger.log("NavigationSplitView appeared")
                    LifecycleDebugLogger.logKeyWindowLayout("NavigationSplitView appear")
                }
        } else {
            NavigationView {
                HistorySidebarView(historyStore: historyStore)
                    .frame(minWidth: 250, idealWidth: 280, maxWidth: 340)
                DetailView(historyStore: historyStore)
            }
            .windowBackground()
            .onAppear {
                LifecycleDebugLogger.log("NavigationView appeared")
                LifecycleDebugLogger.logKeyWindowLayout("NavigationView appear")
            }
        }
    }

    @available(macOS 13, *)
    private var splitView: some View {
        NavigationSplitView {
            HistorySidebarView(historyStore: historyStore)
                .navigationSplitViewColumnWidth(min: 250, ideal: 280, max: 340)
        } detail: {
            DetailView(historyStore: historyStore)
        }
    }
}

private extension View {
    @ViewBuilder
    func removeSidebarToggleToolbarItem() -> some View {
        if #available(macOS 14, *) {
            toolbar(removing: .sidebarToggle)
        } else {
            self
        }
    }

}
