// R61 spike v6：只剩四臂，专门问"产品的哪一处形状让 scrollTo 失效"。
//
// 已知（同一轮的读数，都有 log）：
//   · 孤立 spike：scrollTo **有效** —— selectedRow 1→60、originY 0→1662。而且六臂全绿：
//     加 focusEffectDisabled / 加 onDrop+overlay+animation / VStack 在 reader 内 / Button 行 / 全家桶，
//     没有一件能把它按死。
//   · 产品树：scrollTo **无效** —— 胶水确实跑了（GLUE_DEBUG 两条都打），id 也解析到了，
//     表格一动不动；而 AppKit `scrollRowToVisible` 一动就动（originY 0→2191）。
//   · 只滚不重设选中：选中行仍是 -1 ⇒ "揭示那一行"和"让选中重新落地"是两件事，不是一件。
// 剩下没测的两条正是产品独有的形状：
//   I：`ScrollViewReader` 在 if/else 分支**里面**（产品：VStack { 搜索/筛选; header; if 空 {…} else { historyList } }）
//   J：行内容带 onDrag / help / contentShape / 双击手势（产品的 HistoryRowButton）
// 为什么值得再花一次 spike：I 的红绿决定修法是"把 reader 挪到分支外面"（纯 SwiftUI、一处）
// 还是"给产品加 AppKit 桥"（要走视图树、还要处理选中重落地）。不许靠猜。
//
// 跑法：xcrun -sdk macosx swiftc -O spike6.swift -o spike6 2>/dev/null && ./spike6
import AppKit
import SwiftUI

enum Shape {
    case readerOutside      // 已证明有效的那条：reader 在最外层，行是 Text
    case readerInBranch     // 产品形状：VStack 在外，reader 只在 else 分支里
    case productRows        // reader 在最外，行换成产品那件件
    case both               // I + J 一起 = 产品的完整形状

    var label: String {
        switch self {
        case .readerOutside: return "A reader 在外"
        case .readerInBranch: return "I reader 在 if/else 里"
        case .productRows: return "J 产品形状的行"
        case .both: return "K I+J 一起"
        }
    }
    var readerInsideBranch: Bool { self == .readerInBranch || self == .both }
    var productRow: Bool { self == .productRows || self == .both }
}

final class Model: ObservableObject {
    @Published var selection: Set<Int> = [1]
}

final class Counts { var onChange = 0; var scrollTo = 0 }
let counts = Counts()

struct RootView: View {
    @ObservedObject var model: Model
    let shape: Shape

    var body: some View {
        if shape.readerInsideBranch {
            AnyView(VStack(spacing: 0) {
                Text("header").frame(height: 39)
                Divider()
                if model.selection.contains(-1) {
                    Text("empty")
                } else {
                    ScrollViewReader { proxy in AnyView(list(proxy)) }
                }
            })
        } else {
            AnyView(ScrollViewReader { proxy in AnyView(list(proxy)) })
        }
    }

    func list(_ proxy: ScrollViewProxy) -> some View {
        List(selection: Binding(get: { model.selection }, set: { model.selection = $0 })) {
            ForEach(0..<61, id: \.self) { i in
                row(i).id(i)
            }
        }
        .listStyle(.sidebar)
        .onChange(of: model.selection) { _ in
            counts.onChange += 1
            proxy.scrollTo(60)
            counts.scrollTo += 1
        }
    }

    @ViewBuilder func row(_ i: Int) -> some View {
        if shape.productRow {
            HStack(spacing: 6) {
                Button("row \(i)") {}
                Spacer()
                Image(systemName: "star")
            }
            .padding(.vertical, 6)
            .contentShape(Rectangle())
            .simultaneousGesture(TapGesture(count: 2).onEnded {})
            .onDrag { NSItemProvider(object: "x" as NSString) }
            .help("拖动这一行可导出到别的应用")
        } else {
            Text("row \(i)")
        }
    }
}

func findFirst<T>(_ v: NSView, _ cast: (NSView) -> T?) -> T? {
    if let hit = cast(v) { return hit }
    for s in v.subviews { if let hit = findFirst(s, cast) { return hit } }
    return nil
}

func pump(_ seconds: TimeInterval) { RunLoop.main.run(until: Date().addingTimeInterval(seconds)) }

func report(_ tag: String, _ host: NSView) {
    let table = findFirst(host) { $0 as? NSTableView }
    let scroll = findFirst(host) { $0 as? NSScrollView }
    print("\(tag) 表格=\(table != nil) 滚动=\(scroll != nil) selectedRow=\(table?.selectedRow ?? -999) "
        + "originY=\(String(format: "%.1f", scroll?.documentVisibleRect.origin.y ?? -1)) "
        + "onChange=\(counts.onChange) scrollTo=\(counts.scrollTo)")
}

_ = NSApplication.shared
NSApp.setActivationPolicy(.regular)
NSApp.activate(ignoringOtherApps: true)

for shape in [Shape.readerOutside, .readerInBranch, .productRows, .both] {
    counts.onChange = 0
    counts.scrollTo = 0
    let model = Model()
    let window = NSWindow(contentRect: NSRect(x: 200, y: 200, width: 320, height: 300),
                          styleMask: [.titled], backing: .buffered, defer: false)
    let host = NSHostingView(rootView: AnyView(RootView(model: model, shape: shape)))
    host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
    window.contentView = host
    window.makeKeyAndOrderFront(nil)
    pump(0.8)
    report("\(shape.label) 初始", host)
    model.selection = [60]
    pump(0.3)
    report("\(shape.label) +0.3s", host)
    pump(1.2)
    report("\(shape.label) +1.5s", host)
    // 同一棵树上的 AppKit 地板：证明"滚得动"这件事在这台机器上成立，
    // 上面那两行红就是 SwiftUI 那一层没转达，而不是夹具或机器的限制。
    if let table = findFirst(host, { $0 as? NSTableView }) {
        table.scrollRowToVisible(60)
        pump(0.3)
        report("\(shape.label) AppKit 直调", host)
    }
    window.orderOut(nil)
}
