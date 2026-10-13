// R36 的第三把尺子：`bottomInkFraction` 到底在量什么。
//
// 起因是**看图**：`sidebar-history-300x520-light` 这张帧的底 100pt 里，
// 黑药丸在上、下面全是空的浅灰，可判据说它"最底一行 100.0% 是墨"。
// 一个"100% 有墨"的底行和一张"什么都没有"的底行不可能同时为真，
// 所以要么我看错了图，要么这把尺量的不是墨。
//
// 它现在的写法是"底行 vs **左上角那一个像素**"，而左上角在侧栏帧里是工具排/搜索框那一块，
// 未必等于底行所在的窗口底色 —— 那种情况下**整行都会被数成墨**。
// 这个工具把三种参照各自读一遍，让数字自己说：
//   ref=topLeft   现在的实现
//   ref=rowMode   底行自己的众数（这一行的背景）
//   ref=colMode   底行所在那一列的众数
// 用法：bottomedge <png> [tol=12]
import AppKit

let args = CommandLine.arguments
guard args.count >= 2 else {
    FileHandle.standardError.write("usage: bottomedge <png> [tol]\n".data(using: .utf8)!)
    exit(2)
}
let tol = args.count > 2 ? Int(args[2]) ?? 12 : 12
guard let data = FileManager.default.contents(atPath: args[1]),
      let rep = NSBitmapImageRep(data: data), let base = rep.bitmapData else {
    FileHandle.standardError.write("读不到像素\n".data(using: .utf8)!)
    exit(3)
}
let w = rep.pixelsWide, h = rep.pixelsHigh, bpr = rep.bytesPerRow
func pixel(_ x: Int, _ y: Int) -> (Int, Int, Int) {
    let o = y * bpr + x * 4
    return (Int(base[o]), Int(base[o + 1]), Int(base[o + 2]))
}
func dev(_ a: (Int, Int, Int), _ b: (Int, Int, Int)) -> Int {
    abs(a.0 - b.0) + abs(a.1 - b.1) + abs(a.2 - b.2)
}
/// 一行的**中位色**（每通道各自取中位数）。
/// 刻意不用"量化众数的桶心"：桶心是下边界，与真实像素最多能差 7×3=21 > tol=12，
/// 那会把一行**完全干净**的底色读成"100% 有墨"—— 那是我这把尺自己的假阳性。
func rowMode(_ y: Int) -> (Int, Int, Int) {
    var rs: [Int] = [], gs: [Int] = [], bs: [Int] = []
    rs.reserveCapacity(w); gs.reserveCapacity(w); bs.reserveCapacity(w)
    for x in 0..<w {
        let p = pixel(x, y)
        rs.append(p.0); gs.append(p.1); bs.append(p.2)
    }
    func med(_ a: [Int]) -> Int { a.sorted()[a.count / 2] }
    return (med(rs), med(gs), med(bs))
}
func fractionInk(_ y: Int, against ref: (Int, Int, Int)) -> Double {
    var ink = 0
    for x in 0..<w where dev(pixel(x, y), ref) > tol { ink += 1 }
    return Double(ink) / Double(w)
}
let topLeft = pixel(0, 0)
let bottomRow = h - 1
let rm = rowMode(bottomRow)
print("SWEEP \(args[1].split(separator: "/").last ?? "") refTL=\(String(format: "%.1f", fractionInk(bottomRow, against: topLeft) * 100)) refRow=\(String(format: "%.1f", fractionInk(bottomRow, against: rm) * 100)) cornerDev=\(dev(topLeft, rm)) rowMed=\(rm)")
print("FRAME \(w)x\(h)  tol=\(tol)")
print("  左上角像素 = \(topLeft)   底行众数 = \(rm)   两者差 = \(dev(topLeft, rm))")
print("  底行墨占比  ref=topLeft  = \(String(format: "%.1f", fractionInk(bottomRow, against: topLeft) * 100))%")
print("  底行墨占比  ref=rowMode  = \(String(format: "%.1f", fractionInk(bottomRow, against: rm) * 100))%")
for y in [0, 1, 2, 20, 40, h - 21, h - 2] {
    print("  行 \(y)：ref=topLeft \(String(format: "%5.1f", fractionInk(y, against: topLeft) * 100))%"
          + "   ref=rowMode \(String(format: "%5.1f", fractionInk(y, against: rowMode(y)) * 100))%"
          + "   众数=\(rowMode(y))")
}
