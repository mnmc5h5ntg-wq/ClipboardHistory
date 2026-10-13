// R36：`blackBandPt` 报 66pt，而我裁出来的黑药丸只有 ~20pt 高 —— 两个数不可能都对。
// 这个工具逐行数"接近全黑的像素占比"，把黑的**区间**打出来，让 66 这个数要么对上某个区间，
// 要么被证明是量在别的东西上（`blackBandHeight` 从帧底往上数，所以"底行是空的"时它读 0 才对）。
import AppKit
let path = CommandLine.arguments[1]
let data = FileManager.default.contents(atPath: path)!
let rep = NSBitmapImageRep(data: data)!
let base = rep.bitmapData!
let w = rep.pixelsWide, h = rep.pixelsHigh, bpr = rep.bytesPerRow
var runs: [(Int, Int)] = []
var start: Int? = nil
for y in 0..<h {
    var black = 0
    for x in 0..<w {
        let o = y * bpr + x * 4
        if Int(base[o]) + Int(base[o + 1]) + Int(base[o + 2]) < 60 { black += 1 }
    }
    let isBlackRow = Double(black) / Double(w) > 0.5
    if isBlackRow && start == nil { start = y }
    if !isBlackRow && start != nil { runs.append((start!, y - 1)); start = nil }
}
if let s = start { runs.append((s, h - 1)) }
print("黑行区间（px，@2x ⇒ 除 2 得 pt）：", runs.map { "\($0.0)..\($0.1)" }.joined(separator: " "))
print("帧高 px=\(h) ⇒ 最底一个黑行的下沿距帧底 \(h - 1 - (runs.last?.1 ?? 0)) px = \(Double(h - 1 - (runs.last?.1 ?? 0)) / 2) pt")
