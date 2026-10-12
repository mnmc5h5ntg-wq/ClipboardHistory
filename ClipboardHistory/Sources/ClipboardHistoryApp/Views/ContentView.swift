import SwiftUI

struct ContentView: View {
    @ObservedObject var historyStore: HistoryStore

    var body: some View {
        VStack(spacing: 0) {
            notices
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
        // 提示条进出要有过渡（动效审计 M2）。键是"五条提示各自在不在"的签名，
        // 不是条数：两条同时换进换出时条数不变，用 count 做键就什么都不会动。
        .animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)
    }

    /// 五条提示的存在性签名。
    private var noticeSignature: Int {
        var bits = 0
        if historyStore.historyRecoveryNotice != nil { bits |= 1 }
        if historyStore.transferNotice != nil { bits |= 2 }
        if historyStore.droppedFilesNotice != nil { bits |= 4 }
        if historyStore.pasteFailureNotice != nil { bits |= 8 }
        if historyStore.retentionNotice != nil { bits |= 16 }
        return bits
    }

    /// 顶部提示条：没有提示时这里不产生任何高度。
    @ViewBuilder
    private var notices: some View {
        if let recovery = historyStore.historyRecoveryNotice {
            NoticeBanner(message: recovery, tone: .warning) {
                historyStore.dismissHistoryRecoveryNotice()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }
        if let transfer = historyStore.transferNotice {
            NoticeBanner(message: transfer, tone: .warning) {
                historyStore.dismissTransferNotice()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }

        if let dropped = historyStore.droppedFilesNotice {
            NoticeBanner(message: dropped, tone: .warning) {
                historyStore.dismissDroppedFilesNotice()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }

        if let pasteFailure = historyStore.pasteFailureNotice {
            NoticeBanner(message: pasteFailure, tone: .error) {
                historyStore.dismissPasteFailure()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }
        if let retention = historyStore.retentionNotice {
            NoticeBanner(message: retention, tone: .warning) {
                historyStore.dismissRetentionNotice()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
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
