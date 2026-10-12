import Foundation

/// 「清空未收藏记录」的回执（视觉迭代 R6 / 审计 B-P1-2）。
///
/// 为什么单独一个纯函数：这一句要回答的是"我刚刚那一下到底删了多少、留下了多少"，
/// 而**数字必须是动手之前数出来的** —— `HistoryStore.perform(.clear)` 之后
/// `entries` 只剩收藏，那时候再数就永远得到"清空了 0 条"。
/// 把"数"与"说"收在这里，调用点只剩一行薄胶水，`HistoryStore` 不新增任何方法
/// （AGENTS.md：Store 只减不加，新特性先建 `*Policy` / `*Planner`）。
///
/// 输入刻意取 `[Bool]` 而不是 `[HistoryStore.Entry]`：纯函数不该为了拿一个
/// `isFavorite` 而去依赖一个 `@MainActor` 的存储类型 —— 那样这条判据就没法在
/// 不开窗口、不建 Store 的情况下被断言（本仓库为这类耦合记过不止一次）。
enum ClearHistoryReceiptPolicy {
    /// 一次清空会删掉多少、保留多少。
    struct Tally: Equatable {
        let removed: Int
        let kept: Int
    }

    static func tally(isFavorites: [Bool]) -> Tally {
        let kept = isFavorites.filter { $0 }.count
        return Tally(removed: isFavorites.count - kept, kept: kept)
    }

    /// 回执正文。
    ///
    /// 措辞上的两条规矩（第三轮 U-5"状态语言统一"）：
    /// ① 说清发生了什么 + 说清还剩什么 —— 一次不可撤销的删除之后，
    ///    用户第一件要问的是"我的收藏还在吗"；
    /// ② 0 条也要出声。"没有可清空的记录"是一句**回执**，
    ///    沉默会让用户以为按钮坏了，然后去多点两下。
    static func text(tally: Tally) -> String {
        if tally.removed == 0 {
            return "没有可清空的记录（\(tally.kept) 条收藏保留）。"
        }
        return "已清空 \(tally.removed) 条未收藏记录，\(tally.kept) 条收藏保留。"
    }

    static func receipt(isFavorites: [Bool]) -> String {
        text(tally: tally(isFavorites: isFavorites))
    }
}
