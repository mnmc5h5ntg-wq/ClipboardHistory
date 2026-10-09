import SwiftUI
import Carbon

struct HotKeyRecorderView: NSViewRepresentable {
    @Binding var shortcut: HotKeyShortcut
    let onInvalidShortcut: () -> Void

    func makeNSView(context: Context) -> HotKeyRecorderButton {
        let button = HotKeyRecorderButton()
        button.bezelStyle = .rounded
        button.setButtonType(.momentaryPushIn)
        button.target = context.coordinator
        button.action = #selector(Coordinator.startRecording(_:))
        button.onShortcutChange = { shortcut in
            context.coordinator.updateShortcut(shortcut)
        }
        button.onInvalidShortcut = onInvalidShortcut
        button.shortcut = shortcut
        return button
    }

    func updateNSView(_ nsView: HotKeyRecorderButton, context: Context) {
        nsView.shortcut = shortcut
        nsView.onInvalidShortcut = onInvalidShortcut
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(shortcut: $shortcut)
    }

    @MainActor
    final class Coordinator: NSObject {
        private let shortcut: Binding<HotKeyShortcut>

        init(shortcut: Binding<HotKeyShortcut>) {
            self.shortcut = shortcut
        }

        @objc func startRecording(_ sender: HotKeyRecorderButton) {
            sender.startRecording()
        }

        func updateShortcut(_ newShortcut: HotKeyShortcut) {
            shortcut.wrappedValue = newShortcut
        }
    }
}

final class HotKeyRecorderButton: NSButton {
    var shortcut: HotKeyShortcut = .defaultShortcut {
        didSet {
            if !isRecording {
                title = shortcut.displayString
            }
        }
    }
    var onShortcutChange: ((HotKeyShortcut) -> Void)?
    var onInvalidShortcut: (() -> Void)?

    private var isRecording = false

    override var acceptsFirstResponder: Bool { true }

    func startRecording() {
        isRecording = true
        title = "请输入快捷键"
        window?.makeFirstResponder(self)
    }

    override func keyDown(with event: NSEvent) {
        guard isRecording else {
            super.keyDown(with: event)
            return
        }

        if event.keyCode == UInt16(kVK_Escape) {
            cancelRecording()
            return
        }

        guard let newShortcut = HotKeyShortcut(event: event) else {
            onInvalidShortcut?()
            cancelRecording()
            return
        }

        shortcut = newShortcut
        isRecording = false
        // 立刻回显新组合。`shortcut` 的 didSet 在 `isRecording` 还是 true 的那一步被跳过，
        // 而以前之后再没人改过标题 —— 按钮会一直停在"请输入快捷键"，
        // 直到下一次 SwiftUI 刷新把同一个值重新赋一遍才恢复（`updateNSView`）。
        title = shortcut.displayString
        window?.makeFirstResponder(nil)
        onShortcutChange?(newShortcut)
    }

    override func resignFirstResponder() -> Bool {
        let result = super.resignFirstResponder()
        if result, isRecording {
            cancelRecording()
        }
        return result
    }

    private func cancelRecording() {
        isRecording = false
        title = shortcut.displayString
        window?.makeFirstResponder(nil)
    }
}
