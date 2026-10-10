import AppKit
import SwiftUI

@MainActor
final class SettingsWindowController {
    private let showMainWindowHotKeySettings: HotKeySettings
    private let repeatCopyHotKeySettings: HotKeySettings
    private let loginItemSettings: LoginItemSettings
    private let contextPreferences: ContextPreferenceSettings
    private var weightsStore: RecommendationWeightsStore
    private weak var historyStore: HistoryStore?
    private var windowController: NSWindowController?

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings,
        contextPreferences: ContextPreferenceSettings = ContextPreferenceSettings(),
        weightsStore: RecommendationWeightsStore = RecommendationWeightsStore()
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
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
            loginItemSettings: loginItemSettings,
            contextPreferences: contextPreferences,
            weightsStore: weightsStore,
            feedbackStore: historyStore?.feedbackStore ?? RecommendationFeedbackStore(),
            clearHistoryAction: { [weak self] in
                self?.historyStore?.perform(.clear)
            },
            exportHistoryAction: { [weak self] url in
                guard let self, let store = self.historyStore else { return "历史记录不可用" }
                let (data, summary) = store.exportArchiveJSON()
                do {
                    try data.write(to: url, options: .atomic)
                    return ArchiveTransfer.exportWarningText(summary: summary)
                } catch {
                    return "导出失败：\(error.localizedDescription)"
                }
            },
            importHistoryAction: { [weak self] url in
                guard let self, let store = self.historyStore else { return "历史记录不可用" }
                do {
                    let summary = try store.importArchiveJSON(Data(contentsOf: url))
                    return "导入完成：新增 \(summary.importedCount - summary.skippedDuplicateCount) 条，"
                        + "跳过重复 \(summary.skippedDuplicateCount) 条。"
                } catch {
                    return "导入失败：\(error.localizedDescription)"
                }
            }
        )
    }
}
