import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 右键菜单的收口（issue #13：未汉化 + 含无关系统项）。
///
/// 这里钉的是两件事，缺一不可：**每一项都是中文**，以及**没有窗口级/系统级无关项**。
/// 只钉第一条会漏掉"中文但无关"（例如「显示全部标签页」在中文系统里就是中文的窗口项），
/// 只钉第二条会漏掉英文注入项，所以两条各自有断言，另加一条 sanitize 的阳性对照。
@MainActor
final class ChineseTextContextMenuTests: XCTestCase {
    private func titles(_ menu: NSMenu) -> [String] {
        menu.items.filter { !$0.isSeparatorItem }.map(\.title)
    }

    private func hasCJK(_ string: String) -> Bool {
        string.unicodeScalars.contains { (0x4E00...0x9FFF).contains($0.value) }
    }

    // MARK: - 我们自己列的菜单

    func testReadOnlyMenuIsChineseAndOnlyEditingActions() {
        let menu = ChineseTextContextMenu.makeReadOnlyMenu()
        XCTAssertEqual(titles(menu), ["复制", "全选", "查找…"],
                       "只读预览区应当只有这三项；多了就是又被塞了东西")
        XCTAssertEqual(menu.items.count, 4, "三项之间只应有一条分隔线")
    }

    func testEditableMenuIsChineseAndOnlyEditingActions() {
        let menu = ChineseTextContextMenu.makeEditableMenu()
        XCTAssertEqual(titles(menu), ["撤销", "重做", "剪切", "复制", "粘贴", "全选"],
                       "搜索框的可编辑菜单项与顺序都被钉住：顺序变了用户会点错")
    }

    /// 通用形状断言：两份菜单里**任何一项**都得含中文字符。
    /// 这条比"标题在白名单里"更耐改 —— 将来加一项忘了汉化，它会红。
    func testEveryMenuItemTitleIsChinese() {
        for menu in [ChineseTextContextMenu.makeReadOnlyMenu(), ChineseTextContextMenu.makeEditableMenu()] {
            for item in menu.items where !item.isSeparatorItem {
                XCTAssertTrue(hasCJK(item.title), "右键菜单里出现非中文项：\(item.title)")
            }
        }
    }

    func testBothMenusDisableContextMenuPlugIns() {
        // `allowsContextMenuPlugIns = false` 是关掉了 AppKit 自动附加项的那道源头开关。
        XCTAssertFalse(ChineseTextContextMenu.makeReadOnlyMenu().allowsContextMenuPlugIns)
        XCTAssertFalse(ChineseTextContextMenu.makeEditableMenu().allowsContextMenuPlugIns)
    }

    // MARK: - sanitize 的牙

    func testSanitizeRemovesInjectedSystemItemsAndKeepsOurs() {
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "复制", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
        let tabOverview = NSMenuItem(title: "Show All Tabs", action: #selector(NSWindow.toggleTabOverview(_:)), keyEquivalent: "")
        let services = NSMenuItem(title: "服务", action: nil, keyEquivalent: "")
        // 听写项在中文系统里的标题就是"开始听写"：按标题挡不住它，只能按 selector 挡。
        // Swift 没有 `NSResponder.startDictation` 这个入口，所以这里只能按名字取 selector。
        let dictation = NSMenuItem(title: "开始听写", action: Selector(("startDictation:")), keyEquivalent: "")
        menu.addItem(tabOverview)
        menu.addItem(services)
        menu.addItem(dictation)

        // 阳性对照：先证明"脏东西确实在"，否则 sanitize 什么都不删也能通过。
        XCTAssertEqual(menu.items.count, 4)
        XCTAssertTrue(menu.items.contains(tabOverview))

        ChineseTextContextMenu.sanitize(menu)

        XCTAssertEqual(menu.items.count, 1, "sanitize 后只剩我们自己那一项：\(menu.items.map(\.title))")
        XCTAssertFalse(menu.items.contains(tabOverview), "按 action 挡不住 toggleTabOverview:")
        XCTAssertFalse(menu.items.contains(services), "action 为 nil 的项要按标题挡住")
        XCTAssertFalse(menu.items.contains(dictation))
    }

    func testSanitizeDropsEdgeSeparatorsOnly() {
        let menu = NSMenu()
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "全选", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
        menu.addItem(.separator())
        ChineseTextContextMenu.sanitize(menu)
        XCTAssertEqual(titles(menu), ["全选"])
        XCTAssertEqual(menu.items.count, 1, "首尾分隔线该清掉，中间的不该动")

        let withMiddle = NSMenu()
        withMiddle.addItem(NSMenuItem(title: "复制", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
        withMiddle.addItem(.separator())
        withMiddle.addItem(NSMenuItem(title: "全选", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
        ChineseTextContextMenu.sanitize(withMiddle)
        XCTAssertEqual(withMiddle.items.count, 3, "中间的分隔线是有意的分组，清掉就把视觉层级抹平了")
    }

    /// 只读区弹菜单时会再 sanitize 一次（AppKit 的注入时机在各版本上不一致）。
    /// 这条钉的是"那个回调真的会清"，而不是只钉菜单构建时的干净状态。
    func testTextViewSanitizesOnEveryOpen() {
        let textView = ChineseSelectableNSTextView()
        textView.string = "一段可以复制的文本"
        guard let menu = textView.menu else {
            XCTFail("只读文本区没有菜单")
            return
        }
        menu.addItem(NSMenuItem(title: "Show Tab Bar", action: #selector(NSWindow.toggleTabBar(_:)), keyEquivalent: ""))
        // 实测这份菜单是"3 项 + 1 条分隔线 = 4"，装上脏项后是 5。
        // 先证明脏项确实在，sanitize 才有内容可清（否则这条断言会绿在空集上）。
        XCTAssertEqual(menu.items.count, 5, "夹具没把脏项装上，这条测不到东西")
        textView.menuWillOpen(menu)
        XCTAssertEqual(titles(menu), ["复制", "全选", "查找…"],
                       "menuWillOpen 之后仍带着系统项 —— 说明弹出前的清理没生效")
        XCTAssertEqual(menu.items.count, 4, "清掉脏项后应当回到 3 项 + 1 条分隔线")
    }

    // MARK: - 两个"别偷偷改回去"的源码守卫

    func testSearchFieldNoLongerSwallowsTheRightClick() throws {
        let source = try productSource(named: "Views/ChineseTextContextMenu.swift")
        XCTAssertFalse(source.contains("editor.menu = nil"),
                       "搜索框又被改成「完全没有右键菜单」了 —— 那是压英文项的老办法，issue #13 要的是中文菜单")
        XCTAssertTrue(source.contains("makeEditableMenu()"), "搜索框应当接在可编辑中文菜单上")
    }

    func testAutomaticWindowTabbingIsDisabledAtLaunch() throws {
        let source = try productSource(named: "Managers/ApplicationShell.swift")
        XCTAssertTrue(source.contains("NSWindow.allowsAutomaticWindowTabbing = false"),
                      "「Show All Tabs」这类窗口级项的源头开关被移除了（issue #13）")
        // 必须在建窗之前设：applicationWillFinishLaunching 里。
        let willFinish = try XCTUnwrap(
            source.components(separatedBy: "func applicationWillFinishLaunching").dropFirst().first
        )
        XCTAssertTrue(willFinish.prefix(700).contains("allowsAutomaticWindowTabbing = false"),
                      "设晚了等于没设 —— 窗口已经建好，注入项也已经进菜单了")
    }

    /// 在屏探针自己会 `install()`，所以它证明不了**产品**在启动时装过监视器。
    /// 这条源码守卫补上那个缺口：把 install 从 `applicationWillFinishLaunching` 里删掉，
    /// 这条必须红（否则"搜索框右键是中文的"这个结论只在测试进程里成立）。
    func testFieldEditorInterceptorIsInstalledAtLaunch() throws {
        let source = try productSource(named: "Managers/ApplicationShell.swift")
        let willFinish = try XCTUnwrap(
            source.components(separatedBy: "func applicationWillFinishLaunching").dropFirst().first
        )
        XCTAssertTrue(willFinish.prefix(1200).contains("FieldEditorRightClickInterceptor.install()"),
                      "编辑态右键的拦截监视器没在启动时装 —— 用户实际用的那份还是系统菜单")
    }

    /// 拦截器的"认领范围"必须窄：只认我们自己的搜索框。
    /// 这条钉的是 `owningSearchField` 的判据来源（沿 superview 往上找 `ChineseMenuTextField`），
    /// 而不是让它退化成"凡是 field editor 都吞"。
    func testInterceptorOnlyClaimsOurOwnSearchFields() throws {
        let source = try productSource(named: "Views/ChineseTextContextMenu.swift")
        XCTAssertTrue(source.contains("as? ChineseMenuTextField"),
                      "拦截器不再按『是不是我们的搜索框』认领右键 —— 会吞掉别的文本控件的右键菜单")
        XCTAssertFalse(containsInstallInController(source),
                       "监视器被装到了视图层：每次重建 NSView 都会多装一个，右键会被重复处理")
    }

    private func containsInstallInController(_ source: String) -> Bool {
        source.components(separatedBy: "\n").contains { $0.contains("Interceptor.install()") }
    }

    /// 别再回到"给共享 field editor 挂菜单"那条路：实测 AppKit 会把它复原（D-032 里记着数字）。
    /// 这条守卫不是风格洁癖 —— 那段代码看着像修好了，其实什么都没改。
    func testNobodyAssignsTheSharedFieldEditorsMenuAgain() throws {
        let source = try productSource(named: "Views/ChineseTextContextMenu.swift")
        let codeOnly = source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("///") }
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        XCTAssertFalse(codeOnly.contains("editor.menu ="),
                       "又给共享 field editor 挂菜单了 —— 这条路实测无效（会被 AppKit 覆盖），别再回来")
        XCTAssertFalse(codeOnly.contains("allowsContextMenuPlugIns = true"),
                       "有人把自动附加项的源头开关打开了")
    }

    /// 认领判据本身：沿 superview 往上找，找到我们的搜索框才算我们的。
    /// 不靠窗口、不靠当前事件，所以这条能在普通 `swift test` 里跑。
    func testInterceptorRecognisesOnlyEditorsNestedInOurSearchField() {
        let field = ChineseMenuTextField(frame: NSRect(x: 0, y: 0, width: 200, height: 22))
        let editor = NSTextView(frame: NSRect(x: 0, y: 0, width: 200, height: 22))
        let clip = NSView(frame: NSRect(x: 0, y: 0, width: 200, height: 22))
        clip.addSubview(editor)
        field.addSubview(clip)
        XCTAssertTrue(FieldEditorRightClickInterceptor.owningSearchField(of: editor) === field,
                      "搜索框里的 field editor 没被认出来 —— 拦截器会形同不存在")

        let stranger = NSTextView(frame: NSRect(x: 0, y: 0, width: 200, height: 22))
        XCTAssertNil(FieldEditorRightClickInterceptor.owningSearchField(of: stranger),
                     "别人的文本视图也被认领了 —— 那会把别的控件的右键菜单吞掉")
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
        throw XCTSkip("找不到 Sources/ClipboardHistoryApp/\(relativePath)")
    }
}
