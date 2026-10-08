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
        }
    }
}
