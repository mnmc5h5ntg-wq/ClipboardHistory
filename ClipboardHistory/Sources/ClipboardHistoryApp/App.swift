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
            // R110：符号名从 `MenuBarController.statusSymbolName` 引用，不在这里写字面量
            // —— 12 上那颗图标由 AppKit 自己画（`NSImage(systemSymbolName:)`），
            // 两处各写各的就会变成"同一个入口在两台机器上长得不一样"（BACKLOG 164）。
            MenuBarExtra {
                MenuBarRecommendationsView(historyStore: historyStore, appDelegate: appDelegate)
                Divider()
                ForEach(AppCommandCatalog.menuBarCommands.filter { $0 != .quit }, id: \.self) { command in
                    Button(MenuShortcutPresentation.title(
                        command.title,
                        hint: appDelegate.menuShortcutHint(for: command)
                    )) {
                        appDelegate.perform(command)
                    }
                    .modifier(MenuCommandShortcutModifier(command: command))
                }
                Divider()
                Button(AppCommand.quit.title) {
                    appDelegate.perform(.quit)
                }
                .modifier(MenuCommandShortcutModifier(command: .quit))
            } label: {
                // R418：暂停时菜单栏那颗图标要有一道斜杠（BACKLOG 443）。
                // 标签视图自己引用 `MenuBarController.statusSymbolName`，与 12 那颗图同一个名字。
                MenuBarStatusLabel()
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
