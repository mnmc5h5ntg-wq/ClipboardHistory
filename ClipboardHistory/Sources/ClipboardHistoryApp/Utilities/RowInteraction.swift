import AppKit
import SwiftUI

/// 列表行上手势的判定逻辑。
///
/// 为什么要单独抽出来：这些判断决定"点一下会发生什么"，属于会被误改又最难肉眼发现的那类
/// （尤其"带修饰键时不要复制"这种例外），放进视图里就只能靠手点验证。
enum RowDoubleTap {
    /// 双击一行是否执行"复制这条"。
    ///
    /// 按住 shift / command 时**不复制**：这两个键在本列表里是"范围选择 / 多选"的手势前缀
    /// （见 `HistorySidebarView.select(_:)`），用户在多选过程中误双击一下，
    /// 不该把一条记录写进剪贴板并把它顶到列表最前。其余修饰键（如 control）不参与选择语义，照常复制。
    static func shouldCopy(modifiers: NSEvent.ModifierFlags) -> Bool {
        modifiers.isDisjoint(with: [.shift, .command])
    }
}

/// 收藏切换的呈现。行内星标与详情区浮层按钮共用同一份符号与文案 ——
/// 以前两处各写各的（`GlassPill` 里一份、`HistoryRow` 里一份），改一处忘一处正是审计第二轮 1.9 那类不一致的来源。
enum FavoriteTogglePresentation {
    static func symbolName(isFavorite: Bool) -> String {
        isFavorite ? "star.fill" : "star"
    }

    static func helpText(isFavorite: Bool) -> String {
        isFavorite ? "取消收藏" : "收藏"
    }

    /// 已收藏的颜色。这是量出来的，不是挑的（`scripts/frame_audit.py` + 离屏帧，方法记在 `AGENT_UI_AUDIT.md`）：
    /// `Color.yellow` 在亮色行底上只有 **1.67:1**（暗色 10.81:1），而"已收藏"恰恰是最该被看见的那一态；
    /// `Color.orange` 仍只有 **2.68:1**；再压深一档（下面这个 RGB）实测 **亮色 3.90:1 / 暗色 4.28:1**，
    /// 两边都过"可交互控件 ≥3:1"。深浅两态共用一个色值，因为这一版在两种底色下都达标 ——
    /// 换底色或换行高时要重新量，别把这个数当常数。
    static var favoriteColor: Color { Color(red: 0.86, green: 0.45, blue: 0.0) }
}
