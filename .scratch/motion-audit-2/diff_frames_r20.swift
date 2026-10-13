// R20 的视觉 A/B：把"哪些像素动了"量成**行带**，而不是只看"哪些帧的哈希变了"。
//
// 存在的理由：帧哈希只告诉我"这 22 帧变了"，而本轮我只打算动**搜索框那一条**。
// 哈希给不出"顺手动了别的东西"这种答案 —— 只有行带能。
// 与 R19 记下的那条同族：整窗像素会把效果归因给错误的元素，判据要框区域。
//
// 用法：swift diff_frames_r20.swift <before-dir> <after-dir> [name-prefix]
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: diff_frames <before> <after> [prefix]\n".data(using: .utf8)!)
    exit(2)
}
let before = args[1], after = args[2]
let prefix = args.count > 3 ? args[3] : ""
let scale = 2   // 捕获是 @2x，行号换算成 pt 要除以它
let tolerance = 8 // 单通道容差：低于它是抗锯齿噪声（R19 记过"容差为 0 会淹没分类器"）

func bitmap(_ path: String) -> NSBitmapImageRep? {
    guard let data = FileManager.default.contents(atPath: path) else { return nil }
    return NSBitmapImageRep(data: data)
}

/// 一个像素占几个字节。`NSBitmapImageRep` 没有 `bytesPerPixel`，只能自己算。
func strideOfPixels(_ rep: NSBitmapImageRep) -> Int {
    rep.samplesPerPixel * rep.bitsPerSample / 8
}

func differs(_ a: UnsafeMutablePointer<UInt8>, _ b: UnsafeMutablePointer<UInt8>,
             channels: Int) -> Bool {
    for channel in 0..<channels where abs(Int(a[channel]) - Int(b[channel])) > tolerance {
        return true
    }
    return false
}

let names = (try? FileManager.default.contentsOfDirectory(atPath: after))?.sorted() ?? []
for name in names where name.hasPrefix(prefix) && name.hasSuffix(".png") {
    guard let fresh = bitmap(after + "/" + name) else { continue }
    guard let prior = bitmap(before + "/" + name) else {
        print("\(name)  NO_PAIR（before 侧没有这一帧）")
        continue
    }
    guard let ob = prior.bitmapData, let nb = fresh.bitmapData else {
        print("\(name)  NO_BYTES")
        continue
    }
    let ow = prior.pixelsWide, oh = prior.pixelsHigh, obpr = prior.bytesPerRow
    let nw = fresh.pixelsWide, nh = fresh.pixelsHigh, nbpr = fresh.bytesPerRow
    guard ow == nw, oh == nh else {
        print("\(name)  SIZE \(ow)x\(oh) -> \(nw)x\(nh)")
        continue
    }
    let opx = strideOfPixels(prior), npx = strideOfPixels(fresh)
    guard opx == npx, prior.bitsPerSample == fresh.bitsPerSample,
          !prior.isPlanar, !fresh.isPlanar else {
        print("\(name)  FORMAT prior=\(opx)B/pp bpp=\(prior.bitsPerSample) planar=\(prior.isPlanar) "
              + "fresh=\(npx)B/pp bpp=\(fresh.bitsPerSample) planar=\(fresh.isPlanar) ⇒ 不比")
        continue
    }
    let channels = min(opx, 4)

    var bands: [(start: Int, end: Int)] = []
    var openStart: Int? = nil
    var lastChanged = -100
    var changedRows = 0
    for y in 0..<oh {
        var rowDiffers = false
        var x = 0
        while x < ow, !rowDiffers {
            if differs(ob + y * obpr + x * opx, nb + y * nbpr + x * npx, channels: channels) {
                rowDiffers = true
            }
            x += 1
        }
        if rowDiffers {
            changedRows += 1
            if openStart == nil { openStart = y }
            lastChanged = y
        } else if y - lastChanged > 4 * scale, let start = openStart {
            bands.append((start, lastChanged))
            openStart = nil
        }
    }
    if let start = openStart { bands.append((start, lastChanged)) }

    let described = bands
        .map { String(format: "%.1f–%.1fpt", Double($0.start) / Double(scale),
                      Double($0.end + 1) / Double(scale)) }
        .joined(separator: ", ")
    print("\(name)  rows=\(changedRows)  bands(top-down pt): \(described.isEmpty ? "none" : described)")
}
