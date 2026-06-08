import SwiftUI

@main
struct ClipboardHistoryApp: App {

    @StateObject private var historyStore = HistoryStore()
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView(historyStore: historyStore)
                .frame(minWidth: 600, minHeight: 400)
                .onAppear {
                    appDelegate.configure(historyStore: historyStore)
                }
                .background(WindowConfigurator())
        }
        .windowStyle(.hiddenTitleBar)

        if #available(macOS 13, *) {
            MenuBarExtra("时间剪史", systemImage: "clipboard") {
                Text("时间剪史")
                quickCopyItems
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

    @ViewBuilder
    private var quickCopyItems: some View {
        ForEach(QuickCopyMenu.sections(entries: historyStore.entries)) { section in
            Divider()
            Text(section.title)
            ForEach(section.entries) { entry in
                Button {
                    appDelegate.copyHistoryEntry(id: entry.id)
                } label: {
                    Label(
                        EntryPresentation.privateMenuTitle(for: entry),
                        systemImage: EntryPresentation.menuSymbol(for: entry)
                    )
                }
            }
        }
    }
}
