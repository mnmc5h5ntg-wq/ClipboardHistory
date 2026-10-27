import SwiftUI

enum NoticeTone {
    case warning
    case error
    /// R417：暂停采集是一个**持续状态**，横幅只在它成立期间存在，动作是「继续采集」。
    case paused

    /// 与状态规范同源：横幅的 tone 全部映射到 `StatePresentation.Kind` 之后，
    /// 图标、颜色、底色调都由规范决定，不再在这里各写一份（审计 §4 U-5）。
    var stateKind: StatePresentation.Kind {
        switch self {
        case .warning: return .warning
        case .error: return .error
        case .paused: return .paused
        }
    }
}

/// 窗口顶部的一次性提示条。目前有两个使用者：存档恢复提示（R-02）与
/// 自动粘贴失败（R-13）。两者原本都是"只写进 @Published 属性，没人显示"，
/// 于是用户看不到任何解释 —— 这个视图把那半条链路补上。
struct NoticeBanner: View {
    let message: String
    var tone: NoticeTone = .warning
    let onDismiss: () -> Void
    /// 动作位文案。以前这里硬写"知道了"，而"打开历史文件夹"才是存档损坏的下一步
    /// —— 留了口子但没用它，等于规范里那句"说清下一步"没落地。
    var actionTitle: String? = nil

    var body: some View {
        let kind = tone.stateKind
        let band = VStack(spacing: 0) {
            // 那一行本身交给 `StateLine`：横幅、菜单栏状态行、空态共用同一个组件，
            // 才不会过两周又漂回三种字号（审计 §4 U-5）。
            StateLine(kind: kind,
                      message: message,
                      actionTitle: StatePresentation.actionTitle(for: kind, provided: actionTitle),
                      action: onDismiss)
                .padding(.horizontal, 14)
                .padding(.vertical, 9)

            Divider()
        }
        // **色带不许涂到标题栏与工具栏后面**（R23 / U-45）。
        //
        // 这条是量出来的，不是猜的：`content-with-two-notices` 沿一列扫色度 ——
        // 一条文字的警告横幅占了 **88pt**，其中 y 0–52 是**只有底色、没有内容**的一条，
        // 文字从 y≈60 才开始；同一帧里两行文字的错误横幅只占 50pt。
        // 根因是 SwiftUI 4 起 `.background(_:)` 对 `ShapeStyle` 的默认
        // `ignoresSafeAreaEdges` 是 `.all` ⇒ 底色铺进安全区，而文字被安全区顶下去，
        // 于是"提示条"看起来上半截是空的，并且把颜色涂到了透明标题栏（红绿灯）后面。
        // 系统的提示条（邮件/备忘录那一类）都只画内容区那一条 —— 这才是原生语言。
        //
        // macOS 12 没有这个开关（SwiftUI 3 的 `.background` 不越安全区，本来就是对的行为），
        // 所以按版本分叉，而不是找一个两边都凑合的负 padding。
        if #available(macOS 13.0, *) {
            band.background(StatePresentation.backgroundStyle(for: kind),
                            ignoresSafeAreaEdges: [])
                .accessibilityElement(children: .contain)
        } else {
            band.background(StatePresentation.backgroundStyle(for: kind))
                .accessibilityElement(children: .contain)
        }
    }
}
