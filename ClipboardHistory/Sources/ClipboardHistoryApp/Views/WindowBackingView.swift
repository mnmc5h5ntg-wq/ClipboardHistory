import AppKit

/// R568（规格 `docs/FOLD_DUO_SPEC_2026-11-03.md` D4a）：主窗口要能「让位」——右页 alpha 归零
/// 之后露出桌面 —— 前提是窗口**非不透明**。而窗口一旦非不透明，SwiftUI 那层 vibrancy 材质就开始
/// 采样桌面：真机合成通道同一条侧栏带现读 **0.9339 → 0.6637**、并漏进 **319** 个背景像素
/// （读数 `TRANSPARENCY_MATERIAL_NEG`，规格 §4 第一条的答案是"会"）。
///
/// 这一层底衬把「今天窗口本身是不透明的」这个事实**显式搬进内容层**：窗口可以非不透明，
/// 而观感与今天逐字相同。证人三条，都不靠眼睛：
/// ① 判据 `testTheProductWindowIsNonOpaqueWithItsOwnOpaqueBacking` 读带内 alpha 必须处处 255；
/// ② 356 张基线帧 `frame_baseline.py compare` 不许变；
/// ③ 负臂（刀 **M1480** 撤掉这一层）⇒ 同一条带立刻移动 0.2702、品红又漏回来 —— 没有这一条，
///    上面两条证明的只是"一件永远不会发生的事"。
///
/// 代价要说清并留给第③段：加了底衬之后侧栏材质**不再采样桌面** —— 今天它也不采样（窗口是 opaque 的），
/// 所以对用户没有变化；但第③段真要「露出桌面」时，必须在右页那一侧把这一层撤掉，
/// 那是那一段的靶，本轮不做（§3 的闸门顺序）。
@MainActor
final class WindowBackingView: NSView {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        commonInit()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        commonInit()
    }

    private func commonInit() {
        wantsLayer = true
        autoresizingMask = [.width, .height]
    }

    /// 颜色必须**跟着外观现读**：把 `cgColor` 写死一次，用户切深浅色之后这层会留在旧色上 ——
    /// 那是把本轮要修的观感问题换成一个新问题。
    override var wantsUpdateLayer: Bool { true }

    override func updateLayer() {
        layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        needsDisplay = true
    }

    /// 底衬不参与命中：命中要落到内容那一层。这条约定今天**可观察**的是"赢的是谁"
    /// （读数 `TRANSPARENCY_HITTEST`）—— 窗口级的点击穿透不靠它：容器在那块内容没覆盖的空区
    /// 仍然返回自己，所以像素 alpha 不路由鼠标，第③段真要穿透得显式用 `contentShape`/`ignoresMouseEvents`。
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
}

/// 容器：底衬在下、SwiftUI 内容在上。为什么不能把底衬当 `NSHostingView` 的 subview 加进去 ——
/// 本轮实测：那样加之后离屏捕获里**右半页整片是 alpha=0**（`x[853..1672] y[118..1238]`，
/// 洞正好从中缝 424pt 起），因为底衬被塞进了 hosting view 自己的绘制层里，只盖住了侧栏那一片。
/// 容器把顺序摆明：先加底衬、后加内容，内容没画到的地方露出来的是底衬，不是桌面。
@MainActor
final class WindowBackingContainer: NSView {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        addSubview(WindowBackingView(frame: bounds))
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        addSubview(WindowBackingView(frame: bounds))
    }

    /// 把内容视图包进容器（已经包过就不重复包 —— 配置器会被多次调用）。
    static func wrapping(_ content: NSView) -> NSView {
        if content is WindowBackingContainer || content.superview is WindowBackingContainer {
            return content
        }
        let container = WindowBackingContainer(frame: content.bounds)
        content.autoresizingMask = [.width, .height]
        content.frame = container.bounds
        container.addSubview(content)
        return container
    }
}
