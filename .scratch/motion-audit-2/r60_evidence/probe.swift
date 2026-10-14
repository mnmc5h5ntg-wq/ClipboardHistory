// R60 探针：把逐帧堆叠图切成 10 帧，逐行打印三类计数，用来**从数据里**挑
// "搜索框那颗放大镜"的检测规则 —— 不许凭印象写阈值（R57 那条色号阈值的教训）。
//
// 跑法：swift run 不行（这是独立脚本），用
//   xcrun swiftc -O /tmp/r60probe/probe.swift -o /tmp/r60probe/probe && /tmp/r60probe/probe
import Foundation
import AppKit

let path = CommandLine.arguments.count > 1 ? CommandLine.arguments[1]
    : "/tmp/r59-motion/notice-banner-dismiss-逐帧-stack.png"
guard let data = FileManager.default.contents(atPath: path),
      let rep = NSBitmapImageRep(data: data) else {
    FileHandle.standardError.write("读不到 \(path)\n".data(using: .utf8)!)
    exit(2)
}
let W = rep.pixelsWide, H = rep.pixelsHigh
let frames = 10, gap = 2
let frameH = (H - gap * frames) / frames
print("stack \(W)x\(H) 帧数=\(frames) 每帧=\(frameH)px 间隔=\(gap)")
guard frameH > 40 else { print("切帧几何不对"); exit(3) }

func px(_ f: Int, _ x: Int, _ y: Int) -> (Int, Int, Int) {
    let oy = f * (frameH + gap) + y
    guard let c = rep.colorAt(x: x, y: oy) else { return (-1, -1, -1) }
    return (Int((c.redComponent * 255).rounded()),
            Int((c.greenComponent * 255).rounded()),
            Int((c.blueComponent * 255).rounded()))
}

for f in 0..<frames {
    var lines: [String] = []
    for y in 0..<frameH {
        var red = 0, grayMid = 0, bright = 0, lumSum = 0
        for x in 40..<200 {
            let (r, g, b) = px(f, x, y)
            if r < 0 { continue }
            let lum = (r * 3 + g * 6 + b) / 10
            lumSum += lum
            if r > 120, r - g > 60, r - b > 60 { red += 1 }
            if abs(r - g) <= 12, abs(g - b) <= 14, lum > 60, lum < 170 { grayMid += 1 }
            if lum > 170 { bright += 1 }
        }
        if red > 0 || grayMid > 3 || bright > 3 {
            lines.append("  y=\(y) 红=\(red) 中灰=\(grayMid) 亮=\(bright) 均值=\(lumSum / 160)")
        }
    }
    print("=== 第 \(f) 帧 ===")
    print(lines.joined(separator: "\n"))
}
