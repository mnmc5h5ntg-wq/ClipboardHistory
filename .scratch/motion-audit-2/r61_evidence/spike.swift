// R61 spike v4：把"产品里 scrollTo 无效、孤立复现里有效"这条差**逐件 bisect**。
//
// 读数来源（都在这轮）：
//   · 产品探针：远臂 `selectedRow` 2.0s 内一直 = -1，而 `GLUE_DEBUG 已请求 scrollTo`
//     确实打了 ⇒ 胶水在跑、id 也解析出来了，是 `scrollTo` 本身在**产品那棵树**上没滚动。
//   · 孤立 spike（v3，arm A）：同一条 `ScrollViewReader` + `.id` + `scrollTo`，
//     0.25s 内 `selectedRow=60`、`documentVisibleRect.origin.y=1662` ⇒ API 本身没问题。
// 所以差在树里。下面每一件单独开关一次，哪一件把它按死，修法就不该假装是 scrollTo。
//
// v1 的自己的 bug：`findTable` 在 `makeKeyAndOrderFront` 之后立刻跑，那时 SwiftUI 还没物化表格
// ⇒ 四臂全打"没有表格"。v2 的 bug：把 `var sel` 包成 Binding，SwiftUI 观察不到任何变化
// ⇒ `onChange=0` 会被误读成"onChange 不触发"。两版都留在这句话里，因为它们正是
// "探针自己造了一条死通道还当成产品的读数"这一族的两个样本。
//
// 跑法：
//   cd .scratch/motion-audit-2/r61_evidence
//   xcrun -sdk macosx swiftc -O spike.swift -o spike4 2>/dev/null && ./spike4
import AppKit
import SwiftUI

enum Feature: Hashable { case dropOverlay, focusDisabled, inVStack, readerOutside, drag, help, shape, tap }

enum Variant: CaseIterable {
    case plain, focusDisabled, dropAndOverlay, insideVStack, buttonRows, everything, readerInsideVStack, productRowParts

    var features: Set<Feature> {
        switch self {
        case .plain: return []
        case .focusDisabled: return [.focusDisabled]
        case .dropAndOverlay: return [.dropOverlay]
        case .insideVStack: return [.inVStack]
        case .buttonRows: return []
        case .everything: return [.dropOverlay, .focusDisabled, .inVStack]
        case .readerInsideVStack: return [.readerOutside]
        case .productRowParts: return [.drag, .help, .shape, .tap]
        }
    }
    var label: String {
        switch self {
        case .plain: return "A plain"
        case .focusDisabled: return "D +focusEffectDisabled"
        case .dropAndOverlay: return "E +onDrop/overlay/animation"
        case .insideVStack: return "F +VStack/header"
        case .buttonRows: return "G +Button 行"
        case .everything: return "H 全家桶"
        case .readerInsideVStack: return "I reader 在 if/else 里面（产品的形状）"
        case .productRowParts: return "J 行上有 onDrag/help/contentShape/双击手势"
        }
    }
}

final class Counter {
    var onChange = 0
    var scrollTo = 0
}


struct BisectList: View {
    @ObservedObject var model: Model
    let variant: Variant
    let counter = Counter()

    var body: some View { AnyView(root()) }

    private func root() -> AnyView {
        if variant == .readerInsideVStack {
            // 产品就是这个形状：VStack 在上，if/else 分支在下，ScrollViewReader 只包住 else 那条。
            return AnyView(VStack(spacing: 0) {
                Text("header").frame(height: 39)
                Divider()
                ScrollViewReader { proxy in tree(proxy) }
            })
        }
        return AnyView(ScrollViewReader { proxy in
            // 刻意不用 ViewBuilder 逐件叠加：那会引入 _ConditionalContent，
            // 而"中间多包一层条件"本身就可能改变 scrollTo 的可达性 —— 它正是我要 bisect 的东西，
            // 不能自己先污染。这里一律 AnyView，把类型擦除做成常数，只让"加了哪件修饰"变。
            AnyView(tree(proxy))
        })

    private func baseList(_ proxy: ScrollViewProxy) -> AnyView {
        AnyView(
            List(selection: Binding(get: { model.selection }, set: { model.selection = $0 })) {
                ForEach(0..<61, id: \.self) { i in
                    row(i).id(i)
                }
            }
            .listStyle(.sidebar)
            .onChange(of: model.selection) { _ in
                counter.onChange += 1
                proxy.scrollTo(60)
                counter.scrollTo += 1
            }
        )
    }

    /// 逐件往上加，加一件测一件。每件都由 variant 单独决定，互不牵连。
    private func tree(_ proxy: ScrollViewProxy) -> AnyView {
        var out = baseList(proxy)
        if variant.features.contains(.dropOverlay) {
            out = AnyView(out
                .onDrop(of: [.fileURL], isTargeted: .constant(false)) { _ in false }
                .overlay { Rectangle().fill(Color.accentColor.opacity(0.2)) }
                .animation(.easeInOut(duration: 0.2), value: counter.scrollTo))
        }
        if variant.features.contains(.focusDisabled), #available(macOS 14.0, *) {
            out = AnyView(out.focusEffectDisabled())
        }
        if variant.features.contains(.inVStack) {
            out = AnyView(VStack(spacing: 0) {
                Text("header").frame(height: 39)
                Divider()
                out
            })
        }
        return out
    }

    /// 行内容也做成一档：产品的 `HistoryRowButton` 是按钮，不是 Text。
    @ViewBuilder func row(_ i: Int) -> some View {
        if variant == .productRowParts {
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
        } else if variant == .buttonRows || variant == .everything {
            HStack {
                Button("row \(i)") {}
                Spacer()
                Button(action: {}) { Image(systemName: "star") }.buttonStyle(.plain)
            }
        } else {
            Text("row \(i)")
        }
    }
}

final class Model: ObservableObject {
    @Published var selection: Set<Int> = [1]
}

func findFirst<T>(_ v: NSView, _ cast: (NSView) -> T?) -> T? {
    if let hit = cast(v) { return hit }
    for s in v.subviews { if let hit = findFirst(s, cast) { return hit } }
    return nil
}

func pump(_ seconds: TimeInterval) { RunLoop.main.run(until: Date().addingTimeInterval(seconds)) }

func report(_ tag: String, _ host: NSView, _ counter: Counter) {
    let table = findFirst(host) { $0 as? NSTableView }
    let scroll = findFirst(host) { $0 as? NSScrollView }
    print("\(tag) 表格=\(table != nil) 滚动=\(scroll != nil) selectedRow=\(table?.selectedRow ?? -999) "
        + "originY=\(String(format: "%.1f", scroll?.documentVisibleRect.origin.y ?? -1)) "
        + "visibleH=\(String(format: "%.1f", scroll?.documentVisibleRect.height ?? -1)) "
        + "docH=\(String(format: "%.1f", scroll?.documentView?.frame.height ?? -1)) "
        + "onChange=\(counter.onChange) scrollTo=\(counter.scrollTo)")
}

_ = NSApplication.shared
NSApp.setActivationPolicy(.regular)
NSApp.activate(ignoringOtherApps: true)

for variant in Variant.allCases {
    let model = Model()
    let root = BisectList(model: model, variant: variant)
    let window = NSWindow(contentRect: NSRect(x: 200, y: 200, width: 320, height: 300),
                          styleMask: [.titled], backing: .buffered, defer: false)
    let host = NSHostingView(rootView: AnyView(root))
    host.frame = NSRect(origin: .zero, size: window.contentLayoutRect.size)
    window.contentView = host
    window.makeKeyAndOrderFront(nil)
    pump(0.8)
    report("\(variant.label) 初始", host, root.counter)
    model.selection = [60]
    pump(0.3)
    report("\(variant.label) +0.3s", host, root.counter)
    pump(1.2)
    report("\(variant.label) +1.5s", host, root.counter)
    window.orderOut(nil)
}
