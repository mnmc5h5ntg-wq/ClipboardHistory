// R29d spike（仓库外，一次性证据，不进判据）
//
// 要判的事：暗色帧里"设置侧栏未选中行的标签"是 (0,0,0) 落在 (24,24,24) 的底上 —— 黑字黑底。
// 而**同一张帧**的内容区标题是 (221,221,221)（正确）。
// `UICaptureHarness.render` 的注释里早就写着这条症状：
//   "只注入 colorScheme 会拍出'深色底 + 黑色列表文字'的假不可读帧"
// 并给出解药：改 `NSApp.appearance`。解药在仓库里已经装了，症状却还在 ⇒
// **要么解药没覆盖这棵子树，要么还有第二个通道**。这一支 spike 只判一件事：
// 哪一种踢法能让侧栏文字在暗色里落到**亮侧**。
//
// 四条臂，同一棵树、同一个尺寸、同一把尺：
//   A = 仓库现在的配方（NSApp.appearance + window.appearance + colorScheme + cacheDisplay）
//   B = A + 把 cacheDisplay 包进 `performAsCurrentDrawingAppearance`
//       （`fillUnderAmbient` 那条判据已经在用这个 API，所以工具链支持）
//   C = A + `orderFrontRegardless` + 跑 0.2s runloop 再 cacheDisplay（R19 的"踢"）
//   D = A 但外观设成 aqua（亮色对照臂：证明这棵树本身能画对，只是方向问题）
//
// 编译：xcrun swiftc sidebar_appearance_r29d.swift -o /tmp/r29d && /tmp/r29d
import AppKit
import SwiftUI

struct SideRow: Identifiable, Hashable {
    let id: Int
    let title: String
    let symbol: String
}

let sideRows = [
    SideRow(id: 0, title: "快捷键", symbol: "command"),
    SideRow(id: 1, title: "通用", symbol: "gearshape"),
    SideRow(id: 2, title: "隐私", symbol: "hand.raised"),
    SideRow(id: 3, title: "推荐", symbol: "wand.and.stars"),
    SideRow(id: 4, title: "数据", symbol: "folder"),
    SideRow(id: 5, title: "统计", symbol: "chart.bar"),
]

/// 复刻设置窗口的**形状**：左边 `List(selection:)` 侧栏（AppKit 承载），
/// 右边普通 SwiftUI 文字。不是复刻产品代码 —— 产品代码在判据里拍，这里只判通道。
struct Pane: View {
    @State private var selection: Int? = 0

    var body: some View {
        HStack(spacing: 0) {
            List(sideRows, id: \.id, selection: $selection) { row in
                Label(row.title, systemImage: row.symbol).tag(row.id)
            }
            .frame(width: 200)
            VStack(alignment: .leading, spacing: 8) {
                Text("快捷键").font(.title3)
                Text("关闭或隐藏主窗口后，可使用此快捷键重新打开。")
                    .font(.caption).foregroundStyle(.secondary)
                Text("在任意应用里呼出浮层，打字筛选后回车直接粘回原应用。")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .padding(20)
            Spacer(minLength: 0)
        }
        .frame(width: 640, height: 440)
    }
}

func lin(_ c: Double) -> Double { c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4) }

func lumaOf(_ r: Int, _ g: Int, _ b: Int) -> Double {
    0.2126 * lin(Double(r) / 255) + 0.7152 * lin(Double(g) / 255) + 0.0722 * lin(Double(b) / 255)
}

/// 一块区域里"相对最众数背景"的墨：分亮侧 / 暗侧，外加最亮最暗的实际 RGB。
func measure(_ rep: NSBitmapImageRep, _ title: String, x: Int, y: Int, w: Int, h: Int) {
    var hist = [Int](repeating: 0, count: 256)
    for sy in stride(from: y, to: y + h, by: 2) {
        for sx in stride(from: x, to: x + w, by: 2) {
            guard let c = rep.colorAt(x: sx, y: sy) else { continue }
            hist[Int(c.redComponent * 255)] += 1
        }
    }
    let modal = hist.firstIndex(of: hist.max() ?? 0) ?? 0
    var brighter = 0, darker = 0
    var lightest = modal, darkest = modal
    for sy in y..<(y + h) {
        for sx in x..<(x + w) {
            guard let c = rep.colorAt(x: sx, y: sy) else { continue }
            let r = Int(c.redComponent * 255), g = Int(c.greenComponent * 255), b = Int(c.blueComponent * 255)
            let d = Double(max(abs(r - modal), max(abs(g - modal), abs(b - modal))))
            if d <= 24 { continue }
            if lumaOf(r, g, b) > lumaOf(modal, modal, modal) {
                brighter += 1
                lightest = max(lightest, max(r, max(g, b)))
            } else {
                darker += 1
                darkest = min(darkest, min(r, min(g, b)))
            }
        }
    }
    print(String(format: "  %-10@ bg=%3d  亮侧=%6d 暗侧=%6d  最亮≈%3d 最暗≈%3d  ⇒ %@",
                 title as NSString, modal, brighter, darker, lightest, darkest,
                 brighter + darker == 0 ? "没有墨" : (brighter > darker ? "墨在亮侧" : "墨在暗侧")))
}

func shoot(_ arm: String, appearanceName: NSAppearance.Name, drawingScope: Bool, orderFront: Bool) {
    let appearance = NSAppearance(named: appearanceName)!
    let previousApp = NSApp.appearance
    NSApp.appearance = appearance
    defer { NSApp.appearance = previousApp }

    let root = Pane().environment(\.colorScheme, appearanceName == .darkAqua ? .dark : .light)
    let hosting = NSHostingView(rootView: root)
    if #available(macOS 13.0, *) { hosting.sizingOptions = [] }
    let size = NSSize(width: 640, height: 440)
    hosting.frame = NSRect(origin: .zero, size: size)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    window.titlebarAppearsTransparent = true
    window.contentView = hosting
    if orderFront {
        window.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
    }
    window.layoutIfNeeded()
    hosting.layoutSubtreeIfNeeded()
    guard let rep = hosting.bitmapImageRepForCachingDisplay(in: hosting.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    if drawingScope {
        appearance.performAsCurrentDrawingAppearance { hosting.cacheDisplay(in: hosting.bounds, to: rep) }
    } else {
        hosting.cacheDisplay(in: hosting.bounds, to: rep)
    }
    let scale = Int(Double(rep.pixelsWide) / 640.0)
    print("\(arm)  scale=\(scale)x  visible=\(window.occlusionState.contains(.visible))")
    // 侧栏未选中行的标签列（第一行是选中的，量第 2–4 行那一段）
    measure(rep, "侧栏文字", x: 42 * scale, y: 100 * scale, w: 120 * scale, h: 120 * scale)
    measure(rep, "侧栏图标", x: 12 * scale, y: 100 * scale, w: 28 * scale, h: 120 * scale)
    measure(rep, "内容标题", x: 225 * scale, y: 25 * scale, w: 160 * scale, h: 24 * scale)
    window.orderOut(nil)
}

_ = NSApplication.shared
shoot("A 仓库现配方 ", appearanceName: .darkAqua, drawingScope: false, orderFront: false)
shoot("B +绘制外观域", appearanceName: .darkAqua, drawingScope: true, orderFront: false)
shoot("C +orderFront", appearanceName: .darkAqua, drawingScope: false, orderFront: true)
shoot("D 亮色对照臂", appearanceName: .aqua, drawingScope: false, orderFront: false)

// MARK: - 第二组臂：产品里那棵树的**形状**

/// 复刻 `CompatibleSplitView`：侧栏与详情各自装进一个**嵌套的 `NSHostingView`**，
/// 再塞进 `NSSplitView`。A–D 用的是纯 SwiftUI 的 `HStack`，环境能一路传下去；
/// 嵌套 hosting view 是**另一棵环境的根** —— 外面临时注入的 `colorScheme` 进不来。
struct SplitReplica<Sidebar: View, Detail: View>: NSViewRepresentable {
    @ViewBuilder let sidebar: () -> Sidebar
    @ViewBuilder let detail: () -> Detail
    /// 这一条是本轮要判的**候选解药**：给嵌套 hosting view 显式设外观。
    let pinAppearance: NSAppearance?

    func makeNSView(context: Context) -> NSSplitView {
        let split = NSSplitView()
        split.isVertical = true
        split.dividerStyle = .thin
        let left = NSHostingView(rootView: sidebar())
        left.translatesAutoresizingMaskIntoConstraints = false
        left.widthAnchor.constraint(equalToConstant: 200).isActive = true
        let right = NSHostingView(rootView: detail())
        right.translatesAutoresizingMaskIntoConstraints = false
        if let pinAppearance { left.appearance = pinAppearance; right.appearance = pinAppearance }
        split.addArrangedSubview(left)
        split.addArrangedSubview(right)
        return split
    }

    func updateNSView(_ split: NSSplitView, context: Context) {
        if let left = split.arrangedSubviews.first as? NSHostingView<Sidebar> { left.rootView = sidebar() }
        if let right = split.arrangedSubviews.last as? NSHostingView<Detail> { right.rootView = detail() }
    }
}

struct SidebarList: View {
    @State private var selection: Int? = 0
    var body: some View {
        List(sideRows, id: \.id, selection: $selection) { row in
            Label(row.title, systemImage: row.symbol).tag(row.id)
        }
    }
}

struct DetailPane: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("快捷键").font(.title3)
            Text("关闭或隐藏主窗口后，可使用此快捷键重新打开。")
                .font(.caption).foregroundStyle(.secondary)
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}

/// E/F/G：同一棵树，三种"外观从哪儿来"。
/// `flipAfterBuild=true` 模拟**运行中切深色**（自动深色模式在日落时干的就是这件事）。
func shootSplit(_ arm: String, startWith: NSAppearance.Name, flipTo: NSAppearance.Name?,
                pin: Bool, measureAgainst: NSAppearance.Name) {
    let start = NSAppearance(named: startWith)!
    let previousApp = NSApp.appearance
    NSApp.appearance = start
    defer { NSApp.appearance = previousApp }

    let pinAppearance = pin ? NSAppearance(named: measureAgainst) : nil
    let root = SplitReplica(sidebar: { SidebarList() }, detail: { DetailPane() }, pinAppearance: pinAppearance)
        .environment(\.colorScheme, measureAgainst == .darkAqua ? .dark : .light)
    let hosting = NSHostingView(rootView: root)
    if #available(macOS 13.0, *) { hosting.sizingOptions = [] }
    let size = NSSize(width: 640, height: 440)
    hosting.frame = NSRect(origin: .zero, size: size)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = start
    window.contentView = hosting
    window.layoutIfNeeded()
    hosting.layoutSubtreeIfNeeded()

    if let flipTo {
        let target = NSAppearance(named: flipTo)!
        NSApp.appearance = target
        window.appearance = target
        // 不重建 hosting view：真实场景里用户只是切了个外观，视图树原封不动。
        RunLoop.main.run(until: Date().addingTimeInterval(0.1))
        window.layoutIfNeeded()
    }

    guard let rep = hosting.bitmapImageRepForCachingDisplay(in: hosting.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    hosting.cacheDisplay(in: hosting.bounds, to: rep)
    let scale = Int(Double(rep.pixelsWide) / 640.0)
    print("\(arm)  建窗=\(startWith == .darkAqua ? "dark" : "light")"
          + " 绘制时=\(flipTo.map { $0 == .darkAqua ? "dark" : "light" } ?? "不变")"
          + " 钉外观=\(pin)")
    measure(rep, "侧栏文字", x: 42 * scale, y: 100 * scale, w: 120 * scale, h: 120 * scale)
    measure(rep, "侧栏图标", x: 12 * scale, y: 100 * scale, w: 28 * scale, h: 120 * scale)
    measure(rep, "内容标题", x: 225 * scale, y: 25 * scale, w: 160 * scale, h: 24 * scale)
    window.orderOut(nil)
}

/// 侧栏行的两种写法：产品现在用的**显式 `.primary`**，和不写颜色的默认写法。
struct RowList: View {
    let explicit: Bool
    @State private var selection: Int? = 0

    var body: some View {
        List(sideRows, id: \.id, selection: $selection) { row in
            Label(row.title, systemImage: row.symbol)
                .tag(row.id)
                .modifier(MaybePrimary(explicit: explicit))
        }
    }
}

private struct MaybePrimary: ViewModifier {
    let explicit: Bool
    func body(content: Content) -> some View {
        if explicit {
            content.foregroundStyle(AnyShapeStyle(.primary))
        } else {
            content
        }
    }
}

/// 2×2 判定矩阵：{默认上色, 显式 `.primary`} × {直接画, 包在绘制外观域里画}。
/// 产品侧栏用的是**显式 `.primary`**（`SettingsSidebarRow` 里那行三元表达式），
/// 而 A–G 的复刻体用的是默认上色 —— 这就是为什么 A–G 全都画对了。
func shootMatrix(_ arm: String, explicit: Bool, drawingScope: Bool) {
    let appearance = NSAppearance(named: .darkAqua)!
    let previousApp = NSApp.appearance
    NSApp.appearance = appearance
    defer { NSApp.appearance = previousApp }

    let root = RowList(explicit: explicit).environment(\.colorScheme, .dark)
    let hosting = NSHostingView(rootView: root)
    if #available(macOS 13.0, *) { hosting.sizingOptions = [] }
    let size = NSSize(width: 300, height: 300)
    hosting.frame = NSRect(origin: .zero, size: size)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    window.contentView = hosting
    window.layoutIfNeeded()
    hosting.layoutSubtreeIfNeeded()
    guard let rep = hosting.bitmapImageRepForCachingDisplay(in: hosting.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    if drawingScope {
        appearance.performAsCurrentDrawingAppearance { hosting.cacheDisplay(in: hosting.bounds, to: rep) }
    } else {
        hosting.cacheDisplay(in: hosting.bounds, to: rep)
    }
    let scale = max(1, Int(Double(rep.pixelsWide) / 300.0))
    print("\(arm)")
    measure(rep, "文字列", x: 42 * scale, y: 95 * scale, w: 150 * scale, h: 150 * scale)
    measure(rep, "图标列", x: 12 * scale, y: 95 * scale, w: 28 * scale, h: 150 * scale)
    window.orderOut(nil)
}

shootMatrix("H 默认上色   / 直接画      ", explicit: false, drawingScope: false)
shootMatrix("I 显式 .primary / 直接画     ", explicit: true, drawingScope: false)
shootMatrix("J 默认上色   / 绘制外观域    ", explicit: false, drawingScope: true)
shootMatrix("K 显式 .primary / 绘制外观域 ", explicit: true, drawingScope: true)

/// L：产品在这台机器上走的其实是 `NavigationSplitView`（`SettingsView.swift:221`），
/// `CompatibleSplitView` 只是 macOS 12 的那条腿。侧栏列由 AppKit 的 source list 承载 ——
/// 这是 A–K 全都没碰过的一条通道。
@available(macOS 13.0, *)
struct NavSplitReplica: View {
    @State private var selection: Int? = 0
    var body: some View {
        NavigationSplitView {
            List(sideRows, id: \.id, selection: $selection) { row in
                Label(row.title, systemImage: row.symbol)
                    .foregroundStyle(AnyShapeStyle(.primary))
                    .symbolRenderingMode(.hierarchical)
                    .tag(row.id)
            }
            .navigationSplitViewColumnWidth(min: 148, ideal: 148)
        } detail: {
            VStack(alignment: .leading, spacing: 8) {
                Text("快捷键").font(.title3)
                Text("关闭或隐藏主窗口后，可使用此快捷键重新打开。")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .padding(20)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }
}

func shootNav(_ arm: String, appearanceName: NSAppearance.Name) {
    let appearance = NSAppearance(named: appearanceName)!
    let previousApp = NSApp.appearance
    NSApp.appearance = appearance
    defer { NSApp.appearance = previousApp }
    let root = Group {
        if #available(macOS 13.0, *) {
            NavSplitReplica().environment(\.colorScheme, appearanceName == .darkAqua ? .dark : .light)
        }
    }
    let hosting = NSHostingView(rootView: root)
    if #available(macOS 13.0, *) { hosting.sizingOptions = [] }
    let size = NSSize(width: 640, height: 440)
    hosting.frame = NSRect(origin: .zero, size: size)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    window.titlebarAppearsTransparent = true
    window.contentView = hosting
    window.layoutIfNeeded()
    hosting.layoutSubtreeIfNeeded()
    guard let rep = hosting.bitmapImageRepForCachingDisplay(in: hosting.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    hosting.cacheDisplay(in: hosting.bounds, to: rep)
    let scale = max(1, Int(Double(rep.pixelsWide) / 640.0))
    print(arm)
    measure(rep, "侧栏文字", x: 42 * scale, y: 100 * scale, w: 100 * scale, h: 120 * scale)
    measure(rep, "侧栏图标", x: 10 * scale, y: 100 * scale, w: 30 * scale, h: 120 * scale)
    window.orderOut(nil)
}

shootNav("L NavigationSplitView 暗色", appearanceName: .darkAqua)
shootNav("M 同上，亮色对照臂        ", appearanceName: .aqua)

/// N：产品侧栏**不是 `List`** —— `SettingsSidebarView` 是一列 `Button { Label(...) }`
/// （`SettingsView.swift:722`）。A–M 全都没试过这一条通道。
struct ButtonRows: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(sideRows) { row in
                Button(action: {}) {
                    Label(row.title, systemImage: row.symbol)
                        .foregroundStyle(row.id == 0 ? AnyShapeStyle(Color.accentColor) : AnyShapeStyle(.primary))
                        .symbolRenderingMode(.hierarchical)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 8)
                }
                .buttonStyle(.plain)
            }
            Spacer()
        }
        .padding(.top, 8)
        .frame(width: 148, height: 300, alignment: .topLeading)
    }
}

func shootButtons(_ arm: String, appearanceName: NSAppearance.Name) {
    let appearance = NSAppearance(named: appearanceName)!
    let previousApp = NSApp.appearance
    NSApp.appearance = appearance
    defer { NSApp.appearance = previousApp }
    let root = ButtonRows().environment(\.colorScheme, appearanceName == .darkAqua ? .dark : .light)
    let hosting = NSHostingView(rootView: root)
    if #available(macOS 13.0, *) { hosting.sizingOptions = [] }
    let size = NSSize(width: 148, height: 300)
    hosting.frame = NSRect(origin: .zero, size: size)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    window.contentView = hosting
    window.layoutIfNeeded()
    hosting.layoutSubtreeIfNeeded()
    guard let rep = hosting.bitmapImageRepForCachingDisplay(in: hosting.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    hosting.cacheDisplay(in: hosting.bounds, to: rep)
    let scale = max(1, Int(Double(rep.pixelsWide) / 148.0))
    print(arm)
    measure(rep, "文字列", x: 40 * scale, y: 95 * scale, w: 100 * scale, h: 150 * scale)
    measure(rep, "图标列", x: 8 * scale, y: 95 * scale, w: 30 * scale, h: 150 * scale)
    window.orderOut(nil)
}

shootButtons("N Button 侧栏 暗色", appearanceName: .darkAqua)
shootButtons("N2 Button 侧栏 亮色", appearanceName: .aqua)

/// O：**A–N 漏掉的那一格** —— 产品的侧栏是"嵌套 `NSHostingView` 里装一列 `Button{Label}`"。
/// E 试过嵌套容器（里面装的是 `List`），N 试过 Button（装在外层 hosting view 里），两半从没合起来。
/// P = O + 在 `makeNSView` 里给嵌套视图钉上 `effectiveAppearance`，并在 `updateNSView` 里跟着翻。
/// 直接搭出那一棵树（不走 NSViewRepresentable，避免把 SwiftUI 的环境带进来当混淆项）。
func shootNestedButtons(_ arm: String, pinNested: Bool) {
    let appearance = NSAppearance(named: .darkAqua)!
    let previousApp = NSApp.appearance
    NSApp.appearance = appearance
    defer { NSApp.appearance = previousApp }

    let split = NSSplitView()
    split.isVertical = true
    split.dividerStyle = .thin
    let nested = NSHostingView(rootView: ButtonRows())      // ← 产品的形状：嵌套 hosting view 装 Button 列
    nested.translatesAutoresizingMaskIntoConstraints = false
    nested.widthAnchor.constraint(equalToConstant: 148).isActive = true
    if pinNested { nested.appearance = appearance }
    let right = NSHostingView(rootView: DetailPane())
    right.translatesAutoresizingMaskIntoConstraints = false
    split.addArrangedSubview(nested)
    split.addArrangedSubview(right)

    let size = NSSize(width: 640, height: 440)
    let window = NSWindow(contentRect: NSRect(origin: NSPoint(x: -20000, y: -20000), size: size),
                          styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    window.contentView = split
    split.frame = NSRect(origin: .zero, size: size)
    window.layoutIfNeeded()
    split.layoutSubtreeIfNeeded()
    guard let rep = nested.bitmapImageRepForCachingDisplay(in: nested.bounds) else {
        print("\(arm): 建不出位图缓存"); return
    }
    nested.cacheDisplay(in: nested.bounds, to: rep)
    let scale = max(1, Int(Double(rep.pixelsWide) / 148.0))
    print("\(arm)  nested.appearance=\(nested.appearance == nil ? "nil（跟着窗口）" : "钉死 darkAqua")"
          + "  effective=\(nested.effectiveAppearance == appearance ? "dark" : "不是 dark")")
    measure(rep, "文字列", x: 40 * scale, y: 95 * scale, w: 100 * scale, h: 150 * scale)
    measure(rep, "图标列", x: 8 * scale, y: 95 * scale, w: 30 * scale, h: 150 * scale)
    window.orderOut(nil)
}

shootNestedButtons("O 嵌套 hosting + Button 列（产品形状）", pinNested: false)
shootNestedButtons("P 同上 + 给嵌套视图钉外观         ", pinNested: true)




shootSplit("E 嵌套侧栏   ", startWith: .darkAqua, flipTo: nil, pin: false, measureAgainst: .darkAqua)
// F：亮色下建，**运行中翻成暗色**再画 —— 真实自动深色模式的那条路
shootSplit("F 运行时翻暗 ", startWith: .aqua, flipTo: .darkAqua, pin: false, measureAgainst: .darkAqua)
// G：同 F，但给嵌套 hosting view 钉上外观（候选解药）
shootSplit("G 钉外观解药 ", startWith: .aqua, flipTo: .darkAqua, pin: true, measureAgainst: .darkAqua)

