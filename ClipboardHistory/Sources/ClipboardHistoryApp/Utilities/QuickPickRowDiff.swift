import Foundation

/// 快速选择浮层的**行级更新计划**：旧 id 序列 → 新 id 序列，拆成 AppKit 能直接执行的三步。
///
/// 为什么要单独一个纯函数（AGENTS.md 的"新逻辑先落到 *Policy / *Planner，Store/Controller
/// 里只留薄胶水"）：动效审计 M1 的结论是 **SwiftUI `List` 拿不到行过渡**（四种写法实测全部
/// 一帧到位，见 D-055），而这个浮层是**真 `NSTableView`** —— 报告 §12.4 / §12.7 给的替代路径
/// 就是走它自己的原生行动画（`insertRows(at:withAnimation:)` / `removeRows(at:withAnimation:)`
/// 配 `.effectFade`，macOS 10.7 起；MiaoYan `Views/NotesTableView.swift:623,705-707` 是同类先例，
/// 零依赖）。**标签拼写更正过报告**：报告 §12.4/§351 写的是 `insertRows(at:with:)`，
/// 那是 Objective-C 选择器的样子，从 Swift 里按 `with:` 和 `animationOptions:` 都编不过
/// （"extra argument 'with' in call"），正确的外名是 `withAnimation:` —— 由 `swift build` 的 0 错误定。
///
/// 原生行动画的前提是"别再 `reloadData()` 一把梭"，而要告诉表格**哪些行走了、哪些行来了**。
/// 那件事的正确性完全取决于索引推进的顺序，所以把它抽出来，配真值表测。
enum QuickPickRowDiff: Equatable, Sendable {
    /// 三步的**下标空间**不同，这是这套 API 最容易搞错的地方：
    /// `removals` 是**旧**下标，`insertions` 与 `reloads` 是**新**下标。
    /// 删与插发生在同一个 `beginUpdates/endUpdates` 批次里（AppKit 按这个次序解释它们）；
    /// 刷新刻意排在批次**之后**，这样它读到的就是落定的新下标，与 `reloads` 同一套坐标。
    struct Plan: Equatable, Sendable {
        var removals: IndexSet = IndexSet()
        var insertions: IndexSet = IndexSet()
        /// 位置与身份都没变、但内容（标题文案）变了的那几行。
        var reloads: IndexSet = IndexSet()
        /// 保留下来的行**相对顺序变了**（例如刚复制的那条被顶到最前）。
        /// 原生行动画处理不了"整体重排"，这时只能退回整表刷新 —— 明说，不假装成功。
        var needsFullReload = false

        var isNoop: Bool { removals.isEmpty && insertions.isEmpty && reloads.isEmpty && !needsFullReload }
    }

    /// `titles` 只用来判"内容变没变"（同一条记录的文案会随时间/来源显示不同）。
    static func plan(oldIDs: [UUID], oldTitles: [String], newIDs: [UUID], newTitles: [String]) -> Plan {
        precondition(oldIDs.count == oldTitles.count && newIDs.count == newTitles.count,
                     "id 与文案必须一一对应，否则下面的下标全是错的")
        var plan = Plan()
        let oldSet = Set(oldIDs), newSet = Set(newIDs)
        // 这里**曾经**有一条"重复 id 就退回整表刷新"的显式前置判断，删掉是因为变异对照打不红它：
        // 把 `if oldIDs.count != oldSet.count …` 改成 `if false`，`testDuplicateIDsFallBackToFullReload`
        // 照样通过 —— 因为重复 id 一定会让下面那句"保留行的相对顺序"先不一致（`[a,a] != [a]`），
        // 那条判据已经把这件事覆盖了。留下两个入口只会让读者以为重复是靠这里拦的。
        // 现在由 `testDuplicateIDsFallBackToFullReload` 直接断言**行为**（重复 ⇒ 整体重排 ⇒ 整表刷新），
        // 它是可被打红的（关掉保留顺序检查就红，见账本 U-20 的变异表）。

        for (index, id) in oldIDs.enumerated() where !newSet.contains(id) {
            plan.removals.insert(index)
        }
        for (index, id) in newIDs.enumerated() where !oldSet.contains(id) {
            plan.insertions.insert(index)
        }
        // 删完之后剩下的行，其相对顺序必须已经等于新序列里"共有"那部分的顺序；
        // 不等就是整体重排，`.effectFade` 那套 API 表达不了。
        let keptOld = oldIDs.filter { newSet.contains($0) }
        let keptNew = newIDs.filter { oldSet.contains($0) }
        if keptOld != keptNew {
            plan.needsFullReload = true
            plan.removals = []
            plan.insertions = []
            plan.reloads = []
            return plan
        }
        // 共有行按新下标原地刷新文案（删过之后，新序列里这些行的位置就是它们的位置）。
        for (index, id) in newIDs.enumerated() where oldSet.contains(id) {
            let oldIndex = oldIDs.firstIndex(of: id) ?? index
            if oldTitles.indices.contains(oldIndex), newTitles[index] != oldTitles[oldIndex] {
                plan.reloads.insert(index)
            }
        }
        return plan
    }
}
