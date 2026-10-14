// R60 探针 v3：找**水平直边**，不是找颜色、也不是找均匀。
//
// 前两版都废了，而且废得有价值：
//   v1「中灰像素数 ≥60」—— 淡到一半的横幅白字正好落进中灰带，第 5 帧在 rows 30–47 报了 82，
//      那不是搜索框，是正在消失的字。
//   v2「最长均匀段 ≥60」—— 每一帧的第 0–3 行都是 200：横幅那片平底本身就是均匀的。
// 所以这次问一个结构问题：**搜索框的上边是一条横贯一二百像素的直线**，
// 而字的笔画是散的。于是取"相邻两行亮度差 ≥12 的最长连续 x 段"——
// 只有真正的水平边会给出 120 以上的连续段。
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
let x0 = 40, x1 = min(320, W)
print("stack \(W)x\(H) 每帧=\(frameH)px，扫描 x∈[\(x0),\(x1))")

var lum: [[[Int]]] = []
for f in 0..<frames {
    var plane: [[Int]] = []
    for y in 0..<frameH {
        var row: [Int] = []
        for x in x0..<x1 {
            guard let c = rep.colorAt(x: x, y: f * (frameH + gap) + y) else { row.append(-1); continue }
            row.append(Int(((c.redComponent * 3 + c.greenComponent * 6 + c.blueComponent) / 10 * 255).rounded()))
        }
        plane.append(row)
    }
    lum.append(plane)
}

for f in 0..<frames {
    var best = (row: -1, run: 0)
    var edges: [String] = []
    for y in 1..<frameH {
        var run = 0, mx = 0
        for i in 0..<(x1 - x0) {
            let a = lum[f][y][i], b = lum[f][y - 1][i]
            if a >= 0, b >= 0, abs(a - b) >= 12 { run += 1; mx = max(mx, run) } else { run = 0 }
        }
        if mx >= 120 {
            if best.row < 0 { best = (y, mx) }
            if edges.count < 5 { edges.append("y=\(y):\(mx)") }
        }
    }
    // 同一帧里横幅那颗红图标的行范围（它淡到看不见 = 横幅基本没了）
    var redRows: [Int] = []
    for y in 0..<frameH {
        var hits = 0
        for i in 0..<(x1 - x0) {
            guard let c = rep.colorAt(x: x0 + i, y: f * (frameH + gap) + y) else { continue }
            let r = Int((c.redComponent * 255).rounded()), g = Int((c.greenComponent * 255).rounded()),
                b = Int((c.blueComponent * 255).rounded())
            if r > 120, r - g > 60, r - b > 60 { hits += 1 }
        }
        if hits > 0 { redRows.append(y) }
    }
    print("第 \(f) 帧 第一条水平边(连续≥120px)=\(best.row < 0 ? "—" : "\(best.row)")px"
        + " 边行=[\(edges.joined(separator: " "))]"
        + " ｜ 红图标行=" + (redRows.isEmpty ? "—" : "\(redRows.min()!)–\(redRows.max()!)")
        + (best.row >= 0 && !redRows.isEmpty && best.row < redRows.max()! ? "  ⇒ 边在图标下沿之上：两者同行" : ""))
}
