import SwiftUI

enum NoticeTone {
    case warning
    case error

    /// 与状态规范同源：横幅只有这两种 tone，映射到 `StatePresentation.Kind` 之后，
    /// 图标、颜色、底色调都由规范决定，不再在这里各写一份（审计 §4 U-5）。
    var stateKind: StatePresentation.Kind {
        switch self {
        case .warning: return .warning
        case .error: return .error
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
        VStack(spacing: 0) {
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
        .background(StatePresentation.backgroundStyle(for: kind))
        .accessibilityElement(children: .contain)
    }
}
