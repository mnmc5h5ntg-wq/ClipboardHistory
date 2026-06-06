import SwiftUI

@main
struct ClipboardHistoryApp: App {

    @StateObject private var manager = ClipboardManager()
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView(manager: manager)
                .frame(minWidth: 600, minHeight: 400)
                .onAppear {
                    appDelegate.configure(manager: manager)
                }
                .background(WindowConfigurator())
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("关于时间剪史") {
                    showAboutPanel()
                }
            }
            CommandGroup(replacing: .newItem) {}
            CommandGroup(replacing: .windowSize) {}
        }

        if #available(macOS 13, *) {
            MenuBarExtra("时间剪史", systemImage: "clipboard") {
                Text("时间剪史")
                Button("显示主窗口") {
                    appDelegate.showMainWindow()
                }
                Button("刷新历史") {
                    appDelegate.refreshHistory()
                }
                Button("清空历史…") {
                    appDelegate.confirmAndClearHistory()
                }
                Divider()
                Button("退出时间剪史") {
                    appDelegate.quit()
                }
            }
        }
    }

    private func showAboutPanel() {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.2.1"
        let githubURL = "https://github.com/mnmc5h5ntg-wq/ClipboardHistory"
        NSApplication.shared.orderFrontStandardAboutPanel(options: [
            .applicationName: "时间剪史",
            .applicationVersion: version,
            .credits: NSAttributedString(
                string: """
                作者：王子懿
                License：MIT
                GitHub：\(githubURL)

                一个 macOS 原生风格的剪贴板历史管理工具，支持文本、图片和常见文件预览。
                """
            )
        ])
    }
}
