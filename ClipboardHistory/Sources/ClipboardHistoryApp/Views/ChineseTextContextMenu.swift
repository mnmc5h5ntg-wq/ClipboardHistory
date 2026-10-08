import AppKit
import SwiftUI

enum ChineseTextContextMenu {
    static func makeReadOnlyMenu(delegate: NSMenuDelegate? = nil) -> NSMenu {
        let menu = NSMenu()
        menu.allowsContextMenuPlugIns = false
        menu.addItem(item("复制", action: #selector(NSText.copy(_:)), key: "c"))
        menu.addItem(.separator())
        menu.addItem(item("全选", action: #selector(NSText.selectAll(_:)), key: "a"))
        menu.addItem(item("查找…", action: #selector(NSResponder.performTextFinderAction(_:)), key: "f", tag: NSTextFinder.Action.showFindInterface.rawValue))
        menu.delegate = delegate
        return menu
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
        context.coordinator.attach(to: textField)
        textField.isBordered = false
        textField.isBezeled = false
        textField.drawsBackground = false
        textField.focusRingType = .none
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
        private var textField: ChineseMenuTextField?

        init(text: Binding<String>) {
            self.text = text
        }

        func attach(to textField: ChineseMenuTextField) {
            self.textField = textField
            NotificationCenter.default.addObserver(
                self,
                selector: #selector(fieldEditorBecameActive(_:)),
                name: NSText.didBeginEditingNotification,
                object: textField
            )
        }

        @objc private func fieldEditorBecameActive(_ notification: Notification) {
            guard let tf = textField else { return }
            // 每次 field editor 激活时，干掉其右键菜单
            if let editor = tf.currentEditor() as? NSTextView {
                editor.menu = nil
            }
        }

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

        func controlTextDidBeginEditing(_ notification: Notification) {
            guard let tf = notification.object as? NSTextField else { return }
            // 立即干掉 field editor 的右键菜单
            if let editor = tf.currentEditor() as? NSTextView {
                editor.menu = nil
            }
        }
    }
}

final class ChineseMenuTextField: NSTextField {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        configureSingleLineEditing()
        menu = nil
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        configureSingleLineEditing()
        menu = nil
    }

    func configureSingleLineEditing() {
        guard let textFieldCell = cell as? NSTextFieldCell else { return }
        textFieldCell.usesSingleLineMode = true
        textFieldCell.wraps = false
        textFieldCell.isScrollable = true
    }

    override func menu(for event: NSEvent) -> NSMenu? {
        nil
    }

    override func rightMouseDown(with event: NSEvent) {
        // 不调用 super，彻底吞掉右键事件
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

    override func menu(for event: NSEvent) -> NSMenu? {
        ChineseTextContextMenu.makeReadOnlyMenu(delegate: self)
    }

    override func rightMouseDown(with event: NSEvent) {
        NSMenu.popUpContextMenu(ChineseTextContextMenu.makeReadOnlyMenu(delegate: self), with: event, for: self)
    }

    func menuWillOpen(_ menu: NSMenu) {
        menu.removeServiceItems()
    }
}

private extension NSMenu {
    func removeServiceItems() {
        for item in items.reversed() {
            if item.title.localizedCaseInsensitiveCompare("Services") == .orderedSame
                || item.title == "服务" {
                removeItem(item)
            }
        }
        removeEdgeSeparators()
    }

    func removeEdgeSeparators() {
        while items.first?.isSeparatorItem == true {
            removeItem(at: 0)
        }
        while items.last?.isSeparatorItem == true {
            removeItem(at: items.count - 1)
        }
    }
}
