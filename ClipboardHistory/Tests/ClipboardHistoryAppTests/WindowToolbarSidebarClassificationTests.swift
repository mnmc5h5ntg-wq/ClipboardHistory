import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// `WindowConfigurator.Coordinator.isSidebarToolbarItem` 的用例（审计第二轮 08-08 / 13-08：
/// 这条"靠字符串猜再删按钮"的判断此前没有任何测试）。
///
/// 它决定从窗口工具栏里摘掉哪些项，所以两个方向都要钉：
/// **漏判**只是多留一个系统按钮；**误判**会把用户需要的按钮删掉，而且没有任何提示。
/// 因此下面负向用例（普通项必须活下来）比正向更承重。
@MainActor
final class WindowToolbarSidebarClassificationTests: XCTestCase {
    private func coordinator() -> WindowConfigurator.Coordinator {
        WindowConfigurator().makeCoordinator()
    }

    private func item(identifier: String = "item",
                      label: String = "",
                      paletteLabel: String = "",
                      toolTip: String? = nil,
                      action: Selector? = nil,
                      view: NSView? = nil) -> NSToolbarItem {
        let item = NSToolbarItem(itemIdentifier: NSToolbarItem.Identifier(identifier))
        // 坑（实测）：`item.view = nil` 会**顺手清掉 `item.action`**。
        // 第一版这里无条件赋值，于是"按 action 认出 toggleSidebar"那条用例红了 ——
        // 红的是夹具，不是产品。所以 view 只在真的有的时候赋，action 放在最后赋。
        if let view { item.view = view }
        item.label = label
        item.paletteLabel = paletteLabel
        if let toolTip { item.toolTip = toolTip }
        if let action { item.action = action }
        return item
    }

    private func assertClassified(_ item: NSToolbarItem, _ expected: Bool, _ why: String,
                                 file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertEqual(coordinator().isSidebarToolbarItem(item), expected, why, file: file, line: line)
    }

    // MARK: - 正向：这些必须被认出来（否则系统那个"显示/隐藏侧栏"按钮会留在我们自绘的窗口上）

    func testRecognisesSidebarToggleByActionSelector() {
        // 注意：这条钉的是"行为"，不是函数里那条 `item.action == #selector(...)` 直判分支 ——
        // 实测把那条直判删掉，本用例仍然绿（下面的字符串路径也会命中 "togglesidebar:"）。
        // 也就是说直判是冗余保险；写在这里是为了将来有人删字符串路径时看得见还剩什么。
        assertClassified(item(identifier: "whatever", action: #selector(NSSplitViewController.toggleSidebar(_:))),
                         true, "按 action 认不出 toggleSidebar，就会留下一个重复的侧栏按钮")
    }

    func testRecognisesSwiftUIGeneratedIdentifier() {
        assertClassified(item(identifier: "com.apple.SwiftUI.navigationSplitView.toggleSidebar"),
                         true, "SwiftUI 自己生成的那个开关必须被摘掉（这是这条判断存在的原因）")
    }

    func testRecognisesEnglishLabelsAndPaletteLabels() {
        assertClassified(item(identifier: "x", label: "Hide Sidebar"), true, "label 里的 sidebar")
        assertClassified(item(identifier: "x", label: "", paletteLabel: "Sidebar"), true, "paletteLabel 里的 sidebar")
        assertClassified(item(identifier: "x", label: "", toolTip: "toggle the sidebar"), true, "toolTip 里的 sidebar")
    }

    func testRecognisesChineseLabels() {
        // 中文系统语言下 AppKit 给的是本地化文案，英文关键词一个都命中不了。
        assertClassified(item(identifier: "x", label: "隐藏边栏"), true, "label 里的「边栏」")
        assertClassified(item(identifier: "x", label: "", toolTip: "切换侧边栏"), true, "toolTip 里的「侧边栏」")
    }

    func testRecognisesSidebarItemBehindACustomView() {
        let button = NSButton(title: "", target: nil, action: #selector(NSSplitViewController.toggleSidebar(_:)))
        let host = NSView()
        host.addSubview(button)
        assertClassified(item(identifier: "x", label: "", view: host),
                         true, "图标包在自定义 view 里时，要能顺着子视图的 action 认出来")

        let labeled = NSView()
        labeled.setAccessibilityLabel("隐藏侧边栏")
        assertClassified(item(identifier: "x", label: "", view: labeled),
                         true, "只带无障碍标签的自定义 view 也要认出来")
    }

    func testRecognisesAppKitTrackingSeparator() {
        // 既有行为：分隔追踪项和开关同属侧栏 chrome，一起摘掉。钉住它是为了将来改动时看得见，
        // 不代表"必须如此"——真要保留它，改这条用例即可（连同注释）。
        assertClassified(item(identifier: NSToolbarItem.Identifier.sidebarTrackingSeparator.rawValue),
                         true, "tracking separator 的标识里含 sidebar")
    }

    // MARK: - 负向：普通项必须活下来（误判的代价是用户少一个按钮，且没有任何提示）

    func testKeepsOrdinaryAppItems() {
        assertClassified(item(identifier: "copy", label: "复制", toolTip: "拷贝选中项"),
                         false, "我们自己造的项被误判删掉，用户就再也找不到复制按钮")
        assertClassified(item(identifier: "filter", label: "筛选"), false, "筛选项不得被误删")
        assertClassified(item(identifier: "search", label: "搜索",
                              action: #selector(NSResponder.cancelOperation(_:))), false, "带无关 action 的项不得被误删")
        assertClassified(item(identifier: "x", label: "窗口", toolTip: "调整窗口大小"), false, "含「窗口」不含边栏词")
    }

    func testKeepsEmptyAndUnrelatedItems() {
        assertClassified(item(identifier: "x"), false, "全空的项不该被删")
        let view = NSView()
        view.setAccessibilityLabel("缩略图")
        assertClassified(item(identifier: "x", label: "", view: view), false, "自定义 view 里没有侧栏线索时不得被删")
    }

    /// 大小写与"整词"都要对：`Sidebar` 命中，`side` 单独出现不该命中。
    func testMatchingIsCaseInsensitiveButNotLoose() {
        assertClassified(item(identifier: "SIDEbarThing"), true, "大小写不敏感")
        assertClassified(item(identifier: "sideboard"), false, "「side」单独出现不是侧栏线索")
        assertClassified(item(identifier: "navigation-split"), false, "「split」不在关键词里")
    }
}
