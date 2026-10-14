import Foundation
import AppKit
// 用法：zoom <stack.png> <帧号> <x0> <x1> <放大倍数> <输出.png>
let a = CommandLine.arguments
guard let d = FileManager.default.contents(atPath: a[1]), let r = NSBitmapImageRep(data: d) else { exit(2) }
let frame = Int(a[2])!, x0 = Int(a[3])!, x1 = Int(a[4])!, k = Int(a[5])!
let H = r.pixelsHigh, gap = 2, frames = 10
let fh = (H - gap * frames) / frames
let top = frame * (fh + gap)
let w = x1 - x0
let out = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w * k, pixelsHigh: fh * k,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
for y in 0..<fh { for x in 0..<w {
    let c = r.colorAt(x: x0 + x, y: top + y) ?? .black
    for dy in 0..<k { for dx in 0..<k { out.setColor(c, atX: x * k + dx, y: y * k + dy) } }
}}
try! out.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[6]))
print("ok \(w*k)x\(fh*k)")
