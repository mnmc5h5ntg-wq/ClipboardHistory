// R31 spike（仓库外，一次性证据，不进判据）
//
// 要判的事只有一件：**"合成后"的像素到底能不能在离屏条件下拍到。**
// R30 量到设置页侧栏列的宿主视图生效外观是 `NSAppearanceNameVibrantDark`，
// 而 `cacheDisplay` 不走窗口服务器的 vibrancy 合成 ⇒ 帧里是"合成前"的像素
// （暗档侧栏文字因此是黑字黑底）。这条把三个盲区绑在同一个原因上：
// 侧栏文字、`.borderedProminent` 的红色填充（BACKLOG 40 / 人工批次 36.4）、材质层。
//
// 四条臂，同一棵树、同一个尺，只换"怎么取像素"：
//   A `cacheDisplay`（仓库现在用的）              ⇒ 预期：文字在暗侧（合成前）
//   B `CGWindowListCreateImage(optionIncludingWindow)` ⇒ 走窗口服务器 ⇒ 预期：文字在亮侧
//   C 上屏 0.3s 之后 `screencapture -l<window>`（外部命令，本 spike 只打印命令，不自动跑）
//   D 对照组：把材质层换成纯色底（没有 vibrancy）⇒ 两臂应当一致，用来证明差别真的来自合成而不是别的
//
// 编译：xcrun swiftc composite_capture_r31.swift -o /tmp/r31 && /tmp/r31
import AppKit
import CoreGraphics
import SwiftUI

struct Row: Identifiable, Hashable {
    let id: Int
    let title: String
    let symbol: String
}

let rows = [
    Row(id: 0, title: "快捷键", symbol: "command"),
    Row(id: 1, title: "通用", symbol: "gearshape"),
    Row(id: 2, title: "隐私", symbol: "hand.raised"),
    Row(id: 3, title: "推荐", symbol: "wand.and.stars"),
]

/// 复刻 `NavigationSplitView` 侧栏那一列的**关键条件**：内容装在 `NSVisualEffectView(material:.sidebar)` 里。
/// `useMaterial=false` 是 D 臂（把材质换成纯色底），用来证明差别来自合成而不是别的层。
func build(useMaterial: Bool, appearance: NSAppearance) -> (NSWindow, NSView) {
    let list = List(rows, id: \.id) { row in
        Label(row.title, systemImage: row.symbol)
            .foregroundStyle(AnyShapeStyle(.primary))
            .symbolRenderingMode(.hierarchical)
    }
    .frame(width: 200, height: 300)
    let hosting = NSHostingView(rootView: AnyView(list.environment(\.colorScheme, .dark)))
    hosting.frame = NSRect(x: 0, y: 0, width: 200, height: 300)

    let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 200, height: 300),
                          styleMask: [.titled, .closable, .resizable],
                          backing: .buffered, defer: false)
    window.appearance = appearance
    if useMaterial {
        let effect = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: 200, height: 300))
        effect.material = .sidebar
        effect.blendingMode = .withinWindow
        effect.state = .active
        effect.autoresizingMask = [.width, .height]
        effect.addSubview(hosting)
        window.contentView = effect
    } else {
        let plain = NSView(frame: NSRect(x: 0, y: 0, width: 200, height: 300))
        plain.wantsLayer = true
        plain.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor
        plain.addSubview(hosting)
        window.contentView = plain
    }
    window.setFrameOrigin(NSPoint(x: -12000, y: -6000))
    return (window, hosting)
}

func luma(_ r: Int, _ g: Int, _ b: Int) -> Double {
    func lin(_ c: Int) -> Double {
        let s = Double(c) / 255
        return s <= 0.03928 ? s / 12.92 : pow((s + 0.055) / 1.055, 2.4)
    }
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

/// 与仓库那把 `inkSideCounts` 同一条思路：区域众数当底，偏离 >16 记一侧。
func sideSplit(_ pixels: [UInt8], _ w: Int, _ h: Int, _ bpr: Int,
               x0: Int, y0: Int, x1: Int, y1: Int) -> (brighter: Int, darker: Int, bg: Int) {
    var hist = [Int](repeating: 0, count: 256)
    func lum(_ x: Int, _ y: Int) -> Int {
        let o = y * bpr + x * 4
        return Int(luma(Int(pixels[o]), Int(pixels[o + 1]), Int(pixels[o + 2])).rounded())
    }
    for y in y0..<y1 { for x in x0..<x1 { hist[lum(x, y) / 8] += 1 } }
    let bg = hist.firstIndex(of: hist.max() ?? 0) ?? 0
    let bgLuma = bg * 8 + 4
    var brighter = 0, darker = 0
    for y in y0..<y1 {
        for x in x0..<x1 {
            let d = lum(x, y) - bgLuma
            if d > 16 { brighter += 1 } else if d < -16 { darker += 1 }
        }
    }
    return (brighter, darker, bgLuma)
}

func report(_ arm: String, _ rep: NSBitmapImageRep) {
    guard let base = rep.bitmapData else { print("\(arm): 没有位图"); return }
    let pixels = Array(UnsafeBufferPointer(start: base, count: rep.bytesPerRow * rep.pixelsHigh))
    // 文字列：x 40..190（图标在左边），y 第 2–4 行
    let scale = max(1, rep.pixelsWide / 200)
    let s = sideSplit(pixels, rep.pixelsWide, rep.pixelsHigh, rep.bytesPerRow,
                      x0: 40 * scale, y0: 60 * scale, x1: 190 * scale, y1: 200 * scale)
    print(String(format: "%@  %dx%dpx  底=%d  亮侧=%d 暗侧=%d ⇒ %@",
                 arm, rep.pixelsWide, rep.pixelsHigh, s.bg, s.brighter, s.darker,
                 s.brighter + s.darker == 0 ? "没有墨" : (s.brighter > s.darker ? "文字在亮侧（合成后该有的样子）" : "文字在暗侧（合成前）")))
}

_ = NSApplication.shared
let dark = NSAppearance(named: .darkAqua)!

for useMaterial in [true, false] {
    let label = useMaterial ? "材质 .sidebar" : "纯色底（对照）"
    let (window, host) = build(useMaterial: useMaterial, appearance: dark)
    window.layoutIfNeeded()
    host.layoutSubtreeIfNeeded()
    print("=== \(label)  侧栏宿主生效外观=\(host.effectiveAppearance.name.rawValue)")

    // A：仓库现在这条路
    if let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) {
        dark.performAsCurrentDrawingAppearance { host.cacheDisplay(in: host.bounds, to: rep) }
        report("A cacheDisplay            ", rep)
    }

    // B：把**整窗**（含材质层）走一次 cacheDisplay —— 材质层在不在、文字极性翻不翻，
    // 这一臂能分开：如果底的亮度变了而文字仍在暗侧，说明"没合成"的不是背景，而是文字本身。
    window.orderFrontRegardless()
    window.display()
    RunLoop.main.run(until: Date().addingTimeInterval(0.3))
    if let root = window.contentView,
       let rep = root.bitmapImageRepForCachingDisplay(in: root.bounds) {
        dark.performAsCurrentDrawingAppearance { root.cacheDisplay(in: root.bounds, to: rep) }
        report("B 整窗 cacheDisplay      ", rep)
    }
    // C：`CGWindowListCreateImage` 在本机 SDK（macOS 15）**已标记 unavailable**，
    //     替代是 ScreenCaptureKit（要录屏授权 + 窗口真上屏）。
    //     ⇒ "走窗口服务器取图"这条路在离屏测试进程里**结构上没有**，只能真机截屏。
    print("C 窗口服务器取图：CGWindowListCreateImage 不可用（SDK 标记 unavailable，替代要录屏授权）")
    window.orderOut(nil)
}
