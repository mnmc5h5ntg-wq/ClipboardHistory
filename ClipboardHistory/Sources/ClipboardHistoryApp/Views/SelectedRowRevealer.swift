import AppKit
import SwiftUI

/// 「把当前选中的那一行滚进视口」——BACKLOG 61 的修法本体（R61）。
///
/// 为什么需要它（全是本轮在屏实测，四臂读数见 `UIInteractionProbeTests
/// .testOffScreenProgrammaticSelectionIsDroppedAndNothingPretendsOtherwise`）：
/// * `List(selection:)` **不会选中视口外的行**：store 里 1 条、表格 `selectedRowIndexes=[]`。
///   于是详情区在讲一条列表里根本没有高亮的记录（纯采集路径就能到，见同文件的
///   `testIntakeBehindATallPinnedBlockSelectsARowTheListCannotShow`：开头固定 K 条、
///   视口只装 2.6 行时，`add()` 把新记录落在第 K 行 = 视口外，全程没有一次点击）。
/// * 把那一行**滚进视口，SwiftUI 自己就把选中补回来了**（3/3 次稳定读出 `selectedRowIndexes=[60]`，
///   不需要再走一次选中入口）。所以缺的确实只是"揭示"这一步。
/// * SwiftUI 自家的 `ScrollViewReader` + `.id` + `scrollTo` 在这棵树上**不滚**
///   （带 anchor、不带 anchor 都试过；胶水确实执行了、id 也解析到了）。同一份形状在孤立 spike 里能滚，
///   六臂 bisect 没找到是哪一件按死的 —— 结论是"这条路在产品侧不成立"，不是"再调调看"。
///   `HistorySidebarView.swift` 里有一条守卫钉住这个结论：不许在没有重测的情况下再写 scrollTo。
///
/// 职责边界（这条是本文件最重要的一句话）：**只滚，不选**。
/// 选中集的作者仍然是 `List(selection:)`（D-1 修法③），store 只是落状态。
/// 一旦这里出现 `selectRowIndexes`，就有了第二个作者，而 D-1 当年正是为了消灭第二个作者才做的。
enum SelectionRevealPlan {
    /// 选中项在**可见顺序**里的行号。取不到就返回 nil（不滚）。
    ///
    /// `nil` 的三种情形都要走到"什么都不做"：没有选中、选中项被筛掉/搜掉了、
    /// 以及选中集合是空的（多选后清空）。这时候硬猜一个 0 会把视口甩到第一条 ——
    /// 那是"用一个错的行号做一次真的滚动"，比不滚更坏。
    static func rowIndex(of selectedID: HistoryStore.Entry.ID?,
                         in visibleOrder: [HistoryStore.Entry.ID]) -> Int? {
        guard let selectedID else { return nil }
        return visibleOrder.firstIndex(of: selectedID)
    }
}

/// 揭示的**运动**（R413）：跨视口长跳才有过程，近步与减弱动态仍瞬移。
///
/// 为什么要有阈值而不是"每次都演"：方向键是一行一行走的，一次按键的位移只有一行高。
/// 给这种零位移反馈套 0.20s 的滑动，读起来不是"移过去了"，而是"按键粘住了"。
/// 长跳（新记录落在固定块之后、程序化选中视口外几十行）才是需要空间连续性的那一格 ——
/// 中间帧要让眼睛看见"我从哪来"。
///
/// 时长取 `.slider`（0.20）而不是 `.selection`（0.12）：目录里 `.slider` 的注释写的是
/// "位移越长，时长越要跟上，否则读起来像它跳过去了"；这一格正是位移，不是底色淡入。
/// 判据不押在动画上：`isAnimated` 是模型值，减弱动态时只是 instant，视口照样到目标。
enum SelectionRevealMotion {
    struct Plan: Equatable {
        let isAnimated: Bool
        let duration: TimeInterval
    }

    static func plan(distance: CGFloat, viewportHeight: CGFloat, reduceMotion: Bool) -> Plan {
        guard !reduceMotion, viewportHeight > 0, distance > viewportHeight else {
            return Plan(isAnimated: false, duration: 0)
        }
        return Plan(isAnimated: true, duration: MotionCatalog.duration(for: .slider))
    }
}

/// 挂在侧栏 `List` 上的透明宿主视图：它的唯一动作是 `scrollRowToVisible`。
struct SelectedRowRevealer: NSViewRepresentable {
    /// **选中项的 id** —— 闸门按它判，不按行号判（见 `SelectionRevealHostView` 的注释）。
    let revealKey: AnyHashable?
    /// 当前选中项在可见顺序里的行号；nil = 这次没有该揭示的东西。
    let rowIndex: Int?

    func makeNSView(context: Context) -> SelectionRevealHostView {
        SelectionRevealHostView()
    }

    func updateNSView(_ nsView: SelectionRevealHostView, context: Context) {
        nsView.revealIfSelectionChanged(key: revealKey, row: rowIndex)
    }
}

final class SelectionRevealHostView: NSView {
    /// 上一次为**哪个选中项**滚过。闸门按 id 判，不按行号判，这是两件事：
    /// * 按"每次更新都滚"⇒ 用户在往下翻看时，任意一次重算都会把他拽回选中行（R22 那一族的自伤）。
    /// * 按"行号变了才滚"⇒ 挡住第一种，但挡不住**行号漂移**：用户在读第 40 行，
    ///   此时上面插进来一条新记录，选中项的行号从 39 变 40 —— 选中没变，视口却跳了。
    ///   本轮实测过这条路径确实存在（`store.add` 会让 `rowIndex` 变，而 `selectedEntry` 不变）。
    /// 所以这里记的是 id：**选中变了才滚，行号漂了不滚。**
    private var lastRevealedKey: AnyHashable?
    private weak var table: NSTableView?
    /// 每次揭示递增；动画完成回调只认自己那一代（新选中把旧回调作废）。
    private var revealGeneration = 0
    /// 只给单测把动画放慢到足以拍中段；产品路径恒 nil，时长仍来自 `SelectionRevealMotion`。
    var revealDurationOverride: TimeInterval?

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        // 宿主视图刚挂上时 `superview` 还没有兄弟子树可找，SwiftUI 下一次 update 会补上；
        // 这里先解析一次，能让"启动就选中第一条"那一格也滚到位。
        resolveTable()
    }

    func revealIfSelectionChanged(key: AnyHashable?, row: Int?) {
        guard let row else {
            lastRevealedKey = nil
            return
        }
        if key == lastRevealedKey { return }
        if table == nil { resolveTable() }
        guard let table, row >= 0, row < table.numberOfRows else { return }
        // 已经可见 ⇒ 不动。判据要能被读出来（注释与日志同一件事）。
        if let scroll = table.enclosingScrollView,
           scroll.documentVisibleRect.intersects(table.rect(ofRow: row)) {
            lastRevealedKey = key
            return
        }
        lastRevealedKey = key
        revealGeneration += 1
        let generation = revealGeneration
        // **推迟一个回合再滚**，这一句是本轮实测逼出来的：
        // 在 `updateNSView` 里同步滚，视口先动、SwiftUI 的选中后落地，于是上一行（此时已被滚出视口、
        // 单元格已回收）的**取消选中没被写进表格** —— 实测读到 `selectedRowIndexes = [2, 60]`
        // 而 store 只有 1 条，也就是"列表亮两行、详情讲一条"这个新分裂。
        // 推迟之后：先在旧行还看得见的时候撤掉它的选中，再把新行滚进来（新行一被物化，
        // SwiftUI 就把选中给它 —— 这条是同轮臂 3 读出来的：只滚不动选中，集合自己从 [] 变 [60]）。
        DispatchQueue.main.async { [weak self, weak table] in
            guard let self, let table, self.lastRevealedKey == key else { return }
            guard let scroll = table.enclosingScrollView else { return }
            let clip = scroll.contentView
            let start = clip.bounds.origin
            // **先让系统滚一次**：List 的选中是在目标行被物化之后补回来的（本文件开头的实测），
            // 纯 bounds 动画不会替它物化行 —— R413 的真在屏探针就是在这里读到 origin 到位、
            // 选中集仍是 []。这一次调用同时把「系统最小滚动」的目标量出来；随后回起点、
            // 演到同一个目标，于是 instant 与 animated 的落点一致，选中也不会丢。
            table.scrollRowToVisible(row)
            // List 的行高是物化后才定下来的：第一次滚只能拿到旧估计，目标会在 layout 后跳
            // （R413 在屏：2191 → 3211）。先 layout 再滚一次，读**物化后的**系统目标。
            table.layoutSubtreeIfNeeded()
            table.scrollRowToVisible(row)
            scroll.layoutSubtreeIfNeeded()
            let target = clip.bounds.origin
            guard abs(target.y - start.y) > 0.5 else { return }
            let plan = SelectionRevealMotion.plan(
                distance: abs(target.y - start.y),
                viewportHeight: scroll.documentVisibleRect.height,
                reduceMotion: MotionCatalog.motionShouldBeReduced)
            guard plan.isAnimated else {
                // 近步 / 减弱动态：系统已经落位；不重置、不演。
                return
            }
            clip.setBoundsOrigin(start)
            scroll.reflectScrolledClipView(clip)
            let duration = self.revealDurationOverride ?? plan.duration
            NSAnimationContext.runAnimationGroup({ context in
                context.duration = duration
                context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                clip.animator().setBoundsOrigin(target)
            }, completionHandler: { [weak self, weak scroll, weak clip, weak table] in
                // 完成回调不在主线程 ⇒ AppKit 状态回主线程改。
                DispatchQueue.main.async {
                    guard let self, let scroll, let clip, let table,
                          self.revealGeneration == generation else { return }
                    clip.setBoundsOrigin(target)
                    scroll.reflectScrolledClipView(clip)
                    // 动画只移动 bounds，不会替 List 物化目标行；完成时再叫一次系统滚动，
                    // 让 row view/visibleRect 在目标处落定（R413 在屏探针：origin 到了、rect 仍为空）。
                    table.scrollRowToVisible(row)
                }
            })
        }
    }

    /// 向上找 `enclosingScrollView.documentView`，找不到再从祖先的兄弟子树里有界地向下找一次。
    /// 刻意不写"永远找得到"：找不到的后果是**不滚**（退化成今天的行为），不是崩。
    private func resolveTable() {
        if let enclosing = enclosingScrollView?.documentView as? NSTableView {
            table = enclosing
            return
        }
        var ancestor: NSView? = superview
        for _ in 0..<6 {
            guard let current = ancestor else { return }
            if let hit = current.subviews.lazy.compactMap({ Self.firstTable(in: $0) }).first {
                table = hit
                return
            }
            ancestor = current.superview
        }
    }

    private static func firstTable(in view: NSView) -> NSTableView? {
        if let table = view as? NSTableView { return table }
        for sub in view.subviews {
            if let table = firstTable(in: sub) { return table }
        }
        return nil
    }
}
