import Foundation

/// 「这一次要不要真去取预览」的决定 —— 纯函数，可断言。
///
/// 为什么要把一行 `guard` 提成函数：`freezeLoadingForCapture` 是**默认关闭**的注入点（R211 / BACKLOG 233），
/// 而"默认关闭"这句话今天必须有证人。证人要读的是**决定**，不是注释：
/// `MediaLoadingPlanTests` 直接问"按 `DetailFileView` / `DetailView` 的默认值走，加载会不会开始"，
/// 于是有人把默认值翻成 true 时那一格会红（R213 的刀 M748 就是钉这一格）。
///
/// 形状与仓库规矩一致（AGENTS.md：新特性先建 `*Policy` / `*Planner` 纯函数，视图里只留薄胶水）。
enum MediaLoadingPlan {
    /// 冻结只该发生在**夹具主动要求**的那条路上；默认值 ⇒ 真去加载。
    static func startsLoad(freezeLoadingForCapture: Bool) -> Bool {
        !freezeLoadingForCapture
    }

    /// 加载没开始的时候，界面停在哪个阶段：0=加载骨架（与 `DetailView` 那条按值动画的键同一档）。
    static func stageWhenLoadNotStarted() -> Int { 0 }
}
