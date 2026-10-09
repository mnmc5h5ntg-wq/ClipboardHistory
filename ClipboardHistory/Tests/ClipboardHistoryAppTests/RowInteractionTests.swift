import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 行上新增的两个手势（双击复制、点星标收藏）的判定与呈现。
///
/// 这里刻意**不重复** store 层已有的用例（`copyAndPromote` / `toggleFavorite` 的效果
/// 在 `HistoryStoreTests` 里已经钉着），只钉这次改动带来的新契约。
@MainActor
final class RowInteractionTests: XCTestCase {
    // MARK: - 双击复制的修饰键规则

    func testDoubleTapCopiesOnlyWithoutSelectionModifiers() {
        XCTAssertTrue(RowDoubleTap.shouldCopy(modifiers: []), "裸双击就是要复制，否则这个功能没意义")
        XCTAssertFalse(RowDoubleTap.shouldCopy(modifiers: .shift), "shift 是范围选择前缀，误双击不该写剪贴板")
        XCTAssertFalse(RowDoubleTap.shouldCopy(modifiers: .command), "command 是多选前缀，同上")
        XCTAssertFalse(RowDoubleTap.shouldCopy(modifiers: [.shift, .command]))
        // control 在本列表里不参与选择语义 —— 这一条是防止将来有人"顺手"把它也挡掉，
        // 挡了不会有人发现，只会让"⌃双击"这种手型莫名其妙地失灵。
        XCTAssertTrue(RowDoubleTap.shouldCopy(modifiers: .control))
    }

    /// 规则必须和真正的选择前缀保持一致：`HistorySidebarView.select(_:)` 用的是 shift / command。
    /// 两边各写各的迟早会漂移，所以这里直接把"选择侧用了哪些键"当判据读出来。
    func testModifierRuleMatchesWhatRowSelectionActuallyUses() throws {
        let source = try productSource(named: "Views/HistorySidebarView.swift")
        let afterSelect = try XCTUnwrap(
            source.components(separatedBy: "private func select(_ entry:").dropFirst().first,
            "找不到 select(_:)，这条守卫的锚点失效了"
        )
        let selectBody = try XCTUnwrap(
            afterSelect.components(separatedBy: "private func ").first,
            "select(_:) 之后取不到函数体"
        )
        let code = codeOnly(in: selectBody)
        XCTAssertTrue(code.contains(".shift"), "select 里已经没有 shift 了，规则要跟着改：\(selectBody)")
        XCTAssertTrue(code.contains(".command"), "select 里已经没有 command 了，规则要跟着改：\(selectBody)")
        XCTAssertFalse(code.contains(".option"),
                       "select 现在开始用 option 了 —— 双击的例外名单要一起加，否则两个手势会抢同一次点击")
    }

    // MARK: - 收藏星标的呈现

    func testFavoritePresentation() {
        XCTAssertEqual(FavoriteTogglePresentation.symbolName(isFavorite: true), "star.fill")
        XCTAssertEqual(FavoriteTogglePresentation.symbolName(isFavorite: false), "star")
        XCTAssertEqual(FavoriteTogglePresentation.helpText(isFavorite: true), "取消收藏")
        XCTAssertEqual(FavoriteTogglePresentation.helpText(isFavorite: false), "收藏")
    }

    /// 行内星标与详情区浮层必须共用同一份呈现。以前是两处各写各的字面量，
    /// 改一处忘一处就是审计第二轮 1.9 那类"同一个语义两种长相"的来源。
    /// 正向对照（helper 里确实有这些词）也在下面，否则把 helper 清空也能"通过"。
    func testFavoritePresentationIsNotDuplicatedAtTheCallSites() throws {
        let forbidden = ["star.fill", "取消收藏", "yellow"]
        for file in ["Views/HistoryRowViews.swift", "Views/GlassControls.swift"] {
            let code = try codeOnly(in: productSource(named: file))
            for needle in forbidden {
                XCTAssertFalse(code.contains(needle), "\(file) 的代码里又出现字面量 \(needle)，应该走 FavoriteTogglePresentation")
            }
        }
        let helper = try productSource(named: "Utilities/RowInteraction.swift")
        for needle in ["star.fill", "取消收藏"] {
            XCTAssertTrue(helper.contains(needle), "helper 里反而没有 \(needle)：守卫的正向对照失败")
        }
        XCTAssertTrue(helper.contains("favoriteColor"), "helper 里应当定义收藏色本体")
    }

    /// 去掉行注释再扫。第一版没去注释，被一句写着"收藏/取消收藏"的文档注释判成违规 ——
    /// 位置/存在类断言的锚点必须先证明"读到的是正文而不是注释"，否则守卫会在别人写注释时乱咬。
    private func codeOnly(in source: String) -> String {
        source.split(separator: "\n", omittingEmptySubsequences: false).map { line in
            if let range = line.range(of: "//") { return String(line[..<range.lowerBound]) }
            return String(line)
        }.joined(separator: "\n")
    }

    // MARK: - 点星标的副作用边界

    /// 点星标的实际边界（钉住现状，不是钉住"理想"）：它翻一个收藏，并把选中收成那一条。
    ///
    /// "会收成一条"是详情区那颗收藏星一直以来的行为（`toggleFavorite` 走
    /// `reconcileSelection(preferredEntryID:)`，那里会 `selectedEntryIDs = [preferredEntryID]`），
    /// 行内星标只是把同一个动作搬近了，没有改语义。要不要让收藏**不动多选集合**是另一个决定，
    /// 记在 `AGENT_BACKLOG.md` 的 R2-20，改之前先想清楚"取消收藏后这条离开收藏筛选"时选择该去哪。
    func testFavoriteStarTogglesExactlyOneEntryAndSelectsIt() {
        let store = HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 20, maxAgeDays: nil)
        )
        for index in 0..<3 {
            store.add(ClipboardIntake.Entry(
                content: .text("记录 \(index)"), thumbnail: nil, sourceUTIs: ["public.utf8-plain-text"]
            ), timestamp: Date(timeIntervalSince1970: Double(10 + index)))
        }
        let target = store.entries[2]
        store.perform(.selectOnly(target))

        store.perform(.toggleFavorite(target))

        XCTAssertEqual(store.entries.filter(\.isFavorite).map(\.id), [target.id],
                       "应当正好翻这一条，不多不少")
        XCTAssertEqual(store.selectedEntry?.id, target.id, "点完星标，详情区应当还看着这一条")

        store.perform(.toggleFavorite(store.entries.first { $0.id == target.id }!))
        XCTAssertFalse(store.entries.contains { $0.isFavorite }, "再点一次要能取消回去")
    }

    // MARK: - 夹具

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp/\(relativePath)（从 \(#filePath) 上溯 6 层未果）")
    }
}
