import SwiftUI

struct ContentView: View {
    @ObservedObject var historyStore: HistoryStore
    /// R523：折叠态只留列表；默认展开，离屏夹具不必跟着改。
    var isCollapsed: Bool = false
    var toggleCollapse: () -> Void = {}
    /// R417：「暂停记录」以前只在设置页那颗开关上可见 —— 主窗口里复制进不来，
    /// 界面一句话都不说。这里与设置页读同一个键，开关一动横幅就进出。
    @AppStorage("recordingPaused") private var recordingPaused = false
    /// 取证通道：离屏夹具/胶片送不进设置页那次点击，只有它们写这颗键。
    @Environment(\.pausedForCapture) private var pausedForCapture

    var body: some View {
        VStack(spacing: 0) {
            notices
            if isCollapsed {
                // 折叠态**不渲染 detail**：不是把详情列压到 0 宽（那还会留着布局与焦点），
                // 而是根本不进 NavigationSplitView。
                HistorySidebarView(historyStore: historyStore,
                                   isCollapsed: true,
                                   toggleCollapse: toggleCollapse)
                    // 折叠态不再套 `windowBackground`（那是给分栏内外两面的材质）；
                    // 窗口自己的底色就是列表后面这一层，夹具用同色不透明底拍它。
                    .background(Color(nsColor: .windowBackgroundColor))
                    .onAppear {
                        LifecycleDebugLogger.log("collapsed sidebar appeared")
                        LifecycleDebugLogger.logKeyWindowLayout("collapsed sidebar appear")
                    }
            } else if #available(macOS 13, *) {
                splitView
                    .removeSidebarToggleToolbarItem()
                    .windowBackground()
                    .onAppear {
                        LifecycleDebugLogger.log("NavigationSplitView appeared")
                        LifecycleDebugLogger.logKeyWindowLayout("NavigationSplitView appear")
                    }
            } else {
                NavigationView {
                    HistorySidebarView(historyStore: historyStore,
                                       isCollapsed: false,
                                       toggleCollapse: toggleCollapse)
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
        // 提示条进出要有过渡（动效审计 M2）。键是"六条提示各自在不在"的签名，
        // 不是条数：两条同时换进换出时条数不变，用 count 做键就什么都不会动。
        .animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)
    }

    /// 暂停状态的绘制值：取证键优先，产品路径读 `@AppStorage`。
    private var isPausedForDrawing: Bool { pausedForCapture ?? recordingPaused }

    /// 六条提示的存在性签名（第五条是暂停状态）。
    private var noticeSignature: Int {
        var bits = 0
        if historyStore.historyRecoveryNotice != nil { bits |= 1 }
        if historyStore.transferNotice != nil { bits |= 2 }
        if historyStore.droppedFilesNotice != nil { bits |= 4 }
        if historyStore.pasteFailureNotice != nil { bits |= 8 }
        if historyStore.retentionNotice != nil { bits |= 16 }
        if isPausedForDrawing { bits |= 32 }
        return bits
    }

    /// 顶部提示条：没有提示时这里不产生任何高度。
    @ViewBuilder
    private var notices: some View {
        // 暂停状态排在最前：它是持续状态，用户最需要先看到"这段时间复制不进来"。
        // 动作不是「知道了」而是「继续记录」—— 知道没有用，把采集打开才有用。
        if isPausedForDrawing {
            NoticeBanner(message: "已暂停记录剪贴板 —— 这段时间的复制不会进入历史。",
                         tone: .paused) {
                recordingPaused = false
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }
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
            HistorySidebarView(historyStore: historyStore,
                               isCollapsed: false,
                               toggleCollapse: toggleCollapse)
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
