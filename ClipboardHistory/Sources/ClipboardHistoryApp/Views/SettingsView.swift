import SwiftUI

struct SettingsView: View {
    @ObservedObject private var showMainWindowHotKeySettings: HotKeySettings
    @ObservedObject private var repeatCopyHotKeySettings: HotKeySettings
    @ObservedObject private var loginItemSettings: LoginItemSettings
    @State private var showMainWindowShortcut: HotKeyShortcut
    @State private var repeatCopyShortcut: HotKeyShortcut
    @State private var launchAtLogin: Bool

    init(
        showMainWindowHotKeySettings: HotKeySettings,
        repeatCopyHotKeySettings: HotKeySettings,
        loginItemSettings: LoginItemSettings
    ) {
        self.showMainWindowHotKeySettings = showMainWindowHotKeySettings
        self.repeatCopyHotKeySettings = repeatCopyHotKeySettings
        self.loginItemSettings = loginItemSettings
        _showMainWindowShortcut = State(initialValue: showMainWindowHotKeySettings.shortcut)
        _repeatCopyShortcut = State(initialValue: repeatCopyHotKeySettings.shortcut)
        _launchAtLogin = State(initialValue: loginItemSettings.isEnabled)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("快捷键")
                .font(.headline)

            GroupBox {
                VStack(spacing: 12) {
                    HotKeySettingsRow(
                        settings: showMainWindowHotKeySettings,
                        shortcut: $showMainWindowShortcut
                    )

                    Divider()

                    HotKeySettingsRow(
                        settings: repeatCopyHotKeySettings,
                        shortcut: $repeatCopyShortcut
                    )
                }
            }

            Text("启动")
                .font(.headline)

            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Toggle("开机启动", isOn: $launchAtLogin)
                        .disabled(!loginItemSettings.isSupported)

                    if let message = loginItemSettings.message {
                        Text(message)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(20)
        .frame(width: 460)
        .onAppear {
            loginItemSettings.refresh()
            launchAtLogin = loginItemSettings.isEnabled
        }
        .onChange(of: showMainWindowShortcut) { newValue in
            saveShowMainWindowShortcut(newValue)
        }
        .onChange(of: showMainWindowHotKeySettings.shortcut) { newValue in
            showMainWindowShortcut = newValue
        }
        .onChange(of: repeatCopyShortcut) { newValue in
            saveRepeatCopyShortcut(newValue)
        }
        .onChange(of: repeatCopyHotKeySettings.shortcut) { newValue in
            repeatCopyShortcut = newValue
        }
        .onChange(of: launchAtLogin) { newValue in
            saveLaunchAtLogin(newValue)
        }
        .onChange(of: loginItemSettings.isEnabled) { newValue in
            launchAtLogin = newValue
        }
    }

    private func saveShowMainWindowShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != showMainWindowHotKeySettings.shortcut else { return }
        if !showMainWindowHotKeySettings.save(shortcut) {
            showMainWindowShortcut = showMainWindowHotKeySettings.shortcut
        }
    }

    private func saveRepeatCopyShortcut(_ shortcut: HotKeyShortcut) {
        guard shortcut != repeatCopyHotKeySettings.shortcut else { return }
        if !repeatCopyHotKeySettings.save(shortcut) {
            repeatCopyShortcut = repeatCopyHotKeySettings.shortcut
        }
    }

    private func saveLaunchAtLogin(_ enabled: Bool) {
        guard enabled != loginItemSettings.isEnabled else { return }
        loginItemSettings.setEnabled(enabled)
    }
}

private struct HotKeySettingsRow: View {
    @ObservedObject var settings: HotKeySettings
    @Binding var shortcut: HotKeyShortcut

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(settings.action.title)
                    Text(settings.action.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer(minLength: 24)

                HotKeyRecorderView(
                    shortcut: $shortcut,
                    onInvalidShortcut: {
                        settings.recordInvalidShortcut()
                    }
                )
                .frame(width: 128, height: 28)

                Button("恢复默认") {
                    settings.reset()
                    shortcut = settings.shortcut
                }
            }

            if let message = settings.message {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }
}
