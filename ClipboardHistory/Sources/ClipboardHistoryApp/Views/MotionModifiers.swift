import SwiftUI

/// 符号图标"换了一个"或"状态被改了"时的过渡。
///
/// 为什么要有这一层：`Image(systemName:)` 换了符号名，默认表现是**啪地换成另一个图标**，
/// 用户不知道是"我按的东西生效了"还是"界面自己跳了"。系统给了两个**互相独立**的表达：
/// - `contentTransition(.symbolEffect(.replace))`（14+）—— 管"符号换了"：形状连续地变过去；
/// - `symbolEffect(.bounce, value:)`（14+）—— 管"我按到了"：值变了弹一下
///   （HIG 给它的语义正是 "an action occurred"）；
/// - macOS 12/13 两个 API 都没有 ⇒ 退化成**交叉淡入**（身份变了 + `.transition(.opacity)`），
///   信息量一样（"这里变了"），只是没有弹性。
///
/// 这两件事**要同时挂**，别再写成 if/else。上一版它们是互斥分支，而收藏/固定两颗按钮恒传一个
/// 非 nil 的 `bounceValue` ⇒ 14+ 正常态只跑 bounce、永远跑不到 replace（报告 MC-12）。
/// 当时我选的修法是"把 bounce 删掉"，那等于把两条一起砍，也顺手把报告 M5 要的"弹一下"砍没了
/// —— 那是修过头。现在按报告给的另一个选项做：**replace 打底，bounce 叠加**。
///
/// 减弱动态时按目录的规矩：**保留形变/淡入、去掉弹跳**。
/// 淡入是"告诉你这里变了"，弹跳是"让你看见我动了" —— 前者是信息，后者才是前庭触发源。
struct SymbolMotion: ViewModifier {
    /// 当前符号名。macOS 12/13 那一档要靠它制造身份变化（见下面注释）。
    let symbol: String
    /// 符号本身会变的按钮（收藏 / 固定 / 已复制）：换符号时给一次连续过渡。
    var replacesSymbol = false
    /// 非 nil 时，这个值变了就弹一下（仅 14+，且未开启减弱动态）。
    /// 只给"状态被改了"的那两颗（收藏 / 固定）。**不要**给复制用 ——
    /// 那是每天上百次的动作，频率闸门（报告红线 0/8）判它不该有弹跳。
    var bounceValue: Int?

    func body(content: Content) -> some View {
        if replacesSymbol, #available(macOS 14.0, *) {
            bouncing(content.contentTransition(.symbolEffect(.replace)))
        } else if replacesSymbol {
            // macOS 12/13：没有符号替换 API，就靠"身份变了 + 淡入"表达同一件事。
            // `.id(symbol)` 只在这一档出现 —— 14+ 的 `contentTransition` 要求视图身份**连续**，
            // 在那里加 id 等于把系统给的连续过渡换成一次重建。
            content.id(symbol).transition(MotionCatalog.transition(for: .contentFade))
        } else {
            bouncing(content)
        }
    }

    /// 叠加就这一行；单独抽出来是为了让"减弱动态 ⇒ 不弹"只有一处写法。
    @ViewBuilder
    private func bouncing<V: View>(_ view: V) -> some View {
        if let bounceValue, !MotionCatalog.motionShouldBeReduced, #available(macOS 14.0, *) {
            view.symbolEffect(.bounce, value: bounceValue)
        } else {
            view
        }
    }
}

extension View {
    /// 符号状态反馈的唯一入口（见 `SymbolMotion` 的注释）。
    func symbolMotion(symbol: String, replacesSymbol: Bool = false, bounceValue: Int? = nil) -> some View {
        modifier(SymbolMotion(symbol: symbol, replacesSymbol: replacesSymbol, bounceValue: bounceValue))
    }
}
