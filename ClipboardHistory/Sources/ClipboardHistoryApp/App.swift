import SwiftUI

@main
struct ClipboardHistoryApp: App {

    @StateObject private var historyStore = AppDelegate.sharedHistoryStore
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView(historyStore: historyStore)
                .frame(minWidth: 600, minHeight: 440)
                .onAppear {
                    appDelegate.configure()
                }
                .background(WindowConfigurator())
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            ClipboardHistoryCommands(appDelegate: appDelegate)
        }

        if #available(macOS 13, *) {
            MenuBarExtra("时间剪史", systemImage: "clipboard") {
                MenuBarRecommendationsView(historyStore: historyStore, appDelegate: appDelegate)
                Divider()
                ForEach(AppCommandCatalog.menuBarCommands.filter { $0 != .quit }, id: \.self) { command in
                    Button(command.title) {
                        appDelegate.perform(command)
                    }
                }
                Divider()
                Button(AppCommand.quit.title) {
                    appDelegate.perform(.quit)
                }
            }
            // R109：这一行以前**没有**——`MenuBarRecommendationsView` 里那句
            // "这里挂 `.transition` 也不会执行，因为 `MenuBarExtraStyle.menu` 的内容会被编译成真的
            // `NSMenu`"（以及钉住它的守卫 `testNoUnexecutedTransitionClaimsAcrossViews`）
            // 全部挂在这个**默认值**上。默认值不是契约：哪天有人加一行 `.menuBarExtraStyle(.window)`，
            // 那句理由就当场失效，而守卫数的是文件里有没有 `animation(`，它仍然绿。
            // 所以把理由的前提写成代码，并让一条源码守卫读它（BACKLOG 163）。
            .menuBarExtraStyle(.menu)
        }
    }
}
