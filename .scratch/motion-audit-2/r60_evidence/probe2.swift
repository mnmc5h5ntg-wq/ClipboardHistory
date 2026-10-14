// R60 探针 v2：用**结构**而不是颜色把"搜索框那条均匀填充"和"正在淡出的横幅文字"分开。
//
// 为什么要有 v2：v1 用"中灰像素数 ≥60"当搜索框的标记，结果第 5 帧在 rows 30–47 也报了 82 ——
// 那不是框，那是**淡到一半的横幅文字**（白字掉到 50% 就正好落进中灰亮度带）。
// 同一族错误本轮已经犯过两次（各自峰值归一、吃饱和度的质心），所以这次换轴：
// 框是一片**连续均匀**的填充（相邻像素亮度差 ≤6），文字是一笔一笔的笔画（连续段只有几 px）。
// 于是判据变成"这一行里最长的均匀段有多长"，与亮度、与淡入淡出都无关。
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

// 亮度缓存：整帧一次读完，避免 colorAt 被调两遍。
func luma(_ f: Int, _ x: Int, _ y: Int) -> Int {
    guard let c = rep.colorAt(x: x, y: f * (frameH + gap) + y) else { return -1 }
    return Int(((c.redComponent * 3 + c.greenComponent * 6 + c.blueComponent) / 10 * 255).rounded())
}

for f in 0..<frames {
    var topEdge = -1, topRun = 0
    var report: [String] = []
    for y in 0..<frameH {
        var best = 0, run = 1, prev = -99
        for x in 40..<240 {
            let l = luma(f, x, y)
            if l < 0 { continue }
            if abs(l - prev) <= 6 { run += 1 } else { run = 1 }
            prev = l
            if run > best { best = run }
        }
        if best >= 60 {
            if topEdge < 0 { topEdge = y; topRun = best }
            if report.count < 4 { report.append("y=\(y) 最长均匀段=\(best)") }
        }
    }
    print("第 \(f) 帧：框顶(均匀段≥60)=\(topEdge < 0 ? "—" : "\(topEdge)")px"
        + (topEdge >= 0 ? " 该段长=\(topRun) 共 \(report.count)+ 行" : "")
        + "  ｜ " + report.joined(separator: " "))
}
