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

        if #available(macOS 13, *) {
            MenuBarExtra("时间剪史", systemImage: "clipboard") {
                Text("时间剪史")
                Button("显示主窗口") {
                    appDelegate.showMainWindow()
                }
                Button("设置…") {
                    appDelegate.showSettings()
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
}
