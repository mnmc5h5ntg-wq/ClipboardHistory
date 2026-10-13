// R20 的第二把尺子：把"这 22 帧变了"翻译成"变了的东西是不是只有搜索框那一条"。
//
// 两个模式：
//   shift <before.png> <after.png> [maxPx] [tol] [x0pt x1pt]
//       逐档试纵向位移（after 的第 y 行 对 before 的第 y-k 行），报告每一档还剩多少行不同。
//       最少的那一档 = 真实的整体平移量；剩下的差异带 = **真正的内容变化**。
//       存在的理由：搜索框长高 1pt 会把下面整列往下推 1pt，逐行比就会"每一行都不同"，
//       那不是 22 处缺陷，是 1 处平移。不先做这一步，我读到的就是一堆假阳性。
//       后两个参数把比较限制在一段**列**里（整窗帧必须分列读，否则侧栏的变化会
//       被算到详情区头上 —— 与 R19 记的"整窗像素会把动效归因给错的元素"同一条）。
//   crop <in.png> <out.png> <x,y,w,h 单位 pt> [scale]
//       按 pt 裁一块出来（默认 @2x），为了能在对话里**看清**那一小块。
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: inspect <shift|crop> ...\n".data(using: .utf8)!)
    exit(2)
}

func load(_ path: String) -> NSBitmapImageRep {
    guard let data = FileManager.default.contents(atPath: path),
          let rep = NSBitmapImageRep(data: data),
          let ptr = rep.bitmapData else {
        FileHandle.standardError.write("读不到像素：\(path)\n".data(using: .utf8)!)
        exit(3)
    }
    _ = ptr
    return rep
}

func pxStride(_ rep: NSBitmapImageRep) -> Int { rep.samplesPerPixel * rep.bitsPerSample / 8 }

if args[1] == "shift" {
    let prior = load(args[2]), fresh = load(args[3])
    let maxShift = args.count > 4 ? Int(args[4]) ?? 8 : 8
    let tol = args.count > 5 ? Int(args[5]) ?? 8 : 8
    guard prior.pixelsWide == fresh.pixelsWide, prior.pixelsHigh == fresh.pixelsHigh else {
        print("SIZE \(prior.pixelsWide)x\(prior.pixelsHigh) -> \(fresh.pixelsWide)x\(fresh.pixelsHigh)")
        exit(0)
    }
    let w = prior.pixelsWide, h = prior.pixelsHigh
    let ob = prior.bitmapData!, nb = fresh.bitmapData!
    let obpr = prior.bytesPerRow, nbpr = fresh.bytesPerRow
    let opx = pxStride(prior), npx = pxStride(fresh)
    let channels = min(opx, npx, 4)
    let x0 = args.count > 6 ? Int((Double(args[6]) ?? 0) * 2) : 0
    let x1 = args.count > 7 ? Int((Double(args[7]) ?? 0) * 2) : w
    print("帧 \(w)x\(h)px，容差 \(tol)，列范围 \(x0/2)–\(x1/2)pt，比较 after[y] vs before[y-k]")
    for k in 0...maxShift {
        var bands: [(Int, Int)] = []
        var openStart: Int? = nil
        var last = -100
        var count = 0
        for y in k..<h {
            var diff = false
            var x = x0
            while x < min(x1, w), !diff {
                let o = ob + (y - k) * obpr + x * opx
                let n = nb + y * nbpr + x * npx
                for c in 0..<channels where abs(Int(o[c]) - Int(n[c])) > tol { diff = true }
                x += 1
            }
            if diff {
                count += 1
                if openStart == nil { openStart = y }
                last = y
            } else if y - last > 8, let s = openStart {
                bands.append((s, last)); openStart = nil
            }
        }
        if let s = openStart { bands.append((s, last)) }
        let top = bands.prefix(4).map { String(format: "%.1f–%.1fpt", Double($0.0) / 2, Double($0.1 + 1) / 2) }
            .joined(separator: ", ")
        print(String(format: "  k=%dpx (%.1fpt)  不同行=%-5d 带数=%-3d %@",
                     k, Double(k) / 2, count, bands.count, top))
    }
    exit(0)
}

if args[1] == "stats" {
    // 一块区域里的**亮度分布**：众数=背景，最暗 2% 分位=字形，两者算 WCAG 对比度。
    // 存在的理由：R20 看帧时觉得暗色的清除 × "有点淡"，但"有点淡"不是判据 ——
    // 要么量出对比度，要么写"未量化"。（另一条教训：只用亮度判**两态**可分辨是用错轴，
    // 这里判的是同一帧里字形与它自己的底，亮度就是对的那根轴。）
    guard args.count >= 4 else { exit(2) }
    let spec = args[3].split(separator: ",").compactMap { Double($0) }
    guard spec.count == 4 else { print("stats 要 x,y,w,h 四个数（pt）"); exit(2) }
    let scale = args.count > 5 ? (Double(args[5]) ?? 2) : 2
    let rep = load(args[2])
    let x0 = Int(spec[0] * scale), y0 = Int(spec[1] * scale)
    let w = Int(spec[2] * scale), h = Int(spec[3] * scale)
    let base = rep.bitmapData!, bpp = pxStride(rep), bpr = rep.bytesPerRow
    var lumas: [Int] = []
    var counts: [Int: Int] = [:]
    for y in y0..<min(y0 + h, rep.pixelsHigh) {
        for x in x0..<min(x0 + w, rep.pixelsWide) {
            let p = base + y * bpr + x * bpp
            let l = Int((0.2126 * Double(p[0]) + 0.7152 * Double(p[1]) + 0.0722 * Double(p[2])).rounded())
            lumas.append(l)
            counts[l, default: 0] += 1
        }
    }
    guard !lumas.isEmpty else { print("区域为空"); exit(3) }
    let sorted = lumas.sorted()
    let mode = counts.max { $0.value < $1.value }!
    let dark = Array(sorted.prefix(max(1, sorted.count / 50)))
    let light = Array(sorted.suffix(max(1, sorted.count / 50)))
    func relLum(_ v: Int) -> Double {
        let c = Double(v) / 255
        return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
    }
    func ratio(_ a: Int, _ b: Int) -> Double {
        let la = relLum(a) + 0.05, lb = relLum(b) + 0.05
        return max(la, lb) / min(la, lb)
    }
    let darkMean = Int(dark.reduce(0, +) / dark.count)
    let lightMean = Int(light.reduce(0, +) / light.count)
    print("n=\(lumas.count) 背景众数=\(mode.key)(占 \(100*mode.value/lumas.count)% 像素) "
          + "最暗2%均值=\(darkMean) 最亮2%均值=\(lightMean)")
    print("对比度：暗字/背景=\(String(format: "%.2f", ratio(darkMean, mode.key))) "
          + "亮字/背景=\(String(format: "%.2f", ratio(lightMean, mode.key)))（3.0 是非文字 UI 部件的地板）")
    exit(0)
}

if args[1] == "crop" {
    guard args.count >= 5 else { exit(2) }
    let spec = args[4].split(separator: ",").compactMap { Int($0) }
    guard spec.count == 4 else { print("crop 要 x,y,w,h 四个数（pt）"); exit(2) }
    let scale = args.count > 5 ? Double(args[5]) ?? 2 : 2
    let rep = load(args[2])
    let x = Int((Double(spec[0]) * scale).rounded()), y = Int((Double(spec[1]) * scale).rounded())
    let w = Int((Double(spec[2]) * scale).rounded()), h = Int((Double(spec[3]) * scale).rounded())
    let spp = rep.samplesPerPixel
    let out = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                               bitsPerSample: 8, samplesPerPixel: spp, hasAlpha: rep.hasAlpha,
                               isPlanar: false, colorSpaceName: .deviceRGB,
                               bytesPerRow: w * spp, bitsPerPixel: spp * 8)!
    let ob = rep.bitmapData!, nb = out.bitmapData!
    for row in 0..<h {
        let sy = min(y + row, rep.pixelsHigh - 1)
        for col in 0..<w {
            let sx = min(x + col, rep.pixelsWide - 1)
            memcpy(nb + row * out.bytesPerRow + col * spp,
                   ob + sy * rep.bytesPerRow + sx * spp, spp)
        }
    }
    guard let data = out.representation(using: .png, properties: [:]) else { exit(4) }
    try! data.write(to: URL(fileURLWithPath: args[3]))
    print("WROTE \(args[3]) \(w)x\(h)px = \(Double(w)/scale)x\(Double(h)/scale)pt 源=\(args[2])")
    exit(0)
}

print("未知模式 \(args[1])")
exit(2)
