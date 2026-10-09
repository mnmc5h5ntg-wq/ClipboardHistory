import AppKit
import SwiftUI

/// 应用内所有右键菜单的唯一出口（issue #13）。
///
/// 两条原则：
/// ① **文案一律中文**，所以菜单项由我们自己列，不用 AppKit 的自动菜单；
/// ② **不出现无关项**。系统会往"含标准编辑动作"的菜单里塞东西（窗口标签页的
///    「Show All Tabs」、服务、听写、表情与符号、查询、共享…），这些与时间剪史无关。
///    挡它有两层：`allowsContextMenuPlugIns = false` + `NSWindow.allowsAutomaticWindowTabbing = false`
///    从源头关，`sanitize` 在每次弹出前再清一遍（AppKit 的注入发生在 menuWillOpen 前后，
///    不同 macOS 版本时机不一样，所以不能只靠源头）。
///
/// 归属权（在屏探针实测，别按直觉理解）：**编辑态下右键根本不经过搜索框自己**。
/// 事件被直接投给窗口共享的 field editor（`NSTextView`，挂在 `_NSKeyboardFocusClipView` 下），
/// 而它的 `menu` 会被 AppKit 复原、`menu(for:)` 每次现造一份新的 —— 都改不动。
/// 所以编辑态那份由 `FieldEditorRightClickInterceptor` 在派发前截走；非编辑态才走 `menu(for:)`。
enum ChineseTextContextMenu {
    /// 按 action 挡：标题会被本地化（同一台机器换语言就变），selector 不会。
    static let blockedActions: Set<String> = [
        "toggleTabOverview:", "toggleTabBar:", "showAllTabsBar:",
        "selectNextTab:", "selectPreviousTab:", "moveTabToNewWindow:", "mergeAllWindows:",
        "orderFrontServicesMenu:", "orderFrontFontPanel:", "orderFrontColorPanel:",
        "startDictation:", "orderFrontCharacterPalette:",
        "orderFrontAutoFillPanel:", "_showWritingTools:",
    ]

    /// 兜底：action 为空的注入项（有些子菜单只给标题）。比较时用小写英文 + 常见中文写法。
    /// 这份名单只用于"挡住已经出现的脏项"，不是白名单 —— 白名单在 `make*Menu` 里逐条写死。
    static let blockedTitles: Set<String> = [
        "show all tabs", "hide tab bar", "show tab bar", "move tab to new window",
        "merge windows", "merge all windows", "services", "服务",
        "start dictation", "dictation", "emoji & symbols", "symbols and emoji",
        "characters", "look up", "share", "quick look",
        "autofill", "writing tools", "speech", "start speaking", "stop speaking",
        "font", "show fonts", "colors", "show colors",
    ]

    /// 只读文本区（详情预览）：复制 / 全选 / 查找。
    static func makeReadOnlyMenu(delegate: NSMenuDelegate? = nil) -> NSMenu {
        let menu = NSMenu()
        menu.allowsContextMenuPlugIns = false
        menu.addItem(item("复制", action: #selector(NSText.copy(_:)), key: "c"))
        menu.addItem(.separator())
        menu.addItem(item("全选", action: #selector(NSText.selectAll(_:)), key: "a"))
        menu.addItem(item("查找…", action: #selector(NSResponder.performTextFinderAction(_:)), key: "f", tag: NSTextFinder.Action.showFindInterface.rawValue))
        menu.delegate = delegate
        sanitize(menu)
        return menu
    }

    /// 可编辑文本框（搜索框）：撤销 / 重做 / 剪切 / 复制 / 粘贴 / 全选。
    ///
    /// 以前搜索框是**整个右键菜单都不给**（`menu(for:) -> nil` + 吞掉 rightMouseDown），
    /// 那是为了压掉英文系统项而把功能一起砍了。issue #13 的验收要求是"中文且只含合理编辑动作"，
    /// 所以这里给回一份收口过的菜单。两个用它的地方：
    /// ① 非编辑态 —— `ChineseMenuTextField.menu(for:)`（右键命中文本框自己）；
    /// ② 编辑态 —— `FieldEditorRightClickInterceptor` 从共享 field editor 手里截走。
    static func makeEditableMenu() -> NSMenu {
        let menu = NSMenu()
        menu.allowsContextMenuPlugIns = false
        // 撤销/重做走响应链上的 NSUndoManager，selector 没有 Swift 侧的强类型入口，
        // 只能按名字取；取不到时菜单项会显示为灰色（可接受，不会崩）。
        menu.addItem(item("撤销", action: Selector(("undo:")), key: "z"))
        menu.addItem(item("重做", action: Selector(("redo:")), key: "Z"))
        menu.addItem(.separator())
        menu.addItem(item("剪切", action: #selector(NSText.cut(_:)), key: "x"))
        menu.addItem(item("复制", action: #selector(NSText.copy(_:)), key: "c"))
        menu.addItem(item("粘贴", action: #selector(NSText.paste(_:)), key: "v"))
        menu.addItem(item("全选", action: #selector(NSText.selectAll(_:)), key: "a"))
        // 编辑态那份是**现场交给拦截器**的，不是挂到某个视图上，所以没有"我们子类化的文本视图"
        // 当代理可用 —— 弹出前的清理只能靠这个常驻代理（`NSMenu.delegate` 是 weak，必须有人持有它）。
        menu.delegate = sanitizer
        sanitize(menu)
        return menu
    }

    /// 每次弹出前再 sanitize 一遍的常驻代理。
    /// 它是无状态的（`sanitize` 只改传进来的那份菜单），所以能安全共享；
    /// `NSMenu.delegate` 是 weak，必须有个长命的持有者，否则代理一出去就没了。
    static let sanitizer = MenuSanitizer()

    final class MenuSanitizer: NSObject, NSMenuDelegate, Sendable {
        func menuWillOpen(_ menu: NSMenu) {
            ChineseTextContextMenu.sanitize(menu)
        }
    }

    /// 就地清掉无关项与多余分隔线。`menuWillOpen` 里也要调一次：
    /// AppKit 的自动注入可能发生在菜单构建之后。
    static func sanitize(_ menu: NSMenu) {
        menu.allowsContextMenuPlugIns = false
        for item in menu.items.reversed() where isBlocked(item) {
            menu.removeItem(item)
        }
        while menu.items.first?.isSeparatorItem == true {
            menu.removeItem(at: 0)
        }
        while menu.items.last?.isSeparatorItem == true, !menu.items.isEmpty {
            menu.removeItem(at: menu.items.count - 1)
        }
    }

    static func isBlocked(_ item: NSMenuItem) -> Bool {
        if let action = item.action, blockedActions.contains(NSStringFromSelector(action)) {
            return true
        }
        let title = item.title.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !title.isEmpty else { return false }
        return blockedTitles.contains(title)
    }

    private static func item(
        _ title: String,
        action: Selector,
        key: String,
        tag: Int = 0
    ) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: key)
        item.target = nil
        item.tag = tag
        return item
    }
}

struct ChineseEditableTextField: NSViewRepresentable {
    @Binding var text: String
    let placeholder: String

    func makeNSView(context: Context) -> ChineseMenuTextField {
        let textField = ChineseMenuTextField()
        textField.delegate = context.coordinator
        textField.isBordered = false
        textField.isBezeled = false
        textField.drawsBackground = false
        // 以前这里是 `.none`：搜索框拿不到任何可见焦点提示，键盘用户 Tab 过来也看不出
        // 焦点在哪（审计第二轮 1.10 / R2-02）。恢复系统焦点环。
        textField.focusRingType = .default
        textField.font = .systemFont(ofSize: 13)
        textField.textColor = .secondaryLabelColor
        textField.placeholderString = placeholder
        textField.lineBreakMode = .byTruncatingTail
        textField.setContentHuggingPriority(.defaultLow, for: .horizontal)
        textField.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        textField.configureSingleLineEditing()
        textField.stringValue = text
        return textField
    }

    func updateNSView(_ nsView: ChineseMenuTextField, context: Context) {
        // 编辑中不覆盖（避免打断输入法组字）
        guard nsView.currentEditor() == nil else { return }
        if nsView.stringValue != text {
            nsView.stringValue = text
        }
        nsView.placeholderString = placeholder
        nsView.configureSingleLineEditing()
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(text: $text)
    }

    @MainActor
    final class Coordinator: NSObject, NSTextFieldDelegate {
        private let text: Binding<String>

        init(text: Binding<String>) {
            self.text = text
        }

        // 这里**不再**往 field editor 上挂菜单了。实测（本轮 EXP2）：
        // `editor.menu = 我们那份` 会被 AppKit 覆盖回去 —— 右键时 `editor.menu` 读出来是
        // 「剪切/拷贝/粘贴/粘贴并匹配样式/快速查看附件/字体/拼写和语法/替换/转换/语音/书写方向/布局方向」，
        // 正是 issue #13 报的那一串；而且 `menu(for:)` 每次现造一份新的，改它不留住（第二次问还是满的、
        // `allowsContextMenuPlugIns` 还是 true）。编辑态的右键只能从事件层截走，见 `FieldEditorRightClickInterceptor`。

        func controlTextDidChange(_ notification: Notification) {
            guard let tf = notification.object as? NSTextField else { return }
            // 输入法组字中不推送（避免中间态破坏候选词）
            if let editor = tf.currentEditor(), let marked = (editor as? NSTextView)?.markedRange(), marked.length > 0 {
                return
            }
            text.wrappedValue = tf.stringValue
        }

        func controlTextDidEndEditing(_ notification: Notification) {
            guard let tf = notification.object as? NSTextField else { return }
            text.wrappedValue = tf.stringValue
        }
    }
}

/// 把"编辑态搜索框上的右键"从共享 field editor 手里截走（issue #13）。
///
/// 为什么只能这么拦：编辑态下命中并处理右键的是**窗口共享的 field editor**
/// （`NSTextView`，挂在 `_NSKeyboardFocusClipView` 下）。我们不是它的子类化宿主，
/// 既改不动它的 `menu`（会被 AppKit 覆盖），也改不动它每次现造的 `menu(for:)`。
/// 本地事件监视器（`addLocalMonitorForEvents`）是 AppKit 派发给窗口**之前**的唯一合法出口，
/// 只作用于本 App 的事件流，不碰别的 app，也不需要换 window delegate。
@MainActor
enum FieldEditorRightClickInterceptor {
    /// 交付出口。默认就是"真弹"；在屏探针把它换成"只记录不弹"
    /// （`popUpContextMenu` 模态且实测取消不掉，真弹会把测试进程钉住）。
    static var present: (NSView, NSEvent, NSMenu) -> Void = { view, event, menu in
        NSMenu.popUpContextMenu(menu, with: event, for: view)
    }

    private static var monitorToken: Any?

    /// 在 `applicationWillFinishLaunching` 里装一次；重复调用是幂等的。
    static func install() {
        guard monitorToken == nil else { return }
        monitorToken = NSEvent.addLocalMonitorForEvents(matching: [.rightMouseDown, .otherMouseDown]) { event in
            // 回调闭包是 `@Sendable` 的，不能直接碰 `@MainActor` 的状态。事件监视本来就跑在主线程
            // 派发路径上，所以这里只在"确实在主线程"时处理，其它情况原样交回（不吞别人的事件）。
            if FieldEditorRightClickInterceptor.isOnMainThread {
                return FieldEditorRightClickInterceptor.handle(event)
            }
            return event
        }
    }

    static func uninstall() {
        if let monitorToken { NSEvent.removeMonitor(monitorToken) }
        monitorToken = nil
    }

    /// 纯判定：这次右键是不是"落在我们某个搜索框的 field editor 上"。
    /// 拆出来是为了能在不弹菜单、不依赖当前事件的前提下单独测（在屏探针的两个方向都靠它）。
    static func owns(event: NSEvent) -> Bool {
        event.type == .rightMouseDown || event.type == .otherMouseDown ? owningField(of: event) != nil : false
    }

    /// 命中就返回 nil（把事件吞掉，AppKit 那条"弹系统那份"的路就不走了），否则原样交回。
    @discardableResult
    static func handle(_ event: NSEvent) -> NSEvent? {
        guard let field = owningField(of: event) else { return event }
        present(field, event, ChineseTextContextMenu.makeEditableMenu())
        return nil
    }

    static func owningField(of event: NSEvent) -> ChineseMenuTextField? {
        guard let window = event.window, let editor = window.firstResponder as? NSTextView else { return nil }
        return owningSearchField(of: editor)
    }

    /// field editor 是共享的、且挂在文本框的子视图树里（实测 `editor.isDescendant(of: 搜索框) == true`），
    /// 所以顺着 superview 往上找就能确认"这次编辑属于我们的搜索框"，不需要私有 API。
    static func owningSearchField(of editor: NSView) -> ChineseMenuTextField? {
        var current: NSView? = editor
        while let view = current {
            if let field = view as? ChineseMenuTextField { return field }
            current = view.superview
        }
        return nil
    }

    private static var isOnMainThread: Bool { Thread.isMainThread }
}

final class ChineseMenuTextField: NSTextField {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        configureSingleLineEditing()
        menu = ChineseTextContextMenu.makeEditableMenu()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        configureSingleLineEditing()
        menu = ChineseTextContextMenu.makeEditableMenu()
    }

    func configureSingleLineEditing() {
        guard let textFieldCell = cell as? NSTextFieldCell else { return }
        textFieldCell.usesSingleLineMode = true
        textFieldCell.wraps = false
        textFieldCell.isScrollable = true
    }

    /// 非编辑态（框里还没进 field editor）时，右键命中的是文本框自己，走这里。
    /// 编辑态下右键属于共享 field editor，不走这里 —— 那一份在 `Coordinator` 里挂到 editor 上。
    /// 每次现做一份：菜单项的可用态由响应链在 update() 时算，复用同一份会带着上一次的灰态。
    override func menu(for event: NSEvent) -> NSMenu? {
        ChineseTextContextMenu.makeEditableMenu()
    }
}

struct ChineseSelectableTextView: NSViewRepresentable {
    let text: String
    let font: NSFont

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = true
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false

        let textView = ChineseSelectableNSTextView()
        textView.isEditable = false
        textView.isSelectable = true
        textView.drawsBackground = false
        textView.font = font
        textView.textColor = .labelColor
        textView.textContainerInset = NSSize(width: 20, height: 20)
        textView.textContainer?.widthTracksTextView = false
        textView.textContainer?.heightTracksTextView = false
        textView.minSize = NSSize(width: 0, height: 0)
        textView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        textView.isHorizontallyResizable = true
        textView.isVerticallyResizable = true
        textView.autoresizingMask = [.width]
        textView.applyReadOnlyMenuBehavior()
        textView.string = text

        scrollView.documentView = textView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let textView = scrollView.documentView as? ChineseSelectableNSTextView else { return }
        if textView.string != text {
            textView.string = text
        }
        textView.font = font
        textView.applyReadOnlyMenuBehavior()
    }
}

final class ChineseSelectableNSTextView: NSTextView, NSMenuDelegate {
    convenience init() {
        let storage = NSTextStorage()
        let layoutManager = NSLayoutManager()
        let textContainer = NSTextContainer(
            containerSize: NSSize(
                width: CGFloat.greatestFiniteMagnitude,
                height: CGFloat.greatestFiniteMagnitude
            )
        )
        storage.addLayoutManager(layoutManager)
        layoutManager.addTextContainer(textContainer)
        self.init(frame: .zero, textContainer: textContainer)
    }

    override init(frame frameRect: NSRect, textContainer container: NSTextContainer?) {
        super.init(frame: frameRect, textContainer: container)
        applyReadOnlyMenuBehavior()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        applyReadOnlyMenuBehavior()
    }

    func applyReadOnlyMenuBehavior() {
        isRichText = false
        importsGraphics = false
        usesFontPanel = false
        allowsDocumentBackgroundColorChange = false
        isAutomaticQuoteSubstitutionEnabled = false
        isAutomaticDashSubstitutionEnabled = false
        isAutomaticTextReplacementEnabled = false
        isAutomaticSpellingCorrectionEnabled = false
        isContinuousSpellCheckingEnabled = false
        enabledTextCheckingTypes = 0
        menu = ChineseTextContextMenu.makeReadOnlyMenu(delegate: self)
        selectedTextAttributes = [
            .backgroundColor: NSColor.selectedTextBackgroundColor,
            .foregroundColor: NSColor.selectedTextColor
        ]
    }

    /// 只读文本区自己就是命中视图（在屏实测：右键确实落到这里），
    /// 所以这里显式弹我们那份 —— `NSTextView` 的默认实现会在 `menuForEvent:` 之外
    /// 再拼上「拼写和语法 / 书写方向 / 布局方向」那一套。
    override func rightMouseDown(with event: NSEvent) {
        NSMenu.popUpContextMenu(ChineseTextContextMenu.makeReadOnlyMenu(delegate: self), with: event, for: self)
    }

    override func menu(for event: NSEvent) -> NSMenu? {
        ChineseTextContextMenu.makeReadOnlyMenu(delegate: self)
    }

    func menuWillOpen(_ menu: NSMenu) {
        // AppKit 的自动注入发生在这里之前/之后都有可能，所以每次弹出前再清一遍。
        ChineseTextContextMenu.sanitize(menu)
    }
}

