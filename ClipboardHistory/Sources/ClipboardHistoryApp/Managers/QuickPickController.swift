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

        guard let content = panel.contentView else {
            // 带 .titled 的面板正常一定有 contentView；这里不 force unwrap 是因为
            // 这个函数在快捷键回调链上跑，一次崩溃的表现是"按 ⌃⌥⇧V 应用直接没了"。
            // 拿不到容器就安静地不显示，比崩掉更可用（下面调用方按 isVisible 决定 toggle 方向）。
            return panel
        }
        // 空结果那一句放在表格**下面**而不是盖在上面：面板固定 420×300，
        // 盖上去要自己算居中，而 stack 已经管好了间距与宽度。
        let empty = NSTextField(labelWithString: "")
        empty.font = .systemFont(ofSize: 13)
        empty.textColor = .secondaryLabelColor
        empty.alignment = .center
        empty.lineBreakMode = .byTruncatingTail
        empty.isHidden = true

        let stack = NSStackView(views: [field, scroll, empty])
        // 隐藏时必须真的从布局里拿掉，否则那句话会占着一行高度把表格挤短。
        stack.detachesHiddenViews = true
        stack.orientation = .vertical
        stack.spacing = 8
        stack.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
        stack.frame = content.bounds
        stack.autoresizingMask = [.width, .height]
        content.addSubview(stack)

        self.panel = panel
        self.field = field
        self.table = table
        self.emptyLabel = empty
        return panel
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
        if let message, emptyLabel.stringValue != message {
            emptyLabel.stringValue = message
        }
        let duration = MotionCatalog.duration(for: .contentFade)
        if MotionCatalog.motionShouldBeReduced {
            emptyLabel.isHidden = !shouldShow
            emptyLabel.alphaValue = shouldShow ? 1 : 0
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
    }

    /// 刷新候选列表。**刻意不再 `reloadData()` 一把梭**（动效审计 M1 的替代路径，报告 §12.4/§12.7）：
    /// 整表刷新等于告诉 AppKit"每一行都是新的"，于是它什么都不能动画 —— 这正是
    /// SwiftUI `List` 那条路走死之后，报告给的第二个方案：这个浮层本来就是真 `NSTableView`，
    /// 用它的原生行动画（`.effectFade`，10.7 起，MiaoYan 同款），零依赖。
    /// 输入时"候选变少 / 清空后重新匹配上"因此有了可读的"被抽走 / 补进来"，
    /// 而不是整块文字闪一下。
    private func rebuildRows() {
        let next = model.visible.map { Row(entry: $0, title: Self.rowTitle(for: $0)) }
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
