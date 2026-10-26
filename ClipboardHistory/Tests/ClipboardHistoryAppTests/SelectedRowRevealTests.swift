// R61 / BACKLOG 61：`SelectionRevealPlan.rowIndex` 的真值表 + 两条源码守卫。
//
// 不覆盖管线：这个文件判的是"行号怎么算"和"文件里有没有出现第二个选中作者"，
// 它不知道屏幕上有没有真的滚过去。管线级判据在同文件的
// `testOffScreenProgrammaticSelectionIsRevealedAndNotJumped` —— 那一条从产品入口 `store.perform(.setSelection)` 进、在**在屏**窗口里读
// `NSTableView.selectedRowIndexes` 与 `documentVisibleRect`。
// 这里刻意不做视觉断言：`rowIndex` 算对了而宿主视图找不到表格，产品照样是坏的，
// 那种坏只有探针能报（本轮就是活例：`scrollTo` 版在源码里"接到了"，屏幕上一步没动）。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class SelectedRowRevealTests: XCTestCase {

    /// 真值表：四种输入各判一件事，缺一种就有一条产品行为没有判据。
    func testRowIndexTruthTable() {
        // `Entry.ID` 是 UUID（不是可写的字符串），所以 order 在这里自建 ——
        // 断言里的行号只能从这份 order 来。三个 uuid 各自 `UUID()`，
        // 不用 `uuidString(...)!`：写错一位就是在测试里崩溃，而崩溃会被报表读成"没跑"。
        let a = UUID()
        let b = UUID()
        let c = UUID()
        // 「不在可见顺序里的那条」用一个必然不属于 order 的 uuid：
        // 这里不许 `uuidString(...)!`，写错十六进制就是在测试里崩溃（崩溃 = 把红伪装成没跑）。
        let absent = UUID()
        let order: [HistoryStore.Entry.ID] = [a, b, c]

        // 1. 正常：选中项在可见顺序里 ⇒ 给它的行号。
        XCTAssertEqual(SelectionRevealPlan.rowIndex(of: b, in: order), 1,
                       "行号算错 ⇒ 滚到别的行去了，比不滚更坏")
        XCTAssertEqual(SelectionRevealPlan.rowIndex(of: a, in: order), 0, "第一条的行号必须是 0")
        XCTAssertEqual(SelectionRevealPlan.rowIndex(of: c, in: order), 2, "最后一条的行号必须是 2")

        // 2. 没有选中（清空 / 还没选）⇒ nil，什么都不做。
        XCTAssertNil(SelectionRevealPlan.rowIndex(of: nil, in: order),
                     "没有选中也返回一个行号 ⇒ 每次重算都会把视口甩到那一行")

        // 3. 选中项被筛掉/搜掉了 ⇒ nil。**这一条是本表最重要的一格**：
        //    拿 `firstIndex ?? 0` 兜底会把「看不见的那条」滚成「滚到第一条」，
        //    于是搜索框里打一个字就跳一次顶 —— 而它读起来像是正常工作。
        XCTAssertNil(SelectionRevealPlan.rowIndex(of: absent, in: order),
                     "选中项不在可见顺序里时必须不滚：兜底成 0 等于用错的行号做一次真滚动")
        XCTAssertNil(SelectionRevealPlan.rowIndex(of: a, in: []), "空列表里没有行可滚")

        // 4. 重复 id（存档去重失败那一族的形状）⇒ 取第一条匹配，不取最后一条：
        //    列表显示的顺序就是 `filteredEntries` 的顺序，第一条匹配才是屏幕上那一行。
        XCTAssertEqual(SelectionRevealPlan.rowIndex(of: b, in: [b, b, c]), 0,
                       "重复 id 时必须落在**列表顺序的第一条**：滚到第二条匹配 = 屏幕上高亮的是第一条")
    }

    /// 单一作者守卫：这个文件里不许出现"第二个选中作者"。
    ///
    /// D-1 修法③ 的结论是 `List(selection:)` 是选中的唯一作者、store 只是落状态。
    /// 这一族修"看不见高亮"最省事的写法就是在这里顺手 `table.selectRowIndexes(...)` ——
    /// 那时选中集由宿主视图写、`List` 不知情，store 与表格会各说一套（本轮臂 2/3 读到的就是这类分裂）。
    /// 所以守卫判的是"有没有这个调用"，而不是"行为对不对"。
    func testRevealerOnlyScrollsAndNeverSelects() throws {
        let source = codeOnly(try productSourceText(named: "Views/SelectedRowRevealer.swift"))
        for forbidden in ["selectRowIndexes", "select(", "selectedRow =", "deselectAll"] {
            XCTAssertFalse(source.contains(forbidden),
                           "揭示器里出现了 \(forbidden) ⇒ 它变成选中的第二个作者了（D-1 修法③）。"
                             + "本轮实测：把行滚进视口之后 SwiftUI 自己会把选中补上，这里不需要写选中")
        }
        XCTAssertTrue(source.contains("setBoundsOrigin"),
                      "揭示器不再滚动了 ⇒ BACKLOG 61 的修法本体没了，回来重读正文")
        XCTAssertTrue(source.contains("scroll.reflectScrolledClipView"),
                      "瞬移分支改了 bounds 却没 reflect ⇒ 表格的可见行不会跟着更新")
    }

    /// R413：揭示的**运动**是模型值。跨视口才演、近步与减弱动态瞬移；时长走 `.slider`。
    func testSelectionRevealMotionTruthTable() {
        XCTAssertEqual(SelectionRevealMotion.plan(distance: 100, viewportHeight: 300, reduceMotion: false),
                       .init(isAnimated: false, duration: 0),
                       "近步也演 ⇒ 方向键连翻会变成一帧一帧的滑动，按键像粘住")
        XCTAssertEqual(SelectionRevealMotion.plan(distance: 301, viewportHeight: 300, reduceMotion: false),
                       .init(isAnimated: true, duration: MotionCatalog.duration(for: .slider)),
                       "跨视口长跳没有过程 ⇒ 这一格又回到瞬移")
        XCTAssertEqual(SelectionRevealMotion.plan(distance: 900, viewportHeight: 300, reduceMotion: true),
                       .init(isAnimated: false, duration: 0),
                       "减弱动态仍演 ⇒ 这一档没有降级出口")
        XCTAssertEqual(SelectionRevealMotion.plan(distance: 900, viewportHeight: 0, reduceMotion: false),
                       .init(isAnimated: false, duration: 0),
                       "视口高 0 还演 ⇒ 没有可插值的距离，动画不是信息")
        XCTAssertEqual(SelectionRevealMotion.plan(distance: 300, viewportHeight: 300, reduceMotion: false),
                       .init(isAnimated: false, duration: 0),
                       "门槛是严格大于：刚好一屏不算长跳")
    }

    /// 接线守卫：模型值必须真的接到 AppKit 的 bounds 动画上，且 instant 分支仍走系统最小滚动。
    func testRevealAnimationIsWiredIntoTheRevealer() throws {
        let source = codeOnly(try productSourceText(named: "Views/SelectedRowRevealer.swift"))
        XCTAssertTrue(source.contains("SelectionRevealMotion.plan("),
                      "揭示器没有问运动计划 ⇒ 上面的真值表测的是没人用的替身")
        XCTAssertTrue(source.contains("table.scrollRowToVisible(row)"),
                      "没有先让系统物化/选中目标行 ⇒ 纯 bounds 动画会让 List 的选中集停在空集（R413 在屏探针）")
        XCTAssertTrue(source.contains("NSAnimationContext.runAnimationGroup"),
                      "没有 AppKit 动画 ⇒ `isAnimated` 只是一个名字")
        XCTAssertTrue(source.contains("clip.animator().setBoundsOrigin"),
                      "没有把 bounds 交给 animator ⇒ 过程不会发生")
        XCTAssertTrue(source.contains("clip.setBoundsOrigin(start)"),
                      "动画前没有回到起点 ⇒ 中段读到的会是落点（瞬移）")
        XCTAssertTrue(source.contains("revealDurationOverride ?? plan.duration"),
                      "产品路径没有走计划时长 ⇒ 真值表里的 duration 不承重")
        XCTAssertTrue(source.contains("revealReduceMotionOverride ?? MotionCatalog.motionShouldBeReduced"),
                      "减弱动态的默认来源被改掉 ⇒ 系统开关不再是产品路径的唯一默认；单测 seam 只能覆盖测试")
    }

    /// 声明守卫（与 R61 那条实测一一对应）：侧栏里不许留着"用 SwiftUI 的 scrollTo 跟随选中"这句话。
    ///
    /// 本轮真的写过那三行（`ScrollViewReader` + `.id` + `scrollTo`，anchor 两种都试）：
    /// 临时插桩证明它执行了、id 也解析了，而表格一步没滚。留着它比不留更坏 ——
    /// 下一个人会以为"跟随选中"已经做了。**要重新走这条路，先重跑探针那条判据。**
    func testSidebarDoesNotClaimTheSwiftUIScrollRoute() throws {
        let sidebar = codeOnly(try productSourceText(named: "Views/HistorySidebarView.swift"))
        XCTAssertFalse(sidebar.contains("scrollTo"),
                       "侧栏又出现 scrollTo：本轮实测它在产品这棵树上不滚（见 SelectedRowRevealer 正文）")
        XCTAssertFalse(sidebar.contains("ScrollViewReader"), "同上：这条路由已经量死，不许留声明")
        XCTAssertTrue(sidebar.contains("SelectedRowRevealer"),
                      "侧栏没挂揭示器 ⇒ BACKLOG 61 又回到「选中一条列表里看不见的高亮」那个状态")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        // 找不到被守卫的文件时要**红**，不许跳过：会跳过的守卫和通过的守卫在报表里长得一样。
        throw NSError(domain: "SelectedRowRevealTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
