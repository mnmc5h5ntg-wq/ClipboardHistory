import AppKit
import SwiftUI

struct ClipboardHistoryCommands: Commands {
    let appDelegate: AppDelegate

    var body: some Commands {
        ClipboardHistoryAppMenuCommands(appDelegate: appDelegate)
        ClipboardHistoryFileMenuCleanupCommands()
        ClipboardHistoryViewMenuCleanupCommands()
        ClipboardHistoryWindowCommands()
        ClipboardHistoryHelpCommands(appDelegate: appDelegate)
    }
}

private struct ClipboardHistoryAppMenuCommands: Commands {
    let appDelegate: AppDelegate

    var body: some Commands {
        CommandGroup(replacing: .appInfo) {
            Button("关于时间剪史") {
                appDelegate.showAboutPanel()
            }
        }
        CommandGroup(replacing: .appSettings) {
            Button(AppCommand.showSettings.title) {
                appDelegate.perform(.showSettings)
            }
            .keyboardShortcut(",", modifiers: .command)
        }
        CommandGroup(replacing: .systemServices) {
            EmptyView()
        }
        CommandGroup(replacing: .appTermination) {
            Button(AppCommand.quit.title) {
                appDelegate.perform(.quit)
            }
            .keyboardShortcut("q", modifiers: .command)
        }
    }
}

private struct ClipboardHistoryFileMenuCleanupCommands: Commands {
    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            EmptyView()
        }
        CommandGroup(replacing: .saveItem) {
            EmptyView()
        }
        CommandGroup(replacing: .importExport) {
            EmptyView()
        }
        CommandGroup(replacing: .printItem) {
            EmptyView()
        }
    }
}

private struct ClipboardHistoryViewMenuCleanupCommands: Commands {
    var body: some Commands {
        CommandGroup(replacing: .toolbar) {
            EmptyView()
        }
        CommandGroup(replacing: .sidebar) {
            EmptyView()
        }
    }
}

private struct ClipboardHistoryWindowCommands: Commands {
    var body: some Commands {
        CommandGroup(replacing: .windowArrangement) {
            Button("全部前置") {
                NSApplication.shared.arrangeInFront(nil)
            }
        }
    }
}

private struct ClipboardHistoryHelpCommands: Commands {
    let appDelegate: AppDelegate

    var body: some Commands {
        CommandGroup(replacing: .help) {
            Button("GitHub 项目主页") {
                appDelegate.openGitHubRepository()
            }
        }
    }
}
