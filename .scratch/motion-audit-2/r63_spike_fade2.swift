import AppKit
import Darwin

setbuf(stdout, nil)   //  piping 出去时 stdout 是块缓冲：崩了就把已有读数全吞掉（本轮已经踩过一次）

// R63 第三问（决定性的一问）：`animator().alphaValue` 那条淡入，在**真正的 App 事件循环**里
// 会不会把模型值落到终值。上一版 spike 用的是 `RunLoop.main.run(until:)`，
// 读数是"永远是 0、完成回调从不跑" —— 但那有两种解释，而我不能挑一个便宜的写进账本：
//   A. AppKit 的动画由公共模式的定时器源驱动，`run(until:)` 不服务它 ⇒ **量尺的锅**；
//   B. 这条淡入真的会卡在 0 ⇒ **产品的锅**（用户永远看不见空结果那句话）。
// 这一版把泵换成 `NSApp.run()`（和线上一样），其余形状一字不动。

let app = NSApplication.shared
let panel = NSPanel(contentRect: NSRect(x: 100, y: 300, width: 300, height: 140),
                    styleMask: [.titled, .fullSizeContentView], backing: .buffered, defer: false)
guard let content = panel.contentView else { fatalError() }

func label(_ text: String, _ y: CGFloat) -> NSTextField {
    let f = NSTextField(labelWithString: text)
    f.frame = NSRect(x: 10, y: y, width: 260, height: 20)
    content.addSubview(f)
    return f
}

let a = label("臂1 产品形状（无完成回调）", 110)
let b = label("臂2 带完成回调", 85)
let e = label("臂3 屏外 orderFront", 60)
let live = label("臂4 真实屏位置", 35)

panel.orderFrontRegardless()
RunLoop.main.run(until: Date().addingTimeInterval(0.2))   // 先让窗口真的建好显示周期

func start(_ target: NSTextField) {
    target.alphaValue = 0
    NSAnimationContext.runAnimationGroup({ ctx in
        ctx.duration = 0.2
        ctx.allowsImplicitAnimation = false
        target.animator().alphaValue = 1
    }, completionHandler: {
        print("完成回调 \(target.stringValue.prefix(12)) alpha=\(String(format: "%.3f", target.alphaValue))")
    })
}
start(a); start(b); start(live)

var ticks = 0
Timer.scheduledTimer(withTimeInterval: 0.3, repeats: true) { _ in
    ticks += 1
    print("tick\(ticks) 臂1=\(String(format: "%.3f", a.alphaValue)) 臂2=\(String(format: "%.3f", b.alphaValue)) 臂4=\(String(format: "%.3f", live.alphaValue))")
    if ticks == 4 {
        // 臂3：在"屏外 -20000"这一档跑同一条淡入（夹具用的就是这一档）
        panel.setFrameOrigin(NSPoint(x: -20000, y: -20000))
        start(e)
    }
    if ticks == 8 {
        print("最终 臂1=\(String(format: "%.3f", a.alphaValue)) 臂2=\(String(format: "%.3f", b.alphaValue)) "
              + "臂3(屏外)=\(String(format: "%.3f", e.alphaValue)) 臂4=\(String(format: "%.3f", live.alphaValue))")
        // 屏外这一档同时读一次 cacheDisplay 的墨，判"夹具拍得到拍不到"
        if let rep = content.bitmapImageRepForCachingDisplay(in: content.bounds) {
            content.cacheDisplay(in: content.bounds, to: rep)
            let scale = Double(rep.pixelsWide) / Double(max(content.bounds.width, 1))
            for row in [110.0, 85.0, 60.0, 35.0] {
                var ink = 0
                // 位图行从**顶部**数：AppKit 的 y 向上，所以要 (contentH - y - h) 换算，再夹进范围。
                let top = max(0, min(rep.pixelsHigh - 1, Int((content.bounds.height - (row + 20)) * scale)))
                let bot = max(top, min(rep.pixelsHigh, Int((content.bounds.height - row) * scale)))
                var y = top
                while y < bot {
                    for x in 0..<rep.pixelsWide where (rep.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0.03 {
                        ink += 1
                    }
                    y += 1
                }
                print("行 y=\(Int(row)) 的墨像素=\(ink) (top=\(top) bot=\(bot) scale=\(scale))")
            }
        }
        app.stop(nil)
    }
}
app.run()
