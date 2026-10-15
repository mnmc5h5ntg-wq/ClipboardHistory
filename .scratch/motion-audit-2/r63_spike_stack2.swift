import AppKit

// R63 第二问：stack 贴边之后（B 已证可行），**排列子视图**要不要额外做什么才能撑满宽度。
// B 的实测：stack 420×300 ✓、scroll 396×252 ✓，但 field 只有 92 宽、还被推到 x=318。
// 所以候选修法有两个，都要量出 field 的真实宽度才能选，不能靠"文档说 .width 会等宽"。

let app = NSApplication.shared

func makePanel() -> (NSPanel, NSView) {
    let panel = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 420, height: 300),
                        styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
                        backing: .buffered, defer: false)
    return (panel, panel.contentView!)
}

func stack(_ views: [NSView]) -> NSStackView {
    let s = NSStackView(views: views)
    s.orientation = .vertical
    s.spacing = 8
    s.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
    return s
}

func field() -> NSTextField {
    let f = NSTextField(string: "")            // 产品用的是可编辑搜索框，不是 label
    f.placeholderString = "搜索历史记录…"
    f.font = .systemFont(ofSize: 14)
    f.isBordered = false
    f.drawsBackground = false
    return f
}

func pin(_ s: NSStackView, _ c: NSView) {
    c.addSubview(s)
    NSLayoutConstraint.activate([
        s.leadingAnchor.constraint(equalTo: c.leadingAnchor),
        s.trailingAnchor.constraint(equalTo: c.trailingAnchor),
        s.topAnchor.constraint(equalTo: c.topAnchor),
        s.bottomAnchor.constraint(equalTo: c.bottomAnchor),
    ])
}

func settle(_ tag: String, _ panel: NSPanel, _ s: NSStackView, _ subviews: [NSView]) {
    panel.orderFrontRegardless()
    RunLoop.main.run(until: Date().addingTimeInterval(0.25))
    panel.contentView!.layoutSubtreeIfNeeded()
    let widths = subviews.map { Int($0.frame.width.rounded()) }
    let frames = subviews.map { NSStringFromRect($0.frame) }
    print("\(tag) stackW=\(Int(s.frame.width.rounded())) stackH=\(Int(s.frame.height.rounded())) "
          + "subWidths=\(widths) frames=\(frames)")
}

// —— B'：.width 对齐 + 把 field 的水平 hugging 压低
let (p1, c1) = makePanel()
let f1 = field(), s1n = NSScrollView(), e1 = NSTextField(labelWithString: "没有匹配的历史")
let st1 = stack([f1, s1n, e1])
st1.alignment = .width
f1.setContentHuggingPriority(.defaultLow, for: .horizontal)
pin(st1, c1)
settle("B' .width + hugging=low", p1, st1, [f1, s1n, e1])

// —— E：不设 alignment，直接给每个子视图一条"宽 = stack 宽 - 2×inset"
let (p2, c2) = makePanel()
let f2 = field(), s2n = NSScrollView(), e2 = NSTextField(labelWithString: "没有匹配的历史")
let st2 = stack([f2, s2n, e2])
pin(st2, c2)
NSLayoutConstraint.activate([
    f2.widthAnchor.constraint(equalTo: st2.widthAnchor, constant: -24),
    s2n.widthAnchor.constraint(equalTo: st2.widthAnchor, constant: -24),
    e2.widthAnchor.constraint(equalTo: st2.widthAnchor, constant: -24),
])
settle("E  显式等宽约束", p2, st2, [f2, s2n, e2])

// —— F：.leading 对齐（对照组：预期 scroll 会被压成 0 宽，用来证明"不做事不行"）
let (p3, c3) = makePanel()
let f3 = field(), s3n = NSScrollView(), e3 = NSTextField(labelWithString: "没有匹配的历史")
let st3 = stack([f3, s3n, e3])
st3.alignment = .leading
pin(st3, c3)
settle("F  .leading（对照）", p3, st3, [f3, s3n, e3])

// —— G：B' 的形状，但 scroll 里放一张 5 行的表，量 visibleRect（判"行画不画得出来"）
let (p4, c4) = makePanel()
let f4 = field()
let table = NSTableView()
let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("c"))
table.addTableColumn(column)
table.rowHeight = 34
table.headerView = nil
let scroll4 = NSScrollView()
scroll4.documentView = table
scroll4.hasVerticalScroller = true
scroll4.drawsBackground = false
scroll4.borderType = .noBorder
let e4 = NSTextField(labelWithString: "没有匹配的历史")
e4.isHidden = true
let st4 = stack([f4, scroll4, e4])
st4.detachesHiddenViews = true
st4.alignment = .width
f4.setContentHuggingPriority(.defaultLow, for: .horizontal)
pin(st4, c4)
settle("G  B'+真表", p4, st4, [f4, scroll4, table])
print("G  table.frame=\(NSStringFromRect(table.frame)) visible=\(NSStringFromRect(table.visibleRect)) "
      + "clip=\(NSStringFromRect(scroll4.contentView.frame))")
