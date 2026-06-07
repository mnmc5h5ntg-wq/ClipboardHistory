import SwiftUI

struct SettingsView: View {
    @ObservedObject private var hotKeySettings: HotKeySettings
    @State private var showMainWindowShortcut: HotKeyShortcut

    init(hotKeySettings: HotKeySettings) {
        self.hotKeySettings = hotKeySettings
        _showMainWindowShortcut = State(initialValue: hotKeySettings.shortcut)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("快捷键")
                .font(.headline)

            GroupBox {
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("呼出主窗口")
                        Text("关闭或隐藏主窗口后，可使用此快捷键重新打开。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    Spacer(minLength: 24)

                    HotKeyRecorderView(
                        shortcut: $showMainWindowShortcut,
                        onInvalidShortcut: {
                            hotKeySettings.recordInvalidShortcut()
                        }
                    )
                    .frame(width: 128, height: 28)

                    Button("恢复默认") {
                        resetShortcut()
                    }
                }

                if let message = hotKeySettings.message {
                    Text(message)
                        .font(.caption)
                        .foregroundStyle(.red)
                }
            }
        }
        .padding(20)
        .frame(width: 460)
        .onChange(of: showMainWindowShortcut) { newValue in
            saveShortcut(newValue)
        }
        .onChange(of: hotKeySettings.shortcut) { newValue in
            showMainWindowShortcut = newValue
        }
    }

    private func saveShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != hotKeySettings.shortcut else { return }
        if !hotKeySettings.save(shortcut) {
            showMainWindowShortcut = hotKeySettings.shortcut
        }
    }

    private func resetShortcut() {
        hotKeySettings.reset()
        showMainWindowShortcut = hotKeySettings.shortcut
    }
}
