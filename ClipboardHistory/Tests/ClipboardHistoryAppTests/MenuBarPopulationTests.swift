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

    // MARK: - R110 / BACKLOG 164：菜单栏那颗图标的**身份**

    /// 把一张 `NSImage` 画进位图并返回 (PNG 字节, 墨统计)。
    ///
    /// 墨 = alpha ≥ 0.5 的像素；模板图在这里按原样（黑）绘制，两臂同一颗尺。
    private func rasterize(_ image: NSImage, side: Int) -> (data: Data, ink: Int, box: (minX: Int, minY: Int, maxX: Int, maxY: Int))? {
        guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: side, pixelsHigh: side,
                                         bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                         isPlanar: false, colorSpaceName: .deviceRGB,
                                         bytesPerRow: 0, bitsPerPixel: 0) else { return nil }
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        image.draw(in: NSRect(x: 0, y: 0, width: side, height: side))
        NSGraphicsContext.restoreGraphicsState()
        guard let bytes = rep.bitmapData else { return nil }
        let spp = rep.samplesPerPixel
        var ink = 0
        var minX = side, minY = side, maxX = -1, maxY = -1
        for py in 0..<side {
            for px in 0..<side {
                let alpha = bytes[py * rep.bytesPerRow + px * spp + (spp - 1)]
                if alpha >= 128 {
                    ink += 1
                    minX = min(minX, px); maxX = max(maxX, px)
                    minY = min(minY, py); maxY = max(maxY, py)
                }
            }
        }
        let png = rep.representation(using: .png, properties: [:]) ?? Data()
        return (png, ink, (minX, minY, maxX, maxY))
    }

    /// ①**运行时**：12 那棵分支交出去的图，必须逐像素等于「自己按同一个 symbolName
    /// 做出来的系统符号」，而且不是那段手画的兜底 —— 这一条是"换素材"唯一的产物级证据。
    /// ②**几何**：它仍占 18×18 那一格、仍是模板图（染色交给系统）。
    /// ③**读数**：墨像素与包围盒进台账，不许只留一句「已经换成 SF Symbol」。
    func testStatusBarGlyphIsTheSystemSymbolNotTheDrawnFallback() throws {
        let controller = MenuBarController()
        let product = controller.makeStatusBarIcon()
        let side = 72  // 18pt × 4

        XCTAssertEqual(product.size, NSSize(width: 18, height: 18),
                       "状态项图标换了占位那一格：这一轮只许换素材，几何要能单独归因（BACKLOG 164）")
        XCTAssertTrue(product.isTemplate,
                      "模板位丢了 ⇒ 暗色菜单栏里它会是一块黑，而不是随系统染色的白")

        let reference = try XCTUnwrap(
            NSImage(systemSymbolName: MenuBarController.statusSymbolName,
                    accessibilityDescription: "时间剪史"),
            "`\(MenuBarController.statusSymbolName)` 在这台机器上取不到系统符号 ⇒ 产品会走手画兜底，两棵表面必然不同形")
        reference.isTemplate = true
        reference.size = NSSize(width: 18, height: 18)

        guard let a = rasterize(product, side: side),
              let b = rasterize(reference, side: side) else {
            return XCTFail("画不出位图 ⇒ 这一格没有对象，不判（不是通过）")
        }
        XCTAssertGreaterThan(a.ink, 0, "交出去的图一个墨像素都没有 ⇒ 菜单栏会是一块空白")
        XCTAssertEqual(a.data.count, b.data.count, "PNG 字节数就不同：先看图再看断言")
        XCTAssertEqual(a.data, b.data,
                       "产品那颗图标与「同一个 symbolName 的系统符号」逐像素不同 ⇒ 它走的是手画兜底（或 symbolName 又分叉了）")
        // 反向牙（不是恒真式）：参考符号**不该**是空的 —— 两条臂都空时上面那句相等是假的。
        XCTAssertGreaterThan(b.ink, 0, "参考臂自己就没有墨 ⇒ 两条臂都空，① 的相等是假的")
        // 几何那一格（阈值来自本轮实测，不是先写数再找理由）：
        // 本机 72px（=18pt×4）这一格里墨包围盒 `10..60 × 7..67`、墨像素 892、墨占 0.17。
        // ⇒ 留白地板 2px（实测最小那一侧 4px）、墨量地板 400（实测 892，一半的余量）。
        // 顶到边 ⇒ 18×18 的占位把笔画裁了；墨量掉下来 ⇒ 换成了一条头发丝或一个空白格。
        let margin = 2
        XCTAssertGreaterThanOrEqual(a.box.minX, margin, "墨贴左边（minX=\(a.box.minX)）⇒ 图标在 18pt 那一格里出框")
        XCTAssertGreaterThanOrEqual(a.box.minY, margin, "墨贴下边（minY=\(a.box.minY)）⇒ 同上")
        XCTAssertLessThanOrEqual(a.box.maxX, side - 1 - margin, "墨贴右边（maxX=\(a.box.maxX)）⇒ 同上")
        XCTAssertLessThanOrEqual(a.box.maxY, side - 1 - margin, "墨贴上边（maxY=\(a.box.maxY)）⇒ 同上")
        XCTAssertGreaterThanOrEqual(a.ink, 400,
            "4× 这一格只有 \(a.ink) 个墨像素（本机实测 892）⇒ 素材掉成头发丝或半空，菜单栏里会看不清")
        XCTAssertEqual(a.box.maxX - a.box.minX + 1, b.box.maxX - b.box.minX + 1,
                       "墨宽在两臂之间不一致：像素级相等已经先红，这一条是给报表看的分带")
        CaptureReadings.emit("MENUBAR_GLYPH symbol=\(MenuBarController.statusSymbolName) 倍率=4 边=\(side)px "
                             + "墨像素=\(a.ink) 包围盒px=\(a.box.minX)..\(a.box.maxX)×\(a.box.minY)..\(a.box.maxY) "
                             + "墨占=\(String(format: "%.2f", Double(a.ink) / Double(side * side))) "
                             + "与参考=相同 模板=\(product.isTemplate)")
    }

    /// 源码那一格：symbolName **只许出现一次**（在 `MenuBarController` 的声明里），
    /// 两个调用点都引用常量。写死字面量就是"两棵表面各画各的"的下一次开端。
    func testBothSurfacesReferenceTheOneSymbolName() throws {
        let app = codeOnly(try productSource(named: "App.swift"))
        let controllerSource = codeOnly(try productSource(named: "Managers/MenuBarController.swift"))
        XCTAssertTrue(app.contains("systemImage: MenuBarController.statusSymbolName"),
                      "13+ 的 `MenuBarExtra` 没引用那颗常量 ⇒ 两棵表面的图标又能各写各的了（BACKLOG 164）")
        XCTAssertFalse(app.contains("systemImage: \""),
                       "App.swift 里又出现了写字面量的 `systemImage: \"…\"` ⇒ 请引用 `MenuBarController.statusSymbolName`")
        XCTAssertTrue(controllerSource.contains("static let statusSymbolName"),
                      "`MenuBarController.statusSymbolName` 不见了 ⇒ 那条「两个调用点共用一个名字」的结构没了")
        XCTAssertTrue(controllerSource.contains("NSImage(systemSymbolName: Self.statusSymbolName"),
                      "12 那棵分支不再按常量取系统符号 ⇒ 它又回到手画那颗了")
        let literals = (app + controllerSource).components(separatedBy: "\"\(MenuBarController.statusSymbolName)\"").count - 1
        XCTAssertEqual(literals, 1,
                       "symbolName 的字面量在两份产品源码里出现 \(literals) 次（只许 1 次，在声明处）"
                       + " ⇒ 多于一次就是有人又把名字写死在调用点上")
    }

    /// 165 的那一格：菜单已经填过（此刻刷新在飞 ⇒ 写着「正在整理推荐…」），
    /// 刷新**落地之后**没有人再叫 `populate` ⇒ 那句话就一直挂着。
    /// 这一格是"修前必须红"的证据：实现体落下去之前它应当红在下面那条断言上。
    func testMenuRepopulatesItselfWhenTheRefreshLands() {
        let store = populatedStore()
        let controller = controller(for: store)
        let menu = NSMenu()
        controller.attachLiveRefresh(to: menu, store: store)
        controller.populate(menu)
        let before = menu.items.map { $0.attributedTitle?.string ?? $0.title }
        XCTAssertTrue(before.contains("正在整理推荐…"),
                      "前提不成立 ⇒ 这一格没有对象：populate 时刷新必须仍在途中。实际：\(before)")
        // 等刷新真的收尾（结果落进 store），**不再叫 populate**
        waitUntil("预测刷新要收尾") { !store.isRefreshingPredictions }
        let after = menu.items.map { $0.attributedTitle?.string ?? $0.title }
        XCTAssertFalse(after.contains("正在整理推荐…"),
                       "刷新已经落地，这张菜单里那句「正在整理推荐…」还在 ⇒ 165：没有人重填（BACKLOG 165）")
        XCTAssertTrue(after.contains("猜你要粘贴"),
                      "刷新落地后菜单应当出现候选区。实际：\(after)")
        // 读数走局部变量，不在字符串里嵌套带引号的 `contains("…")`
        // （Swift 的插值里塞转义引号会直接把整行字面量打断，本轮实测一次）。
        let loading = "正在整理推荐…"
        let header = "猜你要粘贴"
        let beforeHangs = before.contains(loading)
        let afterHangs = after.contains(loading)
        let afterHasCandidates = after.contains(header)
        CaptureReadings.emit("MENU_LIVE_REFRESH 修前项数=" + String(before.count)
                             + " 修后项数=" + String(after.count)
                             + " 修前挂着正在整理=" + String(beforeHangs)
                             + " 修后挂着正在整理=" + String(afterHangs)
                             + " 修后有候选区=" + String(afterHasCandidates)
                             + " store候选数=" + String(store.predictionSuggestionEntries.count))
    }

    /// 机制那一格之外还要钉**接线**：`attachLiveRefresh` 若没人调，上面那条判据照样绿
    /// （判据是自己调它才通的）—— 那是「零调用点的死尺」那一族，R78 的 M416 记过。
    func testLiveRefreshIsWiredIntoTheMenuTheControllerBuilds() throws {
        let src = codeOnly(try productSource(named: "Managers/MenuBarController.swift"))
        let make = src.components(separatedBy: "func makeMenu()").dropFirst().first ?? ""
        let body = String(make.prefix(700))
        XCTAssertTrue(body.contains("attachLiveRefresh(to: menu"),
                      "12 那棵路径自己造的那张菜单没接上刷新桥 ⇒ 机制有牙但产品不咬（BACKLOG 165）")
        XCTAssertTrue(body.contains("populate(menu)"), "makeMenu 里连初次填充都没了 ⇒ 这一格的锚点漂了")
        XCTAssertTrue(src.contains("private var refreshBridge: AnyCancellable?"),
                      "订阅没有被属性持有 ⇒ 返回的 AnyCancellable 当场释放，桥活不过一次赋值")
        XCTAssertTrue(src.contains(".receive(on: DispatchQueue.main)"),
                      "同步重填会读到「算完了但候选还没写」（HistoryStore 先置 false 后写候选）⇒ "
                      + "菜单会当场从「正在整理」翻成「暂无推荐」，那是另一种假话。这一格由 M602 打红。")
    }

    /// 读一份产品源码（与 `UICaptureHarness` 同一套找法）；找不到就红，不许跳过。
    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "MenuBarPopulationTests", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }

    /// 去掉整行注释：守卫读的是**代码**，不是文档里的一句话。
    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }
}
