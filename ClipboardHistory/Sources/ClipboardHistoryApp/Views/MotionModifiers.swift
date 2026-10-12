import SwiftUI

/// 符号图标"换了一个"或"状态被改了"时的过渡。
///
/// 为什么要有这一层：`Image(systemName:)` 换了符号名，默认表现是**啪地换成另一个图标**，
/// 用户不知道是"我按的东西生效了"还是"界面自己跳了"。系统给了两个连续性的表达：
/// - macOS 14+：`.contentTransition(.symbolEffect(.replace))`（形状连续地变过去）、
///   `.symbolEffect(.bounce, value:)`（值变了弹一下）；
/// - macOS 12：两个 API 都没有 ⇒ 退化成**交叉淡入**（身份变了 + `.transition(.opacity)`），
///   信息量一样（"这里变了"），只是没有弹性。
///
/// 减弱动态时按目录的规矩：**保留淡入、去掉弹跳**。
/// 淡入是"告诉你这里变了"，弹跳是"让你看见我动了" —— 前者是信息，后者才是前庭触发源。
struct SymbolMotion: ViewModifier {
    /// 当前符号名。macOS 12/13 那一档要靠它制造身份变化（见下面注释）。
    let symbol: String
    /// 符号本身会变的按钮（收藏 / 固定 / 已复制）：换符号时给一次连续过渡。
    ///
    /// 这里**曾经**还有第三条路：`symbolEffect(.bounce, value:)`。它被删掉是因为它永远走不到
    /// —— 收藏/固定两颗按钮恒传一个非 nil 的 `bounceValue`，于是 14+ 正常态**只**跑 bounce、
    /// 永远跑不到 `replace`，而 `replace` 才是"符号换了"这件事的表达。
    /// 三条分支里两条互斥、一条被恒真参数挡死，纯值测试完全看不见（它测的是 `MotionCatalog`，
    /// 不是分支可达性）—— 报告 MC-12。
    /// 另一个方向也成立：复制/粘贴是每天上百次的动作，按频率闸门本来就不该给它弹跳。
    var replacesSymbol = false

    func body(content: Content) -> some View {
        if replacesSymbol, #available(macOS 14.0, *) {
            content.contentTransition(.symbolEffect(.replace))
        } else if replacesSymbol {
            // macOS 12/13：没有符号替换 API，就靠"身份变了 + 淡入"表达同一件事。
            // `.id(symbol)` 只在这一档出现 —— 14+ 的 `contentTransition` 要求视图身份**连续**，
            // 在那里加 id 等于把系统给的连续过渡换成一次重建。
            content.id(symbol).transition(MotionCatalog.transition(for: .contentFade))
        } else {
            content
        }
    }
}

extension View {
    /// 符号状态反馈的唯一入口（见 `SymbolMotion` 的注释）。
    func symbolMotion(symbol: String, replacesSymbol: Bool = false) -> some View {
        modifier(SymbolMotion(symbol: symbol, replacesSymbol: replacesSymbol))
    }
}
