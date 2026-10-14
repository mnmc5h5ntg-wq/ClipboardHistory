import AppKit
import SwiftUI

@MainActor
final class SettingsWindowController {
    private let showMainWindowHotKeySettings: HotKeySettings
    private let repeatCopyHotKeySettings: HotKeySettings
    private let quickPickHotKeySettings: HotKeySettings
    private let loginItemSettings: LoginItemSettings
    private let contextPreferences: ContextPreferenceSettings
    private var weightsStore: RecommendationWeightsStore
    private weak var historyStore: HistoryStore?
    private var windowController: NSWindowController?

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        // 有默认值只是为了让旧的测试夹具不必一起改；生产侧（AppDelegate）始终显式传入，
        // 而"确实传了"由 Round3QuickPickTests 的接线守卫钉住。
        quickPickHotKeySettings: HotKeySettings = HotKeySettings(action: .quickPick),
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        weightsStore: RecommendationWeightsStore = RecommendationWeightsStore()
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
        self.quickPickHotKeySettings = quickPickHotKeySettings
        self.loginItemSettings = loginItemSettings
        self.contextPreferences = contextPreferences
        self.weightsStore = weightsStore
    }

    func configure(historyStore: HistoryStore, weightsStore: RecommendationWeightsStore? = nil) {
        self.historyStore = historyStore
        if let ws = weightsStore {
            self.weightsStore = ws
        }
        if let hostingController = windowController?.contentViewController as? NSHostingController<SettingsView> {
            hostingController.rootView = makeSettingsView()
        }
    }

    func show() {
        let controller = makeWindowControllerIfNeeded()
        controller.showWindow(nil)
        controller.window?.center()
        NSApplication.shared.activate(ignoringOtherApps: true)
    }

    private func makeWindowControllerIfNeeded() -> NSWindowController {
        if let windowController {
            return windowController
        }

        let hostingController = NSHostingController(rootView: makeSettingsView())
        let window = NSWindow(contentViewController: hostingController)
        window.title = "设置"
        window.styleMask = [.titled, .closable, .miniaturizable, .resizable]
        window.isReleasedWhenClosed = false
        window.setContentSize(NSSize(width: SettingsViewLayout.windowContentSize.width, height: SettingsViewLayout.windowContentSize.height))
        window.minSize = NSSize(width: SettingsViewLayout.minimumWindowSize.width, height: SettingsViewLayout.minimumWindowSize.height)

        let controller = NSWindowController(window: window)
        windowController = controller
        return controller
    }

    private func makeSettingsView() -> SettingsView {
        SettingsView(
            showMainWindowHotKeySettings: showMainWindowHotKeySettings,
            repeatCopyHotKeySettings: repeatCopyHotKeySettings,
            quickPickHotKeySettings: quickPickHotKeySettings,
            loginItemSettings: loginItemSettings,
            contextPreferences: contextPreferences,
            weightsStore: weightsStore,
            feedbackStore: historyStore?.feedbackStore ?? RecommendationFeedbackStore(),
            dailyCopyLedger: historyStore?.dailyCopyLedger,
            clearHistoryAction: { [weak self] in
                guard let store = self?.historyStore else { return nil }
                // 顺序是这条的全部价值：**先数再清**。清完再数，`entries` 只剩收藏，
                // 回执会永远说"清空了 0 条"（R6 / 审计 B-P1-2，判据见
                // `MotionDriverTests.testClearHistoryReceiptCountsTheRealRemoval`）。
                let receipt = ClearHistoryReceiptPolicy.receipt(isFavorites: store.entries.map(\.isFavorite))
                store.perform(.clear)
                return receipt
            },
            exportHistoryAction: { [weak self] url in
                guard let self, let store = self.historyStore else { return "历史记录不可用" }
                let (data, summary) = store.exportArchiveJSON()
                do {
                    try data.write(to: url, options: .atomic)
                    return ArchiveTransfer.exportWarningText(summary: summary)
                } catch {
                    // R43 / BACKLOG 62：原文进日志，界面只说"发生了什么 + 下一步"。
                    // 修前这句是 "导出失败：\(error.localizedDescription)" —— 与 R41 的 U-67 同一族，
                    // 只是换了个出口（那次收了"写剪贴板"，这三个导出/导入出口没人管）。
                    LifecycleDebugLogger.log("SettingsWindow archive export failed error=\(error)")
                    return ArchiveTransferReceipt.exportFailed(error)
                }
            },
            importHistoryAction: { [weak self] url in
                guard let self, let store = self.historyStore else { return "历史记录不可用" }
                do {
                    let summary = try store.importArchiveJSON(Data(contentsOf: url))
                    return "导入完成：新增 \(summary.importedCount - summary.skippedDuplicateCount) 条，"
                        + "跳过重复 \(summary.skippedDuplicateCount) 条。"
                } catch {
                    // 同 R43：措辞归 `ArchiveTransferReceipt`，原文归日志。
                    LifecycleDebugLogger.log("SettingsWindow archive import failed error=\(error)")
                    return ArchiveTransferReceipt.importFailed(error)
                }
            }
        )
    }
}
