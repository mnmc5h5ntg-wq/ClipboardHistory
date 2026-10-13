// R19 spike #3：浮层到底能不能被拍出来 —— 三种"踢"法各试一次。
//
// spike #2 的读数把 R18 写下的机制推翻了，但没有把结论推翻：
//   · 裸 NSVisualEffectView 离屏**画得出来**（spike #1：mid=(58,58,58,a=255)）
//     ⇒ "因为那是个材质，所以拍不到"这句话是错的，而且面板里**根本没有材质视图**；
//   · 复刻浮层那一棵树，orderFront 到屏幕外之后 `table.visibleRect` 仍是 0×0
//     ⇒ 真正的拦路的是 **NSScrollView/NSTableView 没有走完一次真实显示周期**，
//       document view 拿不到有效可见区，`cacheDisplay` 于是没有东西可画。
//
// 这一支问的是能不能绕过它：A 强制窗口 display；B 换 API（displayIgnoringOpacity）；
// C 干脆不走 NSStackView，手工给 scroll/table 一个确定 frame。
import AppKit

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

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
let source = Rows()

func makeTable() -> (NSScrollView, NSTableView) {
    let table = NSTableView()
    table.addTableColumn(NSTableColumn(identifier: NSUserInterfaceItemIdentifier("q")))
    table.headerView = nil
    table.rowHeight = 34
    table.backgroundColor = .clear
    table.selectionHighlightStyle = .regular
    table.dataSource = source
    table.delegate = source
    let scroll = NSScrollView()
    scroll.documentView = table
    scroll.hasVerticalScroller = true
    scroll.drawsBackground = false
    scroll.borderType = .noBorder
    return (scroll, table)
}

func makePanel() -> NSPanel {
    let panel = NSPanel(contentRect: NSRect(x: -20000, y: -20000, width: 420, height: 300),
                        styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
                        backing: .buffered, defer: false)
    panel.isFloatingPanel = true
    panel.level = .floating
    panel.titleVisibility = .hidden
    panel.titlebarAppearsTransparent = true
    panel.animationBehavior = .none
    return panel
}

func countOpaque(_ rep: NSBitmapImageRep) -> Int {
    guard let base = rep.bitmapData else { return -1 }
    var n = 0
    for y in 0..<rep.pixelsHigh {
        for x in 0..<rep.pixelsWide where base[y * rep.bytesPerRow + x * 4 + 3] > 128 { n += 1 }
    }
    return n
}

func measure(_ tag: String, _ view: NSView, _ table: NSTableView, extra: (String) -> Void = { _ in }) {
    guard let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else {
        print("\(tag): NO_REP"); return
    }
    view.cacheDisplay(in: view.bounds, to: rep)
    let line = "\(tag): cacheDisplay opaque=\(countOpaque(rep))"
        + " visibleRect=\(NSStringFromRect(table.visibleRect))"
    extra(line)
}

// ---- A：orderFront 之后强制窗口 display ----
let panelA = makePanel()
let (scrollA, tableA) = makeTable()
panelA.contentView?.addSubview(scrollA)
scrollA.frame = NSRect(x: 12, y: 12, width: 396, height: 276)
scrollA.autoresizingMask = [.width, .height]
tableA.reloadData()
panelA.orderFrontRegardless()
panelA.display()
RunLoop.current.run(until: Date().addingTimeInterval(0.4))
measure("A display()", scrollA, tableA) { print($0) }

// ---- B：换 API —— displayIgnoringOpacity 到自建 rep ----
if let rep = scrollA.bitmapImageRepForCachingDisplay(in: scrollA.bounds),
   let context = NSGraphicsContext(bitmapImageRep: rep) {
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    scrollA.displayIgnoringOpacity(scrollA.bounds, in: context)
    NSGraphicsContext.restoreGraphicsState()
    print("B displayIgnoringOpacity: opaque=\(countOpaque(rep))")
} else {
    print("B displayIgnoringOpacity: NO_REP_OR_CONTEXT")
}

// ---- C：确定 frame + tile + 滚回顶部，再量一次 ----
scrollA.tile()
scrollA.contentView.scroll(to: .zero)
scrollA.reflectScrolledClipView(scrollA.contentView)
tableA.frame = NSRect(x: 0, y: 0, width: 396, height: 6 * 34)
measure("C 手工 frame + tile", scrollA, tableA) { print($0) }
tableA.selectRowIndexes(IndexSet(integer: 2), byExtendingSelection: false)
scrollA.tile()
measure("C2 选中一行之后", scrollA, tableA) { print($0 + " selected=\(tableA.selectedRow)") }

// ---- D：把整棵子树塞进一个**已经上过屏**的普通窗口（对照：证明"能不能画"与材质无关） ----
let panelD = makePanel()
let (scrollD, tableD) = makeTable()
panelD.contentView?.addSubview(scrollD)
scrollD.frame = NSRect(x: 12, y: 12, width: 396, height: 276)
tableD.reloadData()
tableD.frame = NSRect(x: 0, y: 0, width: 396, height: 6 * 34)
scrollD.tile()
panelD.orderFront(nil)
RunLoop.current.run(until: Date().addingTimeInterval(0.6))
scrollD.tile()
measure("D orderFront(nil) + tile", scrollD, tableD) { print($0) }
print("D visible=\(panelD.isVisible) alpha=\(panelD.alphaValue) opaqueWindow=\(panelD.isOpaque)"
      + " windowNumber=\(panelD.windowNumber)")
