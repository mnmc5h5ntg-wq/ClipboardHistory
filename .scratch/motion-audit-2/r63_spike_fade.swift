import AppKit

// R63 的第二问：`animator().alphaValue` 这条淡入，在**没有真实显示周期**的进程里
// 到底是"迟早会落到终值"还是"永远是 0"。
// 为什么必须分开：产品里空结果那句话走的就是这条路（`applyEmptyState`：先 `alphaValue = 0`
// 再 `animator().alphaValue = 1`）。探针读到 alpha=0.000 停了两秒 ——
// 这既可能是"通道看不见动画"（D-055 记过），也可能是"用户从来没见过那句话"。
// 两者的处置完全相反，所以要一个与产品无关的最小实验来定机制。

let app = NSApplication.shared
let panel = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 300, height: 120),
                    styleMask: [.titled, .fullSizeContentView], backing: .buffered, defer: false)
guard let content = panel.contentView else { fatalError() }

func probe(_ tag: String, _ label: NSTextField) {
    print("\(tag) alpha=\(String(format: "%.3f", label.alphaValue)) hidden=\(label.isHidden)")
}

// 臂 1：照抄产品的形状（先 0，再 animator() 到 1，组内 allowsImplicitAnimation=false）
let a = NSTextField(labelWithString: "臂1 产品形状")
a.frame = NSRect(x: 10, y: 90, width: 200, height: 20)
content.addSubview(a)
a.alphaValue = 0
NSAnimationContext.runAnimationGroup { ctx in
    ctx.duration = 0.2
    ctx.allowsImplicitAnimation = false
    a.animator().alphaValue = 1
}
probe("臂1 设完立刻读", a)

// 臂 2：同样形状，但带 completionHandler，回调里把终值再钉一次
let b = NSTextField(labelWithString: "臂2 带完成回调")
b.frame = NSRect(x: 10, y: 65, width: 200, height: 20)
content.addSubview(b)
b.alphaValue = 0
var bCompleted = false
NSAnimationContext.runAnimationGroup({ ctx in
    ctx.duration = 0.2
    ctx.allowsImplicitAnimation = false
    b.animator().alphaValue = 1
}, completionHandler: { bCompleted = true })
probe("臂2 设完立刻读", b)

// 臂 3：先落终值，再 animator()（"淡入只是装饰"那一档）
let c = NSTextField(labelWithString: "臂3 模型先落 1")
c.frame = NSRect(x: 10, y: 40, width: 200, height: 20)
content.addSubview(c)
c.alphaValue = 0
c.alphaValue = 1
NSAnimationContext.runAnimationGroup { ctx in
    ctx.duration = 0.2
    c.animator().alphaValue = 1
}
probe("臂3 设完立刻读", c)

// 臂 4：显式 layer-backing（图层动画可能比非图层更依赖显示周期）
let d = NSTextField(labelWithString: "臂4 layer-backed")
d.frame = NSRect(x: 10, y: 15, width: 200, height: 20)
d.wantsLayer = true
content.addSubview(d)
d.alphaValue = 0
NSAnimationContext.runAnimationGroup { ctx in
    ctx.duration = 0.2
    d.animator().alphaValue = 1
}
probe("臂4 设完立刻读", d)

// —— 不 orderFront（离屏、无显示周期）先读一遍
RunLoop.main.run(until: Date().addingTimeInterval(0.5))
print("—— 没上屏，转了 0.5s ——")
probe("臂1", a); probe("臂2", b); probe("臂3", c); probe("臂4", d)
print("臂2 完成回调跑了吗 = \(bCompleted)")
RunLoop.main.run(until: Date().addingTimeInterval(2.0))
print("—— 再转 2.0s，仍未上屏 ——")
probe("臂1", a); probe("臂2", b); probe("臂3", c); probe("臂4", d)
print("臂2 完成回调跑了吗 = \(bCompleted)")

// —— 现在才上屏（真实显示周期），看会不会补上
panel.setFrameOrigin(NSPoint(x: 200, y: 400))
panel.orderFrontRegardless()
RunLoop.main.run(until: Date().addingTimeInterval(1.0))
print("—— orderFront 之后再转 1.0s ——")
probe("臂1", a); probe("臂2", b); probe("臂3", c); probe("臂4", d)
print("臂2 完成回调跑了吗 = \(bCompleted)")

// —— 屏幕外 orderFront（夹具用的那一档：-20000）
let e = NSTextField(labelWithString: "臂5 屏外 orderFront")
e.frame = NSRect(x: 10, y: 15, width: 220, height: 20)
content.addSubview(e)
e.alphaValue = 0
NSAnimationContext.runAnimationGroup { ctx in
    ctx.duration = 0.2
    ctx.allowsImplicitAnimation = false
    e.animator().alphaValue = 1
}
panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
RunLoop.main.run(until: Date().addingTimeInterval(1.0))
print("—— 屏外 orderFront 之后 1.0s ——")
probe("臂5", e)
let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds)
if let rep {
    content.cacheDisplay(in: content.bounds, to: rep)
    var drawn5 = 0
    for y in 0..<rep.pixelsHigh {
        for x in 0..<rep.pixelsWide where rep.colorAt(x: x, y: y)!.alphaComponent > 0.03 { drawn5 += 1 }
    }
    print("臂5 所在区域 cacheDisplay 不透明像素=\(drawn5)")
}
