// 不覆盖管线：本文件钉两件事 —— 行级更新计划的纯函数真值表，和"控制器确实把计划交给了
// AppKit 的行动画 API"这条源码守卫。它**不**证明屏幕上真的在淡入。
// 在屏证据在 `MotionFilmstripTests.testNativeRowAnimationIsVisibleToTheRuler`（要环境变量才跑，
// 并且它回答的是"这把尺看不看得见 AppKit 的图层动画"；量到之前不许把 ① 记成交付）。
// 查询 → 候选 → 回车提交那条产品链的管线级用例在 `Round3QuickPickTests.testTypingThenDownThenEnterCommitsTheRightEntry`。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 动效审计 M1 的替代路径（报告 §12.4 / §12.7、MC-7）：`List` 拿不到行过渡，
/// 而快速选择浮层本来就是真 `NSTableView` ⇒ 走它自己的原生行动画。
/// 原生行动画的**全部正确性**都压在"告诉表格哪些行走了、哪些行来了"这一步上：
/// 索引空间搞错不会报错，只会让动画落在别的行上，或者直接抛"行数算不回来"。
/// 所以这一步抽成纯函数，在这里逐档钉住。
@MainActor
final class QuickPickRowDiffTests: XCTestCase {
    private let a = UUID(), b = UUID(), c = UUID(), x = UUID()

    private func titles(_ ids: [UUID], _ mark: String = "") -> [String] {
        ids.map { "\($0.uuidString.prefix(4))\(mark)" }
    }

    /// 计划要能直接喂给 `beginUpdates/endUpdates`，那套 API 有一条硬前提：
    /// **旧行数 − 删除数 + 插入数 == 新行数**。算不回来的表现是 AppKit 运行时异常
    /// （"attempt to insert … but the number of rows is wrong"），
    /// 而它出现在用户正在打字的那张表上。下面每一条都顺带检查这个不变量。
    private func executablePlan(oldIDs: [UUID], newIDs: [UUID],
                                file: StaticString = #filePath, line: UInt = #line) -> QuickPickRowDiff.Plan {
        let plan = QuickPickRowDiff.plan(oldIDs: oldIDs, oldTitles: titles(oldIDs),
                                         newIDs: newIDs, newTitles: titles(newIDs))
        // 不变量只在"走三步/移动"时成立：退回整表刷新时三步**被清空是设计**
        // （控制器随后 `reloadData()`，没有坐标要加总），所以那条加总检查不适用。
        // 第一版没写这个分支，于是"混着增删的重排"那条用例被辅助函数自己判红了
        // —— 报的是"行数算不回来"，而真相是"这里根本不发增删"。
        if !plan.needsFullReload {
            XCTAssertEqual(oldIDs.count - plan.removals.count + plan.insertions.count,
                           newIDs.count, "行数算不回来 ⇒ 真喂给 AppKit 会抛异常", file: file, line: line)
        } else {
            XCTAssertTrue(plan.removals.isEmpty && plan.insertions.isEmpty && plan.reloads.isEmpty
                          && plan.moves.isEmpty,
                          "退回整表刷新时必须清空四步，否则控制器会既 reloadData 又插删，行数算两遍",
                          file: file, line: line)
        }
        if plan.needsFullReload {
            XCTAssertTrue(plan.removals.isEmpty && plan.insertions.isEmpty && plan.reloads.isEmpty,
                          "退回整表刷新时必须清空三步，否则控制器会既 reloadData 又插删，行数算两遍",
                          file: file, line: line)
        }
        return plan
    }

    func testIdenticalListsTellTheTableNothing() {
        let plan = executablePlan(oldIDs: [a, b, c], newIDs: [a, b, c])
        XCTAssertTrue(plan.isNoop, "一模一样的两批 ⇒ 什么都不该告诉表格，否则每次按键都在重演一遍")
    }

    func testRemovalIsExpressedInOldCoordinates() {
        let plan = executablePlan(oldIDs: [a, b, c], newIDs: [a, c])
        XCTAssertEqual(plan.removals, IndexSet([1]))
        XCTAssertTrue(plan.insertions.isEmpty)
    }

    func testInsertionIsExpressedInNewCoordinates() {
        let plan = executablePlan(oldIDs: [a, c], newIDs: [x, a, c])
        XCTAssertEqual(plan.insertions, IndexSet([0]))
        XCTAssertTrue(plan.removals.isEmpty)
    }

    /// 同一条记录的**文案**会变（时间列、"置顶"前缀），身份和位置都没变 ⇒ 只许原地刷新。
    /// 这一档以前是漏的：落到 insert/remove 里就会把一行好好的东西"演"成一次插入。
    func testSameRowDifferentCopyIsAReloadOnly() {
        let plan = QuickPickRowDiff.plan(oldIDs: [a, b], oldTitles: titles([a, b]),
                                         newIDs: [a, b], newTitles: titles([a, b], "·刚刚"))
        XCTAssertEqual(plan.reloads, IndexSet([0, 1]))
        XCTAssertTrue(plan.removals.isEmpty && plan.insertions.isEmpty)
        XCTAssertFalse(plan.needsFullReload)
        XCTAssertFalse(plan.isNoop, "文案变了却不是 noop：`isNoop` 漏掉 reloads 就等于把该刷新的行吞掉")
    }

    /// **翻案记录（R17）**：这条以前叫 `testReorderOfKeptRowsFallsBackToFullReload`，
    /// 断言"[a,b]→[b,a] 必须退回整表刷新"，理由写的是"`.effectFade` 那套 API 表达不了整体重排"。
    ///
    /// 那句话对**多行同时跳**仍然成立（下面那条新用例继续钉着它），
    /// 但把最高频的一种形状一起划进了"表达不了"：**恰好一行挪位** ——
    /// 也就是"刚复制的那条被顶到最前"。`NSTableView.moveRow(at:to:)` 就是为它造的，
    /// 而且它在 `allowsImplicitAnimation` 打开时**自己会动**。
    /// 于是这个浮层里最常见的一次变化，一直是整表硬刷新。
    ///
    /// 翻案前先读了原文（D-055 / M1 的替代路径那一段）：当年砍的是
    /// "SwiftUI `List` 拿不到行过渡"，与本条无关；本条是**同一个结论被用到了它没覆盖的形状上**。
    func testSingleRowPromotionBecomesAMoveNotAHardReload() {
        let plan = executablePlan(oldIDs: [a, b], newIDs: [b, a])
        XCTAssertFalse(plan.needsFullReload, "两行互换就是「一行挪位」，不该再走整表硬刷新")
        XCTAssertEqual(plan.moves, [QuickPickRowDiff.Move(from: 0, to: 1)])
        XCTAssertFalse(plan.isNoop, "重排不是'没变化'：控制器要是当成 noop，界面就留在旧顺序上")

        // 真·顶到最前：第三条被复制到 [a,b,c,d] 之后变成 [d,a,b,c]
        let promoted = executablePlan(oldIDs: [a, b, c, x], newIDs: [x, a, b, c])
        XCTAssertEqual(promoted.moves, [QuickPickRowDiff.Move(from: 3, to: 0)],
                       "末行（夹具里的 `x`）提到最前是这个浮层最高频的重排，必须是 move 不是 reload")
        XCTAssertFalse(promoted.needsFullReload)
    }

    /// 仍然要退回整表刷新的那些形状 —— 这一条是上面那条翻案的**边界**，
    /// 没有它，"能表达一行"会被读成"能表达任意重排"。
    func testOtherReorderShapesStillFallBackToFullReload() {
        // 中间两行互换：要两次 move，而两次 move 的坐标系换算没有文档保证
        let twoSwaps = executablePlan(oldIDs: [a, b, c, x], newIDs: [c, b, a, x])
        XCTAssertTrue(twoSwaps.needsFullReload, "多行同时跳不许硬凑成一串 moveRow")
        XCTAssertTrue(twoSwaps.moves.isEmpty)

        // 移动与增删**混在一起**：`moveRow` 的 `from` 该按删之前还是删之后解释，未知
        let mixed = executablePlan(oldIDs: [a, b, c], newIDs: [c, b, a, x])
        XCTAssertTrue(mixed.needsFullReload || mixed.moves.isEmpty,
                      "混着增删的重排不许走 move 那一档")
    }

    /// `singleMove` 自己是纯函数，得有自己的真值表 ——
    /// 否则上面两条只能通过 `plan(...)` 间接看到它，而它错的方式是"安静地给出一个错下标"。
    func testSingleMoveTruthTable() {
        func move(_ old: [UUID], _ new: [UUID]) -> QuickPickRowDiff.Move? {
            QuickPickRowDiff.singleMove(from: old, to: new)
        }
        XCTAssertNil(move([a, b, c], [a, b, c]), "没动就不该给出移动")
        XCTAssertEqual(move([a, b], [b, a]), QuickPickRowDiff.Move(from: 0, to: 1))
        XCTAssertEqual(move([a, b, c, x], [x, a, b, c]), QuickPickRowDiff.Move(from: 3, to: 0))
        XCTAssertEqual(move([a, b, c], [b, c, a]), QuickPickRowDiff.Move(from: 0, to: 2),
                       "首行沉到最后也是一行挪位")
        // 这条被实现纠正了直觉：**循环位移就是一次移动**（把末行提到最前）。
        // 我一开始把它写成"需要两次 move ⇒ 应为 nil"，那是错的断言，不是对的代码。
        XCTAssertEqual(move([a, b, c], [c, a, b]), QuickPickRowDiff.Move(from: 2, to: 0),
                       "把末行提到最前 = 一次 moveRow，这正是'刚复制的那条被顶到最前'")
        XCTAssertNil(move([a, b, c, x], [c, b, a, x]), "中间两行互换要两次 move ⇒ 不是一行挪位")
        XCTAssertNil(move([a, b, c], [a, b]), "行数不同不是移动，是删除")
        XCTAssertNil(move([a, b], [c, x]), "两行全换不是移动")
        XCTAssertNil(move([], []), "空表没有可移动的行")
        XCTAssertNil(move([a], [a]))
    }

    /// 删除与插入**同时**发生（打字时候选一边变少一边补进来），三步的坐标空间必须仍能对齐。
    /// 保留行的文案同时改掉，才能看出 `reloads` 用的是**新**下标：
    /// 老下标是 1、2，新下标也是 1、2 —— 换个布局（插在前面）就不一样了，见下一条。
    func testRemoveAndInsertTogetherStillAddUp() {
        let plan = QuickPickRowDiff.plan(oldIDs: [a, b, c], oldTitles: ["A", "B", "C"],
                                         newIDs: [x, b, c], newTitles: ["X", "B·新", "C·新"])
        XCTAssertEqual(plan.removals, IndexSet([0]), "a 在**旧**下标 0")
        XCTAssertEqual(plan.insertions, IndexSet([0]), "x 在**新**下标 0")
        XCTAssertEqual(plan.reloads, IndexSet([1, 2]), "b、c 在新下标 1、2 —— 不是旧下标 1、2")
        XCTAssertEqual([a, b, c].count - plan.removals.count + plan.insertions.count, 3)
    }

    /// 插在**前面**时新旧下标会错开一位；这一档把坐标系钉死，
    /// 否则 `reloads` 会安静地刷错行（不崩、不报错，只是刷的是别的行）。
    func testReloadIndicesFollowTheNewCoordinateSpaceWhenARowIsInsertedBeforeThem() {
        let plan = QuickPickRowDiff.plan(oldIDs: [a, b], oldTitles: ["A", "B"],
                                         newIDs: [x, a, b], newTitles: ["X", "A·新", "B·新"])
        XCTAssertEqual(plan.insertions, IndexSet([0]))
        XCTAssertEqual(plan.reloads, IndexSet([1, 2]),
                       "a、b 删前删后位置变了：它们的新下标是 1、2，不是旧的 0、1")
    }

    func testEmptyToNotEmptyAndBackAreBothExecutable() {
        let plan = executablePlan(oldIDs: [], newIDs: [a, b])
        XCTAssertEqual(plan.insertions, IndexSet([0, 1]))
        let emptied = executablePlan(oldIDs: [a, b], newIDs: [])
        XCTAssertEqual(emptied.removals, IndexSet([0, 1]))
    }

    /// id 重复在真实数据里不该发生，但一旦发生，"按 id 找旧下标"和行数不变量都不成立，
    /// 而它的表现是"按 ⌃⌥⇧V 打字时 App 直接没了"。
    ///
    /// 拦下它的是**保留行相对顺序**那一句（`[a,a] != [a]`），不是某个专门的重复判断：
    /// 上一版那样写过，变异对照打不红（账本 U-20 的 M5），所以入口删了、断言留着。
    /// 这条断言的可打红性由 M4 证明 —— 把 `keptOld != keptNew` 改成 `false` 它就红。
    func testDuplicateIDsFallBackToFullReload() {
        let plan = QuickPickRowDiff.plan(oldIDs: [a, a], oldTitles: titles([a, a]),
                                         newIDs: [a], newTitles: titles([a]))
        XCTAssertTrue(plan.needsFullReload, "旧列表里有重复 id ⇒ 不许用三步去描述")
        XCTAssertTrue(plan.removals.isEmpty && plan.insertions.isEmpty,
                      "整体重排必须清空三步")
        let sameBothSides = QuickPickRowDiff.plan(oldIDs: [a, a], oldTitles: titles([a, a]),
                                                  newIDs: [a, a], newTitles: titles([a, a]))
        XCTAssertTrue(sameBothSides.isNoop, "两边一样地重复 = 什么都没变，不该惊动表格（也不该崩）")
    }

    // MARK: - 减弱动态与总开关

    /// 这一档是**行为**断言，不是源码匹配：减弱动态时给 AppKit 的是"空效果集"，
    /// 也就是"照常增删行、只是不淡入"，而不是"跳过这次更新"。
    /// Pearcleaner 那个反例（`duration: enabled ? X : 0`）之所以进红线，
    /// 就是因为把"关掉动效"写成了"关掉功能"。
    func testRowAnimationOptionsNeverSkipTheUpdate() {
        XCTAssertEqual(QuickPickController.rowAnimationOptions(reduceMotion: false, animationsEnabled: true),
                       .effectFade)
        XCTAssertEqual(QuickPickController.rowAnimationOptions(reduceMotion: true, animationsEnabled: true), [],
                       "减弱动态 ⇒ 空效果集，但仍然是'更新行'")
        XCTAssertEqual(QuickPickController.rowAnimationOptions(reduceMotion: false, animationsEnabled: false), [],
                       "总开关关掉（胶片夹具的对照组）也必须走同一条路")
        XCTAssertEqual(QuickPickController.rowAnimationOptions(reduceMotion: true, animationsEnabled: false), [])
    }

    // MARK: - 接线守卫

    /// `rebuildRows()` 是不是真的把计划交给了原生行动画 API。
    ///
    /// 为什么还需要源码级这一条：纯函数全绿、`rowAnimationOptions` 全对，**都拦不住"没人调用它"**。
    /// 本轮已经栽过一次同族（D-055 / MC-12：`bounceValue` 恒传非 nil，把本该走的那条分支挡死，
    /// 三条分支里两条互斥、一条被参数堵死，纯值守卫完全看不见）。
    /// 断言用**整句**而不是关键字：`withAnimation:` 这种词会被注释白送命中，所以先剥注释、再截正文。
    func testRebuildRowsIsWiredToTheAnimatedAPI() throws {
        let source = codeOnly(try productSource(named: "Managers/QuickPickController.swift"))
        let body = try XCTUnwrap(extractFunction(named: "private func rebuildRows()", from: source),
                                 "找不到 `rebuildRows()`：锚点失效，这条守卫无从判定")
        // 先证明截到的确实是那段正文（锚点错位时必须红，而不是安静地空跑）。
        XCTAssertTrue(body.contains("plan.needsFullReload"), "切片里没有正文才有的那句 ⇒ 锚点错位")

        XCTAssertTrue(body.contains("table.removeRows(at: plan.removals, withAnimation: animation)"),
                      "删除没走原生行动画 ⇒ ① 只是注释里的事实")
        XCTAssertTrue(body.contains("table.insertRows(at: plan.insertions, withAnimation: animation)"),
                      "插入没走原生行动画 ⇒ ① 只是注释里的事实")
        XCTAssertTrue(body.contains("Self.rowAnimationOptions(reduceMotion: MotionCatalog.motionShouldBeReduced"),
                      "动画选项没接减弱动态闸门 ⇒ 系统开了「减弱动态效果」照样淡入")
        XCTAssertTrue(body.contains("animationsEnabled: MotionCatalog.animationsEnabled"),
                      "动画选项没接总开关 ⇒ 胶片夹具的两臂对照失效，量到的动无法归因给我们")
        XCTAssertTrue(body.contains("guard !plan.isNoop else { return }"), "没变化时不该惊动表格")
        // R17：计划里有了 `moves`，还得有人真的去执行它 ——
        // "纯函数全绿、调用点忘了传"这一族在本仓库出现过四次以上（`Plan.moves` 就是最新的一个诱饵）。
        XCTAssertTrue(body.contains("table.moveRow(at: move.from, to: move.to)"),
                      "计划算出了行移动，但没人执行 ⇒ 顶到最前仍然是一帧硬换（本轮修的就是它）")
        XCTAssertTrue(body.contains("context.allowsImplicitAnimation = !animation.isEmpty"),
                      "移动没接减弱动态/总开关闸门 ⇒ 关掉动画的那一臂照样滑，"
                      + "胶片的 A/B 对照会把归因给错对象")

        // 整表刷新只准留在"重排"那一档：一旦有人把 beginUpdates 那段改回 `table.reloadData()`，
        // 原生行动画就又是零 —— 这正是 M1 原来的病。
        // 位置类判据先把两个锚点各自证明存在，再比先后（拿注释或别处的词去比索引，就是永真断言）。
        let batchStart = try XCTUnwrap(body.range(of: "table.beginUpdates()"), "增量批次不见了")
        let blanketReload = try XCTUnwrap(body.range(of: "table.reloadData()"), "重排那一档的整表刷新不见了")
        XCTAssertLessThan(blanketReload.lowerBound, batchStart.lowerBound,
                          "整表刷新出现在增量批次**之前或之中** ⇒ 它会把插删动画抹平")

        // 原地刷新必须排在批次落定之后：`reloads` 是新下标，而批次中间 `reloadData(forRowIndexes:)`
        // 按哪套坐标系解释没有文档保证，错一位就安静地刷错行。
        let batchEnd = try XCTUnwrap(body.range(of: "table.endUpdates()"), "批次结束不见了")
        let reload = try XCTUnwrap(body.range(of: "table.reloadData(forRowIndexes: plan.reloads"),
                                             "原地刷新不见了 ⇒ 文案变化（时间档位、置顶前缀）不会被刷出来")
        XCTAssertGreaterThan(reload.lowerBound, batchEnd.lowerBound,
                             "原地刷新排在 endUpdates 之前 ⇒ 它用的下标空间与 plan.reloads 不一致")
    }

    /// 截一个函数的正文：从锚点那句开始，到**第一处**单独占一行的四空格 `}` 结束。
    /// 锚点找不到就返回 nil（调用方必须红）—— 守卫找不到被守卫的东西时不能空跑。
    private func extractFunction(named anchor: String, from source: String) -> String? {
        guard let start = source.range(of: anchor) else { return nil }
        let tail = source[start.upperBound...]
        guard let end = tail.range(of: "\n    }\n") else { return nil }
        return String(tail[..<end.lowerBound])
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relative: String) throws -> String {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + relative)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            root = root.deletingLastPathComponent()
        }
        throw NSError(domain: "QuickPickRowDiffTests", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红",
        ])
    }
}
