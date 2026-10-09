import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 09-08（S2）：`populate(_:)` 以前没有直接测试，菜单内容只能靠
/// `EntryPresentation.menuLabel` 的单测**间接**覆盖 —— 而真正会泄露原文、
/// 或者"没推荐时整段静默消失"的缺陷恰好发生在 populate 这一层。
///
/// 这些用例喂一个内存 store（`RecordingHistoryPersistence` + `TestClipboardWriter`），
/// 只调用 `populate` 检查生成的 `NSMenuItem`，既不装 NSStatusItem 也不读用户真实存档（D-002）。
@MainActor
final class MenuBarPopulationTests: XCTestCase {
    private func waitUntil(
        _ description: String = "条件",
        timeout: TimeInterval = 5.0,
        condition: @MainActor () -> Bool
    ) {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if condition() { return }
            RunLoop.main.run(until: Date().addingTimeInterval(0.02))
        }
        XCTFail("\(description)：\(timeout)s 内未成立")
    }

    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    private func intake(_ text: String) -> ClipboardIntake.Entry {
        ClipboardIntake.Entry(
            content: .text(text), thumbnail: nil,
            sourceUTIs: ["public.utf8-plain-text"],
            sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
        )
    }

    private func populatedStore() -> HistoryStore {
        let store = makeStore()
        store.add(intake("普通的一条记录 abcdef"), timestamp: Date(timeIntervalSince1970: 3))
        store.add(intake("ghp_" + String(repeating: "K", count: 36)), timestamp: Date(timeIntervalSince1970: 2))
        store.add(intake("另一条普通的记录"), timestamp: Date(timeIntervalSince1970: 1))
        return store
    }

    private func controller(for store: HistoryStore) -> MenuBarController {
        let controller = MenuBarController()
        controller.configure(commandHandler: { _ in }, historyStore: store, pasteHandler: nil)
        return controller
    }

    /// 没推荐时不能"整段消失"：必须有一行说明（本轮新加的文案，之前没有任何验证手段）。
    func testMenuSaysSoWhenThereIsNothingToSuggest() {
        let store = makeStore()
        let controller = controller(for: store)
        let menu = NSMenu()
        controller.populate(menu)

        let titles = menu.items.map(\.title)
        XCTAssertTrue(titles.contains("暂无推荐"),
                      "没有推荐时菜单应当明说，而不是静默少一段。实际标题：\(titles)")
        XCTAssertFalse(titles.contains("猜你要粘贴"),
                       "既然没有推荐，就不该出现「有推荐」的表头")
    }

    /// 有推荐时：表头 + 至多三条，且标题必须走脱敏标签。
    func testMenuListsSanitizedRecommendationsWhenPresent() {
        let store = populatedStore()
        let controller = controller(for: store)
        store.refreshPredictions()
        waitUntil("预测应产出候选") { !store.predictionSuggestionEntries.isEmpty }

        let menu = NSMenu()
        controller.populate(menu)
        let titles = menu.items.map(\.title)

        XCTAssertTrue(titles.contains("猜你要粘贴"), "有推荐时必须有表头。实际：\(titles)")
        XCTAssertFalse(titles.contains("暂无推荐"), "有推荐时不该同时出现空态文案")
        let suggestionTitles = store.predictionSuggestionEntries.map { EntryPresentation.menuLabel(for: $0) }
        for expected in suggestionTitles {
            // 菜单项标题是 "脱敏标签\n理由行"，所以按前缀匹配（以前我按全等匹配，测试自己错了）。
            XCTAssertTrue(titles.contains { $0.hasPrefix(expected) },
                          "推荐项 \(expected) 没出现在菜单里；菜单标题：\(titles)")
        }
        XCTAssertLessThanOrEqual(
            titles.filter { candidate in suggestionTitles.contains { candidate.hasPrefix($0) } }.count, 3,
            "菜单里的推荐条目数必须受 prefix(3) 约束"
        )
        XCTAssertFalse(store.predictionReasonByEntryID.isEmpty, "推荐应当带理由，理由行才会拼进标题")
        XCTAssertFalse(store.isRefreshingPredictions, "刷新完成后必须把进行中标记落回 false")
    }

    /// 隐私（R-43 的落点）：疑似令牌那一条，原文不得进任何菜单标题。
    func testMenuNeverShowsTheRawSecretToken() {
        let store = populatedStore()
        let controller = controller(for: store)
        store.refreshPredictions()
        waitUntil("预测应产出候选") { !store.predictionSuggestionEntries.isEmpty }

        let menu = NSMenu()
        controller.populate(menu)
        let titles = menu.items.map(\.title)
        for title in titles {
            XCTAssertFalse(title.contains("ghp_"), "菜单标题里出现了疑似令牌的原文片段：\(title)")
            XCTAssertFalse(title.contains(String(repeating: "K", count: 12)),
                           "菜单标题里出现了疑似令牌的原文：\(title)")
        }
    }

    /// 命令区完整性：所有 `AppCommandCatalog.menuBarCommands` 都要在，且"退出"必须在。
    func testMenuCarriesEveryCommandIncludingQuit() {
        let store = makeStore()
        let controller = controller(for: store)
        let menu = NSMenu()
        controller.populate(menu)

        let titles = Set(menu.items.map(\.title))
        for command in AppCommandCatalog.menuBarCommands {
            XCTAssertTrue(titles.contains(command.title),
                          "命令 \(command.title) 没进菜单；菜单标题：\(titles)")
        }
        XCTAssertTrue(titles.contains(AppCommand.quit.title))
    }

    /// `menuWillOpen` 先刷预测再填菜单，而刷新是异步的 ⇒ 这一次打开**必然**看不到候选。
    /// 那就更不能说"暂无推荐"：这是本轮加空态文案时暴露出来的真问题，
    /// 现在由 `isRefreshingPredictions` 区分"还在算"与"算完确实没有"。
    func testMenuDistinguishesComputingFromEmpty() {
        let store = populatedStore()
        let controller = controller(for: store)
        let menu = NSMenu()

        store.refreshPredictions()
        XCTAssertTrue(store.isRefreshingPredictions, "刷新刚发起时进行中标记必须是 true")
        controller.populate(menu)
        let titlesWhileComputing = menu.items.map(\.title)
        XCTAssertTrue(titlesWhileComputing.contains("正在整理推荐…"),
                      "算的时候必须说\"正在整理推荐…\"，不能说没有。实际：\(titlesWhileComputing)")
        XCTAssertFalse(titlesWhileComputing.contains("暂无推荐"),
                       "还没算完就报\"暂无推荐\"，是把\"不知道\"说成\"没有\"")

        waitUntil("候选应到位") { !store.predictionSuggestionEntries.isEmpty }
        controller.populate(menu)
        XCTAssertTrue(menu.items.map(\.title).contains("猜你要粘贴"),
                      "算完之后重新填菜单应当出现表头与候选")
    }

    /// 空库（真的没有内容）时才是"暂无推荐"。
    func testTrulyEmptyStoreSaysNoRecommendations() {
        let store = makeStore()
        let controller = controller(for: store)
        let menu = NSMenu()
        controller.populate(menu)
        let titles = menu.items.map(\.title)
        XCTAssertTrue(titles.contains("暂无推荐"), "空库且没有刷新在飞时应说\"暂无推荐\"。实际：\(titles)")
        XCTAssertFalse(titles.contains("正在整理推荐…"), "没有刷新在飞时不该假装在算")
    }
}
