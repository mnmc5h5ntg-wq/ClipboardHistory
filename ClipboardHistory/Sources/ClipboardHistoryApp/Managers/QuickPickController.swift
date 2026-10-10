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
        panel.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        panel.makeFirstResponder(field)
    }

    func hide() {
        panel?.orderOut(nil)
    }

    /// 输入变化：查询词进模型、刷新列表、下标夹住。
    func queryChanged(_ text: String) {
        model.setQuery(text)
        rebuildRows()
        table?.reloadData()
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

        let field = QuickPickSearchField()
        field.forwarding = { [weak self] event in
            guard let self else { return false }
            // 返回 true = 这一键被浮层吃掉了（↑↓↩⎋）；false = 交回正常文本编辑（打字、退格、输入法）。
            return self.handle(keyEvent: event) != .passThrough
        }
        field.placeholderString = "搜索历史记录…"
        field.font = .systemFont(ofSize: 14)
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

        let stack = NSStackView(views: [field, scroll])
        stack.orientation = .vertical
        stack.spacing = 8
        stack.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
        stack.frame = panel.contentView!.bounds
        stack.autoresizingMask = [.width, .height]
        panel.contentView?.addSubview(stack)

        self.panel = panel
        self.field = field
        self.table = table
        return panel
    }

    /// 把模型的下标画到表上。`selectRow(at:anchors:scrollTo:notify:)` 是 `NSOutlineView` 的方法，
    /// `NSTableView` 只有 `selectRowIndexes(_:byExtendingSelection:)` —— 这里统一走一个入口，
    /// 免得三处调用点各写一遍下标夹紧逻辑。
    private func selectCurrentRow() {
        guard let table else { return }
        if model.visible.isEmpty {
            table.deselectAll(nil)
            return
        }
        table.selectRowIndexes(IndexSet(integer: model.index), byExtendingSelection: false)
        table.scrollRowToVisible(model.index)
    }

    private func rebuildRows() {
        rows = model.visible.map { Row(entry: $0, title: Self.rowTitle(for: $0)) }
        table?.reloadData()
    }

    /// 行文案：**预览在前，元信息在后**。用户在浮层里是靠认内容选条目的，
    /// 时间和来源只是消歧用的次要信息（与侧栏同一套优先级）。
    static func rowTitle(for entry: HistoryStore.Entry) -> String {
        let preview = entry.shortPreview
            .replacingOccurrences(of: "\n", with: " ")
            .trimmingCharacters(in: .whitespaces)
        let time = ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp)
        let pinned = entry.isPinned ? "置顶 " : ""
        return "\(pinned)\(preview.isEmpty ? "（空）" : preview)  ·  \(time)"
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
        let cell = (tableView.makeView(withIdentifier: identifier, owner: self) as? NSTableCellView) ?? {
            let text = NSTextField(labelWithString: "")
            text.lineBreakMode = .byTruncatingTail
            text.font = .systemFont(ofSize: 13)
            text.identifier = identifier
            let cell = NSTableCellView()
            cell.addSubview(text)
            cell.textField = text
            text.translatesAutoresizingMaskIntoConstraints = false
            NSLayoutConstraint.activate([
                text.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 6),
                text.trailingAnchor.constraint(equalTo: cell.trailingAnchor, constant: -6),
                text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
            ])
            return cell
        }()
        cell.textField?.stringValue = rows[row].title
        return cell
    }

    func tableView(_ tableView: NSTableView, shouldSelectRow row: Int) -> Bool { true }

    func tableViewSelectionDidChange(_ notification: Notification) {
        guard let table else { return }
        let index = table.selectedRow
        if index >= 0 { model.index = index }
    }
}

/// 搜索框：把 ↑ ↓ ↩ ⎋ 交给浮层的判定，其余照常打字。
/// 为什么是子类而不是 `NSEvent` 局部监视器：局部监视器作用在整个 app 的事件流上，
/// 会在主窗口打字时也跟着吃掉方向键；命中视图自己决定才是最窄的作用域。
final class QuickPickSearchField: NSTextField {
    var forwarding: ((NSEvent) -> Bool)?

    override func keyDown(with event: NSEvent) {
        if forwarding?(event) == true { return }
        super.keyDown(with: event)
    }
}

extension QuickPickController: NSTextFieldDelegate {
    func controlTextDidChange(_ notification: Notification) {
        guard let field = notification.object as? NSTextField else { return }
        queryChanged(field.stringValue)
    }
}
