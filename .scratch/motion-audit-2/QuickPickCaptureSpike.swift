// R19 spike #2（仓库外，一次性）：翻案 R18 自己写下的"根因"。
//
// R18 记的是"浮层背景是 NSVisualEffectView，离屏没有可合成层 ⇒ 拍出来全透明"。
// 但 spike #1 直接推翻了这个机制：**裸 NSVisualEffectView 离屏照样画得出 (58,58,58) 不透明**。
// 而读产品代码更干脆：`QuickPickController.ensurePanel()` 里**根本没有 NSVisualEffectView** ——
// 面板内容是 contentView + NSStackView[无边框 NSTextField(drawsBackground=false),
// NSScrollView(drawsBackground=false) > NSTableView(backgroundColor=.clear), 隐藏标签]。
// 也就是说"全透明"很可能是**这些视图本来就故意不画底**，
// 而窗口自己的底不在 contentView 的绘制范围里 —— 那是捕获方式错了，不是拍不到。
//
// 这一支要量的就一件事：给表格一次真正的布局/显示"踢"，行文字会不会出现。
// 判据用**不透明像素数**（行文字是实色），不用"变化像素占比"（均匀底上恒等于 1）。
import AppKit
import SwiftUI

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

func opaqueCount(_ view: NSView) -> (opaque: Int, total: Int, mid: String) {
    guard let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { return (-1, 0, "NO_REP") }
    view.cacheDisplay(in: view.bounds, to: rep)
    guard let base = rep.bitmapData else { return (-1, 0, "NO_BYTES") }
    let w = rep.pixelsWide, h = rep.pixelsHigh, bpr = rep.bytesPerRow
    var opaque = 0
    for y in 0..<h {
        for x in 0..<w where base[y * bpr + x * 4 + 3] > 128 { opaque += 1 }
    }
    let mid = (h / 2) * bpr + (w / 2) * 4
    return (opaque, w * h, "(\(base[mid]),\(base[mid + 1]),\(base[mid + 2]),a=\(base[mid + 3]))")
}

func report(_ tag: String, _ view: NSView) {
    let r = opaqueCount(view)
    let pct = r.total > 0 ? Double(r.opaque) / Double(r.total) * 100 : 0
    print("\(tag): opaque=\(r.opaque)/\(r.total) (\(String(format: "%.2f", pct))%) mid=\(r.mid)"
          + " tableFrame=\(NSStringFromRect(view.frame))")
}

// ---- 复刻浮层的那一棵树（照抄产品里的四个"不画底"设置） ----
let panel = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 420, height: 300),
                    styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
                    backing: .buffered, defer: false)
panel.isFloatingPanel = true
panel.level = .floating
panel.titleVisibility = .hidden
panel.titlebarAppearsTransparent = true
panel.animationBehavior = .none

final class Rows: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    func numberOfRows(in tableView: NSTableView) -> Int { 6 }
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let cell = NSTableCellView()
        let text = NSTextField(labelWithString: "记录 \(row + 1) 的内容预览")
        text.translatesAutoresizingMaskIntoConstraints = false
        cell.addSubview(text)
        NSLayoutConstraint.activate([text.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 6),
                                     text.centerYAnchor.constraint(equalTo: cell.centerYAnchor)])
        return cell
    }
}

let field = NSTextField()
field.placeholderString = "搜索历史记录…"
field.isBordered = false
field.drawsBackground = false
field.frame = NSRect(x: 0, y: 0, width: 396, height: 24)

let table = NSTableView()
table.addTableColumn(NSTableColumn(identifier: NSUserInterfaceItemIdentifier("q")))
table.headerView = nil
table.rowHeight = 34
table.backgroundColor = .clear
table.selectionHighlightStyle = .regular
let source = Rows()
table.dataSource = source
table.delegate = source

let scroll = NSScrollView()
scroll.documentView = table
scroll.hasVerticalScroller = true
scroll.drawsBackground = false
scroll.borderType = .noBorder

guard let content = panel.contentView else { fatalError("no content view") }
let stack = NSStackView(views: [field, scroll])
stack.orientation = .vertical
stack.spacing = 8
stack.edgeInsets = NSEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
stack.frame = content.bounds
stack.autoresizingMask = [.width, .height]
content.addSubview(stack)

report("1 只建好、什么都没踢", content)

table.reloadData()
report("2 reloadData 之后", content)

panel.layoutIfNeeded()
content.layoutSubtreeIfNeeded()
report("3 布局之后", content)

table.tile()
scroll.tile()
report("4 tile 之后", content)

panel.setFrame(NSRect(x: -20000, y: -20000, width: 420, height: 300), display: false)
panel.orderFrontRegardless()
let deadline = Date().addingTimeInterval(0.8)
while Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
report("5 orderFront 到屏幕外 + 转 0.8s", content)
print("   visible=\(panel.isVisible) key=\(panel.isKeyWindow) tableFrame=\(NSStringFromRect(table.frame))"
      + " rows=\(table.numberOfRows) drawnRect=\(NSStringFromRect(table.visibleRect))")

table.selectRowIndexes(IndexSet(integer: 2), byExtendingSelection: false)
table.display()
report("6 选中第 3 行并 display", content)
panel.orderOut(nil)
