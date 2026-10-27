import AppKit
import Carbon
import SwiftUI

/// 「正在录制」这一档的表达（R141 / BACKLOG 173 点的那一次真动效）。
///
/// 为什么这一处该有视觉反馈，而多数地方不该：这颗按钮在录制态会**吃掉所有按键** ——
/// 用户按下去的东西不再进任何 App，而是被这里当成组合键记下来。产品以前只用一句标题
/// （「请输入快捷键」）说这件事，而且是**瞬间换字**：字换了，可它还是同一个灰 bezel，
/// 于是「我在听」这件事在屏幕上没有形状。失焦会自动退出录制，
/// 但一个不知道自己有没有在听的人不会去试失焦。
///
/// 为什么是这一种反馈：不新造一档语言。这个窗口里「字段在接收输入」本来就有说法 ——
/// 搜索框那一条（`VisualFill.fieldActive` / `VisualStroke.fieldActiveStroke`，R76 量过焦点档）。
/// 录制器本质上就是一个在听键字的字段，所以它借用**强调色描边**：宽度取
/// `VisualStroke.highlight`（1.5pt，与命中高亮同一档），不常驻、不脉动
/// （全仓唯一的常驻时钟是骨架扫光，见 `SkeletonShimmer`；再加一条常驻动效就等于没有）。
///
/// 状态不许押在动画上：`strokeWidth(isRecording:)` 是**模型值**，减弱动态时只是不淡入，
/// 描边照样在。这条由真值表判，不由帧判（中间态在离屏通道里量不到，R11 那一族）。
enum HotKeyRecorderEmphasis {
    /// 静置 = 0pt：这一层逐像素等于不存在，所以旧帧不许变（帧基线 `CHANGED=0` 的前提）。
    static func strokeWidth(isRecording: Bool) -> CGFloat {
        isRecording ? VisualStroke.highlight : 0
    }

    /// 静置 = 透明。不用「不画」之外的第二种"没有"，免得色度轴上留下说不清的读数。
    static func strokeColor(isRecording: Bool) -> NSColor {
        isRecording ? .controlAccentColor : .clear
    }
}

/// 描边本体。抽出来的理由与 R45 的 `DailyCopyHeatmapCell(isHovered:)` 一样：
/// **触发**（真的点下去、真的进录制态）与**表达**（这一圈长什么样）是两件事 ——
/// 前者在离屏通道里做不到（R14：三条合成 hover 通道全断），后者必须可离线渲染、可量。
struct HotKeyRecorderRing: View {
    let isRecording: Bool

    var body: some View {
        // 圆角一律走 `VisualShape.rounded`：产品里只允许那一处 `RoundedRectangle(cornerRadius:)`
        // （R15 立的规矩，由 `VisualTokenTests.testCornersComeFromTheShapeFactory` 钉住 ——
        //  这一处第一版就是自己构了圆角矩形，被它当场拦下）。
        VisualShape.rounded(VisualRadius.control)
            .strokeBorder(Color(nsColor: HotKeyRecorderEmphasis.strokeColor(isRecording: isRecording)),
                          lineWidth: HotKeyRecorderEmphasis.strokeWidth(isRecording: isRecording))
            // 描边盖在按钮上面，不许替按钮接点击：接了就会把「点一下进录制」这条路整个吃掉。
            .allowsHitTesting(false)
    }
}

/// 快捷键录制器。**调用点签名不变**（`SettingsView:807` 那三行照旧），
/// 只是从「一个 NSViewRepresentable」变成「一个包着 representable 的 SwiftUI 视图」——
/// representable 自己的 body 就是那颗 `NSButton`，没法给它加 overlay，所以分两层。
struct HotKeyRecorderView: View {
    @Binding var shortcut: HotKeyShortcut
    let onInvalidShortcut: () -> Void
    /// R412：**只报告**按钮自己翻出来的那个状态，不另立一份真值 ——
    /// 设置行拿它画「这一行正在吃键」，状态的所有权仍在按钮。
    var onRecordingChange: (Bool) -> Void = { _ in }
    /// 由按钮自己翻，不让调用方再持一份：快捷键页有三行，多一处真值就会与按钮不一致。
    @State private var isRecording = false

    var body: some View {
        HotKeyRecorderField(shortcut: $shortcut,
                            onInvalidShortcut: onInvalidShortcut,
                            onRecordingChange: { recording in
                                // `@State.wrappedValue` 的 setter 是 nonmutating，
                                // 所以在逃逸闭包里赋值是合法的。
                                isRecording = recording
                                onRecordingChange(recording)
                            })
            .overlay(HotKeyRecorderRing(isRecording: isRecording))
            // `.emphasis`（0.16s）：进入录制是用户自己点出来的，反馈要"立刻在"，
            // 但换字与描边同时瞬切会读成闪烁 —— 与 `DetailView` 的强调同一档。
            .animation(MotionCatalog.animation(for: .emphasis), value: isRecording)
    }
}

/// 原来那个 `HotKeyRecorderView` 的本体，改名后成为内层。
struct HotKeyRecorderField: NSViewRepresentable {
    @Binding var shortcut: HotKeyShortcut
    let onInvalidShortcut: () -> Void
    /// 录制态进出各调一次，且在主线程（全部来自 AppKit 的调用栈）。
    var onRecordingChange: (Bool) -> Void = { _ in }

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
        button.onRecordingChange = onRecordingChange
        button.shortcut = shortcut
        return button
    }

    func updateNSView(_ nsView: HotKeyRecorderButton, context: Context) {
        nsView.shortcut = shortcut
        nsView.onInvalidShortcut = onInvalidShortcut
        nsView.onRecordingChange = onRecordingChange
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
            updateHelp()
        }
    }
    var onShortcutChange: ((HotKeyShortcut) -> Void)?
    var onInvalidShortcut: (() -> Void)?
    /// 录制态的**唯一对外出口**。R141 之前这个状态是私有的：标题换了，
    /// 而 SwiftUI 侧完全不知道它在听 —— 所以那一圈描边没有东西可跟。
    var onRecordingChange: ((Bool) -> Void)?

    private(set) var isRecording = false

    override var acceptsFirstResponder: Bool { true }

    /// R438：这颗按钮以前**没有任何帮助文本** —— 用户看不出灰键帽可点，也不知道 Esc 能取消。
    /// 帮助随录制态换一句（同一处出口，避免两种状态各写一份）。
    private func updateHelp() {
        let text = isRecording
            ? "请输入快捷键；按 Esc 取消"
            : "点一下重新录制；按 Esc 取消"
        toolTip = text
        setAccessibilityHelp(text)
    }

    func startRecording() {
        // 「我在听」这一圈是一个**承诺**：按下去的键会被这里吃掉。所以拿不到响应者链的时候
        // 不许亮 —— R143 的审查轮指出：原来 `makeFirstResponder` 的返回值被丢掉，
        // 于是"窗口在、但链没接上"这一格会画出一圈假的承诺。
        // 没有窗口（单元测试里就是这种）不做这个判断：那时既没有承诺也没有观众。
        if let window = window, !window.makeFirstResponder(self) {
            NSSound.beep()
            return
        }
        setRecording(true)
        title = "请输入快捷键"
        updateHelp()
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
        setRecording(false)
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
        setRecording(false)
        title = shortcut.displayString
        window?.makeFirstResponder(nil)
    }

    /// 只在这里翻状态、只在这里出口 —— 于是「一次转换演两遍」这种错
    /// 在结构上就写不出来（`keyDown` 提交与 `resignFirstResponder` 都会走到退出）。
    private func setRecording(_ next: Bool) {
        guard isRecording != next else { return }
        isRecording = next
        updateHelp()
        onRecordingChange?(next)
    }
}
