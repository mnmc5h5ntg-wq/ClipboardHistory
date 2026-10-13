// R19 spike（仓库外，一次性）：把捕获窗口真的 orderFront 到屏幕外，材质到底能不能合成？
//
// 为什么先做这个而不是直接改测试：R18 数出了 8 个夹具的"纯黑填充带"（系统 List 的选中高亮），
// 结论是"选中态没有像素证据"。那句结论的前提是**离屏窗口没有可合成层**。
// 这个前提一直没被打过靶：如果 orderFront 之后材质就有颜色了，
// 那选中态、浮层、玻璃药丸三批结论全部可以重开。
//
// 三条臂，每条量两次（没上屏 / 上屏之后）：
//   A 裸 NSVisualEffectView（浮层的背景就是它）
//   B NSTableView 带选中行（浮层的行）
//   C SwiftUI List(selection:)（主窗口侧栏的真实形状）
// 量两个数：未被绘制比例、最长连续纯黑带（与仓库里同一把尺：≥60pt 才算填充）。
import AppKit
import SwiftUI

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

func metrics(_ view: NSView, _ tag: String) {
    let bounds = view.bounds
    guard let rep = view.bitmapImageRepForCachingDisplay(in: bounds) else {
        print("\(tag): NO_BITMAP"); return
    }
    view.cacheDisplay(in: bounds, to: rep)
    guard let base = rep.bitmapData else { print("\(tag): NO_BYTES"); return }
    let bytes = base
    let w = rep.pixelsWide, h = rep.pixelsHigh, bpr = rep.bytesPerRow
    var clear = 0, total = 0, bestRun = 0, run = 0
    let minRun = max(Int(60.0 * Double(w) / Double(max(Int(bounds.width), 1))), 1)
    for y in 0..<h {
        var longest = 0, current = 0
        for x in 0..<w {
            let o = y * bpr + x * 4
            total += 1
            if bytes[o + 3] < 8 { clear += 1 }
            if bytes[o] < 8, bytes[o + 1] < 8, bytes[o + 2] < 8, bytes[o + 3] > 240 {
                current += 1; longest = max(longest, current)
            } else { current = 0 }
        }
        if longest >= minRun { run += 1; bestRun = max(bestRun, run) } else { run = 0 }
    }
    // 中间那颗像素的颜色：材质合成成功的话它不该是纯黑、也不该是纯透明
    let mid = (h / 2) * bpr + (w / 2) * 4
    let probe = "(\(bytes[mid]),\(bytes[mid + 1]),\(bytes[mid + 2]),a=\(bytes[mid + 3]))"
    print("\(tag): transparent=\(String(format: "%.1f", Double(clear) / Double(max(total, 1)) * 100))%"
          + " blackBandPt=\(String(format: "%.0f", Double(bestRun) * Double(bounds.height) / Double(max(h, 1))))"
          + " midPixel=\(probe)")
}

func makeWindow(_ content: NSView, size: NSSize) -> NSWindow {
    let window = NSWindow(contentRect: NSRect(x: -20000, y: -20000, width: size.width, height: size.height),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = NSAppearance(named: .darkAqua)
    window.titlebarAppearsTransparent = true
    content.frame = NSRect(origin: .zero, size: size)
    window.contentView = content
    window.layoutIfNeeded()
    content.layoutSubtreeIfNeeded()
    return window
}

func spin(_ seconds: TimeInterval) {
    let deadline = Date().addingTimeInterval(seconds)
    while Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
}

// ---- A：裸材质 ----
let effect = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: 320, height: 200))
effect.material = .sidebar
effect.blendingMode = .behindWindow
effect.state = .active
let label = NSTextField(labelWithString: "材质上的字")
label.frame = NSRect(x: 20, y: 90, width: 200, height: 20)
effect.addSubview(label)
let windowA = makeWindow(effect, size: NSSize(width: 320, height: 200))
metrics(effect, "A 未上屏")
windowA.orderFrontRegardless()
spin(0.6)
metrics(effect, "A 上屏后")
print("A visibleOnScreen=\(windowA.isVisible) key=\(windowA.isKeyWindow) screen=\(String(describing: windowA.screen?.frame))")

// ---- B：NSTableView 带选中行 ----
final class RowView: NSTableCellView {
    init(_ text: String) {
        super.init(frame: .zero)
        let field = NSTextField(labelWithString: text)
        field.translatesAutoresizingMaskIntoConstraints = false
        addSubview(field)
        NSLayoutConstraint.activate([field.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
                                     field.centerYAnchor.constraint(equalTo: centerYAnchor)])
    }
    required init?(coder: NSCoder) { fatalError() }
}

final class DataSource: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    func numberOfRows(in tableView: NSTableView) -> Int { 5 }
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        RowView("记录 \(row + 1)")
    }
}

let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: 320, height: 220))
let table = NSTableView()
table.addTableColumn(NSTableColumn(identifier: NSUserInterfaceItemIdentifier("c")))
table.headerView = nil
let source = DataSource()
table.dataSource = source
table.delegate = source
scroll.documentView = table
let windowB = makeWindow(scroll, size: NSSize(width: 320, height: 220))
table.selectRowIndexes(IndexSet(integer: 2), byExtendingSelection: false)
windowB.makeKeyAndOrderFront(nil)
spin(0.6)
metrics(table, "B 选中行(上屏后)")

// ---- C：SwiftUI List(selection:)，主窗口侧栏的真实形状 ----
struct SidebarSpike: View {
    @State private var selection: String? = "r3"
    var body: some View {
        List(selection: $selection) {
            ForEach(1...5, id: \.self) { index in
                Text("记录 \(index)").tag("r\(index)")
            }
        }
        .frame(width: 300, height: 220)
    }
}

let host = NSHostingView(rootView: SidebarSpike().environment(\.colorScheme, .dark))
let windowC = makeWindow(host, size: NSSize(width: 300, height: 220))
metrics(host, "C 未上屏")
windowC.makeKeyAndOrderFront(nil)
app.activate(ignoringOtherApps: true)
spin(0.8)
metrics(host, "C 上屏+key 后")
print("C key=\(windowC.isKeyWindow) main=\(windowC.isMainWindow) active=\(NSApp.isActive)")
windowC.orderOut(nil)
