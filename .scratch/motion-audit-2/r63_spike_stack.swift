import AppKit

// R63 的 AppKit 真值：程序化建的 NSStackView，
// ① 它的 translatesAutoresizingMaskIntoConstraints 默认是什么；
// ② 只给 frame + autoresizingMask（不给约束）时，谁拥有它的尺寸。
// 为什么单独跑：产品里那条判据读到的 stackWidth 到底是"产品的 stack"还是
// AppKit 自己塞进树上的某个 stack，只有脱离测试宿主、用最小对象图才能定。

let app = NSApplication.shared

func newPanel() -> NSPanel {
    NSPanel(contentRect: NSRect(x: 0, y: 0, width: 420, height: 300),
            styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered, defer: false)
}

func report(_ tag: String, _ stack: NSStackView, _ content: NSView, _ scroll: NSScrollView) {
    print("\(tag) stackClass=\(type(of: stack)) translates=\(stack.translatesAutoresizingMaskIntoConstraints ? 1 : 0) "
          + "frame=\(NSStringFromRect(stack.frame)) fitting=\(NSStringFromSize(stack.fittingSize)) "
          + "mask=\(stack.autoresizingMask.rawValue) scrollFrame=\(NSStringFromRect(scroll.frame)) "
          + "contentBounds=\(NSStringFromRect(content.bounds)) stackOwnedConstraints=\(stack.constraints.count) "
          + "subviewStacks=\(content.subviews.compactMap { $0 as? NSStackView }.count)")
}

// —— A：完全照抄产品写法（frame + autoresizingMask，不显式设 translates）
let panel = newPanel()
guard let content = panel.contentView else { fatalError("no content view") }
let field = NSTextField(labelWithString: "搜索历史记录…")
let scroll = NSScrollView()
scroll.hasVerticalScroller = true
let stackA = NSStackView(views: [field, scroll])
stackA.orientation = .vertical
stackA.spacing = 8
stackA.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
stackA.frame = content.bounds
stackA.autoresizingMask = [.width, .height]
content.addSubview(stackA)
print("A0 刚建出来 translates=\(stackA.translatesAutoresizingMaskIntoConstraints ? 1 : 0)")
report("A1 addSubview 后", stackA, content, scroll)
panel.orderFrontRegardless()
RunLoop.main.run(until: Date().addingTimeInterval(0.25))
report("A2 orderFront 后", stackA, content, scroll)
content.layoutSubtreeIfNeeded()
report("A3 layoutSubtreeIfNeeded 后", stackA, content, scroll)

// —— B：显式贴边约束（候选修法）
let panel2 = newPanel()
guard let content2 = panel2.contentView else { fatalError("no content view") }
let field2 = NSTextField(labelWithString: "搜索历史记录…")
let scroll2 = NSScrollView()
scroll2.hasVerticalScroller = true
let stackB = NSStackView(views: [field2, scroll2])
stackB.orientation = .vertical
stackB.alignment = .width
stackB.spacing = 8
stackB.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
stackB.translatesAutoresizingMaskIntoConstraints = false
content2.addSubview(stackB)
NSLayoutConstraint.activate([
    stackB.leadingAnchor.constraint(equalTo: content2.leadingAnchor),
    stackB.trailingAnchor.constraint(equalTo: content2.trailingAnchor),
    stackB.topAnchor.constraint(equalTo: content2.topAnchor),
    stackB.bottomAnchor.constraint(equalTo: content2.bottomAnchor),
])
print("B0 translates=\(stackB.translatesAutoresizingMaskIntoConstraints ? 1 : 0) alignment=\(stackB.alignment.rawValue)")
panel2.orderFrontRegardless()
RunLoop.main.run(until: Date().addingTimeInterval(0.25))
content2.layoutSubtreeIfNeeded()
report("B1 约束版", stackB, content2, scroll2)
print("B2 fieldFrame=\(NSStringFromRect(field2.frame)) scrollFrame=\(NSStringFromRect(scroll2.frame))")

// —— C：不显式设 translates、只给约束（验证 NSStackView 是否本来就该被约束拥有）
let panel3 = newPanel()
guard let content3 = panel3.contentView else { fatalError("no content view") }
let stackC = NSStackView(views: [NSTextField(labelWithString: "x"), NSScrollView()])
stackC.orientation = .vertical
stackC.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
content3.addSubview(stackC)
print("C0 addSubview 前 translates=\(stackC.translatesAutoresizingMaskIntoConstraints ? 1 : 0)")
NSLayoutConstraint.activate([
    stackC.leadingAnchor.constraint(equalTo: content3.leadingAnchor),
    stackC.trailingAnchor.constraint(equalTo: content3.trailingAnchor),
    stackC.topAnchor.constraint(equalTo: content3.topAnchor),
    stackC.bottomAnchor.constraint(equalTo: content3.bottomAnchor),
])
print("C1 加约束后 translates=\(stackC.translatesAutoresizingMaskIntoConstraints ? 1 : 0)（NSStackView 会不会自己翻）")
panel3.orderFrontRegardless()
RunLoop.main.run(until: Date().addingTimeInterval(0.25))
content3.layoutSubtreeIfNeeded()
let sc3 = stackC.arrangedSubviews.compactMap { $0 as? NSScrollView }.first
print("C2 frame=\(NSStringFromRect(stackC.frame)) scroll=\(sc3.map { NSStringFromRect($0.frame) } ?? "nil")")
