import AppKit

/// ⌃⌥⇧V 快速选择浮层（第三轮审计 §5 F-3）。
///
/// spike 的结论决定了这个形状（账本 D-041）：**"不激活本应用就把键盘焦点交给浮层"这条路证不出来**。
/// 裸二进制里 `NSApp.activate(ignoringOtherApps:)` 是空操作，`panel.isKeyWindow` 在激活前后都是 false，
/// 于是 spike 对"能不能"没有任何判别力 —— 而这条路的机制前提（非激活面板成为 key window）
/// 在 AppKit 的公开文档里也是"面板可以不激活应用就显示，但要接键盘就得成为 key window"。
/// 所以这里走的是**本产品已经在用、且线上确认可用**的那条路：
/// `WindowManager.showMainWindow` 同样是 `activate(ignoringOtherApps: true)` + 成 key，
/// 用户今天能用 ⌃⌥V 呼出主窗口并立刻打字，就是这条路的现成证据。
///
/// 差异只在"轻"：不打开整窗，只给一个搜索框 + 候选列表，回车 = 复制并粘回原应用，
/// Esc = 关掉、什么都不动。目标应用因此不需要重新切回来。
@MainActor
final class QuickPickController: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    private struct Row {
        let entry: HistoryStore.Entry
        let title: String
    }

    private var panel: NSPanel?
    private var field: NSTextField?
    private var table: NSTableView?
    /// 空结果时那一句（R7 / 审计 B-P2）。以前是一片空白。
    private var emptyLabel: NSTextField?
    /// 空结果时的可见下一步（R407）。主窗口的同款空态有「清除搜索」按钮，
    /// 浮层只有一句“按 Esc 清空” —— 同一个处境在两个表面给两套答案。
    private var emptyAction: NSButton?
    /// 空句 + CTA 的容器：独立钉在 content 上，不占主 stack 的 arranged subviews
    /// （R408 runner 上多一项会把句子挤离搜索框，gap 33pt；R409 改为直钉）。
    private var emptyBox: NSView?
    /// R409：主输入框的悬停边界。旧面板里它是一行裸文字，
    /// 和主窗口的 `SearchField` 不是同一套语言；只在悬停时出现，静置保持原样。
    private var searchBackdrop: QuickPickSearchBackdrop?
    private var clearButton: NSButton?
    private var model = QuickPickModel(all: [])
    private var rows: [Row] = []

    private let historyStore: () -> HistoryStore?
    /// 提交一条。生产接的是 `ApplicationShell.copyAndPasteEntry`（复制 + 粘回原应用）。
    private let commit: (HistoryStore.Entry) -> Void

    init(historyStore: @escaping () -> HistoryStore?, commit: @escaping (HistoryStore.Entry) -> Void) {
        self.historyStore = historyStore
        self.commit = commit
    }

    var isVisible: Bool { panel?.isVisible == true }

    func toggle() {
        if isVisible {
            hide()
        } else {
            show()
        }
    }

    /// 取一次最新历史。刚复制的东西必须立刻能被搜到 —— 这是这个浮层存在的意义。
    /// 单独成函数而不是塞在 `show()` 里：`show()` 要真的把面板显示出来（在测试进程里
    /// `NSApp.activate` 是空操作，面板也拿不到 key window —— spike 实测），
    /// 而"输入 → 候选 → 回车提交的是哪一条"这条链必须在不起面板的前提下也能被验。
    func refreshEntries() {
        model.all = historyStore()?.entries ?? []
    }

    func show() {
        let panel = ensurePanel()
        refreshEntries()
        model.reset()
        rebuildRows()
        field?.stringValue = ""
        model.index = 0
        selectCurrentRow()
        // R421：先放好再出场。以前建在 (0,0) 就再也没动过 —— 那是屏幕左下角，常常压在 Dock 上。
        if let visible = screenForPresentation?.visibleFrame {
            placePanel(in: visible)
        }
        panel.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        if panel.makeFirstResponder(field) {
            // 面板一出来字段就是第一响应者：这是「可以打字」的真实承诺，焦点边界要跟着亮。
            // 拿不到第一响应者就不亮 —— 与 R141 录制环同一条规矩，别画假承诺。
            searchBackdrop?.focused = true
        }
    }

    /// R421：面板落点。屏幕优先取**鼠标所在**那一块（热键呼出跟随工作区），取不到再退回主屏。
    /// 捕获路径（`windowForCapture`）**不读屏幕、不改窗口位置** —— 帧仍然只拍内容。
    private var screenForPresentation: NSScreen? {
        NSScreen.screens.first { $0.frame.contains(NSEvent.mouseLocation) } ?? NSScreen.main
    }

    /// internal 只给单测拿真 `NSPanel.frame` 验落点；产品路径只从 `show()` 调。
    func placePanel(in visibleFrame: CGRect) {
        guard let panel else { return }
        panel.setFrameOrigin(QuickPickPlacement.origin(panelSize: panel.frame.size,
                                                      visibleFrame: visibleFrame))
    }

    /// 只给离屏帧夹具用（`UICaptureTests`）：把面板建出来、按 `query` 填好行，
    /// 但**不 `makeKeyAndOrderFront`、不 `activate`** —— 那两件事会抢走用户的前台，
    /// 而捕获套件有一条硬边界：不许碰真窗口（与 `CLIPBOARD_HISTORY_DATA_DIR` 同一族理由）。
    ///
    /// 返回的是**面板本身**而不是它的 contentView —— 这一点仍然成立，但 R19 给的原因作废了。
    /// R19 写的是"把 `contentView` 摘出来塞进另一个窗口，`NSStackView` 会塌成 24×49
    /// （它自己的尺寸约束与搬家后重新生成的换算约束打架）"。R63 实测：
    /// **不搬家也塌**，同一条探针量到 24×49 与 `NSScrollView` 0×0，
    /// 根因在 `ensurePanel()` 里（`NSStackView` 生下来 `translatesAutoresizingMaskIntoConstraints == false`，
    /// 所以产品当时那两行 `frame` + `autoresizingMask` 是空操作）。
    /// 现在拍窗口仍然比拍 contentView 好：窗口才有标题栏区域的真实合成，
    /// 而"搬家会不会弄坏布局"已经不是理由 —— 布局坏了要能被判据抓到，不是被绕开。
    ///
    /// 返回 `nil` 表示面板没建起来 ⇒ 夹具必须**当场红**，
    /// 不许拿一张空白窗当"这就是浮层"（那种帧看着像证据，其实什么都没说）。
    /// 与 `SettingsView.initialCategory` / `DetailView.initialMarkdownMode` 同一手法：
    /// 产品路径一行都不改，只是把"拍得到"这件事变成可能。
    func windowForCapture(query: String = "", hoveredRow: Int? = nil,
                          searchHovered: Bool = false,
                          searchFocused: Bool = false) -> NSWindow? {
        let panel = ensurePanel()
        refreshEntries()
        model.reset()
        if !query.isEmpty { model.setQuery(query) }
        field?.stringValue = query
        updateClearButton(for: query)
        rebuildRows()
        model.index = 0
        selectCurrentRow()
        rowHoveredForCapture = hoveredRow
        searchBackdrop?.hoveredForCapture = searchHovered
        searchBackdrop?.focusedForCapture = searchFocused
        searchBackdrop?.needsDisplay = true
        searchBackdrop?.displayIfNeeded()
        return panel
    }

    /// 离屏帧夹具用：告诉表格"第 N 行是悬停的"（R67）。
    ///
    /// 为什么要有它：`cacheDisplay` 这条通道送不进 `mouseEntered` / `mouseMoved`
    /// （BACKLOG 95 记的就是这条通道的边界），而没有入口就等于"悬停那一帧"在帧基线里
    /// 永远不存在 —— 那一档就成了"代码里有、产物里没有"的东西（R14 那一课）。
    ///
    /// 为什么存的是**行号**而不是去点亮某个 row view：row view 是表格在布局时才建的。
    /// 本方法第一版写的是"`enumerateAvailableRowViews` 里挨个设 `hovered = true`"，
    /// 而调用点在 `windowForCapture` 里 —— 那时一行 row view 都还不存在，遍历到 0 个，
    /// 于是帧逐像素不变，判据红在"什么都没画出来"那一格上（红得对，但当时还不知道原因）。
    /// 存行号、由 `drawBackground` 在画的时候问一次，就没有"什么时候点亮"这个时序问题，
    /// 而且帧上那层灰与鼠标进来的那层灰是**同一段绘制代码**的产物。
    var rowHoveredForCapture: Int? {
        didSet {
            guard rowHoveredForCapture != oldValue, let table else { return }
            table.enumerateAvailableRowViews { rowView, _ in (rowView as? QuickPickRowView)?.refreshFromOutside() }
        }
    }

    func hide() {
        searchBackdrop?.focused = false
        panel?.orderOut(nil)
    }

    /// 输入变化：查询词进模型、刷新列表、下标夹住。
    func queryChanged(_ text: String) {
        updateClearButton(for: text)
        model.setQuery(text)
        // rebuildRows 里已经有 reloadData —— 这里以前还再调一次，
        // 两次刷新会让表格在输入法的每个候选字上重排两遍（打字时肉眼可见的抖动）。
        rebuildRows()
        selectCurrentRow()
    }

    /// 一条按键该做什么。**纯判定**，所以"↑↓ 移动、↩ 提交、Esc 关闭、其它透传"
    /// 能被单测钉住 —— 在离屏环境里把真按键路由进面板是测不到的（见类注释与 D-041）。
    enum KeyOutcome: Equatable {
        case move(Int)
        case commit
        case dismiss
        case passThrough
    }

    static func outcome(for event: NSEvent) -> KeyOutcome {
        switch event.keyCode {
        case 125: return .move(1)                       // ↓
        case 126: return .move(-1)                      // ↑
        case 36, 76: return .commit                     // ↩ / 数字键盘 ↩
        case 53: return .dismiss                        // ⎋
        default: return .passThrough
        }
    }

    @discardableResult
    func handle(keyEvent event: NSEvent) -> KeyOutcome {
        let outcome = Self.outcome(for: event)
        switch outcome {
        case .move(let delta):
            model.move(delta: delta)
            selectCurrentRow()
        case .commit:
            if let entry = model.selection {
                hide()
                commit(entry)
            } else {
                // 没有候选时回车什么都不该做（更不能"提交上一条还在列表里的东西"）
                hide()
            }
        case .dismiss:
            hide()
        case .passThrough:
            break
        }
        return outcome
    }

    // MARK: - 面板

    private func ensurePanel() -> NSPanel {
        if let panel { return panel }
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 420, height: 300),
            styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.isFloatingPanel = true
        panel.level = .floating
        // 关掉之后不许留在屏幕上：快速选择浮层的内容就是用户的剪贴板，
        // 藏着一份没人看得见的历史是不必要的暴露面。
        panel.isReleasedWhenClosed = false
        panel.hidesOnDeactivate = false
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.collectionBehavior = [.transient, .ignoresCycle]
        // 快速面板不要系统的 genie/缩放动画：那是"窗口被收进 Dock"的语义，
        // 而这个面板是"呼出即输入"。同类工具 Maccy 的 `FloatingPanel.swift:38` 也是这么设的。
        //
        // 也**不自己补一段淡入**（动效审计 M3 定稿；报告 §12.1 更正 #7、红线 8）：
        // 这是热键 / 每天上百次的入口，Maccy、alt-tab、CodeEdit、Ice 四家在热键呼出路径上
        // 全部瞬时出现，alt-tab 连退场淡出都做成默认关闭的开关。
        // 动效只留给内容与尺寸变化 —— 而这个面板是固定 420×300，没有可变尺寸那一步。
        panel.animationBehavior = .none

        let field = QuickPickSearchField()
        field.forwarding = { [weak self] event in
            guard let self else { return false }
            // 返回 true = 这一键被浮层吃掉了（↑↓↩⎋）；false = 交回正常文本编辑（打字、退格、输入法）。
            return self.handle(keyEvent: event) != .passThrough
        }
        field.placeholderString = "搜索历史记录…"
        // R71 / BACKLOG 99：这里原来是字面量 14，而主窗口那颗搜索框
        // （`SearchField.swift:14`）用的是 `VisualFont.body`(13) ⇒ **同一个控件在两个表面响一档**。
        // 浮层没有理由比主窗口更响：它是"快"，不是"大"。
        field.font = .systemFont(ofSize: VisualFont.body)
        field.isBordered = false
        field.drawsBackground = false
        field.delegate = self

        let table = NSTableView()
        let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("quickPick"))
        column.resizingMask = .autoresizingMask
        table.addTableColumn(column)
        table.headerView = nil
        table.rowHeight = 34
        table.backgroundColor = .clear
        table.selectionHighlightStyle = .regular
        table.dataSource = self
        table.delegate = self
        table.target = self
        table.doubleAction = #selector(commitTapped(_:))

        let scroll = NSScrollView()
        scroll.documentView = table
        scroll.hasVerticalScroller = true
        scroll.drawsBackground = false
        scroll.borderType = .noBorder

        guard let content = panel.contentView else {
            // 带 .titled 的面板正常一定有 contentView；这里不 force unwrap 是因为
            // 这个函数在快捷键回调链上跑，一次崩溃的表现是"按 ⌃⌥⇧V 应用直接没了"。
            // 拿不到容器就安静地不显示，比崩掉更可用（下面调用方按 isVisible 决定 toggle 方向）。
            return panel
        }
        // 空结果那一句。位置在 stack 里排**在列表前面**（R63 改的，理由见下面 `stack` 那段注释）。
        let empty = NSTextField(labelWithString: "")
        // 状态文案那一档由 `StatePresentation.messageFontSize` 定过一次（= `VisualFont.body`），
        // 这里原来是重抄的一个 13 ⇒ 两处各写一个数就是"三处对齐"散掉的老路（R3 那一族）。
        empty.font = .systemFont(ofSize: VisualFont.body)
        empty.identifier = NSUserInterfaceItemIdentifier("quickPickEmptyMessage")
        empty.textColor = .secondaryLabelColor
        empty.alignment = .center
        empty.lineBreakMode = .byTruncatingTail
        empty.isHidden = true
        // R63：这句话是**淡入**的（`applyEmptyState` 走 `animator().alphaValue`），
        // 而非图层 (`layer-backing` 关) 的 `NSView` 上，`animator()` **不提交模型值**：
        // spike 四臂实测 —— 臂1/臂2（产品形状，无图层）设完之后读到 `alpha=0.000`，
        // 转 2.1 秒仍然是 0.000、连 `completionHandler` 都没跑；
        // 臂3/臂4（`wantsLayer = true` 或先落终值）立刻读到 `alpha=1.000`。
        // 也就是说"用户能不能看见这句话"被压在"动画有没有真的跑完"上面 ——
        // 淡入是装饰，看得见才是契约。开图层之后：模型值恒为终值，呈现值仍然从 0 淡上去。
        // 副作用已经查过：图层化会影响在 vibrant 容器里解析动态颜色（账本 R30 那一族），
        // 而这个面板没有材质视图（`ensurePanel` 里是普通 contentView），所以这里不受影响；
        // 真把帧拍出来之后亮暗两档的这句话都还是要过对比度判据。
        empty.wantsLayer = true

        // R407：空态 CTA。只清查询词，不关面板；文案与主窗口的「清除搜索」同一句。
        let clear = NSButton(title: "清除搜索", target: self, action: #selector(clearQueryTapped(_:)))
        clear.bezelStyle = .rounded
        clear.controlSize = .small
        clear.isHidden = true
        clear.wantsLayer = true

        // 空句与 CTA 放进一个独立容器，直接钉在 content 上：主 stack 只留 field+table。
        // 不放进 stack 的 arranged subviews —— runner 上多一项会被分配/压成按钮宽，
        // 空句 gap 33pt、长句 56pt（R408 的 CI 现读）；这里用固定 leading/trailing 与
        // top=field 底+8，跨机不再依赖 NSStackView 的分配策略。
        // 普通 NSView，不用 NSStackView：runner 上后者的 hugging 会把容器压成按钮宽，
        // 句子跟着只有 56pt、gap 33pt（R409 的 CI 现读）。这里把 empty 的四边直接钉死。
        let emptyBox = NSView()
        emptyBox.translatesAutoresizingMaskIntoConstraints = false
        emptyBox.isHidden = true
        empty.translatesAutoresizingMaskIntoConstraints = false
        clear.translatesAutoresizingMaskIntoConstraints = false
        emptyBox.addSubview(empty)
        emptyBox.addSubview(clear)
        NSLayoutConstraint.activate([
            empty.leadingAnchor.constraint(equalTo: emptyBox.leadingAnchor),
            empty.trailingAnchor.constraint(equalTo: emptyBox.trailingAnchor),
            empty.topAnchor.constraint(equalTo: emptyBox.topAnchor),
            clear.topAnchor.constraint(equalTo: empty.bottomAnchor, constant: 8),
            clear.centerXAnchor.constraint(equalTo: emptyBox.centerXAnchor),
            clear.bottomAnchor.constraint(equalTo: emptyBox.bottomAnchor),
            clear.leadingAnchor.constraint(greaterThanOrEqualTo: emptyBox.leadingAnchor),
            clear.trailingAnchor.constraint(lessThanOrEqualTo: emptyBox.trailingAnchor),
        ])

        let stack = NSStackView(views: [field, scroll])
        // R63 把这句话从"表格下面"挪到"表格上面"。**改的是我自己钉过的决定**（R7 的原文：
        // "空结果那一句放在表格下面而不是盖在上面：盖上去要自己算居中，而 stack 已经管好了间距与宽度"），
        // 所以理由要留在这里：那三条理由是**实现便利**，不是观感判断；而这一轮第一次把这个浮层拍出来
        // （`/tmp/r63_evidence/v3/probe-quickpick-empty.png`）看到的是
        // 搜索框下面 227pt 的空白，那一句在面板最底下 —— 用户刚打完字，眼睛就在列表区那一行，
        // 结果"没有匹配"这句话在 250pt 之外。挪到列表位置（`detachesHiddenViews` 让它在有候选时
        // 整条从布局里消失）之后不需要自己算居中，也不会有跳动：它出现的那一格就是刚才那列表的位置。
        // 隐藏时必须真的从布局里拿掉，否则那句话会占着一行高度把表格挤短。
        stack.detachesHiddenViews = true
        stack.orientation = .vertical
        stack.spacing = 8
        // R63 修的缺陷。原来这两行是：
        //     stack.frame = content.bounds
        //     stack.autoresizingMask = [.width, .height]
        // 而**它们都是空操作**：`NSStackView` 生下来 `translatesAutoresizingMaskIntoConstraints == false`
        // （最小对象图 spike 读数 A0：建出来就是 0），autoresizing 那条通道根本没接管；
        // 外部又一条位置约束都没有 ⇒ Auto Layout 只能按 fittingSize 给它尺寸。
        // 实测（同一条探针、同一个夹具、只换这一个文件）：
        //     修前 stack 24×49、`NSScrollView` 0×0、`NSTableView.visibleRect` 0×0（8 行，一行都画不出来）
        //     修后 stack 420×300、`NSScrollView` 396×251、`visibleRect` 396×251
        // 面板是 420×300 —— 用户按下 ⌃⌥⇧V 看到的是**左下角一小块 + 四分之三的空白**。
        // 所以尺寸的"所有权"必须写出来：贴住 contentView 四条边。
        stack.translatesAutoresizingMaskIntoConstraints = false
        // 内缩不在 `edgeInsets` 里表达（那会与"子视图贴 stack 边"再叠一层，差出 2pt），
        // 而是写成 stack 自己贴边的那四个常量 —— 一条轴只有一个地方能改它。
        stack.edgeInsets = NSEdgeInsets(top: 0, left: 0, bottom: 0, right: 0)
        content.addSubview(stack)
        content.addSubview(emptyBox)
        // R449：底部键盘操作提示。它自己占一行高度，表格让出这一行（stack 底 = 提示顶 - 4）。
        let hint = NSTextField(labelWithString: QuickPickKeyboardHint.text)
        hint.font = QuickPickKeyboardHint.font
        hint.textColor = QuickPickKeyboardHint.color
        hint.alignment = .center
        hint.lineBreakMode = .byTruncatingTail
        hint.identifier = NSUserInterfaceItemIdentifier(QuickPickKeyboardHint.identifier)
        hint.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(hint)
        NSLayoutConstraint.activate([
            hint.leadingAnchor.constraint(equalTo: content.leadingAnchor,
                                          constant: QuickPickKeyboardHint.horizontalInset),
            hint.trailingAnchor.constraint(equalTo: content.trailingAnchor,
                                           constant: -QuickPickKeyboardHint.horizontalInset),
            hint.bottomAnchor.constraint(equalTo: content.bottomAnchor,
                                         constant: -QuickPickKeyboardHint.bottomInset),
            hint.heightAnchor.constraint(equalToConstant: QuickPickKeyboardHint.height),
        ])
        NSLayoutConstraint.activate([
            emptyBox.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            emptyBox.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),
            emptyBox.topAnchor.constraint(equalTo: field.bottomAnchor, constant: 8),
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),
            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 12),
            stack.bottomAnchor.constraint(equalTo: hint.topAnchor,
                                          constant: -QuickPickKeyboardHint.topSpacing),
            // 就这四条，一条都不多写。本轮曾经给三个子视图各写"等宽 = 面板减内缩"
            // （六行）+ 两行 hugging/抗压缩，然后被变异对照逐条审：
            //   M330 撤滚动视图那两条 → 绿   M331 撤搜索框那两条 → 绿
            //   M333 撤 hugging 那一行 → 绿   M334 撤句子那两条 → 绿
            //   M336 撤搜索框抗压缩 → 绿
            // 删掉之后重拍 6 张帧，`list` / `typed` 四张**逐字节不变** ⇒ 它们确实是空转
            // （`NSStackView` 的默认对齐本来就把没有固有宽度的视图拉满、把有固有宽度的居中）。
            // 只有下面那一行**有作者**：M335 撤掉它，长查询那一档立刻红（面板 420 → 899）。
        ])
        // R63 自己改出来、又被自己判据当场抓住的一个回归：把 stack 钉到面板上之后，
        // "内容要多宽"第一次**传到了窗口** —— 一条 40 字的查询词让那句"没有匹配…"
        // 的固有宽度变成 879pt，于是面板从 420 被顶到 899
        // （实测 `QUICKPICK_LONG_QUERY 面板={{0,0},{899,300}}`）。
        // 修之前那条通道根本不存在（stack 连外部约束都没有），所以这是本轮引入的。
        // 降**抗压缩**而不是加宽度约束：那句话本来就有 `.byTruncatingTail`，
        // 只要允许它被压，它就会在面板宽度内截成省略号 —— 而"固定尺寸、呼出即输入"
        // 是这个浮层的设计前提（见类注释）。判据是
        // `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 的长查询那一档。
        empty.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)

        let backdrop = QuickPickSearchBackdrop()
        backdrop.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(backdrop, positioned: .below, relativeTo: stack)
        NSLayoutConstraint.activate([
            backdrop.leadingAnchor.constraint(equalTo: field.leadingAnchor, constant: -8),
            backdrop.trailingAnchor.constraint(equalTo: field.trailingAnchor, constant: 8),
            backdrop.topAnchor.constraint(equalTo: field.topAnchor, constant: -4),
            backdrop.bottomAnchor.constraint(equalTo: field.bottomAnchor, constant: 4),
        ])
        field.onHoverChange = { [weak backdrop] hovering in
            backdrop?.hovered = hovering
        }
        field.onFocusChange = { [weak backdrop] focused in
            backdrop?.focused = focused
        }

        // R435：搜索框有字时补一颗清除按钮（主窗口的 SearchField 早就有）。
        let clearSearch = NSButton()
        clearSearch.image = NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: nil)?
            .withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: VisualFont.row, weight: .medium))
        clearSearch.isBordered = false
        clearSearch.imagePosition = .imageOnly
        clearSearch.target = self
        clearSearch.action = #selector(clearQueryTapped(_:))
        clearSearch.contentTintColor = .secondaryLabelColor
        clearSearch.setAccessibilityLabel("清除搜索")
        clearSearch.identifier = NSUserInterfaceItemIdentifier("quickPickClearSearchButton")
        clearSearch.isHidden = true
        clearSearch.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(clearSearch)
        NSLayoutConstraint.activate([
            clearSearch.trailingAnchor.constraint(equalTo: field.trailingAnchor, constant: -4),
            clearSearch.centerYAnchor.constraint(equalTo: field.centerYAnchor),
            clearSearch.widthAnchor.constraint(equalToConstant: 18),
            clearSearch.heightAnchor.constraint(equalToConstant: 18),
        ])
        self.clearButton = clearSearch
        self.panel = panel
        self.field = field
        self.table = table
        self.emptyLabel = empty
        self.emptyAction = clear
        self.emptyBox = emptyBox
        self.searchBackdrop = backdrop
        return panel
    }

    @objc private func clearQueryTapped(_ sender: Any?) {
        field?.stringValue = ""
        queryChanged("")
        panel?.makeFirstResponder(field)
    }

    /// R435：有字才显示清除按钮。纯判定，真值表在单测里。
    static func showsClearButton(text: String) -> Bool { !text.isEmpty }

    /// 清除按钮的可见性只有这一个入口（产品路径与取证路径共用）。
    private func updateClearButton(for text: String) {
        clearButton?.isHidden = !Self.showsClearButton(text: text)
    }

    /// 把模型的下标画到表上。`selectRow(at:anchors:scrollTo:notify:)` 是 `NSOutlineView` 的方法，
    /// `NSTableView` 只有 `selectRowIndexes(_:byExtendingSelection:)` —— 这里统一走一个入口，
    /// 免得三处调用点各写一遍下标夹紧逻辑。
    private func selectCurrentRow() {
        applyEmptyState()
        guard let table else { return }
        if model.visible.isEmpty {
            table.deselectAll(nil)
            return
        }
        table.selectRowIndexes(IndexSet(integer: model.index), byExtendingSelection: false)
        table.scrollRowToVisible(model.index)
    }

    /// 把"没有候选"这句话摆出来，并淡入（R7）。
    ///
    /// 淡入用 AppKit 的 `alphaValue` 而不是直接 `isHidden` 一翻：这一句出现的位置
    /// 就是刚才还有一堆候选的地方，突然出现读起来像"界面跳了一下"。
    /// 时长与 reduce-motion 都走 `MotionCatalog`，与 SwiftUI 那一侧同一档参数。
    ///
    /// 已知取证边界：`cacheDisplay` 抓不到 AppKit 图层动画（账本 D-055），
    /// 所以这一条只有源码级 + 人工批次 15 的证据，不拿它当"产物已量"。
    private func applyEmptyState() {
        guard let emptyLabel else { return }
        let message = model.emptyMessage
        let shouldShow = message != nil
        emptyBox?.isHidden = !shouldShow
        // 空历史（没词可清）时不摆「清除搜索」：那会是一个点了没用的按钮。
        let canClear = !model.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let showAction = shouldShow && canClear
        if let message, emptyLabel.stringValue != message {
            emptyLabel.stringValue = message
        }
        let duration = MotionCatalog.duration(for: .contentFade)
        if MotionCatalog.motionShouldBeReduced {
            emptyLabel.isHidden = !shouldShow
            emptyLabel.alphaValue = shouldShow ? 1 : 0
            emptyAction?.isHidden = !showAction
            emptyAction?.alphaValue = showAction ? 1 : 0
            return
        }
        if shouldShow {
            // 先亮出来再推透明度：隐藏状态下没有图层，动画不会跑。
            if emptyLabel.isHidden {
                emptyLabel.isHidden = false
                emptyLabel.alphaValue = 0
            }
            NSAnimationContext.runAnimationGroup { context in
                context.duration = duration
                context.allowsImplicitAnimation = false
                emptyLabel.animator().alphaValue = 1
            }
        } else if !emptyLabel.isHidden {
            NSAnimationContext.runAnimationGroup({ context in
                context.duration = duration
                emptyLabel.animator().alphaValue = 0
            }, completionHandler: { [weak emptyLabel] in
                // 完成回调不在主线程；`isHidden` 是 AppKit 状态，必须回主线程改。
                DispatchQueue.main.async { emptyLabel?.isHidden = true }
            })
        }
        fadeEmptyAction(emptyAction, visible: showAction, duration: duration)
    }

    /// 空态 CTA 的显隐跟随那句话：同一档时长、同一个图层通道。
    private func fadeEmptyAction(_ view: NSView?, visible: Bool, duration: TimeInterval) {
        guard let view else { return }
        if visible {
            if view.isHidden {
                view.isHidden = false
                view.alphaValue = 0
            }
            NSAnimationContext.runAnimationGroup { context in
                context.duration = duration
                context.allowsImplicitAnimation = false
                view.animator().alphaValue = 1
            }
        } else if !view.isHidden {
            NSAnimationContext.runAnimationGroup({ context in
                context.duration = duration
                view.animator().alphaValue = 0
            }, completionHandler: { [weak view] in
                DispatchQueue.main.async { view?.isHidden = true }
            })
        }
    }

    /// 刷新候选列表。**刻意不再 `reloadData()` 一把梭**（动效审计 M1 的替代路径，报告 §12.4/§12.7）：
    /// 整表刷新等于告诉 AppKit"每一行都是新的"，于是它什么都不能动画 —— 这正是
    /// SwiftUI `List` 那条路走死之后，报告给的第二个方案：这个浮层本来就是真 `NSTableView`，
    /// 用它的原生行动画（`.effectFade`，10.7 起，MiaoYan 同款），零依赖。
    /// 输入时"候选变少 / 清空后重新匹配上"因此有了可读的"被抽走 / 补进来"，
    /// 而不是整块文字闪一下。
    private func rebuildRows() {
        let next = model.visible.map { Row(entry: $0, title: Self.rowTitle(for: $0, query: model.query)) }
        let plan = QuickPickRowDiff.plan(oldIDs: rows.map(\.entry.id), oldTitles: rows.map(\.title),
                                         newIDs: next.map(\.entry.id), newTitles: next.map(\.title))
        let previous = rows
        rows = next
        guard let table else { return }
        guard !plan.isNoop else { return }
        // 整体重排（刚复制的那条被顶到最前就是这种）原生行动画表达不了：退回整表刷新，
        // 并在日志里留一句 —— 否则"我以为它在动"会变成下一条假账。
        if plan.needsFullReload {
            NSLog("QuickPick rebuild: 行序整体重排（\(previous.count)→\(next.count)），退回整表刷新，本次无行动画")
            table.reloadData()
            return
        }
        table.beginUpdates()
        let animation = Self.rowAnimationOptions(reduceMotion: MotionCatalog.motionShouldBeReduced,
                                                 animationsEnabled: MotionCatalog.animationsEnabled)
        // R17：`NSTableView.moveRow(at:to:)` 既没有 `withAnimation:` 参数，
        // 这张表也**没有** `animationOptions` 那个属性（它是 `NSOutlineView` 的 —— 编译器当场告的）。
        // 行移动动不动，靠的是**隐式动画上下文**：
        // `allowsImplicitAnimation = false` 时行照样挪位，只是不再滑 ——
        // 这正是目录要求的"替换而不是删除"（减弱动态时不能把位置变化这件事一起抹掉）。
        // 单独一个批次：`moveRow` 的 `from` 是**旧**行号、`to` 是新行号，
        // 与增删混在同一个批次里时坐标系怎么换算没有文档保证（见 `QuickPickRowDiff` 里那条"不赌"）。
        if let move = plan.moves.first {
            NSAnimationContext.runAnimationGroup { context in
                context.allowsImplicitAnimation = !animation.isEmpty
                table.beginUpdates()
                table.moveRow(at: move.from, to: move.to)
                table.endUpdates()
            }
        }
        if !plan.removals.isEmpty { table.removeRows(at: plan.removals, withAnimation: animation) }
        if !plan.insertions.isEmpty { table.insertRows(at: plan.insertions, withAnimation: animation) }
        table.endUpdates()
        // 原地刷新排在 `endUpdates()` **之后**。
        // 理由不是"这样更好看"：批量更新里只有 insert/remove 有明确的新旧坐标系约定，
        // `reloadData(forRowIndexes:)` 没有文档保证它在批次中间按哪一套下标解释 ——
        // 而 `plan.reloads` 给的是**新**下标。表格落定之后再刷，读的就是新下标这件事本身。
        // 错一位不会崩，只会安静地刷错行（不报错、不红，只有文案是旧的），所以不赌。
        if !plan.reloads.isEmpty {
            table.reloadData(forRowIndexes: plan.reloads, columnIndexes: IndexSet(integer: 0))
        }
        // R67：行重排之后，"指针在这一格"这件事不再作数 —— 行视图会被挪去配另一行，
        // 而指针没动 ⇒ `mouseExited` 不会来 ⇒ 那层灰会留在错误的一行上。
        // 清掉，等下一次指针事件补回来（`mouseMoved` 在跟踪区里一直有）。
        // 为什么不在这里"按指针位置重算"：那要读物理鼠标此刻在哪，
        // 而帧基线拍的就是这个面板 ⇒ 测试那天手放在屏幕哪儿会写进已经钉住的帧。
        // 实测过：加了那次重算之后 `quickpick-list` / `quickpick-typed` 四张帧变了。
        table.enumerateAvailableRowViews { rowView, _ in
            (rowView as? QuickPickRowView)?.clearHover()
        }
    }

    /// 减弱动态 ⇒ 传空效果集，**不是**"跳过这次更新"。
    ///
    /// `NSTableView` 收到 `[]` 仍然照常增删行、仍然会把下面的行挪上去，只是不叠那层淡入淡出 ——
    /// 这正是目录要求的"替换而不是删除"（账本 U-20 第 3 条）。
    /// 第二个参数是截图夹具的 A/B 档：这一层动效由 AppKit 执行、不吃 SwiftUI 的 `Animation`，
    /// 所以"关掉它之后应当什么都不动"那条对照组必须由我们自己接进同一个总开关，
    /// 否则量到动也说不清是不是我们的动。
    static func rowAnimationOptions(reduceMotion: Bool, animationsEnabled: Bool) -> NSTableView.AnimationOptions {
        (reduceMotion || !animationsEnabled) ? [] : .effectFade
    }

    /// 行文案：**只有预览与命中理由**。时间不再拼进来（R430）——
    /// 它与预览共用一条可截断字符串时，长标题会把时间整段吃掉（`quickpick-list` 第 0/4 行）。
    /// 时间由右侧定宽列单独画（`rowTime`）。
    static func rowTitle(for entry: HistoryStore.Entry, query: String = "") -> String {
        let preview = entry.shortPreview
            .replacingOccurrences(of: "\n", with: " ")
            .trimmingCharacters(in: .whitespaces)
        let pinned = entry.isPinned ? "置顶 " : ""
        var pieces = ["\(pinned)\(preview.isEmpty ? "（空）" : preview)"]
        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            pieces.append("来自 \(reason)")
        }
        return pieces.joined(separator: "  ·  ")
    }

    /// R430：右侧时间列的文字。与侧栏行同一个 formatter，一行里只有一套时间语言。
    static func rowTime(for entry: HistoryStore.Entry) -> String {
        ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp)
    }

    static let timeFieldIdentifier = NSUserInterfaceItemIdentifier("quickPickTime")
    /// 标题与时间列之间的最小空隙。
    static let timeGap: CGFloat = 8
    /// 时间列右沿到行右沿的留白（与标题列左沿的 6pt 对称）。
    static let timeTrailingInset: CGFloat = 6

    /// 行首那一列的 SF Symbol 名（R65 / BACKLOG 94、97）。
    ///
    /// 为什么是一条纯函数：面板那一层的 `NSImageView` 只有 `NSTableView` 自己拿得到
    /// （行是它复用的），而"符号名写错"这件事在屏幕上**不报错、只是那一格什么都不画** ——
    /// 所以名字必须能在不启动表格的情况下被真值表判，而"画得出画不出"由 `rowSymbol` 那一格判。
    ///
    /// 名字与**侧栏** `RowLeadingVisual` 的符号分支一一对应（`doc.text` / `doc` / `doc.on.doc`）；
    /// 图片那一支侧栏走真缩略图、没有符号兜底，这里给它 `photo` —— 那个名字已经在用了
    /// （详情头的类型符号就是 `photo`），不是新造的一种语言。
    /// 浮层刻意**不放缩略图**：行高 34pt、一行只说一件事，一张 16pt 的彩色缩略图会把
    /// "我在找哪一条"变成"我在看哪张图"（判为不加，理由与读数记在账本 D-124）。
    static func rowSymbolName(for content: ClipboardEntryContent) -> String {
        switch content {
        case .text: return "doc.text"
        case .image: return "photo"
        case .file: return "doc"
        case .files: return "doc.on.doc"
        }
    }

    @objc private func commitTapped(_ sender: Any?) {
        if let entry = model.selection {
            hide()
            commit(entry)
        }
    }

    // MARK: - 表视图数据源

    func numberOfRows(in tableView: NSTableView) -> Int { rows.count }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let identifier = NSUserInterfaceItemIdentifier("quickPickCell")
        let cell = (tableView.makeView(withIdentifier: identifier, owner: self) as? QuickPickRowCell) ?? {
            let text = NSTextField(labelWithString: "")
            text.lineBreakMode = .byTruncatingTail
            // R71 / BACKLOG 99：行标签原来是字面量 13，而**同一条记录的标题**在
            // 侧栏（`HistorySidebarView:437`）、行视图（`HistoryRowViews` 四处）、
            // 搜索建议（`SearchField:28`）全都用 `VisualFont.row`(12) ⇒ 浮层是唯一那一处 13。
            // 判这条的依据不是"行高不同所以字号可以不同"（那是没读数的解释）：
            // 帧上按同一把尺量到的行距是 浮层 33–35pt（单行）vs 侧栏 38–47pt（双行），
            // 两者**根本不可比** ⇒ 决定用的是"同一个对象在同一条梯子上只能有一档"。
            text.font = .systemFont(ofSize: VisualFont.row)
            text.identifier = identifier
            // R65 / BACKLOG 94、97：行首那一列。存在的理由是**两件事一起**：
            // ① 文件行原来靠文案里那个 📄 emoji 当图标（彩色 emoji 与 SF Symbol 不是一套语言，
            //    还参与搜索匹配、白吃截断预算）；② 只有文件行有图标 ⇒ 五行里两种左轴
            //    （实测纯文本行标签 34.5pt、文件行标签 56.5pt，差 22pt）。
            //    每一行都给一枚类型符号，同时把左轴钉成一条。
            let symbol = NSImageView()
            symbol.imageScaling = .scaleProportionallyDown
            symbol.contentTintColor = .secondaryLabelColor
            // 类型符号只是图形线索：这一行的文字已经说清是文件/图片/多文件了，
            // 再让读屏念一遍符号名就是噪音（与侧栏 `ThumbnailSymbol` 的 `.accessibilityHidden` 同一条理由）。
            symbol.setAccessibilityElement(false)
            symbol.translatesAutoresizingMaskIntoConstraints = false
            // R430：时间从标题串里拆出来，改成右侧**定宽列**（同一根右沿）。
            // 以前时间与预览共用一条可截断的字符串：长标题先吃掉时间，`quickpick-list`
            // 第 0/4 行就是整行都没有时间；短标题的时间又各自停在自己文字后面，右沿是参差的。
            // 时间不再参与截断预算 ⇒ 标题再长也截标题，时间永远在右边。
            let time = NSTextField(labelWithString: "")
            time.font = .systemFont(ofSize: VisualFont.meta)
            time.textColor = .secondaryLabelColor
            time.alignment = .right
            time.lineBreakMode = .byClipping
            time.identifier = QuickPickController.timeFieldIdentifier
            time.setContentCompressionResistancePriority(.required, for: .horizontal)
            time.setContentHuggingPriority(.required, for: .horizontal)
            time.setAccessibilityLabel("时间")
            let cell = QuickPickRowCell()
            cell.addSubview(symbol)
            cell.addSubview(text)
            cell.addSubview(time)
            cell.textField = text
            cell.imageView = symbol
            cell.timeField = time
            text.translatesAutoresizingMaskIntoConstraints = false
            time.translatesAutoresizingMaskIntoConstraints = false
            text.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
            NSLayoutConstraint.activate([
                symbol.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 6),
                symbol.widthAnchor.constraint(equalToConstant: QuickPickController.symbolSide),
                symbol.heightAnchor.constraint(equalToConstant: QuickPickController.symbolSide),
                symbol.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
                text.leadingAnchor.constraint(equalTo: symbol.trailingAnchor, constant: 6),
                text.trailingAnchor.constraint(equalTo: time.leadingAnchor,
                                               constant: -QuickPickController.timeGap),
                text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
                time.trailingAnchor.constraint(equalTo: cell.trailingAnchor,
                                               constant: -QuickPickController.timeTrailingInset),
                time.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
            ])
            return cell
        }()
        let entry = rows[row].entry
        cell.textField?.stringValue = rows[row].title
        cell.timeField?.stringValue = Self.rowTime(for: entry)
        cell.imageView?.image = Self.rowSymbol(for: entry.content)
        return cell
    }

    /// 那一列的边长（16pt，与侧栏 `ThumbnailSymbol` 的 `frame(width: 16, height: 16)` 同值）。
    static let symbolSide: CGFloat = 16

    /// 把模型给的名字变成一张真图。
    ///
    /// `NSImage(systemSymbolName:)` 对**写错的名字返回 nil**，而 `NSImageView` 拿着 nil
    /// 什么都不画、也不报错 —— 所以这一格必须由判据来保证"名字能画出东西"
    /// （`UICaptureTests` 那三条浮层判据逐行断言 `image != nil`）。
    static func rowSymbol(for content: ClipboardEntryContent) -> NSImage? {
        let configuration = NSImage.SymbolConfiguration(pointSize: VisualGlyph.chipSymbol, weight: .medium)
        return NSImage(systemSymbolName: Self.rowSymbolName(for: content),
                       accessibilityDescription: nil)?
            .withSymbolConfiguration(configuration)
    }

    func tableView(_ tableView: NSTableView, shouldSelectRow row: Int) -> Bool { true }

    // MARK: - 悬停那一档（R67 / BACKLOG 95 那一族：浮层今天没有指针反馈）

    /// 这一行的悬停底色该不该画。纯函数，真值表在捕获卷（`testOverlayHoverTintIsATruthTable`）。
    ///
    /// 为什么选中时不画：选中是比悬停**更重**的一档（`VisualFill.selected` 0.16 由强调色派生，
    /// `VisualFill.hover` 0.06 只是 primary 的一层灰），而且它会留下来，悬停不会。
    /// 在同一行上再叠一层灰，只会把那颗蓝药丸压成灰蓝 —— "哪一条是我选中的"要读第二眼，
    /// 那是把反馈做成了负值。次序 hover < pressed < selected 是语义，不是巧合（`VisualTokens`）。
    static func showsHoverTint(isSelected: Bool, isHovered: Bool) -> Bool {
        isHovered && !isSelected
    }

    /// 悬停那一档用的墨：**与侧栏同一枚令牌**（`VisualFill.hover`），不是浮层自己再定一个数。
    /// R0 之前那种"同一件『鼠标在这里』说出三种音量（0.045 / 0.06 / 0.07）"的分裂，
    /// 就是靠"位点各自挑一个看着差不多的数"长出来的（守卫判据见捕获卷）。
    static let hoverFillAlpha = CGFloat(VisualFill.hover)

    /// 亮档在 `VisualFill.hover` 之上再抬这么多（R225 / 与 R219 的骨架墨同一族病）。
    ///
    /// 为什么抬：`quickpick-hover-420x300-light.png` 逐像素量到悬停带 = `(240,240,240)`
    /// 压在白底 `(255,255,255)` 上 ⇒ **对比度 1.14:1**，而仓库自己给亮档定的地板是
    /// **1.20**（R220 / `testSkeletonBarsAreVisibleAgainstTheirOwnBackground`，骨架条带那条）。
    /// 同一颗 0.06 在暗档是 `(43,43,43)` 压 `(30,30,30)` = **1.19:1**，过它那一档的地板 1.10。
    /// 也就是说"两档共用一个 alpha"这件事，在暗档刚好够用、在亮档刚好不够 ——
    /// 与 R219 的骨架屏是同一个形状的错（错的不是数值，是"一个数管两档"这个没写下来的默认）。
    ///
    /// 为什么抬到 0.09 而不是"够 1.20 就行"（0.0745 就够）：贴边的地板躲不过一次调色，
    /// 而这一档还要**与选中那颗分开** —— 亮档选中带实测 `(220,220,220)`，
    /// 0.09 ⇒ `(232)` 与它差 12 级灰；再往上抬就开始撞选中那一档（悬停不该读成选中）。
    /// 判据把这两条都算了一遍（合成色 → sRGB 相对亮度 → 对比度），不是引用这段散文。
    static let lightHoverLift = CGFloat(0.03)

    /// 悬停那一档的墨，**按色档各给一个数**。暗档 = `VisualFill.hover` 原值，一字未动。
    static func hoverFillAlpha(dark: Bool) -> CGFloat {
        dark ? hoverFillAlpha : hoverFillAlpha + lightHoverLift
    }

    /// 那一层灰左右各缩进多少。**10pt 是量出来的，不是挑的**：
    /// 暗档 `quickpick-list-420x300-dark.png` 上选中那颗药丸的强边沿在 x=42px 与 x=795px
    /// （2× 换算 = 21pt 与 397.5pt），而表格自己在面板里占 12…408pt ⇒ 药丸左右各内缩 ≈9pt。
    /// 悬停的灰如果铺满整格（0…396pt），它就和选中不是一套话：
    /// 同一格里两种宽度，看着像两个不同的东西在抢这一行。
    ///
    /// 9 → 10 是 R67 自己那一帧改的：9pt 拍出来灰带在 x=42…797px，药丸在 x=44…795px
    /// ⇒ 灰带**左右各宽 1pt**。旧的宽度判据给的是 ±2px 容差，所以 9pt 当时是绿的 ——
    /// 绿不等于对上，这一条是**看了画面**才知道的（逐行轮廓判据随后把中行读数钉成
    /// `药丸中行=44…795 / 灰带中行=44…795`，差 0px）。
    static let hoverFillInset: CGFloat = 10

    /// 搜索框的字站在**列表自己的那一列**里（BACKLOG 148 / R104 的产品改动）。
    ///
    /// 改之前实测（`quickpick-list-420x300` 亮/暗、`quickpick-typed-420x300` 暗，2×）：
    /// 同一张 420pt 面板里从上到下三条左轴是 **搜索文字 12.5pt → 药丸 22.0pt → 行内图标 35.5~37.5pt**
    /// ⇒ 占位语「搜索历史记录…」比它正下方那一列的**可见边**往左突出 9.5pt，
    /// 那一行字像贴在面板毛边上，不站在列表自己的列里。暗档打了字之后更难看：
    /// 选中那两三个字的高亮框直接压在面板边上（本轮逐张看帧看到的）。
    ///
    /// 为什么取 `hoverFillInset` 而不是再定一个数：**这一格里"列表的列"就是那颗药丸的左沿**，
    /// 而药丸的左沿 = 表格前缘 12pt + 这个 10pt。两处各写一个常数，就是"同一件事有两个地方能改它"
    /// （R3 那一族）。改完之后判据读的是**帧上药丸自己的左沿**，不是这两个常数 ——
    /// M367 那一课：拿被约束的常量推期望值，改常量等于同时改了判据。
    ///
    /// 为什么不反过来（把整列内容左移到 12.5）：那 10pt 是系统给行选中/悬停留的内缩，
    /// 想抹掉它要 `table.style = .plain`，而那是 macOS 13+ 的 API ⇒ 12 上抹不掉，
    /// 同一扇浮层会在两个系统版本上给出两条轴 —— 比现在这一条更坏。
    static let searchFieldLeadingInset: CGFloat = hoverFillInset

    /// 灰带的圆角。**这一档是被判据教出来的，不是我挑的**：
    /// 第一版直角（逐行内缩跨度 0px）、第二版 6pt（量到 8px），两版都被
    /// `testOverlayHoverFillSharesTheSelectionPillsOutline` 判红 ——
    /// 药丸的实测内缩跨度是 **11px**（`药丸首行=55…784`，中行 `44…795`），
    /// 而直角块的顶行与圆角药丸的顶行差的正好是一个半径。
    ///
    /// 为什么落在 `VisualRadius.card`(8pt)：8pt 画出来的内缩跨度实测 **11px，与药丸逐行完全相同**
    /// （`药丸首行=55…784 / 灰带首行=55…784`、`药丸中行=44…795 / 灰带中行=44…795`，亮暗两档一样）；
    /// 6pt 只有 8px（差 3px ⇒ 红）。**不为此新造一枚 7.5pt 的令牌**：
    /// 这条通道只给得到整数 pt 的分辨率，而 `card` 的语义（"装内容的表面"）本来就盖住一行记录。
    /// 换句话说：AppKit 那颗药丸自己用的就是 8pt 这一档，我们只是把自家的灰对齐到它。
    ///
    /// 为什么这里**不**用 `VisualRadius.panel`(9)（侧栏行的那一档）：
    /// 这一格的对照物是**同一张表里 AppKit 自己那颗药丸**，不是另一个窗口里的 SwiftUI 行。
    /// 用户在同一眼内比较的是"我指着的这条"与"我选中的那条"，两种曲率会读出两个东西；
    /// 而侧栏那两行本来就同心（同一层 fill 换 alpha），9 在那里是对的。
    /// 令牌梯子管的是"同一个概念不许有两种音量"，这里是两个概念（SwiftUI 行底 vs AppKit 药丸同形）。
    static let hoverFillCornerRadius: CGFloat = VisualRadius.card

    /// 每一行用自家的 row view：`NSTableRowView` 默认只画选中，而**双击提交**这个动作
    /// 今天没有任何指针反馈（`table.doubleAction` 是唯一的双击入口，没有 `action`、没有 `NSTrackingArea`）。
    /// 用户呼出浮层时鼠标停在哪里是随机的 ⇒ 他看见的是一列不能碰的文字。
    ///
    /// 这里每次调用都新建一个 row view：`NSTableView` 自己按标识缓存行视图，
    /// 而浮层一屏最多 8 行、只在打字与方向键时重排 —— 每次重排新分配几个视图的成本
    /// 远小于把复用状态管对的复杂度（复用带来的"灰条留在错误一行"见下面 `layout()`）。
    func tableView(_ tableView: NSTableView, rowViewForRow row: Int) -> NSTableRowView? {
        QuickPickRowView()
    }

    func tableViewSelectionDidChange(_ notification: Notification) {
        guard let table else { return }
        let index = table.selectedRow
        if index >= 0 { model.index = index }
    }
}

/// R430：带右侧时间列的行格。`NSTableCellView` 只认 `textField` / `imageView` 两个槽，
/// 时间那一格要复用时得有个自己的引用点。
private final class QuickPickRowCell: NSTableCellView {
    var timeField: NSTextField?
}

/// 浮层的一行，多出来的只有一件事：**悬停那一档**（R67）。
///
/// 为什么画在 row view 里而不是给 cell 加一层 `layer.backgroundColor`：
/// ① 选中那一档是 `NSTableRowView.drawBackground` 画的，我要在它**之后**补灰，
///    才谈得上"选中比悬停重"这个次序；② `drawBackground` 每次都在视图自己的
///    appearance 上下文里解析 `NSColor.labelColor`，而把动态色缓存成 `cgColor`
///    会把它钉死在解析那一刻的外观上（R30 那一族：亮暗两档其中一档是错的）。
final class QuickPickRowView: NSTableRowView {
    private var tracking: NSTrackingArea?
    private var hovered = false {
        didSet { if hovered != oldValue { refreshFill() } }
    }

    /// 那一层灰本体。插在 cell 视图**下面**，所以它永远压不住文字。
    private let fill = HoverFillView()

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        installFill()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        installFill()
    }

    private func installFill() {
        fill.insets = QuickPickController.hoverFillInset
        fill.cornerRadius = QuickPickController.hoverFillCornerRadius
        fill.frame = bounds
        fill.autoresizingMask = [.width, .height]
        fill.isHidden = true
        addSubview(fill, positioned: .below, relativeTo: nil)
    }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let tracking { removeTrackingArea(tracking) }
        let area = NSTrackingArea(rect: .zero,
                                  options: [.mouseEnteredAndExited, .mouseMoved, .activeAlways, .inVisibleRect],
                                  owner: self, userInfo: nil)
        addTrackingArea(area)
        tracking = area
    }

    override func mouseEntered(with event: NSEvent) { hovered = true }

    /// 指针在这一行里移动时重新确认一次。
    ///
    /// 为什么需要：行会因打字而重排，重排时这层灰被清掉（`clearHover`），
    /// 而指针可能一直停在这一格里没离开过 —— 没有这一条，"鼠标在这儿"会在每次打字时消失，
    /// 直到指针挪一下。有了它，下一次抖动就恢复。
    override func mouseMoved(with event: NSEvent) { hovered = true }

    override func mouseExited(with event: NSEvent) { hovered = false }

    /// 行重排之后清掉。产品里下一次指针事件（`mouseMoved` / `mouseEntered`）会把它补回来。
    ///
    /// 为什么必须有：`NSTableView` 会把 row view 挪去配另一行，而指针没动 ⇒ `mouseExited`
    /// 不会来 ⇒ 那条灰留在错误的一行上。
    /// 为什么不在 `layout()` 里"按指针位置重算"（我第一版就是这么写的）：
    /// 那条路会读 `window.mouseLocationOutsideOfEventStream`，也就是**物理鼠标此刻在哪**。
    /// 帧基线里 AppKit 夹具拍的就是产品这个面板本身（R19 的结论：搬走会塌），
    /// 于是"我这次跑测试时手放在屏幕上哪儿"会写进 `quickpick-list` 与 `quickpick-typed`
    /// 两张已经钉住的帧 —— 实测确实变了 4 张。**一把跟着物理鼠标走的尺，
    /// 拍出来的不是产品的样子，是那天桌面的样子**（R18 那一族：帧必须只跟着产品变）。
    /// 现在这一档只由**事件**驱动：离屏捕获没有事件 ⇒ 永远不会自己亮起来，
    /// 而取证通道走的是另一个入口（`rowHoveredForCapture`），两条互不污染。
    func clearHover() { hovered = false }

    /// 控制器从外面改了点亮的行号之后叫这个（`refreshFill` 是私有的）。
    func refreshFromOutside() { refreshFill() }

    override func layout() {
        super.layout()
        refreshFill()      // 选中/点亮状态与这层灰必须在每次布局后一致
    }

    /// 这一行现在算不算"被悬停"：鼠标进来的那一档，**或**取证通道点亮的那一档。
    /// 两条都汇到同一个绘制分支，所以帧上那层灰与用户看到的那层灰是同一段代码的产物
    /// （R14 那一课：`hovered` 若是视图私有状态，"悬停那一帧"在判据里存在、在产物里从未存在过）。
    /// 点亮的是**行号**而不是视图对象，因为 row view 要等表格布局完才存在 ——
    /// 见 `QuickPickController.rowHoveredForCapture` 那段注释里记的第一版失败。
    private var isHoveredForDrawing: Bool {
        if hovered { return true }
        guard let table = enclosingScrollView?.documentView as? NSTableView,
              let controller = table.delegate as? QuickPickController else { return false }
        return controller.rowHoveredForCapture == table.row(for: self)
    }

    /// 点亮/熄灭那一层灰。**不覆盖 `drawBackground`** —— 见 `QuickPickRowView` 的类注释。
    private func refreshFill() {
        fill.isHidden = !QuickPickController.showsHoverTint(isSelected: isSelected,
                                                            isHovered: isHoveredForDrawing)
    }

    override var isSelected: Bool {
        didSet { refreshFill() }
    }
}

/// "这一行正被指针指着"的那一层灰。
///
/// 为什么是一个小视图而不是 `NSTableRowView.drawBackground` 的覆盖（这一条是实测换掉的）：
/// 覆盖那一版把**选中**那一档的圆角抗锯齿也改掉了 —— 4 张已钉住的浮层帧各差 30 行、
/// 每行 2–12 个像素（眼睛逐张看过：看不出来；哈希看得出来），
/// 而把 delegate 换成一个不覆盖任何东西的 `NSTableRowView()` 时，那 122 张帧逐字节不变。
/// 也就是说红不是"换了行视图"造成的，是"接管了 `drawBackground`"造成的：
/// AppKit 一旦不能把它的私有实现塞进这个方法，选中那一档就走了另一条绘制路。
/// 选中那一档是 R19/R63 钉过的东西，不该被一次悬停顺手改掉 ⇒ 换成子视图。
///
/// 它也不做图层缓存：颜色在 `draw` 里解析，所以亮暗两档各自拿对自己的 `labelColor`
/// （R30 那一族：把动态色缓存成 `cgColor` 会把它钉死在解析那一刻的外观上）。
final class HoverFillView: NSView {
    /// 左右各缩进这么多（与选中那颗药丸同宽，见 `QuickPickController.hoverFillInset`）。
    var insets: CGFloat = 0
    /// 圆角半径（与药丸同形，见 `QuickPickController.hoverFillCornerRadius`）。
    var cornerRadius: CGFloat = 0

    override func draw(_ dirtyRect: NSRect) {
        // 色档由**这个视图自己**问（`effectiveAppearance`），不从外面传布尔：
        // 传进来就等于允许调用方（含夹具）替产品决定"这一档该多亮"（R43 那一族）。
        let dark = effectiveAppearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua
        NSColor.labelColor.withAlphaComponent(QuickPickController.hoverFillAlpha(dark: dark)).setFill()
        NSBezierPath(roundedRect: bounds.insetBy(dx: insets, dy: 0),
                     xRadius: cornerRadius,
                     yRadius: cornerRadius).fill()
    }

    /// 指针事件不许停在这一层上：跟踪区在 row view 自己身上。
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
}

/// 搜索框：把 ↑ ↓ ↩ ⎋ 交给浮层的判定，其余照常打字。
/// 为什么是子类而不是 `NSEvent` 局部监视器：局部监视器作用在整个 app 的事件流上，
/// 会在主窗口打字时也跟着吃掉方向键；命中视图自己决定才是最窄的作用域。
final class QuickPickSearchField: NSTextField {
    var forwarding: ((NSEvent) -> Bool)?
    /// R409：悬停只用来点亮搜索框的边界，不改输入行为。
    var onHoverChange: ((Bool) -> Void)?
    /// R415：焦点边界。面板一出现字段就是第一响应者，这条路要能自己报出来；
    /// 产品只在 `makeFirstResponder` 真的成功时点亮（`show()` 那边同一句话）。
    var onFocusChange: ((Bool) -> Void)?
    private var tracking: NSTrackingArea?

    override func becomeFirstResponder() -> Bool {
        let accepted = super.becomeFirstResponder()
        if accepted { onFocusChange?(true) }
        return accepted
    }

    override func resignFirstResponder() -> Bool {
        let resigned = super.resignFirstResponder()
        if resigned { onFocusChange?(false) }
        return resigned
    }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let tracking { removeTrackingArea(tracking) }
        let area = NSTrackingArea(rect: .zero,
                                  options: [.mouseEnteredAndExited, .activeAlways, .inVisibleRect],
                                  owner: self, userInfo: nil)
        addTrackingArea(area)
        tracking = area
    }

    override func mouseEntered(with event: NSEvent) { onHoverChange?(true) }
    override func mouseExited(with event: NSEvent) { onHoverChange?(false) }

    /// 文本左内缩走 cell，不走约束：这颗字段是 `NSStackView` 的 arranged subview，
    /// 它的前缘已经被 stack 以 required 优先级钉死，再加一条 leading 只会与它打架
    /// （R63 那一族的实测形态就是"面板只剩一角"）。
    override class var cellClass: AnyClass? {
        get { QuickPickSearchFieldCell.self }
        set { }
    }

    override func keyDown(with event: NSEvent) {
        if forwarding?(event) == true { return }
        super.keyDown(with: event)
    }
}

/// R409：QuickPick 搜索框的悬停边界。主窗口 `SearchField` 有底/描边这一层，
/// 浮层的主输入框却一直是一行裸文字；这里只在悬停时补边界，静置保持原样。
final class QuickPickSearchBackdrop: NSView {
    var hovered = false { didSet { if hovered != oldValue { needsDisplay = true } } }
    /// R415：面板打开后字段就是第一响应者，焦点边界与悬停共用同一档视觉。
    var focused = false { didSet { if focused != oldValue { needsDisplay = true } } }
    /// 取证键：`nil` 才读产品 hover；`true/false` 时完全替代它。
    var hoveredForCapture: Bool? = nil { didSet { if hoveredForCapture != oldValue { needsDisplay = true } } }
    /// R415：焦点态的取证键；与 hover 的键分开，夹具才能只点亮焦点。
    var focusedForCapture: Bool? = nil { didSet { if focusedForCapture != oldValue { needsDisplay = true } } }

    override func draw(_ dirtyRect: NSRect) {
        guard (focusedForCapture ?? focused) || (hoveredForCapture ?? hovered) else { return }
        let fill = NSColor.labelColor.withAlphaComponent(0.10)
        let stroke = NSColor.labelColor.withAlphaComponent(0.22)
        let path = NSBezierPath(roundedRect: bounds.insetBy(dx: 0.5, dy: 0.5),
                                xRadius: VisualRadius.card,
                                yRadius: VisualRadius.card)
        fill.setFill()
        path.fill()
        stroke.setStroke()
        path.lineWidth = 1
        path.stroke()
    }
}

/// 只干一件事：把文本矩形往右推 `QuickPickController.searchFieldLeadingInset`，
/// 让占位语与打出来的字都站在列表自己的那一列里（BACKLOG 148）。
///
/// 为什么只碰 `drawingRect` / `edit` / `select` 而不碰 `titleRect`：
/// `NSCell.drawingRect(forBounds:)` 的超类实现本身会去问 `titleRect`，
/// 两处都加一次内缩就会**被加两遍**（这一格不是推理，是写完立刻用帧上的读数验的 ——
/// 判据 `QUICKPICK_SEARCH_AXIS` 读的是药丸自己的左沿，不是这两个常数）。
final class QuickPickSearchFieldCell: NSTextFieldCell {
    private func insetted(_ rect: NSRect) -> NSRect {
        let inset = QuickPickController.searchFieldLeadingInset
        // R435：右边给清除按钮留位（按钮有字才出现，但 insets 是静态的 —— 统一留 22pt，
        // 长查询只是早一点截断，不会让左轴移动）。
        let rightInset: CGFloat = 22
        guard rect.width > inset + rightInset else { return rect }
        return NSRect(x: rect.minX + inset, y: rect.minY,
                      width: rect.width - inset - rightInset, height: rect.height)
    }

    override func drawingRect(forBounds rect: NSRect) -> NSRect {
        insetted(super.drawingRect(forBounds: rect))
    }

    override func edit(withFrame rect: NSRect, in controlView: NSView, editor textObj: NSText,
                       delegate: Any?, event: NSEvent?) {
        super.edit(withFrame: insetted(rect), in: controlView, editor: textObj,
                   delegate: delegate, event: event)
    }

    override func select(withFrame rect: NSRect, in controlView: NSView, editor textObj: NSText,
                         delegate: Any?, start selStart: Int, length selLength: Int) {
        super.select(withFrame: insetted(rect), in: controlView, editor: textObj,
                     delegate: delegate, start: selStart, length: selLength)
    }
}

extension QuickPickController: NSTextFieldDelegate {
    func controlTextDidChange(_ notification: Notification) {
        guard let field = notification.object as? NSTextField else { return }
        queryChanged(field.stringValue)
    }
}
